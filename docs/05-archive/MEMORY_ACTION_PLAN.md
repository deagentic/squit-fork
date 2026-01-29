# 🎯 Plan de Acción: Mejora de Memoria en SQUIT

## 📊 Decisión Basada en Investigación

Después de investigar soluciones de la industria (ver `MEMORY_RESEARCH.md`), el plan es implementar **memoria estructurada** usando librerías establecidas, no solo prompts.

---

## 🚀 Fase 1: Quick Wins (Hoy - 2 días)

### Objetivo
Mejorar performance y estructura sin cambios arquitectónicos grandes.

### Acción 1.1: Gemini Context Caching ⚡
**Tiempo estimado**: 4 horas  
**Beneficio**: Reduce latencia 50% + optimiza costos

```python
# app/agentic_adk/agents/master_agent.py

class MasterAgent:
    def __init__(self, config):
        # ... código existente ...
        
        # NUEVO: Crear cached content para system prompt
        self.cached_system_prompt = self._create_cached_prompt()
    
    def _create_cached_prompt(self):
        """
        Cachea el system prompt largo para reducir latencia.
        
        Returns:
            CachedContent de Gemini
        """
        from google.genai import types
        
        system_prompt_long = """
        Eres asistente de SQUIT para código SQL legacy...
        [Todo el system prompt actual]
        """
        
        try:
            cached = self.gemini_client.caches.create(
                model=self.config.GEMINI_MODEL,
                contents=[
                    types.Content(
                        role="user",
                        parts=[types.Part(text=system_prompt_long)]
                    )
                ],
                ttl="3600s",  # 1 hora
                display_name="squit_system_prompt"
            )
            logger.info(f"✅ System prompt cacheado: {cached.name}")
            return cached
        except Exception as e:
            logger.warning(f"⚠️ Context caching no disponible: {e}")
            return None
    
    def process(self, user_query, show_progress=False):
        # ... código existente ...
        
        # MODIFICAR: Usar cached content si está disponible
        if self.cached_system_prompt:
            # Usar cache
            message = types.Content(
                role="user",
                parts=[types.Part(text=user_query)],
                cached_content=self.cached_system_prompt.name
            )
        else:
            # Fallback sin cache
            message = types.Content(...)
```

**Checklist:**
- [ ] Implementar `_create_cached_prompt()`
- [ ] Modificar `process()` para usar cache
- [ ] Agregar fallback si caching falla
- [ ] Test de performance (medir latencia antes/después)
- [ ] Documentar en código

---

### Acción 1.2: LangChain Memory Buffer Window
**Tiempo estimado**: 4 horas  
**Beneficio**: Estructura explícita de memoria

```python
# app/agentic_adk/agents/master_agent.py

from langchain.memory import ConversationBufferWindowMemory

class MasterAgent:
    def __init__(self, config):
        # ... código existente ...
        
        # NUEVO: Agregar memoria estructurada de LangChain
        self.langchain_memory = ConversationBufferWindowMemory(
            k=10,  # Últimos 10 turnos
            return_messages=True,
            memory_key="chat_history",
            input_key="input",
            output_key="output"
        )
        logger.info("✅ LangChain memory buffer inicializado")
    
    def process(self, user_query, show_progress=False):
        # ... código existente de búsqueda y procesamiento ...
        
        # ANTES de llamar al agente: cargar memoria LangChain
        memory_vars = self.langchain_memory.load_memory_variables({})
        chat_history = memory_vars.get("chat_history", [])
        
        # Opcional: Agregar resumen de historial al prompt
        if chat_history:
            history_summary = self._summarize_history(chat_history[-5:])  # Últimos 5
            # Agregar al contexto del agente
        
        # Ejecutar agente (código existente)
        response = ...
        
        # DESPUÉS: Guardar en memoria LangChain
        self.langchain_memory.save_context(
            {"input": user_query},
            {"output": response}
        )
        
        return response
    
    def _summarize_history(self, messages):
        """Resume historial reciente para contexto."""
        summary = "Conversación reciente:\n"
        for msg in messages:
            role = "Usuario" if msg.type == "human" else "Asistente"
            content = msg.content[:100]  # Primeros 100 chars
            summary += f"{role}: {content}...\n"
        return summary
    
    def reset_conversation(self):
        # ... código existente ...
        
        # NUEVO: Limpiar también LangChain memory
        self.langchain_memory.clear()
```

