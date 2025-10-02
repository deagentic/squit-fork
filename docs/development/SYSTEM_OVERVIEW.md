# SQUIT - Sistema BigQuery Vector: Overview

## ✅ Estado Actual del Sistema

**Última actualización**: 2025-09-30

### Componentes Implementados

#### 1. **Pipeline de Chunking Inteligente** ✅
- Clasificación semántica automática de objetos SQL
- 4 estrategias de chunking según tamaño (single, medium, large, mega)
- Traslape del 20% para contexto óptimo
- Extracción de metadatos de negocio (7 dominios)
- Tags semánticos y referencias automáticas

**Archivo**: `app/bigquery_vector/chunking_pipeline.py`

#### 2. **Generación de Embeddings con Gemini** ✅
- Integración nativa con `gemini-embedding-001`
- 768 dimensiones (75% menos storage vs 2048)
- Task type: `CODE_RETRIEVAL_QUERY`
- Modelo remoto en BigQuery ML

**Archivo**: `app/bigquery_vector/chunking_pipeline.py` (método `create_embeddings_table`)

#### 3. **Vector Search Nativo** ✅
- Búsqueda semántica con VECTOR_SEARCH
- Búsqueda híbrida (70% vector + 30% keywords)
- Filtros por dominio, tipo, complejidad
- Búsqueda por similaridad
- Análisis de patrones del codebase

**Archivo**: `app/bigquery_vector/vector_search.py`

#### 4. **Sistema de Tracking Robusto** ✅
- Persistencia de progreso en BigQuery
- Checkpoint/recovery automático
- Métricas detalladas por etapa
- Logging de errores con traceback
- Reportes ejecutivos

**Archivo**: `app/bigquery_vector/progress_tracker.py`

#### 5. **Scripts de Administración** ✅
- `run_bigquery_pipeline.py`: Ejecutor principal con flags
- `monitor_pipeline.py`: Monitor en tiempo real
- Validación de sistema
- Histórico de runs

**Directorio**: `scripts/`

#### 6. **Documentación Completa** ✅
- Documentación técnica completa
- Ejemplos de uso
- Troubleshooting
- Configuración detallada

**Archivo**: `docs/BIGQUERY_VECTOR_COMPLETE.md`

#### 7. **Protección de Credenciales** ✅
- `.gitignore` robusto
- `env.example` con todas las variables
- Protección de credentials.json, API keys, logs

**Archivos**: `.gitignore`, `env.example`

---

## 📊 Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                   sql_objects_code                          │
│              (3M+ objetos SQL originales)                   │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│              intelligent_chunks                             │
│  • Clasificación semántica (8 tipos)                       │
│  • Dominios de negocio (7 dominios)                        │
│  • Chunking inteligente (4 estrategias)                    │
│  • Metadatos enriquecidos                                  │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│      ML.GENERATE_EMBEDDING (Gemini Integration)            │
│  • Modelo: gemini-embedding-001                            │
│  • Dimensiones: 768                                        │
│  • Task: CODE_RETRIEVAL_QUERY                              │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│              chunk_embeddings                               │
│  • Vectores de 768 dims                                    │
│  • Heredados: metadatos + clasificación                    │
│  • Optimizado para búsqueda                                │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│         VECTOR_SEARCH + Índice IVF                          │
│  • Búsqueda semántica < 500ms                              │
│  • Filtros de negocio                                      │
│  • Scoring híbrido                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Tablas del Sistema

### Tablas de Datos

| Tabla | Rows Esperados | Descripción |
|-------|----------------|-------------|
| `sql_objects_code` | ~3M | Objetos SQL originales |
| `intelligent_chunks` | ~5-10M | Chunks con metadatos |
| `chunk_embeddings` | ~5-10M | Chunks + embeddings (768 dims) |

### Tablas de Tracking

| Tabla | Descripción |
|-------|-------------|
| `pipeline_progress` | Progreso de cada etapa del pipeline |
| `pipeline_metrics` | Métricas detalladas (timing, counts) |
| `pipeline_errors` | Errores con traceback completo |

---

## 🚀 Comandos Principales

### Pipeline Completo

```bash
# Ejecutar todo
python scripts/run_bigquery_pipeline.py

# Solo embeddings (chunks ya existen)
python scripts/run_bigquery_pipeline.py --skip-chunks

# Sin crear índice (para testing con < 5K rows)
python scripts/run_bigquery_pipeline.py --skip-index
```

### Monitoreo

```bash
# Monitor en tiempo real
python scripts/monitor_pipeline.py

# Monitor de run específico
python scripts/monitor_pipeline.py --run-id RUN_ID
```

### Reportes

```bash
# Ver histórico
python scripts/run_bigquery_pipeline.py --list-runs

# Reporte de un run
python scripts/run_bigquery_pipeline.py --report RUN_ID

# Validar sistema
python scripts/run_bigquery_pipeline.py --validate
```

### Uso Programático

