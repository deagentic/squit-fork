"""
Pipeline de ingesta BigQuery → Weaviate usando Gemini.

Este módulo implementa el ETL para transferir objetos de código
desde BigQuery a Weaviate con enrichment inteligente usando Gemini.
"""

import hashlib
import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
from google import genai
from google.genai import types

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from squit_client import BigQueryClient
from .config import IngestionConfig, WeaviateConfig
from .weaviate_client import WeaviateClient
from .smart_chunker import SQLSmartChunker, CodeChunk

logger = logging.getLogger(__name__)


class GeminiCodeAnalyzer:
    """Analizador de código SQL usando Gemini para extraer contexto e insights."""

    def __init__(self, gemini_api_key: Optional[str] = None):
        """
        Inicializa el analizador con Gemini.
        
        Args:
            gemini_api_key: API key de Gemini.
        """
        weaviate_config = WeaviateConfig()
        api_key = gemini_api_key or weaviate_config.GEMINI_API_KEY
        self.gemini_client = genai.Client(api_key=api_key)

    def analyze_code(self, sql_code: str, object_name: str, object_type: str) -> Dict[str, Any]:
        """
        Analiza un objeto de código SQL usando Gemini.
        
        Args:
            sql_code: Código SQL a analizar.
            object_name: Nombre del objeto.
            object_type: Tipo del objeto.
            
        Returns:
            Diccionario con análisis del código.
        """
        try:
            # Análisis básico (sin IA)
            basic_analysis = self._basic_analysis(sql_code, object_name, object_type)
            
            # Análisis semántico con Gemini (solo para objetos importantes)
            if self._should_analyze_with_ai(sql_code, object_type):
                gemini_analysis = self._gemini_analysis(sql_code, object_name, object_type)
                basic_analysis.update(gemini_analysis)
            
            # Generar embedding con Gemini
            embedding = self._generate_embedding(sql_code, object_name)
            basic_analysis["embedding"] = embedding
            
            return basic_analysis
            
        except Exception as e:
            logger.warning("Error analizando código %s: %s", object_name, e)
            return self._fallback_analysis(sql_code, object_name, object_type)

    def _generate_embedding(self, sql_code: str, object_name: str) -> List[float]:
        """
        Genera embedding usando Gemini text-embedding-004.
        
        Args:
            sql_code: Código SQL.
            object_name: Nombre del objeto.
            
        Returns:
            Vector embedding de 768 dimensiones.
        """
        try:
            # Preparar texto para embedding (combinar código y nombre)
            text_for_embedding = f"Object: {object_name}\nSQL Code:\n{sql_code[:2000]}"
            
            # Generar embedding usando Gemini optimizado para búsqueda semántica
            from google.genai import types
            
            response = self.gemini_client.models.embed_content(
                model="gemini-embedding-001",
                contents=text_for_embedding,
                config=types.EmbedContentConfig(
                    task_type="SEMANTIC_SIMILARITY",  # Optimizado para búsqueda
                    output_dimensionality=768,
                ),
            )
            
            return response.embeddings[0].values
            
        except Exception as e:
            logger.warning("Error generando embedding para %s: %s", object_name, e)
            # Fallback: vector cero de 768 dimensiones
            return [0.0] * 768

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
        
        # Patrones de negocio en español
        business_patterns = {
            "authentication": r"(login|auth|password|security|usuario|autenticacion)",
            "financial": r"(factur|payment|billing|precio|costo|venta|pago|dinero)",
            "inventory": r"(inventory|stock|producto|almacen|inventario)",
            "reporting": r"(report|reporte|dashboard|analytics|informe)",
            "user_management": r"(user|usuario|perfil|role|rol|cliente)",
            "audit": r"(audit|log|track|history|historial|auditoria)",
            "sales": r"(venta|ventas|cliente|pedido|orden)",
            "security": r"(seguridad|permiso|acceso|clave|token)",
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
        if any(keyword in sql_code.upper() for keyword in ["TRANSACTION", "BEGIN", "COMMIT"]):
            tags.append("transactional")
        if "CURSOR" in sql_code.upper():
            tags.append("cursor_based")
        
        return list(set(tags))

    def _calculate_complexity(self, sql_code: str, line_count: int) -> float:
        """Calcula un score de complejidad del código."""
        complexity_factors = 0
        
        # Longitud del código
        if line_count > 100:
            complexity_factors += 3
        elif line_count > 50:
            complexity_factors += 2
        elif line_count > 20:
            complexity_factors += 1
        
        # Estructuras de control
        control_structures = ["IF", "WHILE", "FOR", "CASE", "TRY", "CATCH", "GOTO"]
        for structure in control_structures:
            complexity_factors += sql_code.upper().count(structure) * 0.5
        
        # Joins complejos
        join_patterns = [
            r"\bJOIN\b", r"\bINNER JOIN\b", r"\bLEFT JOIN\b", 
            r"\bRIGHT JOIN\b", r"\bFULL JOIN\b", r"\bCROSS JOIN\b"
        ]
        for pattern in join_patterns:
            complexity_factors += len(re.findall(pattern, sql_code.upper())) * 0.3
        
        # Subqueries y CTEs
        subquery_count = sql_code.upper().count("SELECT") - 1  # -1 for main SELECT
        complexity_factors += max(0, subquery_count) * 0.4
        
        # CTEs (Common Table Expressions)
        cte_count = sql_code.upper().count("WITH")
        complexity_factors += cte_count * 0.6
        
        # Funciones agregadas complejas
        complex_functions = ["ROW_NUMBER", "RANK", "DENSE_RANK", "PARTITION BY"]
        for func in complex_functions:
            complexity_factors += sql_code.upper().count(func) * 0.4
        
        # Normalizar a 0-100
        return min(100, complexity_factors * 8)

    def _extract_business_context(self, sql_code: str, object_name: str) -> str:
        """Extrae contexto de negocio básico."""
        # Extraer comentarios SQL
        comments = re.findall(r"--.*|/\*.*?\*/", sql_code, re.DOTALL)
        
        # Inferir contexto del nombre
        name_context = self._infer_context_from_name(object_name)
        
        # Combinar contexto
        context_parts = [name_context]
        if comments:
            # Limpiar y agregar comentarios relevantes
            for comment in comments[:3]:
                clean_comment = comment.strip("--/*").strip()
                if len(clean_comment) > 10:  # Solo comentarios significativos
                    context_parts.append(clean_comment)
        
        return " | ".join(filter(None, context_parts))

    def _infer_context_from_name(self, object_name: str) -> str:
        """Infiere contexto del nombre del objeto."""
        name_lower = object_name.lower()
        
        context_mapping = {
            # Gestión de usuarios
            "user": "Gestión de usuarios",
            "usuario": "Gestión de usuarios", 
            "cliente": "Gestión de clientes",
            
            # Seguridad
            "auth": "Autenticación y seguridad",
            "login": "Autenticación y seguridad",
            "password": "Gestión de contraseñas",
            "seguridad": "Seguridad del sistema",
            
            # Finanzas y ventas
            "factur": "Facturación y ventas",
            "venta": "Gestión de ventas",
            "pago": "Procesamiento de pagos",
            "precio": "Gestión de precios",
            
            # Inventario y productos
            "product": "Gestión de productos",
            "inventory": "Control de inventario",
            "almacen": "Gestión de almacén",
            "stock": "Control de stock",
            
            # Reportes y analytics
            "report": "Reportes y analytics",
            "dashboard": "Dashboards ejecutivos",
            "metric": "Métricas del negocio",
            
            # Auditoría y logging
            "audit": "Auditoría y logging",
            "log": "Sistema de logs",
            "history": "Historial de cambios",
            
            # Configuración
            "config": "Configuración del sistema",
            "param": "Parámetros del sistema",
        }
        
        for keyword, context in context_mapping.items():
            if keyword in name_lower:
                return context
        
        return "Funcionalidad general del sistema"

    def _should_analyze_with_ai(self, sql_code: str, object_type: str) -> bool:
        """Determina si vale la pena analizar con Gemini."""
        # Analizar objetos complejos o importantes
        if object_type in ["PROCEDURE", "FUNCTION"]:
            # Procedimientos y funciones siempre son importantes
            return len(sql_code) > 200
        elif object_type == "VIEW":
            # Views complejas
            return len(sql_code) > 300
        elif object_type == "TRIGGER":
            # Triggers siempre son críticos
            return True
        
        return False

    def _gemini_analysis(self, sql_code: str, object_name: str, object_type: str) -> Dict[str, Any]:
        """Análisis semántico usando Gemini."""
        try:
            prompt = f"""
            Analiza este objeto SQL y proporciona información estructurada:

            Objeto: {object_name} (Tipo: {object_type})
            
            Código SQL:
            ```sql
            {sql_code[:3000]}  # Limitar para evitar tokens excesivos
            ```

            Proporciona análisis en formato JSON:
            {{
                "code_summary": "Resumen conciso del propósito (1-2 líneas)",
                "business_context": "Área funcional o dominio de negocio",
                "ai_tags": ["tag1", "tag2", "tag3"],
                "main_functionality": "Funcionalidad principal",
                "data_operations": ["operación1", "operación2"],
                "business_rules": ["regla1", "regla2"],
                "complexity_assessment": "Evaluación de complejidad"
            }}

            Enfócate en:
            1. ¿Qué hace este código?
            2. ¿A qué área de negocio pertenece?
            3. ¿Qué operaciones de datos realiza?
            4. ¿Qué reglas de negocio implementa?
            """
            
            # Configurar para respuesta JSON estructurada
            config = types.GenerateContentConfig(
                temperature=0.1,  # Baja para consistencia
                max_output_tokens=1000,
                response_mime_type="application/json",
            )
            
            response = self.gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=config,
            )
            
            # Parsear respuesta JSON con validación
            if not response.text:
                logger.warning("Respuesta vacía de Gemini para %s", object_name)
                return self._fallback_gemini_analysis(object_name, object_type)
            
            # Limpiar la respuesta para extraer JSON válido
            text = response.text.strip()
            
            # Buscar JSON en la respuesta (a veces Gemini incluye texto extra)
            json_start = text.find('{')
            json_end = text.rfind('}') + 1
            
            if json_start == -1 or json_end <= json_start:
                logger.warning("No se encontró JSON válido en respuesta de Gemini para %s", object_name)
                return self._fallback_gemini_analysis(object_name, object_type)
            
            json_text = text[json_start:json_end]
            analysis = json.loads(json_text)
            
            return {
                "code_summary": analysis.get("code_summary", ""),
                "business_context": analysis.get("business_context", ""),
                "ai_tags": analysis.get("ai_tags", []),
                "main_functionality": analysis.get("main_functionality", ""),
                "data_operations": analysis.get("data_operations", []),
                "business_rules": analysis.get("business_rules", []),
                "complexity_assessment": analysis.get("complexity_assessment", ""),
            }
            
        except Exception as e:
            logger.warning("Error en análisis Gemini para %s: %s", object_name, e)
            return self._fallback_gemini_analysis(object_name, object_type)

    def _fallback_gemini_analysis(self, object_name: str, object_type: str) -> Dict[str, Any]:
        """Análisis de fallback cuando falla Gemini."""
        return {
            "code_summary": f"{object_type} {object_name} - Análisis automático no disponible",
            "business_context": "Contexto no determinado",
            "ai_tags": [object_type.lower()],
            "main_functionality": "Funcionalidad no analizada",
            "data_operations": [],
            "business_rules": [],
            "complexity_assessment": "Evaluación no disponible",
        }

    def _fallback_analysis(self, sql_code: str, object_name: str, object_type: str) -> Dict[str, Any]:
        """Análisis de fallback cuando falla el análisis principal."""
        return {
            "code_length": len(sql_code),
            "complexity_score": 50,  # Score promedio
            "tags": [object_type.lower()],
            "business_context": "Análisis no disponible",
            "code_summary": f"{object_type} {object_name}",
            "embedding": [0.0] * 768,  # Vector cero para Gemini
        }


