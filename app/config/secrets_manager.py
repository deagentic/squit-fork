"""
Gestión segura de secretos con Google Secret Manager.

Proporciona acceso centralizado a secretos con cache, fallback a variables
de ambiente y rotación automática.

Uso:
    from config.secrets_manager import get_secrets_manager
    
    secrets = get_secrets_manager()
    api_key = secrets.get_api_key()
    db_creds = secrets.get_database_credentials()
"""

from typing import Optional, Dict, Any, List
import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Intentar importar Secret Manager (opcional)
try:
    from google.cloud import secretmanager
    SECRET_MANAGER_AVAILABLE = True
except ImportError:
    SECRET_MANAGER_AVAILABLE = False
    logger.warning("google-cloud-secret-manager no disponible. Usando variables de ambiente.")


class SecretsManager:
    """
    Gestiona secretos desde Google Secret Manager con fallback a env vars.
    
    Ventajas:
    - Rotación automática de secretos
    - Auditoría de accesos
    - Encriptación en reposo
    - Versionado de secretos
    - Cache local para performance
    
    Example:
        secrets = SecretsManager(project_id="dfor-prj-dev")
        
        api_key = secrets.get_secret("GEMINI_API_KEY")
        # Intenta Secret Manager, fallback a os.getenv
    """
    
    def __init__(
        self,
        project_id: str,
        use_cache: bool = True,
        cache_ttl_minutes: int = 5
    ):
        """
        Inicializa el secrets manager.
        
        Args:
            project_id: ID del proyecto GCP
            use_cache: Si True, cachea secrets en memoria
            cache_ttl_minutes: TTL del cache en minutos
        """
        self.project_id = project_id
        self.use_cache = use_cache
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)
        
        # Cache de secrets con timestamp
        self._cache: Dict[str, tuple[str, datetime]] = {}
        
        # Inicializar cliente si disponible
        if SECRET_MANAGER_AVAILABLE:
            try:
                self.client = secretmanager.SecretManagerServiceClient()
                logger.info("✅ Secret Manager client inicializado")
            except Exception as e:
                logger.warning(f"No se pudo inicializar Secret Manager: {e}")
                self.client = None
        else:
            self.client = None
    
    def get_secret(
        self,
        secret_id: str,
        version: str = "latest",
        default: Optional[str] = None
    ) -> str:
        """
        Obtiene secret desde Secret Manager o variable de ambiente.
        
        Intenta primero Secret Manager, luego variables de ambiente.
        
        Args:
            secret_id: ID del secret
            version: Versión del secret (default: latest)
            default: Valor por defecto si no se encuentra
            
        Returns:
            Valor del secret
            
        Example:
            api_key = secrets.get_secret("GEMINI_API_KEY")
            # Intenta Secret Manager, luego os.getenv("GEMINI_API_KEY")
        """
        # Verificar cache primero
        if self.use_cache:
            cached_value = self._get_from_cache(secret_id)
            if cached_value is not None:
                return cached_value
        
        # Intentar Secret Manager
        if self.client:
            try:
                value = self._get_from_secret_manager(secret_id, version)
                
                if value:
                    # Guardar en cache
                    if self.use_cache:
                        self._cache[secret_id] = (value, datetime.now())
                    
                    return value
                    
            except Exception as e:
                logger.warning(
                    f"Error obteniendo secret '{secret_id}' de Secret Manager: {e}"
                )
        
        # Fallback a variable de ambiente
        env_value = os.getenv(secret_id)
        if env_value:
            logger.debug(f"Secret '{secret_id}' obtenido de variable de ambiente")
            return env_value
        
        # Si no se encontró y hay default, usarlo
        if default is not None:
            logger.warning(
                f"Secret '{secret_id}' no encontrado, usando valor por defecto"
            )
            return default
        
        # Si llegamos aquí, el secret no se encontró
        raise ValueError(
            f"Secret '{secret_id}' no encontrado en Secret Manager ni "
            f"en variables de ambiente"
        )
    
    def _get_from_secret_manager(self, secret_id: str, version: str) -> Optional[str]:
        """Obtiene secret desde Google Secret Manager."""
        if not self.client:
            return None
        
        name = f"projects/{self.project_id}/secrets/{secret_id}/versions/{version}"
        
        try:
            response = self.client.access_secret_version(request={"name": name})
            secret_value = response.payload.data.decode("UTF-8")
            
            logger.debug(f"Secret '{secret_id}' obtenido de Secret Manager")
            return secret_value
            
        except Exception as e:
            logger.debug(f"Secret '{secret_id}' no encontrado en Secret Manager: {e}")
            return None
    
    def _get_from_cache(self, secret_id: str) -> Optional[str]:
        """Obtiene secret del cache si no ha expirado."""
        if secret_id not in self._cache:
            return None
        
        value, timestamp = self._cache[secret_id]
        age = datetime.now() - timestamp
        
        if age <= self.cache_ttl:
            logger.debug(f"Secret '{secret_id}' obtenido del cache")
            return value
        
        # Cache expirado, remover
        del self._cache[secret_id]
        return None
    
    def clear_cache(self):
        """Limpia el cache de secrets."""
        self._cache.clear()
        logger.info("Cache de secrets limpiado")
    
    # Helper methods para secrets comunes
    
    def get_api_key(self) -> str:
        """Obtiene Gemini API key."""
        return self.get_secret("GEMINI_API_KEY")
    
    def get_database_credentials(self) -> Dict[str, str]:
        """Obtiene credenciales de base de datos."""
        return {
            "project": self.get_secret(
                "GOOGLE_CLOUD_PROJECT",
                default=self.project_id
            ),
            "dataset": os.getenv("BIGQUERY_DATASET", "deacero_sql_objects")
        }
    
    def get_service_account_path(self) -> str:
        """Obtiene path del service account."""
        return self.get_secret(
            "GOOGLE_APPLICATION_CREDENTIALS",
            default=".config/credentials.json"
        )
    
    def list_secrets(self) -> List[str]:
        """
        Lista todos los secrets disponibles.
        
        Returns:
            Lista de secret IDs
        """
        if not self.client:
            logger.warning("Secret Manager no disponible")
            return []
        
        try:
            parent = f"projects/{self.project_id}"
            secrets = self.client.list_secrets(request={"parent": parent})
            
            secret_ids = [
                secret.name.split('/')[-1]
                for secret in secrets
            ]
            
            return secret_ids
            
        except Exception as e:
            logger.error(f"Error listando secrets: {e}")
            return []


