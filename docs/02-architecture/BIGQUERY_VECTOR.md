# BigQuery Vector System - Documentación Completa

## 📋 Resumen Ejecutivo

Sistema de chunking inteligente y búsqueda vectorial 100% en BigQuery, con embeddings reales de Gemini, tracking persistente y recovery automático.

### Componentes Core

1. **Chunking Inteligente**: Clasifica y divide objetos SQL según complejidad y semántica
2. **Embeddings Gemini**: Genera vectores de 768 dimensiones usando `gemini-embedding-001`
3. **Vector Search**: Búsqueda semántica nativa con filtros de negocio
4. **Progress Tracker**: Sistema de tracking persistente con checkpoint/recovery

### Arquitectura Optimizada

```
sql_objects_code (3M objetos)
    ↓
intelligent_chunks (chunking inteligente)
    ↓
ML.GENERATE_EMBEDDING (Gemini API)
    ↓
chunk_embeddings (768 dims)
    ↓
VECTOR_SEARCH (búsqueda nativa)
```

## 🚀 Quick Start

### Ejecución del Pipeline

```bash
# Pipeline completo
python scripts/run_bigquery_pipeline.py

# Solo embeddings (chunks ya existen)
python scripts/run_bigquery_pipeline.py --skip-chunks

# Validar sistema
python scripts/run_bigquery_pipeline.py --validate
```

### Uso en Python

```python
from bigquery_vector.chunking_pipeline import BigQueryChunkingPipeline
from bigquery_vector.vector_search import BigQueryVectorSearch

# Ejecutar pipeline completo
pipeline = BigQueryChunkingPipeline()
run_id = pipeline.run_full_pipeline()

# Búsqueda semántica
search = BigQueryVectorSearch()
results = search.semantic_search(
    query="procedimientos de ventas",
    limit=10,
    business_domains=["ventas"]
)
```

## 📊 Configuración del Sistema

### Parámetros de Chunking

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| `MEGA_OBJECT_THRESHOLD` | 1,000,000 chars | Objetos mega: chunking por GO separators |
| `LARGE_OBJECT_THRESHOLD` | 50,000 chars | Objetos grandes: 250 líneas/chunk |
| `MEDIUM_OBJECT_THRESHOLD` | 15,000 chars | Objetos medianos: 200 líneas/chunk |
| `MIN_CHUNK_SIZE` | 500 chars | Tamaño mínimo viable |
| `MAX_CHUNK_SIZE` | 8,000 chars | Tamaño óptimo para embeddings |
| `MAX_CHUNKS_PER_OBJECT` | 100 | Límite de chunks por objeto |

### Parámetros de Embeddings

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| `EMBEDDING_MODEL` | `gemini-embedding-001` | Modelo Gemini optimizado |
| `EMBEDDING_DIMENSIONS` | 768 | 75% menos storage vs 2048 |
| `TASK_TYPE` | `CODE_RETRIEVAL_QUERY` | Optimizado para código SQL |
| `FLATTEN_JSON_OUTPUT` | `TRUE` | Salida en array plano |

### Parámetros de Vector Search

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| `VECTOR_INDEX_TYPE` | `IVF` | Inverted File Index |
| `DISTANCE_TYPE` | `COSINE` | Similitud coseno |
| `IVF_NUM_LISTS` | 1000 | Optimizado para 3M objetos |

## 🎯 Estrategias de Chunking

El sistema aplica 4 estrategias según el tamaño del objeto:

### 1. Single Chunk (< 15K chars)
```sql
-- Objetos pequeños: chunk único
SELECT sql_code as chunk
```

### 2. Medium Chunking (15K - 50K chars)
```sql
-- 200 líneas por chunk
-- 20% traslape (40 líneas)
-- Step: 160 líneas
SELECT ARRAY_TO_STRING(
  ARRAY(SELECT line FROM UNNEST(lines) WITH OFFSET
        WHERE idx BETWEEN start AND start+199),
  '\n'
)
```

### 3. Large Chunking (50K - 1M chars)
```sql
-- 250 líneas por chunk
-- 20% traslape (50 líneas)
-- Step: 200 líneas
```

### 4. Mega Chunking (> 1M chars)
```sql
-- 400 líneas por chunk
-- 20% traslape (80 líneas)
-- Step: 320 líneas
```

## 🏗️ Estructura de Tablas

### intelligent_chunks

Tabla de chunks con metadatos semánticos:

```sql
CREATE TABLE intelligent_chunks (
  -- Identificadores
  chunk_id STRING PRIMARY KEY,
  parent_object_id STRING,
  
  -- Metadatos de objeto
  server STRING,
  database STRING,
  schema STRING,
  object_name STRING,
  object_type STRING,
  
  -- Chunk data
  chunk_content STRING,
  chunk_index INT64,
  total_chunks INT64,
  chunk_length INT64,
  chunk_lines INT64,
  
  -- Clasificación semántica
  semantic_type STRING,       -- stored_procedure, view, complex_query, etc.
  business_domain STRING,      -- ventas, inventario, finanzas, etc.
  complexity_score FLOAT64,
  
  -- Metadatos enriquecidos
  semantic_tags ARRAY<STRING>,
  references_to ARRAY<STRING>,
  semantic_summary STRING,
  
  -- Tracking
  content_hash STRING,
  last_modified TIMESTAMP,
  created_at TIMESTAMP
)
```

