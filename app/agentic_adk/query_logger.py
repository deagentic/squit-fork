"""
QueryLogger - Sistema de logging de queries en BigQuery para memoria y few-shots.

Este módulo guarda queries del usuario + respuestas + embeddings en BigQuery
para enriquecer la memoria del agente y generar few-shots dinámicos.
"""

import logging
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from google.cloud import bigquery
import google.genai as genai

logger = logging.getLogger(__name__)


class QueryLogger:
    """
    Logger de queries en BigQuery para memoria y few-shots.
    
    Guarda:
    - Query del usuario
    - Respuesta del agente
    - Embedding del query (768 dims)
    - Metadata (session, timestamp, etc)
    
    Propósito:
    1. Memoria: Buscar queries similares del pasado
    2. Few-shots: Enriquecer prompts con ejemplos reales
    3. Analytics: Entender patrones de uso
    """
    
    # Schema de la tabla
    SCHEMA = [
        bigquery.SchemaField("query_id", "STRING", mode="REQUIRED", 
                            description="MD5 hash del query"),
        bigquery.SchemaField("session_id", "STRING", mode="REQUIRED",
                            description="ID de sesión del usuario"),
        bigquery.SchemaField("user_query", "STRING", mode="REQUIRED",
                            description="Query original del usuario"),
        bigquery.SchemaField("assistant_response", "STRING", mode="REQUIRED",
                            description="Respuesta del asistente"),
        bigquery.SchemaField("query_embedding", "FLOAT64", mode="REPEATED",
                            description="Embedding del query (768 dims)"),
        bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED",
                            description="Timestamp de la query"),
        bigquery.SchemaField("response_length", "INTEGER", mode="NULLABLE",
                            description="Longitud de respuesta en caracteres"),
        bigquery.SchemaField("turn_number", "INTEGER", mode="NULLABLE",
                            description="Número de turno en la conversación"),
        bigquery.SchemaField("detected_entities", "STRING", mode="REPEATED",
                            description="Entidades detectadas (kayak, procedures, etc)"),
        bigquery.SchemaField("search_results_count", "INTEGER", mode="NULLABLE",
                            description="Cantidad de resultados de búsqueda"),
    ]
    
    def __init__(
        self,
        project_id: str,
        dataset_id: str = "deacero_sql_objects",
        table_id: str = "query_history",
        gemini_api_key: str = None
    ):
        """
        Inicializa el logger.
        
        Args:
            project_id: GCP project ID
            dataset_id: BigQuery dataset
            table_id: Nombre de tabla para logs
            gemini_api_key: API key de Gemini para embeddings
        """
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.table_id = table_id
        self.full_table_id = f"{project_id}.{dataset_id}.{table_id}"
        
        self.bq_client = bigquery.Client(project=project_id)
        self.gemini_client = genai.Client(api_key=gemini_api_key) if gemini_api_key else None
        
        # Crear tabla si no existe
        self._ensure_table_exists()
        
        logger.info(f"✅ QueryLogger inicializado: {self.full_table_id}")
    
    def _ensure_table_exists(self):
        """Crea la tabla si no existe."""
        try:
            self.bq_client.get_table(self.full_table_id)
            logger.info(f"Tabla {self.table_id} ya existe")
        except Exception:
            # Crear tabla
            table = bigquery.Table(self.full_table_id, schema=self.SCHEMA)
            table.time_partitioning = bigquery.TimePartitioning(
                type_=bigquery.TimePartitioningType.DAY,
                field="timestamp"
            )
            table = self.bq_client.create_table(table)
            logger.info(f"✅ Tabla {self.table_id} creada con particionamiento por día")
    
    def _generate_embedding(self, text: str) -> List[float]:
        """
        Genera embedding de un texto con Gemini.
        
        Args:
            text: Texto a embedear
            
        Returns:
            Lista de 768 floats
        """
        if not self.gemini_client:
            logger.warning("Gemini client no configurado, retornando embedding vacío")
            return [0.0] * 768
        
        try:
            response = self.gemini_client.models.embed_content(
                model="models/embedding-001",
                content=text,
                task_type="retrieval_query"
            )
            return response.embedding
        except Exception as e:
            logger.error(f"Error generando embedding: {e}")
            return [0.0] * 768
    
    def _extract_entities(self, text: str) -> List[str]:
        """
        Extrae entidades mencionadas en el texto.
        
        Args:
            text: Texto a analizar
            
        Returns:
            Lista de entidades detectadas
        """
        text_lower = text.lower()
        entities = []
        
        # Keywords de dominio conocidos
        keywords = [
            "kayak", "inventario", "ventas", "compras", "finanzas",
            "produccion", "logistica", "recursos_humanos",
            "procedure", "function", "view", "table", "trigger"
        ]
        
        for kw in keywords:
            if kw in text_lower:
                entities.append(kw)
        
        return list(set(entities))
    
    def log_query(
        self,
        session_id: str,
        user_query: str,
        assistant_response: str,
        turn_number: int = None,
        search_results_count: int = None
    ):
        """
        Registra una query en BigQuery.
        
        Args:
            session_id: ID de sesión
            user_query: Query del usuario
            assistant_response: Respuesta del asistente
            turn_number: Número de turno en la conversación
            search_results_count: Cantidad de resultados obtenidos
        """
        try:
            # Generar query_id único
            query_hash = hashlib.sha256(
                f"{user_query}{datetime.now(timezone.utc).isoformat()}".encode()
            ).hexdigest()
            
            # Generar embedding
            embedding = self._generate_embedding(user_query)
            
            # Detectar entidades
            combined_text = f"{user_query} {assistant_response}"
            entities = self._extract_entities(combined_text)
            
            # Preparar row
            row = {
                "query_id": query_hash,
                "session_id": session_id,
                "user_query": user_query,
                "assistant_response": assistant_response,
                "query_embedding": embedding,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "response_length": len(assistant_response),
                "turn_number": turn_number,
                "detected_entities": entities,
                "search_results_count": search_results_count
            }
            
            # Insertar en BigQuery (streaming)
            errors = self.bq_client.insert_rows_json(self.full_table_id, [row])
            
            if errors:
                logger.error(f"Error insertando query log: {errors}")
            else:
                logger.info(f"✅ Query logged: {query_hash[:8]}...")
        
        except Exception as e:
            logger.error(f"Error en log_query: {e}")
            # No fallar el proceso principal si logging falla
    
    def get_similar_queries(
        self,
        query: str,
        limit: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Busca queries similares en el historial usando embeddings.
        
        Args:
            query: Query actual del usuario
            limit: Máximo de resultados
            similarity_threshold: Umbral de similitud (0-1)
            
        Returns:
            Lista de queries similares con sus respuestas
        """
        if not self.gemini_client:
            logger.warning("Gemini client no configurado, retornando lista vacía")
            return []
        
        try:
            # Generar embedding del query actual
            query_embedding = self._generate_embedding(query)
            
            # Query en BigQuery con similitud coseno
            sql = f"""
            WITH current_query AS (
                SELECT {query_embedding} AS embedding
            )
            SELECT 
                query_id,
                user_query,
                assistant_response,
                timestamp,
                detected_entities,
                turn_number,
                -- Similitud coseno
                (
                    SELECT SUM(a * b) / (
                        SQRT(SUM(a * a)) * SQRT(SUM(b * b))
                    )
                    FROM UNNEST(query_embedding) AS a WITH OFFSET pos1
                    INNER JOIN UNNEST((SELECT embedding FROM current_query)) AS b WITH OFFSET pos2
                    ON pos1 = pos2
                ) AS similarity
            FROM `{self.full_table_id}`
            WHERE 
                -- Últimos 30 días
                timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
            HAVING similarity >= {similarity_threshold}
            ORDER BY similarity DESC
            LIMIT {limit}
            """
            
            query_job = self.bq_client.query(sql)
            results = query_job.result()
            
            similar_queries = []
            for row in results:
                similar_queries.append({
                    "query_id": row.query_id,
                    "user_query": row.user_query,
                    "assistant_response": row.assistant_response,
                    "similarity": float(row.similarity),
                    "timestamp": row.timestamp.isoformat() if row.timestamp else None,
                    "entities": row.detected_entities or []
                })
            
            logger.info(f"✅ Encontradas {len(similar_queries)} queries similares")
            return similar_queries
        
        except Exception as e:
            logger.error(f"Error buscando queries similares: {e}")
            return []
    
    def get_few_shot_examples(
        self,
        query: str,
        limit: int = 3
    ) -> str:
        """
        Genera ejemplos few-shot desde queries históricas similares.
        
        Args:
            query: Query actual del usuario
            limit: Cantidad de ejemplos
            
        Returns:
            String formateado con ejemplos few-shot
        """
        similar = self.get_similar_queries(query, limit=limit, similarity_threshold=0.75)
        
        if not similar:
            return ""
        
        few_shots = "Ejemplos de queries similares resueltas anteriormente:\n\n"
        
        for i, example in enumerate(similar, 1):
            few_shots += f"Ejemplo {i}:\n"
            few_shots += f"Usuario: {example['user_query']}\n"
            few_shots += f"Asistente: {example['assistant_response'][:200]}...\n"
            few_shots += f"Similitud: {example['similarity']:.2f}\n\n"
        
        return few_shots
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del historial de queries.
        
        Returns:
            Dict con métricas
        """
        try:
            sql = f"""
            SELECT 
                COUNT(*) as total_queries,
                COUNT(DISTINCT session_id) as total_sessions,
                AVG(response_length) as avg_response_length,
                APPROX_TOP_COUNT(detected_entities, 10) as top_entities
            FROM `{self.full_table_id}`
            WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
            """
            
            query_job = self.bq_client.query(sql)
            result = list(query_job.result())[0]
            
            return {
                "total_queries": result.total_queries,
                "total_sessions": result.total_sessions,
                "avg_response_length": float(result.avg_response_length) if result.avg_response_length else 0,
                "top_entities": [
                    {"entity": e.value, "count": e.count} 
                    for e in result.top_entities
                ] if result.top_entities else []
            }
        
        except Exception as e:
            logger.error(f"Error obteniendo stats: {e}")
            return {}


# Singleton
_query_logger = None


def get_query_logger(
    project_id: str,
    gemini_api_key: str,
    dataset_id: str = "deacero_sql_objects"
) -> QueryLogger:
    """Obtiene instancia singleton del QueryLogger."""
    global _query_logger
    if _query_logger is None:
        _query_logger = QueryLogger(
            project_id=project_id,
            dataset_id=dataset_id,
            gemini_api_key=gemini_api_key
        )
    return _query_logger

