"""
Tools para análisis de dependencias.
"""

import logging
from typing import Dict, Any, List
from google.cloud import bigquery
from google.adk.tools.function_tool import FunctionTool

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


def _find_dependencies_impl(object_name: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Encuentra qué objetos SQL usan o dependen de un objeto específico.
    
    Esta herramienta es crítica para análisis de impacto: antes de modificar
    una tabla o procedimiento, úsala para saber qué se puede romper.
    
    Args:
        object_name: Nombre del objeto a analizar (ej: ClientesMaster, sp_ProcesarVentas)
        limit: Máximo de dependencias a retornar (default: 20)
    
    Returns:
        Lista de objetos que dependen del objeto especificado:
        - dependent_object: Nombre del objeto dependiente
        - object_type: Tipo de objeto dependiente
        - business_domain: Dominio
        - how_used: Cómo lo usa (SELECT, INSERT, UPDATE, etc.)
        - criticality: Nivel de criticidad (basado en complejidad y uso)
    """
    client = get_bigquery_client()
    
    query = f"""
    WITH dependencies AS (
        SELECT 
            object_name as dependent_object,
            object_type,
            business_domain,
            complexity_score,
            semantic_tags,
            CASE 
                WHEN ARRAY_LENGTH(REGEXP_EXTRACT_ALL(chunk_content, CONCAT('(?i)', @object_name))) > 5 THEN 'HIGH'
                WHEN ARRAY_LENGTH(REGEXP_EXTRACT_ALL(chunk_content, CONCAT('(?i)', @object_name))) > 2 THEN 'MEDIUM'
                ELSE 'LOW'
            END as usage_frequency,
            CASE 
                WHEN 'INSERT' IN UNNEST(semantic_tags) OR 'UPDATE' IN UNNEST(semantic_tags) THEN 'WRITE'
                WHEN 'SELECT' IN UNNEST(semantic_tags) OR 'query' IN UNNEST(semantic_tags) THEN 'READ'
                ELSE 'REFERENCE'
            END as how_used
        FROM `{_config.full_embeddings_table_id}`
        WHERE UPPER(chunk_content) LIKE CONCAT('%', UPPER(@object_name), '%')
        AND object_name != @object_name
    )
    SELECT 
        dependent_object,
        object_type,
        business_domain,
        how_used,
        usage_frequency,
        CASE 
            WHEN complexity_score > 8 AND usage_frequency = 'HIGH' THEN 'CRITICAL'
            WHEN complexity_score > 5 OR usage_frequency != 'LOW' THEN 'MEDIUM'
            ELSE 'LOW'
        END as criticality,
        ROUND(complexity_score, 2) as complexity_score
    FROM dependencies
    ORDER BY 
        CASE criticality WHEN 'CRITICAL' THEN 1 WHEN 'MEDIUM' THEN 2 ELSE 3 END,
        complexity_score DESC
    LIMIT @limit
    """
    
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("object_name", "STRING", object_name),
            bigquery.ScalarQueryParameter("limit", "INT64", limit)
        ]
    )
    
    try:
        results = client.query(query, job_config=job_config).result()
        deps = [dict(row) for row in results]
        
        logger.info(f"Dependencias de '{object_name}': {len(deps)} encontradas")
        return deps
        
    except Exception as e:
        logger.error(f"Error buscando dependencias: {e}")
        return []


# Renombrar función
_find_dependencies_impl.__name__ = "find_dependencies_tool"

# Crear tool wrapeado
find_dependencies_tool = FunctionTool(_find_dependencies_impl)


def _analyze_impact_impl(object_name: str) -> Dict[str, Any]:
    """
    Analiza el impacto potencial de modificar un objeto SQL.
    
    Genera un reporte ejecutivo del riesgo de cambiar una tabla, procedimiento
    o vista, mostrando todos los objetos afectados clasificados por criticidad.
    
    Args:
        object_name: Nombre del objeto a analizar
    
    Returns:
        Reporte de impacto con:
        - total_dependencies: Total de objetos afectados
        - critical_count: Objetos críticos afectados
        - medium_count: Objetos de riesgo medio
        - low_count: Objetos de bajo riesgo
        - by_type: Distribución por tipo de objeto
        - by_domain: Distribución por dominio de negocio
        - top_critical: Lista de objetos más críticos
        - recommendation: Recomendación de si es seguro modificar
    """
    # Obtener dependencias
    deps = _find_dependencies_impl(object_name, limit=100)
    
    if not deps:
        return {
            "total_dependencies": 0,
            "recommendation": "SAFE - No se encontraron dependencias conocidas",
            "note": "Siempre validar en ambientes de prueba antes de producción"
        }
    
    # Analizar distribución
    critical = [d for d in deps if d['criticality'] == 'CRITICAL']
    medium = [d for d in deps if d['criticality'] == 'MEDIUM']
    low = [d for d in deps if d['criticality'] == 'LOW']
    
    # Por tipo
    from collections import Counter
    by_type = dict(Counter(d['object_type'] for d in deps))
    by_domain = dict(Counter(d['business_domain'] for d in deps))
    
    # Recomendación
    if len(critical) > 0:
        recommendation = "⚠️ ALTO RIESGO - Revisar objetos críticos antes de modificar"
    elif len(medium) > 3:
        recommendation = "⚠️ RIESGO MEDIO - Pruebas exhaustivas recomendadas"
    else:
        recommendation = "✅ RIESGO BAJO - Cambios controlados son seguros"
    
    return {
        "object_analyzed": object_name,
        "total_dependencies": len(deps),
        "critical_count": len(critical),
        "medium_count": len(medium),
        "low_count": len(low),
        "by_type": by_type,
        "by_domain": by_domain,
        "top_critical": [
            {
                "object": d['dependent_object'],
                "type": d['object_type'],
                "domain": d['business_domain'],
                "how_used": d['how_used']
            }
            for d in critical[:5]
        ],
        "recommendation": recommendation
    }


# Renombrar función
_analyze_impact_impl.__name__ = "analyze_impact_tool"

# Crear tool wrapeado
analyze_impact_tool = FunctionTool(_analyze_impact_impl)
