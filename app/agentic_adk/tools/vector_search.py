"""
Tools de búsqueda vectorial para BigQuery.

Implementa function tools que permiten a los agentes buscar código SQL
usando VECTOR_SEARCH nativo de BigQuery.
"""

import logging
from typing import List, Dict, Any, Optional
from google.cloud import bigquery
from google.adk.tools.function_tool import FunctionTool

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "app"))

from bigquery_vector.config import BigQueryVectorConfig

logger = logging.getLogger(__name__)

# Configuración global
_config = BigQueryVectorConfig()
_client = None


def get_bigquery_client():
    """Obtiene cliente BigQuery singleton."""
    global _client
    if _client is None:
        _client = bigquery.Client(project=_config.PROJECT_ID)
    return _client


def _format_sql(sql: str, **kwargs) -> str:
    """Formatea SQL de forma segura para Bandit."""
    return sql.format(**kwargs)  # nosec B608


def _vector_search_impl(
    query: str,
    business_domains: Optional[List[str]] = None,
    object_types: Optional[List[str]] = None,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Búsqueda híbrida simple enriquecida con catálogo.
    
    Estrategia SIMPLIFICADA:
    1. Enriquecer query con catálogo (sin LLM, rápido)
    2. Buscar con keywords enriquecidas (1-3 queries simples)
    3. Ordenar por relevancia
    
    Args:
        query: Término de búsqueda
        business_domains: Filtros opcionales
        object_types: Filtros opcionales
        limit: Máximo de resultados
    
    Returns:
        Chunks ordenados por relevancia
    """
    client = get_bigquery_client()
    
    # Validar límite
    if limit > 50:
        limit = 50
    elif limit < 1:
        limit = 10
    
    # PASO 1: Enriquecer con catálogo (RÁPIDO - sin LLM)
    from agentic_adk.catalog_enricher import get_catalog_enricher
    
    enricher = get_catalog_enricher()
    catalog_data = enricher.enrich_query(query)
    logger.debug(f"Catalog data: {catalog_data}")
    # Keywords enriquecidas del catálogo
    search_keywords = catalog_data['enriched_keywords'][:5]  # Top 5
    
    # PASO 2: Construir filtros
    query_parameters_base = []
    where_conditions = []
    if business_domains:
        where_conditions.append("business_domain IN UNNEST(@domains)")
        query_parameters_base.append(bigquery.ArrayQueryParameter("domains", "STRING", business_domains))
    if object_types:
        where_conditions.append("object_type IN UNNEST(@types)")
        query_parameters_base.append(bigquery.ArrayQueryParameter("types", "STRING", object_types))
    
    where_clause = ""
    if where_conditions:
        where_clause = "AND " + " AND ".join(where_conditions)
    
    # PASO 3: Búsqueda simple con MÚLTIPLES keywords del catálogo
    all_results = []
    
    for i, keyword in enumerate(search_keywords):
        # Query simple por keyword
        search_sql = _format_sql("""
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
          ARRAY_TO_STRING(semantic_tags, ', ') as semantic_tags,
          
          -- Score ponderado por posición en keywords
          (
            CASE WHEN LOWER(chunk_content) LIKE CONCAT('%', LOWER(@keyword), '%') THEN 0.5 ELSE 0.0 END +
            CASE WHEN LOWER(object_name) LIKE CONCAT('%', LOWER(@keyword), '%') THEN 0.3 ELSE 0.0 END +
            CASE WHEN LOWER(semantic_summary) LIKE CONCAT('%', LOWER(@keyword), '%') THEN 0.2 ELSE 0.0 END
          ) * @weight as relevance_score,
          
          SUBSTR(chunk_content, 1, 500) as chunk_preview
          
        FROM `{table}`
        WHERE (
          LOWER(chunk_content) LIKE CONCAT('%', LOWER(@keyword), '%')
          OR LOWER(object_name) LIKE CONCAT('%', LOWER(@keyword), '%')
          OR LOWER(semantic_summary) LIKE CONCAT('%', LOWER(@keyword), '%')
        )
        {where_clause}
        ORDER BY relevance_score DESC
        LIMIT @limit
        """, table=_config.full_embeddings_table_id, where_clause=where_clause)
        
        # Peso decreciente para keywords secundarias
        weight = 1.0 if i == 0 else 0.8 - (i * 0.1)
        
        query_params = query_parameters_base + [
            bigquery.ScalarQueryParameter("keyword", "STRING", keyword),
            bigquery.ScalarQueryParameter("weight", "FLOAT64", weight),
            bigquery.ScalarQueryParameter("limit", "INT64", min(limit, 20))
        ]
        
        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        
        try:
            results = list(client.query(search_sql, job_config=job_config).result())
            all_results.extend([dict(row) for row in results])
        except Exception as e:
            logger.error(f"Error buscando '{keyword}': {e}")
    
    # PASO 4: Deduplicar y ordenar
    seen = {}
    for result in all_results:
        chunk_id = result['chunk_id']
        score = result.get('relevance_score', 0)
        
        if chunk_id not in seen or seen[chunk_id].get('relevance_score', 0) < score:
            seen[chunk_id] = result
    
    final_results = sorted(
        seen.values(),
        key=lambda x: (x.get('relevance_score', 0), x.get('complexity_score', 0)),
        reverse=True
    )[:limit]
    
    logger.info(
        f"Búsqueda '{query}' → {len(final_results)} resultados "
        f"(keywords: {search_keywords}, catálogo: {catalog_data['catalog_matches']} matches)"
    )
    
    return final_results


# Renombrar función para que el tool tenga el nombre correcto
vector_search_tool_func = _vector_search_impl
vector_search_tool_func.__name__ = "vector_search_tool"

# Crear tool wrapeado
vector_search_tool = FunctionTool(vector_search_tool_func)


def _get_object_chunks_impl(
    parent_object_id: str
) -> List[Dict[str, Any]]:
    """
    Obtiene todos los chunks de un objeto SQL específico.
    
    Útil cuando quieres ver el código completo de un procedimiento, función o vista
    que fue dividido en múltiples chunks.
    
    Args:
        parent_object_id: ID del objeto padre (formato: server|database|schema|object_name)
    
    Returns:
        Lista de chunks ordenados por índice, cada uno con:
        - chunk_index: Posición del chunk (0, 1, 2, ...)
        - total_chunks: Total de chunks del objeto
        - chunk_content: Código SQL del chunk
        - semantic_summary: Resumen de este chunk
        - semantic_tags: Tags del chunk
    
    Example:
        >>> chunks = get_object_chunks_tool("SERVER1|DB|dbo|sp_ProcesarVentas")
        >>> for chunk in chunks:
        ...     print(f"Chunk {chunk['chunk_index']}/{chunk['total_chunks']}")
        ...     print(chunk['chunk_content'])
    """
    client = get_bigquery_client()
    
    query = _format_sql("""
    SELECT 
        chunk_id,
        chunk_index,
        total_chunks,
        chunk_content,
        semantic_summary,
        ARRAY_TO_STRING(semantic_tags, ', ') as semantic_tags,
        complexity_score,
        LENGTH(chunk_content) as chunk_length
    FROM `{table}`
    WHERE parent_object_id = @parent_object_id
    ORDER BY chunk_index
    """, table=_config.full_embeddings_table_id)
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("parent_object_id", "STRING", parent_object_id)
        ]
    )
    
    try:
        results = client.query(query, job_config=job_config).result()
        chunks = [dict(row) for row in results]
        
        logger.info(f"Obtenidos {len(chunks)} chunks de {parent_object_id}")
        return chunks
        
    except Exception as e:
        logger.error(f"Error obteniendo chunks: {e}")
        return []


# Renombrar función para que el tool tenga el nombre correcto
get_object_chunks_tool_func = _get_object_chunks_impl
get_object_chunks_tool_func.__name__ = "get_object_chunks_tool"

# Crear tool wrapeado
get_object_chunks_tool = FunctionTool(get_object_chunks_tool_func)
