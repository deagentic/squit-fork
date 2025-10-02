"""
Sistema Agentic RAG con Google ADK para democratizar código SQL legacy.

Este módulo implementa agentes inteligentes que permiten a cualquier persona
entender y trabajar con código SQL legacy mediante lenguaje natural.

Componentes:
- MasterAgent: Orquestador principal
- CodeSearchAgent: Búsqueda semántica
- CodeAnalysisAgent: Análisis de código
- DependencyAgent: Análisis de dependencias
- ExplanationAgent: Generación de explicaciones

Uso:
    from agentic_adk import MasterAgent
    
    agent = MasterAgent()
    response = agent.process("¿Dónde está la lógica de autenticación?")
    print(response)
"""

__version__ = "1.0.0"
__author__ = "Grupo DeAcero"

from .agents.master_agent import MasterAgent
from .agents.code_search_agent import CodeSearchAgent
# CodeAnalysisAgent, DependencyAgent, ExplanationAgent: Fase 2

__all__ = [
    "MasterAgent",
    "CodeSearchAgent",
]
