# Guía de Contribución - SQUIT "SQL Quit"
## Democratizando Código Legacy con IA

Gracias por tu interés en contribuir a la **democratización del conocimiento legacy**. Este documento proporciona las directrices para ayudar a liberar el conocimiento enterrado en código SQL.

## 🎯 Filosofía del Proyecto - Democratización

**SQUIT ("SQL Quit")** democratiza el acceso al código legacy. Priorizamos:

1. **Democratización del conocimiento**: Accesible para todos, no solo expertos
2. **Liberación del conocimiento**: "Quit" = Salir del código críptico

1. **Código limpio y mantenible**: Claridad sobre brevedad
2. **Documentación exhaustiva**: Código auto-documentado + docstrings
3. **Performance optimizado**: Soluciones escalables para 3M+ objetos
4. **Tracking robusto**: Todo debe ser observable y recuperable
5. **Type safety**: Type hints en todo el código

## 🚀 Quick Start

### 1. Setup del Entorno

```bash
# Clonar repositorio
git clone https://github.com/deacero/squit.git
cd squit

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt

# Instalar en modo desarrollo
pip install -e .

# Configurar credenciales
cp env.example .env
# Editar .env con tus valores
```

### 2. Verificar Setup

```bash
# Ejecutar tests
make test

# Verificar linting
make lint

# Validar sistema
python scripts/run_bigquery_pipeline.py --validate
```

## 📋 Proceso de Contribución

### 1. Crear Issue

Antes de comenzar, crea un issue describiendo:
- Problema a resolver o funcionalidad a agregar
- Motivación y casos de uso
- Propuesta de solución (si la tienes)

### 2. Fork y Branch

```bash
# Fork del repositorio en GitHub

# Clonar tu fork
git clone https://github.com/TU_USUARIO/squit.git
cd squit

# Agregar upstream
git remote add upstream https://github.com/deacero/squit.git

# Crear branch para tu feature
git checkout -b feature/descripcion-corta
```

### 3. Desarrollo

#### Estándares de Código

**Python Style:**
- Python 3.11+
- Black formatter (línea max 100 chars)
- Flake8 linter
- Mypy para type checking
- Imports organizados con isort

**Type Hints (OBLIGATORIO):**
```python
from typing import Dict, List, Optional, Any

def my_function(
    param1: str,
    param2: int,
    optional_param: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Función con type hints completos."""
    pass
```

**Docstrings (OBLIGATORIO para funciones públicas):**
```python
def semantic_search(
    self,
    query: str,
    limit: int = 10,
    business_domains: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Realiza búsqueda semántica en el codebase.
    
    Esta función usa embeddings de Gemini para encontrar código similar
    semánticamente a la consulta proporcionada.
    
    Args:
        query: Consulta en lenguaje natural.
        limit: Número máximo de resultados.
        business_domains: Filtrar por dominios específicos.
            Dominios válidos: ventas, inventario, finanzas, etc.
            
    Returns:
        Lista de diccionarios con resultados ordenados por relevancia.
        Cada resultado incluye: chunk_id, object_name, semantic_summary,
        hybrid_score, chunk_preview.
        
    Raises:
        ValueError: Si limit es <= 0.
        RuntimeError: Si no hay embeddings disponibles.
        
    Example:
        >>> search = BigQueryVectorSearch()
        >>> results = search.semantic_search(
        ...     query="autenticación de usuarios",
        ...     limit=5,
        ...     business_domains=["seguridad"]
        ... )
        >>> print(f"Encontrados: {len(results)}")
    """
    pass
```

**Logging (NO usar print()):**
```python
import logging

logger = logging.getLogger(__name__)

# Niveles apropiados
logger.debug("Detalles técnicos para debugging")
logger.info("Operación completada exitosamente")
logger.warning("Situación inusual pero no crítica")
logger.error("Error recuperable")
logger.exception("Error con traceback completo")
```

**Manejo de Errores:**
```python
# ✅ BIEN: Específico y con logging
try:
    result = risky_operation()
except ValueError as e:
    logger.error(f"Valor inválido: {e}")
    raise
except KeyError as e:
    logger.error(f"Clave no encontrada: {e}")
    return None
except Exception as e:
    logger.exception("Error inesperado")
    raise RuntimeError(f"Operación falló: {e}") from e

# ❌ MAL: Genérico y silencioso
try:
    result = risky_operation()
except:
    pass
```

#### Estructura de Commit

```bash
# Formato de mensajes
<type>: <descripción corta>

<descripción detallada si es necesario>
```

**Types:**
- `feat`: Nueva funcionalidad
- `fix`: Corrección de bug
- `docs`: Cambios en documentación
- `style`: Formateo (sin cambio de lógica)
- `refactor`: Refactorización
- `test`: Agregar/modificar tests
- `chore`: Mantenimiento, dependencies

**Ejemplos:**
```bash
feat: agregar filtro por fecha en semantic_search

- Agregar parámetros start_date y end_date
- Validar formato de fechas
- Actualizar tests y documentación

fix: corregir memory leak en chunking_pipeline

El pipeline no cerraba conexiones BigQuery correctamente,
causando acumulación de conexiones en runs largos.
```

### 4. Testing

**OBLIGATORIO:** Todo código nuevo debe tener tests.

