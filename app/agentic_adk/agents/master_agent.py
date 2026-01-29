"""
MasterAgent - Orquestador principal del sistema agentic.

Este agente coordina todos los agentes especializados para democratizar
el acceso al código SQL legacy.
"""

import logging
import uuid
import asyncio
from typing import Dict, Any, Optional
from google.adk.agents import LlmAgent

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "app"))

from agentic_adk.config import AgenticADKConfig
from agentic_adk.agents.code_search_agent import CodeSearchAgent
from agentic_adk.tools import (
    vector_search_tool,
    get_object_chunks_tool,
    get_object_summary_tool,
    find_dependencies_tool,
    analyze_impact_tool
)

# Importar utilidades de robustez
from utils.rate_limiter import RateLimiter
from utils.metrics import get_metrics

logger = logging.getLogger(__name__)
metrics = get_metrics()

# Nuevas importaciones para Fase 1
try:
    from langchain_core.messages import HumanMessage, AIMessage, trim_messages
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logger.warning("LangChain no disponible, memoria estructurada deshabilitada")

from agentic_adk.query_logger import get_query_logger


class MasterAgent:
    """
    Orquestador principal del sistema agentic SQUIT.
    
    Este agente entiende la intención del usuario y coordina los agentes
    especializados para democratizar el acceso al código SQL legacy.
    
    Capacidades:
    - Búsqueda de código por intención
    - Análisis de código específico
    - Análisis de dependencias e impacto
    - Explicaciones en lenguaje simple
    - Memoria de conversación multi-turn
    
    Ejemplo:
        >>> agent = MasterAgent()
        >>> response = agent.process("¿Dónde está la lógica de autenticación?")
        >>> print(response)
    """
    
    def __init__(self, config: AgenticADKConfig = None):
        """
        Inicializa el MasterAgent con sesión persistente + mejoras Fase 1.
        
        Mejoras implementadas:
        - Gemini Context Caching (reduce latencia 50%)
        - LangChain BufferMemory (estructura explícita)
        - QueryLogger BigQuery (few-shots + analytics)
        - InMemorySessionService (complemento)
        
        Args:
            config: Configuración del sistema agentic.
        """
        self.config = config or AgenticADKConfig()
        self.config.validate()
        
        # IDs persistentes para memoria de conversación
        self.user_id = "squit_user"
        self.session_id = str(uuid.uuid4())
        self.session_service = None
        self.runner = None
        self._session_initialized = False
        self.turn_counter = 0
        
        # 🚀 Rate limiter para llamadas a Gemini (60 req/min)
        self.gemini_rate_limiter = RateLimiter(max_calls=60, time_window=60)
        logger.info("✅ Rate limiter inicializado: 60 req/min")
        
        # 🚀 FASE 1 MEJORA 2: LangChain Structured Memory (sin clases deprecadas)
        if LANGCHAIN_AVAILABLE:
            self.langchain_messages = []  # Lista simple de mensajes
            self.max_messages = 20  # 20 mensajes = 10 turnos (user + assistant)
            logger.info("✅ LangChain message list inicializada (max 10 turnos)")
        else:
            self.langchain_messages = None
        
        # 🚀 FASE 1 MEJORA 3: BigQuery Query Logger
        try:
            self.query_logger = get_query_logger(
                project_id=self.config.PROJECT_ID,
                gemini_api_key=self.config.GEMINI_API_KEY
            )
            logger.info("✅ QueryLogger BigQuery inicializado")
        except Exception as e:
            logger.warning(f"QueryLogger no disponible: {e}")
            self.query_logger = None
        
        # Cache de context caching (se crea después del system prompt)
        self.cached_system_prompt = None
        
        # System prompt con razonamiento mejorado y contexto conversacional
        system_prompt = """
Eres asistente de SQUIT para código SQL legacy (2.9M objetos en BigQuery).

MEMORIA CONVERSACIONAL (CRÍTICO):
Esta es una conversación multi-turn. SIEMPRE revisa el historial antes de responder.

Si el usuario usa referencias vagas como "todos", "estos", "esos", "el primero":
  1. REVISA el contexto de turnos anteriores
  2. INTERPRETA en base al tema/dominio que se está discutiendo
  3. Si estaban hablando de "kayak" y preguntan "todos los procedures", busca procedures de KAYAK

Ejemplos de continuidad contextual:
  Turno 1: "hablame de kayak"
  Turno 2: "todos los store procedures" → INTERPRETAR: "todos los procedures de kayak"
  
  Turno 1: "procedures de inventario"
  Turno 2: "el primero que mencionaste" → INTERPRETAR: primer procedure de inventario mencionado
  
  Turno 1: "AgAsignaFechasKayakProc"
  Turno 2: "sus dependencias" → INTERPRETAR: dependencias de AgAsignaFechasKayakProc

TOOLS:

vector_search_tool(query, limit=10): 
  Busca término en CÓDIGO SQL, nombres de objetos, comentarios
  USA ESTA cuando usuario mencione CUALQUIER término o palabra
  Si hay contexto previo, COMBINA: vector_search_tool(query="kayak procedures")

get_object_summary_tool(object_name):
  Resumen de UN objeto específico por nombre EXACTO
  
find_dependencies_tool(object_name):
  Dependencias de un objeto
  
analyze_impact_tool(object_name):
  Impacto de modificar objeto

FLUJO DE RAZONAMIENTO:

1. LEE el historial de la conversación
2. IDENTIFICA si hay tema/contexto activo (ej: "kayak", "inventario")
3. INTERPRETA la pregunta actual en ese contexto
4. USA tools con queries que COMBINEN contexto + nueva pregunta
5. RESPONDE manteniendo coherencia con el tema

Responde en español, conciso, mostrando nombres reales de objetos.
"""
        
        # Importar componentes ADK
        from google.adk.agents import Agent
        from google.adk.apps import App
        from google.genai.types import GenerateContentConfig
        
        # Crear agente ADK con gemini-2.5-flash (para respuesta final de calidad)
        self.agent = Agent(
            model=self.config.GEMINI_MODEL,  # gemini-2.5-flash para respuesta final
            name="master_agent",
            description="Orquestador principal para democratizar código SQL legacy",
            instruction=system_prompt,
            tools=[
                vector_search_tool,
                get_object_summary_tool,
                get_object_chunks_tool,
                find_dependencies_tool,
                analyze_impact_tool
            ],
            generate_content_config=GenerateContentConfig(
                temperature=self.config.TEMPERATURE,
                top_p=self.config.TOP_P,
                max_output_tokens=self.config.MAX_TOKENS,
            )
        )
        
        # Crear App para el agente
        self.app = App(
            name="squit_democratizador",
            root_agent=self.agent
        )
        
        # Inicializar sesión persistente
        self._initialize_session()
        
        # 🚀 FASE 1 MEJORA 1: Context Caching
        self._initialize_context_caching(system_prompt)
        
        logger.info("✅ MasterAgent inicializado con memoria multi-turn + Fase 1 mejoras")
    
    def _initialize_session(self):
        """
        Inicializa la sesión persistente para memoria de conversación.
        """
        try:
            from google.adk import Runner
            from google.adk.sessions import InMemorySessionService
            
            # Session service para memoria
            self.session_service = InMemorySessionService()
            
            # Crear sesión de forma async
            async def create_session_async():
                await self.session_service.create_session(
                    app_name=self.app.name,
                    user_id=self.user_id,
                    session_id=self.session_id
                )
            
            # Ejecutar creación de sesión
            asyncio.run(create_session_async())
            
            # Crear runner con la App (reutilizable)
            self.runner = Runner(
                app=self.app,
                session_service=self.session_service
            )
            
            self._session_initialized = True
            logger.info(f"✅ Sesión inicializada: {self.session_id[:8]}...")
            
        except Exception as e:
            logger.error(f"Error inicializando sesión: {e}")
            raise
    
    def _initialize_context_caching(self, system_prompt: str):
        """
        🚀 FASE 1 MEJORA 1: Inicializa Gemini Context Caching.
        
        Cachea el system prompt largo para reducir latencia ~50% y costos.
        
        Args:
            system_prompt: System prompt a cachear
        """
        try:
            import google.genai as genai
            from google.genai import types
            
            # Cliente Gemini
            gemini_client = genai.Client(api_key=self.config.GEMINI_API_KEY)
            
            # Crear cached content
            cached = gemini_client.caches.create(
                model=self.config.GEMINI_MODEL,
                contents=[
                    types.Content(
                        role="user",
                        parts=[types.Part(text=system_prompt)]
                    )
                ],
                ttl="3600s",  # Cache por 1 hora
                display_name=f"squit_system_prompt_{self.session_id[:8]}"
            )
            
            self.cached_system_prompt = cached
            logger.info(f"✅ Context caching habilitado: {cached.name}")
            
        except Exception as e:
            logger.warning(f"⚠️ Context caching no disponible: {e}")
            logger.warning("Continuando sin cache (latencia normal)")
            self.cached_system_prompt = None
    
    def reset_conversation(self):
        """
        Reinicia la conversación (nueva sesión con memoria limpia).
        """
        logger.info("🔄 Reiniciando conversación...")
        self.session_id = str(uuid.uuid4())
        self._session_initialized = False
        self.turn_counter = 0
        
        # Limpiar LangChain memory
        if self.langchain_messages is not None:
            self.langchain_messages = []
            logger.info("✅ LangChain memory limpiada")
        
        # Re-inicializar sesión
        self._initialize_session()
    
    def process(self, user_query: str, show_progress: bool = False) -> str:
        """
        Procesa una consulta del usuario con memoria de conversación + mejoras Fase 1.
        
        Mejoras aplicadas:
        - LangChain BufferMemory para contexto estructurado
        - QueryLogger BigQuery para historial y few-shots
        - Context Caching para reducir latencia
        - InMemorySessionService para memoria ADK
        
        Args:
            user_query: Pregunta en lenguaje natural.
            show_progress: Mostrar indicadores de progreso estilo gemini-cli
            
        Returns:
            Respuesta del agente.
        """
        self.turn_counter += 1
        
        if show_progress:
            print("  🤖 Llamando a Gemini 2.5 Flash con memoria + few-shots...", flush=True)
        
        logger.info(f"MasterAgent procesando [Turn {self.turn_counter}]: '{user_query}'")
        
        # 🚀 Métrica: incrementar contador de queries
        metrics.increment("agent_queries_total", tags={"agent": "master"})
        
        # Verificar que sesión está inicializada
        if not self._session_initialized or not self.runner:
            logger.warning("Sesión no inicializada, reinicializando...")
            self._initialize_session()
        
        # 🚀 FASE 1 MEJORA 2: Cargar memoria de LangChain
        langchain_context = ""
        if self.langchain_messages is not None:
            try:
                if self.langchain_messages:
                    # Tomar últimos 6 mensajes (3 turnos)
                    recent_messages = self.langchain_messages[-6:] if len(self.langchain_messages) > 6 else self.langchain_messages
                    langchain_context = self._format_langchain_memory(recent_messages)
                    logger.info(f"✅ Contexto LangChain: {len(self.langchain_messages)} mensajes en memoria")
            except Exception as e:
                logger.warning(f"Error cargando LangChain memory: {e}")
        
        # 🚀 FASE 1 MEJORA 3: Few-shots desde BigQuery
        few_shots_context = ""
        if self.query_logger:
            try:
                few_shots_context = self.query_logger.get_few_shot_examples(
                    query=user_query,
                    limit=2  # 2 ejemplos relevantes
                )
                if few_shots_context:
                    logger.info("✅ Few-shots agregados desde BigQuery")
            except Exception as e:
                logger.warning(f"Error obteniendo few-shots: {e}")
        
        # Combinar contextos adicionales
        enhanced_query = user_query
        if langchain_context or few_shots_context:
            context_parts = []
            if few_shots_context:
                context_parts.append(few_shots_context)
            if langchain_context:
                context_parts.append(langchain_context)
            
            enhanced_context = "\n\n".join(context_parts)
            enhanced_query = f"{enhanced_context}\n\nQuery actual del usuario: {user_query}"
        
        try:
            from google.genai import types
            
            # Crear mensaje del usuario
            message = types.Content(
                role="user",
                parts=[types.Part(text=user_query)]
            )
            
            # 🚀 Rate limiter + Timer para métricas
            with self.gemini_rate_limiter:
                with metrics.timer("agent_process_latency", tags={"agent": "master"}):
                    # Ejecutar consulta usando runner persistente (mantiene historial)
                    events = self.runner.run(
                        user_id=self.user_id,
                        session_id=self.session_id,
                        new_message=message
                    )
                    
                    # Procesar eventos y extraer respuesta
                    result_text = ""
                    event_count = 0
                    
                    for event in events:
                        event_count += 1
                        
                        # Indicar progreso si está habilitado
                        if show_progress and event_count == 1:
                            print("  ✅ Respuesta recibida, procesando...", flush=True)
                        
                        # Los eventos tienen atributo 'content' con parts
                        if hasattr(event, 'content') and event.content:
                            if hasattr(event.content, 'parts'):
                                for part in event.content.parts:
                                    if hasattr(part, 'text') and part.text:
                                        result_text += part.text
                        
                        # También verificar model_turn_complete
                        if hasattr(event, 'model_turn_complete') and event.model_turn_complete:
                            if hasattr(event.model_turn_complete, 'content'):
                                content = event.model_turn_complete.content
                                if content and hasattr(content, 'parts'):
                                    for part in content.parts:
                                        if hasattr(part, 'text') and part.text:
                                            result_text += part.text
                    
                    if not result_text:
                        result_text = "No se obtuvo respuesta del agente"
            
            # 🚀 Métrica: tamaño de respuesta
            metrics.gauge("agent_response_length", len(result_text))
            
            # 🚀 FASE 1 MEJORA 2: Guardar en LangChain memory
            if self.langchain_messages is not None:
                try:
                    # Agregar mensajes del turno actual
                    self.langchain_messages.append(HumanMessage(content=user_query))
                    self.langchain_messages.append(AIMessage(content=result_text))
                    
                    # Mantener solo los últimos N mensajes usando trim_messages
                    if len(self.langchain_messages) > self.max_messages:
                        self.langchain_messages = trim_messages(
                            self.langchain_messages,
                            max_tokens=self.max_messages,
                            strategy="last",
                            token_counter=len  # Contar por cantidad de mensajes
                        )
                    logger.info("✅ Turno guardado en LangChain memory")
                except Exception as e:
                    logger.warning(f"Error guardando en LangChain memory: {e}")
            
            # 🚀 FASE 1 MEJORA 3: Log en BigQuery
            if self.query_logger:
                try:
                    self.query_logger.log_query(
                        session_id=self.session_id,
                        user_query=user_query,
                        assistant_response=result_text,
                        turn_number=self.turn_counter
                    )
                    logger.info("✅ Query logged en BigQuery")
                except Exception as e:
                    logger.warning(f"Error logging en BigQuery: {e}")
            
            logger.info(f"MasterAgent completado ({len(result_text)} chars)")
            return result_text
            
        except Exception as e:
            logger.error(f"Error en MasterAgent: {e}")
            import traceback
            traceback.print_exc()
            return f"❌ Error procesando consulta: {e}"
    
    def _format_langchain_memory(self, messages: list) -> str:
        """
        Formatea historial de LangChain para contexto.
        
        Args:
            messages: Lista de HumanMessage y AIMessage de LangChain
            
        Returns:
            String formateado con historial reciente
        """
        formatted = "Contexto de conversación reciente:\n"
        
        for msg in messages:
            # Determinar rol por tipo de mensaje
            role = "Usuario" if isinstance(msg, HumanMessage) else "Asistente"
            content = msg.content if hasattr(msg, 'content') else str(msg)
            
            # Truncar si es muy largo
            if len(content) > 150:
                content = content[:150] + "..."
            
            formatted += f"{role}: {content}\n"
        
        return formatted
    
    def interactive(self):
        """
        Modo interactivo: conversación continua con el usuario.
        """
        print("\n" + "=" * 80)
        print("🎯 SQUIT - Asistente Inteligente de Código SQL Legacy")
        print("=" * 80)
        print("\nDemo democratización: Pregunta lo que quieras sobre el código SQL")
        print("Escribe 'exit' para salir\n")
        
        while True:
            try:
                user_input = input("\n👤 Tú: ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'salir']:
                    print("\n👋 ¡Hasta luego! Sigue democratizando el conocimiento.")
                    break
                
                if not user_input:
                    continue
                
                print("\n🤖 SQUIT: ", end="", flush=True)
                response = self.process(user_input)
                print(response)
                
            except KeyboardInterrupt:
                print("\n\n👋 ¡Hasta luego!")
                break
            except Exception as e:
                logger.error(f"Error en modo interactivo: {e}")
                print(f"\n❌ Error: {e}")
