# Configuración - SQUIT

Documentación completa de configuración de variables de entorno, rutas y archivos.

**Última actualización:** 2025-10-02

---

## 📋 Variables de Entorno

### Archivo `.env`

El sistema usa un archivo `.env` en el root del proyecto para configuración.

**Crear desde template:**
```bash
cp .env.template .env
nano .env
```

### Variables Requeridas (Mínimo)

```bash
# Google Cloud Project
GOOGLE_CLOUD_PROJECT=tu-proyecto-id

# Credenciales (ruta correcta)
GOOGLE_APPLICATION_CREDENTIALS=.config/credentials.json

# Gemini API
GEMINI_API_KEY=tu-gemini-api-key
GEMINI_CHAT_MODEL=gemini-2.5-flash  # ← Modelo recomendado
```

### Variables BigQuery

```bash
# Dataset y tablas principales
BIGQUERY_DATASET=deacero_sql_objects
BIGQUERY_TABLE=sql_objects_code
BIGQUERY_CHUNKS_TABLE=intelligent_chunks
BIGQUERY_EMBEDDINGS_TABLE=chunk_embeddings
BIGQUERY_QUERY_HISTORY_TABLE=query_history
```

### Variables de Embeddings

```bash
# Configuración de modelo de embeddings
EMBEDDING_MODEL_NAME=gemini_embedding_model
EMBEDDING_ENDPOINT=gemini-embedding-001
EMBEDDING_DIMENSIONS=768  # ← Dimensiones optimizadas
```

### Variables Opcionales

```bash
# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR

# Región de Google Cloud
GCP_REGION=us-central1

# Weaviate (opcional, para sistemas alternativos)
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=

# Catálogo de aplicaciones (ruta custom)
# CATALOG_PATH=data/catalogo.csv  # Por defecto busca automáticamente
```

---

## 📁 Archivos de Configuración

### Tabla de Ubicaciones

| Archivo | Ubicación | Propósito | En Git |
|---------|-----------|-----------|--------|
| `.env` | Root | Variables de entorno | ❌ No |
| `.env.template` | Root | Template de config | ✅ Sí |
| `credentials.json` | `.config/` | Service account GCP | ❌ No |
| `catalogo.csv` | `data/` | Catálogo de 280+ apps | ❌ No |
| `catalog.example.csv` | `data/` | Ejemplo de catálogo | ✅ Sí |

### 1. Credenciales de Google Cloud

**Ubicación:** `.config/credentials.json`

**Obtener:**
1. Google Cloud Console → IAM & Admin → Service Accounts
2. Crear Service Account (si no existe)
3. Create Key → JSON
4. Descargar archivo JSON

**Configurar:**
```bash
# Copiar a la ubicación correcta
cp ~/Downloads/tu-proyecto-xxxxx.json .config/credentials.json

# Verificar permisos (debe ser privado)
chmod 600 .config/credentials.json

# Configurar en .env
echo "GOOGLE_APPLICATION_CREDENTIALS=.config/credentials.json" >> .env
```

**Permisos necesarios en GCP:**
- BigQuery Data Viewer
- BigQuery Job User
- BigQuery Data Editor (si ejecutas pipeline)

---

### 2. Catálogo de Aplicaciones

**Ubicación:** `data/catalogo.csv`

**Propósito:** Enriquece búsquedas con contexto de 280+ aplicaciones de negocio

**Búsqueda Automática:**

El sistema busca en este orden:
1. `data/catalogo.csv` ⭐ (prioridad 1)
2. `data/catalog.csv` (fallback)
3. `data/catalog.example.csv` (ejemplo)

**Formato del Catálogo:**

Formato completo (recomendado):
```csv
Name,Sistema Objeto,Descripcion,Proceso End To End,Tecnologia,...
Kayak,KAY - Kayak,Sistema de fechas de embarque,Logística,Python
Acerias,ACE - Acerias,Manejo de inventario acerias,Manufactura,Wtool
```

Formato simplificado (alternativa):
```csv
application_name,database_name,business_domain,description
KAYAK_APP,LogisticaDB,logistica,Sistema de fechas de embarque
```

**Configurar:**
```bash
# Si tienes el catálogo real
cp tu-catalogo-real.csv data/catalogo.csv

# Verificar carga
python3 -c "
from app.agentic_adk.catalog_enricher import CatalogEnricher
e = CatalogEnricher()
print(f'Apps: {len(e.catalog_df)}')
print(f'Path: {e.catalog_path}')
"
```

