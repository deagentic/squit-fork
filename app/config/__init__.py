"""
Configuración centralizada para SQUIT.

Incluye:
- Configuración por entorno (dev/staging/prod)
- Gestión de secretos con Google Secret Manager
- Variables de ambiente
"""

from .environments import Environment, EnvironmentConfig

__all__ = [
    'Environment',
    'EnvironmentConfig',
]

