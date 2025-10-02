# Plan: Sistema Agentic RAG con Google ADK
## Democratizando Código Legacy con Agentes IA

---

## 🎯 Objetivo

Implementar un sistema de agentes inteligentes que permita a **cualquier persona** en la organización entender y trabajar con código SQL legacy mediante conversación en lenguaje natural.

## 🏗️ Arquitectura del Sistema

### Componentes

```
Usuario (lenguaje natural)
    ↓
MasterAgent (Orquestador - Gemini 2.0)
    ├─→ CodeSearchAgent (Búsqueda semántica)
    │   └─→ VectorSearchTool (BigQuery VECTOR_SEARCH)
    ├─→ CodeAnalysisAgent (Análisis de código)
    │   └─→ CodeReaderTool (Lee chunks completos)
    ├─→ DependencyAgent (Análisis de dependencias)
    │   └─→ DependencySearchTool (Busca referencias)
    └─→ ExplanationAgent (Genera explicaciones)
        └─→ SummarizerTool (Resume y simplifica)
```

### Stack Tecnológico

- **Framework**: Google Agent Development Kit (ADK) ([adk-docs](https://google.github.io/adk-docs/))
- **LLM**: Gemini 2.5 Flash (SIEMPRE usar esta versión)
- **Vector Search**: BigQuery VECTOR_SEARCH nativo ([vector-search docs](https://cloud.google.com/bigquery/docs/vector-search))
- **Storage**: BigQuery (tabla `chunk_embeddings` con vectores de 768 dims)
- **Tools**: Function tools custom + BigQuery integration

---

## 📋 Casos de Uso Específicos

### 1. **Búsqueda por Intención**
```
Usuario: "¿Dónde está la lógica de autenticación de usuarios?"

Flujo:
1. MasterAgent analiza la intención
2. Delega a CodeSearchAgent
3. CodeSearchAgent usa VectorSearchTool
4. Retorna chunks relevantes
5. ExplanationAgent genera resumen comprensible
```

### 2. **Análisis de Impacto**
```
Usuario: "¿Qué se rompe si modifico la tabla ClientesMaster?"

Flujo:
1. MasterAgent identifica necesidad de análisis de dependencias
2. DependencyAgent busca referencias a ClientesMaster
3. Analiza tipo de uso (lectura/escritura)
4. ExplanationAgent genera reporte de riesgo
```

### 3. **Explicación de Código**
```
Usuario: "¿Qué hace el procedimiento sp_ProcesarVentas?"

Flujo:
1. CodeSearchAgent encuentra el procedimiento
2. CodeAnalysisAgent lee chunks completos
3. Identifica lógica de negocio paso a paso
4. ExplanationAgent genera explicación en lenguaje simple
```

### 4. **Onboarding de Desarrolladores**
```
Usuario: "Explícame el módulo de inventario"

Flujo:
1. MasterAgent identifica tema amplio
2. CodeSearchAgent busca por dominio "inventario"
3. Identifica componentes principales
4. ExplanationAgent genera overview con mapas conceptuales
```

---

## 🤖 Diseño de Agentes (ADK)

### 1. MasterAgent (Orquestador)

**Tipo**: `LlmAgent` con transfer a otros agentes

**Responsabilidades**:
- Entender intención del usuario
- Decidir qué agente(s) usar
- Coordinar flujo entre agentes
- Sintetizar respuesta final

**Tools**:
- Transfer a CodeSearchAgent
- Transfer a CodeAnalysisAgent
- Transfer a DependencyAgent
- Transfer a ExplanationAgent

**Prompt del Sistema**:
```
Eres el asistente inteligente de SQUIT, especializado en democratizar código SQL legacy.

Tu objetivo es ayudar a CUALQUIER persona (desarrolladores nuevos, arquitectos, managers)
a entender código SQL sin necesidad de ser experto.

Capacidades:
- Buscar código por intención (no sintaxis exacta)
- Analizar código y explicar qué hace
- Identificar dependencias y riesgo de cambios
- Generar explicaciones comprensibles

Delega a:
- CodeSearchAgent: para buscar código
- CodeAnalysisAgent: para analizar código específico
- DependencyAgent: para análisis de impacto
- ExplanationAgent: para generar explicaciones finales
```

### 2. CodeSearchAgent (Búsqueda Semántica)

**Tipo**: `LlmAgent` con tool `VectorSearchTool`

**Responsabilidades**:
- Traducir lenguaje natural a búsqueda vectorial
- Ejecutar VECTOR_SEARCH en BigQuery
- Rankear resultados por relevancia
- Aplicar filtros (dominio, tipo, complejidad)

**Tool**: `VectorSearchTool`
```python
def vector_search(
    query: str,
    business_domains: List[str] = None,
    object_types: List[str] = None,
    limit: int = 10
) -> List[Dict]:
    """
    Busca código SQL por intención semántica.
    
    Args:
        query: Descripción en lenguaje natural de lo que busca
        business_domains: Filtrar por: ventas, inventario, finanzas, etc.
        object_types: Filtrar por: PROCEDURE, VIEW, FUNCTION, etc.
        limit: Número máximo de resultados
    
    Returns:
        Lista de chunks relevantes con metadata
    """
```

**Implementación**:
- Usa `ML.GENERATE_EMBEDDING` para query
- Ejecuta `VECTOR_SEARCH` con embeddings
- Aplica filtros WHERE
- Retorna chunks con scores

### 3. CodeAnalysisAgent (Análisis de Código)

**Tipo**: `LlmAgent` con tool `CodeReaderTool`

**Responsabilidades**:
- Leer código completo de objetos
- Identificar lógica de negocio
- Extraer flujos y patrones
- Analizar complejidad

**Tool**: `CodeReaderTool`
```python
def get_object_code(
    object_id: str,
    include_metadata: bool = True
) -> Dict:
    """
    Obtiene código completo de un objeto SQL.
    
    Args:
        object_id: ID del chunk o parent_object_id
        include_metadata: Incluir metadatos (dominio, complejidad, etc.)
    
    Returns:
        Código completo con contexto
    """
```

### 4. DependencyAgent (Análisis de Dependencias)

**Tipo**: `LlmAgent` con tool `DependencySearchTool`

**Responsabilidades**:
- Encontrar dependencias de objetos
- Identificar objetos que dependen de X
- Analizar tipo de dependencia (lee/escribe)
- Calcular impacto de cambios

**Tool**: `DependencySearchTool`
```python
def find_dependencies(
    object_name: str,
    dependency_type: str = "both"  # "uses" | "used_by" | "both"
) -> Dict:
    """
    Encuentra dependencias de un objeto SQL.
    
    Args:
        object_name: Nombre del objeto (tabla, procedimiento, etc.)
        dependency_type: Tipo de dependencias a buscar
    
    Returns:
        Grafo de dependencias con metadatos
    """
```

### 5. ExplanationAgent (Generación de Explicaciones)

**Tipo**: `LlmAgent` especializado en comunicación clara

**Responsabilidades**:
- Traducir técnico → lenguaje simple
- Generar resúmenes ejecutivos
- Crear mapas conceptuales
- Adaptar explicación al nivel del usuario

**Prompt del Sistema**:
```
Eres un experto en explicar código técnico de forma simple y comprensible.

Tu audiencia puede ser:
- Desarrolladores nuevos (necesitan contexto técnico)
- Managers (necesitan impacto de negocio)
- Analistas (necesitan flujos de proceso)

Principios:
1. Usar lenguaje simple sin jerga innecesaria
2. Empezar con resumen de alto nivel
3. Dar detalles técnicos solo si se piden
4. Usar ejemplos concretos
5. Destacar riesgos y consideraciones
```

---

## 🔧 Implementación de Tools

### VectorSearchTool (BigQuery VECTOR_SEARCH)

**Implementación**:
```python
from google_adk import function_tool
from google.cloud import bigquery

@function_tool
def vector_search(
    query: str,
    business_domains: list[str] = None,
    object_types: list[str] = None,
    limit: int = 10
) -> list[dict]:
    """Busca código SQL por intención semántica usando BigQuery VECTOR_SEARCH."""
    
    client = bigquery.Client(project=config.PROJECT_ID)
    
    # Construir query con ML.GENERATE_EMBEDDING + VECTOR_SEARCH
    search_query = f"""
    WITH query_embedding AS (
      SELECT ml_generate_embedding_result as embedding
      FROM ML.GENERATE_EMBEDDING(
        MODEL `{config.PROJECT_ID}.{config.DATASET_ID}.gemini_embedding_model`,
        (SELECT @query AS content),
        STRUCT(TRUE AS flatten_json_output, 'CODE_RETRIEVAL_QUERY' AS task_type, 768 AS output_dimensionality)
      )
    )
    SELECT 
      chunk_id,
      object_name,
      semantic_summary,
      business_domain,
      complexity_score,
      1.0 - distance as relevance_score,
      SUBSTR(chunk_content, 1, 500) as preview
    FROM VECTOR_SEARCH(
      (SELECT * FROM `{config.full_embeddings_table_id}` WHERE 1=1
       {build_filters(business_domains, object_types)}),
      'embedding',
      (SELECT * FROM query_embedding),
      top_k => @limit,
      distance_type => 'COSINE'
    )
    ORDER BY distance ASC
    """
    
    # Ejecutar con parámetros
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("query", "STRING", query),
            bigquery.ScalarQueryParameter("limit", "INT64", limit)
        ]
    )
    
    results = client.query(search_query, job_config=job_config).result()
    return [dict(row) for row in results]
```

### Otras Tools

Similar implementación para:
- `CodeReaderTool`: Query SQL directo a `chunk_embeddings`
- `DependencySearchTool`: VECTOR_SEARCH + filtros por referencias
- `SummarizerTool`: Agregación de chunks con metadatos

---

## 📊 Flujo de Datos

### Búsqueda Semántica
```
1. Usuario: "autenticación usuarios permisos"
2. VectorSearchTool genera embedding del query
3. VECTOR_SEARCH compara con embeddings en BigQuery
4. Retorna top-10 chunks más similares
5. Agent analiza y presenta resultados
```

### Análisis de Código
```
1. Usuario: "¿Qué hace sp_ProcesarVentas?"
2. CodeSearchAgent encuentra chunks del procedimiento
3. CodeReaderTool obtiene código completo
4. CodeAnalysisAgent identifica:
   - Parámetros de entrada
   - Lógica principal
   - Tablas usadas
   - Validaciones
5. ExplanationAgent genera explicación estructurada
```

---

## 🎯 Métricas de Éxito

### Métricas Técnicas
- **Latencia**: < 5 segundos por consulta
- **Precisión**: > 80% de consultas resueltas correctamente
- **Recall**: Encuentra código relevante en top-10 resultados

### Métricas de Democratización
- **Adopción**: Número de usuarios únicos/mes
- **Satisfacción**: Rating de utilidad de respuestas
- **Impacto**: Reducción en tiempo de onboarding
- **Accesibilidad**: Uso por no-expertos SQL

---

## 🚀 Plan de Implementación

### Fase 1: Setup Base (1-2 días)
- [x] Instalar google-adk
- [ ] Configurar credenciales Gemini
- [ ] Crear estructura de proyecto
- [ ] Implementar VectorSearchTool básico
- [ ] Test de conectividad BigQuery

### Fase 2: Agentes Core (2-3 días)
- [ ] Implementar CodeSearchAgent
- [ ] Implementar CodeAnalysisAgent
- [ ] Implementar MasterAgent (orquestador)
- [ ] Tests unitarios de cada agente

### Fase 3: Tools Avanzados (2 días)
- [ ] Implementar DependencySearchTool
- [ ] Implementar CodeReaderTool completo
- [ ] Integrar con sistema de tracking
- [ ] Cache de embeddings frecuentes

### Fase 4: Refinamiento (2 días)
- [ ] Implementar ExplanationAgent
- [ ] Optimizar prompts del sistema
- [ ] Mejorar manejo de errores
- [ ] Logging y observabilidad

### Fase 5: Testing & Demo (1-2 días)
- [ ] Crear script de demo interactivo
- [ ] Tests end-to-end
- [ ] Documentación de uso
- [ ] Video demo

**Total estimado**: 8-11 días

---

## 📁 Estructura de Archivos

```
squit/
├── app/
│   ├── agentic_adk/              # NUEVO sistema con ADK
│   │   ├── __init__.py
│   │   ├── config.py             # Config ADK
│   │   ├── tools/                # Tools para BigQuery
│   │   │   ├── __init__.py
│   │   │   ├── vector_search.py
│   │   │   ├── code_reader.py
│   │   │   └── dependency_search.py
│   │   ├── agents/               # Agentes especializados
│   │   │   ├── __init__.py
│   │   │   ├── master_agent.py
│   │   │   ├── code_search_agent.py
│   │   │   ├── code_analysis_agent.py
│   │   │   ├── dependency_agent.py
│   │   │   └── explanation_agent.py
│   │   └── pipeline.py           # Orquestador principal
│   ├── agentic_rag/              # Sistema anterior (mantener)
│   └── bigquery_vector/          # Sistema base (mantener)
├── scripts/
│   └── demo_agentic_adk.py       # Demo interactivo
└── docs/
    ├── AGENTIC_SYSTEM_PLAN.md    # Este documento
    └── AGENTIC_ADK_GUIDE.md      # Guía de uso
```

---

## 💡 Ejemplos de Prompts

### Búsqueda Simple
```
Usuario: "procedimientos de cálculo de nómina"
Sistema: Encuentra 8 procedimientos relacionados con nómina,
         mostrando nombre, complejidad y resumen de cada uno.
```

### Análisis de Código
```
Usuario: "explícame sp_CalcularComisiones línea por línea"
Sistema: 
1. Resumen: Calcula comisiones de vendedores basado en ventas
2. Parámetros: @Mes, @Año, @Vendedor (opcional)
3. Lógica principal:
   a. Obtiene ventas del mes
   b. Aplica reglas de comisión por rango
   c. Considera bonos especiales
   d. Genera registro en tablas de comisiones
4. Tablas usadas: Ventas, Vendedores, ReglasComision
5. Complejidad: Media (score: 6.5/10)
```

### Análisis de Impacto
```
Usuario: "quiero agregar una columna a la tabla Productos, ¿qué impacta?"
Sistema:
⚠️ IMPACTO ALTO - 45 objetos afectados:
- 12 procedimientos LEEN de Productos
- 3 procedimientos ESCRIBEN a Productos  
- 8 vistas usan Productos
- 22 reportes dependen de estas vistas

🔴 Críticos (revisar antes):
- sp_ActualizarInventario (producción diaria)
- vw_ReporteVentasConsolidado (dashboard ejecutivo)

🟡 Medianos:
- sp_ImportarProductosCSV (semanal)
- ...
```

---

## 🔐 Consideraciones de Seguridad

1. **Acceso a Datos**: Tools solo leen, nunca modifican
2. **Rate Limiting**: Limitar consultas por usuario/hora
3. **Validación**: Sanitizar inputs antes de queries
4. **Logging**: Auditar todas las consultas
5. **Privacidad**: No exponer datos sensibles en logs

---

## 📊 Monitoreo y Observabilidad

### Métricas a Trackear
- Latencia por tipo de consulta
- Tools más usados
- Agentes más invocados
- Errores y causas
- Satisfacción del usuario (thumbs up/down)

### Integración
- Cloud Trace para latencias ([ADK tracing](https://google.github.io/adk-docs/observability/cloud-trace/))
- Logging estructurado
- Dashboard de métricas

---

## 🎓 Próximos Pasos (Post-MVP)

1. **Multi-turn Conversations**: Mantener contexto entre preguntas
2. **Code Generation**: Generar queries SQL desde lenguaje natural
3. **Refactoring Suggestions**: Sugerir mejoras de código
4. **Interactive Learning**: Aprender de feedback de usuarios
5. **Multi-modal**: Generar diagramas visuales de dependencias

---

**Documento de Plan v1.0**  
*Preparado para implementación con Google ADK*  
*Fecha: 2025-09-30*