**Checklist:**
- [ ] Agregar `langchain` a imports
- [ ] Inicializar `ConversationBufferWindowMemory`
- [ ] Modificar `process()` para cargar/guardar
- [ ] Implementar `_summarize_history()`
- [ ] Actualizar `reset_conversation()`
- [ ] Test con caso real (kayak)

---

## 🏗️ Fase 2: Arquitectura Robusta (Semana 2-3)

### Objetivo
Memoria semántica persistente con Weaviate.

### Acción 2.1: Configurar Weaviate para Memoria Conversacional
**Tiempo estimado**: 1 día

```python
# app/agentic_adk/weaviate_memory.py (NUEVO ARCHIVO)

import weaviate
from typing import List, Dict, Any
from datetime import datetime
import google.genai as genai

class WeaviateConversationMemory:
    """
    Memoria conversacional persistente usando Weaviate.
    """
    
    SCHEMA = {
        "class": "ConversationTurn",
        "description": "Turno de conversación en SQUIT",
        "vectorizer": "none",  # Usamos Gemini embeddings
        "properties": [
            {
                "name": "session_id",
                "dataType": ["string"],
                "description": "ID de sesión"
            },
            {
                "name": "user_id",
                "dataType": ["string"],
                "description": "ID de usuario"
            },
            {
                "name": "turn_number",
                "dataType": ["int"],
                "description": "Número de turno en la conversación"
            },
            {
                "name": "user_input",
                "dataType": ["text"],
                "description": "Query del usuario"
            },
            {
                "name": "assistant_response",
                "dataType": ["text"],
                "description": "Respuesta del asistente"
            },
            {
                "name": "extracted_entities",
                "dataType": ["string[]"],
                "description": "Entidades mencionadas (kayak, procedures, etc)"
            },
            {
                "name": "timestamp",
                "dataType": ["date"],
                "description": "Timestamp del turno"
            }
        ]
    }
    
    def __init__(self, weaviate_url: str, gemini_api_key: str):
        """Inicializa cliente Weaviate y Gemini."""
        self.client = weaviate.Client(url=weaviate_url)
        self.gemini_client = genai.Client(api_key=gemini_api_key)
        self._ensure_schema()
    
    def _ensure_schema(self):
        """Crea schema si no existe."""
        try:
            self.client.schema.get("ConversationTurn")
        except:
            self.client.schema.create_class(self.SCHEMA)
    
    def add_turn(
        self,
        session_id: str,
        user_id: str,
        turn_number: int,
        user_input: str,
        assistant_response: str,
        entities: List[str] = None
    ):
        """Guarda turno en Weaviate con embedding."""
        # Generar embedding del turno completo
        combined_text = f"User: {user_input}\nAssistant: {assistant_response}"
        
        embedding = self.gemini_client.models.embed_content(
            model="models/embedding-001",
            content=combined_text,
            task_type="retrieval_document"
        )
        
        # Guardar en Weaviate
        self.client.data_object.create(
            class_name="ConversationTurn",
            data_object={
                "session_id": session_id,
                "user_id": user_id,
                "turn_number": turn_number,
                "user_input": user_input,
                "assistant_response": assistant_response,
                "extracted_entities": entities or [],
                "timestamp": datetime.now().isoformat()
            },
            vector=embedding["embedding"]
        )
    
    def search_relevant_turns(
        self,
        query: str,
        session_id: str = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Busca turnos relevantes por similitud semántica."""
        # Generar embedding de la query
        embedding = self.gemini_client.models.embed_content(
            model="models/embedding-001",
            content=query,
            task_type="retrieval_query"
        )
        
        # Búsqueda vectorial en Weaviate
        near_vector = {"vector": embedding["embedding"]}
        
        where_filter = None
        if session_id:
            where_filter = {
                "path": ["session_id"],
                "operator": "Equal",
                "valueString": session_id
            }
        
        results = (
            self.client.query
            .get("ConversationTurn", [
                "session_id", "turn_number", "user_input",
                "assistant_response", "extracted_entities", "timestamp"
            ])
            .with_near_vector(near_vector)
            .with_where(where_filter) if where_filter else None
            .with_limit(limit)
            .do()
        )
        
        return results["data"]["Get"]["ConversationTurn"]
```