# Singleton global
_global_secrets_manager: Optional[SecretsManager] = None


def get_secrets_manager(project_id: str = None) -> SecretsManager:
    """
    Obtiene el secrets manager global (singleton).
    
    Args:
        project_id: ID del proyecto (usa GOOGLE_CLOUD_PROJECT si None)
        
    Returns:
        SecretsManager singleton
        
    Example:
        from config.secrets_manager import get_secrets_manager
        
        secrets = get_secrets_manager()
        api_key = secrets.get_api_key()
    """
    global _global_secrets_manager
    
    if _global_secrets_manager is None:
        project = project_id or os.getenv("GOOGLE_CLOUD_PROJECT", "dfor-prj-dev")
        _global_secrets_manager = SecretsManager(project_id=project)
    
    return _global_secrets_manager


def setup_secrets_from_manager():
    """
    Setup inicial: carga secrets de Secret Manager a variables de ambiente.
    
    Útil para compatibilidad con código que espera variables de ambiente.
    
    Example:
        # Al inicio de la aplicación
        from config.secrets_manager import setup_secrets_from_manager
        
        setup_secrets_from_manager()
        
        # Ahora os.getenv("GEMINI_API_KEY") tiene el valor de Secret Manager
    """
    secrets = get_secrets_manager()
    
    # Secrets a cargar
    secret_mappings = {
        "GEMINI_API_KEY": "GEMINI_API_KEY",
        "GOOGLE_CLOUD_PROJECT": "GOOGLE_CLOUD_PROJECT",
        "GOOGLE_APPLICATION_CREDENTIALS": "GOOGLE_APPLICATION_CREDENTIALS",
    }
    
    for secret_id, env_var in secret_mappings.items():
        try:
            value = secrets.get_secret(secret_id)
            os.environ[env_var] = value
            logger.debug(f"✅ Secret '{secret_id}' cargado a env var '{env_var}'")
        except Exception as e:
            logger.warning(f"⚠️ No se pudo cargar secret '{secret_id}': {e}")
    
    logger.info("Secrets cargados desde Secret Manager")

