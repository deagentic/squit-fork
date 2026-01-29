# 🧪 Testing Guide - SQUIT

Guía completa de testing, coverage y buenas prácticas para SQUIT.

---

## 📋 Overview

SQUIT utiliza `pytest` como framework principal de testing, con mocks para dependencias externas y fixtures compartidos para datos de prueba.

**Objetivo de coverage**: ≥ 70%

---

## 🚀 Quick Start

```bash
# Ejecutar todos los tests
pytest

# Con coverage
pytest --cov=app --cov-report=html

# Tests específicos
pytest app/tests/test_retry.py

# Tests por tipo
pytest -m unit           # Solo unitarios
pytest -m integration    # Solo integración
pytest -m "not slow"     # Excluir tests lentos
```

---

## 📁 Estructura de Tests

```
app/tests/
├── conftest.py                      # Fixtures compartidos
├── fixtures/                        # Datos de prueba
│   ├── sample_sql_objects.json
│   └── sample_chunks.json
├── unit/                            # Tests unitarios
│   ├── test_retry.py                # ✅ Implementado
│   ├── test_rate_limiter.py
│   ├── test_circuit_breaker.py
│   ├── test_metrics.py
│   └── test_structured_logging.py
├── integration/                     # Tests de integración
│   ├── test_bigquery_integration.py
│   ├── test_gemini_integration.py
│   └── test_end_to_end.py
└── e2e/                            # Tests end-to-end
    └── test_full_pipeline.py
```

---

## ✅ Tests Implementados

### 1. test_retry.py

Tests para retry con backoff exponencial:

```python
def test_successful_call_no_retry():
    """Función exitosa no reintenta."""
    
def test_retry_on_exception():
    """Reintenta en excepción."""
    
def test_max_retries_exceeded():
    """Lanza excepción después de max_retries."""
    
def test_backoff_timing():
    """Backoff aumenta exponencialmente."""
```

**Ejecutar:**
```bash
pytest app/tests/test_retry.py -v
```

---

## 🎯 Próximos Tests a Implementar

### Alta Prioridad

1. **test_chunking_pipeline.py** - Tests de chunking strategies
   - Test chunking de objetos mega (>1M chars)
   - Test chunking de objetos large (>50K chars)
   - Test recovery desde checkpoint
   - Test manejo de errores

2. **test_vector_search.py** - Tests de búsquedas
   - Test búsqueda semántica con mock data
   - Test búsqueda híbrida combina scores
   - Test filtros por dominio
   - Test paginación

3. **test_progress_tracker.py** - Tests de tracking
   - Test inicio y finalización de run
   - Test actualización de progreso
   - Test recovery desde checkpoint
   - Test registro de métricas

### Media Prioridad

4. **test_master_agent.py** - Tests del agente
   - Test procesamiento de queries
   - Test memoria conversacional
   - Test integración con tools
   - Test rate limiting

5. **test_rate_limiter.py** - Tests de rate limiting
   - Test bloqueo al exceder límite
   - Test liberación de tokens
   - Test thread safety

6. **test_circuit_breaker.py** - Tests de circuit breaker
   - Test apertura después de threshold
   - Test estado HALF_OPEN
   - Test recovery

---

## 🔨 Escribir Tests

### Test Unitario Básico

```python
import pytest
from utils.retry import retry_with_backoff

def test_retry_behavior():
    """Test que retry funciona correctamente."""
    # Arrange
    mock_func = Mock(side_effect=[
        ConnectionError(),
        "success"
    ])
    
    @retry_with_backoff(max_retries=2)
    def test_func():
        return mock_func()
    
    # Act
    result = test_func()
    
    # Assert
    assert result == "success"
    assert mock_func.call_count == 2
```

### Test con Fixtures

```python
@pytest.fixture
def sample_sql_code():
    """Fixture con código SQL de ejemplo."""
    return """
    CREATE PROCEDURE TestProc
    AS
    BEGIN
        SELECT * FROM Users
    END
    """

def test_chunking_strategy(sample_sql_code):
    """Test chunking con fixture."""
    from bigquery_vector.chunking_pipeline import chunk_code
    
    chunks = chunk_code(sample_sql_code)
    
    assert len(chunks) > 0
    assert all(len(c) >= 500 for c in chunks)
```

### Test de Integración