```python
# tests/test_vector_search.py
import pytest
from bigquery_vector.vector_search import BigQueryVectorSearch

def test_semantic_search_basic(mock_bigquery_client):
    """Test búsqueda semántica básica."""
    search = BigQueryVectorSearch()
    results = search.semantic_search("test query", limit=10)
    
    assert len(results) <= 10
    assert all('chunk_id' in r for r in results)

def test_semantic_search_validation():
    """Test validación de parámetros."""
    search = BigQueryVectorSearch()
    
    with pytest.raises(ValueError):
        search.semantic_search("query", limit=-1)

def test_semantic_search_with_filters(mock_bigquery_client):
    """Test búsqueda con filtros."""
    search = BigQueryVectorSearch()
    results = search.semantic_search(
        "query",
        business_domains=["ventas"],
        object_types=["PROCEDURE"]
    )
    
    assert all(r['business_domain'] == 'ventas' for r in results)
```

**Ejecutar Tests:**
```bash
# Todos los tests
make test

# Tests con coverage
make test-cov

# Tests específicos
pytest tests/test_vector_search.py -v
pytest tests/test_vector_search.py::test_semantic_search_basic -v
```

### 5. Documentación

**Actualizar documentación relevante:**
- README.md si cambias la API pública
- docs/API.md si agregas/modificas funciones
- docs/BIGQUERY_VECTOR_COMPLETE.md si cambias el pipeline
- Docstrings en el código

### 6. Quality Checks

```bash
# Formatear código
make format

# Verificar linting
make lint

# Verificar type hints
mypy app/

# Análisis de seguridad
make security

# Todo junto
make format && make lint && make test
```

### 7. Pull Request

```bash
# Asegurar que estás actualizado
git fetch upstream
git rebase upstream/main

# Push a tu fork
git push origin feature/tu-feature

# Crear Pull Request en GitHub
```

**Template de PR:**
```markdown
## Descripción
Breve descripción de los cambios.

## Motivación
¿Por qué son necesarios estos cambios?

## Cambios Principales
- Cambio 1
- Cambio 2
- Cambio 3

## Testing
- [ ] Tests unitarios agregados
- [ ] Tests de integración actualizados
- [ ] Todos los tests pasan localmente
- [ ] Coverage mantenido/mejorado

## Checklist
- [ ] Código formateado con black
- [ ] Linting pasa (flake8)
- [ ] Type hints agregados
- [ ] Docstrings actualizados
- [ ] Documentación actualizada
- [ ] Tests agregados/actualizados
- [ ] Changelog actualizado (si aplica)

## Screenshots/Logs
Si aplica, agregar screenshots o logs relevantes.

## Issues Relacionados
Closes #123
Relates to #456
```

## 🎨 Áreas de Contribución

### 1. Mejoras al Pipeline
- Optimizaciones de performance
- Nuevas estrategias de chunking
- Mejoras en clasificación semántica

### 2. Vector Search
- Nuevos tipos de búsqueda
- Filtros adicionales
- Optimizaciones de queries

### 3. Progress Tracking
- Nuevas métricas
- Mejoras en reportes
- Dashboard de visualización

### 4. Scripts y Utilidades
- Nuevos scripts de análisis
- Mejoras en CLI
- Automatizaciones

### 5. Documentación
- Ejemplos adicionales
- Tutoriales
- Mejoras en explicaciones

### 6. Testing
- Más coverage
- Tests de integración
- Tests de performance

## ⚠️ Prohibiciones Estrictas

**NUNCA:**
- Commitear credenciales (.env, credentials.json, API keys)
- Usar print() en lugar de logging
- Modificar estructura de tablas sin discusión previa
- Hardcodear valores en lugar de usar config
- Ignorar errores silenciosamente
- Cambiar dimensiones de embeddings (768 es optimizado)
- Eliminar tracking/logging existente
- Crear queries sin límites en producción

## 🐛 Reportar Bugs

**Template de Bug Report:**
```markdown
## Descripción del Bug
Descripción clara y concisa del problema.

## Pasos para Reproducir
1. Paso 1
2. Paso 2
3. ...

## Comportamiento Esperado
Qué debería pasar.

## Comportamiento Actual
Qué pasa realmente.

## Entorno
- OS: [e.g. macOS 14.0]
- Python: [e.g. 3.11.5]
- SQUIT version: [e.g. 2.0.0]

## Logs/Traceback
```
Logs relevantes aquí
```

## Screenshots
Si aplica.

## Contexto Adicional
Cualquier otra información relevante.
```

## 💡 Solicitar Features

**Template de Feature Request:**
```markdown
## Descripción del Feature
Descripción clara de la funcionalidad deseada.

## Motivación
¿Por qué sería útil? ¿Qué problema resuelve?

## Casos de Uso
- Caso 1
- Caso 2

## Propuesta de Implementación
Si tienes una idea de cómo implementarlo.

## Alternativas Consideradas
Otras formas de resolver el problema.

## Información Adicional
Screenshots, mockups, referencias, etc.
```

## 📞 Comunicación

- **Issues**: Para bugs y feature requests
- **Discussions**: Para preguntas y discusiones
- **Email**: ktouma@deacero.com para temas privados

## 🙏 Código de Conducta

- Sé respetuoso y profesional
- Acepta críticas constructivas
- Enfócate en lo mejor para el proyecto
- Ayuda a otros contribuidores

## 📚 Recursos

- [README.md](README.md): Overview del proyecto
- [docs/BIGQUERY_VECTOR_COMPLETE.md](docs/BIGQUERY_VECTOR_COMPLETE.md): Documentación técnica
- [docs/API.md](docs/API.md): Referencia de API
- [.cursorrules](.cursorrules): Reglas del proyecto para Cursor AI

---

**¡Gracias por contribuir a SQUIT!** 🚀

Tu contribución ayuda a mejorar el análisis de código SQL para toda la organización.
