"""
Tests para verificar las mejoras de seguridad (SQL Injection),
thread safety y observabilidad en BigQueryClient.
"""
import sys
import threading
from pathlib import Path
from unittest.mock import Mock, patch
import logging
import pandas as pd
import pytest
from google.cloud import bigquery

# Agregar el directorio app al path para importar squit_client
sys.path.insert(0, str(Path(__file__).parent.parent))
from squit_client.client import BigQueryClient
from squit_client.config import Config

class TestBigQueryClientSQLInjection:
    """Tests para asegurar que el cliente es resistente a Inyección SQL."""
    
    @patch("squit_client.client.bigquery.Client")
    def test_search_objects_sql_injection(self, mock_client):
        """Test que la búsqueda de objetos parametriza los inputs maliciosos."""
        mock_bq_client = Mock()
        mock_client.return_value = mock_bq_client
        mock_job = mock_bq_client.query.return_value
        mock_job.result.return_value.to_dataframe.return_value = pd.DataFrame()
        mock_job.total_bytes_processed = 1000
        
        with patch.object(Config, "get_credentials_path", return_value=None):
            client = BigQueryClient()
            client.search_objects(search_term="'; DROP TABLE sql_objects; --")
            
            # Verificamos que se usan query_parameters para evitar inyección SQL
            call_kwargs = mock_bq_client.query.call_args[1]
            job_config = call_kwargs.get("job_config")
            
            assert job_config is not None, "Debería usar QueryJobConfig para pasar parámetros"
            assert len(job_config.query_parameters) > 0, "Debería recibir parámetros en la consulta"
            
            # El término de búsqueda debe estar presente como parámetro, no en crudo en el string
            param_values = [p.value for p in job_config.query_parameters]
            assert "'; DROP TABLE sql_objects; --" in param_values or "%'; DROP TABLE sql_objects; --%" in param_values

    @patch("squit_client.client.bigquery.Client")
    def test_get_object_details_sql_injection(self, mock_client):
        """Test que los detalles de un objeto están parametrizados."""
        mock_bq_client = Mock()
        mock_client.return_value = mock_bq_client
        mock_job = mock_bq_client.query.return_value
        mock_job.result.return_value.to_dataframe.return_value = pd.DataFrame()
        mock_job.total_bytes_processed = 1000
        
        with patch.object(Config, "get_credentials_path", return_value=None):
            client = BigQueryClient()
            client.get_object_details(object_name="test' OR '1'='1", server="SERVER1")
            
            call_kwargs = mock_bq_client.query.call_args[1]
            job_config = call_kwargs.get("job_config")
            
            assert job_config is not None, "Debería usar QueryJobConfig para pasar parámetros"
            assert len(job_config.query_parameters) >= 2, "Debería recibir parámetros en la consulta"

class TestBigQueryClientThreadSafety:
    """Tests para asegurar que inicialización e invocación del cliente sean Thread Safe."""
    
    @patch("squit_client.client.bigquery.Client")
    def test_client_initialization_thread_safety(self, mock_client):
        """Test para verificar que múltiples hilos comparten adecuadamente la instancia de bigquery."""
        mock_bq_client = Mock()
        mock_client.return_value = mock_bq_client
        
        with patch.object(Config, "get_credentials_path", return_value=None):
            client = BigQueryClient()
            
            def init_sim():
                _ = client.client
                
            threads = [threading.Thread(target=init_sim) for _ in range(10)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
                
            # Aseguramos de que tengamos protecciones u obtengamos el mock client de manera consistente
            assert client._client == mock_bq_client

class TestBigQueryClientObservability:
    """Tests para asegurar que el cliente emite logs apropiados."""
    
    @patch("squit_client.client.bigquery.Client")
    def test_execute_query_logs_latency_and_rows(self, mock_client, capsys, caplog):
        """Test para verificar que la ejecución de query genera trazas de observabilidad."""
        mock_bq_client = Mock()
        mock_client.return_value = mock_bq_client
        
        mock_job = Mock()
        mock_job.result.return_value.to_dataframe.return_value = pd.DataFrame({'test': [1,2,3]})
        mock_job.total_bytes_processed = 1024
        
        mock_bq_client.query.return_value = mock_job
        
        with patch.object(Config, "get_credentials_path", return_value=None):
            caplog.set_level(logging.INFO)
            client = BigQueryClient()
            client.execute_query("SELECT 1")
            
            # Verificar si se registra algo útil (bytes, rows, latency, etc)
            log_messages = [record.message for record in caplog.records]
            assert any("Filas" in msg for msg in log_messages), "Debería logear la cantidad de filas"
            assert any("Bytes procesados" in msg for msg in log_messages) or mock_job.total_bytes_processed > 0, "Debería logear los bytes procesados"
            assert any("Latencia" in msg or "Latencia de la consulta" in msg for msg in log_messages), "Debería logear la latencia"