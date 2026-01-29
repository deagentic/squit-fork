# SQUIT Agentic RAG - Phase 1 Implementation

## 🎯 Overview

El sistema Agentic RAG de SQUIT implementa un enfoque inteligente para analizar y entender código SQL legacy usando múltiples agentes especializados y Weaviate como vector database.

## 🏗️ Arquitectura del Sistema

### Componentes Principales

```
User Query → Master Agent → Coordinate Specialized Agents:
                         ├── Code Search Agent (Vector + Hybrid Search)
                         ├── Dependency Analysis Agent (Graph Analysis)
                         ├── Pattern Analysis Agent (ML Patterns)
                         └── Schema Analysis Agent (Metadata)
                              ↓
                         Synthesize & Validate Results
                              ↓
                         Intelligent Response
```

### Collections en Weaviate

#### 1. **CodeObjects** - Objetos de código SQL
- **Propósito**: Almacenar código SQL con embeddings semánticos
- **Vectorización**: `text-embedding-004` (768 dimensiones) - Gemini
- **Campos clave**: 
  - `sql_code`: Código SQL completo
  - `code_summary`: Resumen generado por IA
  - `business_context`: Contexto de negocio extraído
  - `complexity_score`: Score de complejidad (0-100)
  - `tags`: Tags automáticos por análisis

#### 2. **Dependencies** - Relaciones entre objetos
- **Propósito**: Mapear dependencias y relaciones
- **Campos clave**:
  - `source_object_id`, `target_object_id`: Objetos relacionados
  - `dependency_type`: Tipo de relación (FK, VIEW, CALL)
  - `relationship_strength`: Fuerza de la relación (0.0-1.0)
  - `is_critical`: Si es crítica para el negocio

#### 3. **Metadata** - Contexto adicional
- **Propósito**: Información contextual del sistema
- **Campos clave**:
  - `entity_type`: Tipo (server, database, schema)
  - `business_domain`: Dominio (ventas, finanzas, etc.)
  - `criticality_level`: Nivel de criticidad

#### 4. **CodePatterns** - Patrones identificados
- **Propósito**: Patrones de código detectados automáticamente
- **Campos clave**:
  - `pattern_name`: Nombre del patrón
  - `pattern_type`: Tipo (DESIGN_PATTERN, ANTI_PATTERN)
  - `confidence_score`: Confianza en la identificación

## 🤖 Agentes Implementados

### 1. **MasterAgent** - Coordinador Principal
- **Función**: Analiza consultas y coordina agentes especializados
- **Capacidades**:
  - Query intent analysis
  - Agent routing y coordination
  - Response synthesis
  - Memory management

### 2. **CodeSearchAgent** - Búsqueda de Código
- **Función**: Búsqueda semántica y por patrones en código
- **Capacidades**:
  - Semantic search usando embeddings
  - Keyword search en metadata
  - Hybrid search (vector + BM25)
  - Result analysis con IA

### 3. **DependencyAnalysisAgent** - Análisis de Dependencias
- **Función**: Mapea relaciones y analiza impacto
- **Capacidades**:
  - Dependency mapping
  - Impact analysis
  - Risk assessment
  - Circular dependency detection

## 🔄 Pipeline de Ingesta

### Proceso ETL BigQuery → Weaviate

1. **Extracción**: Query optimizada desde BigQuery
2. **Transformación**: 
   - Análisis de código con IA
   - Extracción de tags automáticos
   - Cálculo de métricas de complejidad
   - Generación de embeddings
3. **Carga**: Inserción en Weaviate con metadatos enriquecidos

### Características del Pipeline
- **Procesamiento paralelo**: 4 workers por defecto
- **Análisis inteligente**: OpenAI para contexto semántico
- **Deduplicación**: Por content_hash
- **Incremental updates**: Solo objetos modificados
- **Error handling**: Retry logic y fallbacks

## 🚀 Configuración y Uso

### 1. Configuración Inicial

```bash
# Copiar configuración de ejemplo
cp env.example .env

# Editar variables de entorno
# GEMINI_API_KEY=tu-api-key
# GOOGLE_APPLICATION_CREDENTIALS=./credentials.json

# Configurar sistema completo
make agentic-setup
```

### 2. Verificar Salud del Sistema

```bash
# Verificar que todo esté funcionando
make agentic-health

# Ver logs en tiempo real
make agentic-logs
```

### 3. Ejecutar Demo

```bash
# Demo completo con ingesta de muestra
make agentic-demo

# Solo ingesta (sin demo)
make agentic-ingest
```

### 4. Desarrollo

```bash
# Entorno de desarrollo con Jupyter
make agentic-dev

# Jupyter disponible en: http://localhost:8888
# Weaviate UI en: http://localhost:8080
```

## 💻 Uso Programático

### Inicialización Básica

```python
from agentic_rag import WeaviateClient, MasterAgent, IngestionPipeline
from squit_client import BigQueryClient

# Inicializar clientes
bigquery_client = BigQueryClient()
weaviate_client = WeaviateClient()

# Configurar schema
weaviate_client.create_schema()

# Inicializar agente maestro
master_agent = MasterAgent(weaviate_client)
```

### Consultas Agentic

