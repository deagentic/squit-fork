"""
Utilidades de retry con backoff exponencial.

Este módulo proporciona decorators para reintentar operaciones que pueden fallar
de manera transiente (problemas de red, APIs temporalmente no disponibles, etc.).

Uso:
    from utils.retry import retry_with_backoff
    
    @retry_with_backoff(max_retries=3, exceptions=(ConnectionError,))
    def fetch_data():
        return api.get_data()
"""

from typing import Callable, TypeVar, Tuple, Type
import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Callable[[Exception, int], None] = None
):
    """
    Decorator para retry con exponential backoff.
    
    Reintenta la función decorada hasta max_retries veces con un delay
    que se multiplica exponencialmente tras cada fallo.
    
    Args:
        max_retries: Máximo número de reintentos (default: 3)
        initial_delay: Delay inicial en segundos (default: 1.0)
        backoff_factor: Factor de multiplicación del delay (default: 2.0)
        max_delay: Máximo delay entre reintentos (default: 60.0)
        exceptions: Tupla de excepciones a capturar (default: Exception)
        on_retry: Callback opcional llamado en cada reintento con (error, attempt)
        
    Returns:
        Decorator function
        
    Example:
        @retry_with_backoff(
            max_retries=3,
            exceptions=(ConnectionError, TimeoutError)
        )
        def fetch_data():
            return api.get_data()
        
        # Con callback custom
        def log_retry(error, attempt):
            print(f"Retry {attempt}: {error}")
        
        @retry_with_backoff(max_retries=5, on_retry=log_retry)
        def risky_operation():
            return external_service.call()
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except exceptions as e:
                    last_exception = e
                    
                    # Si es el último intento, lanzar excepción
                    if attempt == max_retries:
                        logger.error(
                            f"{func.__name__} falló después de {max_retries} intentos: {e}",
                            extra={
                                'function': func.__name__,
                                'max_retries': max_retries,
                                'error': str(e),
                                'error_type': type(e).__name__
                            }
                        )
                        raise
                    
                    # Calcular delay para próximo intento
                    current_delay = min(delay, max_delay)
                    
                    # Log del reintento
                    logger.warning(
                        f"{func.__name__} intento {attempt + 1}/{max_retries} falló: {e}. "
                        f"Reintentando en {current_delay:.1f}s...",
                        extra={
                            'function': func.__name__,
                            'attempt': attempt + 1,
                            'max_retries': max_retries,
                            'delay': current_delay,
                            'error': str(e),
                            'error_type': type(e).__name__
                        }
                    )
                    
                    # Callback opcional
                    if on_retry:
                        try:
                            on_retry(e, attempt + 1)
                        except Exception as callback_error:
                            logger.error(f"Error en callback on_retry: {callback_error}")
                    
                    # Esperar antes de reintentar
                    time.sleep(current_delay)
                    
                    # Aumentar delay para próximo intento
                    delay *= backoff_factor
            
            # No debería llegar aquí, pero por seguridad
            raise last_exception
        
        return wrapper
    return decorator


def retry_with_jitter(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
):
    """
    Decorator para retry con exponential backoff y jitter.
    
    Similar a retry_with_backoff pero agrega un componente aleatorio
    al delay para evitar "thundering herd" problem.
    
    Args:
        max_retries: Máximo número de reintentos
        base_delay: Delay base en segundos
        max_delay: Máximo delay entre reintentos
        exceptions: Tupla de excepciones a capturar
        
    Returns:
        Decorator function
    """
    import random
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(
                            f"{func.__name__} falló después de {max_retries} intentos"
                        )
                        raise
                    
                    # Exponential backoff con jitter
                    exponential_delay = base_delay * (2 ** attempt)
                    jitter = random.uniform(0, exponential_delay * 0.1)  # 10% jitter
                    delay = min(exponential_delay + jitter, max_delay)
                    
                    logger.warning(
                        f"{func.__name__} intento {attempt + 1} falló. "
                        f"Reintentando en {delay:.1f}s..."
                    )
                    
                    time.sleep(delay)
            
            raise last_exception
        
        return wrapper
    return decorator


class RetryConfig:
    """
    Configuración reutilizable de retry para diferentes servicios.
    
    Example:
        # Configuración para BigQuery
        bigquery_retry = RetryConfig(
            max_retries=5,
            initial_delay=2.0,
            exceptions=(ServiceUnavailable, TooManyRequests)
        )
        
        @bigquery_retry.decorator
        def query_bigquery():
            return client.query("SELECT * FROM table")
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0,
        max_delay: float = 60.0,
        exceptions: Tuple[Type[Exception], ...] = (Exception,)
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor
        self.max_delay = max_delay
        self.exceptions = exceptions
    
    def decorator(self, func: Callable[..., T]) -> Callable[..., T]:
        """Aplica configuración de retry a la función."""
        return retry_with_backoff(
            max_retries=self.max_retries,
            initial_delay=self.initial_delay,
            backoff_factor=self.backoff_factor,
            max_delay=self.max_delay,
            exceptions=self.exceptions
        )(func)


# Configuraciones predefinidas para servicios comunes
BIGQUERY_RETRY = RetryConfig(
    max_retries=5,
    initial_delay=2.0,
    backoff_factor=2.0,
    max_delay=30.0
)

GEMINI_API_RETRY = RetryConfig(
    max_retries=3,
    initial_delay=1.0,
    backoff_factor=2.0,
    max_delay=10.0
)

NETWORK_RETRY = RetryConfig(
    max_retries=3,
    initial_delay=0.5,
    backoff_factor=2.0,
    max_delay=5.0
)

