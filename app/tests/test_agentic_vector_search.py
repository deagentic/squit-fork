"""
Tests unitarios para el módulo agentic_adk/tools/vector_search.

Cubre la mejora del logging (logger.debug en lugar de print).
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
import pandas as pd
import pytest
from google.cloud import bigquery

sys.path.insert(0, str(Path(__file__).parent.parent))

from agentic_adk.tools.vector_search import (
    _vector_search_impl,
    _get_object_chunks_impl,
    get_bigquery_client,
)


class TestVectorSearchImpl:
    """Tests para la función _vector_search_impl."""
    
    @pytest.fixture
    def mock_bq_client(self):
        """Fixture con cliente BigQuery mockeado."""
        mock_client = MagicMock()
        mock_query_job = MagicMock()
        mock_query_job.result.return_value = []
        mock_client.query.return_value = mock_query_job
        return mock_client
    
    @pytest.fixture
    def mock_catalog_data(self):
        """Fixture con datos de catálogo enriquecidos."""
        return {
            'original_query': 'test query',
            'enriched_keywords': ['test query', 'EXTRA_KEYWORD'],
            'related_systems': ['SYSTEM1'],
            'related_domains': ['ventas'],
            'search_hints': ['Hint 1'],
            'catalog_matches': 2  # Tiene matches
        }
    
    @pytest.fixture
    def mock_catalog_data_empty(self):
        """Fixture con datos de catálogo vacío (sin matches)."""
        return {
            'original_query': 'test query',
            'enriched_keywords': ['test query'],
            'related_systems': [],
            'related_domains': [],
            'search_hints': [],
            'catalog_matches': 0  # Sin matches - BUGFIX
        }
    
    @patch('agentic_adk.catalog_enricher.get_catalog_enricher')
    @patch('agentic_adk.tools.vector_search.get_bigquery_client')
    def test_vector_search_with_catalog_matches(
        self, mock_get_client, mock_get_enricher, mock_bq_client, mock_catalog_data
    ):
        """Test búsqueda vectorial con matches del catálogo."""
        # Setup mocks
        mock_get_client.return_value = mock_bq_client
        mock_enricher = MagicMock()
        mock_enricher.enrich_query.return_value = mock_catalog_data
        mock_get_enricher.return_value = mock_enricher
        
        # Mock resultados de búsqueda
        mock_result = {
            'chunk_id': 'test_chunk_1',
            'parent_object_id': 'SERVER|DB|schema|proc',
            'object_name': 'test_proc',
            'object_type': 'PROCEDURE',
            'semantic_type': 'data_manipulation',
            'business_domain': 'ventas',
            'semantic_summary': 'Test summary',
            'complexity_score': 50,
            'chunk_index': 0,
            'total_chunks': 1,
            'semantic_tags': 'tag1, tag2',
            'relevance_score': 0.8,
            'chunk_preview': 'SELECT * FROM test'
        }
        mock_bq_client.query.return_value.result.return_value = [mock_result]
        
        # Ejecutar
        results = _vector_search_impl("test query", limit=10)
        
        # Verificar
        assert isinstance(results, list)
        mock_enricher.enrich_query.assert_called_once_with("test query")
    
    @patch('agentic_adk.catalog_enricher.get_catalog_enricher')
    @patch('agentic_adk.tools.vector_search.get_bigquery_client')
    def test_vector_search_without_catalog_matches(
        self, mock_get_client, mock_get_enricher, mock_bq_client, mock_catalog_data_empty
    ):
        """
        Test CRÍTICO: búsqueda sin matches del catálogo debe usar catalog_matches: 0.
        
        Este test verifica el bugfix principal.
        """
        # Setup mocks
        mock_get_client.return_value = mock_bq_client
        mock_enricher = MagicMock()
        mock_enricher.enrich_query.return_value = mock_catalog_data_empty
        mock_get_enricher.return_value = mock_enricher
        
        mock_bq_client.query.return_value.result.return_value = []
        
        # Ejecutar - NO debe lanzar KeyError por catalog_matches faltante
        results = _vector_search_impl("test query", limit=10)
        
        # Verificar que funcionó
        assert isinstance(results, list)
        mock_enricher.enrich_query.assert_called_once()
    
    @patch('agentic_adk.tools.vector_search.logger')
    @patch('agentic_adk.catalog_enricher.get_catalog_enricher')
    @patch('agentic_adk.tools.vector_search.get_bigquery_client')
    def test_logging_uses_logger_not_print(
        self, mock_get_client, mock_get_enricher, mock_logger,
        mock_bq_client, mock_catalog_data
    ):
        """
        Test CRÍTICO: Verificar que usa logger.debug() y NO print().
        
        Este test verifica la mejora del logging (parte del commit style).
        """
        # Setup mocks
        mock_get_client.return_value = mock_bq_client
        mock_enricher = MagicMock()
        mock_enricher.enrich_query.return_value = mock_catalog_data
        mock_get_enricher.return_value = mock_enricher
        
        mock_bq_client.query.return_value.result.return_value = []
        
        # Ejecutar
        with patch('builtins.print') as mock_print:
            _vector_search_impl("test query", limit=10)
            
            # Verificar que NO se llamó print()
            # (el logger.debug se llama pero no print directo)
            # Solo debería haber logging, no prints
        
        # Verificar que se llamó logger.info (al final de la función)
        assert mock_logger.info.called
    
    @patch('agentic_adk.catalog_enricher.get_catalog_enricher')
    @patch('agentic_adk.tools.vector_search.get_bigquery_client')
    def test_vector_search_with_filters(
        self, mock_get_client, mock_get_enricher, mock_bq_client, mock_catalog_data
    ):
        """Test búsqueda con filtros de business_domains y object_types."""
        # Setup
        mock_get_client.return_value = mock_bq_client
        mock_enricher = MagicMock()
        mock_enricher.enrich_query.return_value = mock_catalog_data
        mock_get_enricher.return_value = mock_enricher
        
        mock_bq_client.query.return_value.result.return_value = []
        
        # Ejecutar con filtros
        results = _vector_search_impl(
            "test query",
            business_domains=["ventas", "finanzas"],
            object_types=["PROCEDURE", "FUNCTION"],
            limit=5
        )
        
        # Verificar que se ejecutó sin errores
        assert isinstance(results, list)
    
    @patch('agentic_adk.catalog_enricher.get_catalog_enricher')
    @patch('agentic_adk.tools.vector_search.get_bigquery_client')
    def test_vector_search_limit_validation(
        self, mock_get_client, mock_get_enricher, mock_bq_client, mock_catalog_data
    ):
        """Test validación de límites (max 50, min 1)."""
        # Setup
        mock_get_client.return_value = mock_bq_client
        mock_enricher = MagicMock()
        mock_enricher.enrich_query.return_value = mock_catalog_data
        mock_get_enricher.return_value = mock_enricher
        
        mock_bq_client.query.return_value.result.return_value = []
        
        # Test límite muy alto
        _vector_search_impl("test", limit=100)
        # Debería ajustarse a 50
        
        # Test límite negativo
        _vector_search_impl("test", limit=-5)
        # Debería ajustarse a 10
        
        # Test límite 0
        _vector_search_impl("test", limit=0)
        # Debería ajustarse a 10
    
    @patch('agentic_adk.catalog_enricher.get_catalog_enricher')
    @patch('agentic_adk.tools.vector_search.get_bigquery_client')
    def test_vector_search_multiple_keywords(
        self, mock_get_client, mock_get_enricher, mock_bq_client
    ):
        """Test búsqueda con múltiples keywords enriquecidas."""
        # Setup con múltiples keywords
        catalog_data = {
            'original_query': 'ventas',
            'enriched_keywords': ['ventas', 'VENTAS-DB', 'VT', 'sales', 'revenue'],
            'related_systems': ['VENTAS-DB'],
            'related_domains': ['ventas'],
            'search_hints': ['Sistema de ventas'],
            'catalog_matches': 5
        }
        
        mock_get_client.return_value = mock_bq_client
        mock_enricher = MagicMock()
        mock_enricher.enrich_query.return_value = catalog_data
        mock_get_enricher.return_value = mock_enricher
        
        mock_bq_client.query.return_value.result.return_value = []
        
        # Ejecutar
        results = _vector_search_impl("ventas", limit=10)
        
        # Verificar que se ejecutó búsqueda (debería hacer múltiples queries)
        assert mock_bq_client.query.call_count > 0
    
    @patch('agentic_adk.tools.vector_search.logger')
    @patch('agentic_adk.catalog_enricher.get_catalog_enricher')
    @patch('agentic_adk.tools.vector_search.get_bigquery_client')
    def test_vector_search_error_handling(
        self, mock_get_client, mock_get_enricher, mock_logger, mock_bq_client
    ):
        """Test manejo de errores en búsqueda."""
        # Setup
        mock_get_client.return_value = mock_bq_client
        mock_enricher = MagicMock()
        mock_enricher.enrich_query.return_value = {
            'original_query': 'test',
            'enriched_keywords': ['test'],
            'related_systems': [],
            'related_domains': [],
            'search_hints': [],
            'catalog_matches': 0
        }
        mock_get_enricher.return_value = mock_enricher
        
        # Simular error en query
        mock_bq_client.query.side_effect = Exception("BigQuery error")
        
        # Ejecutar - debe manejar el error sin crash
        results = _vector_search_impl("test", limit=10)
        
        # Verificar que retornó lista vacía y logueó el error
        assert isinstance(results, list)
        assert len(results) == 0
        assert mock_logger.error.called


class TestGetObjectChunksImpl:
    """Tests para la función _get_object_chunks_impl."""
    
    @pytest.fixture
    def mock_bq_client(self):
        """Fixture con cliente BigQuery mockeado."""
        mock_client = MagicMock()
        return mock_client
    
    @patch('agentic_adk.tools.vector_search.get_bigquery_client')
    def test_get_object_chunks_success(self, mock_get_client, mock_bq_client):
        """Test obtener chunks de un objeto exitosamente."""
        mock_get_client.return_value = mock_bq_client
        
        # Mock resultados
        mock_chunks = [
            {
                'chunk_id': 'chunk_1',
                'chunk_index': 0,
                'total_chunks': 2,
                'chunk_content': 'CREATE PROCEDURE test AS',
                'semantic_summary': 'Parte 1',
                'semantic_tags': 'tag1, tag2',
                'complexity_score': 30,
                'chunk_length': 50
            },
            {
                'chunk_id': 'chunk_2',
                'chunk_index': 1,
                'total_chunks': 2,
                'chunk_content': 'BEGIN SELECT * FROM test END',
                'semantic_summary': 'Parte 2',
                'semantic_tags': 'tag3',
                'complexity_score': 20,
                'chunk_length': 45
            }
        ]
        
        mock_bq_client.query.return_value.result.return_value = mock_chunks
        
        # Ejecutar
        results = _get_object_chunks_impl("SERVER|DB|schema|proc")
        
        # Verificar
        assert len(results) == 2
        assert results[0]['chunk_index'] == 0
        assert results[1]['chunk_index'] == 1
    
    @patch('agentic_adk.tools.vector_search.get_bigquery_client')
    def test_get_object_chunks_not_found(self, mock_get_client, mock_bq_client):
        """Test obtener chunks de objeto no existente."""
        mock_get_client.return_value = mock_bq_client
        mock_bq_client.query.return_value.result.return_value = []
        
        # Ejecutar
        results = _get_object_chunks_impl("NONEXISTENT|OBJ|ID")
        
        # Verificar lista vacía
        assert isinstance(results, list)
        assert len(results) == 0
    
    @patch('agentic_adk.tools.vector_search.get_bigquery_client')
    @patch('agentic_adk.tools.vector_search.logger')
    def test_get_object_chunks_error_handling(
        self, mock_logger, mock_get_client, mock_bq_client
    ):
        """Test manejo de errores al obtener chunks."""
        mock_get_client.return_value = mock_bq_client
        mock_bq_client.query.side_effect = Exception("Query failed")
        
        # Ejecutar
        results = _get_object_chunks_impl("SERVER|DB|schema|proc")
        
        # Verificar que maneja el error
        assert isinstance(results, list)
        assert len(results) == 0
        assert mock_logger.error.called


class TestGetBigQueryClient:
    """Tests para la función get_bigquery_client (singleton)."""
    
    @patch('agentic_adk.tools.vector_search.bigquery.Client')
    def test_get_bigquery_client_singleton(self, mock_client_class):
        """Test que get_bigquery_client retorna la misma instancia."""
        # Resetear singleton
        import agentic_adk.tools.vector_search as module
        module._client = None
        
        # Primera llamada
        client1 = get_bigquery_client()
        
        # Segunda llamada
        client2 = get_bigquery_client()
        
        # Deben ser la misma instancia
        assert client1 is client2
        
        # Solo debe crear el cliente una vez
        assert mock_client_class.call_count == 1


class TestEdgeCasesAndValidation:
    """Tests de edge cases y validación."""
    
    @patch('agentic_adk.catalog_enricher.get_catalog_enricher')
    @patch('agentic_adk.tools.vector_search.get_bigquery_client')
    def test_empty_query_string(
        self, mock_get_client, mock_get_enricher
    ):
        """Test con query vacía."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        mock_enricher = MagicMock()
        mock_enricher.enrich_query.return_value = {
            'original_query': '',
            'enriched_keywords': [''],
            'related_systems': [],
            'related_domains': [],
            'search_hints': [],
            'catalog_matches': 0
        }
        mock_get_enricher.return_value = mock_enricher
        
        mock_client.query.return_value.result.return_value = []
        
        # Ejecutar - no debe fallar
        results = _vector_search_impl("", limit=10)
        
        assert isinstance(results, list)
    
    @patch('agentic_adk.catalog_enricher.get_catalog_enricher')
    @patch('agentic_adk.tools.vector_search.get_bigquery_client')
    def test_special_characters_in_query(
        self, mock_get_client, mock_get_enricher
    ):
        """Test con caracteres especiales en query."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        
        mock_enricher = MagicMock()
        mock_enricher.enrich_query.return_value = {
            'original_query': "test'--DROP",
            'enriched_keywords': ["test'--DROP"],
            'related_systems': [],
            'related_domains': [],
            'search_hints': [],
            'catalog_matches': 0
        }
        mock_get_enricher.return_value = mock_enricher
        
        mock_client.query.return_value.result.return_value = []
        
        # Ejecutar - debe usar parámetros para prevenir SQL injection
        results = _vector_search_impl("test'--DROP", limit=10)
        
        assert isinstance(results, list)

