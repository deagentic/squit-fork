# Estándar de Modelos de IA para SQUIT

## 📋 Modelos Oficiales

### REGLA ESTRICTA: SIEMPRE usar estos modelos

| Propósito | Modelo | Versión | Por qué |
|-----------|--------|---------|---------|
| **Chat / Agentes** | `gemini-2.5-flash` | Última | Más rápido, mejor reasoning |
| **Embeddings** | `gemini-embedding-001` | Estable | 768 dims optimizado |

## ❌ NO USAR

- ~~`gemini-2.0-flash-exp`~~ → Experimental, puede cambiar
- ~~`gemini-1.5-pro`~~ → Más lento y costoso
- ~~`text-embedding-004`~~ → No optimizado para código
- Embeddings con dims diferentes a 768

## ✅ Configuración Correcta

### En .env

```bash
# Modelo de chat (agentes)
GEMINI_CHAT_MODEL=gemini-2.5-flash

# Modelo de embeddings (búsqueda vectorial)  
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
```

### En Código Python

```python
# Para agentes ADK
from google_adk import LlmAgent

agent = LlmAgent(
    model="gemini/gemini-2.5-flash",  # SIEMPRE
    system_instruction="...",
    tools=[...]
)

# Para embeddings en BigQuery
MODEL `project.dataset.gemini_embedding_model`
REMOTE WITH CONNECTION `project.region.vertex_ai_connection`
OPTIONS(ENDPOINT = 'gemini-embedding-001')  # SIEMPRE
```

### En BigQuery SQL

```sql
-- Generar embeddings
FROM ML.GENERATE_EMBEDDING(
  MODEL `dfor-prj-dev.deacero_sql_objects.gemini_embedding_model`,
  (SELECT content),
  STRUCT(
    TRUE AS flatten_json_output,
    'CODE_RETRIEVAL_QUERY' AS task_type,  -- SIEMPRE para código
    768 AS output_dimensionality  -- SIEMPRE 768
  )
)
```

## 🔧 Parámetros de Generación

### Para Agentes (gemini-2.5-flash)

```python
model_kwargs={
    "temperature": 0.1,      # Baja para determinismo
    "top_p": 0.95,           # Estándar
    "max_output_tokens": 8000  # Suficiente para respuestas largas
}
```

### Para Embeddings (gemini-embedding-001)

```sql
STRUCT(
  TRUE AS flatten_json_output,  # SIEMPRE TRUE
  'CODE_RETRIEVAL_QUERY' AS task_type,  # SIEMPRE para código SQL
  768 AS output_dimensionality  # SIEMPRE 768
)
```

## 📊 Beneficios de este Estándar

| Aspecto | Beneficio |
|---------|-----------|
| **Velocidad** | gemini-2.5-flash es el más rápido |
| **Costo** | Flash es más económico que Pro |
| **Calidad** | 2.5 > 2.0 en reasoning |
| **Estabilidad** | Versión estable vs experimental |
| **Storage** | 768 dims = 75% menos que 2048 |
| **Consistencia** | Mismo modelo en todo el sistema |

## ⚠️ Migraciones

Si encuentras código con modelos antiguos:

```python
# ❌ ANTIGUO
model="gemini/gemini-2.0-flash-exp"
model="gemini/gemini-1.5-pro"

# ✅ NUEVO
model="gemini/gemini-2.5-flash"
```

## 🔍 Verificación

```bash
# Buscar usos de modelos antiguos
grep -r "gemini-2.0" app/ scripts/
grep -r "gemini-1.5" app/ scripts/

# Deben retornar vacío o solo en comentarios históricos
```

---

**Estándar establecido**: 2025-09-30  
**Próxima revisión**: Cuando Google libere gemini-3.x  
**Contacto**: ktouma@deacero.com