```python
from bigquery_vector.chunking_pipeline import BigQueryChunkingPipeline
from bigquery_vector.vector_search import BigQueryVectorSearch

# Pipeline
pipeline = BigQueryChunkingPipeline()
run_id = pipeline.run_full_pipeline()

# Búsqueda
search = BigQueryVectorSearch()
results = search.semantic_search(
    query="procedimientos de ventas",
    business_domains=["ventas"],
    limit=10
)
```

---

## 📈 Performance Esperado

### Dataset: 3M objetos SQL

| Etapa | Tiempo | Throughput |
|-------|--------|------------|
| Chunking | ~30-45 min | ~1-2K chunks/seg |
| Embeddings | ~2-4 horas | ~300-500 embeds/seg |
| Vector Index | ~10-15 min | - |
| **Total** | **~3-5 horas** | - |

### Búsquedas

- **Latencia**: < 500ms por query
- **Throughput**: > 100 queries/seg
- **Precisión**: @10 > 0.85 (esperado)

---

## 🔧 Configuración Clave

Ver `app/bigquery_vector/config.py` para configuración completa.

### Chunking

```python
MEGA_OBJECT_THRESHOLD = 1_000_000  # 1M chars
LARGE_OBJECT_THRESHOLD = 50_000    # 50K chars
MEDIUM_OBJECT_THRESHOLD = 15_000   # 15K chars
MIN_CHUNK_SIZE = 500               # Mínimo viable
MAX_CHUNK_SIZE = 8_000             # Óptimo
MAX_CHUNKS_PER_OBJECT = 100        # Límite
```

### Embeddings

```python
EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSIONS = 768  # Optimizado
TASK_TYPE = "CODE_RETRIEVAL_QUERY"
```

### Vector Index

```python
VECTOR_INDEX_TYPE = "IVF"
DISTANCE_TYPE = "COSINE"
IVF_NUM_LISTS = 1000  # Para ~3M objetos
```

---

## 📚 Documentación

| Documento | Descripción |
|-----------|-------------|
| `BIGQUERY_VECTOR_COMPLETE.md` | Documentación técnica completa |
| `BIGQUERY_VECTOR_SYSTEM.md` | Overview del sistema original |
| `ESTADO_ACTUAL_SISTEMA.md` | Estado general del proyecto |
| `TECHNICAL.md` | Detalles técnicos |
| `API.md` | Referencia de APIs |

---

## 🔐 Seguridad

### Archivos Protegidos por .gitignore

- ✅ `.env` y variantes
- ✅ `credentials.json` y service accounts
- ✅ Archivos de logs (`*.log`)
- ✅ `__pycache__` y `.pyc`
- ✅ Archivos temporales y cache
- ✅ Documentos privados
- ✅ Datos locales y exports
- ✅ Configuraciones de IDEs

### Setup de Credenciales

```bash
# 1. Copiar template
cp env.example .env

# 2. Editar con valores reales
nano .env

# 3. Descargar service account de GCP
# https://console.cloud.google.com/iam-admin/serviceaccounts

# 4. Guardar como credentials.json
mv ~/Downloads/key.json ./credentials.json

# 5. Verificar que están ignorados
git check-ignore .env credentials.json
```

---

## 🎯 Próximos Pasos

### Optimizaciones

- [ ] Chunking incremental (solo nuevos/modificados)
- [ ] Batch processing con rate limiting
- [ ] Cache de embeddings frecuentes
- [ ] Re-ranking de resultados

### Features

- [ ] API REST para búsquedas
- [ ] Dashboard de métricas
- [ ] A/B testing de estrategias
- [ ] Auto-tuning de parámetros

### Integración

- [ ] Conectar con Agentic RAG existente
- [ ] Cliente Python para búsquedas
- [ ] CLI interactiva

---

## 📞 Referencias Rápidas

### GCP Console

- **BigQuery**: https://console.cloud.google.com/bigquery
- **Vertex AI**: https://console.cloud.google.com/vertex-ai
- **IAM**: https://console.cloud.google.com/iam-admin

### Documentación Oficial

- **BigQuery ML**: https://cloud.google.com/bigquery/docs/generate-text-embedding
- **Vector Search**: https://cloud.google.com/bigquery/docs/vector-search
- **Gemini API**: https://ai.google.dev/docs

### Archivos Principales

```
squit/
├── app/bigquery_vector/
│   ├── config.py               # Configuración
│   ├── chunking_pipeline.py    # Pipeline core
│   ├── vector_search.py        # Búsquedas
│   └── progress_tracker.py     # Tracking
├── scripts/
│   ├── run_bigquery_pipeline.py  # Ejecutor
│   └── monitor_pipeline.py       # Monitor
├── docs/
│   └── BIGQUERY_VECTOR_COMPLETE.md
├── .gitignore                  # Protección
└── env.example                 # Template
```

---

**Sistema listo para producción** ✅  
**Documentación completa** ✅  
**Credenciales protegidas** ✅  
**Tracking robusto** ✅
