"""
Pipeline de ingesta BigQuery → Weaviate.

Este módulo implementa el ETL para transferir objetos de código
desde BigQuery a Weaviate con enrichment inteligente.
"""

import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

import pandas as pd
import weaviate
from openai import OpenAI

from ..squit_client import BigQueryClient
from .config import IngestionConfig
from .weaviate_client import WeaviateClient

logger = logging.getLogger(__name__)


class CodeAnalyzer:
    """Analizador de código SQL para extraer contexto e insights."""

    def __init__(self, openai_client: Optional[OpenAI] = None):
        """
        Inicializa el analizador.
        
        Args:
            openai_client: Cliente OpenAI para análisis semántico.
        """
        self.openai_client = openai_client or OpenAI()

    def analyze_code(self, sql_code: str, object_name: str, object_type: str) -> Dict[str, Any]:
        """
        Analiza un objeto de código SQL.
        
        Args:
            sql_code: Código SQL a analizar.
            object_name: Nombre del objeto.
            object_type: Tipo del objeto.
            
        Returns:
            Diccionario con análisis del código.
        """
        try:
            # Análisis básico
            basic_analysis = self._basic_analysis(sql_code, object_name, object_type)
            
            # Análisis semántico con IA (solo para objetos importantes)
            if self._should_analyze_with_ai(sql_code, object_type):
                ai_analysis = self._ai_analysis(sql_code, object_name, object_type)
                basic_analysis.update(ai_analysis)
            
            return basic_analysis
            
        except Exception as e:
            logger.warning("Error analizando código %s: %s", object_name, e)
            return self._fallback_analysis(sql_code, object_name, object_type)

    def _basic_analysis(self, sql_code: str, object_name: str, object_type: str) -> Dict[str, Any]:
        """Análisis básico sin IA."""
        # Calcular métricas básicas
        code_length = len(sql_code)
        line_count = len(sql_code.splitlines())
        
        # Extraer tags basados en patrones
        tags = self._extract_tags(sql_code, object_name, object_type)
        
        # Calcular score de complejidad
        complexity_score = self._calculate_complexity(sql_code, line_count)
        
        # Extraer contexto básico
        business_context = self._extract_business_context(sql_code, object_name)
        
        return {
            "code_length": code_length,
            "line_count": line_count,
            "complexity_score": complexity_score,
            "tags": tags,
            "business_context": business_context,
            "code_summary": f"{object_type} {object_name}",
        }

    def _extract_tags(self, sql_code: str, object_name: str, object_type: str) -> List[str]:
        """Extrae tags automáticos basados en patrones."""
        tags = [object_type.lower()]
        
        # Patrones de negocio
        business_patterns = {
            "authentication": r"(login|auth|password|security|usuario)",
            "financial": r"(factur|payment|billing|precio|costo|venta)",
            "inventory": r"(inventory|stock|producto|almacen)",
            "reporting": r"(report|reporte|dashboard|analytics)",
            "user_management": r"(user|usuario|perfil|role)",
            "audit": r"(audit|log|track|history|historial)",
        }
        
        code_lower = sql_code.lower()
        name_lower = object_name.lower()
        
        for tag, pattern in business_patterns.items():
            if re.search(pattern, code_lower) or re.search(pattern, name_lower):
                tags.append(tag)
        
        # Patrones técnicos
        if "CREATE" in sql_code.upper():
            tags.append("ddl")
        if any(keyword in sql_code.upper() for keyword in ["INSERT", "UPDATE", "DELETE"]):
            tags.append("dml")
        if "SELECT" in sql_code.upper() and object_type == "VIEW":
            tags.append("query")
        if "TRANSACTION" in sql_code.upper():
            tags.append("transactional")
        if "CURSOR" in sql_code.upper():
            tags.append("cursor_based")
        
        return list(set(tags))

    def _calculate_complexity(self, sql_code: str, line_count: int) -> float:
        """Calcula un score de complejidad del código."""
        # Factores de complejidad
        complexity_factors = 0
        
        # Longitud del código
        if line_count > 100:
            complexity_factors += 2
        elif line_count > 50:
            complexity_factors += 1
        
        # Estructuras de control
        control_structures = ["IF", "WHILE", "FOR", "CASE", "TRY", "CATCH"]
        for structure in control_structures:
            complexity_factors += sql_code.upper().count(structure) * 0.5
        
        # Joins complejos
        join_count = len(re.findall(r"\b(JOIN|INNER JOIN|LEFT JOIN|RIGHT JOIN|FULL JOIN)\b", sql_code.upper()))
        complexity_factors += join_count * 0.3
        
        # Subqueries
        subquery_count = sql_code.upper().count("SELECT") - 1  # -1 for main SELECT
        complexity_factors += max(0, subquery_count) * 0.4
        
        # Normalizar a 0-100
        return min(100, complexity_factors * 10)

    def _extract_business_context(self, sql_code: str, object_name: str) -> str:
        """Extrae contexto de negocio básico."""
        # Extraer comentarios
        comments = re.findall(r"--.*|/\*.*?\*/", sql_code, re.DOTALL)
        
        # Inferir contexto del nombre
        name_context = self._infer_context_from_name(object_name)
        
        # Combinar contexto
        context_parts = [name_context]
        if comments:
            context_parts.extend([comment.strip("--/*").strip() for comment in comments[:3]])
        
        return " | ".join(filter(None, context_parts))

    def _infer_context_from_name(self, object_name: str) -> str:
        """Infiere contexto del nombre del objeto."""
        name_lower = object_name.lower()
        
        context_mapping = {
            "user": "Gestión de usuarios",
            "usuario": "Gestión de usuarios", 
            "auth": "Autenticación y seguridad",
            "login": "Autenticación y seguridad",
            "factur": "Facturación y ventas",
            "venta": "Ventas",
            "product": "Gestión de productos",
            "inventory": "Inventario",
            "report": "Reportes y analytics",
            "audit": "Auditoría y logging",
            "config": "Configuración del sistema",
        }
        
        for keyword, context in context_mapping.items():
            if keyword in name_lower:
                return context
        
        return "Funcionalidad general"

    def _should_analyze_with_ai(self, sql_code: str, object_type: str) -> bool:
        """Determina si vale la pena analizar con IA."""
        # Solo analizar objetos complejos o importantes
        if object_type in ["PROCEDURE", "FUNCTION"] and len(sql_code) > 500:
            return True
        if object_type == "VIEW" and len(sql_code) > 200:
            return True
        return False

    def _ai_analysis(self, sql_code: str, object_name: str, object_type: str) -> Dict[str, Any]:
        """Análisis semántico usando OpenAI."""
        try:
            prompt = f"""
            Analiza este objeto SQL y proporciona:
            1. Un resumen conciso de su propósito (1-2 líneas)
            2. El contexto de negocio (área funcional)
            3. 3-5 tags descriptivos

            Objeto: {object_name} ({object_type})
            Código SQL:
            ```sql
            {sql_code[:2000]}  # Limitar para evitar tokens excesivos
            ```

            Responde en formato JSON:
            {{
                "code_summary": "...",
                "business_context": "...", 
                "ai_tags": ["tag1", "tag2", "tag3"]
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500,
            )
            
            # Parsear respuesta JSON
            import json
            result = json.loads(response.choices[0].message.content)
            
            return {
                "code_summary": result.get("code_summary", ""),
                "business_context": result.get("business_context", ""),
                "ai_tags": result.get("ai_tags", []),
            }
            
        except Exception as e:
            logger.warning("Error en análisis IA para %s: %s", object_name, e)
            return {}

    def _fallback_analysis(self, sql_code: str, object_name: str, object_type: str) -> Dict[str, Any]:
        """Análisis de fallback cuando falla el análisis principal."""
        return {
            "code_length": len(sql_code),
            "complexity_score": 50,  # Score promedio
            "tags": [object_type.lower()],
            "business_context": "Análisis no disponible",
            "code_summary": f"{object_type} {object_name}",
        }


class IngestionPipeline:
    """
    Pipeline principal para ingestar datos de BigQuery a Weaviate.
    
    Implementa el proceso ETL completo con enrichment inteligente
    y procesamiento en paralelo.
    """

    def __init__(
        self,
        bigquery_client: BigQueryClient,
        weaviate_client: WeaviateClient,
        config: Optional[IngestionConfig] = None,
    ):
        """
        Inicializa el pipeline.
        
        Args:
            bigquery_client: Cliente BigQuery configurado.
            weaviate_client: Cliente Weaviate configurado.
            config: Configuración del pipeline.
        """
        self.bigquery_client = bigquery_client
        self.weaviate_client = weaviate_client
        self.config = config or IngestionConfig()
        self.analyzer = CodeAnalyzer()
        
        # Estadísticas de procesamiento
        self.stats = {
            "processed": 0,
            "success": 0,
            "errors": 0,
            "skipped": 0,
        }

    def _format_sql(self, sql: str, **kwargs) -> str:
        """Formatea SQL de forma segura para Bandit."""
        return sql.format(**kwargs)  # nosec B608

    def run_full_ingestion(
        self,
        limit: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Ejecuta la ingesta completa desde BigQuery.
        
        Args:
            limit: Límite de objetos a procesar.
            filters: Filtros para BigQuery.
            
        Returns:
            Estadísticas del procesamiento.
        """
        logger.info("Iniciando ingesta completa BigQuery → Weaviate")
        
        try:
            # 1. Obtener datos de BigQuery
            logger.info("Extrayendo datos de BigQuery...")
            df = self._extract_from_bigquery(limit, filters)
            
            if df.empty:
                logger.warning("No se encontraron datos para procesar")
                return self.stats
            
            logger.info("Extraídos %d objetos de BigQuery", len(df))
            
            # 2. Procesar en chunks
            total_chunks = len(df) // self.config.CHUNK_SIZE + 1
            
            for i, chunk_df in enumerate(self._chunk_dataframe(df)):
                logger.info("Procesando chunk %d/%d (%d objetos)", 
                          i + 1, total_chunks, len(chunk_df))
                
                self._process_chunk(chunk_df)
            
            logger.info("Ingesta completada. Estadísticas: %s", self.stats)
            return self.stats
            
        except Exception as e:
            logger.error("Error en ingesta completa: %s", e)
            raise

    def _extract_from_bigquery(
        self, 
        limit: Optional[int], 
        filters: Optional[Dict[str, Any]]
    ) -> pd.DataFrame:
        """Extrae datos de BigQuery con filtros opcionales."""
        
        # Construir query base
        query = self._format_sql("""
        SELECT 
            server,
            database,
            schema,
            object_name,
            object_type,
            sql_code,
            content_hash,
            last_modified,
            CONCAT(server, '|', database, '|', schema, '|', object_name) as bigquery_id
        FROM `{table}`
        WHERE sql_code IS NOT NULL 
        AND LENGTH(sql_code) >= @min_len
        AND LENGTH(sql_code) <= @max_len
        """, table=self.bigquery_client.config.full_table_id)
        
        # Agregar filtros adicionales
        query_params = [
            bigquery.ScalarQueryParameter("min_len", "INT64", self.config.MIN_CODE_LENGTH),
            bigquery.ScalarQueryParameter("max_len", "INT64", self.config.MAX_CODE_LENGTH)
        ]

        if filters:
            for field, value in filters.items():
                if isinstance(value, list):
                    param_name = f"filter_{field}"
                    query += f" AND {field} IN UNNEST(@{param_name})"
                    query_params.append(bigquery.ArrayQueryParameter(param_name, "STRING", value))
                else:
                    param_name = f"filter_{field}"
                    query += f" AND {field} = @{param_name}"
                    query_params.append(bigquery.ScalarQueryParameter(param_name, "STRING", value))

        # Ordenar por relevancia (objetos más recientes primero)
        query += " ORDER BY last_modified DESC"

        # Agregar límite
        if limit:
            query += " LIMIT @limit"
            query_params.append(bigquery.ScalarQueryParameter("limit", "INT64", limit))

        return self.bigquery_client.execute_query(query, query_parameters=query_params)

    def _chunk_dataframe(self, df: pd.DataFrame) -> List[pd.DataFrame]:
        """Divide el DataFrame en chunks para procesamiento."""
        chunks = []
        for i in range(0, len(df), self.config.CHUNK_SIZE):
            chunk = df.iloc[i:i + self.config.CHUNK_SIZE]
            chunks.append(chunk)
        return chunks

    def _process_chunk(self, chunk_df: pd.DataFrame) -> None:
        """Procesa un chunk de datos."""
        # Convertir a lista de diccionarios
        objects = chunk_df.to_dict("records")
        
        # Procesar en paralelo
        with ThreadPoolExecutor(max_workers=self.config.PARALLEL_WORKERS) as executor:
            futures = {
                executor.submit(self._process_single_object, obj): obj 
                for obj in objects
            }
            
            for future in as_completed(futures):
                obj = futures[future]
                try:
                    future.result()
                    self.stats["success"] += 1
                except Exception as e:
                    logger.error("Error procesando %s: %s", obj.get("object_name"), e)
                    self.stats["errors"] += 1
                
                self.stats["processed"] += 1
                
                # Log progreso
                if self.stats["processed"] % self.config.LOG_PROGRESS_EVERY == 0:
                    logger.info("Progreso: %d objetos procesados", self.stats["processed"])

    def _process_single_object(self, obj: Dict[str, Any]) -> None:
        """Procesa un objeto individual."""
        try:
            # Verificar si ya existe (por hash)
            if self._object_exists(obj["content_hash"]):
                self.stats["skipped"] += 1
                return
            
            # Analizar código
            analysis = self.analyzer.analyze_code(
                sql_code=obj["sql_code"],
                object_name=obj["object_name"],
                object_type=obj["object_type"],
            )
            
            # Preparar datos para Weaviate
            weaviate_data = self._prepare_for_weaviate(obj, analysis)
            
            # Insertar en Weaviate
            uuid = self.weaviate_client.insert_code_object(weaviate_data)
            logger.debug("Objeto %s insertado con UUID: %s", obj["object_name"], uuid)
            
        except Exception as e:
            logger.error("Error procesando objeto %s: %s", obj.get("object_name"), e)
            raise

    def _object_exists(self, content_hash: str) -> bool:
        """Verifica si un objeto ya existe en Weaviate."""
        try:
            collection = self.weaviate_client.get_collection("CodeObjects")
            response = collection.query.fetch_objects(
                where=weaviate.classes.query.Filter.by_property("content_hash").equal(content_hash),
                limit=1,
            )
            return len(response.objects) > 0
        except Exception:
            return False

    def _prepare_for_weaviate(self, obj: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Prepara datos para inserción en Weaviate."""
        # Combinar tags básicos con tags de IA
        all_tags = analysis.get("tags", [])
        if "ai_tags" in analysis:
            all_tags.extend(analysis["ai_tags"])
        
        return {
            "server": obj["server"],
            "database": obj["database"], 
            "schema": obj["schema"],
            "object_name": obj["object_name"],
            "object_type": obj["object_type"],
            "sql_code": obj["sql_code"],
            "code_summary": analysis.get("code_summary", ""),
            "business_context": analysis.get("business_context", ""),
            "complexity_score": analysis.get("complexity_score", 0),
            "last_modified": obj["last_modified"],
            "content_hash": obj["content_hash"],
            "tags": list(set(all_tags)),  # Eliminar duplicados
            "bigquery_id": obj["bigquery_id"],
        }

    def run_incremental_update(self) -> Dict[str, Any]:
        """
        Ejecuta actualización incremental basada en cambios recientes.
        
        Returns:
            Estadísticas del procesamiento incremental.
        """
        logger.info("Iniciando actualización incremental")
        
        try:
            # Obtener objetos modificados recientemente
            recent_query = self._format_sql("""
            SELECT *,
                CONCAT(server, '|', database, '|', schema, '|', object_name) as bigquery_id
            FROM `{table}`
            WHERE last_modified >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
            AND sql_code IS NOT NULL
            ORDER BY last_modified DESC
            """, table=self.bigquery_client.config.full_table_id)
            
            df = self.bigquery_client.execute_query(recent_query)
            
            if df.empty:
                logger.info("No hay cambios recientes para procesar")
                return {"processed": 0, "updated": 0, "new": 0}
            
            logger.info("Encontrados %d objetos modificados recientemente", len(df))
            
            # Procesar actualizaciones
            updated = 0
            new = 0
            
            for _, obj in df.iterrows():
                if self._update_or_create_object(obj.to_dict()):
                    updated += 1
                else:
                    new += 1
            
            stats = {"processed": len(df), "updated": updated, "new": new}
            logger.info("Actualización incremental completada: %s", stats)
            return stats
            
        except Exception as e:
            logger.error("Error en actualización incremental: %s", e)
            raise

    def _update_or_create_object(self, obj: Dict[str, Any]) -> bool:
        """
        Actualiza un objeto existente o crea uno nuevo.
        
        Returns:
            True si se actualizó, False si se creó nuevo.
        """
        try:
            # Verificar si existe
            if self._object_exists(obj["content_hash"]):
                # TODO: Implementar lógica de actualización
                logger.debug("Objeto %s ya existe, saltando", obj["object_name"])
                return True
            else:
                # Crear nuevo objeto
                self._process_single_object(obj)
                return False
                
        except Exception as e:
            logger.error("Error actualizando objeto %s: %s", obj.get("object_name"), e)
            raise

    def get_ingestion_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas del último procesamiento."""
        return {
            **self.stats,
            "success_rate": self.stats["success"] / max(1, self.stats["processed"]) * 100,
            "error_rate": self.stats["errors"] / max(1, self.stats["processed"]) * 100,
        }
