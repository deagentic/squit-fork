# 🔬 Investigación: Soluciones de Memoria para Agentes IA

## 📋 Resumen Ejecutivo

Esta investigación analiza soluciones establecidas para memoria en agentes conversacionales, comparándolas con la implementación actual basada en prompt engineering.

**Hallazgo clave**: Existen **librerías especializadas** que ofrecen memoria estructurada, persistente y optimizada, superiores a depender solo de prompts.

---

## 🎯 Problema Identificado

### Implementación Actual
```python
# app/agentic_adk/agents/master_agent.py
self.session_service = InMemorySessionService()  # Google ADK
system_prompt = """
MEMORIA CONVERSACIONAL (CRÍTICO):
Siempre revisa el historial antes de responder...
"""  # ❌ Prompt engineering para contexto
```

**Limitaciones detectadas:**
1. ✅ Memoria técnica funciona (InMemorySessionService)
2. ❌ Interpretación contextual depende de prompts
3. ❌ Sin estructura de memoria (semántica vs episódica)
4. ❌ Sin persistencia entre sesiones
5. ❌ Sin optimización de tokens (context caching)

---

## 🏗️ Arquitecturas de Memoria para Agentes

### 1. **Tipos de Memoria** (Literatura de IA)

| Tipo | Función | Duración | Implementación |
|------|---------|----------|----------------|
| **Working Memory** | Contexto inmediato (turno actual) | Volátil | En prompt |
| **Episodic Memory** | Conversaciones pasadas | Sesión | Session service |
| **Semantic Memory** | Conocimiento general | Persistente | Vector DB |
| **Procedural Memory** | Cómo hacer tareas | Persistente | Tools/Functions |

### 2. **Modelo de Memoria Cognitiva**

```
Usuario: "hablame de kayak"
├── Working Memory: Query actual + instrucciones sistema
├── Episodic Memory: Historial de esta conversación
├── Semantic Memory: Conocimiento sobre "kayak" en codebase
└── Procedural Memory: Cómo buscar en BigQuery
```

---

## 📚 Soluciones de la Industria

### 🥇 Opción 1: **Vertex AI Memory Bank** (Google Cloud)

**Descripción**: Servicio gestionado de Google para memoria de agentes conversacionales.

**Características:**
- ✅ Memoria multimodal (texto, contexto, entidades)
- ✅ Integración nativa con Google ADK
- ✅ Persistencia automática
- ✅ Búsqueda semántica incorporada
- ✅ Gestión de entidades y preferencias

**Implementación:**
```python
from google.cloud.aiplatform import Agent
from google.cloud.aiplatform.agent_engine import MemoryBank

# Crear Memory Bank
memory_bank = MemoryBank(
    display_name="squit_memory",
    project=PROJECT_ID,
    location="us-central1"
)

# Configurar agente con memoria
agent = Agent(
    display_name="squit_agent",
    memory_bank=memory_bank,
    # ... resto de config
)

# Automáticamente mantiene contexto entre conversaciones
response = agent.query(
    content="todos los procedures",  # ✅ Recuerda contexto de "kayak"
    session_id="user_session_123"
)
```

**Ventajas:**
- ✅ Solución oficial de Google
- ✅ Integración directa con ADK
- ✅ Escalable y gestionada
- ✅ Optimizada para Gemini

**Desventajas:**
- ⚠️ Requiere Vertex AI (costos adicionales)
- ⚠️ Menos control que self-hosted
- ⚠️ Curva de aprendizaje de Vertex AI

**Documentación**: [cloud.google.com/vertex-ai/docs/agent-engine/memory-bank](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-engine/memory-bank/overview)

---

### 🥈 Opción 2: **LangChain Memory Modules**

**Descripción**: Framework modular para construir aplicaciones con LLMs, incluye módulos de memoria especializados.

**Ya está en nuestro `requirements.txt`**: ✅

**Módulos de Memoria:**

#### A. `ConversationBufferMemory`
```python
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory(
    return_messages=True,
    memory_key="chat_history"
)

# Guarda TODO el historial
memory.save_context(
    {"input": "hablame de kayak"},
    {"output": "Kayak es un sistema..."}
)

memory.save_context(
    {"input": "todos los procedures"},
    {"output": "Procedures de kayak: ..."}  # ✅ Ya tiene contexto
)

# Recuperar historial completo
history = memory.load_memory_variables({})
```

