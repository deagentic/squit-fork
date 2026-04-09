"""
Configuración del sistema Agentic RAG.
"""

import os
from typing import Optional


class WeaviateConfig:
    """Configuración para conexión con Weaviate."""

    # Configuración de conexión
    WEAVIATE_URL: str = os.getenv("WEAVIATE_URL", "http://localhost:8080")
    WEAVIATE_API_KEY: Optional[str] = os.getenv("WEAVIATE_API_KEY")
    
    # Configuración de Gemini (para embeddings y LLM)
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    
    # Configuración de modelos Gemini
    EMBEDDING_MODEL: str = "gemini-embedding-001"  # Gemini embedding model estable
    LLM_MODEL: str = "gemini-2.5-flash"  # Gemini modelo estable y correcto
    
    # Configuración de vectorización
    VECTOR_DIMENSIONS: int = 768  # Para gemini-embedding-001
    DISTANCE_METRIC: str = "cosine"
    
    # Límites de procesamiento optimizados
    BATCH_SIZE: int = 500
    MAX_OBJECTS_PER_BATCH: int = 2000
    PARALLEL_WORKERS: int = 8
    
    # Configuración de búsqueda
    DEFAULT_SEARCH_LIMIT: int = 10
    MAX_SEARCH_LIMIT: int = 100
    HYBRID_SEARCH_ALPHA: float = 0.7  # Balance vector vs keyword


class AgentConfig:
    """Configuración para agentes del sistema."""
    
    # Configuración de agentes
    MAX_ITERATIONS: int = 5
    TEMPERATURE: float = 0.1  # Baja para consistencia
    MAX_TOKENS: int = 4000
    
    # Timeouts
    AGENT_TIMEOUT: int = 30  # segundos
    TOOL_TIMEOUT: int = 10   # segundos
    
    # Configuración de memoria
    MEMORY_WINDOW: int = 10  # Últimas 10 interacciones
    CONTEXT_LENGTH: int = 8000  # Tokens de contexto
    
    # Prompts del sistema
    MASTER_AGENT_PROMPT: str = """
    Eres un experto en análisis de código SQL legacy. Tu trabajo es coordinar
    agentes especializados para analizar un codebase de 3.4M objetos SQL.
    
    Tienes acceso a estos agentes especializados:
    - CodeSearchAgent: Búsqueda semántica y por patrones
    - DependencyAnalysisAgent: Análisis de dependencias y referencias
    - PatternAnalysisAgent: Identificación de patrones de código
    - SchemaAnalysisAgent: Análisis de estructura de base de datos
    
    Para cada consulta:
    1. Analiza qué tipo de información se necesita
    2. Decide qué agentes usar y en qué orden
    3. Coordina la recolección de información
    4. Sintetiza una respuesta coherente y útil
    
    Mantén respuestas concisas pero completas. Siempre cita fuentes específicas.
    """
    
    CODE_SEARCH_AGENT_PROMPT: str = """
    Eres un especialista en búsqueda de código SQL. Tu trabajo es encontrar
    objetos de código relevantes usando búsqueda vectorial y por patrones.
    
    Capacidades:
    - Búsqueda semántica por funcionalidad
    - Búsqueda por nombres y patrones
    - Identificación de código similar
    - Filtrado por tipo de objeto, servidor, base de datos
    
    Siempre proporciona contexto sobre por qué los resultados son relevantes.
    """
    
    DEPENDENCY_AGENT_PROMPT: str = """
    Eres un experto en análisis de dependencias de código SQL. Tu trabajo es
    mapear las relaciones entre objetos de código.
    
    Capacidades:
    - Identificar referencias directas (FK, views, stored procedures)
    - Mapear dependencias indirectas a través de flujo de datos
    - Análizar impacto de cambios potenciales
    - Detectar dependencias circulares
    
    Proporciona análisis detallado de las implicaciones de las dependencias.
    """


class IngestionConfig:
    """Configuración para el pipeline de ingesta."""
    
    # Configuración de procesamiento
    CHUNK_SIZE: int = 1000  # Objetos por chunk
    PARALLEL_WORKERS: int = 4
    
    # Configuración de embeddings
    CODE_EMBEDDING_STRATEGY: str = "semantic"  # semantic, syntactic, hybrid
    INCLUDE_COMMENTS: bool = True
    INCLUDE_METADATA: bool = True
    
    # Filtros de calidad
    MIN_CODE_LENGTH: int = 10  # Caracteres mínimos
    MAX_CODE_LENGTH: int = 100000  # Caracteres máximos
    EXCLUDE_EMPTY_OBJECTS: bool = True
    
    # Configuración de retry
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 5  # segundos
    
    # Logging
    LOG_PROGRESS_EVERY: int = 100  # objetos
    LOG_LEVEL: str = "INFO"


class SearchConfig:
    """Configuración para búsquedas y análisis."""
    
    # Configuración de búsqueda híbrida
    VECTOR_WEIGHT: float = 0.7
    KEYWORD_WEIGHT: float = 0.3
    
    # Configuración de clustering
    SIMILARITY_THRESHOLD: float = 0.8
    MIN_CLUSTER_SIZE: int = 3
    
    # Configuración de análisis de dependencias
    MAX_DEPENDENCY_DEPTH: int = 5
    INCLUDE_TRANSITIVE_DEPS: bool = True
    
    # Configuración de patrones
    PATTERN_CONFIDENCE_THRESHOLD: float = 0.75
    MIN_PATTERN_OCCURRENCES: int = 5