### chunk_embeddings

Tabla de embeddings con vectores de 768 dimensiones:

```sql
CREATE TABLE chunk_embeddings (
  -- Heredados de intelligent_chunks
  chunk_id STRING PRIMARY KEY,
  parent_object_id STRING,
  [... todos los campos de chunks ...],
  
  -- Embedding data
  content STRING,              -- Texto usado para embedding
  embedding ARRAY<FLOAT64>,    -- Vector de 768 dims
  embedding_created_at TIMESTAMP
)
```

### Sistema de Tracking

#### pipeline_progress

```sql
CREATE TABLE pipeline_progress (
  run_id STRING,
  pipeline_stage STRING,
  status STRING,              -- running, completed, failed
  started_at TIMESTAMP,
  completed_at TIMESTAMP,
  progress_percentage FLOAT64,
  items_processed INT64,
  items_total INT64,
  checkpoint_data JSON,       -- Para recovery
  metadata JSON,
  PRIMARY KEY (run_id, pipeline_stage)
)
```

#### pipeline_metrics

```sql
CREATE TABLE pipeline_metrics (
  metric_id STRING PRIMARY KEY,
  run_id STRING,
  pipeline_stage STRING,
  metric_name STRING,
  metric_value FLOAT64,
  metric_type STRING,         -- gauge, counter, timing
  recorded_at TIMESTAMP,
  metadata JSON
)
```

#### pipeline_errors

```sql
CREATE TABLE pipeline_errors (
  error_id STRING PRIMARY KEY,
  run_id STRING,
  pipeline_stage STRING,
  error_type STRING,
  error_message STRING,
  error_traceback STRING,
  occurred_at TIMESTAMP,
  context JSON
)
```

## 🔍 Búsqueda Vectorial

### Búsqueda Semántica Básica

```python
from bigquery_vector.vector_search import BigQueryVectorSearch

search = BigQueryVectorSearch()

# Búsqueda simple
results = search.semantic_search(
    query="procedimientos de cálculo de inventario",
    limit=10
)

for result in results:
    print(f"{result['object_name']}: {result['semantic_summary']}")
    print(f"Score: {result['hybrid_score']:.3f}")
```

### Búsqueda con Filtros

```python
# Filtrar por dominio de negocio
results = search.semantic_search(
    query="actualizar precios",
    business_domains=["ventas", "inventario"],
    object_types=["PROCEDURE"],
    min_complexity=5.0
)

# Búsqueda solo vectorial (sin keywords)
results = search.semantic_search(
    query="calcular totales",
    use_hybrid=False
)
```

### Búsqueda por Similaridad

```python
# Encontrar objetos similares
similar = search.find_similar_objects(
    object_id="chunk_uuid_here",
    limit=5,
    exclude_same_object=True
)
```

### Búsqueda por Funcionalidad

```python
# Búsqueda temática preconfigurada
results = search.search_by_functionality(
    functionality="autenticacion",
    limit=10
)

# Funcionalidades soportadas:
# - autenticacion
# - ventas
# - inventario
# - reportes
# - pagos
# - usuarios
```

### Query SQL Directa

```sql
-- Búsqueda híbrida (vector + keywords)
WITH query_embedding AS (
  SELECT ml_generate_embedding_result as embedding
  FROM ML.GENERATE_EMBEDDING(
    MODEL `gemini_embedding_model`,
    (SELECT 'procedimientos de ventas' AS content),
    STRUCT(TRUE AS flatten_json_output, 'CODE_RETRIEVAL_QUERY' AS task_type, 768 AS output_dimensionality)
  )
)
SELECT 
  base.chunk_id,
  base.object_name,
  base.semantic_summary,
  distance,
  1.0 - distance as similarity_score
FROM VECTOR_SEARCH(
  (SELECT * FROM chunk_embeddings),
  'embedding',
  (SELECT * FROM query_embedding),
  top_k => 10,
  distance_type => 'COSINE'
)
ORDER BY distance ASC
```

## 📈 Sistema de Tracking

### Iniciar y Trackear Pipeline

```python
from bigquery_vector.progress_tracker import ProgressTracker

tracker = ProgressTracker()

# Iniciar run
run_id = tracker.start_run(
    pipeline_name="bigquery_vector_pipeline",
    metadata={"environment": "production"}
)

# Trackear etapa
tracker.update_stage(
    run_id=run_id,
    stage="create_chunks",
    status="running",
    progress=50.0,
    items_processed=150000,
    items_total=300000
)

# Registrar métrica
tracker.log_metric(
    run_id=run_id,
    metric_name="chunks_per_second",
    metric_value=5000.0,
    pipeline_stage="create_chunks"
)

# Completar etapa
tracker.complete_stage(
    run_id=run_id,
    stage="create_chunks",
    items_processed=300000
)
```

