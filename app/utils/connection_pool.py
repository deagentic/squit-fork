"""
Connection pooling para BigQuery.

Reutiliza conexiones de BigQuery para mejorar performance y reducir overhead.

Uso:
    from utils.connection_pool import BigQueryConnectionPool
    
    pool = BigQueryConnectionPool()
    client = pool.get_client()  # Reutiliza conexión existente
"""

from google.cloud import bigquery
from typing import Optional
import threading
import logging

logger = logging.getLogger(__name__)


class BigQueryConnectionPool:
    """
    Pool de conexiones a BigQuery (singleton).
    
    Reutiliza una única conexión BigQuery thread-safe en lugar de crear
    múltiples instancias, reduciendo overhead y mejorando performance.
    
    BigQuery Client es thread-safe, así que una instancia es suficiente.
    
    Example:
        pool = BigQueryConnectionPool()
        client = pool.get_client()
        
        # Usar client normalmente
        results = client.query("SELECT * FROM table").result()
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, project_id: Optional[str] = None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, project_id: Optional[str] = None):
        """
        Inicializa el pool (solo la primera vez).
        
        Args:
            project_id: ID del proyecto GCP (opcional)
        """
        if self._initialized:
            return
        
        self.project_id = project_id
        self._client = None
        self._client_lock = threading.Lock()
        self._initialized = True
        
        logger.info(f"BigQueryConnectionPool inicializado: project={project_id}")
    
    def get_client(self) -> bigquery.Client:
        """
        Obtiene cliente BigQuery reutilizable.
        
        Crea el cliente solo la primera vez que se solicita (lazy initialization).
        
        Returns:
            bigquery.Client thread-safe
        """
        if self._client is None:
            with self._client_lock:
                if self._client is None:
                    logger.debug("Creando nuevo cliente BigQuery")
                    self._client = bigquery.Client(project=self.project_id)
        
        return self._client
    
    def reset(self):
        """
        Resetea el pool, forzando creación de nueva conexión.
        
        Útil si la conexión se corrompe o para testing.
        """
        with self._client_lock:
            old_client = self._client
            self._client = None
            
            if old_client:
                try:
                    old_client.close()
                except Exception as e:
                    logger.warning(f"Error cerrando cliente anterior: {e}")
            
            logger.info("BigQuery connection pool reseteado")


def get_bigquery_client(project_id: Optional[str] = None) -> bigquery.Client:
    """
    Helper function para obtener cliente BigQuery del pool.
    
    Args:
        project_id: ID del proyecto (opcional)
        
    Returns:
        bigquery.Client
        
    Example:
        from utils.connection_pool import get_bigquery_client
        
        client = get_bigquery_client()
        results = client.query("SELECT 1").result()
    """
    pool = BigQueryConnectionPool(project_id=project_id)
    return pool.get_client()

