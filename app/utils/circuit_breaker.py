"""
Circuit Breaker pattern para proteger contra fallos en cascada.

El Circuit Breaker actúa como un interruptor automático que abre el circuito
cuando detecta demasiados fallos, evitando llamadas a servicios degradados.

Estados:
- CLOSED: Normal, llamadas permitidas
- OPEN: Fallando, llamadas bloqueadas
- HALF_OPEN: Probando recuperación

Uso:
    from utils.circuit_breaker import CircuitBreaker
    
    breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
    
    result = breaker.call(api_function, arg1, arg2)
"""

from enum import Enum
from typing import Callable, Any, Type
import time
import threading
import logging

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Estados del circuit breaker."""
    CLOSED = "closed"        # Normal, llamadas permitidas
    OPEN = "open"           # Fallando, llamadas bloqueadas
    HALF_OPEN = "half_open" # Probando si servicio se recuperó


class CircuitBreakerError(Exception):
    """Excepción lanzada cuando circuit breaker está abierto."""
    pass


class CircuitBreaker:
    """
    Circuit breaker para proteger contra fallos en cascada.
    
    Si una operación falla repetidamente (≥ failure_threshold), el circuit
    se "abre" y bloquea llamadas por recovery_timeout segundos, evitando
    saturar un servicio degradado.
    
    Después del timeout, entra en estado HALF_OPEN para probar una llamada.
    Si tiene éxito, cierra el circuit. Si falla, lo vuelve a abrir.
    
    Thread-safe.
    
    Example:
        breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60.0,
            expected_exception=ConnectionError
        )
        
        try:
            result = breaker.call(api.get_data, param1)
        except CircuitBreakerError:
            # Circuit está abierto, usar fallback
            result = get_cached_data()
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception,
        success_threshold: int = 2
    ):
        """
        Inicializa el circuit breaker.
        
        Args:
            failure_threshold: Número de fallos antes de abrir circuit
            recovery_timeout: Segundos antes de probar recovery
            expected_exception: Tipo de excepción que cuenta como fallo
            success_threshold: Éxitos en HALF_OPEN antes de cerrar
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.success_threshold = success_threshold
        
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        self.lock = threading.Lock()
        
        logger.info(
            f"CircuitBreaker inicializado: threshold={failure_threshold}, "
            f"timeout={recovery_timeout}s",
            extra={
                'failure_threshold': failure_threshold,
                'recovery_timeout': recovery_timeout
            }
        )
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Ejecuta función a través del circuit breaker.
        
        Args:
            func: Función a ejecutar
            *args: Argumentos posicionales
            **kwargs: Argumentos con nombre
            
        Returns:
            Resultado de la función
            
        Raises:
            CircuitBreakerError: Si circuit está abierto
            Exception: Cualquier excepción de la función
        """
        with self.lock:
            if self.state == CircuitState.OPEN:
                # Verificar si es tiempo de probar recovery
                if time.time() - self.last_failure_time >= self.recovery_timeout:
                    logger.info("Circuit breaker: Intentando recovery (HALF_OPEN)")
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                else:
                    # Circuit aún está abierto
                    time_remaining = self.recovery_timeout - (time.time() - self.last_failure_time)
                    logger.warning(
                        f"Circuit breaker OPEN: {time_remaining:.0f}s restantes",
                        extra={'time_remaining': time_remaining}
                    )
                    raise CircuitBreakerError(
                        f"Circuit breaker is OPEN. Retry in {time_remaining:.0f}s"
                    )
        
        # Intentar llamada
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
            
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        """Maneja éxito de llamada."""
        with self.lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                logger.debug(
                    f"Circuit HALF_OPEN: éxito {self.success_count}/{self.success_threshold}"
                )
                
                # Si alcanzamos threshold de éxitos, cerrar circuit
                if self.success_count >= self.success_threshold:
                    logger.info("Circuit breaker: Recovery exitoso, cerrando circuit")
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
                    
            elif self.state == CircuitState.CLOSED:
                # Reset failure count en estado normal
                self.failure_count = 0
    
    def _on_failure(self):
        """Maneja fallo de llamada."""
        with self.lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            logger.warning(
                f"Circuit breaker: fallo {self.failure_count}/{self.failure_threshold}",
                extra={'failure_count': self.failure_count}
            )
            
            # Si estamos en HALF_OPEN y falla, volver a abrir
            if self.state == CircuitState.HALF_OPEN:
                logger.warning("Circuit breaker: Recovery falló, reabriendo circuit")
                self.state = CircuitState.OPEN
                self.failure_count = 0
                self.success_count = 0
                
            # Si alcanzamos threshold de fallos, abrir circuit
            elif self.failure_count >= self.failure_threshold:
                logger.error(
                    f"Circuit breaker: Threshold alcanzado ({self.failure_threshold}), "
                    f"abriendo circuit por {self.recovery_timeout}s"
                )
                self.state = CircuitState.OPEN
    
    def get_state(self) -> CircuitState:
        """Obtiene estado actual del circuit."""
        with self.lock:
            return self.state
    
    def get_stats(self) -> dict:
        """
        Obtiene estadísticas del circuit breaker.
        
        Returns:
            Dict con state, failure_count, success_count, etc.
        """
        with self.lock:
            stats = {
                'state': self.state.value,
                'failure_count': self.failure_count,
                'success_count': self.success_count,
                'failure_threshold': self.failure_threshold,
                'success_threshold': self.success_threshold,
                'recovery_timeout': self.recovery_timeout
            }
            
            if self.last_failure_time and self.state == CircuitState.OPEN:
                time_remaining = max(
                    0,
                    self.recovery_timeout - (time.time() - self.last_failure_time)
                )
                stats['time_until_retry'] = time_remaining
            
            return stats
    
    def reset(self):
        """Resetea circuit breaker a estado CLOSED."""
        with self.lock:
            old_state = self.state
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.last_failure_time = None
            
            logger.info(
                f"Circuit breaker reseteado: {old_state.value} → CLOSED",
                extra={'old_state': old_state.value}
            )


class CircuitBreakerDecorator:
    """
    Decorator para aplicar circuit breaker a funciones.
    
    Example:
        breaker = CircuitBreakerDecorator(
            failure_threshold=5,
            recovery_timeout=60
        )
        
        @breaker.decorator
        def call_api():
            return api.get_data()
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception
    ):
        self.breaker = CircuitBreaker(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=expected_exception
        )
    
    def decorator(self, func: Callable) -> Callable:
        """Aplica circuit breaker a la función."""
        def wrapper(*args, **kwargs):
            return self.breaker.call(func, *args, **kwargs)
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper


# Circuit breakers predefinidos para servicios comunes
GEMINI_CIRCUIT_BREAKER = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=30.0
)

BIGQUERY_CIRCUIT_BREAKER = CircuitBreaker(
    failure_threshold=3,
    recovery_timeout=60.0
)

EXTERNAL_API_CIRCUIT_BREAKER = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60.0
)

