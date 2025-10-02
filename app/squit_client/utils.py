"""
Utilidades y funciones auxiliares para el cliente SQUIT.

Este módulo contiene funciones de utilidad que son reutilizadas
en diferentes partes del sistema.
"""

import logging
import os
import warnings
from contextlib import contextmanager, redirect_stderr
from io import StringIO
from typing import Generator, List


def setup_logging(level: str = "INFO") -> None:
    """
    Configura el sistema de logging para SQUIT.

    Args:
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def suppress_warnings() -> None:
    """
    Suprime warnings específicos de BigQuery y gRPC.

    Esta función configura el entorno para suprimir warnings
    que no afectan la funcionalidad pero pueden confundir
    a los usuarios finales.
    """
    # Suprimir warnings de BigQuery Storage
    warnings.filterwarnings(
        "ignore", category=UserWarning, module="google.cloud.bigquery"
    )
    warnings.filterwarnings("ignore", message=".*BigQuery Storage.*")

    # Configurar logging de librerías externas
    logging.getLogger("grpc").setLevel(logging.ERROR)
    logging.getLogger("google.auth").setLevel(logging.ERROR)
    logging.getLogger("google.cloud").setLevel(logging.ERROR)

    # Variables de entorno para gRPC
    os.environ.update(
        {
            "GRPC_VERBOSITY": "ERROR",
            "GLOG_minloglevel": "3",
            "GRPC_TRACE": "",
        }
    )


@contextmanager
def capture_stderr() -> Generator[StringIO, None, None]:
    """
    Context manager para capturar stderr.

    Yields:
        StringIO object con el contenido capturado.
    """
    stderr_capture = StringIO()
    with redirect_stderr(stderr_capture):
        yield stderr_capture


def filter_important_errors(stderr_content: str) -> List[str]:
    """
    Filtra errores importantes del output de stderr.

    Args:
        stderr_content: Contenido capturado de stderr.

    Returns:
        Lista de errores importantes.
    """
    if not stderr_content:
        return []

    lines = stderr_content.split("\n")
    excluded_patterns = [
        "ALTS creds ignored",
        "absl::InitializeLog",
        "BigQuery Storage module",
        "WARNING: All log messages before",
    ]

    return [
        line
        for line in lines
        if line and not any(pattern in line for pattern in excluded_patterns)
    ]


def format_number(number: int) -> str:
    """
    Formatea números con separadores de miles.

    Args:
        number: Número a formatear.

    Returns:
        Número formateado como string.
    """
    return f"{number:,}"


def truncate_text(text: str, max_length: int = 50) -> str:
    """
    Trunca texto a una longitud máxima.

    Args:
        text: Texto a truncar.
        max_length: Longitud máxima.

    Returns:
        Texto truncado con "..." si es necesario.
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def validate_file_path(file_path: str) -> bool:
    """
    Valida que una ruta de archivo sea válida.

    Args:
        file_path: Ruta del archivo a validar.

    Returns:
        True si la ruta es válida.
    """
    try:
        # Verificar que el directorio padre existe o se puede crear
        parent_dir = os.path.dirname(file_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
        return True
    except (OSError, PermissionError):
        return False
