# 📚 Índice de Documentación - SQUIT

Documentación completa del proyecto SQUIT organizada por categorías.

Última actualización: 2025-10-02

---

## 🚀 Inicio Rápido

**Nuevo en SQUIT?** Empieza aquí:

1. **Lee el [README principal](../README.md)** - Visión general y quick start
2. **Configura credenciales**:
   - Copia `.env.template` → `.env`
   - Descarga service account JSON → `.config/credentials.json`
   - Obtén Gemini API Key
   - Copia catálogo → `data/catalogo.csv`
3. **Ejecuta**: `python3 scripts/squit.py`

---

## 📁 Organización de Documentos

```
docs/
├── setup/          → Pipeline de datos y configuración inicial
├── usage/          → Cómo usar SQUIT (CLI, API, ejemplos)
├── development/    → Arquitectura y desarrollo avanzado
└── archive/        → Documentación histórica (referencia)
```

---

## 📊 1. SETUP - Pipeline y Configuración

### Configuración Inicial

- **[BigQuery Vector Complete](setup/BIGQUERY_VECTOR_COMPLETE.md)** ⭐ **GUÍA PRINCIPAL**
  - Pipeline completo de chunks + embeddings + índice vectorial
  - Paso a paso desde extracción hasta búsqueda
  - Tiempos: ~30min chunking, ~2-4h embeddings, ~10min índice
  - **Empieza aquí si vas a procesar código SQL**

- **[Extraction Guide](setup/EXTRACTION_GUIDE.md)**
  - Cómo extraer código SQL desde SQL Server
  - Script SQL para obtener objetos de todas las DBs
  - Carga a BigQuery

### Configuración de IA

- **[Models Standard](setup/MODELS_STANDARD.md)**
  - Configuración de modelos Gemini
  - ⭐ **gemini-2.5-flash** para agentes (RECOMENDADO)
  - ⭐ **gemini-embedding-001** para vectores (768 dims)
  - Parámetros: temperature, max_tokens, etc.

### Sistemas Opcionales

- **[Weaviate Setup](setup/WEAVIATE_SETUP.md)**
  - Setup de Weaviate (opcional, para sistemas alternativos)
  - Docker compose configuration
  - **Nota**: Sistema principal usa BigQuery nativo

---

## 💻 2. USAGE - Cómo Usar SQUIT

### Uso Principal

- **[Agentic ADK Guide](usage/AGENTIC_ADK_GUIDE.md)** ⭐ **SISTEMA PRINCIPAL**
  - Sistema agentico con Google ADK
  - MasterAgent + agentes especializados
  - Memoria conversacional multi-turn
  - Context caching + few-shot learning
  - **CLI**: `python3 scripts/squit.py`

- **[API Reference](usage/API.md)**
  - APIs de búsqueda y análisis
  - Endpoints de BigQuery Vector Search
  - Catalog Enricher API
  - Query Logger API

- **[Examples](usage/EXAMPLES.md)**
  - Ejemplos prácticos de uso
  - Scripts de demo
  - Casos de uso reales

---

## 🏗️ 3. DEVELOPMENT - Arquitectura

### Arquitectura del Sistema

- **[System Overview](development/SYSTEM_OVERVIEW.md)**
  - Arquitectura general
  - Flujo de datos
  - Componentes principales

- **[Technical Documentation](development/TECHNICAL.md)**
  - Decisiones técnicas
  - Trade-offs
  - Performance optimization

### Fases de Desarrollo

- **[Phase 1 Implementation](development/PHASE1_IMPLEMENTATION.md)**
  - Implementación de memoria conversacional
  - Context caching
  - Few-shot learning

- **[Phase 1 Executive Summary](development/PHASE1_SUMMARY_EXECUTIVE.md)**
  - Resumen ejecutivo de mejoras
  - Métricas de impacto
  - Next steps

### Optimizaciones

- **[Memory Optimization](development/MEMORY_OPTIMIZATION.md)**
  - Optimización de memoria conversacional
  - Estrategias de caching
  - Performance tuning

- **[Context Awareness Fix](development/CONTEXT_AWARENESS_FIX.md)**
  - Mejoras en awareness de contexto
  - Solución a problemas de memoria

---

## 📦 4. ESTRUCTURA DE ARCHIVOS

### Directorios Principales

```
squit/
├── .config/
│   ├── credentials.json          # ← Service account GCP (NO en git)
│   └── README.md                 # Instrucciones de credentials
│
├── data/
│   ├── catalogo.csv              # ← Catálogo de 280+ apps (NO en git)
│   ├── catalog.example.csv       # Ejemplo de catálogo
│   └── README.md                 # Documentación de catálogo
│
├── app/
│   ├── agentic_adk/              # ⭐ Sistema principal
│   │   ├── agents/               # Agentes especializados
│   │   │   ├── master_agent.py   # Orquestador
│   │   │   ├── code_search_agent.py
│   │   │   ├── explanation_agent.py
│   │   │   └── dependency_agent.py
│   │   ├── tools/                # Herramientas para agentes
│   │   │   ├── vector_search.py  # Búsqueda BigQuery
│   │   │   ├── code_reader.py
│   │   │   └── dependency_search.py
│   │   ├── catalog_enricher.py   # Enriquecimiento con catálogo
│   │   ├── query_logger.py       # Analytics de queries
│   │   └── config.py             # Configuración
│   │
│   ├── bigquery_vector/          # Pipeline de datos
│   │   ├── chunking_pipeline.py  # Chunking inteligente
│   │   ├── vector_search.py      # Búsquedas vectoriales
│   │   ├── progress_tracker.py   # Tracking de progreso
│   │   └── config.py             # Configuración BigQuery
│   │
│   └── squit_client/             # Cliente base BigQuery
│       ├── client.py
│       └── config.py
│
├── scripts/
│   ├── squit.py                  # ⭐ CLI PRINCIPAL (EMPEZAR AQUÍ)
│   ├── run_bigquery_pipeline.py  # Pipeline de datos
│   ├── demo_agentic_adk.py       # Demo completo
│   └── test_*.py                 # Tests y validaciones
│
├── docs/                         # ← ESTÁS AQUÍ
│   ├── INDEX.md                  # ⭐ Este archivo
│   ├── setup/                    # Guías de setup
│   ├── usage/                    # Guías de uso
│   └── development/              # Docs técnicos
│
├── .env                          # ← Configuración (crear desde template)
├── .env.template                 # Template de configuración
├── requirements.txt              # Dependencias Python
├── README.md                     # README principal
└── CONTRIBUTING.md               # Guía de contribución
```

