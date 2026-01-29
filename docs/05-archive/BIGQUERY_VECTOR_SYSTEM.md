# 🧠 BigQuery Vector Search System

Sistema de chunking inteligente y búsqueda vectorial 100% nativo en BigQuery, optimizado para objetos SQL masivos con embeddings semánticos usando Gemini.

## 🎯 Arquitectura del Sistema

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   BigQuery      │    │  Smart Chunking  │    │ Vector Search   │
│ sql_objects_code│───▶│     Pipeline     │───▶│   + Embeddings  │
│   (3.4M objs)   │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │                           │
                              ▼                           ▼
                    ┌──────────────────┐    ┌─────────────────┐
                    │ intelligent_chunks│    │ chunk_embeddings│
                    │  (~5M chunks)     │    │  (Gemini-001)   │
                    └──────────────────┘    └─────────────────┘
```

## 🚀 Comandos Principales

### Pipeline Completo
```bash
# Ejecutar pipeline completo (recomendado)
make bigquery-full

# O paso a paso:
make create-chunks      # Crear chunks inteligentes
make analyze-data       # Analizar calidad
make search-chunks      # Probar búsquedas
```

### Análisis y Diagnóstico
```bash
make analyze-source     # Analizar datos originales
make analyze-quality    # Calidad de chunks
make check-readiness    # ¿Listo para búsquedas?
make compare-systems    # BigQuery vs Weaviate
```

### Búsquedas
```bash
make search-chunks      # Demo de búsquedas
make search-interactive # Modo interactivo
make analyze-patterns   # Patrones del codebase
```

## 🧩 Estrategia de Chunking

### Chunking Inteligente por Tamaño

| Tamaño Objeto | Estrategia | Chunks Estimados | Ejemplo |
|---------------|------------|------------------|---------|
| >1M chars | **Mega chunking** | ~1,500 | `Dem_Configuracion_Fallas_Demora_Mig` |
| 50K-1M chars | **Large chunking** | ~10-50 | Procedures complejos |
| 15K-50K chars | **Medium chunking** | ~3-10 | Functions grandes |
| <15K chars | **Single chunk** | 1 | Objetos pequeños |

### Chunking Semántico por Tipo

| Tipo Objeto | Estrategia de División | Preserva |
|-------------|----------------------|----------|
| **PROCEDURE** | Bloques BEGIN/END, secciones lógicas | Variables, parámetros, contexto |
| **FUNCTION** | Bloques lógicos, RETURN statements | Firma, lógica, tipo retorno |
| **VIEW** | Subconsultas, JOINs, CTEs | Relaciones entre tablas |
| **TRIGGER** | Eventos, acciones, condiciones | Eventos disparadores |

## 📊 Metadatos Generados

Cada chunk incluye:

```sql
-- Metadatos básicos
chunk_id, parent_object_id, server, database, schema, object_name, object_type

-- Metadatos del chunk  
chunk_content, chunk_type, chunk_index, total_chunks, chunk_length, chunk_lines

-- Análisis semántico
semantic_type, business_domain, semantic_summary, semantic_tags, complexity_score

-- Referencias y relaciones
references_to, estimated_tokens