---

### 3. Configuración de BigQuery

**Tabla Principal:** `PROJECT.DATASET.TABLE`

**Ejemplo:**
```
dfor-prj-dev.deacero_sql_objects.sql_objects_code
```

**Variables:**
```bash
GOOGLE_CLOUD_PROJECT=dfor-prj-dev
BIGQUERY_DATASET=deacero_sql_objects
BIGQUERY_TABLE=sql_objects_code
```

**Tablas Generadas por Pipeline:**

| Tabla | Propósito | Tamaño Estimado |
|-------|-----------|-----------------|
| `intelligent_chunks` | Chunks con metadatos | ~5-10M rows |
| `chunk_embeddings` | Chunks + embeddings (768 dims) | ~5-10M rows |
| `pipeline_progress` | Tracking de progreso | ~100 rows |
| `pipeline_metrics` | Métricas detalladas | ~1K rows |
| `query_history` | Logs de queries | Crece con uso |

---

### 4. Configuración de Modelos IA

#### Gemini API Key

**Obtener:**
1. Ir a [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create API Key
3. Copiar key

**Configurar:**
```bash
echo "GEMINI_API_KEY=tu-api-key-aqui" >> .env
```

#### Modelos Recomendados

**Para Agentes (Chat):**
```bash
GEMINI_CHAT_MODEL=gemini-2.5-flash  # ← Recomendado
# Alternativas:
# - gemini-2.0-flash-thinking-exp  (experimental)
# - gemini-1.5-pro (más lento pero más preciso)
```

**Para Embeddings:**
```bash
EMBEDDING_MODEL_NAME=gemini_embedding_model
EMBEDDING_ENDPOINT=gemini-embedding-001
EMBEDDING_DIMENSIONS=768  # ← NO CAMBIAR (optimizado)
```

**⚠️ IMPORTANTE:**
- **NO usar** `gemini-2.0-flash-exp` (deprecado)
- **SIEMPRE usar** `gemini-2.5-flash` para agentes
- **NO cambiar** dimensiones de embeddings (768 está optimizado)

#### Parámetros de Generación

```python
# En código (opcional, ya configurados por defecto):
generation_config = {
    "temperature": 0.1,      # Baja para respuestas deterministas
    "max_output_tokens": 8000,
    "top_p": 0.95,
    "top_k": 40
}
```

---

## 🔧 Configuración por Componente

### MasterAgent (Sistema Agentico)

**Requiere:**
```bash
GEMINI_API_KEY=...
GEMINI_CHAT_MODEL=gemini-2.5-flash
GOOGLE_CLOUD_PROJECT=...
GOOGLE_APPLICATION_CREDENTIALS=.config/credentials.json
```

**Opcional:**
```bash
# Catálogo para enriquecimiento
# (se busca automáticamente en data/)
```

### CatalogEnricher

**Requiere:**
- Archivo `data/catalogo.csv` (o catalog.csv)

**Configuración custom (opcional):**
```python
from agentic_adk.catalog_enricher import CatalogEnricher
from pathlib import Path

# Ruta custom
enricher = CatalogEnricher(catalog_path=Path("mi-catalogo.csv"))
```

### BigQueryVectorSearch

**Requiere:**
```bash
GOOGLE_CLOUD_PROJECT=...
GOOGLE_APPLICATION_CREDENTIALS=.config/credentials.json
BIGQUERY_DATASET=...
BIGQUERY_EMBEDDINGS_TABLE=chunk_embeddings
EMBEDDING_MODEL_NAME=gemini_embedding_model
```

### QueryLogger

**Requiere:**
```bash
GOOGLE_CLOUD_PROJECT=...
GOOGLE_APPLICATION_CREDENTIALS=.config/credentials.json
BIGQUERY_DATASET=...
BIGQUERY_QUERY_HISTORY_TABLE=query_history
```

---

## 🔍 Validación de Configuración

### Script de Validación

```bash
# Crear script de validación
cat > validate_config.py << 'EOF'
#!/usr/bin/env python3
"""Valida configuración de SQUIT."""

import os
import sys
from pathlib import Path

# Agregar app al path
sys.path.insert(0, str(Path(__file__).parent / "app"))

def validate():
    """Valida configuración completa."""
    errors = []
    warnings = []
    
    # 1. Validar .env
    if not Path(".env").exists():
        errors.append(".env no existe (copiar desde .env.template)")
    
    # 2. Validar credenciales
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", ".config/credentials.json")
    if not Path(creds_path).exists():
        errors.append(f"Credenciales no encontradas: {creds_path}")
    
    # 3. Validar variables requeridas
    required_vars = [
        "GOOGLE_CLOUD_PROJECT",
        "GEMINI_API_KEY",
        "GEMINI_CHAT_MODEL"
    ]
    
    for var in required_vars:
        if not os.getenv(var):
            errors.append(f"Variable requerida falta: {var}")
    
    # 4. Validar modelo
    model = os.getenv("GEMINI_CHAT_MODEL", "")
    if "2.0-flash-exp" in model:
        warnings.append("⚠️  Modelo deprecado: usa gemini-2.5-flash")
    
    # 5. Validar catálogo
    if not Path("data/catalogo.csv").exists():
        warnings.append("Catálogo no encontrado: data/catalogo.csv (opcional)")
    else:
        from agentic_adk.catalog_enricher import CatalogEnricher
        enricher = CatalogEnricher()
        print(f"✅ Catálogo: {len(enricher.catalog_df)} apps")
    
    # 6. Test conexión BigQuery
    try:
        from google.cloud import bigquery
        client = bigquery.Client()
        client.query("SELECT 1").result()
        print("✅ Conexión BigQuery OK")
    except Exception as e:
        errors.append(f"Error BigQuery: {e}")
    
    # Reportar
    if errors:
        print("\n❌ ERRORES:")
        for err in errors:
            print(f"  - {err}")
        return False
    
    if warnings:
        print("\n⚠️  ADVERTENCIAS:")
        for warn in warnings:
            print(f"  - {warn}")
    
    print("\n✅ Configuración válida")
    return True

if __name__ == "__main__":
    sys.exit(0 if validate() else 1)
EOF

chmod +x validate_config.py
python3 validate_config.py
```

### Checklist de Configuración

- [ ] `.env` creado desde `.env.template`
- [ ] `GOOGLE_CLOUD_PROJECT` configurado
- [ ] `GOOGLE_APPLICATION_CREDENTIALS=.config/credentials.json`
- [ ] Archivo `.config/credentials.json` existe
- [ ] `GEMINI_API_KEY` configurado
- [ ] `GEMINI_CHAT_MODEL=gemini-2.5-flash`
- [ ] `data/catalogo.csv` copiado (opcional)
- [ ] Conexión BigQuery validada
- [ ] Tabla `sql_objects_code` existe en BigQuery

---

## 🐛 Troubleshooting

### Error: "credentials.json was not found"

**Problema:** Ruta incorrecta en `.env`

**Solución:**
```bash
# Verificar ruta
ls -la .config/credentials.json

# Actualizar .env
echo "GOOGLE_APPLICATION_CREDENTIALS=.config/credentials.json" >> .env
```

### Error: "Catálogo no encontrado"

**Problema:** Archivo de catálogo no existe

**Solución:**
```bash
# Verificar ubicación
ls -la data/catalogo.csv

# Si no existe, copiar desde ejemplo o tu archivo
cp tu-catalogo.csv data/catalogo.csv
```

### Error: "Model not found: gemini-2.0-flash-exp"

**Problema:** Modelo deprecado

**Solución:**
```bash
# Actualizar en .env
sed -i '' 's/gemini-2.0-flash-exp/gemini-2.5-flash/' .env
```

### Error: "BigQuery table not found"

**Problema:** Tabla no existe o proyecto incorrecto

**Solución:**
```bash
# Verificar proyecto
echo $GOOGLE_CLOUD_PROJECT

# Verificar tabla existe
bq show $GOOGLE_CLOUD_PROJECT:$BIGQUERY_DATASET.$BIGQUERY_TABLE
```

---

## 📚 Referencias

- [README Principal](../../README.md) - Setup inicial
- [.env.template](../../.env.template) - Template completo
- [data/README.md](../../data/README.md) - Documentación de catálogo
- [.config/README.md](../../.config/README.md) - Documentación de credenciales

---

**Última actualización:** 2025-10-02  
**Mantenido por:** Grupo DeAcero

