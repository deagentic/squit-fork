"""
SQUIT - SQL Objects BigQuery Client.

Un cliente Python profesional para acceder y consultar objetos SQL
almacenados en BigQuery. Diseñado específicamente para la tabla
dfor-prj-dev.deacero_sql_objects.sql_objects_code.

Ejemplo de uso:
    >>> from squit_client import BigQueryClient
    >>> client = BigQueryClient()
    >>> stats = client.get_statistics()
    >>> print(f"Total objetos: {stats['total_objects']:,}")
"""

__version__ = "1.0.0"
__author__ = "Grupo DeAcero"
__email__ = "ktouma@deacero.com"

from .client import BigQueryClient
from .config import Config
from .exceptions import (
    AuthenticationError,
    ConfigurationError,
    ConnectionError,
    ExportError,
    QueryError,
    SquitError,
    ValidationError,
)

__all__ = [
    "BigQueryClient",
    "Config",
    "SquitError",
    "ConnectionError",
    "QueryError",
    "AuthenticationError",
    "ConfigurationError",
    "ValidationError",
    "ExportError",
]
