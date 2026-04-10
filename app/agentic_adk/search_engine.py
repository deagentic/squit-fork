"""
Motor de búsqueda inteligente multi-etapa para democratizar código SQL.

Este módulo implementa una estrategia sofisticada de búsqueda:
1. Router inteligente (Gemini) extrae keywords del intent
2. Búsqueda híbrida multi-query al dataset
3. Reranking de resultados
4. Búsqueda iterativa si necesita más contexto
"""

import logging
from typing import List, Dict, Any, Optional
from google.cloud import bigquery
import google.genai as genai

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "app"))

from bigquery_vector.config import BigQueryVectorConfig
from agentic_adk.config import AgenticADKConfig

logger = logging.getLogger(__name__)


class IntelligentSearchEngine:
    """
    Motor de búsqueda inteligente multi-etapa.
    
    Estrategia:
    1. Router LLM → Extrae keywords + sinónimos + contexto
    2. Multi-query → Genera variaciones de búsqueda
    3. Hybrid search → Vector (si disponible) + Keywords en código
    4. Reranking → Ordena por relevancia real
    5. Iterative search → Profundiza si es necesario
    """
    
    def __init__(
        self,
        bq_config: Optional[BigQueryVectorConfig] = None,
        adk_config: Optional[AgenticADKConfig] = None
    ):
        """
        Inicializa el motor de búsqueda.
        
        Args:
            bq_config: Configuración de BigQuery
            adk_config: Configuración de Gemini
        """
        self.bq_config = bq_config or BigQueryVectorConfig()
        self.adk_config = adk_config or AgenticADKConfig()
        self.client = bigquery.Client(project=self.bq_config.PROJECT_ID)
        self.gemini_client = genai.Client(api_key=self.adk_config.GEMINI_API_KEY)
        
        logger.info("✅ IntelligentSearchEngine inicializado")

    def _format_sql(self, sql: str, **kwargs) -> str:
        """Formatea SQL de forma segura para Bandit."""
        return sql.format(**kwargs)  # nosec B608
    
    def search(
        self,
        user_query: str,
        max_results: int = 10,
        business_domains: Optional[List[str]] = None,
        object_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Búsqueda inteligente multi-etapa.
        
        Args:
            user_query: Query del usuario en lenguaje natural
            max_results: Máximo de resultados finales
            business_domains: Filtros opcionales de dominio
            object_types: Filtros opcionales de tipo
            
        Returns:
            Resultados con metadata de búsqueda
        """
        logger.info(f"🔍 Búsqueda inteligente: '{user_query}'")
        
        # ETAPA 1: Router inteligente - Extraer keywords y contexto
        search_intent = self._extract_search_intent(user_query)
        logger.info(f"📋 Intent extraído: {search_intent['keywords']}")
        
        # ETAPA 2: Multi-query - Generar variaciones de búsqueda
        queries = self._generate_search_queries(search_intent, business_domains, object_types)
        logger.info(f"🔄 Generadas {len(queries)} queries")
        
        # ETAPA 3: Ejecutar búsquedas en paralelo
        all_results = []
        for query_variant in queries:
            results = self._execute_hybrid_search(query_variant)
            all_results.extend(results)
        
        logger.info(f"📊 Resultados brutos: {len(all_results)} chunks")
        
        # ETAPA 4: Deduplicar por chunk_id
        unique_results = self._deduplicate_results(all_results)
        logger.info(f"🔹 Después de dedup: {len(unique_results)} chunks únicos")
        
        # ETAPA 5: Reranking con contexto del intent
        reranked = self._rerank_results(unique_results, search_intent, user_query)
        logger.info(f"⭐ Después de rerank: Top {min(len(reranked), max_results)}")
        
        # ETAPA 6: Decidir si necesita búsqueda iterativa
        final_results = reranked[:max_results]
        
        needs_more = self._needs_more_context(final_results, search_intent)
        if needs_more and len(final_results) < 5:
            logger.info("🔍 Búsqueda iterativa: expandiendo contexto...")
            additional = self._iterative_search(search_intent, final_results)
            final_results.extend(additional)
            final_results = self._deduplicate_results(final_results)[:max_results]
        
        return {
            "results": final_results,
            "total_found": len(final_results),
            "search_intent": search_intent,
            "queries_executed": len(queries),
            "needed_iteration": needs_more
        }
    
    def _extract_search_intent(self, user_query: str) -> Dict[str, Any]:
        """
        Usa Gemini + Catálogo para extraer intent enriquecido.
        
        Returns:
            Intent con keywords enriquecidas del catálogo
        """
        # PASO 1: Enriquecer con catálogo de aplicaciones
        from agentic_adk.catalog_enricher import get_catalog_enricher
        
        enricher = get_catalog_enricher()
        catalog_enrichment = enricher.enrich_query(user_query)
        
        # Construir contexto del catálogo para el router
        catalog_context = ""
        if catalog_enrichment['catalog_matches'] > 0:
            catalog_context = f"""
CONTEXTO DEL CATÁLOGO DE APLICACIONES:
- Sistemas relacionados: {', '.join(catalog_enrichment['related_systems'][:3])}
- Keywords sugeridas: {', '.join(catalog_enrichment['enriched_keywords'])}
"""
            if catalog_enrichment['search_hints']:
                catalog_context += f"- Hint: {catalog_enrichment['search_hints'][0][:200]}\n"
        
        # PASO 2: Router LLM con contexto enriquecido
        router_prompt = f"""
Analiza esta consulta sobre código SQL y extrae información de búsqueda:

Consulta: "{user_query}"

{catalog_context}

Extrae:
1. KEYWORDS principales (español E inglés) - términos para buscar en código SQL
   - Incluye códigos de sistema si son relevantes (ej: "AG", "INV", "KAY")
2. SYNONYMS - sinónimos y variaciones
3. DOMAIN_HINTS - dominios de negocio (ventas, inventario, finanzas, produccion, logistica, recursos_humanos, compras)
4. TYPE_HINTS - tipos de objeto (PROCEDURE, VIEW, FUNCTION, TRIGGER, TABLE)
5. COMPLEXITY - nivel esperado (high, medium, any)

Responde SOLO JSON:
{{
  "keywords": ["keyword1", "keyword2"],
  "synonyms": {{"keyword1": ["syn1", "syn2"]}},
  "domain_hints": ["dominio1"],
  "type_hints": ["TYPE1"],
  "complexity": "any"
}}
"""
        
        try:
            from google.genai.types import GenerateContentConfig
            
            # Usar LITE para router (más rápido, menos rate limit)
            response = self.gemini_client.models.generate_content(
                model=self.adk_config.GEMINI_MODEL_LITE,
                contents=router_prompt,
                config=GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
            
            import json
            intent = json.loads(response.text)
            logger.info(f"✅ Intent extraído: {intent.get('keywords', [])}")
            return intent
            
        except Exception as e:
            logger.error(f"Error en router: {e}")
            # Fallback: extracción simple
            words = [w for w in user_query.lower().split() if len(w) > 3]
            return {
                "keywords": words[:5],
                "synonyms": {},
                "domain_hints": [],
                "type_hints": [],
                "complexity": "any"
            }
    
    def _generate_search_queries(
        self,
        intent: Dict[str, Any],
        domains: Optional[List[str]],
        types: Optional[List[str]]
    ) -> List[Dict[str, Any]]:
        """
        Genera múltiples variaciones de búsqueda.
        
        Returns:
            Lista de query configs para ejecutar
        """
        queries = []
        keywords = intent.get('keywords', [])
        synonyms = intent.get('synonyms', {})
        
        # Query 1: Keywords principales
        for keyword in keywords[:3]:  # Top 3 keywords
            queries.append({
                "search_term": keyword,
                "domains": domains or intent.get('domain_hints', []),
                "types": types or intent.get('type_hints', []),
                "weight": 1.0
            })
        
        # Query 2: Sinónimos
        for keyword, syns in synonyms.items():
            for syn in syns[:2]:  # Top 2 sinónimos por keyword
                queries.append({
                    "search_term": syn,
                    "domains": domains or intent.get('domain_hints', []),
                    "types": types or intent.get('type_hints', []),
                    "weight": 0.8
                })
        
        # Query 3: Combinaciones si hay múltiples keywords
        if len(keywords) >= 2:
            combined = " ".join(keywords[:2])
            queries.append({
                "search_term": combined,
                "domains": domains or intent.get('domain_hints', []),
                "types": types or intent.get('type_hints', []),
                "weight": 1.2  # Mayor peso para queries combinadas
            })
        
        return queries[:10]  # Máximo 10 queries
    
    def _execute_hybrid_search(self, query_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Ejecuta búsqueda híbrida parametrizada.
        
        Busca en:
        - object_name
        - chunk_content (CÓDIGO SQL COMPLETO)
        - semantic_summary
        - business_domain
        """
        search_term = query_config['search_term']
        domains = query_config.get('domains', [])
        types = query_config.get('types', [])
        weight = query_config.get('weight', 1.0)
        
        # Parámetros base
        query_parameters = [
            bigquery.ScalarQueryParameter("search_term", "STRING", search_term),
            bigquery.ScalarQueryParameter("weight", "FLOAT64", weight)
        ]

        # Construir filtros WHERE
        where_conditions = []
        if domains:
            where_conditions.append("business_domain IN UNNEST(@domains)")
            query_parameters.append(bigquery.ArrayQueryParameter("domains", "STRING", domains))
        if types:
            where_conditions.append("object_type IN UNNEST(@types)")
            query_parameters.append(bigquery.ArrayQueryParameter("types", "STRING", types))
        
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        # Query híbrida parametrizada - busca en CÓDIGO SQL completo
        sql = self._format_sql("""
        SELECT 
          chunk_id,
          parent_object_id,
          object_name,
          object_type,
          semantic_type,
          business_domain,
          semantic_summary,
          complexity_score,
          chunk_index,
          total_chunks,
          
          -- Score híbrido parametrizado
          (
            -- 50%: Búsqueda en CÓDIGO SQL COMPLETO
            CASE 
              WHEN UPPER(chunk_content) LIKE CONCAT('%', UPPER(@search_term), '%') THEN 0.5
              ELSE 0.0
            END +
            
            -- 25%: Nombre del objeto
            CASE 
              WHEN UPPER(object_name) LIKE CONCAT('%', UPPER(@search_term), '%') THEN 0.25
              ELSE 0.0
            END +
            
            -- 15%: Resumen semántico
            CASE
              WHEN UPPER(semantic_summary) LIKE CONCAT('%', UPPER(@search_term), '%') THEN 0.15
              ELSE 0.0
            END +
            
            -- 10%: Dominio de negocio
            CASE
              WHEN LOWER(business_domain) LIKE CONCAT('%', LOWER(@search_term), '%') THEN 0.1
              ELSE 0.0
            END
          ) * @weight as relevance_score,
          
          SUBSTR(chunk_content, 1, 500) as chunk_preview
          
        FROM `{table}`
        {where_clause}
        {filter_connector} (
          UPPER(chunk_content) LIKE CONCAT('%', UPPER(@search_term), '%')
          OR UPPER(object_name) LIKE CONCAT('%', UPPER(@search_term), '%')
          OR UPPER(semantic_summary) LIKE CONCAT('%', UPPER(@search_term), '%')
        )
        ORDER BY relevance_score DESC
        LIMIT 20
        """, 
        table=self.bq_config.full_embeddings_table_id, 
        where_clause=where_clause,
        filter_connector="AND" if where_clause else "WHERE")
        
        job_config = bigquery.QueryJobConfig(query_parameters=query_parameters)
        
        try:
            results = list(self.client.query(sql, job_config=job_config).result())
            chunks = [dict(row) for row in results]
            logger.info(f"  Query '{search_term}': {len(chunks)} resultados")
            return chunks
        except Exception as e:
            logger.error(f"Error en búsqueda '{search_term}': {e}")
            return []
    
    def _deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """Elimina duplicados por chunk_id, mantiene el de mayor score."""
        seen = {}
        for result in results:
            chunk_id = result['chunk_id']
            score = result.get('relevance_score', 0)
            
            if chunk_id not in seen or seen[chunk_id].get('relevance_score', 0) < score:
                seen[chunk_id] = result
        
        return list(seen.values())
    
    def _rerank_results(
        self,
        results: List[Dict],
        intent: Dict[str, Any],
        original_query: str
    ) -> List[Dict]:
        """
        Reranking inteligente de resultados.
        
        Usa Gemini para reordenar resultados por relevancia real al intent.
        """
        if not results:
            return []
        
        # Si hay pocos resultados, no hace falta reranking
        if len(results) <= 5:
            return sorted(results, key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        # Preparar contexto para reranking con Gemini
        results_summary = []
        for i, r in enumerate(results[:20]):  # Top 20 para reranking
            results_summary.append({
                "index": i,
                "object_name": r['object_name'],
                "type": r['object_type'],
                "domain": r['business_domain'],
                "summary": r['semantic_summary'][:200],
                "initial_score": r.get('relevance_score', 0)
            })
        
        reranking_prompt = f"""
Eres un experto en análisis de código SQL. Reordena estos resultados por relevancia real.

Query original: "{original_query}"
Intent detectado: {intent.get('keywords', [])}

Resultados a reordenar:
{results_summary}

Retorna los índices ordenados de MÁS a MENOS relevante para el query.
Considera:
- Coincidencia con keywords del intent
- Relevancia del dominio de negocio
- Tipo de objeto apropiado
- Complejidad apropiada

Responde SOLO con JSON: {{"reranked_indices": [3, 1, 7, 2, ...]}}
"""
        
        try:
            from google.genai.types import GenerateContentConfig
            
            response = self.gemini_client.models.generate_content(
                model=self.adk_config.GEMINI_MODEL,
                contents=reranking_prompt,
                config=GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
            
            import json
            reranked_data = json.loads(response.text)
            indices = reranked_data.get('reranked_indices', [])
            
            # Reordenar según índices
            reranked_results = []
            for idx in indices:
                if 0 <= idx < len(results):
                    reranked_results.append(results[idx])
            
            # Agregar cualquiera que no esté en el reranking
            for r in results:
                if r not in reranked_results:
                    reranked_results.append(r)
            
            logger.info(f"✅ Reranking aplicado: {len(reranked_results)} resultados")
            return reranked_results
            
        except Exception as e:
            logger.error(f"Error en reranking: {e}")
            # Fallback: ordenar por score original
            return sorted(results, key=lambda x: x.get('relevance_score', 0), reverse=True)
    
    def _needs_more_context(
        self,
        results: List[Dict],
        intent: Dict[str, Any]
    ) -> bool:
        """Decide si necesita búsqueda iterativa adicional."""
        # Si no hay resultados, sí necesita más contexto
        if len(results) == 0:
            return True
        
        # Si hay pocos resultados (< 3), intentar ampliar
        if len(results) < 3:
            return True
        
        # Si los scores son muy bajos (< 0.3), buscar más
        avg_score = sum(r.get('relevance_score', 0) for r in results) / len(results)
        if avg_score < 0.3:
            return True
        
        return False
    
    def _iterative_search(
        self,
        intent: Dict[str, Any],
        current_results: List[Dict]
    ) -> List[Dict]:
        """
        Búsqueda iterativa - expande con sinónimos y términos relacionados.
        """
        logger.info("🔄 Búsqueda iterativa: expandiendo...")
        
        # Generar términos relacionados con Gemini
        expansion_prompt = f"""
Para buscar código SQL, sugiere términos relacionados con estas keywords:
{intent.get('keywords', [])}

Considerando dominios: {intent.get('domain_hints', [])}

Genera 5-10 términos relacionados que podrían aparecer en código SQL.
Por ejemplo:
- inventario → stock, almacen, existencias, inventory, warehouse
- ventas → sale, factura, invoice, pedido, order

Responde SOLO JSON: {{"related_terms": ["term1", "term2", ...]}}
"""
        
        try:
            from google.genai.types import GenerateContentConfig
            import json
            
            # Usar LITE para expansión de términos
            response = self.gemini_client.models.generate_content(
                model=self.adk_config.GEMINI_MODEL_LITE,
                contents=expansion_prompt,
                config=GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.3
                )
            )
            
            expansion = json.loads(response.text)
            related_terms = expansion.get('related_terms', [])
            
            logger.info(f"📚 Términos expandidos: {related_terms}")
            
            # Buscar con términos expandidos
            additional_results = []
            for term in related_terms[:5]:
                query_config = {
                    "search_term": term,
                    "domains": intent.get('domain_hints', []),
                    "types": intent.get('type_hints', []),
                    "weight": 0.6  # Menor peso para términos expandidos
                }
                results = self._execute_hybrid_search(query_config)
                additional_results.extend(results)
            
            return additional_results
            
        except Exception as e:
            logger.error(f"Error en búsqueda iterativa: {e}")
            return []


# Singleton del motor
_search_engine = None


def get_search_engine() -> IntelligentSearchEngine:
    """Obtiene instancia singleton del motor de búsqueda."""
    global _search_engine
    if _search_engine is None:
        _search_engine = IntelligentSearchEngine()
    return _search_engine