**Checklist:**
- [ ] Crear `weaviate_memory.py`
- [ ] Implementar schema de ConversationTurn
- [ ] Implementar `add_turn()` con embeddings
- [ ] Implementar `search_relevant_turns()`
- [ ] Tests unitarios

---

### Acción 2.2: Integrar con MasterAgent
**Tiempo estimado**: 1 día

```python
# app/agentic_adk/agents/master_agent.py

from agentic_adk.weaviate_memory import WeaviateConversationMemory

class MasterAgent:
    def __init__(self, config):
        # ... código existente ...
        
        # NUEVO: Memoria persistente en Weaviate
        self.persistent_memory = WeaviateConversationMemory(
            weaviate_url=config.WEAVIATE_URL,
            gemini_api_key=config.GEMINI_API_KEY
        )
        self.turn_counter = 0
    
    def process(self, user_query, show_progress=False):
        self.turn_counter += 1
        
        # NUEVO: Buscar contexto relevante en memoria persistente
        relevant_turns = self.persistent_memory.search_relevant_turns(
            query=user_query,
            session_id=self.session_id,
            limit=3  # Top 3 turnos relevantes
        )
        
        # Agregar al contexto del agente
        if relevant_turns:
            context_summary = self._format_relevant_memory(relevant_turns)
            # Incluir en prompt o como parte del mensaje
        
        # Ejecutar agente (código existente)
        response = ...
        
        # NUEVO: Guardar turno en memoria persistente
        self.persistent_memory.add_turn(
            session_id=self.session_id,
            user_id=self.user_id,
            turn_number=self.turn_counter,
            user_input=user_query,
            assistant_response=response,
            entities=self._extract_entities(user_query, response)
        )
        
        return response
    
    def _format_relevant_memory(self, turns):
        """Formatea turnos relevantes para contexto."""
        memory_context = "Contexto relevante de conversación anterior:\n"
        for turn in turns:
            memory_context += f"Turn {turn['turn_number']}: {turn['user_input'][:50]}...\n"
        return memory_context
    
    def _extract_entities(self, user_input, response):
        """Extrae entidades mencionadas (simplificado)."""
        # Implementación simple: palabras clave frecuentes
        text = f"{user_input} {response}".lower()
        entities = []
        
        # Keywords de dominio
        keywords = ["kayak", "inventario", "ventas", "procedure", "tabla"]
        for kw in keywords:
            if kw in text:
                entities.append(kw)
        
        return entities
```

**Checklist:**
- [ ] Agregar `persistent_memory` en `__init__()`
- [ ] Modificar `process()` para buscar memoria relevante
- [ ] Implementar `_format_relevant_memory()`
- [ ] Implementar `_extract_entities()`
- [ ] Guardar turnos después de respuesta
- [ ] Test end-to-end

---

### Acción 2.3: Sistema de Entidades
**Tiempo estimado**: 1 día

```python
# app/agentic_adk/entity_tracker.py (NUEVO)

class EntityTracker:
    """
    Rastrea entidades mencionadas en la conversación.
    Ayuda al agente a entender "el primero", "ese procedure", etc.
    """
    
    def __init__(self):
        self.entities = {
            "procedures": [],
            "tables": [],
            "databases": [],
            "topics": []  # kayak, inventario, etc
        }
        self.current_topic = None
    
    def add_procedures(self, procedures: List[str]):
        """Registra procedures mencionados."""
        self.entities["procedures"].extend(procedures)
    
    def get_first_procedure(self):
        """Obtiene el primer procedure mencionado."""
        return self.entities["procedures"][0] if self.entities["procedures"] else None
    
    def get_procedure_by_index(self, index: int):
        """Obtiene procedure por índice (1-based)."""
        idx = index - 1
        if 0 <= idx < len(self.entities["procedures"]):
            return self.entities["procedures"][idx]
        return None
    
    def set_current_topic(self, topic: str):
        """Establece tema actual de conversación."""
        self.current_topic = topic
        self.entities["topics"].append(topic)
    
    def clear(self):
        """Limpia entidades."""
        self.entities = {k: [] for k in self.entities}
        self.current_topic = None
```

