"""
Agente de búsqueda semántica de código SQL.

Este agente especializado permite buscar código SQL usando lenguaje natural,
democratizando el acceso al código legacy.
"""

import logging
from typing import Dict, Any
from google.adk.agents import LlmAgent

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "app"))

from agentic_adk.config import AgenticADKConfig
from agentic_adk.tools import vector_search_tool, get_object_chunks_tool

logger = logging.getLogger(__name__)


class CodeSearchAgent:
    """
    Agente especializado en búsqueda semántica de código SQL.
    
    Este agente democratiza la búsqueda de código permitiendo usar lenguaje
    natural en lugar de queries técnicas exactas.
    
    Capacidades:
    - Búsqueda por intención semántica
    - Comprensión de sinónimos y contexto
    - Filtrado por dominio de negocio
    - Rankeo por relevancia
    """
    
    def __init__(self, config: AgenticADKConfig = None):
        """
        Inicializa el agente de búsqueda.
        
        Args:
            config: Configuración del sistema agentic.
        """
        self.config = config or AgenticADKConfig()
        self.config.validate()
        
        # System prompt enfocado en democratización
        system_prompt = """
Eres un agente especializado en BUSCAR código SQL legacy.

Tu objetivo es DEMOCRATIZAR el acceso al código, permitiendo que cualquier persona
(desarrolladores nuevos, arquitectos, managers) pueda encontrar código sin ser experto SQL.

CAPACIDADES:
- Búsqueda semántica: entiendes INTENCIÓN, no solo palabras exactas
- Comprensión de sinónimos: "autenticación" = "login" = "validación usuario"
- Filtros inteligentes: por dominio de negocio (ventas, inventario, etc.)
- Contexto de negocio: entiendes qué código es relevante para qué proceso

TOOLS DISPONIBLES:
1. vector_search_tool: Busca código por intención semántica
   - Úsala cuando el usuario busca "dónde está X" o "código que hace Y"
   - Aplica filtros apropiados (business_domains, object_types)
   - Limita resultados a lo más relevante (5-10)

2. get_object_chunks_tool: Obtiene código completo de un objeto
   - Úsala cuando necesites ver todo el código de un objeto específico
   - Útil después de encontrar un objeto con vector_search_tool

INSTRUCCIONES:
- Si el usuario pregunta genéricamente, usa vector_search_tool
- Si pregunta por objeto específico, usa get_object_summary_tool primero
- Interpreta intención, no palabras literales
- Prefiere recall (encontrar todo relevante) sobre precisión
- Explica resultados en lenguaje simple

DOMINIOS DE NEGOCIO:
- ventas: facturación, clientes, pedidos
- inventario: stock, almacenes, productos
- finanzas: pagos, cuentas, balances
- produccion: manufactura, órdenes
- logistica: envíos, rutas
- recursos_humanos: empleados, nómina
- compras: proveedores, órdenes de compra

Siempre responde en español de forma clara y accesible.
"""
        
        # Importar GenerateContentConfig
        from google.genai.types import GenerateContentConfig
        
        # Crear agente ADK
        self.agent = LlmAgent(
            name="code_search_agent",
            description="Agente especializado en búsqueda semántica de código SQL",
            model=f"gemini/{self.config.GEMINI_MODEL}",
            instruction=system_prompt,
            tools=[vector_search_tool, get_object_chunks_tool],
            generate_content_config=GenerateContentConfig(
                temperature=self.config.TEMPERATURE,
                top_p=self.config.TOP_P,
                max_output_tokens=self.config.MAX_TOKENS,
            )
        )
        
        logger.info("✅ CodeSearchAgent inicializado")
    
    def search(self, query: str) -> str:
        """
        Busca código SQL por intención.
        
        Args:
            query: Pregunta del usuario en lenguaje natural.
            
        Returns:
            Respuesta del agente con resultados.
        """
        logger.info(f"CodeSearchAgent: '{query}'")
        
        try:
            response = self.agent.run(query)
            return response.text
            
        except Exception as e:
            logger.error(f"Error en CodeSearchAgent: {e}")
            return f"Error buscando código: {e}"
