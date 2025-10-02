"""
Configuración de pytest para los tests de SQUIT.

Este archivo contiene fixtures y configuraciones compartidas
para todos los tests del proyecto.
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from squit_client.client import BigQueryClient
from squit_client.config import Config


@pytest.fixture
def mock_config():
    """Fixture que proporciona una configuración mock."""
    config = Config()
    config.PROJECT_ID = "test-project"
    config.DATASET_ID = "test_dataset"
    config.TABLE_ID = "test_table"
    return config


@pytest.fixture
def mock_bigquery_client():
    """Fixture que proporciona un cliente BigQuery mock."""
    with patch("squit_client.client.bigquery.Client") as mock_client:
        yield mock_client


@pytest.fixture
def mock_service_account():
    """Fixture que proporciona credenciales de cuenta de servicio mock."""
    with patch(
        "squit_client.client.service_account.Credentials.from_service_account_file"
    ) as mock_creds:
        mock_creds.return_value = Mock()
        yield mock_creds


@pytest.fixture
def sample_dataframe():
    """Fixture que proporciona un DataFrame de ejemplo."""
    return pd.DataFrame(
        {
            "server": ["SERVER1", "SERVER2"],
            "database": ["DB1", "DB2"],
            "object_name": ["proc1", "proc2"],
            "object_type": ["PROCEDURE", "PROCEDURE"],
            "count": [100, 200],
        }
    )


@pytest.fixture
def mock_table_info():
    """Fixture que proporciona información mock de tabla BigQuery."""
    mock_table = Mock()
    mock_table.table_id = "test_table"
    mock_table.project = "test_project"
    mock_table.dataset_id = "test_dataset"
    mock_table.num_rows = 1000
    mock_table.num_bytes = 50000
    mock_table.created = "2024-01-01"
    mock_table.modified = "2024-01-02"
    mock_table.location = "US"

    # Mock del schema
    mock_field = Mock()
    mock_field.name = "test_column"
    mock_field.field_type = "STRING"
    mock_field.description = "Test description"
    mock_table.schema = [mock_field]

    return mock_table


@pytest.fixture
def squit_client(mock_bigquery_client, mock_config):
    """Fixture que proporciona un cliente SQUIT configurado para testing."""
    with patch.object(Config, "get_credentials_path", return_value=None):
        client = BigQueryClient()
        client.config = mock_config
        client._client = mock_bigquery_client
        return client


class MockQueryJob:
    """Mock para trabajos de consulta BigQuery."""

    def __init__(self, dataframe: pd.DataFrame, total_bytes: int = 1000):
        self.dataframe = dataframe
        self.total_bytes_processed = total_bytes

    def result(self):
        """Mock del método result."""
        mock_result = Mock()
        mock_result.to_dataframe.return_value = self.dataframe
        return mock_result


@pytest.fixture
def mock_query_job(sample_dataframe):
    """Fixture que proporciona un trabajo de consulta mock."""
    return MockQueryJob(sample_dataframe)
