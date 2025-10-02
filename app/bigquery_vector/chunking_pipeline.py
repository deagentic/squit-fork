"""
Pipeline de chunking inteligente 100% en BigQuery.

Este módulo implementa la lógica de chunking directamente en BigQuery SQL,
optimizando para embeddings semánticos y búsqueda vectorial.

Arquitectura:
- Clasificación semántica automática de objetos SQL
- Chunking inteligente por tamaño y complejidad
- Extracción de metadatos de negocio
- Generación de embeddings con Gemini
- Tracking robusto de progreso

Uso:
    pipeline = BigQueryChunkingPipeline()
    
    # Pipeline completo con tracking
    run_id = pipeline.run_full_pipeline()
    
    # O ejecutar etapas individuales
    pipeline.create_chunks_table()
    pipeline.create_embeddings_table()
    pipeline.create_vector_index()
"""

import logging
import traceback
from typing import Dict, List, Optional, Any
from datetime import datetime
from google.cloud import bigquery
from .config import BigQueryVectorConfig
from .progress_tracker import ProgressTracker

logger = logging.getLogger(__name__)


class BigQueryChunkingPipeline:
    """
    Pipeline de chunking inteligente usando BigQuery nativo.
    
    Este pipeline procesa objetos SQL de forma incremental, 
    con checkpoint/recovery automático y tracking detallado.
    
    Atributos:
        config: Configuración del pipeline
        client: Cliente BigQuery
        tracker: Sistema de tracking de progreso
    """
    
    def __init__(self, config: Optional[BigQueryVectorConfig] = None):
        """
        Inicializa el pipeline de chunking.
        
        Args:
            config: Configuración del pipeline.
        """
        self.config = config or BigQueryVectorConfig()
        self.client = bigquery.Client(project=self.config.PROJECT_ID)
        self.tracker = ProgressTracker(config=self.config)
        
    def create_chunks_table(self) -> Dict[str, Any]:
        """
        Crea la tabla de chunks inteligentes con SQL nativo.
        
        Returns:
            Estadísticas de la operación.
        """
        logger.info("Creando tabla de chunks inteligentes...")
        
        # SQL para chunking inteligente
        create_chunks_sql = f"""
        CREATE OR REPLACE TABLE `{self.config.full_chunks_table_id}` AS
        WITH 
        -- Paso 1: Clasificación semántica de objetos
        classified_objects AS (
          SELECT 
            server,
            database,
            schema,
            object_name,
            object_type,
            sql_code,
            content_hash,
            last_modified,
            LENGTH(sql_code) as code_length,
            
            -- Clasificación semántica basada en patrones (RE2 compatible)
            CASE 
              WHEN REGEXP_CONTAINS(UPPER(sql_code), r'SELECT.*FROM.*JOIN') THEN 'complex_query'
              WHEN REGEXP_CONTAINS(UPPER(sql_code), r'CREATE\\s+PROCEDURE') THEN 'stored_procedure'
              WHEN REGEXP_CONTAINS(UPPER(sql_code), r'CREATE\\s+FUNCTION') THEN 'function'
              WHEN REGEXP_CONTAINS(UPPER(sql_code), r'CREATE\\s+VIEW') THEN 'view'
              WHEN REGEXP_CONTAINS(UPPER(sql_code), r'CREATE\\s+TRIGGER') THEN 'trigger'
              WHEN REGEXP_CONTAINS(UPPER(sql_code), r'CREATE\\s+TABLE') THEN 'ddl'
              WHEN REGEXP_CONTAINS(UPPER(sql_code), r'INSERT|UPDATE|DELETE') THEN 'dml'
              ELSE 'simple_sql'
            END as semantic_type,
            
            -- Contexto de negocio
            CASE
              WHEN REGEXP_CONTAINS(LOWER(CONCAT(object_name, sql_code)), r'venta|sale|factura|cliente') THEN 'ventas'
              WHEN REGEXP_CONTAINS(LOWER(CONCAT(object_name, sql_code)), r'inventario|stock|almacen') THEN 'inventario'
              WHEN REGEXP_CONTAINS(LOWER(CONCAT(object_name, sql_code)), r'pago|payment|cuenta|finanz') THEN 'finanzas'
              WHEN REGEXP_CONTAINS(LOWER(CONCAT(object_name, sql_code)), r'produccion|manufactura') THEN 'produccion'
              WHEN REGEXP_CONTAINS(LOWER(CONCAT(object_name, sql_code)), r'envio|shipping|logistic') THEN 'logistica'
              WHEN REGEXP_CONTAINS(LOWER(CONCAT(object_name, sql_code)), r'empleado|nomina|hr') THEN 'recursos_humanos'
              WHEN REGEXP_CONTAINS(LOWER(CONCAT(object_name, sql_code)), r'compra|proveedor|supplier') THEN 'compras'
              ELSE 'general'
            END as business_domain,
            
            -- Score de complejidad (simplificado)
            (LENGTH(sql_code) / 1000) + 
            (ARRAY_LENGTH(REGEXP_EXTRACT_ALL(UPPER(sql_code), r'JOIN')) * 2) +
            (ARRAY_LENGTH(REGEXP_EXTRACT_ALL(UPPER(sql_code), r'SELECT')) * 1) +
            (ARRAY_LENGTH(REGEXP_EXTRACT_ALL(UPPER(sql_code), r'WHERE')) * 0.5) as complexity_score
            
          FROM `{self.config.full_source_table_id}`
          WHERE sql_code IS NOT NULL
            AND LENGTH(sql_code) >= {self.config.MIN_CHUNK_SIZE}
        ),
        
        -- Paso 2: Chunking inteligente basado en tamaño y tipo
        chunked_objects AS (
          SELECT 
            *,
            -- Estrategia de chunking
            CASE 
              -- Objetos mega (>1M chars): chunking por separadores GO
              WHEN code_length > {self.config.MEGA_OBJECT_THRESHOLD} THEN 'mega_chunking'
              -- Objetos grandes: chunking por bloques semánticos
              WHEN code_length > {self.config.LARGE_OBJECT_THRESHOLD} THEN 'large_chunking'
              -- Objetos medianos: chunking por funciones
              WHEN code_length > {self.config.MEDIUM_OBJECT_THRESHOLD} THEN 'medium_chunking'
              -- Objetos pequeños: chunk único
              ELSE 'single_chunk'
            END as chunking_strategy,
            
            -- Generar chunks por LÍNEAS con traslape (estrategia robusta)
            CASE 
              -- MEGA: 400 líneas/chunk, traslape 80 líneas (20%), step 320
              WHEN code_length > {self.config.MEGA_OBJECT_THRESHOLD} THEN
                ARRAY(
                  SELECT ARRAY_TO_STRING(
                    ARRAY(
                      SELECT line 
                      FROM UNNEST(SPLIT(sql_code, '\\n')) AS line WITH OFFSET idx
                      WHERE idx BETWEEN start_line AND start_line + 399
                    ), 
                    '\\n'
                  ) as chunk
                  FROM UNNEST(GENERATE_ARRAY(0, ARRAY_LENGTH(SPLIT(sql_code, '\\n')) - 1, 320)) AS start_line
                  WHERE start_line <= ARRAY_LENGTH(SPLIT(sql_code, '\\n')) - 100
                  LIMIT {self.config.MAX_CHUNKS_PER_OBJECT}
                )
              
              -- LARGE: 250 líneas/chunk, traslape 50 líneas (20%), step 200
              WHEN code_length > {self.config.LARGE_OBJECT_THRESHOLD} THEN
                ARRAY(
                  SELECT ARRAY_TO_STRING(
                    ARRAY(
                      SELECT line
                      FROM UNNEST(SPLIT(sql_code, '\\n')) AS line WITH OFFSET idx
                      WHERE idx BETWEEN start_line AND start_line + 249
                    ),
                    '\\n'
                  ) as chunk
                  FROM UNNEST(GENERATE_ARRAY(0, ARRAY_LENGTH(SPLIT(sql_code, '\\n')) - 1, 200)) AS start_line
                  WHERE start_line <= ARRAY_LENGTH(SPLIT(sql_code, '\\n')) - 50
                  LIMIT {self.config.MAX_CHUNKS_PER_OBJECT}
                )
              
              -- MEDIUM: 200 líneas/chunk, traslape 40 líneas (20%), step 160
              WHEN code_length > {self.config.MEDIUM_OBJECT_THRESHOLD} THEN
                ARRAY(
                  SELECT ARRAY_TO_STRING(
                    ARRAY(
                      SELECT line
                      FROM UNNEST(SPLIT(sql_code, '\\n')) AS line WITH OFFSET idx
                      WHERE idx BETWEEN start_line AND start_line + 199
                    ),
                    '\\n'
                  ) as chunk
                  FROM UNNEST(GENERATE_ARRAY(0, ARRAY_LENGTH(SPLIT(sql_code, '\\n')) - 1, 160)) AS start_line
                  WHERE start_line <= ARRAY_LENGTH(SPLIT(sql_code, '\\n')) - 40
                  LIMIT 50
                )
              
              -- SMALL: chunk único
              ELSE [sql_code]
            END as raw_chunks
            
          FROM classified_objects
        ),
        
        -- Paso 3: Expandir chunks y generar metadatos
        expanded_chunks AS (
          SELECT 
            -- IDs únicos
            GENERATE_UUID() as chunk_id,
            CONCAT(server, '|', database, '|', schema, '|', object_name) as parent_object_id,
            
            -- Metadatos del objeto padre
            server, database, schema, object_name, object_type,
            semantic_type, business_domain, complexity_score,
            content_hash, last_modified,
            
            -- Metadatos del chunk
            chunk_content,
            pos as chunk_index,
            ARRAY_LENGTH(raw_chunks) as total_chunks,
            chunking_strategy,
            
            -- Información del chunk
            LENGTH(chunk_content) as chunk_length,
            ARRAY_LENGTH(SPLIT(chunk_content, '\\n')) as chunk_lines,
            
            -- Tags semánticos del chunk (RE2 compatible)
            ARRAY(
              SELECT tag FROM UNNEST([
                IF(REGEXP_CONTAINS(UPPER(chunk_content), r'SELECT'), 'query', NULL),
                IF(REGEXP_CONTAINS(UPPER(chunk_content), r'INSERT'), 'insert', NULL),
                IF(REGEXP_CONTAINS(UPPER(chunk_content), r'UPDATE'), 'update', NULL),
                IF(REGEXP_CONTAINS(UPPER(chunk_content), r'DELETE'), 'delete', NULL),
                IF(REGEXP_CONTAINS(UPPER(chunk_content), r'JOIN'), 'joins', NULL),
                IF(REGEXP_CONTAINS(UPPER(chunk_content), r'CURSOR'), 'cursor', NULL),
                IF(REGEXP_CONTAINS(UPPER(chunk_content), r'TRIGGER'), 'trigger', NULL),
                IF(REGEXP_CONTAINS(UPPER(chunk_content), r'TRANSACTION'), 'transactional', NULL)
              ]) AS tag
              WHERE tag IS NOT NULL
            ) as semantic_tags,
            
            -- Referencias extraídas (simplificado)
            ARRAY(
              SELECT DISTINCT ref 
              FROM UNNEST(REGEXP_EXTRACT_ALL(chunk_content, r'FROM\\s+([A-Za-z0-9_\\.\\[\\]]+)')) AS ref
              WHERE ref IS NOT NULL AND ref != ''
              LIMIT 10
            ) as references_to,
            
            -- Resumen semántico (simplificado)
            CONCAT(
              semantic_type, ' en ', object_name, 
              IF(business_domain != 'general', CONCAT(' (', business_domain, ')'), ''),
              ' - ', 
              CASE 
                WHEN REGEXP_CONTAINS(UPPER(chunk_content), r'SELECT') THEN 'consulta de datos'
                WHEN REGEXP_CONTAINS(UPPER(chunk_content), r'INSERT') THEN 'inserción de datos'
                WHEN REGEXP_CONTAINS(UPPER(chunk_content), r'UPDATE') THEN 'actualización de datos'
                WHEN REGEXP_CONTAINS(UPPER(chunk_content), r'DELETE') THEN 'eliminación de datos'
                ELSE 'lógica de negocio'
              END
            ) as semantic_summary
            
          FROM chunked_objects
          CROSS JOIN UNNEST(raw_chunks) AS chunk_content WITH OFFSET pos
          WHERE LENGTH(chunk_content) >= {self.config.MIN_CHUNK_SIZE}
        )
        
        -- Resultado final
        SELECT 
          chunk_id,
          parent_object_id,
          server,
          database,
          schema,
          object_name,
          object_type,
          chunk_content,
          chunking_strategy,
          chunk_index,
          total_chunks,
          semantic_type,
          business_domain,
          complexity_score,
          chunk_length,
          chunk_lines,
          semantic_tags,
          references_to,
          semantic_summary,
          content_hash,
          last_modified,
          CURRENT_TIMESTAMP() as created_at
          
        FROM expanded_chunks
        ORDER BY parent_object_id, chunk_index
        """
        
        # Ejecutar query
        job = self.client.query(create_chunks_sql)
        result = job.result()
        
        # Obtener estadísticas
        stats = self._get_chunks_statistics()
        
        logger.info("Tabla de chunks creada exitosamente")
        return stats
    
    def create_embeddings_table(self) -> Dict[str, Any]:
        """
        Crea la tabla de embeddings usando Vertex AI integrado.
        
        Returns:
            Estadísticas de la operación.
        """
        logger.info("Generando embeddings con Vertex AI...")
        
        # Crear modelo remoto para embeddings REALES con gemini-embedding-001
        create_model_sql = f"""
        CREATE OR REPLACE MODEL `{self.config.PROJECT_ID}.{self.config.DATASET_ID}.gemini_embedding_model`
        REMOTE WITH CONNECTION `{self.config.PROJECT_ID}.us-central1.vertex_ai_connection_central`
        OPTIONS(ENDPOINT = 'gemini-embedding-001')
        """
        
        logger.info("Creando modelo remoto de embeddings...")
        try:
            job = self.client.query(create_model_sql)
            job.result()
            logger.info("✅ Modelo remoto creado exitosamente")
        except Exception as e:
            logger.error("❌ Error creando modelo: %s", e)
            raise Exception(f"Fallo al crear modelo de embeddings. Verifica permisos: {e}")
        
        # Crear tabla con embeddings REALES usando ML.GENERATE_EMBEDDING
        create_embeddings_sql = f"""
        CREATE OR REPLACE TABLE `{self.config.full_embeddings_table_id}` AS
        SELECT 
          chunk_id, parent_object_id, server, database, schema,
          object_name, object_type, chunk_content, semantic_type,
          business_domain, semantic_summary, semantic_tags,
          complexity_score, chunk_index, total_chunks,
          created_at,
          CURRENT_TIMESTAMP() as embedding_created_at,
          content,
          ml_generate_embedding_result as embedding
        FROM ML.GENERATE_EMBEDDING(
          MODEL `{self.config.PROJECT_ID}.{self.config.DATASET_ID}.gemini_embedding_model`,
          (
            SELECT 
              chunk_id, parent_object_id, server, database, schema,
              object_name, object_type, chunk_content, semantic_type,
              business_domain, semantic_summary, semantic_tags,
              complexity_score, chunk_index, total_chunks, created_at,
              CONCAT(
                object_name, ' ',
                semantic_type, ' ',
                business_domain, ' ',
                semantic_summary, ' ',
                SUBSTR(chunk_content, 1, 6000)
              ) as content
            FROM `{self.config.full_chunks_table_id}`
            WHERE chunk_content IS NOT NULL
          ),
          STRUCT(TRUE AS flatten_json_output, 'CODE_RETRIEVAL_QUERY' AS task_type, 768 AS output_dimensionality)
        )
        """
        
        logger.info("Generando embeddings reales con Vertex AI...")
        # Ejecutar creación de embeddings
        job = self.client.query(create_embeddings_sql)
        job.result()
        
        logger.info("✅ Embeddings reales generados exitosamente")
        
        stats = self._get_embeddings_statistics()
        
        logger.info("Embeddings generados exitosamente")
        return stats
    
    def create_vector_index(self) -> Dict[str, Any]:
        """
        Crea el índice vectorial optimizado.
        
        Returns:
            Estadísticas del índice.
        """
        logger.info("Verificando si se puede crear índice vectorial...")
        
        # Verificar cantidad de rows (mínimo 5000 para IVF)
        count_sql = f"SELECT COUNT(*) as total FROM `{self.config.full_embeddings_table_id}`"
        count_result = list(self.client.query(count_sql))
        total_rows = count_result[0].total if count_result else 0
        
        if total_rows < 5000:
            logger.warning(f"Solo {total_rows} rows - mínimo 5000 requerido para índice IVF")
            logger.info("Usar VECTOR_SEARCH directamente sin índice para pruebas")
            return {
                "index_name": None,
                "status": "skipped",
                "reason": f"Insuficientes rows ({total_rows} < 5000)",
                "recommendation": "Usar VECTOR_SEARCH sin índice o esperar dataset completo"
            }
        
        create_index_sql = f"""
        CREATE VECTOR INDEX IF NOT EXISTS `{self.config.VECTOR_INDEX_NAME}`
        ON `{self.config.full_embeddings_table_id}`(embedding)
        OPTIONS (
          index_type = '{self.config.VECTOR_INDEX_TYPE}',
          distance_type = '{self.config.DISTANCE_TYPE}',
          ivf_options = '{{"num_lists": {self.config.IVF_NUM_LISTS}}}'
        )
        """
        
        job = self.client.query(create_index_sql)
        result = job.result()
        
        logger.info("Índice vectorial creado exitosamente")
        return {"index_name": self.config.VECTOR_INDEX_NAME, "status": "created"}
    
    def _get_chunks_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas de la tabla de chunks."""
        stats_sql = f"""
        SELECT 
          COUNT(*) as total_chunks,
          COUNT(DISTINCT parent_object_id) as unique_objects,
          AVG(chunk_length) as avg_chunk_length,
          AVG(total_chunks) as avg_chunks_per_object,
          COUNT(DISTINCT semantic_type) as semantic_types,
          COUNT(DISTINCT business_domain) as business_domains,
          MAX(complexity_score) as max_complexity,
          AVG(complexity_score) as avg_complexity
        FROM `{self.config.full_chunks_table_id}`
        """
        
        result = list(self.client.query(stats_sql))
        return dict(result[0]) if result else {}
    
    def _get_embeddings_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas de la tabla de embeddings."""
        stats_sql = f"""
        SELECT 
          COUNT(*) as total_embeddings,
          COUNT(DISTINCT parent_object_id) as unique_objects_with_embeddings,
          AVG(ARRAY_LENGTH(embedding)) as avg_embedding_dimensions
        FROM `{self.config.full_embeddings_table_id}`
        WHERE embedding IS NOT NULL
        """
        
        result = list(self.client.query(stats_sql))
        return dict(result[0]) if result else {}
    
    def get_chunking_report(self) -> Dict[str, Any]:
        """
        Genera reporte completo del proceso de chunking.
        
        Returns:
            Reporte detallado con estadísticas.
        """
        report_sql = f"""
        WITH chunk_stats AS (
          SELECT 
            chunking_strategy,
            semantic_type,
            business_domain,
            COUNT(*) as chunks_count,
            COUNT(DISTINCT parent_object_id) as objects_count,
            AVG(chunk_length) as avg_chunk_length,
            MIN(chunk_length) as min_chunk_length,
            MAX(chunk_length) as max_chunk_length,
            AVG(complexity_score) as avg_complexity
          FROM `{self.config.full_chunks_table_id}`
          GROUP BY chunking_strategy, semantic_type, business_domain
        )
        SELECT 
          chunking_strategy,
          semantic_type,
          business_domain,
          chunks_count,
          objects_count,
          ROUND(avg_chunk_length, 0) as avg_chunk_length,
          min_chunk_length,
          max_chunk_length,
          ROUND(avg_complexity, 2) as avg_complexity
        FROM chunk_stats
        ORDER BY chunks_count DESC
        """
        
        results = list(self.client.query(report_sql))
        
        return {
            "chunking_breakdown": [dict(row) for row in results],
            "summary": self._get_chunks_statistics()
        }
    
    def run_full_pipeline(
        self,
        skip_chunks: bool = False,
        skip_embeddings: bool = False,
        skip_index: bool = False
    ) -> str:
        """
        Ejecuta el pipeline completo con tracking robusto.
        
        Args:
            skip_chunks: Saltar creación de chunks.
            skip_embeddings: Saltar generación de embeddings.
            skip_index: Saltar creación de índice.
            
        Returns:
            run_id del pipeline ejecutado.
        """
        # Iniciar run
        run_id = self.tracker.start_run(
            pipeline_name="bigquery_vector_pipeline",
            metadata={
                "project": self.config.PROJECT_ID,
                "dataset": self.config.DATASET_ID,
                "skip_chunks": skip_chunks,
                "skip_embeddings": skip_embeddings,
                "skip_index": skip_index
            }
        )
        
        logger.info(f"🚀 Iniciando pipeline completo: {run_id}")
        
        try:
            # Etapa 1: Crear chunks
            if not skip_chunks:
                self._run_chunks_stage(run_id)
            else:
                logger.info("⏭️  Saltando creación de chunks")
            
            # Etapa 2: Generar embeddings
            if not skip_embeddings:
                self._run_embeddings_stage(run_id)
            else:
                logger.info("⏭️  Saltando generación de embeddings")
            
            # Etapa 3: Crear índice vectorial
            if not skip_index:
                self._run_index_stage(run_id)
            else:
                logger.info("⏭️  Saltando creación de índice")
            
            # Pipeline completado
            self.tracker.update_stage(
                run_id=run_id,
                stage="pipeline_complete",
                status="completed",
                progress=100.0,
                metadata={"completed_at": datetime.now().isoformat()}
            )
            
            logger.info(f"✅ Pipeline completado exitosamente: {run_id}")
            
            # Imprimir reporte
            self.tracker.print_progress_report(run_id)
            
            return run_id
            
        except Exception as e:
            logger.error(f"❌ Error en pipeline: {e}")
            self.tracker.fail_stage(
                run_id=run_id,
                stage="pipeline",
                error_message=str(e),
                error_traceback=traceback.format_exc()
            )
            raise
    
    def _run_chunks_stage(self, run_id: str):
        """Ejecuta la etapa de creación de chunks con tracking."""
        logger.info("📦 Etapa 1: Creando chunks inteligentes...")
        
        self.tracker.update_stage(
            run_id=run_id,
            stage="create_chunks",
            status="running",
            progress=0.0
        )
        
        try:
            start_time = datetime.now()
            
            # Crear chunks
            stats = self.create_chunks_table()
            
            duration = (datetime.now() - start_time).total_seconds()
            
            # Registrar métricas
            self.tracker.log_metric(run_id, "chunks_created", stats.get("total_chunks", 0), "create_chunks")
            self.tracker.log_metric(run_id, "unique_objects", stats.get("unique_objects", 0), "create_chunks")
            self.tracker.log_metric(run_id, "avg_chunk_length", stats.get("avg_chunk_length", 0), "create_chunks")
            self.tracker.log_metric(run_id, "duration_seconds", duration, "create_chunks", "timing")
            
            # Completar etapa
            self.tracker.complete_stage(
                run_id=run_id,
                stage="create_chunks",
                items_processed=stats.get("total_chunks", 0),
                metadata=stats
            )
            
            logger.info(f"✅ Chunks creados: {stats.get('total_chunks', 0)}")
            
        except Exception as e:
            self.tracker.fail_stage(
                run_id=run_id,
                stage="create_chunks",
                error_message=str(e),
                error_traceback=traceback.format_exc()
            )
            raise
    
    def _run_embeddings_stage(self, run_id: str):
        """Ejecuta la etapa de generación de embeddings con tracking."""
        logger.info("🔮 Etapa 2: Generando embeddings con Vertex AI...")
        
        self.tracker.update_stage(
            run_id=run_id,
            stage="create_embeddings",
            status="running",
            progress=0.0
        )
        
        try:
            start_time = datetime.now()
            
            # Generar embeddings
            stats = self.create_embeddings_table()
            
            duration = (datetime.now() - start_time).total_seconds()
            
            # Registrar métricas
            self.tracker.log_metric(run_id, "embeddings_created", stats.get("total_embeddings", 0), "create_embeddings")
            self.tracker.log_metric(run_id, "avg_embedding_dimensions", stats.get("avg_embedding_dimensions", 0), "create_embeddings")
            self.tracker.log_metric(run_id, "duration_seconds", duration, "create_embeddings", "timing")
            
            # Completar etapa
            self.tracker.complete_stage(
                run_id=run_id,
                stage="create_embeddings",
                items_processed=stats.get("total_embeddings", 0),
                metadata=stats
            )
            
            logger.info(f"✅ Embeddings generados: {stats.get('total_embeddings', 0)}")
            
        except Exception as e:
            self.tracker.fail_stage(
                run_id=run_id,
                stage="create_embeddings",
                error_message=str(e),
                error_traceback=traceback.format_exc()
            )
            raise
    
    def _run_index_stage(self, run_id: str):
        """Ejecuta la etapa de creación de índice con tracking."""
        logger.info("📊 Etapa 3: Creando índice vectorial...")
        
        self.tracker.update_stage(
            run_id=run_id,
            stage="create_index",
            status="running",
            progress=0.0
        )
        
        try:
            start_time = datetime.now()
            
            # Crear índice
            result = self.create_vector_index()
            
            duration = (datetime.now() - start_time).total_seconds()
            
            # Registrar métricas
            self.tracker.log_metric(run_id, "duration_seconds", duration, "create_index", "timing")
            
            # Completar o saltar etapa
            if result.get("status") == "skipped":
                self.tracker.update_stage(
                    run_id=run_id,
                    stage="create_index",
                    status="skipped",
                    progress=100.0,
                    metadata=result
                )
                logger.info(f"⏭️  Índice saltado: {result.get('reason')}")
            else:
                self.tracker.complete_stage(
                    run_id=run_id,
                    stage="create_index",
                    items_processed=1,
                    metadata=result
                )
                logger.info(f"✅ Índice creado: {result.get('index_name')}")
            
        except Exception as e:
            self.tracker.fail_stage(
                run_id=run_id,
                stage="create_index",
                error_message=str(e),
                error_traceback=traceback.format_exc()
            )
            raise
