"""
Schemas de validación con Pydantic.

Define modelos para validar requests, responses y configuración.
"""

from .search_request import SearchRequest, SearchResponse

__all__ = [
    'SearchRequest',
    'SearchResponse',
]