**Ventajas:**
- ✅ Simple de usar
- ✅ Memoria completa

**Desventajas:**
- ❌ Crece indefinidamente (tokens)
- ❌ Sin estructura semántica

#### B. `ConversationSummaryMemory`
```python
from langchain.memory import ConversationSummaryMemory
from langchain.llms import OpenAI  # O Gemini via LangChain

llm = OpenAI()  # Para resumir
memory = ConversationSummaryMemory(
    llm=llm,
    return_messages=True
)

# Automáticamente resume conversaciones largas
# ✅ Optimiza tokens
# ✅ Mantiene contexto esencial
```

**Ventajas:**
- ✅ Optimiza tokens (resume)
- ✅ Escalable a conversaciones largas

**Desventajas:**
- ⚠️ Pérdida de detalles al resumir
- ⚠️ Requiere LLM extra para resumir

#### C. `ConversationBufferWindowMemory`
```python
from langchain.memory import ConversationBufferWindowMemory

memory = ConversationBufferWindowMemory(
    k=5,  # Solo últimos 5 turnos
    return_messages=True
)

# ✅ Ventana deslizante
# ✅ Tokens constantes
```

#### D. `VectorStoreRetrieverMemory` (⭐ Recomendado)
```python
from langchain.memory import VectorStoreRetrieverMemory
from langchain.embeddings import OpenAIEmbeddings  # O Gemini
from langchain.vectorstores import Weaviate  # Ya lo tenemos!

# Usar nuestro Weaviate existente
embeddings = GeminiEmbeddings()  # Gemini embeddings
vectorstore = Weaviate(...)

memory = VectorStoreRetrieverMemory(
    retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
    return_docs=True
)

# Memoria semántica: recupera turnos RELEVANTES (no todos)
memory.save_context(
    {"input": "hablame de kayak"},
    {"output": "Kayak es..."}
)

# Turno 10 más tarde:
relevant_history = memory.load_memory_variables(
    {"input": "el primer procedure que mencionaste sobre fechas"}
)
# ✅ Recupera turno sobre kayak aunque hayan pasado 10 turnos
```

**Ventajas:**
- ✅ Búsqueda semántica de memoria
- ✅ Recupera contexto relevante (no todo)
- ✅ Escalable indefinidamente
- ✅ Usa Weaviate que ya tenemos

**Desventajas:**
- ⚠️ Requiere embeddings (Gemini API calls)
- ⚠️ Más complejo que buffer simple

---

### 🥉 Opción 3: **Cognee + Weaviate** (Open Source)

**Descripción**: Sistema de memoria estructurada open-source específico para agentes.

**Arquitectura:**
```python
from cognee import Cognee, Memory

# Configurar memoria persistente
cognee = Cognee(
    vector_store="weaviate",  # Ya lo tenemos
    embedding_model="gemini"   # Nuestro modelo
)

# Crear memoria estructurada
memory = Memory(
    type="conversational",
    persistence="weaviate"
)

# Agregar contexto
await memory.add({
    "type": "conversation_turn",
    "user_input": "hablame de kayak",
    "assistant_response": "Kayak es...",
    "entities": ["kayak", "procedures"],
    "timestamp": datetime.now()
})

# Búsqueda semántica de memoria
relevant_context = await memory.search(
    query="procedures que mencionaste",
    limit=3
)
```

**Ventajas:**
- ✅ Open source y self-hosted
- ✅ Memoria estructurada con entidades
- ✅ Integración con Weaviate (ya lo tenemos)
- ✅ Sin vendor lock-in

**Desventajas:**
- ⚠️ Menos maduro que LangChain
- ⚠️ Documentación limitada
- ⚠️ Comunidad más pequeña

---

### 🛠️ Opción 4: **MemGPT** (Memoria Jerárquica)

**Descripción**: Sistema de memoria inspirado en OS virtuales, con paginación de contexto.

**Concepto:**
```
Main Memory (prompt):     Contexto inmediato (4K tokens)
↕
Archive Memory (vector):  Toda la conversación (ilimitado)
```

**Características:**
- ✅ Paginación automática de contexto
- ✅ Memoria recursiva (chunks de chunks)
- ✅ Optimización extrema de tokens