class GeminiIngestionPipeline:
    """
    Pipeline principal para ingestar datos usando Gemini.
    
    Implementa el proceso ETL completo con enrichment inteligente
    usando Gemini para análisis y embeddings.
    """

    def __init__(
        self,
        bigquery_client: BigQueryClient,
        weaviate_client: WeaviateClient,
        config: Optional[IngestionConfig] = None,
    ):
        """
        Inicializa el pipeline con Gemini.
        
        Args:
            bigquery_client: Cliente BigQuery configurado.
            weaviate_client: Cliente Weaviate configurado.
            config: Configuración del pipeline.
        """
        self.bigquery_client = bigquery_client
        self.weaviate_client = weaviate_client
        self.config = config or IngestionConfig()
        self.analyzer = GeminiCodeAnalyzer()
        self.chunker = SQLSmartChunker()
        
        # Estadísticas de procesamiento
        self.stats = {
            "processed": 0,
            "success": 0,
            "errors": 0,
            "skipped": 0,
            "embeddings_generated": 0,
            "ai_analysis_completed": 0,
            "chunks_created": 0,
            "large_objects_chunked": 0,
        }

    def run_full_ingestion(
        self,
        limit: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Ejecuta la ingesta completa desde BigQuery usando Gemini.
        
        Args:
            limit: Límite de objetos a procesar.
            filters: Filtros para BigQuery.
            
        Returns:
            Estadísticas del procesamiento.
        """
        logger.info("Iniciando ingesta completa BigQuery → Weaviate (Gemini)")
        
        try:
            # 1. Obtener datos de BigQuery
            logger.info("Extrayendo datos de BigQuery...")
            df = self._extract_from_bigquery(limit, filters)
            
            if df.empty:
                logger.warning("No se encontraron datos para procesar")
                return self.stats
            
            logger.info("Extraídos %d objetos de BigQuery", len(df))
            
            # 2. Procesar en chunks con Gemini
            total_chunks = len(df) // self.config.CHUNK_SIZE + 1
            
            for i, chunk_df in enumerate(self._chunk_dataframe(df)):
                logger.info("Procesando chunk %d/%d (%d objetos) con Gemini", 
                          i + 1, total_chunks, len(chunk_df))
                
                self._process_chunk_with_gemini(chunk_df)
            
            logger.info("Ingesta completada con Gemini. Estadísticas: %s", self.stats)
            return self.stats
            
        except Exception as e:
            logger.error("Error en ingesta completa con Gemini: %s", e)
            raise

    def _extract_from_bigquery(
        self, 
        limit: Optional[int], 
        filters: Optional[Dict[str, Any]]
    ) -> pd.DataFrame:
        """Extrae datos de BigQuery con filtros optimizados."""
        
        # Query optimizada para objetos más relevantes
        query = f"""
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
        FROM `{self.bigquery_client.config.full_table_id}`
        WHERE sql_code IS NOT NULL 
        AND LENGTH(sql_code) >= {self.config.MIN_CODE_LENGTH}
        AND LENGTH(sql_code) <= {self.config.MAX_CODE_LENGTH}
        AND object_type IN ('PROCEDURE', 'FUNCTION', 'VIEW', 'TRIGGER')  -- Objetos más importantes
        """
        
        # Agregar filtros adicionales
        if filters:
            for field, value in filters.items():
                if isinstance(value, list):
                    # Escapar valores para SQL
                    escaped_values = [v.replace("\\", "\\\\") for v in value]
                    values_str = "', '".join(escaped_values)
                    query += f" AND {field} IN ('{values_str}')"
                else:
                    # Escapar valor único para SQL
                    escaped_value = value.replace("\\", "\\\\")
                    query += f" AND {field} = '{escaped_value}'"
        
        # Ordenar por relevancia (objetos más recientes y complejos primero)
        query += """
        ORDER BY 
            CASE object_type 
                WHEN 'PROCEDURE' THEN 1
                WHEN 'FUNCTION' THEN 2  
                WHEN 'TRIGGER' THEN 3
                WHEN 'VIEW' THEN 4
                ELSE 5
            END,
            last_modified DESC,
            LENGTH(sql_code) DESC
        """
        
        # Aplicar límite
        if limit:
            query += f" LIMIT {limit}"
        
        return self.bigquery_client.execute_query(query)

    def _chunk_dataframe(self, df: pd.DataFrame) -> List[pd.DataFrame]:
        """Divide el DataFrame en chunks para procesamiento."""
        chunks = []
        for i in range(0, len(df), self.config.CHUNK_SIZE):
            chunk = df.iloc[i:i + self.config.CHUNK_SIZE]
            chunks.append(chunk)
        return chunks

    def _process_chunk_with_gemini(self, chunk_df: pd.DataFrame) -> None:
        """Procesa un chunk de datos usando Gemini."""
        # Convertir a lista de diccionarios
        objects = chunk_df.to_dict("records")
        
        # Procesar en paralelo (con menos workers para Gemini por rate limits)
        max_workers = min(self.config.PARALLEL_WORKERS, 2)  # Máximo 2 para Gemini
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self._process_single_object_with_gemini, obj): obj 
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
                    logger.info("Progreso Gemini: %d objetos procesados", self.stats["processed"])

    def _process_single_object_with_gemini(self, obj: Dict[str, Any]) -> None:
        """Procesa un objeto individual usando Gemini con smart chunking."""
        object_name = obj.get("object_name", "Unknown")
        object_type = obj.get("object_type", "Unknown")
        sql_code = obj.get("sql_code", "")
        
        try:
            # Verificar si ya existe (por hash)
            if self._object_exists(obj["content_hash"]):
                self.stats["skipped"] += 1
                return
            
            # Determinar si necesita chunking inteligente
            if self.chunker.should_chunk_object(sql_code, object_type):
                logger.info("Chunking objeto grande %s (%d chars)", object_name, len(sql_code))
                self._process_chunked_object(obj)
                self.stats["large_objects_chunked"] += 1
            else:
                # Procesar como objeto único
                self._process_single_chunk(obj)
            
        except Exception as e:
            logger.error("Error procesando objeto %s con Gemini: %s", obj.get("object_name"), e)
            raise
    
    def _process_chunked_object(self, obj: Dict[str, Any]) -> None:
        """Procesa un objeto grande dividiéndolo en chunks inteligentes."""
        object_name = obj.get("object_name", "Unknown")
        
        # Generar chunks inteligentes
        chunks = self.chunker.chunk_sql_object(obj)
        
        logger.info("Objeto %s dividido en %d chunks semánticos", object_name, len(chunks))
        
        # Procesar cada chunk
        for chunk in chunks:
            self._process_code_chunk(chunk)
            self.stats["chunks_created"] += 1
    
    def _process_code_chunk(self, chunk: CodeChunk) -> None:
        """Procesa un chunk individual de código."""
        try:
            # Analizar código del chunk con Gemini
            analysis = self.analyzer.analyze_code(
                sql_code=chunk.code_content,
                object_name=f"{chunk.object_name}_chunk_{chunk.chunk_index}",
                object_type=chunk.object_type,
            )
            
            # Actualizar estadísticas
            if "embedding" in analysis and any(x != 0 for x in analysis["embedding"]):
                self.stats["embeddings_generated"] += 1
            
            if "ai_tags" in analysis:
                self.stats["ai_analysis_completed"] += 1
            
            # Preparar datos para Weaviate con información del chunk
            weaviate_data = {
                "bigquery_id": chunk.chunk_id,  # ID único del chunk
                "parent_object_id": chunk.parent_object_id,  # ID del objeto padre
                "server": chunk.server,
                "database": chunk.database,
                "schema": chunk.schema,
                "object_name": chunk.object_name,
                "object_type": chunk.object_type,
                "sql_code": chunk.code_content,
                "content_hash": self._generate_chunk_hash(chunk),
                "last_modified": None,
                
                # Metadatos específicos del chunk
                "chunk_type": chunk.chunk_type,
                "chunk_index": chunk.chunk_index,
                "total_chunks": chunk.total_chunks,
                "is_chunk": True,
                
                # Información semántica del chunk
                "semantic_summary": chunk.semantic_summary,
                "business_context": chunk.business_context,
                "complexity_score": chunk.complexity_score,
                "tags": chunk.tags,
                "references_to": chunk.references_to,
                "char_count": chunk.char_count,
                "line_count": chunk.line_count,
                "estimated_tokens": chunk.estimated_tokens,
                
                # Análisis de Gemini
                "code_summary": analysis.get("code_summary", chunk.semantic_summary),
                "ai_tags": analysis.get("ai_tags", chunk.tags),
                "main_functionality": analysis.get("main_functionality", ""),
                "data_operations": analysis.get("data_operations", []),
                "business_rules": analysis.get("business_rules", []),
                "complexity_assessment": analysis.get("complexity_assessment", ""),
            }
            
            # Insertar chunk en Weaviate con embedding
            uuid = self.weaviate_client.insert_code_object_with_vector(
                weaviate_data, 
                analysis.get("embedding", [0.0] * 768)
            )
            
            logger.debug("Chunk %s procesado, UUID: %s", chunk.chunk_id, uuid)
            
        except Exception as e:
            logger.error("Error procesando chunk %s: %s", chunk.chunk_id, e)
            raise
    
    def _process_single_chunk(self, obj: Dict[str, Any]) -> None:
        """Procesa un objeto como chunk único (objetos pequeños)."""
        chunks = self.chunker.chunk_sql_object(obj)  # Retornará un solo chunk
        
        if chunks:
            chunk = chunks[0]
            chunk.chunk_type = 'complete'  # Marcar como objeto completo
            self._process_code_chunk(chunk)
    
    def _generate_chunk_hash(self, chunk: CodeChunk) -> str:
        """Genera hash único para un chunk."""
        import hashlib
        content = f"{chunk.parent_object_id}_{chunk.chunk_index}_{chunk.code_content}"
        return hashlib.md5(content.encode()).hexdigest()

    def _object_exists(self, content_hash: str) -> bool:
        """Verifica si un objeto ya existe en Weaviate."""
        try:
            collection = self.weaviate_client.get_collection("CodeObjects")
            import weaviate.classes as wvc
            response = collection.query.fetch_objects(
                where=wvc.query.Filter.by_property("content_hash").equal(content_hash),
                limit=1,
            )
            return len(response.objects) > 0
        except Exception:
            return False

    def _prepare_for_weaviate_with_gemini(self, obj: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Prepara datos para inserción en Weaviate con análisis de Gemini."""
        # Combinar tags básicos con tags de Gemini
        all_tags = analysis.get("tags", [])
        if "ai_tags" in analysis:
            all_tags.extend(analysis["ai_tags"])
        
        # Enriquecer business_context con análisis de Gemini
        business_context = analysis.get("business_context", "")
        if analysis.get("main_functionality"):
            business_context += f" | Funcionalidad: {analysis['main_functionality']}"
        
        return {
            "server": obj["server"],
            "database": obj["database"], 
            "schema": obj["schema"],
            "object_name": obj["object_name"],
            "object_type": obj["object_type"],
            "sql_code": obj["sql_code"],
            "code_summary": analysis.get("code_summary", f"{obj['object_type']} {obj['object_name']}"),
            "business_context": business_context,
            "complexity_score": analysis.get("complexity_score", 0),
            "last_modified": obj["last_modified"],
            "content_hash": obj["content_hash"],
            "tags": list(set(all_tags)),  # Eliminar duplicados
            "bigquery_id": obj["bigquery_id"],
            # Campos adicionales de Gemini
            "main_functionality": analysis.get("main_functionality", ""),
            "data_operations": analysis.get("data_operations", []),
            "business_rules": analysis.get("business_rules", []),
            "complexity_assessment": analysis.get("complexity_assessment", ""),
        }

    def get_ingestion_stats(self) -> Dict[str, Any]:
        """Retorna estadísticas del último procesamiento con Gemini."""
        total_processed = max(1, self.stats["processed"])
        
        return {
            **self.stats,
            "success_rate": self.stats["success"] / total_processed * 100,
            "error_rate": self.stats["errors"] / total_processed * 100,
            "embedding_rate": self.stats["embeddings_generated"] / total_processed * 100,
            "ai_analysis_rate": self.stats["ai_analysis_completed"] / total_processed * 100,
            "powered_by": "Gemini",
        }
