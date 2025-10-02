"""
BigQuery Vector Search - Módulo nativo para embeddings y búsqueda vectorial.

Este módulo implementa chunking inteligente y vector search 100% en BigQuery,
eliminando la necesidad de sistemas externos como Weaviate para casos de uso estándar.
"""

from .chunking_pipeline import BigQueryChunkingPipeline
from .vector_search import BigQueryVectorSearch
from .config import BigQueryVectorConfig

__all__ = [
    "BigQueryChunkingPipeline",
    "BigQueryVectorSearch", 
    "BigQueryVectorConfig",
]