```python
# Consulta simple
response = master_agent.process_query(
    "¿Dónde está la lógica de autenticación?"
)
print(response["response"])

# Consulta con contexto
response = master_agent.process_query(
    "¿Qué pasa si modifico la tabla Usuarios?",
    context={"object_id": "SERVER1|DB|schema|Usuarios"}
)
```

### Pipeline de Ingesta

```python
# Crear pipeline
pipeline = IngestionPipeline(bigquery_client, weaviate_client)

# Ingesta completa (cuidado: puede tomar tiempo)
stats = pipeline.run_full_ingestion(limit=1000)

# Ingesta incremental (cambios recientes)
stats = pipeline.run_incremental_update()

# Ingesta filtrada
filters = {
    "object_type": ["PROCEDURE", "FUNCTION"],
    "server": "SRVDBDES05\\BASCULA"
}
stats = pipeline.run_full_ingestion(limit=500, filters=filters)
```

## 🔍 Ejemplos de Consultas

### Búsqueda Semántica
```python
# Buscar funcionalidad específica
response = master_agent.process_query(
    "Busca código relacionado con facturación y pagos"
)

# Buscar por patrón técnico
response = master_agent.process_query(
    "¿Dónde se usan transacciones en el código?"
)
```

### Análisis de Dependencias
```python
# Análisis de impacto
response = master_agent.process_query(
    "¿Qué objetos dependen de la tabla ClientesMaster?",
    context={"object_id": "SRVDBDES05\\BASCULA|CRM|dbo|ClientesMaster"}
)

# Análisis de riesgo
response = master_agent.process_query(
    "¿Es seguro modificar el procedimiento sp_CalcularFactura?"
)
```

### Análisis Arquitectónico
```python
# Entender módulos
response = master_agent.process_query(
    "¿Cómo está organizado el módulo de ventas?"
)

# Identificar patrones
response = master_agent.process_query(
    "¿Qué patrones de diseño se usan en el sistema?"
)
```

## 📊 Métricas y Monitoreo

### Health Check
```bash
# Verificar salud completa
make agentic-health

# Solo Weaviate
curl http://localhost:8080/v1/.well-known/ready
```

### Estadísticas de Collections
```python
# Obtener estadísticas
stats = weaviate_client.get_collection_stats()
print(f"CodeObjects: {stats['CodeObjects']:,}")
print(f"Dependencies: {stats['Dependencies']:,}")
```

### Performance Metrics
- **Query response time**: ~2-5 segundos
- **Ingestion rate**: ~100 objetos/minuto
- **Search accuracy**: Depende de calidad de embeddings
- **Memory usage**: ~1-2GB para Weaviate

## 🔧 Configuración Avanzada

### Variables de Entorno Clave

```bash
# OpenAI (requerido)
OPENAI_API_KEY=sk-your-key

# Weaviate
WEAVIATE_URL=http://localhost:8080

# Agentes
AGENT_TEMPERATURE=0.1  # Baja para consistencia
AGENT_LOG_LEVEL=INFO

# Pipeline
INGESTION_BATCH_SIZE=100
PARALLEL_WORKERS=4
```

### Configuración de Modelos

```python
# En agentic_rag/config.py
EMBEDDING_MODEL = "text-embedding-3-small"  # Optimizado para código
LLM_MODEL = "gpt-4o-mini"  # Para reasoning
HYBRID_SEARCH_ALPHA = 0.7  # Balance vector vs keyword
```

## 🚨 Troubleshooting

### Problemas Comunes

#### Weaviate no inicia
```bash
# Verificar Docker
docker ps | grep weaviate

# Ver logs
make agentic-logs

# Resetear si es necesario
make agentic-reset
```

#### Error de API Key
```bash
# Verificar variable de entorno
echo $OPENAI_API_KEY

# Verificar en contenedor
docker-compose -f docker-compose.weaviate.yml run --rm squit-agentic env | grep OPENAI
```

#### Problemas de memoria
```bash
# Reducir batch size
export INGESTION_BATCH_SIZE=50
export PARALLEL_WORKERS=2
```

## 🔮 Próximos Pasos (Phase 2+)

### Funcionalidades Pendientes
1. **Pattern Analysis Agent**: Identificación automática de patrones
2. **Schema Analysis Agent**: Análisis de estructura de BD
3. **Web Interface**: UI para consultas interactivas
4. **Advanced Analytics**: Métricas de calidad y complejidad
5. **Recommendation Engine**: Sugerencias de modernización

### Optimizaciones Planeadas
1. **Custom embeddings**: Entrenar modelo específico para SQL
2. **Graph algorithms**: Algoritmos avanzados para dependencias
3. **Caching layer**: Redis para consultas frecuentes
4. **Batch processing**: Procesamiento masivo optimizado

## 📚 Referencias

- [Weaviate Agentic RAG Guide](https://weaviate.io/blog/what-is-agentic-rag)
- [Implementing Agentic RAG](https://weaviate.io/blog/what-is-agentic-rag#implementing-agentic-rag)
- Documentación técnica en `docs/TECHNICAL.md`
- Ejemplos de uso en `docs/EXAMPLES.md`

---

**Phase 1 Status**: ✅ **COMPLETADA**
- Weaviate configurado y funcionando
- Schema diseñado para 4 collections
- Pipeline de ingesta implementado
- Agentes básicos funcionando
- Demo interactivo disponible

**Siguiente**: Phase 2 - Advanced Agents & Web Interface