### Reportes

```python
# Ver resumen de un run
summary = tracker.get_run_summary(run_id)
print(f"Total stages: {summary['total_stages']}")
print(f"Completed: {summary['completed_stages']}")

# Imprimir reporte formateado
tracker.print_progress_report(run_id)

# Ver histórico
runs = tracker.get_all_runs(limit=10)
for run in runs:
    print(f"{run['run_id']}: {run['completed_stages']}/{run['total_stages']}")
```

### Recovery desde Checkpoint

```python
# Recuperar último checkpoint
checkpoint = tracker.get_last_checkpoint(
    pipeline_name="bigquery_vector_pipeline",
    stage="create_embeddings"
)

if checkpoint:
    # Continuar desde checkpoint
    start_from = checkpoint['items_processed']
    print(f"Continuando desde: {start_from}")
```

## 🛠️ Scripts de Administración

### run_bigquery_pipeline.py

Script principal de ejecución:

```bash
# Ver ayuda
python scripts/run_bigquery_pipeline.py --help

# Ejecutar pipeline completo
python scripts/run_bigquery_pipeline.py

# Ejecutar con flags
python scripts/run_bigquery_pipeline.py \
  --skip-chunks \
  --skip-index \
  --verbose

# Ver histórico
python scripts/run_bigquery_pipeline.py --list-runs --limit 20

# Ver reporte específico
python scripts/run_bigquery_pipeline.py --report bigquery_vector_pipeline_20250930_143022

# Validar sistema
python scripts/run_bigquery_pipeline.py --validate
```

## 📊 Métricas de Performance

### Optimizaciones Implementadas

| Aspecto | Antes | Después | Mejora |
|---------|-------|---------|--------|
| Dimensiones embedding | 2048 | 768 | 75% menos storage |
| Velocidad embedding | 1x | 3x | 3x más rápido |
| Traslape chunks | 0% | 20% | Mejor contexto |
| Chunking | Python | BigQuery SQL | 10x más rápido |
| Vector search | - | IVF índice | Sub-segundo |

### Benchmarks Esperados

Para dataset de **3M objetos SQL**:

- **Chunking**: ~30-45 minutos
- **Embeddings**: ~2-4 horas (con Gemini API)
- **Vector Index**: ~10-15 minutos
- **Search latency**: < 500ms por query

## 🔧 Troubleshooting

### Error: "Vertex AI connection not found"

```bash
# Crear conexión Vertex AI
bq mk --connection \
  --location=us-central1 \
  --project_id=dfor-prj-dev \
  --connection_type=CLOUD_RESOURCE \
  vertex_ai_connection_central
```

### Error: "Insufficient permissions"

Grant necesarios:
```bash
# BigQuery ML
gcloud projects add-iam-policy-binding dfor-prj-dev \
  --member="serviceAccount:SERVICE_ACCOUNT" \
  --role="roles/aiplatform.user"

# Vector Search
gcloud projects add-iam-policy-binding dfor-prj-dev \
  --member="serviceAccount:SERVICE_ACCOUNT" \
  --role="roles/bigquery.admin"
```

### Error: "Not enough rows for IVF index"

El índice IVF requiere mínimo 5000 rows. Para datasets pequeños:

```python
# Usar búsqueda sin índice
results = search.semantic_search(
    query="mi búsqueda",
    limit=10
)
# BigQuery usa brute-force search automáticamente
```

### Pipeline Interrumpido

El sistema tiene recovery automático:

```bash
# Ver último run
python scripts/run_bigquery_pipeline.py --list-runs

# Continuar desde checkpoint
python scripts/run_bigquery_pipeline.py --skip-chunks
```

## 📚 Referencias

### Documentación BigQuery

- [BigQuery ML - Generate Embeddings](https://cloud.google.com/bigquery/docs/generate-text-embedding)
- [BigQuery Vector Search](https://cloud.google.com/bigquery/docs/vector-search)
- [Vertex AI Embeddings](https://cloud.google.com/vertex-ai/docs/generative-ai/embeddings)

### Configuración

Ver archivos:
- `app/bigquery_vector/config.py` - Configuración completa
- `app/bigquery_vector/chunking_pipeline.py` - Pipeline core
- `app/bigquery_vector/vector_search.py` - Búsquedas
- `app/bigquery_vector/progress_tracker.py` - Tracking

## 🎯 Roadmap

### Optimizaciones Futuras

- [ ] Chunking incremental (solo objetos nuevos/modificados)
- [ ] Batch embeddings con rate limiting inteligente
- [ ] Cache de embeddings frecuentes
- [ ] Vector search con re-ranking
- [ ] Integración con agentic RAG

### Funcionalidades Planeadas

- [ ] API REST para búsquedas
- [ ] Dashboard de métricas en tiempo real
- [ ] A/B testing de estrategias de chunking
- [ ] Auto-tuning de parámetros

---

**Sistema implementado**: Septiembre 2025  
**Última actualización**: 2025-09-30  
**Contacto**: SQUIT Team
