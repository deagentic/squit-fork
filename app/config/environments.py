"""
Configuración por entorno (development, staging, production).

Proporciona configuraciones específicas para cada entorno,
permitiendo diferentes límites, timeouts y comportamientos.

Uso:
    from config.environments import EnvironmentConfig, Environment
    
    config = EnvironmentConfig.get_config()  # Usa SQUIT_ENV
    # O
    config = EnvironmentConfig.get_config("production")
"""

from typing import Dict, Any
from enum import Enum
import os
import logging

logger = logging.getLogger(__name__)


class Environment(Enum):
    """Entornos disponibles."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class EnvironmentConfig:
    """
    Configuración por entorno.
    
    Proporciona configuraciones específicas para dev/staging/prod,
    permitiendo diferentes comportamientos según el entorno.
    
    Example:
        # Obtener config del entorno actual (desde SQUIT_ENV)
        config = EnvironmentConfig.get_config()
        
        print(config["LOG_LEVEL"])  # DEBUG en dev, WARNING en prod
        print(config["MAX_SEARCH_LIMIT"])  # 10 en dev, 100 en prod
    """
    
    # Configuración base compartida
    BASE_CONFIG = {
        "PROJECT_ID": os.getenv("GOOGLE_CLOUD_PROJECT", "dfor-prj-dev"),
        "DATASET_ID": "deacero_sql_objects",
        "EMBEDDING_MODEL": "gemini-embedding-001",
        "CHAT_MODEL": "gemini-2.5-flash",
        "EMBEDDING_DIMENSIONS": 768,
    }
    
    # Configuraciones específicas por entorno
    ENVIRONMENTS: Dict[Environment, Dict[str, Any]] = {
        Environment.DEVELOPMENT: {
            **BASE_CONFIG,
            "ENV_NAME": "development",
            "LOG_LEVEL": "DEBUG",
            "LOG_FORMAT_JSON": False,  # Formato legible en dev
            "MAX_SEARCH_LIMIT": 10,
            "DEFAULT_SEARCH_LIMIT": 5,
            "ENABLE_CACHING": False,  # Sin cache en dev para testing
            "ENABLE_METRICS": True,
            "EMBEDDING_BATCH_SIZE": 10,  # Pequeño para testing rápido
            "RATE_LIMIT_CALLS": 10,  # Bajo para evitar consumir cuota
            "RETRY_MAX_ATTEMPTS": 2,  # Pocas reintentos en dev
            "CIRCUIT_BREAKER_THRESHOLD": 3,
            "CIRCUIT_BREAKER_TIMEOUT": 30,
            "QUERY_TIMEOUT": 30,  # 30 segundos
            "TEMPERATURE": 0.1,
            "MAX_TOKENS": 4000,
        },
        Environment.STAGING: {
            **BASE_CONFIG,
            "PROJECT_ID": os.getenv("GOOGLE_CLOUD_PROJECT", "dfor-prj-staging"),
            "ENV_NAME": "staging",
            "LOG_LEVEL": "INFO",
            "LOG_FORMAT_JSON": True,  # JSON en staging
            "MAX_SEARCH_LIMIT": 50,
            "DEFAULT_SEARCH_LIMIT": 10,
            "ENABLE_CACHING": True,
            "ENABLE_METRICS": True,
            "EMBEDDING_BATCH_SIZE": 100,
            "RATE_LIMIT_CALLS": 30,  # Moderado en staging
            "RETRY_MAX_ATTEMPTS": 3,
            "CIRCUIT_BREAKER_THRESHOLD": 5,
            "CIRCUIT_BREAKER_TIMEOUT": 45,
            "QUERY_TIMEOUT": 60,  # 1 minuto
            "TEMPERATURE": 0.1,
            "MAX_TOKENS": 6000,
        },
        Environment.PRODUCTION: {
            **BASE_CONFIG,
            "PROJECT_ID": os.getenv("GOOGLE_CLOUD_PROJECT", "dfor-prj-prod"),
            "ENV_NAME": "production",
            "LOG_LEVEL": "WARNING",
            "LOG_FORMAT_JSON": True,  # JSON estructurado en prod
            "MAX_SEARCH_LIMIT": 100,
            "DEFAULT_SEARCH_LIMIT": 10,
            "ENABLE_CACHING": True,
            "ENABLE_METRICS": True,
            "EMBEDDING_BATCH_SIZE": 1000,  # Batch grande en prod
            "RATE_LIMIT_CALLS": 60,  # Máximo en prod
            "RETRY_MAX_ATTEMPTS": 5,  # Más reintentos en prod
            "CIRCUIT_BREAKER_THRESHOLD": 10,
            "CIRCUIT_BREAKER_TIMEOUT": 60,
            "QUERY_TIMEOUT": 120,  # 2 minutos
            "TEMPERATURE": 0.1,
            "MAX_TOKENS": 8000,
        }
    }
    
    @classmethod
    def get_config(cls, env: str = None) -> Dict[str, Any]:
        """
        Obtiene configuración para entorno especificado.
        
        Args:
            env: Nombre del entorno (development/staging/production)
                 Si None, usa variable SQUIT_ENV (default: development)
        
        Returns:
            Dict con configuración del entorno
            
        Example:
            # Usa SQUIT_ENV
            config = EnvironmentConfig.get_config()
            
            # Forzar entorno específico
            config = EnvironmentConfig.get_config("production")
        """
        env_name = env or os.getenv("SQUIT_ENV", "development")
        
        try:
            environment = Environment(env_name)
        except ValueError:
            logger.warning(
                f"Entorno inválido '{env_name}', usando development",
                extra={'requested_env': env_name}
            )
            environment = Environment.DEVELOPMENT
        
        config = cls.ENVIRONMENTS[environment].copy()
        
        logger.info(
            f"Configuración cargada para entorno: {environment.value}",
            extra={'environment': environment.value}
        )
        
        return config
    
    @classmethod
    def get_current_environment(cls) -> Environment:
        """
        Obtiene el entorno actual.
        
        Returns:
            Environment enum value
        """
        env_name = os.getenv("SQUIT_ENV", "development")
        try:
            return Environment(env_name)
        except ValueError:
            return Environment.DEVELOPMENT
    
    @classmethod
    def is_production(cls) -> bool:
        """Verifica si estamos en producción."""
        return cls.get_current_environment() == Environment.PRODUCTION
    
    @classmethod
    def is_development(cls) -> bool:
        """Verifica si estamos en development."""
        return cls.get_current_environment() == Environment.DEVELOPMENT


def get_env_config() -> Dict[str, Any]:
    """
    Helper function para obtener configuración del entorno actual.
    
    Returns:
        Dict con configuración
        
    Example:
        from config.environments import get_env_config
        
        config = get_env_config()
        print(config["LOG_LEVEL"])
    """
    return EnvironmentConfig.get_config()