---

## 🔑 Archivos de Configuración

| Archivo | Ubicación | Propósito | En Git |
|---------|-----------|-----------|--------|
| `.env` | Root | Variables de entorno | ❌ No |
| `.env.template` | Root | Template de config | ✅ Sí |
| `credentials.json` | `.config/` | Service account GCP | ❌ No |
| `catalogo.csv` | `data/` | Catálogo de 280+ apps | ❌ No |
| `catalog.example.csv` | `data/` | Ejemplo de catálogo | ✅ Sí |

### Variables de Entorno Clave

```bash
# Mínimo requerido en .env:
GOOGLE_CLOUD_PROJECT=tu-proyecto-id
GOOGLE_APPLICATION_CREDENTIALS=.config/credentials.json  # ← Ruta correcta
GEMINI_API_KEY=tu-api-key
GEMINI_CHAT_MODEL=gemini-2.5-flash  # ← Modelo recomendado

# BigQuery (tablas principales)
BIGQUERY_DATASET=deacero_sql_objects
BIGQUERY_TABLE=sql_objects_code
BIGQUERY_CHUNKS_TABLE=intelligent_chunks
BIGQUERY_EMBEDDINGS_TABLE=chunk_embeddings

# Embeddings
EMBEDDING_MODEL_NAME=gemini_embedding_model
EMBEDDING_ENDPOINT=gemini-embedding-001
EMBEDDING_DIMENSIONS=768
```

---

## 🎓 Flujos de Trabajo Comunes

### 1. Usuario Final (Solo Consultas)

```bash
# Setup inicial (una vez)
cp .env.template .env
# Editar .env con credenciales
cp tu-proyecto-xxxxx.json .config/credentials.json

# Usar SQUIT
python3 scripts/squit.py
```

### 2. Administrador (Procesar Datos)

```bash
# 1. Extraer código SQL (ver EXTRACTION_GUIDE.md)
# 2. Cargar a BigQuery
# 3. Ejecutar pipeline
python3 scripts/run_bigquery_pipeline.py

# Monitorear progreso
python3 scripts/monitor_pipeline.py
```

### 3. Desarrollador (Contribuir)

```bash
# Fork y clonar
git clone https://github.com/tu-usuario/squit.git
cd squit

# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Hacer cambios
git checkout -b feature/mi-feature

# Commit y PR
git commit -m "feat: mi cambio"
git push origin feature/mi-feature
```

---

## 🔗 Enlaces Rápidos

### Documentos Clave

- [README Principal](../README.md) - Visión general del proyecto
- [CONTRIBUTING](../CONTRIBUTING.md) - Cómo contribuir
- [BigQuery Vector Complete](setup/BIGQUERY_VECTOR_COMPLETE.md) - Pipeline completo
- [Agentic ADK Guide](usage/AGENTIC_ADK_GUIDE.md) - Sistema principal de agentes
- [Models Standard](setup/MODELS_STANDARD.md) - Configuración de modelos IA

### Scripts Importantes

- `scripts/squit.py` - CLI principal
- `scripts/run_bigquery_pipeline.py` - Pipeline de datos
- `scripts/demo_agentic_adk.py` - Demo completo del sistema

### Configuración

- `.env.template` - Template de variables de entorno
- `data/README.md` - Documentación de catálogo
- `.config/README.md` - Documentación de credenciales

---

## ❓ FAQ

### ¿Por dónde empiezo?

1. Lee el [README principal](../README.md)
2. Configura `.env` y credentials
3. Ejecuta `python3 scripts/squit.py`

### ¿Dónde van las credenciales?

- Service account JSON → `.config/credentials.json`
- API keys y config → `.env` (root)
- **Nunca** commitear estos archivos

### ¿Dónde está el catálogo?

- Catálogo real → `data/catalogo.csv` (280+ apps)
- Ejemplo → `data/catalog.example.csv`
- Sistema busca automáticamente en `data/`

### ¿Qué modelo de Gemini usar?

- **Chat/Agentes**: `gemini-2.5-flash` (recomendado)
- **Embeddings**: `gemini-embedding-001` (768 dims)
- Configurar en `.env`: `GEMINI_CHAT_MODEL=gemini-2.5-flash`

### ¿Cómo contribuir?

1. Lee [CONTRIBUTING.md](../CONTRIBUTING.md)
2. Fork el repo
3. Crea branch (`feature/` o `fix/`)
4. Commit con formato: `feat:`, `fix:`, `docs:`, etc.
5. Abre Pull Request

---

## 📞 Soporte

- **Issues**: [GitHub Issues](https://github.com/grupodeacero/squit/issues)
- **Docs**: Este directorio (`docs/`)
- **Contribución**: [CONTRIBUTING.md](../CONTRIBUTING.md)

---

**Última actualización**: 2025-10-02  
**Versión**: 2.0.0  
**Mantenido por**: Grupo DeAcero
