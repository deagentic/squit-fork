"""
Configuración para el sistema Agentic ADK.
"""

import os
from typing import Optional


class AgenticADKConfig:
    """Configuración del sistema de agentes ADK."""
    
    # Gemini API
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_CHAT_MODEL", "gemini-2.5-flash")  # Respuesta final
    GEMINI_MODEL_LITE: str = "gemini-2.5-flash-lite"  # Tareas intermedias (router, contexto)
    
    # BigQuery Vector System
    PROJECT_ID: str = os.getenv("GOOGLE_CLOUD_PROJECT", "dfor-prj-dev")
    DATASET_ID: str = "deacero_sql_objects"
    EMBEDDINGS_TABLE: str = "chunk_embeddings"
    EMBEDDING_MODEL_NAME: str = "gemini_embedding_model"  # Nombre del modelo en BigQuery
    
    # Configuración de agentes
    TEMPERATURE: float = 0.1  # Baja para respuestas deterministas
    MAX_TOKENS: int = 8000
    TOP_P: float = 0.95
    
    # Límites y performance
    DEFAULT_SEARCH_LIMIT: int = 10
    MAX_SEARCH_LIMIT: int = 50
    VECTOR_SEARCH_TIMEOUT: int = 30  # segundos
    
    @property
    def full_embeddings_table_id(self) -> str:
        """ID completo de la tabla de embeddings."""
        return f"{self.PROJECT_ID}.{self.DATASET_ID}.{self.EMBEDDINGS_TABLE}"
    
    @property
    def full_embedding_model_id(self) -> str:
        """ID completo del modelo de embeddings."""
        return f"{self.PROJECT_ID}.{self.DATASET_ID}.{self.EMBEDDING_MODEL_NAME}"
    
    def validate(self) -> bool:
        """
        Valida que la configuración esté completa.
        
        Returns:
            True si la configuración es válida.
            
        Raises:
            ValueError: Si falta configuración crítica.
        """
        if not self.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY no configurado. "
                "Configura en .env o variable de ambiente."
            )
        
        if not self.PROJECT_ID:
            raise ValueError("GOOGLE_CLOUD_PROJECT no configurado")
        
        return True
