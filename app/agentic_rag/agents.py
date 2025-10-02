"""
Agentes especializados para el sistema Agentic RAG.

Este módulo implementa los agentes de IA que coordinan
el análisis inteligente del código SQL legacy.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from openai import OpenAI

from .config import AgentConfig, WeaviateConfig
from .weaviate_client import WeaviateClient

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Clase base para todos los agentes del sistema."""

    def __init__(
        self,
        name: str,
        description: str,
        weaviate_client: WeaviateClient,
        config: Optional[AgentConfig] = None,
    ):
        """
        Inicializa el agente base.
        
        Args:
            name: Nombre del agente.
            description: Descripción de capacidades.
            weaviate_client: Cliente Weaviate.
            config: Configuración del agente.
        """
        self.name = name
        self.description = description
        self.weaviate_client = weaviate_client
        self.config = config or AgentConfig()
        self.openai_client = OpenAI()
        
        # Memoria de conversación
        self.memory: List[Dict[str, Any]] = []

    @abstractmethod
    def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Procesa una consulta específica del agente.
        
        Args:
            query: Consulta del usuario.
            context: Contexto adicional.
            
        Returns:
            Respuesta del agente.
        """
        pass

    def add_to_memory(self, query: str, response: Dict[str, Any]) -> None:
        """Agrega interacción a la memoria."""
        self.memory.append({
            "timestamp": str(datetime.now()),
            "query": query,
            "response": response,
        })
        
        # Mantener solo las últimas N interacciones
        if len(self.memory) > self.config.MEMORY_WINDOW:
            self.memory = self.memory[-self.config.MEMORY_WINDOW:]

    def get_memory_context(self) -> str:
        """Retorna contexto de memoria para el LLM."""
        if not self.memory:
            return ""
        
        context_parts = []
        for interaction in self.memory[-3:]:  # Últimas 3 interacciones
            context_parts.append(f"Q: {interaction['query']}")
            context_parts.append(f"A: {interaction['response'].get('summary', '')}")
        
        return "\n".join(context_parts)


class CodeSearchAgent(BaseAgent):
    """
    Agente especializado en búsqueda de código.
    
    Implementa búsqueda semántica, por patrones y híbrida
    para encontrar objetos de código relevantes.
    """

    def __init__(self, weaviate_client: WeaviateClient, config: Optional[AgentConfig] = None):
        """Inicializa el agente de búsqueda de código."""
        super().__init__(
            name="CodeSearchAgent",
            description="Especialista en búsqueda semántica y por patrones de código SQL",
            weaviate_client=weaviate_client,
            config=config,
        )

    def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Procesa consulta de búsqueda de código.
        
        Args:
            query: Consulta de búsqueda.
            context: Contexto adicional (filtros, preferencias).
            
        Returns:
            Resultados de búsqueda con análisis.
        """
        try:
            logger.info("CodeSearchAgent procesando: %s", query)
            
            # Extraer parámetros del contexto
            limit = context.get("limit", 10) if context else 10
            filters = context.get("filters") if context else None
            search_type = context.get("search_type", "hybrid") if context else "hybrid"
            
            # Ejecutar búsqueda
            if search_type == "semantic":
                results = self._semantic_search(query, limit, filters)
            elif search_type == "keyword":
                results = self._keyword_search(query, limit, filters)
            else:
                results = self._hybrid_search(query, limit, filters)
            
            # Analizar resultados con IA
            analysis = self._analyze_search_results(query, results)
            
            response = {
                "agent": self.name,
                "query": query,
                "results": results,
                "analysis": analysis,
                "total_found": len(results),
                "search_type": search_type,
            }
            
            # Agregar a memoria
            self.add_to_memory(query, response)
            
            return response
            
        except Exception as e:
            logger.error("Error en CodeSearchAgent: %s", e)
            return {
                "agent": self.name,
                "query": query,
                "error": str(e),
                "results": [],
                "total_found": 0,
            }

    def _semantic_search(
        self, 
        query: str, 
        limit: int, 
        filters: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Búsqueda semántica pura usando vectores."""
        return self.weaviate_client.search_code_objects(
            query=query,
            limit=limit,
            filters=filters,
            hybrid=False,
        )

    def _keyword_search(
        self, 
        query: str, 
        limit: int, 
        filters: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Búsqueda por keywords en metadata."""
        # Implementar búsqueda BM25 pura cuando esté disponible
        # Por ahora usar híbrida con alpha=0 (solo keywords)
        return self.weaviate_client.search_code_objects(
            query=query,
            limit=limit, 
            filters=filters,
            hybrid=True,  # Con alpha=0 en config
        )

    def _hybrid_search(
        self, 
        query: str, 
        limit: int, 
        filters: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Búsqueda híbrida combinando vectores y keywords."""
        return self.weaviate_client.search_code_objects(
            query=query,
            limit=limit,
            filters=filters,
            hybrid=True,
        )

    def _analyze_search_results(self, query: str, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analiza los resultados de búsqueda con IA."""
        if not results:
            return {"summary": "No se encontraron resultados relevantes."}
        
        try:
            # Preparar contexto para análisis
            results_summary = []
            for i, result in enumerate(results[:5]):  # Top 5 para análisis
                results_summary.append(
                    f"{i+1}. {result['object_name']} ({result['object_type']}) "
                    f"- {result['server']}/{result['database']} "
                    f"- {result.get('code_summary', 'Sin resumen')}"
                )
            
            prompt = f"""
            Analiza estos resultados de búsqueda para la consulta: "{query}"

            Resultados encontrados:
            {chr(10).join(results_summary)}

            Proporciona un análisis en formato JSON:
            {{
                "summary": "Resumen ejecutivo de los resultados (2-3 líneas)",
                "relevance_assessment": "Qué tan relevantes son los resultados",
                "patterns_identified": ["patrón1", "patrón2"],
                "recommendations": ["recomendación1", "recomendación2"]
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model=self.config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": self.config.CODE_SEARCH_AGENT_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=self.config.TEMPERATURE,
                max_tokens=800,
            )
            
            analysis = json.loads(response.choices[0].message.content)
            return analysis
            
        except Exception as e:
            logger.warning("Error analizando resultados: %s", e)
            return {
                "summary": f"Encontrados {len(results)} objetos relacionados con '{query}'",
                "relevance_assessment": "Análisis no disponible",
                "patterns_identified": [],
                "recommendations": [],
            }


class DependencyAnalysisAgent(BaseAgent):
    """
    Agente especializado en análisis de dependencias.
    
    Mapea relaciones entre objetos y analiza impacto de cambios.
    """

    def __init__(self, weaviate_client: WeaviateClient, config: Optional[AgentConfig] = None):
        """Inicializa el agente de análisis de dependencias."""
        super().__init__(
            name="DependencyAnalysisAgent",
            description="Especialista en análisis de dependencias y relaciones entre objetos",
            weaviate_client=weaviate_client,
            config=config,
        )

    def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Procesa consulta de análisis de dependencias.
        
        Args:
            query: Consulta sobre dependencias.
            context: Contexto con objeto_id u otros parámetros.
            
        Returns:
            Análisis de dependencias.
        """
        try:
            logger.info("DependencyAnalysisAgent procesando: %s", query)
            
            # Extraer objeto de interés del contexto o query
            target_object = self._extract_target_object(query, context)
            
            if not target_object:
                return {
                    "agent": self.name,
                    "query": query,
                    "error": "No se pudo identificar el objeto target",
                    "dependencies": [],
                }
            
            # Analizar dependencias
            dependencies = self._analyze_dependencies(target_object)
            
            # Analizar impacto
            impact_analysis = self._analyze_impact(target_object, dependencies)
            
            response = {
                "agent": self.name,
                "query": query,
                "target_object": target_object,
                "dependencies": dependencies,
                "impact_analysis": impact_analysis,
                "total_dependencies": len(dependencies),
            }
            
            self.add_to_memory(query, response)
            return response
            
        except Exception as e:
            logger.error("Error en DependencyAnalysisAgent: %s", e)
            return {
                "agent": self.name,
                "query": query,
                "error": str(e),
                "dependencies": [],
            }

    def _extract_target_object(self, query: str, context: Optional[Dict[str, Any]]) -> Optional[str]:
        """Extrae el objeto target del query o contexto."""
        # Si hay objeto_id en contexto, usarlo
        if context and "object_id" in context:
            return context["object_id"]
        
        # TODO: Usar NLP para extraer nombre de objeto del query
        # Por ahora, buscar patrones simples
        import re
        
        # Buscar patrones como "tabla X", "procedimiento Y", etc.
        patterns = [
            r"tabla\s+(\w+)",
            r"procedure\s+(\w+)", 
            r"view\s+(\w+)",
            r"objeto\s+(\w+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query.lower())
            if match:
                return match.group(1)
        
        return None

    def _analyze_dependencies(self, object_id: str) -> List[Dict[str, Any]]:
        """Analiza dependencias de un objeto."""
        try:
            # Obtener dependencias directas de Weaviate
            dependencies = self.weaviate_client.get_object_dependencies(object_id)
            
            # Enriquecer con información adicional
            enriched_deps = []
            for dep in dependencies:
                enriched_dep = self._enrich_dependency(dep)
                enriched_deps.append(enriched_dep)
            
            return enriched_deps
            
        except Exception as e:
            logger.error("Error analizando dependencias: %s", e)
            return []

    def _enrich_dependency(self, dependency: Dict[str, Any]) -> Dict[str, Any]:
        """Enriquece información de dependencia."""
        # Agregar información del objeto target
        target_id = dependency.get("target_object_id")
        if target_id:
            # Buscar información del objeto target
            target_info = self._get_object_info(target_id)
            dependency["target_info"] = target_info
        
        return dependency

    def _get_object_info(self, object_id: str) -> Dict[str, Any]:
        """Obtiene información básica de un objeto."""
        try:
            results = self.weaviate_client.search_code_objects(
                query=object_id,
                limit=1,
                filters={"bigquery_id": object_id},
                hybrid=False,
            )
            
            if results:
                return {
                    "name": results[0].get("object_name"),
                    "type": results[0].get("object_type"),
                    "server": results[0].get("server"),
                    "database": results[0].get("database"),
                }
            
            return {"name": "Unknown", "type": "Unknown"}
            
        except Exception:
            return {"name": "Error", "type": "Error"}

    def _analyze_impact(self, object_id: str, dependencies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analiza el impacto potencial de cambios."""
        try:
            # Calcular métricas de impacto
            total_deps = len(dependencies)
            critical_deps = sum(1 for dep in dependencies if dep.get("is_critical", False))
            
            # Categorizar nivel de impacto
            if critical_deps > 5 or total_deps > 20:
                impact_level = "HIGH"
            elif critical_deps > 2 or total_deps > 10:
                impact_level = "MEDIUM"
            else:
                impact_level = "LOW"
            
            # Generar recomendaciones con IA
            recommendations = self._generate_impact_recommendations(
                object_id, dependencies, impact_level
            )
            
            return {
                "impact_level": impact_level,
                "total_dependencies": total_deps,
                "critical_dependencies": critical_deps,
                "recommendations": recommendations,
                "risk_factors": self._identify_risk_factors(dependencies),
            }
            
        except Exception as e:
            logger.error("Error analizando impacto: %s", e)
            return {"impact_level": "UNKNOWN", "error": str(e)}

    def _generate_impact_recommendations(
        self, 
        object_id: str, 
        dependencies: List[Dict[str, Any]], 
        impact_level: str
    ) -> List[str]:
        """Genera recomendaciones usando IA."""
        try:
            deps_summary = []
            for dep in dependencies[:5]:  # Top 5 dependencias
                target_info = dep.get("target_info", {})
                deps_summary.append(
                    f"- {dep['dependency_type']}: {target_info.get('name', 'Unknown')} "
                    f"({target_info.get('type', 'Unknown')})"
                )
            
            prompt = f"""
            Analiza el impacto de modificar el objeto: {object_id}
            
            Nivel de impacto: {impact_level}
            Dependencias principales:
            {chr(10).join(deps_summary)}
            
            Proporciona recomendaciones específicas en formato JSON:
            {{
                "recommendations": [
                    "Recomendación específica 1",
                    "Recomendación específica 2", 
                    "Recomendación específica 3"
                ]
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model=self.config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": self.config.DEPENDENCY_AGENT_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=self.config.TEMPERATURE,
                max_tokens=600,
            )
            
            result = json.loads(response.choices[0].message.content)
            return result.get("recommendations", [])
            
        except Exception as e:
            logger.warning("Error generando recomendaciones: %s", e)
            return [
                f"Revisar cuidadosamente las {len(dependencies)} dependencias",
                "Planificar testing exhaustivo antes de cambios",
                "Considerar implementación gradual",
            ]

    def _identify_risk_factors(self, dependencies: List[Dict[str, Any]]) -> List[str]:
        """Identifica factores de riesgo en las dependencias."""
        risk_factors = []
        
        # Dependencias circulares
        if self._has_circular_dependencies(dependencies):
            risk_factors.append("Dependencias circulares detectadas")
        
        # Alto número de dependencias
        if len(dependencies) > 15:
            risk_factors.append("Alto número de dependencias")
        
        # Dependencias críticas
        critical_count = sum(1 for dep in dependencies if dep.get("is_critical", False))
        if critical_count > 3:
            risk_factors.append(f"{critical_count} dependencias críticas")
        
        return risk_factors

    def _has_circular_dependencies(self, dependencies: List[Dict[str, Any]]) -> bool:
        """Detecta dependencias circulares básicas."""
        # Implementación simplificada - en producción usar algoritmo de grafos
        source_targets = [(dep["source_object_id"], dep["target_object_id"]) for dep in dependencies]
        
        for source, target in source_targets:
            # Buscar si target también depende de source
            reverse_exists = any(
                dep["source_object_id"] == target and dep["target_object_id"] == source
                for dep in dependencies
            )
            if reverse_exists:
                return True
        
        return False


class MasterAgent(BaseAgent):
    """
    Agente maestro que coordina otros agentes.
    
    Implementa el patrón de coordinación multi-agente
    para responder consultas complejas.
    """

    def __init__(
        self,
        weaviate_client: WeaviateClient,
        config: Optional[AgentConfig] = None,
    ):
        """Inicializa el agente maestro."""
        super().__init__(
            name="MasterAgent",
            description="Coordinador principal del sistema multi-agente",
            weaviate_client=weaviate_client,
            config=config,
        )
        
        # Inicializar agentes especializados
        self.code_search_agent = CodeSearchAgent(weaviate_client, config)
        self.dependency_agent = DependencyAnalysisAgent(weaviate_client, config)

    def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Procesa consulta coordinando agentes especializados.
        
        Args:
            query: Consulta del usuario.
            context: Contexto adicional.
            
        Returns:
            Respuesta sintetizada de múltiples agentes.
        """
        try:
            logger.info("MasterAgent procesando: %s", query)
            
            # Analizar tipo de consulta
            query_analysis = self._analyze_query_intent(query)
            
            # Coordinar agentes según el análisis
            agent_responses = self._coordinate_agents(query, query_analysis, context)
            
            # Sintetizar respuesta final
            final_response = self._synthesize_response(query, query_analysis, agent_responses)
            
            self.add_to_memory(query, final_response)
            return final_response
            
        except Exception as e:
            logger.error("Error en MasterAgent: %s", e)
            return {
                "agent": self.name,
                "query": query,
                "error": str(e),
                "response": "Lo siento, ocurrió un error procesando tu consulta.",
            }

    def _analyze_query_intent(self, query: str) -> Dict[str, Any]:
        """Analiza la intención de la consulta."""
        try:
            prompt = f"""
            Analiza esta consulta sobre código SQL legacy y determina qué agentes necesitas:

            Consulta: "{query}"

            Agentes disponibles:
            - CodeSearchAgent: Búsqueda semántica de código
            - DependencyAnalysisAgent: Análisis de dependencias e impacto

            Responde en JSON:
            {{
                "primary_intent": "search|dependency|analysis|general",
                "agents_needed": ["CodeSearchAgent", "DependencyAnalysisAgent"],
                "search_terms": ["término1", "término2"],
                "analysis_type": "impact|pattern|architecture|general"
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model=self.config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": self.config.MASTER_AGENT_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=self.config.TEMPERATURE,
                max_tokens=400,
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.warning("Error analizando intención: %s", e)
            # Fallback: usar ambos agentes
            return {
                "primary_intent": "general",
                "agents_needed": ["CodeSearchAgent", "DependencyAnalysisAgent"],
                "search_terms": [query],
                "analysis_type": "general",
            }

    def _coordinate_agents(
        self, 
        query: str, 
        query_analysis: Dict[str, Any], 
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Coordina la ejecución de agentes especializados."""
        responses = {}
        
        agents_needed = query_analysis.get("agents_needed", [])
        
        # Ejecutar CodeSearchAgent si es necesario
        if "CodeSearchAgent" in agents_needed:
            search_context = {
                "limit": context.get("limit", 10) if context else 10,
                "search_type": "hybrid",
            }
            responses["code_search"] = self.code_search_agent.process_query(query, search_context)
        
        # Ejecutar DependencyAnalysisAgent si es necesario
        if "DependencyAnalysisAgent" in agents_needed:
            # Usar resultados de búsqueda como contexto si están disponibles
            dep_context = context or {}
            if "code_search" in responses and responses["code_search"]["results"]:
                # Usar el primer resultado como objeto target
                first_result = responses["code_search"]["results"][0]
                dep_context["object_id"] = first_result.get("bigquery_id")
            
            responses["dependency"] = self.dependency_agent.process_query(query, dep_context)
        
        return responses

    def _synthesize_response(
        self, 
        query: str, 
        query_analysis: Dict[str, Any], 
        agent_responses: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Sintetiza respuesta final combinando información de agentes."""
        try:
            # Preparar contexto para síntesis
            synthesis_context = []
            
            if "code_search" in agent_responses:
                search_resp = agent_responses["code_search"]
                synthesis_context.append(
                    f"Búsqueda de código: {search_resp.get('total_found', 0)} objetos encontrados"
                )
            
            if "dependency" in agent_responses:
                dep_resp = agent_responses["dependency"]
                synthesis_context.append(
                    f"Análisis de dependencias: {dep_resp.get('total_dependencies', 0)} dependencias"
                )
            
            prompt = f"""
            Sintetiza una respuesta coherente para la consulta: "{query}"

            Información recopilada:
            {chr(10).join(synthesis_context)}

            Contexto de memoria:
            {self.get_memory_context()}

            Proporciona una respuesta clara y útil que combine toda la información.
            """
            
            response = self.openai_client.chat.completions.create(
                model=self.config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": self.config.MASTER_AGENT_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=self.config.TEMPERATURE,
                max_tokens=1000,
            )
            
            synthesized_response = response.choices[0].message.content
            
            return {
                "agent": self.name,
                "query": query,
                "response": synthesized_response,
                "query_analysis": query_analysis,
                "agent_responses": agent_responses,
                "timestamp": str(datetime.now()),
            }
            
        except Exception as e:
            logger.error("Error sintetizando respuesta: %s", e)
            
            # Fallback: respuesta simple basada en datos disponibles
            fallback_response = self._create_fallback_response(query, agent_responses)
            
            return {
                "agent": self.name,
                "query": query,
                "response": fallback_response,
                "agent_responses": agent_responses,
                "synthesis_error": str(e),
            }

    def _create_fallback_response(self, query: str, agent_responses: Dict[str, Any]) -> str:
        """Crea respuesta de fallback sin IA."""
        response_parts = []
        
        if "code_search" in agent_responses:
            search_resp = agent_responses["code_search"]
            total_found = search_resp.get("total_found", 0)
            response_parts.append(f"Encontré {total_found} objetos relacionados con '{query}'.")
        
        if "dependency" in agent_responses:
            dep_resp = agent_responses["dependency"]
            total_deps = dep_resp.get("total_dependencies", 0)
            response_parts.append(f"Identifiqué {total_deps} dependencias.")
        
        if not response_parts:
            return "No pude encontrar información específica para tu consulta."
        
        return " ".join(response_parts)