**Implementación:**
```python
from memgpt import Agent as MemGPTAgent

agent = MemGPTAgent(
    name="squit_agent",
    model="gemini-2.5-flash",
    # Automáticamente gestiona memoria
)

# MemGPT decide qué mantener en prompt y qué archivar
response = agent.message("todos los procedures")
# ✅ Busca automáticamente en archive si necesita contexto
```

**Ventajas:**
- ✅ Optimización extrema de tokens
- ✅ Conversaciones infinitas
- ✅ Auto-gestión de memoria

**Desventajas:**
- ⚠️ Overhead de sistema (más complejidad)
- ⚠️ Latencia adicional (paginación)
- ⚠️ Menos control explícito

---

## 🔥 Opción 5: **Context Caching de Gemini** (⭐ Quick Win)

**Descripción**: Feature nativa de Gemini para cachear system prompts y contexto largo.

**Beneficio**: Reduce latencia y costos sin cambiar arquitectura.

**Implementación:**
```python
from google import genai
from google.genai import types

# Crear cached content
cached_content = client.caches.create(
    model="gemini-2.5-flash",
    contents=[
        types.Content(
            role="user",
            parts=[types.Part(
                text="""SQUIT System Prompt + Instrucciones contextuales largas..."""
            )]
        )
    ],
    ttl="3600s"  # Cache por 1 hora
)

# Usar cache en cada query
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="hablame de kayak",
    cached_content=cached_content.name
)

# ✅ System prompt se procesa 1 vez
# ✅ Latencia reducida ~50%
# ✅ Costos reducidos (cached tokens son más baratos)
```

**Ventajas:**
- ✅ Fácil de implementar (change mínimo)
- ✅ Reduce latencia significativamente
- ✅ Reduce costos
- ✅ Complementa otras soluciones

**Desventajas:**
- ⚠️ No resuelve interpretación contextual
- ⚠️ Solo optimiza performance

