# Scripts Directory

Scripts organizados por propósito y uso.

## Estructura

```
scripts/
├── prod/          # Scripts de producción
├── dev/           # Scripts de desarrollo y testing
├── tools/         # Herramientas y utilities
└── *.py           # Scripts principales de acceso rápido
```

## Scripts Principales (Root)

- `squit.py` - CLI principal interactivo
- `run_bigquery_pipeline.py` - Ejecutor de pipeline completo

## Scripts de Producción (`prod/`)

Scripts para operaciones productivas y deployment:

- `bigquery_create_chunks.py` - Crear chunks inteligentes
- `bigquery_generate_embeddings.py` - Generar embeddings
- `bigquery_search_chunks.py` - Búsquedas vectoriales
- `migrate_all_data.py` - Migración completa de datos
- `setup_vertex_ai_connection.py` - Setup de Vertex AI
- `verify_bigquery_access.py` - Verificación de acceso

## Scripts de Desarrollo (`dev/`)

Scripts para testing, validación y demos:

- `demo_agentic_adk.py` - Demo del sistema agentic
- `demo_simple.py` - Demo simplificado
- `validate_phase1.py` - Validación Phase 1
- `test_*.py` - Scripts de testing
- `monitor_*.py` - Monitoring y observabilidad

## Scripts de Herramientas (`tools/`)

Utilidades y análisis:

- `analyze_bigquery_schema.py` - Análisis de schema
- `compare_vector_systems.py` - Comparación de sistemas
- `clean_code.py` - Limpieza de código
- `extract_sql_server_code.py` - Extracción de SQL Server

## Uso

### Desarrollo
```bash
# Demo interactivo
python3 scripts/dev/demo_agentic_adk.py

# Validar sistema
python3 scripts/dev/validate_phase1.py
```

### Producción
```bash
# Pipeline completo
python3 scripts/run_bigquery_pipeline.py

# Búsquedas
python3 scripts/prod/bigquery_search_chunks.py
```

### Herramientas
```bash
# Analizar datos
python3 scripts/tools/analyze_bigquery_schema.py
```

