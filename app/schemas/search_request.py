"""
Modelos Pydantic para validación de requests y responses.

Valida inputs del usuario y estructura de responses para garantizar
consistencia y prevenir errores.

Uso:
    from schemas.search_request import SearchRequest
    
    # Validar request
    request = SearchRequest(**raw_data)
    
    # request.query es válido y sanitizado
    results = search(request.query, request.limit)
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum


class BusinessDomain(str, Enum):
    """Dominios de negocio válidos."""
    VENTAS = "ventas"
    INVENTARIO = "inventario"
    FINANZAS = "finanzas"
    PRODUCCION = "produccion"
    LOGISTICA = "logistica"
    RECURSOS_HUMANOS = "recursos_humanos"
    COMPRAS = "compras"
    GENERAL = "general"


class ObjectType(str, Enum):
    """Tipos de objetos SQL válidos."""
    PROCEDURE = "PROCEDURE"
    FUNCTION = "FUNCTION"
    VIEW = "VIEW"
    TABLE = "TABLE"
    TRIGGER = "TRIGGER"
    INDEX = "INDEX"


class SemanticType(str, Enum):
    """Tipos semánticos de código."""
    COMPLEX_QUERY = "complex_query"
    STORED_PROCEDURE = "stored_procedure"
    FUNCTION = "function"
    VIEW = "view"
    TRIGGER = "trigger"
    DDL = "ddl"
    DML = "dml"
    SIMPLE_SQL = "simple_sql"


class SearchRequest(BaseModel):
    """
    Modelo para validar requests de búsqueda semántica.
    
    Valida parámetros de búsqueda y aplica límites razonables.
    
    Example:
        request = SearchRequest(
            query="inventario de productos",
            limit=10,
            business_domains=["inventario", "ventas"],
            use_hybrid=True
        )
        
        # request.query está validado y sanitizado
        # request.limit está entre 1 y 100
    """
    
    query: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Query de búsqueda en lenguaje natural"
    )
    
    limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Número máximo de resultados"
    )
    
    business_domains: Optional[List[BusinessDomain]] = Field(
        default=None,
        description="Filtrar por dominios de negocio"
    )
    
    object_types: Optional[List[ObjectType]] = Field(
        default=None,
        description="Filtrar por tipos de objeto"
    )
    
    semantic_types: Optional[List[SemanticType]] = Field(
        default=None,
        description="Filtrar por tipos semánticos"
    )
    
    min_complexity: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Complejidad mínima"
    )
    
    max_complexity: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Complejidad máxima"
    )
    
    use_hybrid: bool = Field(
        default=True,
        description="Usar búsqueda híbrida (70% vector + 30% keywords)"
    )
    
    @field_validator('query')
    @classmethod
    def query_not_empty(cls, v):
        """Valida que query no esté vacío."""
        if not v or not v.strip():
            raise ValueError("Query no puede estar vacío")
        return v.strip()
    
    @field_validator('business_domains', 'object_types', 'semantic_types')
    @classmethod
    def lists_not_empty(cls, v):
        """Valida que listas no estén vacías si se proporcionan."""
        if v is not None and len(v) == 0:
            raise ValueError("Lista no puede estar vacía")
        return v
    
    @model_validator(mode='after')
    def validate_complexity_range(self):
        """Valida que min_complexity <= max_complexity."""
        if self.min_complexity is not None and self.max_complexity is not None:
            if self.min_complexity > self.max_complexity:
                raise ValueError(
                    f"min_complexity ({self.min_complexity}) debe ser <= max_complexity ({self.max_complexity})"
                )
        return self
    
    class Config:
        """Config de Pydantic."""
        use_enum_values = True


class SearchResult(BaseModel):
    """Modelo para un resultado de búsqueda individual."""
    
    chunk_id: str
    parent_object_id: str
    object_name: str
    object_type: str
    semantic_type: str
    business_domain: str
    semantic_summary: str
    complexity_score: float
    chunk_index: int
    total_chunks: int
    chunk_preview: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    
    class Config:
        """Config de Pydantic."""
        orm_mode = True  # Permite crear desde NamedTuple o Row de BigQuery


class SearchResponse(BaseModel):
    """
    Modelo para response de búsqueda.
    
    Estructura la respuesta con metadatos útiles.
    
    Example:
        response = SearchResponse(
            query="inventario",
            results=[...],
            total_results=42,
            latency_ms=125.3
        )
    """
    
    query: str
    results: List[SearchResult]
    total_results: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)
    latency_ms: float = Field(ge=0.0, description="Latencia en milisegundos")
    
    used_hybrid_search: bool = Field(default=True)
    filters_applied: Dict[str, Any] = Field(default_factory=dict)
    
    @model_validator(mode='after')
    def results_within_limit(self):
        """Valida que results no exceda limit."""
        if len(self.results) > self.limit:
            raise ValueError(f"Results count ({len(self.results)}) excede limit ({self.limit})")
        return self


class ChunkRequest(BaseModel):
    """Modelo para request de chunking."""
    
    sql_code: str = Field(..., min_length=10)
    object_name: str = Field(..., min_length=1, max_length=200)
    object_type: ObjectType
    
    max_chunk_size: int = Field(default=8000, ge=500, le=50000)
    overlap_size: int = Field(default=200, ge=0, le=5000)
    
    @model_validator(mode='after')
    def overlap_less_than_chunk(self):
        """Valida que overlap < max_chunk_size."""
        if self.overlap_size >= self.max_chunk_size:
            raise ValueError(
                f"overlap_size ({self.overlap_size}) debe ser < max_chunk_size ({self.max_chunk_size})"
            )
        return self


class AgentRequest(BaseModel):
    """Modelo para request del agente conversacional."""
    
    query: str = Field(..., min_length=1, max_length=1000)
    session_id: Optional[str] = None
    user_id: Optional[str] = "default_user"
    
    max_tokens: int = Field(default=8000, ge=100, le=10000)
    temperature: float = Field(default=0.1, ge=0.0, le=1.0)
    
    include_memory: bool = Field(default=True)
    max_memory_turns: int = Field(default=10, ge=1, le=50)
    
    @field_validator('query')
    @classmethod
    def sanitize_query(cls, v):
        """Sanitiza query removiendo caracteres peligrosos."""
        # Remover caracteres de control
        sanitized = ''.join(char for char in v if char.isprintable() or char == '\n')
        return sanitized.strip()


class AgentResponse(BaseModel):
    """Modelo para response del agente."""
    
    query: str
    response: str
    session_id: str
    turn_number: int = Field(ge=1)
    
    latency_ms: float = Field(ge=0.0)
    tokens_used: int = Field(ge=0)
    
    tools_called: List[str] = Field(default_factory=list)
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConfigValidation(BaseModel):
    """Modelo para validar configuración del sistema."""
    
    project_id: str = Field(..., min_length=1)
    dataset_id: str = Field(..., min_length=1)
    gemini_api_key: str = Field(..., min_length=20)
    gemini_model: str = Field(default="gemini-2.5-flash")
    
    embedding_dimensions: int = Field(default=768, ge=128, le=2048)
    max_search_limit: int = Field(default=100, ge=1, le=1000)
    rate_limit_calls: int = Field(default=60, ge=1, le=1000)
    
    @field_validator('project_id', 'dataset_id')
    @classmethod
    def no_special_chars(cls, v):
        """Valida que no contengan caracteres especiales peligrosos."""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError(f"ID contiene caracteres inválidos: {v}")
        return v
    
    @field_validator('gemini_api_key')
    @classmethod
    def valid_api_key_format(cls, v):
        """Valida formato básico de API key."""
        if not v.startswith('AI'):  # Gemini keys empiezan con AI
            raise ValueError("API key parece inválido (debe empezar con 'AI')")
        return v


class HealthCheckResponse(BaseModel):
    """Modelo para response de health check."""
    
    status: str = Field(..., pattern="^(healthy|degraded|unhealthy)$")
    timestamp: str
    version: str = "2.0.0"
    
    components: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    uptime_seconds: float = Field(ge=0.0)
    
    class Config:
        """Config de Pydantic."""
        schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2025-01-14T12:00:00Z",
                "version": "2.0.0",
                "components": {
                    "bigquery": {"status": "healthy", "latency_ms": 50},
                    "gemini": {"status": "healthy"},
                },
                "uptime_seconds": 3600.0
            }
        }

