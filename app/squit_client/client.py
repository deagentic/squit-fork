"""
Cliente principal para acceder a BigQuery.

Este módulo contiene la implementación principal del cliente
para interactuar con la tabla de objetos SQL en BigQuery.
"""

import logging
from typing import Any, Dict, List, Optional

import pandas as pd
from google.api_core import exceptions as gcp_exceptions
from google.cloud import bigquery
from google.oauth2 import service_account

from .config import Config
from .exceptions import (
    AuthenticationError,
    ConfigurationError,
    ConnectionError,
    ExportError,
    QueryError,
    ValidationError,
)

logger = logging.getLogger(__name__)


class BigQueryClient:
    """
    Cliente para acceder a la tabla sql_objects_code en BigQuery.

    Este cliente proporciona métodos para consultar, analizar y exportar
    datos de objetos SQL almacenados en BigQuery de manera eficiente
    y segura.

    Attributes:
        config: Configuración del cliente.

    Example:
        >>> client = BigQueryClient()
        >>> stats = client.get_statistics()
        >>> print(f"Total objetos: {stats['total_objects']:,}")
    """

    def __init__(self, credentials_path: Optional[str] = None) -> None:
        """
        Inicializa el cliente BigQuery.

        Args:
            credentials_path: Ruta al archivo JSON de credenciales.
                Si no se proporciona, usa GOOGLE_APPLICATION_CREDENTIALS.

        Raises:
            AuthenticationError: Si no se pueden cargar credenciales.
            ConnectionError: Si no se puede conectar a BigQuery.
        """
        self.config = Config()
        self._client: Optional[bigquery.Client] = None
        self._initialize_client(credentials_path)

    def _initialize_client(self, credentials_path: Optional[str]) -> None:
        """
        Inicializa el cliente BigQuery con credenciales apropiadas.

        Args:
            credentials_path: Ruta opcional a las credenciales.

        Raises:
            AuthenticationError: Si falla la inicialización.
        """
        try:
            creds_path = self.config.get_credentials_path(credentials_path)

            if creds_path:
                self._initialize_with_service_account(creds_path)
            else:
                self._initialize_with_default_credentials()

        except Exception as e:
            raise AuthenticationError(
                f"Error al inicializar cliente BigQuery: {e}"
            ) from e

    def _initialize_with_service_account(self, creds_path: str) -> None:
        """Inicializa cliente con cuenta de servicio."""
        credentials = service_account.Credentials.from_service_account_file(creds_path)
        self._client = bigquery.Client(
            credentials=credentials, project=self.config.PROJECT_ID
        )
        logger.info("Cliente inicializado con credenciales desde: %s", creds_path)

    def _initialize_with_default_credentials(self) -> None:
        """Inicializa cliente con credenciales por defecto."""
        self._client = bigquery.Client(project=self.config.PROJECT_ID)
        logger.info("Cliente inicializado con credenciales por defecto")

    @property
    def client(self) -> bigquery.Client:
        """
        Retorna el cliente BigQuery.

        Returns:
            Cliente BigQuery inicializado.

        Raises:
            ConnectionError: Si el cliente no está inicializado.
        """
        if self._client is None:
            raise ConnectionError("Cliente BigQuery no inicializado")
        return self._client

    def get_table_info(self) -> Dict[str, Any]:
        """
        Obtiene información básica de la tabla.

        Returns:
            Diccionario con metadatos de la tabla.

        Raises:
            ConnectionError: Si no se puede acceder a la tabla.
        """
        try:
            table = self.client.get_table(self.config.full_table_id)

            return {
                "table_id": table.table_id,
                "project": table.project,
                "dataset": table.dataset_id,
                "num_rows": table.num_rows,
                "num_bytes": table.num_bytes,
                "created": table.created,
                "modified": table.modified,
                "location": table.location,
                "schema": [
                    (field.name, field.field_type, field.description or "")
                    for field in table.schema
                ],
            }
        except gcp_exceptions.NotFound as e:
            raise ConnectionError(
                f"Tabla no encontrada: {self.config.full_table_id}"
            ) from e
        except Exception as e:
            raise ConnectionError(
                f"Error obteniendo información de la tabla: {e}"
            ) from e

    def execute_query(
        self,
        query: str,
        limit: Optional[int] = None,
        dry_run: bool = False,
    ) -> pd.DataFrame:
        """
        Ejecuta una consulta SQL personalizada.

        Args:
            query: Consulta SQL a ejecutar.
            limit: Límite opcional de filas.
            dry_run: Si True, solo valida la consulta sin ejecutarla.

        Returns:
            DataFrame con los resultados.

        Raises:
            QueryError: Si hay error en la consulta.
            ValidationError: Si los parámetros son inválidos.
        """
        try:
            validated_query = self._prepare_query(query, limit)
            job_config = bigquery.QueryJobConfig(dry_run=dry_run)
            query_job = self.client.query(validated_query, job_config=job_config)

            if dry_run:
                self._log_dry_run_results(query_job)
                return pd.DataFrame()

            return self._process_query_results(query_job)

        except gcp_exceptions.BadRequest as e:
            raise QueryError(f"Error en la consulta SQL: {e}") from e
        except ValidationError:
            raise
        except Exception as e:
            raise QueryError(f"Error ejecutando consulta: {e}") from e

    def _prepare_query(self, query: str, limit: Optional[int]) -> str:
        """
        Prepara y valida la consulta SQL.

        Args:
            query: Consulta SQL original.
            limit: Límite opcional de filas.

        Returns:
            Consulta SQL preparada.

        Raises:
            ValidationError: Si los parámetros son inválidos.
        """
        if not query.strip():
            raise ValidationError("La consulta no puede estar vacía")

        if limit is not None:
            validated_limit = self.config.validate_query_limit(limit)
            return f"{query.rstrip(';')} LIMIT {validated_limit}"

        return query.rstrip(";")

    def _log_dry_run_results(self, query_job: bigquery.QueryJob) -> None:
        """Log de resultados de dry run."""
        bytes_processed = query_job.total_bytes_processed or 0
        logger.info("Consulta validada. Bytes procesados: %s", f"{bytes_processed:,}")

    def _process_query_results(self, query_job: bigquery.QueryJob) -> pd.DataFrame:
        """
        Procesa los resultados de la consulta.

        Args:
            query_job: Trabajo de consulta de BigQuery.

        Returns:
            DataFrame con los resultados.
        """
        results = query_job.result()
        df = results.to_dataframe()
        logger.info("Consulta ejecutada exitosamente. Filas: %s", f"{len(df):,}")
        return df

    def get_sample_data(self, limit: int = 10) -> pd.DataFrame:
        """
        Obtiene una muestra de datos de la tabla.

        Args:
            limit: Número de filas a retornar.

        Returns:
            DataFrame con la muestra de datos.

        Raises:
            ValidationError: Si el límite es inválido.
        """
        validated_limit = self.config.validate_query_limit(limit)

        query = f"""
        SELECT *
        FROM `{self.config.full_table_id}`
        ORDER BY last_modified DESC
        LIMIT {validated_limit}
        """
        return self.execute_query(query)

    def search_objects(
        self,
        search_term: str,
        search_columns: Optional[List[str]] = None,
        object_types: Optional[List[str]] = None,
        servers: Optional[List[str]] = None,
        limit: int = 100,
    ) -> pd.DataFrame:
        """
        Busca objetos SQL por término de búsqueda.

        Args:
            search_term: Término a buscar.
            search_columns: Columnas donde buscar.
            object_types: Filtrar por tipos de objeto.
            servers: Filtrar por servidores.
            limit: Límite de resultados.

        Returns:
            DataFrame con los resultados de búsqueda.

        Raises:
            ValidationError: Si los parámetros son inválidos.
        """
        if not search_term.strip():
            raise ValidationError("El término de búsqueda no puede estar vacío")

        validated_limit = self.config.validate_query_limit(limit)
        columns = search_columns or self.config.DEFAULT_SEARCH_COLUMNS

        where_clause = self._build_search_where_clause(
            search_term, columns, object_types, servers
        )

        query = f"""
        SELECT
            server,
            database,
            schema,
            object_name,
            object_type,
            last_modified,
            SUBSTR(sql_code, 1, 200) as sql_preview
        FROM `{self.config.full_table_id}`
        WHERE {where_clause}
        ORDER BY last_modified DESC
        LIMIT {validated_limit}
        """

        return self.execute_query(query)

    def _build_search_where_clause(
        self,
        search_term: str,
        columns: List[str],
        object_types: Optional[List[str]],
        servers: Optional[List[str]],
    ) -> str:
        """
        Construye la cláusula WHERE para búsqueda.

        Args:
            search_term: Término a buscar.
            columns: Columnas donde buscar.
            object_types: Tipos de objeto para filtrar.
            servers: Servidores para filtrar.

        Returns:
            Cláusula WHERE completa.
        """
        # Condiciones de búsqueda por término
        search_conditions = [f"{column} LIKE '%{search_term}%'" for column in columns]
        where_clauses = [f"({' OR '.join(search_conditions)})"]

        # Filtros adicionales
        if object_types:
            types_filter = self._build_in_clause("object_type", object_types)
            where_clauses.append(types_filter)

        if servers:
            servers_filter = self._build_in_clause("server", servers)
            where_clauses.append(servers_filter)

        return " AND ".join(where_clauses)

    def _build_in_clause(self, column: str, values: List[str]) -> str:
        """
        Construye cláusula IN para filtros.

        Args:
            column: Nombre de la columna.
            values: Valores para el filtro.

        Returns:
            Cláusula IN formateada.
        """
        escaped_values = "', '".join(values)
        return f"{column} IN ('{escaped_values}')"

    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas generales de la tabla.

        Returns:
            Diccionario con estadísticas clave.
        """
        query = f"""
        SELECT
            COUNT(*) as total_objects,
            COUNT(DISTINCT server) as unique_servers,
            COUNT(DISTINCT database) as unique_databases,
            COUNT(DISTINCT object_type) as unique_object_types,
            MIN(last_modified) as oldest_modification,
            MAX(last_modified) as newest_modification
        FROM `{self.config.full_table_id}`
        """

        df = self.execute_query(query)
        return df.iloc[0].to_dict() if not df.empty else {}

    def get_top_objects_by_type(self, limit: int = 10) -> pd.DataFrame:
        """
        Obtiene los tipos de objetos más comunes.

        Args:
            limit: Número de tipos a retornar.

        Returns:
            DataFrame con tipos y estadísticas.
        """
        validated_limit = self.config.validate_query_limit(limit)

        query = f"""
        SELECT
            object_type,
            COUNT(*) as count,
            ROUND(
                COUNT(*) * 100.0 / (
                    SELECT COUNT(*)
                    FROM `{self.config.full_table_id}`
                ),
                2
            ) as percentage
        FROM `{self.config.full_table_id}`
        GROUP BY object_type
        ORDER BY count DESC
        LIMIT {validated_limit}
        """
        return self.execute_query(query)

    def get_top_servers(self, limit: int = 10) -> pd.DataFrame:
        """
        Obtiene los servidores con más objetos.

        Args:
            limit: Número de servidores a retornar.

        Returns:
            DataFrame con servidores y estadísticas.
        """
        validated_limit = self.config.validate_query_limit(limit)

        query = f"""
        SELECT
            server,
            COUNT(*) as object_count,
            COUNT(DISTINCT database) as database_count,
            COUNT(DISTINCT object_type) as object_type_count
        FROM `{self.config.full_table_id}`
        GROUP BY server
        ORDER BY object_count DESC
        LIMIT {validated_limit}
        """
        return self.execute_query(query)

    def export_data(
        self,
        query: str,
        filename: str,
        format_type: str = "csv",
    ) -> bool:
        """
        Exporta resultados de consulta a archivo.

        Args:
            query: Consulta SQL a ejecutar.
            filename: Nombre del archivo de salida.
            format_type: Formato de exportación.

        Returns:
            True si la exportación fue exitosa.

        Raises:
            ConfigurationError: Si el formato no está soportado.
            ExportError: Si falla la exportación.
        """
        try:
            validated_format = self.config.validate_export_format(format_type)
            df = self.execute_query(query)

            if df.empty:
                logger.warning("No hay datos para exportar")
                return False

            self._export_dataframe(df, filename, validated_format)
            logger.info("Datos exportados exitosamente a %s", filename)
            return True

        except (ConfigurationError, QueryError):
            raise
        except Exception as e:
            raise ExportError(f"Error exportando datos: {e}") from e

    def _export_dataframe(
        self, df: pd.DataFrame, filename: str, format_type: str
    ) -> None:
        """
        Exporta DataFrame al formato especificado.

        Args:
            df: DataFrame a exportar.
            filename: Nombre del archivo.
            format_type: Formato de exportación.

        Raises:
            ExportError: Si el formato no se puede procesar.
        """
        export_methods = {
            "csv": lambda: df.to_csv(filename, index=False),
            "json": lambda: df.to_json(filename, orient="records", indent=2),
            "parquet": lambda: df.to_parquet(filename, index=False),
        }

        export_method = export_methods.get(format_type)
        if not export_method:
            raise ExportError(f"Método de exportación no implementado: {format_type}")

        export_method()

    def get_object_details(self, object_name: str, server: str) -> pd.DataFrame:
        """
        Obtiene detalles completos de un objeto específico.

        Args:
            object_name: Nombre del objeto SQL.
            server: Servidor donde se encuentra.

        Returns:
            DataFrame con detalles del objeto.

        Raises:
            ValidationError: Si los parámetros son inválidos.
        """
        if not object_name.strip() or not server.strip():
            raise ValidationError("object_name y server son requeridos")

        query = f"""
        SELECT *
        FROM `{self.config.full_table_id}`
        WHERE object_name = '{object_name}'
        AND server = '{server}'
        ORDER BY last_modified DESC
        """

        return self.execute_query(query)

    def get_objects_by_database(
        self, server: str, database: str, limit: int = 100
    ) -> pd.DataFrame:
        """
        Obtiene objetos de una base de datos específica.

        Args:
            server: Nombre del servidor.
            database: Nombre de la base de datos.
            limit: Límite de resultados.

        Returns:
            DataFrame con objetos de la base de datos.
        """
        validated_limit = self.config.validate_query_limit(limit)

        query = f"""
        SELECT
            schema,
            object_name,
            object_type,
            last_modified,
            SUBSTR(sql_code, 1, 100) as sql_preview
        FROM `{self.config.full_table_id}`
        WHERE server = '{server}'
        AND database = '{database}'
        ORDER BY object_type, object_name
        LIMIT {validated_limit}
        """

        return self.execute_query(query)

    def validate_connection(self) -> bool:
        """
        Valida la conexión a BigQuery.

        Returns:
            True si la conexión es exitosa.

        Raises:
            ConnectionError: Si falla la validación.
        """
        try:
            # Consulta simple para validar conexión
            query = f"SELECT 1 as test FROM `{self.config.full_table_id}` LIMIT 1"
            result = self.execute_query(query)
            return not result.empty
        except Exception as e:
            raise ConnectionError(f"Error validando conexión: {e}") from e
