"""
Tests unitarios para el módulo catalog_enricher.

Cubre el bugfix de catalog_matches: 0 cuando no hay catálogo cargado.
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from agentic_adk.catalog_enricher import CatalogEnricher, get_catalog_enricher


class TestCatalogEnricher:
    """Tests para la clase CatalogEnricher."""
    
    @pytest.fixture
    def mock_catalog_data(self):
        """Fixture con datos de catálogo de ejemplo."""
        return pd.DataFrame({
            'application_name': ['App1', 'App2', 'App3'],
            'description': ['Sistema de ventas', 'Gestión de inventario', 'Contabilidad'],
            'database_name': ['VENTAS-DB', 'INV-DB', 'CONT-DB'],
            'business_domain': ['ventas', 'inventario', 'finanzas']
        })
    
    @pytest.fixture
    def mock_catalog_data_old_format(self):
        """Fixture con datos de catálogo en formato antiguo."""
        return pd.DataFrame({
            'Name': ['App1', 'App2', 'App3'],
            'Descripcion': ['Sistema de ventas', 'Gestión de inventario', 'Contabilidad'],
            'Sistema Objeto': ['VENTAS-DB', 'INV-DB', 'CONT-DB'],
            'Proceso End To End': ['ventas', 'inventario', 'finanzas']
        })
    
    def test_init_with_existing_catalog(self, tmp_path):
        """Test inicialización con catálogo existente."""
        # Crear archivo CSV temporal
        catalog_path = tmp_path / "catalogo.csv"
        catalog_path.write_text("application_name,description\nApp1,Test")
        
        enricher = CatalogEnricher(catalog_path=catalog_path)
        
        assert enricher.catalog_path == catalog_path
        assert enricher.catalog_df is not None
        assert len(enricher.catalog_df) == 1
    
    def test_init_with_nonexistent_catalog(self, tmp_path):
        """Test inicialización con catálogo no existente."""
        catalog_path = tmp_path / "nonexistent.csv"
        
        enricher = CatalogEnricher(catalog_path=catalog_path)
        
        assert enricher.catalog_path == catalog_path
        assert enricher.catalog_df is not None
        assert len(enricher.catalog_df) == 0
    
    def test_enrich_query_without_catalog(self):
        """
        Test CRÍTICO: enrich_query sin catálogo debe retornar catalog_matches: 0.
        
        Este es el bugfix principal del merge.
        """
        enricher = CatalogEnricher.__new__(CatalogEnricher)
        enricher.catalog_df = pd.DataFrame()  # Catálogo vacío
        
        result = enricher.enrich_query("test query")
        
        # Verificar que TODOS los campos requeridos están presentes
        assert 'original_query' in result
        assert 'enriched_keywords' in result
        assert 'related_systems' in result
        assert 'related_processes' in result
        assert 'search_hints' in result
        assert 'catalog_matches' in result  # ← BUGFIX: debe estar presente
        
        # Verificar valores
        assert result['original_query'] == "test query"
        assert result['enriched_keywords'] == ["test query"]
        assert result['related_systems'] == []
        assert result['related_processes'] == []
        assert result['search_hints'] == []
        assert result['catalog_matches'] == 0  # ← BUGFIX: debe ser 0
    
    def test_enrich_query_with_catalog_matches(self, mock_catalog_data):
        """Test enrich_query con catálogo que tiene matches."""
        enricher = CatalogEnricher.__new__(CatalogEnricher)
        enricher.catalog_df = mock_catalog_data
        enricher.catalog_path = Path("test.csv")
        
        result = enricher.enrich_query("ventas")
        
        # Verificar estructura completa
        assert 'original_query' in result
        assert 'enriched_keywords' in result
        assert 'related_systems' in result
        assert 'related_domains' in result
        assert 'search_hints' in result
        assert 'catalog_matches' in result
        
        # Verificar que encontró matches
        assert result['catalog_matches'] > 0
        assert len(result['enriched_keywords']) > 1
        assert 'VENTAS' in result['enriched_keywords'][1]  # Sistema
    
    def test_enrich_query_with_old_format_catalog(self, mock_catalog_data_old_format):
        """Test backward compatibility con formato antiguo de catálogo."""
        enricher = CatalogEnricher.__new__(CatalogEnricher)
        enricher.catalog_df = mock_catalog_data_old_format
        enricher.catalog_path = Path("test.csv")
        
        result = enricher.enrich_query("ventas")
        
        # Debe funcionar igual con formato antiguo
        assert result['catalog_matches'] > 0
        assert len(result['enriched_keywords']) > 1
    
    def test_enrich_query_no_matches(self, mock_catalog_data):
        """Test enrich_query sin matches en el catálogo."""
        enricher = CatalogEnricher.__new__(CatalogEnricher)
        enricher.catalog_df = mock_catalog_data
        enricher.catalog_path = Path("test.csv")
        
        result = enricher.enrich_query("xyz123noexiste")
        
        # Sin matches pero con catálogo cargado
        assert result['catalog_matches'] == 0
        assert result['enriched_keywords'] == ["xyz123noexiste"]
        assert result['related_systems'] == []
    
    def test_enrich_query_matching_application_name(self, mock_catalog_data):
        """Test matching en nombre de aplicación (peso alto)."""
        enricher = CatalogEnricher.__new__(CatalogEnricher)
        enricher.catalog_df = mock_catalog_data
        enricher.catalog_path = Path("test.csv")
        
        result = enricher.enrich_query("App1")
        
        assert result['catalog_matches'] > 0
        assert len(result['search_hints']) > 0
    
    def test_enrich_query_matching_description(self, mock_catalog_data):
        """Test matching en descripción."""
        enricher = CatalogEnricher.__new__(CatalogEnricher)
        enricher.catalog_df = mock_catalog_data
        enricher.catalog_path = Path("test.csv")
        
        result = enricher.enrich_query("inventario")
        
        assert result['catalog_matches'] > 0
        assert 'INV' in str(result['enriched_keywords'])
    
    def test_get_context_for_term_with_matches(self, mock_catalog_data):
        """Test get_context_for_term con matches."""
        enricher = CatalogEnricher.__new__(CatalogEnricher)
        enricher.catalog_df = mock_catalog_data
        enricher.catalog_path = Path("test.csv")
        
        context = enricher.get_context_for_term("ventas")
        
        assert context is not None
        assert isinstance(context, str)
        assert len(context) > 0
    
    def test_get_context_for_term_without_matches(self, mock_catalog_data):
        """Test get_context_for_term sin matches."""
        enricher = CatalogEnricher.__new__(CatalogEnricher)
        enricher.catalog_df = mock_catalog_data
        enricher.catalog_path = Path("test.csv")
        
        context = enricher.get_context_for_term("noexiste123")
        
        assert context is None
    
    def test_catalog_matches_consistency(self, mock_catalog_data):
        """
        Test CRÍTICO: catalog_matches debe estar SIEMPRE en el resultado.
        
        Verifica que ambos paths de return tengan la misma firma.
        """
        enricher = CatalogEnricher.__new__(CatalogEnricher)
        
        # Path 1: Sin catálogo
        enricher.catalog_df = pd.DataFrame()
        result1 = enricher.enrich_query("test")
        
        # Path 2: Con catálogo
        enricher.catalog_df = mock_catalog_data
        enricher.catalog_path = Path("test.csv")
        result2 = enricher.enrich_query("test")
        
        # Ambos deben tener catalog_matches
        assert 'catalog_matches' in result1
        assert 'catalog_matches' in result2
        
        # Las keys esenciales deben estar en ambos
        essential_keys = {'original_query', 'enriched_keywords', 'search_hints', 'catalog_matches'}
        assert essential_keys.issubset(set(result1.keys()))
        assert essential_keys.issubset(set(result2.keys()))


class TestCatalogEnricherSingleton:
    """Tests para el patrón singleton de get_catalog_enricher()."""
    
    def test_get_catalog_enricher_singleton(self):
        """Test que get_catalog_enricher retorna la misma instancia."""
        # Resetear singleton
        import agentic_adk.catalog_enricher as module
        module._enricher = None
        
        enricher1 = get_catalog_enricher()
        enricher2 = get_catalog_enricher()
        
        assert enricher1 is enricher2
    
    def test_get_catalog_enricher_returns_instance(self):
        """Test que get_catalog_enricher retorna una instancia válida."""
        enricher = get_catalog_enricher()
        
        assert isinstance(enricher, CatalogEnricher)
        assert hasattr(enricher, 'enrich_query')
        assert hasattr(enricher, 'get_context_for_term')


class TestCatalogEnricherEdgeCases:
    """Tests de edge cases y validación."""
    
    @pytest.fixture
    def mock_catalog_data(self):
        """Fixture con datos de catálogo de ejemplo."""
        return pd.DataFrame({
            'application_name': ['App1', 'App2', 'App3'],
            'description': ['Sistema de ventas', 'Gestión de inventario', 'Contabilidad'],
            'database_name': ['VENTAS-DB', 'INV-DB', 'CONT-DB'],
            'business_domain': ['ventas', 'inventario', 'finanzas']
        })
    
    def test_enrich_query_empty_string(self):
        """Test con query vacía."""
        enricher = CatalogEnricher.__new__(CatalogEnricher)
        enricher.catalog_df = pd.DataFrame()
        
        result = enricher.enrich_query("")
        
        assert result['catalog_matches'] == 0
        assert result['enriched_keywords'] == [""]
    
    def test_enrich_query_with_special_characters(self, mock_catalog_data):
        """Test con caracteres especiales en query."""
        enricher = CatalogEnricher.__new__(CatalogEnricher)
        enricher.catalog_df = mock_catalog_data
        enricher.catalog_path = Path("test.csv")
        
        result = enricher.enrich_query("ventas@#$%")
        
        # Debe manejar caracteres especiales sin error
        assert 'catalog_matches' in result
        assert isinstance(result['catalog_matches'], int)
    
    def test_enrich_query_with_none_values_in_catalog(self):
        """Test con valores None en el catálogo."""
        df = pd.DataFrame({
            'application_name': ['App1', None, 'App3'],
            'description': [None, 'Desc2', 'Desc3'],
            'database_name': ['DB1', None, None],
            'business_domain': [None, None, 'finanzas']
        })
        
        enricher = CatalogEnricher.__new__(CatalogEnricher)
        enricher.catalog_df = df
        enricher.catalog_path = Path("test.csv")
        
        result = enricher.enrich_query("test")
        
        # Debe manejar None sin error
        assert 'catalog_matches' in result
        assert isinstance(result['catalog_matches'], int)