**Integración en MasterAgent:**
```python
class MasterAgent:
    def __init__(self, config):
        # ... código existente ...
        self.entity_tracker = EntityTracker()
    
    def process(self, user_query, show_progress=False):
        # ... código existente ...
        
        # NUEVO: Detectar tema/entidades en respuesta
        if "kayak" in response.lower():
            self.entity_tracker.set_current_topic("kayak")
        
        # Extraer procedures de respuesta
        procedures = self._extract_procedures_from_response(response)
        if procedures:
            self.entity_tracker.add_procedures(procedures)
        
        return response
    
    def _extract_procedures_from_response(self, response):
        """Extrae nombres de procedures de la respuesta."""
        import re
        # Pattern: CamelCaseProc o sp_underscore_proc
        pattern = r'\b([A-Z][a-z]+(?:[A-Z][a-z]+)*Proc|sp_\w+)\b'
        matches = re.findall(pattern, response)
        return list(set(matches))
```

---

## 📊 Fase 3: Evaluación y Ajustes (Semana 4)

### Tests de Performance
```python
# scripts/benchmark_memory.py (NUEVO)

import time
from agentic_adk import MasterAgent

def benchmark_memory():
    """Compara performance antes/después de mejoras."""
    agent = MasterAgent()
    
    queries = [
        "hablame de kayak",
        "todos los store procedures",
        "el primero que mencionaste",
        "sus dependencias"
    ]
    
    times = []
    for query in queries:
        start = time.time()
        response = agent.process(query)
        elapsed = time.time() - start
        times.append(elapsed)
        print(f"{query[:30]}: {elapsed:.2f}s")
    
    avg_time = sum(times) / len(times)
    print(f"\nPromedio: {avg_time:.2f}s")
    return avg_time
```

### Tests de Calidad
```python
# scripts/test_memory_quality.py (NUEVO)

def test_context_retention():
    """Valida que el agente mantiene contexto correctamente."""
    agent = MasterAgent()
    
    # Turno 1: Establecer contexto
    r1 = agent.process("hablame de kayak")
    assert "kayak" in r1.lower()
    
    # Turno 2: Referencia vaga
    r2 = agent.process("todos los store procedures")
    assert "kayak" in r2.lower(), "Perdió contexto de kayak"
    
    # Turno 3: Referencia ordinal
    r3 = agent.process("el primero que mencionaste")
    assert len(r3) > 100, "No recordó el primer procedure"
    
    print("✅ Contexto retenido correctamente")
```

---

## 📋 Checklist General

### Fase 1: Quick Wins
- [ ] Context Caching implementado
- [ ] LangChain Buffer Memory integrado
- [ ] Tests de performance ejecutados
- [ ] Documentación actualizada

### Fase 2: Arquitectura Robusta
- [ ] Weaviate memory schema creado
- [ ] Búsqueda semántica de memoria funcional
- [ ] Entity tracker implementado
- [ ] Integración end-to-end validada

### Fase 3: Producción
- [ ] Benchmarks completados
- [ ] Tests de calidad pasando
- [ ] Documentación completa
- [ ] Deploy a producción

---

## 🎯 KPIs de Éxito

| Métrica | Baseline (actual) | Target (post-mejora) |
|---------|------------------|----------------------|
| Latencia promedio | X segundos | -50% |
| Retención de contexto | 50% | 95% |
| Interpretación correcta | 60% | 90% |
| Costo por query | $X | -30% |

---

## 📅 Timeline

```
Semana 1 (Hoy):
├── Días 1-2: Fase 1 (Quick Wins)
└── Días 3-5: Diseño Fase 2

Semana 2:
├── Días 1-3: Implementación Weaviate Memory
└── Días 4-5: Integración con MasterAgent

Semana 3:
├── Días 1-2: Entity Tracker
├── Días 3-4: Tests y ajustes
└── Día 5: Documentación

Semana 4:
├── Días 1-2: Benchmarks
├── Días 3-4: Optimizaciones
└── Día 5: Deploy
```

---

**Próximo paso inmediato**: ¿Empezamos con Fase 1 (Context Caching + LangChain)?

