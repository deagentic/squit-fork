"""
Configuración del cliente BigQuery.

Este módulo contiene todas las configuraciones y constantes
utilizadas por el cliente SQUIT.
"""

import os
from typing import List, Optional


class Config:
    """Configuración centralizada del cliente SQUIT."""

    # Configuración de BigQuery
    PROJECT_ID: str = "dfor-prj-dev"
    DATASET_ID: str = "deacero_sql_objects"
    TABLE_ID: str = "sql_objects_code"

    # Límites de consulta
    DEFAULT_QUERY_LIMIT: int = 1000
    MAX_QUERY_LIMIT: int = 50000
    MIN_QUERY_LIMIT: int = 1

    # Configuración de exportación
    DEFAULT_EXPORT_FORMAT: str = "csv"
    SUPPORTED_EXPORT_FORMATS: List[str] = ["csv", "json", "parquet"]

    # Configuración de búsqueda
    DEFAULT_SEARCH_COLUMNS: List[str] = ["object_name", "sql_code"]
    MAX_SEARCH_RESULTS: int = 10000

    # Configuración de logging
    DEFAULT_LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    @property
    def full_table_id(self) -> str:
        """
        Retorna el ID completo de la tabla BigQuery.

        Returns:
            String con formato: project.dataset.table
        """
        return f"{self.PROJECT_ID}.{self.DATASET_ID}.{self.TABLE_ID}"

    @classmethod
    def get_credentials_path(cls, custom_path: Optional[str] = None) -> Optional[str]:
        """
        Obtiene la ruta de las credenciales de Google Cloud.

        Args:
            custom_path: Ruta personalizada a las credenciales.

        Returns:
            Ruta a las credenciales o None si no se encuentra.
        """
        if custom_path and os.path.exists(custom_path):
            return custom_path

        # Verificar variable de entorno
        env_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if env_path and os.path.exists(env_path):
            return env_path

        # Buscar en ubicaciones comunes
        common_paths = [
            "credentials.json",
            "config/credentials.json",
            "/tmp/credentials.json",  # Para Docker
            os.path.expanduser("~/.config/gcloud/application_default_credentials.json"),
        ]

        for path in common_paths:
            if os.path.exists(path):
                return path

        return None

    @classmethod
    def validate_query_limit(cls, limit: int) -> int:
        """
        Valida y ajusta el límite de consulta.

        Args:
            limit: Límite propuesto.

        Returns:
            Límite validado.

        Raises:
            ValueError: Si el límite está fuera del rango permitido.
        """
        if limit < cls.MIN_QUERY_LIMIT:
            raise ValueError(f"Límite mínimo: {cls.MIN_QUERY_LIMIT}")

        if limit > cls.MAX_QUERY_LIMIT:
            raise ValueError(f"Límite máximo: {cls.MAX_QUERY_LIMIT}")

        return limit

    @classmethod
    def validate_export_format(cls, format_type: str) -> str:
        """
        Valida el formato de exportación.

        Args:
            format_type: Formato propuesto (case-insensitive).

        Returns:
            Formato validado en minúsculas.

        Raises:
            ValueError: Si el formato no está soportado.
        """
        normalized_format = format_type.lower()
        if normalized_format not in cls.SUPPORTED_EXPORT_FORMATS:
            raise ValueError(
                f"Formato '{format_type}' no soportado. "
                f"Formatos disponibles: {cls.SUPPORTED_EXPORT_FORMATS}"
            )

        return normalized_format