-- Embeddings
embedding (768 dimensiones, Gemini embedding-001)
```

## 🔍 Capacidades de Búsqueda

### Búsqueda Semántica Básica
```sql
SELECT * FROM `project.dataset.semantic_search`(
  'autenticacion usuario login password', 
  10
);
```

### Búsqueda por Dominio
```sql
SELECT * FROM `project.dataset.search_by_domain`(
  'factura venta cliente', 
  'ventas', 
  5
);
```

### Búsqueda Híbrida (Vector + Keyword)
```sql
WITH hybrid_results AS (
  SELECT chunk_id, object_name, semantic_summary, distance
  FROM VECTOR_SEARCH(
    TABLE `project.dataset.chunk_embeddings`,
    'embedding',
    ML.GENERATE_TEXT_EMBEDDING('gemini-embedding-001', 'mi consulta'),
    top_k => 20
  )
  WHERE business_domain = 'ventas'
    AND semantic_type = 'stored_procedure'
)
SELECT * FROM hybrid_results
ORDER BY distance ASC
LIMIT 10;
```

## 📈 Optimizaciones Implementadas

### Para Objetos Masivos (9.3M chars)
- ✅ **Chunking por separadores GO** (máx 100 chunks/objeto)
- ✅ **Overlap inteligente** (300 chars para contexto)
- ✅ **Límite de tamaño** (6K chars/chunk óptimo)
- ✅ **Preservación semántica** (bloques lógicos intactos)

### Para Performance
- ✅ **Índices vectoriales IVF** con 1,000 listas
- ✅ **Embeddings en paralelo** con rate limiting
- ✅ **Funciones SQL reutilizables** para queries comunes
- ✅ **Filtrado avanzado** por metadatos

### Para Costos
- ✅ **Sin infraestructura adicional** (solo BigQuery)
- ✅ **Embeddings eficientes** (Gemini embedding-001)
- ✅ **Storage optimizado** (solo chunks relevantes)
- ✅ **Compute on-demand** (sin servidores dedicados)

## 🔧 Configuración

### Variables de Entorno Requeridas
```bash
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
GOOGLE_CLOUD_PROJECT=dfor-prj-dev
GEMINI_API_KEY=your_gemini_api_key
```

### Configuración Personalizable
```python
# app/bigquery_vector/config.py
EMBEDDING_MODEL = "gemini-embedding-001"  # Modelo de embeddings
MAX_CHUNK_SIZE = 6000                     # Tamaño óptimo por chunk
MEGA_OBJECT_THRESHOLD = 1000000          # Umbral para objetos mega
IVF_NUM_LISTS = 1000                     # Optimización índice vectorial
```

## 📊 Métricas Esperadas

### Para tu Dataset (3.4M objetos)
- **Chunks generados**: ~5M (factor 1.5x)
- **Objetos mega chunkeados**: ~10 objetos → ~15K chunks
- **Tiempo de procesamiento**: 30-60 minutos
- **Costo embeddings**: $20-40 USD
- **Storage adicional**: ~2GB
- **Performance búsquedas**: 100-500 queries/sec

### Comparación vs Weaviate
| Métrica | BigQuery Vector | Weaviate |
|---------|----------------|----------|
| **Setup** | ⭐⭐⭐⭐⭐ 30 min | ⭐⭐ 4-8 horas |
| **Costo anual** | ⭐⭐⭐⭐⭐ $1,830 | ⭐⭐ $6,700 |
| **Mantenimiento** | ⭐⭐⭐⭐⭐ Mínimo | ⭐⭐ Alto |
| **Performance** | ⭐⭐⭐⭐⭐ Excelente | ⭐⭐⭐⭐ Muy buena |
| **Latencia** | ⭐⭐⭐⭐ 50-200ms | ⭐⭐⭐⭐⭐ 10-50ms |

## 🎯 Casos de Uso Optimizados

### ✅ Ideales para BigQuery Vector
- 🔍 **RAG para código SQL legacy**
- 📊 **Analytics + Vector Search combinado**
- 💰 **Búsquedas semánticas cost-effective**
- 🔧 **Integración con pipelines existentes**
- 📈 **Escalabilidad automática**

### ⚠️ Considerar Weaviate para
- 🕸️ **Grafos de conocimiento complejos**
- 🎭 **Multi-modal embeddings** (texto + imagen + audio)
- ⚡ **Ultra-baja latencia** (<10ms crítica)
- 🔄 **Replicación multi-región avanzada**

## 🚀 Próximos Pasos

1. **Ejecutar análisis comparativo**:
   ```bash
   make compare-systems
   ```

2. **Crear chunks inteligentes**:
   ```bash
   make create-chunks
   ```

3. **Probar búsquedas**:
   ```bash
   make search-interactive
   ```

4. **Integrar en aplicaciones**:
   - Usar funciones SQL creadas
   - Implementar APIs REST
   - Crear dashboards de analytics

## 🔧 Mantenimiento

### Actualizaciones Regulares
```bash
# Actualizar embeddings (semanal)
make create-chunks

# Analizar calidad (mensual)  
make analyze-quality

# Limpiar datos obsoletos (según necesidad)
make clean-chunks
```

### Monitoreo
- Cobertura de embeddings: >95%
- Calidad de chunks: >80% en rango óptimo
- Performance de índices: <200ms promedio
- Costos: Monitorear uso de ML.GENERATE_TEXT_EMBEDDING

---

**🎉 Sistema BigQuery Vector Search listo para producción con chunking inteligente optimizado para objetos SQL masivos.**
