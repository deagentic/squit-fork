"""
Tests unitarios para el cliente BigQuery.

Este módulo contiene tests comprensivos para verificar
la funcionalidad del cliente SQUIT.
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
import pytest
from google.api_core import exceptions as gcp_exceptions

sys.path.insert(0, str(Path(__file__).parent.parent))

from squit_client.client import BigQueryClient
from squit_client.config import Config
from squit_client.exceptions import (
    AuthenticationError,
    ConnectionError,
    ExportError,
    QueryError,
    ValidationError,
)


class TestBigQueryClientInitialization:
    """Tests para la inicialización del cliente."""

    @patch("squit_client.client.bigquery.Client")
    @patch("squit_client.client.service_account.Credentials.from_service_account_file")
    def test_init_with_credentials_file(self, mock_credentials, mock_client):
        """Test inicialización con archivo de credenciales."""
        mock_credentials.return_value = Mock()
        mock_client.return_value = Mock()

        with patch.object(
            Config, "get_credentials_path", return_value="test_creds.json"
        ):
            client = BigQueryClient()
            assert client._client is not None
            mock_credentials.assert_called_once_with("test_creds.json")

    @patch("squit_client.client.bigquery.Client")
    def test_init_with_default_credentials(self, mock_client):
        """Test inicialización con credenciales por defecto."""
        mock_client.return_value = Mock()

        with patch.object(Config, "get_credentials_path", return_value=None):
            client = BigQueryClient()
            assert client._client is not None
            mock_client.assert_called_once_with(project="dfor-prj-dev")

    @patch("squit_client.client.service_account.Credentials.from_service_account_file")
    def test_init_authentication_error(self, mock_credentials):
        """Test error de autenticación durante inicialización."""
        mock_credentials.side_effect = Exception("Credenciales inválidas")

        with patch.object(
            Config, "get_credentials_path", return_value="invalid_creds.json"
        ):
            with pytest.raises(AuthenticationError):
                BigQueryClient()

    def test_client_property_not_initialized(self):
        """Test error cuando el cliente no está inicializado."""
        client = BigQueryClient.__new__(BigQueryClient)
        client._client = None

        with pytest.raises(ConnectionError, match="Cliente BigQuery no inicializado"):
            _ = client.client


class TestBigQueryClientTableOperations:
    """Tests para operaciones de tabla."""

    def test_get_table_info_success(self, squit_client, mock_table_info):
        """Test obtención exitosa de información de tabla."""
        squit_client._client.get_table.return_value = mock_table_info

        info = squit_client.get_table_info()

        assert info["table_id"] == "test_table"
        assert info["num_rows"] == 1000
        assert len(info["schema"]) == 1
        assert info["schema"][0] == ("test_column", "STRING", "Test description")

    def test_get_table_info_not_found(self, squit_client):
        """Test error cuando la tabla no existe."""
        squit_client._client.get_table.side_effect = gcp_exceptions.NotFound(
            "Tabla no encontrada"
        )

        with pytest.raises(ConnectionError, match="Tabla no encontrada"):
            squit_client.get_table_info()

    def test_validate_connection_success(self, squit_client, mock_query_job):
        """Test validación exitosa de conexión."""
        squit_client._client.query.return_value = mock_query_job

        result = squit_client.validate_connection()

        assert result is True

    def test_validate_connection_failure(self, squit_client):
        """Test falla en validación de conexión."""
        squit_client._client.query.side_effect = Exception("Error de conexión")

        with pytest.raises(ConnectionError, match="Error validando conexión"):
            squit_client.validate_connection()


class TestBigQueryClientQueries:
    """Tests para operaciones de consulta."""

    def test_execute_query_success(
        self, squit_client, mock_query_job, sample_dataframe
    ):
        """Test ejecución exitosa de consulta."""
        squit_client._client.query.return_value = mock_query_job

        result_df = squit_client.execute_query("SELECT * FROM test_table")

        pd.testing.assert_frame_equal(result_df, sample_dataframe)
        squit_client._client.query.assert_called_once()

    def test_execute_query_with_limit(self, squit_client, mock_query_job):
        """Test ejecución de consulta con límite."""
        squit_client._client.query.return_value = mock_query_job

        squit_client.execute_query("SELECT * FROM test_table", limit=100)

        call_args = squit_client._client.query.call_args[0][0]
        assert "LIMIT 100" in call_args

    def test_execute_query_limit_exceeded(self, squit_client):
        """Test error cuando el límite excede el máximo permitido."""
        with pytest.raises(QueryError, match="Límite máximo"):
            squit_client.execute_query("SELECT * FROM test_table", limit=100000)

    def test_execute_query_empty_query(self, squit_client):
        """Test error con consulta vacía."""
        with pytest.raises(ValidationError, match="La consulta no puede estar vacía"):
            squit_client.execute_query("")

    def test_execute_query_bad_request(self, squit_client):
        """Test error de consulta SQL inválida."""
        squit_client._client.query.side_effect = gcp_exceptions.BadRequest(
            "SQL inválido"
        )

        with pytest.raises(QueryError, match="Error en la consulta SQL"):
            squit_client.execute_query("INVALID SQL")

    def test_execute_query_dry_run(self, squit_client):
        """Test ejecución en modo dry run."""
        mock_job = Mock()
        mock_job.total_bytes_processed = 1000
        squit_client._client.query.return_value = mock_job

        result = squit_client.execute_query("SELECT * FROM test", dry_run=True)

        assert result.empty


class TestBigQueryClientSearchOperations:
    """Tests para operaciones de búsqueda."""

    def test_search_objects_basic(self, squit_client, mock_query_job):
        """Test búsqueda básica de objetos."""
        squit_client._client.query.return_value = mock_query_job

        squit_client.search_objects("test_proc")

        squit_client._client.query.assert_called_once()
        call_args = squit_client._client.query.call_args[0][0]
        assert "test_proc" in call_args

    def test_search_objects_empty_term(self, squit_client):
        """Test error con término de búsqueda vacío."""
        with pytest.raises(
            ValidationError, match="El término de búsqueda no puede estar vacío"
        ):
            squit_client.search_objects("")

    def test_search_objects_with_filters(self, squit_client, mock_query_job):
        """Test búsqueda con filtros adicionales."""
        squit_client._client.query.return_value = mock_query_job

        squit_client.search_objects(
            "test", object_types=["PROCEDURE"], servers=["SERVER1"]
        )

        call_args = squit_client._client.query.call_args[0][0]
        assert "object_type IN ('PROCEDURE')" in call_args
        assert "server IN ('SERVER1')" in call_args

    def test_get_sample_data(self, squit_client, mock_query_job):
        """Test obtención de muestra de datos."""
        squit_client._client.query.return_value = mock_query_job

        result_df = squit_client.get_sample_data(5)

        assert not result_df.empty
        call_args = squit_client._client.query.call_args[0][0]
        assert "ORDER BY last_modified DESC" in call_args
        assert "LIMIT 5" in call_args

    def test_get_object_details(self, squit_client, mock_query_job):
        """Test obtención de detalles de objeto específico."""
        squit_client._client.query.return_value = mock_query_job

        result = squit_client.get_object_details("test_proc", "SERVER1")

        assert not result.empty
        call_args = squit_client._client.query.call_args[0][0]
        assert "object_name = 'test_proc'" in call_args
        assert "server = 'SERVER1'" in call_args

    def test_get_object_details_empty_params(self, squit_client):
        """Test error con parámetros vacíos."""
        with pytest.raises(
            ValidationError, match="object_name y server son requeridos"
        ):
            squit_client.get_object_details("", "SERVER1")


class TestBigQueryClientStatistics:
    """Tests para operaciones de estadísticas."""

    def test_get_statistics(self, squit_client, mock_query_job):
        """Test obtención de estadísticas."""
        # Mock DataFrame con estadísticas
        stats_df = pd.DataFrame(
            {"total_objects": [1000], "unique_servers": [5], "unique_databases": [10]}
        )
        mock_query_job.dataframe = stats_df
        squit_client._client.query.return_value = mock_query_job

        stats = squit_client.get_statistics()

        assert stats["total_objects"] == 1000
        assert stats["unique_servers"] == 5
        assert stats["unique_databases"] == 10

    def test_get_top_objects_by_type(self, squit_client, mock_query_job):
        """Test obtención de top tipos de objetos."""
        squit_client._client.query.return_value = mock_query_job

        result = squit_client.get_top_objects_by_type(5)

        assert not result.empty
        call_args = squit_client._client.query.call_args[0][0]
        assert "GROUP BY object_type" in call_args
        assert "LIMIT 5" in call_args

    def test_get_top_servers(self, squit_client, mock_query_job):
        """Test obtención de top servidores."""
        squit_client._client.query.return_value = mock_query_job

        result = squit_client.get_top_servers(3)

        assert not result.empty
        call_args = squit_client._client.query.call_args[0][0]
        assert "GROUP BY server" in call_args
        assert "LIMIT 3" in call_args


class TestBigQueryClientExport:
    """Tests para operaciones de exportación."""

    def test_export_data_csv_success(self, squit_client, mock_query_job, tmp_path):
        """Test exportación exitosa a CSV."""
        squit_client._client.query.return_value = mock_query_job
        output_file = tmp_path / "test_output.csv"

        result = squit_client.export_data("SELECT * FROM test", str(output_file), "csv")

        assert result is True
        assert output_file.exists()

    def test_export_data_invalid_format(self, squit_client):
        """Test error con formato de exportación inválido."""
        with pytest.raises(ExportError, match="Formato 'invalid' no soportado"):
            squit_client.export_data("SELECT * FROM test", "output.txt", "invalid")

    def test_export_data_empty_results(self, squit_client):
        """Test exportación con resultados vacíos."""
        mock_job = Mock()
        empty_df = pd.DataFrame()
        mock_result = Mock()
        mock_result.to_dataframe.return_value = empty_df
        mock_job.result.return_value = mock_result
        squit_client._client.query.return_value = mock_job

        result = squit_client.export_data("SELECT * FROM test", "output.csv")

        assert result is False


class TestConfig:
    """Tests para la configuración."""

    def test_full_table_id(self):
        """Test generación del ID completo de tabla."""
        config = Config()
        expected = f"{config.PROJECT_ID}.{config.DATASET_ID}.{config.TABLE_ID}"
        assert config.full_table_id == expected

    @patch("os.path.exists")
    def test_get_credentials_path_custom(self, mock_exists):
        """Test obtención de ruta de credenciales personalizada."""
        mock_exists.return_value = True

        result = Config.get_credentials_path("custom_path.json")

        assert result == "custom_path.json"
        mock_exists.assert_called_with("custom_path.json")

    def test_validate_query_limit_valid(self):
        """Test validación de límite válido."""
        result = Config.validate_query_limit(1000)
        assert result == 1000

    def test_validate_query_limit_too_high(self):
        """Test error con límite muy alto."""
        with pytest.raises(ValueError, match="Límite máximo"):
            Config.validate_query_limit(100000)

    def test_validate_query_limit_too_low(self):
        """Test error con límite muy bajo."""
        with pytest.raises(ValueError, match="Límite mínimo"):
            Config.validate_query_limit(0)

    def test_validate_export_format_valid(self):
        """Test validación de formato válido."""
        result = Config.validate_export_format("CSV")
        assert result == "csv"

    def test_validate_export_format_invalid(self):
        """Test error con formato inválido."""
        with pytest.raises(ValueError, match="Formato 'invalid' no soportado"):
            Config.validate_export_format("invalid")


class TestBigQueryClientPrivateMethods:
    """Tests para métodos privados del cliente."""

    def test_build_search_where_clause(self, squit_client):
        """Test construcción de cláusula WHERE."""
        where_clause = squit_client._build_search_where_clause(
            search_term="test",
            columns=["col1", "col2"],
            object_types=["PROCEDURE"],
            servers=["SERVER1"],
        )

        assert "col1 LIKE '%test%'" in where_clause
        assert "col2 LIKE '%test%'" in where_clause
        assert "object_type IN ('PROCEDURE')" in where_clause
        assert "server IN ('SERVER1')" in where_clause

    def test_build_in_clause(self, squit_client):
        """Test construcción de cláusula IN."""
        result = squit_client._build_in_clause("column", ["val1", "val2"])
        expected = "column IN ('val1', 'val2')"
        assert result == expected

    def test_prepare_query_with_limit(self, squit_client):
        """Test preparación de consulta con límite."""
        query = "SELECT * FROM test"
        result = squit_client._prepare_query(query, 100)
        assert result == "SELECT * FROM test LIMIT 100"

    def test_prepare_query_empty(self, squit_client):
        """Test error con consulta vacía."""
        with pytest.raises(ValidationError, match="La consulta no puede estar vacía"):
            squit_client._prepare_query("", None)
