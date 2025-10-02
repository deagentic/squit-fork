# Guía de Migración de Datos - SQUIT Agentic RAG

## 🎯 Objetivo

Migrar los 3.4M objetos SQL desde BigQuery a Weaviate para habilitar capacidades de búsqueda semántica y análisis inteligente con Gemini.

## 📋 Comandos de Migración Disponibles

### 🧪 Migración de Prueba
```bash
# Migrar 10 objetos para validar pipeline
make migrate-test
```
- **Objetos**: 10 VIEWs y PROCEDUREs
- **Tiempo**: ~2-3 minutos
- **Propósito**: Validar que todo funcione correctamente

### 📊 Migración de Muestra
```bash
# Migrar 1,000 objetos importantes
make agentic-ingest
```
- **Objetos**: 1,000 PROCEDUREs, FUNCTIONs y VIEWs más importantes
- **Tiempo**: ~30-45 minutos
- **Propósito**: Datos suficientes para testing y desarrollo

### 🚀 Migración Completa
```bash
# Migrar TODOS los 3.4M objetos
make migrate-all
```
- **Objetos**: Todos los objetos SQL del codebase
- **Tiempo**: 8-16 horas
- **Costo**: $10-50 USD en API calls de Gemini
- **Propósito**: Sistema completo para producción

### 📈 Monitoreo en Tiempo Real
```bash
# Monitorear progreso durante migración
make monitor-migration
```
- **Actualización**: Cada 30 segundos
- **Métricas**: Objetos migrados, progreso, tiempo estimado
- **Control**: Ctrl+C para salir

## 🔄 Estrategia de Migración por Fases

### Fase 1: Objetos Críticos (50,000 objetos)
- **Tipos**: PROCEDURE, FUNCTION
- **Prioridad**: Lógica de negocio core
- **Tiempo**: ~2-4 horas

### Fase 2: Vistas Importantes (30,000 objetos)
- **Tipos**: VIEW
- **Prioridad**: Consultas y reportes
- **Tiempo**: ~1-2 horas

### Fase 3: Triggers e Índices (20,000 objetos)
- **Tipos**: TRIGGER, INDEX
- **Prioridad**: Integridad y performance
- **Tiempo**: ~1-2 horas

### Fase 4: Objetos Restantes (resto)
- **Tipos**: TABLE, otros
- **Prioridad**: Completitud
- **Tiempo**: ~4-8 horas

## 📊 Proceso de Migración Detallado

### 1. Extracción desde BigQuery
```sql
-- Query optimizada para objetos relevantes
SELECT server, database, schema, object_name, object_type, sql_code, 
       content_hash, last_modified,
       CONCAT(server, '|', database, '|', schema, '|', object_name) as bigquery_id
FROM `dfor-prj-dev.deacero_sql_objects.sql_objects_code`
WHERE sql_code IS NOT NULL 
AND LENGTH(sql_code) >= 50
AND LENGTH(sql_code) <= 50000
AND object_type IN ('PROCEDURE', 'FUNCTION', 'VIEW', 'TRIGGER')
ORDER BY 
    CASE object_type 
        WHEN 'PROCEDURE' THEN 1
        WHEN 'FUNCTION' THEN 2  
        WHEN 'TRIGGER' THEN 3
        WHEN 'VIEW' THEN 4
        ELSE 5
    END,
    last_modified DESC,
    LENGTH(sql_code) DESC
```

### 2. Análisis con Gemini
```python
# Para cada objeto SQL:
# 1. Análisis básico (complejidad, tags, contexto)
# 2. Análisis con IA (solo objetos >200 caracteres)
# 3. Generación de embedding (768D con gemini-embedding-001)
# 4. Enrichment de metadata
```

### 3. Inserción en Weaviate
```python
# Datos insertados en CodeObjects collection:
{
    "server": "SRVDBDES05\\BASCULA",
    "database": "TiSeguridad", 
    "object_name": "sp_AuthenticateUser",
    "object_type": "PROCEDURE",
    "sql_code": "CREATE PROCEDURE...",
    "code_summary": "Resumen generado por Gemini",
    "business_context": "Autenticación y seguridad",
    "complexity_score": 75.5,
    "tags": ["authentication", "security", "procedure"],
    "bigquery_id": "server|db|schema|object",
    # + vector embedding (768 dimensiones)
}
```

## 📈 Métricas de Calidad Esperadas