**Documentación**: [ai.google.dev/gemini-api/docs/caching](https://ai.google.dev/gemini-api/docs/caching)

---

## 📊 Comparación de Soluciones

| Solución | Complejidad | Persistencia | Escalabilidad | Costo | Vendor Lock-in |
|----------|-------------|--------------|---------------|-------|----------------|
| **InMemorySessionService (actual)** | Baja | Sesión | Baja | Gratis | Google ADK |
| **Vertex AI Memory Bank** | Media | Persistente | Alta | $$$ | Google Cloud |
| **LangChain ConversationBufferMemory** | Baja | Sesión | Baja | Gratis | Ninguno |
| **LangChain VectorStoreRetrieverMemory** | Media | Persistente | Alta | $ | Ninguno |
| **Cognee + Weaviate** | Alta | Persistente | Alta | $ | Ninguno |
| **MemGPT** | Alta | Persistente | Muy Alta | $ | Ninguno |
| **Gemini Context Caching** | Baja | No aplica | No aplica | $ | Gemini |

### Leyenda de Costos:
- **Gratis**: Sin costo adicional
- **$**: Embeddings + storage (bajo)
- **$$$**: Servicio gestionado (alto)

---

## 🎯 Recomendación Pragmática

### 🚀 **Fase 1: Quick Wins** (1-2 días)

#### A. Implementar Context Caching
```python
# master_agent.py
class MasterAgent:
    def __init__(self, config):
        # Cachear system prompt
        self.cached_prompt = self._create_cached_prompt()
    
    def _create_cached_prompt(self):
        return client.caches.create(
            model=self.config.GEMINI_MODEL,
            contents=[...system_prompt...],
            ttl="3600s"
        )
```

**Beneficio**: ✅ Reduce latencia 50% sin cambios arquitectónicos

#### B. Agregar LangChain ConversationBufferWindowMemory
```python
from langchain.memory import ConversationBufferWindowMemory

class MasterAgent:
    def __init__(self, config):
        self.langchain_memory = ConversationBufferWindowMemory(k=10)
        # Complementa InMemorySessionService con estructura
```

**Beneficio**: ✅ Estructura explícita de memoria sin complejidad

---

### 🏗️ **Fase 2: Arquitectura Robusta** (1 semana)

#### Implementar LangChain VectorStoreRetrieverMemory con Weaviate

```python
from langchain.memory import VectorStoreRetrieverMemory
from langchain.vectorstores import Weaviate
from langchain.embeddings import GoogleGenerativeAIEmbeddings

class MasterAgent:
    def __init__(self, config):
        # Configurar memoria vectorial
        embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=config.GEMINI_API_KEY
        )
        
        # Usar Weaviate existente
        vectorstore = Weaviate(
            client=weaviate_client,  # Ya existe en el proyecto
            index_name="squit_conversation_memory",
            text_key="conversation_text",
            embedding=embeddings
        )
        
        # Memoria semántica
        self.semantic_memory = VectorStoreRetrieverMemory(
            retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
            return_docs=True
        )
    
    def process(self, user_query):
        # Recuperar contexto relevante (no todo)
        relevant_context = self.semantic_memory.load_memory_variables(
            {"input": user_query}
        )
        
        # Combinar con InMemorySessionService
        # ...
        
        # Guardar nuevo turno
        self.semantic_memory.save_context(
            {"input": user_query},
            {"output": response}
        )
```

**Beneficios:**
- ✅ Búsqueda semántica de memoria
- ✅ Escalable indefinidamente
- ✅ Reutiliza Weaviate existente
- ✅ Sin vendor lock-in

---

### 🔮 **Fase 3: Enterprise Grade** (2-3 semanas)

#### Migrar a Vertex AI Memory Bank

**Cuándo hacerlo:**
- Si necesitas persistencia entre reinic ios de aplicación
- Si necesitas multi-tenant con memoria separada
- Si tienes presupuesto para servicios gestionados

```python
from google.cloud.aiplatform import Agent
from google.cloud.aiplatform.agent_engine import MemoryBank

class MasterAgent:
    def __init__(self, config):
        self.memory_bank = MemoryBank(
            display_name="squit_production_memory",
            project=config.PROJECT_ID,
            location="us-central1"
        )
        
        self.agent = Agent(
            display_name="squit_agent",
            memory_bank=self.memory_bank,
            # ... resto
        )
```

---

## 🧪 Plan de Migración

### Semana 1: Investigación y Prototipo
- [ ] Probar Gemini Context Caching (1 día)
- [ ] Probar LangChain BufferWindowMemory (1 día)
- [ ] Diseñar arquitectura con VectorStoreRetrieverMemory (1 día)

### Semana 2: Implementación Fase 1
- [ ] Implementar Context Caching en MasterAgent
- [ ] Agregar LangChain memory como complemento
- [ ] Tests de validación

### Semana 3: Implementación Fase 2
- [ ] Configurar Weaviate para memoria conversacional
- [ ] Implementar VectorStoreRetrieverMemory
- [ ] Migrar casos de uso críticos

### Semana 4: Validación y Optimización
- [ ] Tests exhaustivos con casos reales
- [ ] Comparación de performance vs baseline
- [ ] Ajustes y documentación

---

## 📝 Conclusiones

### ❌ **Problema con Solución Actual**
- Dependencia excesiva de prompt engineering
- Sin estructura explícita de memoria
- No escala a conversaciones largas
- Sin persistencia

### ✅ **Solución Recomendada**
1. **Short-term**: Context Caching + LangChain Buffer (quick wins)
2. **Mid-term**: LangChain VectorStoreRetrieverMemory + Weaviate (arquitectura robusta)
3. **Long-term**: Evaluar Vertex AI Memory Bank si se justifica

### 💡 **Key Insight**
> "No reinventar la rueda. Usar librerías establecidas que ya resolvieron el problema de memoria en agentes."

---

## 📚 Referencias

1. **Vertex AI Memory Bank**: https://cloud.google.com/vertex-ai/docs/agent-engine/memory-bank
2. **LangChain Memory**: https://python.langchain.com/docs/modules/memory/
3. **Gemini Context Caching**: https://ai.google.dev/gemini-api/docs/caching
4. **MemGPT Paper**: https://arxiv.org/abs/2310.08560
5. **Cognee**: https://github.com/cognee/cognee
6. **Crew AI Memory**: https://docs.crewai.com/concepts/memory

---

**Autor**: Investigación solicitada por Karim Touma  
**Fecha**: 2025-10-01  
**Versión**: 1.0.0  
**Status**: 📋 Investigación completa - Pendiente decisión de implementación

