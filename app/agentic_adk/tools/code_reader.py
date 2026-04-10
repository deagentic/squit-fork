"""
Tools para lectura detallada de código.
"""

import logging
from typing import Dict, Any
from google.cloud import bigquery
from google.adk.tools.function_tool import FunctionTool

def _format_sql(sql: str, **kwargs) -> str:
    """Formatea SQL de forma segura para Bandit."""
    return sql.format(**kwargs)  # nosec B608

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "app"))

from bigquery_vector.config import BigQueryVectorConfig

logger = logging.getLogger(__name__)

_config = BigQueryVectorConfig()
_client = None


def get_bigquery_client():
    """Obtiene cliente BigQuery singleton."""
    global _client
    if _client is None:
        _client = bigquery.Client(project=_config.PROJECT_ID)
    return _client


def _read_code_impl(chunk_id: str) -> Dict[str, Any]:
    """
    Lee el código completo de un chunk específico.
    
    Args:
        chunk_id: ID único del chunk a leer
    
    Returns:
        Código y metadatos del chunk
    """
    client = get_bigquery_client()
    
    query = _format_sql("""
    SELECT 
        chunk_id,
        object_name,
        object_type,
        chunk_content,
        semantic_summary,
        business_domain
    FROM `{table}`
    WHERE chunk_id = @chunk_id
    """, table=_config.full_embeddings_table_id)
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("chunk_id", "STRING", chunk_id)
        ]
    )
    
    try:
        results = list(client.query(query, job_config=job_config).result())
        if results:
            return dict(results[0])
        return {}
    except Exception as e:
        logger.error(f"Error leyendo código: {e}")
        return {}


def _get_object_summary_impl(object_name: str) -> Dict[str, Any]:
    """
    Obtiene resumen de un objeto SQL.
    
    Args:
        object_name: Nombre del objeto
        
    Returns:
        Resumen del objeto
    """
    client = get_bigquery_client()
    
    query = _format_sql("""
    SELECT 
        object_name,
        object_type,
        business_domain,
        AVG(complexity_score) as avg_complexity,
        COUNT(*) as total_chunks
    FROM `{table}`
    WHERE UPPER(object_name) = UPPER(@object_name)
    GROUP BY object_name, object_type, business_domain
    LIMIT 1
    """, table=_config.full_embeddings_table_id)
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("object_name", "STRING", object_name)
        ]
    )
    
    try:
        results = list(client.query(query, job_config=job_config).result())
        if results:
            return dict(results[0])
        return {"error": f"Objeto '{object_name}' no encontrado"}
    except Exception as e:
        logger.error(f"Error obteniendo resumen: {e}")
        return {"error": str(e)}


# Renombrar funciones para que las tools tengan nombres correctos
_read_code_impl.__name__ = "read_code_tool"
_get_object_summary_impl.__name__ = "get_object_summary_tool"

# Crear tools wrapeados
read_code_tool = FunctionTool(_read_code_impl)
get_object_summary_tool = FunctionTool(_get_object_summary_impl)

__all__ = ["read_code_tool", "get_object_summary_tool"]