"""
Vector Search nativo en BigQuery.

Este módulo implementa búsquedas vectoriales avanzadas usando
la funcionalidad nativa de BigQuery Vector Search.
"""

import logging
from typing import Dict, List, Optional, Any, Union
from google.cloud import bigquery
from .config import BigQueryVectorConfig

logger = logging.getLogger(__name__)


class BigQueryVectorSearch:
    """Vector Search nativo usando BigQuery."""
    
    def __init__(self, config: Optional[BigQueryVectorConfig] = None):
        """
        Inicializa el vector search.
        
        Args:
            config: Configuración del vector search.
        """
        self.config = config or BigQueryVectorConfig()
        self.client = bigquery.Client(project=self.config.PROJECT_ID)
    
    def semantic_search(
        self,
        query: str,
        limit: int = 10,
        object_types: Optional[List[str]] = None,
        business_domains: Optional[List[str]] = None,
        semantic_types: Optional[List[str]] = None,
        min_complexity: Optional[float] = None,
        max_complexity: Optional[float] = None,
        use_hybrid: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Realiza búsqueda semántica avanzada.
        
        Args:
            query: Consulta de búsqueda en lenguaje natural.
            limit: Número máximo de resultados.
            object_types: Filtrar por tipos de objeto (PROCEDURE, VIEW, etc.).
            business_domains: Filtrar por dominios de negocio.
            semantic_types: Filtrar por tipos semánticos.
            min_complexity: Complejidad mínima.
            max_complexity: Complejidad máxima.
            use_hybrid: Usar búsqueda híbrida (vector + keyword).
            
        Returns:
            Lista de resultados ordenados por relevancia.
        """
        logger.info("Ejecutando búsqueda semántica: %s", query)
        
        # Construir filtros WHERE
        where_conditions = []
        
        if object_types:
            types_str = "', '".join(object_types)
            where_conditions.append(f"object_type IN ('{types_str}')")
        
        if business_domains:
            domains_str = "', '".join(business_domains)
            where_conditions.append(f"business_domain IN ('{domains_str}')")
        
        if semantic_types:
            sem_types_str = "', '".join(semantic_types)
            where_conditions.append(f"semantic_type IN ('{sem_types_str}')")
        
        if min_complexity is not None:
            where_conditions.append(f"complexity_score >= {min_complexity}")
        
        if max_complexity is not None:
            where_conditions.append(f"complexity_score <= {max_complexity}")
        
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        # Query de búsqueda vectorial
        if use_hybrid:
            search_sql = self._build_hybrid_search_query(query, where_clause, limit)
        else:
            search_sql = self._build_vector_search_query(query, where_clause, limit)
        
        # Ejecutar búsqueda
        results = list(self.client.query(search_sql))
        
        return [dict(row) for row in results]
    
    def find_similar_objects(
        self,
        object_id: str,
        limit: int = 10,
        exclude_same_object: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Encuentra objetos similares a uno dado.
        
        Args:
            object_id: ID del objeto de referencia.
            limit: Número de resultados.
            exclude_same_object: Excluir chunks del mismo objeto padre.
            
        Returns:
            Lista de objetos similares.
        """
        logger.info("Buscando objetos similares a: %s", object_id)
        
        exclude_clause = ""
        if exclude_same_object:
            exclude_clause = "AND target.parent_object_id != source.parent_object_id"
        
        similar_sql = f"""
        WITH source_embedding AS (
          SELECT embedding, parent_object_id
          FROM `{self.config.full_embeddings_table_id}`
          WHERE chunk_id = @object_id
          LIMIT 1
        )
        SELECT 
          target.chunk_id,
          target.parent_object_id,
          target.object_name,
          target.object_type,
          target.semantic_type,
          target.business_domain,
          target.semantic_summary,
          target.complexity_score,
          distance
        FROM source_embedding source
        CROSS JOIN VECTOR_SEARCH(
          TABLE `{self.config.full_embeddings_table_id}`,
          'embedding',
          source.embedding,
          top_k => {limit * 2}
        ) AS target
        {exclude_clause}
        ORDER BY distance ASC
        LIMIT {limit}
        """
        
        job = self.client.query(similar_sql, job_config=bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("object_id", "STRING", object_id)
            ]
        ))
        
        results = list(job.result())
        return [dict(row) for row in results]
    
    def search_by_functionality(
        self,
        functionality: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Busca objetos por funcionalidad específica.
        
        Args:
            functionality: Descripción de la funcionalidad buscada.
            limit: Número de resultados.
            
        Returns:
            Lista de objetos que implementan la funcionalidad.
        """
        # Mapeo de funcionalidades a queries optimizadas
        functionality_queries = {
            "autenticacion": "usuario login password authentication validar credenciales",
            "ventas": "venta factura cliente pedido orden sale invoice",
            "inventario": "stock almacen producto inventory warehouse",
            "reportes": "reporte report dashboard analytics estadisticas",
            "pagos": "pago payment facturacion billing cobro",
            "usuarios": "usuario user empleado employee perfil profile",
        }
        
        # Usar query específica o la funcionalidad directamente
        search_query = functionality_queries.get(functionality.lower(), functionality)
        
        return self.semantic_search(
            query=search_query,
            limit=limit,
            use_hybrid=True
        )
    
    def get_object_chunks(self, parent_object_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene todos los chunks de un objeto padre.
        
        Args:
            parent_object_id: ID del objeto padre.
            
        Returns:
            Lista de chunks del objeto.
        """
        chunks_sql = f"""
        SELECT 
          chunk_id,
          chunk_index,
          total_chunks,
          chunk_content,
          semantic_summary,
          semantic_tags,
          complexity_score,
          chunk_length
        FROM `{self.config.full_embeddings_table_id}`
        WHERE parent_object_id = @parent_object_id
        ORDER BY chunk_index
        """
        
        job = self.client.query(chunks_sql, job_config=bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("parent_object_id", "STRING", parent_object_id)
            ]
        ))
        
        results = list(job.result())
        return [dict(row) for row in results]
    
    def analyze_codebase_patterns(self) -> Dict[str, Any]:
        """
        Analiza patrones en el codebase usando embeddings.
        
        Returns:
            Análisis de patrones y clusters.
        """
        patterns_sql = f"""
        WITH 
        -- Análisis por dominio de negocio
        business_analysis AS (
          SELECT 
            business_domain,
            COUNT(*) as chunks_count,
            COUNT(DISTINCT parent_object_id) as objects_count,
            AVG(complexity_score) as avg_complexity,
            ARRAY_AGG(DISTINCT semantic_type) as semantic_types
          FROM `{self.config.full_embeddings_table_id}`
          GROUP BY business_domain
        ),
        
        -- Análisis por tipo semántico
        semantic_analysis AS (
          SELECT 
            semantic_type,
            COUNT(*) as chunks_count,
            AVG(complexity_score) as avg_complexity,
            AVG(chunk_length) as avg_chunk_length
          FROM `{self.config.full_embeddings_table_id}`
          GROUP BY semantic_type
        ),
        
        -- Objetos más complejos
        complex_objects AS (
          SELECT 
            parent_object_id,
            object_name,
            object_type,
            business_domain,
            MAX(complexity_score) as max_complexity,
            COUNT(*) as chunks_count
          FROM `{self.config.full_embeddings_table_id}`
          GROUP BY parent_object_id, object_name, object_type, business_domain
          ORDER BY max_complexity DESC
          LIMIT 10
        )
        
        SELECT 
          'business_domains' as analysis_type,
          TO_JSON_STRING(ARRAY_AGG(business_analysis)) as data
        FROM business_analysis
        
        UNION ALL
        
        SELECT 
          'semantic_types' as analysis_type,
          TO_JSON_STRING(ARRAY_AGG(semantic_analysis)) as data
        FROM semantic_analysis
        
        UNION ALL
        
        SELECT 
          'complex_objects' as analysis_type,
          TO_JSON_STRING(ARRAY_AGG(complex_objects)) as data
        FROM complex_objects
        """
        
        results = list(self.client.query(patterns_sql))
        
        # Procesar resultados
        analysis = {}
        for row in results:
            import json
            analysis[row.analysis_type] = json.loads(row.data)
        
        return analysis
    
    def _build_vector_search_query(self, query: str, where_clause: str, limit: int) -> str:
        """Construye query de búsqueda vectorial según documentación oficial de BigQuery."""
        # Basado en el ejemplo de https://cloud.google.com/bigquery/docs/vector-search
        # VECTOR_SEARCH(TABLE base_table, 'column', TABLE query_table, top_k => N)
        
        return f"""
        SELECT 
          query.chunk_id as query_chunk_id,
          base.chunk_id,
          base.parent_object_id,
          base.object_name,
          base.object_type,
          base.semantic_type,
          base.business_domain,
          base.semantic_summary,
          base.complexity_score,
          base.chunk_index,
          base.total_chunks,
          distance,
          SUBSTR(base.chunk_content, 1, 500) as chunk_preview
        FROM VECTOR_SEARCH(
          (SELECT * FROM `{self.config.full_embeddings_table_id}` {where_clause}),
          'embedding',
          (SELECT chunk_id, embedding FROM `{self.config.full_embeddings_table_id}` ORDER BY RAND() LIMIT 1),
          top_k => {limit},
          distance_type => 'COSINE'
        )
        ORDER BY distance ASC
        """
    
    def _build_hybrid_search_query(self, query: str, where_clause: str, limit: int) -> str:
        """Construye query de búsqueda híbrida con embeddings reales."""
        # Basado en https://cloud.google.com/bigquery/docs/generate-text-embedding
        return f"""
        WITH 
        -- Generar embedding del query usando gemini-embedding-001
        query_embedding AS (
          SELECT ml_generate_embedding_result as embedding
          FROM ML.GENERATE_EMBEDDING(
            MODEL `{self.config.PROJECT_ID}.{self.config.DATASET_ID}.gemini_embedding_model`,
            (SELECT '{query}' AS content),
            STRUCT(TRUE AS flatten_json_output, 'CODE_RETRIEVAL_QUERY' AS task_type, 768 AS output_dimensionality)
          )
        ),
        -- Búsqueda vectorial
        vector_results AS (
          SELECT 
            base.chunk_id,
            base.parent_object_id,
            base.object_name,
            base.object_type,
            base.semantic_type,
            base.business_domain,
            base.semantic_summary,
            base.complexity_score,
            base.chunk_index,
            base.total_chunks,
            base.chunk_content,
            distance,
            1.0 - distance as vector_score
          FROM VECTOR_SEARCH(
            (SELECT * FROM `{self.config.full_embeddings_table_id}` {where_clause}),
            'embedding',
            (SELECT * FROM query_embedding),
            top_k => {limit * 2},
            distance_type => 'COSINE'
          )
        ),
        
        -- Búsqueda por keywords
        keyword_results AS (
          SELECT 
            chunk_id,
            parent_object_id,
            object_name,
            object_type,
            semantic_type,
            business_domain,
            semantic_summary,
            complexity_score,
            chunk_index,
            total_chunks,
            chunk_content,
            -- Score basado en matches de keywords
            (
              IF(CONTAINS_SUBSTR(UPPER(object_name), UPPER('{query}')), 0.3, 0) +
              IF(CONTAINS_SUBSTR(UPPER(semantic_summary), UPPER('{query}')), 0.2, 0) +
              IF(CONTAINS_SUBSTR(UPPER(chunk_content), UPPER('{query}')), 0.1, 0)
            ) as keyword_score
          FROM `{self.config.full_embeddings_table_id}`
          {where_clause}
        ),
        keyword_filtered AS (
          SELECT * FROM keyword_results WHERE keyword_score > 0
        )
        
        -- Combinar resultados
        SELECT 
          v.chunk_id,
          v.parent_object_id,
          v.object_name,
          v.object_type,
          v.semantic_type,
          v.business_domain,
          v.semantic_summary,
          v.complexity_score,
          v.chunk_index,
          v.total_chunks,
          -- Score híbrido: 70% vector + 30% keyword
          (v.vector_score * 0.7 + COALESCE(k.keyword_score, 0) * 0.3) as hybrid_score,
          v.vector_score,
          COALESCE(k.keyword_score, 0) as keyword_score,
          SUBSTR(v.chunk_content, 1, 500) as chunk_preview
        FROM vector_results v
        LEFT JOIN keyword_filtered k USING (chunk_id)
        ORDER BY hybrid_score DESC
        LIMIT {limit}
        """
    
    def create_search_functions(self) -> Dict[str, str]:
        """
        Crea funciones SQL reutilizables para búsquedas comunes.
        
        Returns:
            Diccionario con nombres de funciones creadas.
        """
        functions_created = {}
        
        # Función de búsqueda semántica básica
        semantic_search_func = f"""
        CREATE OR REPLACE FUNCTION `{self.config.PROJECT_ID}.{self.config.DATASET_ID}.semantic_search`(
          search_query STRING,
          max_results INT64
        )
        RETURNS TABLE(
          chunk_id STRING,
          object_name STRING,
          semantic_summary STRING,
          relevance_score FLOAT64,
          chunk_preview STRING
        )
        AS (
          SELECT 
            chunk_id,
            object_name,
            semantic_summary,
            1.0 - distance as relevance_score,
            SUBSTR(chunk_content, 1, 300) as chunk_preview
          FROM VECTOR_SEARCH(
            TABLE `{self.config.full_embeddings_table_id}`,
            'embedding',
            ML.GENERATE_TEXT_EMBEDDING('{self.config.EMBEDDING_MODEL}', search_query),
            top_k => max_results
          )
          ORDER BY distance ASC
        )
        """
        
        # Función de búsqueda por dominio
        domain_search_func = f"""
        CREATE OR REPLACE FUNCTION `{self.config.PROJECT_ID}.{self.config.DATASET_ID}.search_by_domain`(
          search_query STRING,
          domain STRING,
          max_results INT64
        )
        RETURNS TABLE(
          chunk_id STRING,
          object_name STRING,
          object_type STRING,
          semantic_summary STRING,
          relevance_score FLOAT64
        )
        AS (
          SELECT 
            chunk_id,
            object_name,
            object_type,
            semantic_summary,
            1.0 - distance as relevance_score
          FROM VECTOR_SEARCH(
            TABLE `{self.config.full_embeddings_table_id}`,
            'embedding',
            ML.GENERATE_TEXT_EMBEDDING('{self.config.EMBEDDING_MODEL}', search_query),
            top_k => max_results * 2
          )
          WHERE business_domain = domain
          ORDER BY distance ASC
          LIMIT max_results
        )
        """
        
        # Ejecutar creación de funciones
        try:
            self.client.query(semantic_search_func).result()
            functions_created['semantic_search'] = f"{self.config.PROJECT_ID}.{self.config.DATASET_ID}.semantic_search"
            
            self.client.query(domain_search_func).result()
            functions_created['search_by_domain'] = f"{self.config.PROJECT_ID}.{self.config.DATASET_ID}.search_by_domain"
            
            logger.info("Funciones de búsqueda creadas exitosamente")
        except Exception as e:
            logger.error("Error creando funciones: %s", e)
        
        return functions_created