### Tasa de Éxito por Tipo
- **PROCEDURE**: 95-98% (objetos bien formados)
- **FUNCTION**: 95-98% (similares a procedures)
- **VIEW**: 90-95% (algunas queries complejas pueden fallar)
- **TRIGGER**: 85-90% (código más complejo)
- **INDEX**: 80-85% (metadata limitada)

### Análisis con IA
- **Objetos analizados**: ~60% (solo objetos >200 caracteres)
- **Embeddings generados**: 100% (todos los objetos)
- **Tags automáticos**: 100% (basados en patrones)

## 🚨 Manejo de Errores

### Errores Comunes y Soluciones

#### 1. Rate Limit de Gemini
```
Error: 429 Too Many Requests
Solución: El pipeline tiene retry automático con backoff
```

#### 2. Objeto SQL Malformado
```
Error: JSON parsing failed
Solución: Se usa análisis de fallback sin IA
```

#### 3. Embedding Generation Failed
```
Error: Embedding API error
Solución: Se inserta vector cero, se puede reprocesar después
```

#### 4. Weaviate Connection Lost
```
Error: Connection timeout
Solución: Retry automático con reconexión
```

## 🔧 Configuración Optimizada

### Variables de Entorno Críticas
```bash
GEMINI_API_KEY=your-key              # Requerido para embeddings y análisis
GOOGLE_APPLICATION_CREDENTIALS=...    # Requerido para BigQuery
WEAVIATE_URL=http://weaviate:8080    # URL interna de Docker
```

### Parámetros de Performance
```python
# En IngestionConfig
CHUNK_SIZE = 100              # Objetos por batch
PARALLEL_WORKERS = 2          # Limitado por rate limits Gemini
MIN_CODE_LENGTH = 50          # Filtrar objetos muy pequeños
MAX_CODE_LENGTH = 50000       # Filtrar objetos enormes
```

## 📊 Monitoreo Durante Migración

### Métricas Clave
- **Objetos procesados**: Total acumulado
- **Tasa de éxito**: % de objetos migrados exitosamente
- **Embeddings generados**: Vectores creados
- **Análisis IA completados**: Objetos analizados con Gemini
- **Velocidad**: Objetos por minuto

### Comandos de Monitoreo
```bash
# Monitor en tiempo real
make monitor-migration

# Estado actual de collections
make agentic-health

# Logs detallados
make agentic-logs
```

## 🎯 Recomendaciones de Uso

### Para Desarrollo (Phase 2)
```bash
# Migración de muestra es suficiente
make agentic-ingest  # 1,000 objetos
```

### Para Testing Completo
```bash
# Migración de objetos críticos
# Modificar límite a 50,000 en migrate-all script
```

### Para Producción
```bash
# Migración completa
make migrate-all  # Todos los 3.4M objetos
```

## ⚠️ Consideraciones Importantes

### Costos
- **Embeddings**: ~$0.10 por 1M tokens
- **LLM Analysis**: ~$0.30 por 1M tokens
- **Total estimado**: $10-50 USD para migración completa

### Tiempo
- **Desarrollo**: 30-60 minutos (1,000 objetos)
- **Testing**: 2-4 horas (50,000 objetos)
- **Producción**: 8-16 horas (3.4M objetos)

### Recursos
- **RAM**: 2GB para Weaviate
- **Storage**: ~5GB para datos vectoriales
- **Network**: Estable para APIs externas

## 🚀 Comandos de Ejecución

### Secuencia Recomendada
```bash
# 1. Validar sistema
make validate-phase1

# 2. Probar con 10 objetos
make migrate-test

# 3. Si exitoso, migración de muestra
make agentic-ingest

# 4. Si todo funciona, migración completa
make migrate-all

# 5. Monitorear progreso (en terminal separado)
make monitor-migration
```

### Post-Migración
```bash
# Verificar resultados
make agentic-health

# Explorar datos
make agentic-dev

# Probar consultas agentic
make agentic-demo-full
```

---

## 🎉 Resultado Esperado

Después de la migración completa tendrás:

- ✅ **3.4M objetos SQL** vectorizados en Weaviate
- ✅ **Búsqueda semántica** funcionando en todo el codebase
- ✅ **Análisis automático** de contexto y complejidad
- ✅ **Sistema Agentic RAG** completamente operativo
- ✅ **Consultas inteligentes** sobre código legacy

**¡El sistema estará listo para Phase 2 y uso en producción!**