```python
@pytest.mark.integration
def test_bigquery_connection():
    """Test conexión real a BigQuery."""
    from utils.connection_pool import get_bigquery_client
    
    client = get_bigquery_client()
    result = client.query("SELECT 1 as test").result()
    
    row = list(result)[0]
    assert row.test == 1
```

---

## 🎭 Mocking

### Mock de BigQuery Client

```python
from unittest.mock import Mock, patch

@patch('google.cloud.bigquery.Client')
def test_with_mock_bigquery(mock_client):
    """Test con BigQuery mockeado."""
    # Setup mock
    mock_client.return_value.query.return_value.result.return_value = [
        {'name': 'test', 'value': 123}
    ]
    
    # Test code
    from bigquery_vector.vector_search import BigQueryVectorSearch
    search = BigQueryVectorSearch()
    results = search.semantic_search("test query")
    
    assert len(results) > 0
```

### Mock de Gemini API

```python
@patch('google.genai.Client')
def test_with_mock_gemini(mock_gemini):
    """Test con Gemini mockeado."""
    mock_response = Mock()
    mock_response.text = "Mocked response"
    mock_gemini.return_value.models.generate_content.return_value = mock_response
    
    # Test agent
    from agentic_adk.agents import MasterAgent
    agent = MasterAgent()
    response = agent.process("test query")
    
    assert "Mocked" in response
```

---

## 📊 Coverage

### Ejecutar Coverage

```bash
# Coverage HTML (recomendado)
pytest --cov=app --cov-report=html
open htmlcov/index.html

# Coverage en terminal
pytest --cov=app --cov-report=term-missing

# Coverage solo para módulo específico
pytest --cov=app.utils --cov-report=term
```

### Objetivos de Coverage

| Módulo | Target | Actual |
|--------|--------|--------|
| `utils/` | 80% | 🔄 TBD |
| `bigquery_vector/` | 70% | 🔄 TBD |
| `agentic_adk/` | 70% | 🔄 TBD |
| **Overall** | **70%** | **🔄 TBD** |

---

## 🏷️ Markers

```python
# Marcar test como lento
@pytest.mark.slow
def test_full_pipeline():
    pass

# Marcar como integración
@pytest.mark.integration
def test_bigquery_real():
    pass

# Marcar como unitario
@pytest.mark.unit
def test_pure_function():
    pass

# Skip condicional
@pytest.mark.skipif(not has_credentials(), reason="No credentials")
def test_with_auth():
    pass
```

**Ejecutar por marker:**
```bash
pytest -m unit              # Solo unitarios
pytest -m integration       # Solo integración
pytest -m "not slow"        # Excluir lentos
```

---

## 🔧 Configuración (pyproject.toml)

```toml
[tool.pytest.ini_options]
minversion = "7.0"
addopts = "-ra -q --strict-markers --strict-config"
testpaths = ["app/tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
markers = [
    "slow: marks tests as slow",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
]

[tool.coverage.run]
source = ["app"]
omit = [
    "*/tests/*",
    "*/__pycache__/*",
    "*/examples/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
]
```

---

## 🚀 CI/CD

Ver `.github/workflows/test.yml` para configuración de CI/CD automático.

Tests se ejecutan automáticamente en cada:
- Push a `main`
- Pull request
- Tag de release

---

## 📝 Buenas Prácticas

### ✅ DO

- Escribir tests antes de código (TDD cuando sea posible)
- Un assert por test (cuando tenga sentido)
- Nombres descriptivos: `test_semantic_search_returns_results_ordered_by_relevance`
- Usar fixtures para setup compartido
- Mockear dependencias externas (APIs, BD)
- Tests independientes (no dependen entre sí)

### ❌ DON'T

- Tests que dependen de orden de ejecución
- Tests con sleeps o timeouts arbitrarios
- Tests que modifican estado global
- Tests sin assertions
- Tests con múltiples responsabilidades

---

## 🐛 Debugging Tests

```bash
# Ejecutar con output completo
pytest -v -s

# Detener en primer fallo
pytest -x

# Debug con pdb
pytest --pdb

# Solo último fallo
pytest --lf

# Solo tests que fallaron
pytest --ff
```

---

## 📚 Recursos

- **pytest docs**: https://docs.pytest.org/
- **pytest-cov**: https://pytest-cov.readthedocs.io/
- **unittest.mock**: https://docs.python.org/3/library/unittest.mock.html
- **Testing Best Practices**: https://docs.python-guide.org/writing/tests/

---

**¿Listo para escribir tests?** ¡Empieza con `app/tests/test_retry.py` como ejemplo!

