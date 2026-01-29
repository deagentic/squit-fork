"""
Rate limiter para controlar tasa de llamadas a APIs externas.

Este módulo implementa un rate limiter usando el algoritmo Token Bucket,
que permite ráfagas controladas mientras mantiene una tasa promedio.

Uso:
    from utils.rate_limiter import RateLimiter
    
    limiter = RateLimiter(max_calls=100, time_window=60)
    
    with limiter:
        api.call()  # Se bloquea si excede límite
"""

import time
from threading import Lock
from collections import deque
from typing import Optional, Callable
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Rate limiter usando algoritmo Token Bucket.
    
    Permite max_calls en time_window segundos. Si se excede el límite,
    bloquea hasta que tokens estén disponibles.
    
    Thread-safe y puede usarse como context manager o manualmente.
    
    Example:
        limiter = RateLimiter(max_calls=100, time_window=60)
        
        # Como context manager
        with limiter:
            api.call()
        
        # O manualmente
        limiter.acquire()
        api.call()
    """
    
    def __init__(
        self,
        max_calls: int,
        time_window: float,
        raise_on_limit: bool = False
    ):
        """
        Inicializa el rate limiter.
        
        Args:
            max_calls: Máximo de llamadas permitidas en time_window
            time_window: Ventana de tiempo en segundos
            raise_on_limit: Si True, lanza RateLimitExceeded en vez de bloquear
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.raise_on_limit = raise_on_limit
        self.calls = deque()
        self.lock = Lock()
        
        logger.debug(
            f"RateLimiter creado: {max_calls} calls/{time_window}s",
            extra={'max_calls': max_calls, 'time_window': time_window}
        )
    
    def __enter__(self):
        """Context manager entry."""
        self.acquire()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        pass
    
    def acquire(self, timeout: Optional[float] = None):
        """
        Adquiere permiso para hacer llamada.
        
        Bloquea si se excedió el límite hasta que tokens estén disponibles,
        o lanza excepción si raise_on_limit=True.
        
        Args:
            timeout: Máximo tiempo de espera en segundos (None = sin límite)
            
        Raises:
            RateLimitExceeded: Si raise_on_limit=True y límite excedido
            TimeoutError: Si timeout se excede
        """
        start_time = time.time()
        
        while True:
            with self.lock:
                now = time.time()
                
                # Remover llamadas antiguas fuera de la ventana
                while self.calls and self.calls[0] < now - self.time_window:
                    self.calls.popleft()
                
                # Si hay espacio, registrar llamada y continuar
                if len(self.calls) < self.max_calls:
                    self.calls.append(now)
                    
                    logger.debug(
                        f"Permiso concedido: {len(self.calls)}/{self.max_calls} calls",
                        extra={'current_calls': len(self.calls), 'max_calls': self.max_calls}
                    )
                    return
                
                # Si raise_on_limit, lanzar excepción
                if self.raise_on_limit:
                    logger.warning("Rate limit excedido, lanzando excepción")
                    raise RateLimitExceeded(
                        f"Rate limit exceeded: {self.max_calls} calls per {self.time_window}s"
                    )
                
                # Calcular tiempo de espera
                oldest_call = self.calls[0]
                wait_time = (oldest_call + self.time_window) - now
            
            # Verificar timeout
            if timeout and (time.time() - start_time) >= timeout:
                logger.error("Rate limiter timeout excedido")
                raise TimeoutError("Rate limiter timeout exceeded")
            
            # Log de espera
            logger.info(
                f"Rate limit alcanzado, esperando {wait_time:.1f}s",
                extra={'wait_time': wait_time, 'current_calls': len(self.calls)}
            )
            
            # Esperar antes de reintentar (máximo 100ms para responsividad)
            time.sleep(min(wait_time, 0.1))
    
    def try_acquire(self) -> bool:
        """
        Intenta adquirir permiso sin bloquear.
        
        Returns:
            True si permiso concedido, False si límite excedido
        """
        with self.lock:
            now = time.time()
            
            # Remover llamadas antiguas
            while self.calls and self.calls[0] < now - self.time_window:
                self.calls.popleft()
            
            # Si hay espacio, registrar y retornar True
            if len(self.calls) < self.max_calls:
                self.calls.append(now)
                return True
            
            return False
    
    def get_current_usage(self) -> dict:
        """
        Obtiene estadísticas de uso actual.
        
        Returns:
            Dict con current_calls, max_calls, percentage
        """
        with self.lock:
            now = time.time()
            
            # Limpiar llamadas antiguas
            while self.calls and self.calls[0] < now - self.time_window:
                self.calls.popleft()
            
            current = len(self.calls)
            percentage = (current / self.max_calls) * 100 if self.max_calls > 0 else 0
            
            return {
                'current_calls': current,
                'max_calls': self.max_calls,
                'percentage': percentage,
                'time_window': self.time_window
            }
    
    def reset(self):
        """Resetea el rate limiter, limpiando todas las llamadas registradas."""
        with self.lock:
            self.calls.clear()
            logger.info("Rate limiter reseteado")


