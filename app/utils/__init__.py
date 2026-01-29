"""
Utilidades para el sistema SQUIT.

Incluye:
- Retry logic con backoff exponencial
- Rate limiting
- Circuit breaker
- Logging estructurado
- Métricas
- Connection pooling
"""

from .retry import retry_with_backoff

__all__ = [
    'retry_with_backoff',
]

