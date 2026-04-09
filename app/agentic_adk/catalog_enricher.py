"""
Enriquecedor de contexto usando catálogo de aplicaciones.

Este módulo carga el catálogo de aplicaciones y lo usa para enriquecer
las búsquedas, mapeando términos de negocio a sistemas y código SQL relevante.
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path
import pandas as pd

logger = logging.getLogger(__name__)


class CatalogEnricher:
    """
    Enriquece búsquedas usando catálogo de aplicaciones.
    
    El catálogo contiene metadata de 280+ aplicaciones del negocio:
    - Nombres de sistemas
    - Descripciones de funcionalidad
    - Procesos end-to-end
    - Tecnologías
    
    Esto permite mapear términos de negocio (ej: "matriz de abasto")
    a sistemas específicos y código SQL relevante.
    """
    
    def __init__(self, catalog_path: Optional[Path] = None):
        """
        Inicializa el enriquecedor.
        
        Args:
            catalog_path: Path al archivo catalogo.csv o catalog.csv
        """
        if catalog_path is None:
            # Usar catálogo desde root data/ SOLAMENTE
            # __file__ = app/agentic_adk/catalog_enricher.py
            # .parent = app/agentic_adk/
            # .parent.parent = app/
            # .parent.parent.parent = root/
            root_data_path = Path(__file__).parent.parent.parent / "data"
            
            candidates = [
                # Prioridad 1: catálogo en root data/
                root_data_path / "catalogo.csv",
                root_data_path / "catalog.csv",
                # Prioridad 2: ejemplo
                root_data_path / "catalog.example.csv"
            ]
            
            for candidate in candidates:
                if candidate.exists():
                    catalog_path = candidate
                    break
            else:
                # Fallback: usar catalogo.csv en root data/ aunque no exista
                catalog_path = root_data_path / "catalogo.csv"
        
        self.catalog_path = catalog_path
        self.catalog_df = None
        self._load_catalog()
    
    def _load_catalog(self):
        """Carga el catálogo desde CSV."""
        try:
            if not self.catalog_path.exists():
                logger.warning(f"⚠️  Catálogo no encontrado: {self.catalog_path}")
                self.catalog_df = pd.DataFrame()
                return
            
            # Leer con encoding latin1 (contiene caracteres especiales)
            self.catalog_df = pd.read_csv(self.catalog_path, encoding='latin1')
            logger.info(f"✅ Catálogo cargado: {len(self.catalog_df)} aplicaciones desde {self.catalog_path.name}")
        except Exception as e:
            logger.error(f"❌ Error cargando catálogo desde {self.catalog_path}: {e}")
            self.catalog_df = pd.DataFrame()
    
    def enrich_query(self, user_query: str) -> Dict[str, Any]:
        """
        Enriquece una query del usuario usando el catálogo.
        
        Args:
            user_query: Query original del usuario
            
        Returns:
            {
                "original_query": str,
                "enriched_keywords": [str],
                "related_systems": [str],
                "related_processes": [str],
                "search_hints": [str]
            }
        """
        if self.catalog_df is None or len(self.catalog_df) == 0:
            return {
                "original_query": user_query,
                "enriched_keywords": [user_query],
                "related_systems": [],
                "related_processes": [],
                "search_hints": [],
                "catalog_matches": 0
            }
        
        query_lower = user_query.lower()
        
        # Buscar coincidencias en el catálogo
        matches = []
        
        # Detectar columnas disponibles (backward compatibility)
        has_old_format = 'Name' in self.catalog_df.columns
        name_col = 'Name' if has_old_format else 'application_name'
        desc_col = 'Descripcion' if has_old_format else 'description'
        system_col = 'Sistema Objeto' if has_old_format else 'database_name'
        domain_col = 'Proceso End To End' if has_old_format else 'business_domain'
        
        for idx, row in self.catalog_df.iterrows():
            score = 0
            
            # Match en nombre de aplicación (peso alto)
            if pd.notna(row.get(name_col)):
                if query_lower in str(row[name_col]).lower():
                    score += 3
            
            # Match en descripción (buscar palabras del query)
            if pd.notna(row.get(desc_col)):
                desc = str(row[desc_col]).lower()
                query_words = [w for w in query_lower.split() if len(w) > 3]
                for word in query_words:
                    if word in desc:
                        score += 1
            
            # Match en sistema/database
            if pd.notna(row.get(system_col)):
                if query_lower in str(row[system_col]).lower():
                    score += 2
            
            # Match en dominio/proceso
            if pd.notna(row.get(domain_col)):
                if query_lower in str(row[domain_col]).lower():
                    score += 1
            
            if score > 0:
                matches.append({
                    'app_name': row[name_col],
                    'system': row.get(system_col, 'N/A'),
                    'description': row.get(desc_col, ''),
                    'domain': row.get(domain_col, ''),
                    'score': score
                })
        
        # Ordenar por score
        matches = sorted(matches, key=lambda x: x['score'], reverse=True)[:5]
        
        # Extraer keywords enriquecidas
        enriched_keywords = [user_query]
        related_systems = []
        related_domains = []
        search_hints = []
        
        for match in matches:
            # Agregar nombre del sistema/database como keyword
            if pd.notna(match.get('system')) and match['system'] != 'N/A':
                system_code = str(match['system']).split('-')[0].strip()
                if system_code and system_code not in enriched_keywords:
                    enriched_keywords.append(system_code)
                    related_systems.append(match['system'])
            
            # Agregar dominio de negocio
            if pd.notna(match.get('domain')) and match['domain'] not in related_domains:
                related_domains.append(match['domain'])
            
            # Generar hint de búsqueda
            if match['score'] >= 2:
                search_hints.append(f"Sistema {match['app_name']}: {str(match['description'])[:100]}")
        
        logger.info(f"Enriquecimiento: '{user_query}' → {len(matches)} matches, {len(enriched_keywords)} keywords")
        
        return {
            "original_query": user_query,
            "enriched_keywords": enriched_keywords,
            "related_systems": related_systems,
            "related_domains": related_domains,
            "search_hints": search_hints,
            "catalog_matches": len(matches)
        }
    
    def get_context_for_term(self, term: str) -> Optional[str]:
        """
        Obtiene contexto de negocio para un término.
        
        Args:
            term: Término a buscar (ej: "matriz de abasto")
            
        Returns:
            Contexto textual o None
        """
        enrichment = self.enrich_query(term)
        
        if enrichment['catalog_matches'] > 0:
            context_parts = []
            
            if enrichment['related_systems']:
                context_parts.append(f"Sistemas relacionados: {', '.join(enrichment['related_systems'][:3])}")
            
            if enrichment['search_hints']:
                context_parts.append(f"Contexto: {enrichment['search_hints'][0]}")
            
            return " | ".join(context_parts)
        
        return None


# Singleton
_enricher = None


def get_catalog_enricher() -> CatalogEnricher:
    """Obtiene instancia singleton del enriquecedor."""
    global _enricher
    if _enricher is None:
        _enricher = CatalogEnricher()
    return _enricher