class AdaptiveRateLimiter(RateLimiter):
    """
    Rate limiter adaptivo que ajusta el límite basado en errores.
    
    Si detecta errores de rate limiting (429, TooManyRequests, etc.),
    reduce el límite temporalmente y lo va aumentando gradualmente.
    
    Example:
        limiter = AdaptiveRateLimiter(max_calls=100, time_window=60)
        
        with limiter:
            try:
                api.call()
            except TooManyRequests:
                limiter.on_rate_limit_error()  # Reduce límite
    """
    
    def __init__(
        self,
        max_calls: int,
        time_window: float,
        min_calls: int = None,
        reduction_factor: float = 0.5,
        recovery_rate: float = 0.1
    ):
        """
        Args:
            max_calls: Máximo de llamadas permitidas
            time_window: Ventana de tiempo en segundos
            min_calls: Mínimo de llamadas (default: max_calls * 0.1)
            reduction_factor: Factor de reducción al detectar error (default: 0.5)
            recovery_rate: Tasa de recuperación por período (default: 0.1)
        """
        super().__init__(max_calls, time_window)
        self.original_max_calls = max_calls
        self.min_calls = min_calls or max(1, int(max_calls * 0.1))
        self.reduction_factor = reduction_factor
        self.recovery_rate = recovery_rate
        self.consecutive_successes = 0
    
    def on_rate_limit_error(self):
        """
        Llamar cuando se detecta error de rate limiting.
        
        Reduce el límite de llamadas.
        """
        with self.lock:
            old_limit = self.max_calls
            self.max_calls = max(
                self.min_calls,
                int(self.max_calls * self.reduction_factor)
            )
            self.consecutive_successes = 0
            
            logger.warning(
                f"Rate limit reducido: {old_limit} → {self.max_calls}",
                extra={'old_limit': old_limit, 'new_limit': self.max_calls}
            )
    
    def on_success(self):
        """
        Llamar tras llamada exitosa.
        
        Gradualmente aumenta el límite si hay múltiples éxitos consecutivos.
        """
        with self.lock:
            self.consecutive_successes += 1
            
            # Cada 10 éxitos, aumentar límite
            if self.consecutive_successes >= 10:
                old_limit = self.max_calls
                self.max_calls = min(
                    self.original_max_calls,
                    int(self.max_calls * (1 + self.recovery_rate))
                )
                self.consecutive_successes = 0
                
                if old_limit != self.max_calls:
                    logger.info(
                        f"Rate limit aumentado: {old_limit} → {self.max_calls}",
                        extra={'old_limit': old_limit, 'new_limit': self.max_calls}
                    )


def rate_limit_decorator(
    max_calls: int,
    time_window: float
):
    """
    Decorator para aplicar rate limiting a funciones.
    
    Args:
        max_calls: Máximo de llamadas
        time_window: Ventana en segundos
        
    Example:
        @rate_limit_decorator(max_calls=60, time_window=60)
        def call_api():
            return api.get_data()
    """
    limiter = RateLimiter(max_calls, time_window)
    
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            with limiter:
                return func(*args, **kwargs)
        return wrapper
    return decorator


class RateLimitExceeded(Exception):
    """Excepción lanzada cuando rate limit es excedido."""
    pass


# Rate limiters predefinidos para servicios comunes
GEMINI_RATE_LIMITER = RateLimiter(max_calls=60, time_window=60)  # 60 req/min
BIGQUERY_RATE_LIMITER = RateLimiter(max_calls=100, time_window=1)  # 100 req/sec

