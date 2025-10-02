"""
Agentes especializados usando Gemini API.

Este módulo implementa los agentes de IA que coordinan
el análisis inteligente del código SQL legacy usando Gemini.
"""

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from google import genai
from google.genai import types

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from .config import AgentConfig, WeaviateConfig
from .weaviate_client import WeaviateClient

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Clase base para todos los agentes del sistema usando Gemini."""

    def __init__(
        self,
        name: str,
        description: str,
        weaviate_client: WeaviateClient,
        config: Optional[AgentConfig] = None,
    ):
        """
        Inicializa el agente base con Gemini.
        
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
        
        # Inicializar cliente Gemini
        weaviate_config = WeaviateConfig()
        self.gemini_client = genai.Client(api_key=weaviate_config.GEMINI_API_KEY)
        
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
        """Retorna contexto de memoria para Gemini."""
        if not self.memory:
            return ""
        
        context_parts = []
        for interaction in self.memory[-3:]:  # Últimas 3 interacciones
            context_parts.append(f"Q: {interaction['query']}")
            context_parts.append(f"A: {interaction['response'].get('summary', '')}")
        
        return "\n".join(context_parts)

    def _call_gemini(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Llama a Gemini con el prompt especificado.
        
        Args:
            prompt: Prompt del usuario.
            system_prompt: Prompt del sistema (opcional).
            
        Returns:
            Respuesta de Gemini.
        """
        try:
            # Preparar contenido
            contents = []
            
            if system_prompt:
                contents.append(types.Content(
                    role="user",
                    parts=[types.Part.from_text(system_prompt)]
                ))
                contents.append(types.Content(
                    role="model", 
                    parts=[types.Part.from_text("Entendido. Estoy listo para ayudar.")]
                ))
            
            contents.append(types.Content(
                role="user",
                parts=[types.Part.from_text(prompt)]
            ))
            
            # Configurar generación
            config = types.GenerateContentConfig(
                temperature=self.config.TEMPERATURE,
                max_output_tokens=self.config.MAX_TOKENS,
            )
            
            # Llamar a Gemini
            response = self.gemini_client.models.generate_content(
                model=self.config.LLM_MODEL,
                contents=contents,
                config=config,
            )
            
            return response.text
            
        except Exception as e:
            logger.error("Error llamando a Gemini: %s", e)
            raise


class CodeSearchAgent(BaseAgent):
    """
    Agente especializado en búsqueda de código usando Gemini.
    
    Implementa búsqueda semántica, por patrones y híbrida
    para encontrar objetos de código relevantes.
    """

    def __init__(self, weaviate_client: WeaviateClient, config: Optional[AgentConfig] = None):
        """Inicializa el agente de búsqueda de código con Gemini."""
        super().__init__(
            name="CodeSearchAgent",
            description="Especialista en búsqueda semántica y por patrones de código SQL usando Gemini",
            weaviate_client=weaviate_client,
            config=config,
        )

    def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Procesa consulta de búsqueda de código usando Gemini.
        
        Args:
            query: Consulta de búsqueda.
            context: Contexto adicional (filtros, preferencias).
            
        Returns:
            Resultados de búsqueda con análisis de Gemini.
        """
        try:
            logger.info("CodeSearchAgent (Gemini) procesando: %s", query)
            
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
            
            # Analizar resultados con Gemini
            analysis = self._analyze_search_results_with_gemini(query, results)
            
            response = {
                "agent": self.name,
                "query": query,
                "results": results,
                "analysis": analysis,
                "total_found": len(results),
                "search_type": search_type,
                "powered_by": "Gemini",
            }
            
            # Agregar a memoria
            self.add_to_memory(query, response)
            
            return response
            
        except Exception as e:
            logger.error("Error en CodeSearchAgent (Gemini): %s", e)
            return {
                "agent": self.name,
                "query": query,
                "error": str(e),
                "results": [],
                "total_found": 0,
                "powered_by": "Gemini",
            }

    def _semantic_search(
        self, 
        query: str, 
        limit: int, 
        filters: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Búsqueda semántica usando embeddings de Gemini."""
        # Generar embedding para la query usando Gemini
        query_embedding = self._generate_embedding(query)
        
        # Usar Weaviate con vector manual
        return self.weaviate_client.search_code_objects_by_vector(
            vector=query_embedding,
            limit=limit,
            filters=filters,
        )

    def _generate_embedding(self, text: str) -> List[float]:
        """Genera embedding usando Gemini."""
        try:
            response = self.gemini_client.models.embed_content(
                model="text-embedding-004",
                content=text,
            )
            return response.embedding
            
        except Exception as e:
            logger.error("Error generando embedding: %s", e)
            # Fallback: vector cero
            return [0.0] * 768

    def _keyword_search(
        self, 
        query: str, 
        limit: int, 
        filters: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Búsqueda por keywords en metadata."""
        return self.weaviate_client.search_code_objects(
            query=query,
            limit=limit, 
            filters=filters,
            hybrid=False,  # Solo BM25
        )

    def _hybrid_search(
        self, 
        query: str, 
        limit: int, 
        filters: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Búsqueda híbrida combinando vectores Gemini y keywords."""
        # Generar embedding con Gemini
        query_embedding = self._generate_embedding(query)
        
        # Combinar búsqueda vectorial y por keywords
        return self.weaviate_client.search_code_objects_hybrid(
            query=query,
            vector=query_embedding,
            limit=limit,
            filters=filters,
        )

    def _analyze_search_results_with_gemini(self, query: str, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analiza los resultados de búsqueda con Gemini."""
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
            
            response_text = self._call_gemini(prompt, self.config.CODE_SEARCH_AGENT_PROMPT)
            
            # Parsear JSON de la respuesta
            # Gemini a veces incluye texto extra, extraer solo el JSON
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                analysis = json.loads(json_text)
            else:
                # Fallback si no se puede parsear JSON
                analysis = {
                    "summary": response_text[:200] + "..." if len(response_text) > 200 else response_text,
                    "relevance_assessment": "Análisis disponible",
                    "patterns_identified": [],
                    "recommendations": [],
                }
            
            return analysis
            
        except Exception as e:
            logger.warning("Error analizando resultados con Gemini: %s", e)
            return {
                "summary": f"Encontrados {len(results)} objetos relacionados con '{query}'",
                "relevance_assessment": "Análisis no disponible",
                "patterns_identified": [],
                "recommendations": [],
            }


class DependencyAnalysisAgent(BaseAgent):
    """
    Agente especializado en análisis de dependencias usando Gemini.
    
    Mapea relaciones entre objetos y analiza impacto de cambios.
    """

    def __init__(self, weaviate_client: WeaviateClient, config: Optional[AgentConfig] = None):
        """Inicializa el agente de análisis de dependencias con Gemini."""
        super().__init__(
            name="DependencyAnalysisAgent",
            description="Especialista en análisis de dependencias usando Gemini",
            weaviate_client=weaviate_client,
            config=config,
        )

    def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Procesa consulta de análisis de dependencias usando Gemini.
        
        Args:
            query: Consulta sobre dependencias.
            context: Contexto con objeto_id u otros parámetros.
            
        Returns:
            Análisis de dependencias con insights de Gemini.
        """
        try:
            logger.info("DependencyAnalysisAgent (Gemini) procesando: %s", query)
            
            # Extraer objeto de interés del contexto o query
            target_object = self._extract_target_object(query, context)
            
            if not target_object:
                return {
                    "agent": self.name,
                    "query": query,
                    "error": "No se pudo identificar el objeto target",
                    "dependencies": [],
                    "powered_by": "Gemini",
                }
            
            # Analizar dependencias
            dependencies = self._analyze_dependencies(target_object)
            
            # Analizar impacto con Gemini
            impact_analysis = self._analyze_impact_with_gemini(target_object, dependencies)
            
            response = {
                "agent": self.name,
                "query": query,
                "target_object": target_object,
                "dependencies": dependencies,
                "impact_analysis": impact_analysis,
                "total_dependencies": len(dependencies),
                "powered_by": "Gemini",
            }
            
            self.add_to_memory(query, response)
            return response
            
        except Exception as e:
            logger.error("Error en DependencyAnalysisAgent (Gemini): %s", e)
            return {
                "agent": self.name,
                "query": query,
                "error": str(e),
                "dependencies": [],
                "powered_by": "Gemini",
            }

    def _extract_target_object(self, query: str, context: Optional[Dict[str, Any]]) -> Optional[str]:
        """Extrae el objeto target usando Gemini para NLP."""
        # Si hay objeto_id en contexto, usarlo
        if context and "object_id" in context:
            return context["object_id"]
        
        try:
            # Usar Gemini para extraer entidades del query
            prompt = f"""
            Extrae el nombre del objeto SQL (tabla, procedimiento, vista, función) 
            de esta consulta: "{query}"
            
            Responde solo con el nombre del objeto, o "NONE" si no hay uno específico.
            Ejemplos:
            - "¿Qué depende de la tabla Usuarios?" → "Usuarios"
            - "Analiza el procedimiento sp_Login" → "sp_Login"
            - "¿Hay código similar?" → "NONE"
            """
            
            response = self._call_gemini(prompt)
            extracted = response.strip()
            
            return extracted if extracted != "NONE" else None
            
        except Exception as e:
            logger.warning("Error extrayendo objeto con Gemini: %s", e)
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

    def _analyze_impact_with_gemini(self, object_id: str, dependencies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analiza el impacto potencial usando Gemini."""
        try:
            # Calcular métricas básicas
            total_deps = len(dependencies)
            critical_deps = sum(1 for dep in dependencies if dep.get("is_critical", False))
            
            # Preparar contexto para Gemini
            deps_summary = []
            for dep in dependencies[:10]:  # Top 10 dependencias
                target_info = dep.get("target_info", {})
                deps_summary.append(
                    f"- {dep['dependency_type']}: {target_info.get('name', 'Unknown')} "
                    f"({target_info.get('type', 'Unknown')})"
                )
            
            prompt = f"""
            Analiza el impacto de modificar el objeto SQL: {object_id}
            
            Dependencias encontradas ({total_deps} total, {critical_deps} críticas):
            {chr(10).join(deps_summary)}
            
            Proporciona análisis en formato JSON:
            {{
                "impact_level": "LOW|MEDIUM|HIGH|CRITICAL",
                "risk_assessment": "Evaluación detallada del riesgo",
                "recommendations": ["recomendación1", "recomendación2"],
                "migration_strategy": "Estrategia sugerida para cambios seguros",
                "testing_requirements": ["test1", "test2"]
            }}
            """
            
            response_text = self._call_gemini(prompt, self.config.DEPENDENCY_AGENT_PROMPT)
            
            # Parsear respuesta JSON
            try:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                
                if json_start != -1 and json_end > json_start:
                    json_text = response_text[json_start:json_end]
                    analysis = json.loads(json_text)
                else:
                    raise ValueError("No se encontró JSON válido")
                    
            except (json.JSONDecodeError, ValueError):
                # Fallback si no se puede parsear
                analysis = self._create_fallback_impact_analysis(total_deps, critical_deps)
            
            # Agregar métricas calculadas
            analysis.update({
                "total_dependencies": total_deps,
                "critical_dependencies": critical_deps,
                "risk_factors": self._identify_risk_factors(dependencies),
            })
            
            return analysis
            
        except Exception as e:
            logger.error("Error analizando impacto con Gemini: %s", e)
            return self._create_fallback_impact_analysis(len(dependencies), 0)

    def _create_fallback_impact_analysis(self, total_deps: int, critical_deps: int) -> Dict[str, Any]:
        """Crea análisis de impacto de fallback."""
        # Determinar nivel de impacto basado en métricas
        if critical_deps > 5 or total_deps > 20:
            impact_level = "HIGH"
        elif critical_deps > 2 or total_deps > 10:
            impact_level = "MEDIUM"
        else:
            impact_level = "LOW"
        
        return {
            "impact_level": impact_level,
            "risk_assessment": f"Objeto con {total_deps} dependencias ({critical_deps} críticas)",
            "recommendations": [
                "Revisar todas las dependencias antes de modificar",
                "Planificar testing exhaustivo",
                "Considerar implementación gradual",
            ],
            "migration_strategy": "Análisis detallado requerido",
            "testing_requirements": ["Tests unitarios", "Tests de integración"],
        }

    def _identify_risk_factors(self, dependencies: List[Dict[str, Any]]) -> List[str]:
        """Identifica factores de riesgo en las dependencias."""
        risk_factors = []
        
        # Alto número de dependencias
        if len(dependencies) > 15:
            risk_factors.append("Alto número de dependencias")
        
        # Dependencias críticas
        critical_count = sum(1 for dep in dependencies if dep.get("is_critical", False))
        if critical_count > 3:
            risk_factors.append(f"{critical_count} dependencias críticas")
        
        # Tipos de dependencia riesgosos
        risky_types = ["FK", "TRIGGER", "CONSTRAINT"]
        for dep in dependencies:
            if dep.get("dependency_type") in risky_types:
                risk_factors.append(f"Dependencia {dep['dependency_type']} detectada")
                break
        
        return risk_factors


class MasterAgent(BaseAgent):
    """
    Agente maestro que coordina otros agentes usando Gemini.
    
    Implementa el patrón de coordinación multi-agente
    para responder consultas complejas.
    """

    def __init__(
        self,
        weaviate_client: WeaviateClient,
        config: Optional[AgentConfig] = None,
    ):
        """Inicializa el agente maestro con Gemini."""
        super().__init__(
            name="MasterAgent",
            description="Coordinador principal del sistema multi-agente usando Gemini",
            weaviate_client=weaviate_client,
            config=config,
        )
        
        # Inicializar agentes especializados
        self.code_search_agent = CodeSearchAgent(weaviate_client, config)
        self.dependency_agent = DependencyAnalysisAgent(weaviate_client, config)

    def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Procesa consulta coordinando agentes especializados con Gemini.
        
        Args:
            query: Consulta del usuario.
            context: Contexto adicional.
            
        Returns:
            Respuesta sintetizada de múltiples agentes usando Gemini.
        """
        try:
            logger.info("MasterAgent (Gemini) procesando: %s", query)
            
            # Analizar tipo de consulta con Gemini
            query_analysis = self._analyze_query_intent_with_gemini(query)
            
            # Coordinar agentes según el análisis
            agent_responses = self._coordinate_agents(query, query_analysis, context)
            
            # Sintetizar respuesta final con Gemini
            final_response = self._synthesize_response_with_gemini(query, query_analysis, agent_responses)
            
            self.add_to_memory(query, final_response)
            return final_response
            
        except Exception as e:
            logger.error("Error en MasterAgent (Gemini): %s", e)
            return {
                "agent": self.name,
                "query": query,
                "error": str(e),
                "response": "Lo siento, ocurrió un error procesando tu consulta.",
                "powered_by": "Gemini",
            }

    def _analyze_query_intent_with_gemini(self, query: str) -> Dict[str, Any]:
        """Analiza la intención de la consulta usando Gemini."""
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
            
            response_text = self._call_gemini(prompt, self.config.MASTER_AGENT_PROMPT)
            
            # Extraer JSON de la respuesta
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                return json.loads(json_text)
            else:
                raise ValueError("No se encontró JSON válido en respuesta de Gemini")
            
        except Exception as e:
            logger.warning("Error analizando intención con Gemini: %s", e)
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

    def _synthesize_response_with_gemini(
        self, 
        query: str, 
        query_analysis: Dict[str, Any], 
        agent_responses: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Sintetiza respuesta final usando Gemini."""
        try:
            # Preparar contexto para síntesis
            synthesis_context = []
            
            if "code_search" in agent_responses:
                search_resp = agent_responses["code_search"]
                synthesis_context.append(
                    f"Búsqueda de código: {search_resp.get('total_found', 0)} objetos encontrados"
                )
                if search_resp.get("analysis", {}).get("summary"):
                    synthesis_context.append(f"Análisis: {search_resp['analysis']['summary']}")
            
            if "dependency" in agent_responses:
                dep_resp = agent_responses["dependency"]
                synthesis_context.append(
                    f"Análisis de dependencias: {dep_resp.get('total_dependencies', 0)} dependencias"
                )
                if dep_resp.get("impact_analysis", {}).get("impact_level"):
                    impact_level = dep_resp["impact_analysis"]["impact_level"]
                    synthesis_context.append(f"Nivel de impacto: {impact_level}")
            
            prompt = f"""
            Sintetiza una respuesta coherente y útil para la consulta: "{query}"

            Información recopilada por agentes especializados:
            {chr(10).join(synthesis_context)}

            Contexto de conversación previa:
            {self.get_memory_context()}

            Proporciona una respuesta clara, concisa y accionable que:
            1. Responda directamente la consulta
            2. Combine la información de los agentes
            3. Incluya recomendaciones específicas si es relevante
            4. Sea útil para un desarrollador o arquitecto

            Mantén la respuesta profesional pero accesible.
            """
            
            synthesized_response = self._call_gemini(prompt, self.config.MASTER_AGENT_PROMPT)
            
            return {
                "agent": self.name,
                "query": query,
                "response": synthesized_response,
                "query_analysis": query_analysis,
                "agent_responses": agent_responses,
                "timestamp": str(datetime.now()),
                "powered_by": "Gemini",
            }
            
        except Exception as e:
            logger.error("Error sintetizando respuesta con Gemini: %s", e)
            
            # Fallback: respuesta simple basada en datos disponibles
            fallback_response = self._create_fallback_response(query, agent_responses)
            
            return {
                "agent": self.name,
                "query": query,
                "response": fallback_response,
                "agent_responses": agent_responses,
                "synthesis_error": str(e),
                "powered_by": "Gemini",
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
