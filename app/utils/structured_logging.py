"""
Logging estructurado con contexto para debugging en producción.

Proporciona loggers que emiten JSON estructurado con contexto adicional,
facilitando el análisis de logs en sistemas de monitoreo.

Uso:
    from utils.structured_logging import setup_structured_logging, ContextLogger
    
    # Setup inicial (una vez)
    setup_structured_logging(level="INFO")
    
    # Usar logger con contexto
    logger = ContextLogger(__name__)
    logger.info("Búsqueda completada", query="test", results=10, latency_ms=125)
"""

import logging
import json
from typing import Any, Dict, Optional
from contextvars import ContextVar
from datetime import datetime
import traceback

# Context var para tracking de request/session
request_context: ContextVar[Dict[str, Any]] = ContextVar('request_context', default={})


class StructuredFormatter(logging.Formatter):
    """
    Formatter que produce JSON estructurado.
    
    Convierte log records a JSON con campos estandarizados y contexto adicional.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Formatea log record como JSON.
        
        Args:
            record: Log record de Python logging
            
        Returns:
            String JSON con todos los campos
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "thread_name": record.threadName,
        }
        
        # Agregar contexto de request si existe
        context = request_context.get()
        if context:
            log_data["context"] = context
        
        # Agregar exception info si existe
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }
        
        # Agregar stack info si existe
        if record.stack_info:
            log_data["stack_info"] = record.stack_info
        
        # Agregar campos custom del record
        if hasattr(record, 'custom_fields'):
            log_data.update(record.custom_fields)
        
        try:
            return json.dumps(log_data, default=str)
        except (TypeError, ValueError) as e:
            # Fallback si JSON serialization falla
            return json.dumps({
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "level": "ERROR",
                "message": f"Failed to serialize log: {e}",
                "original_message": str(record.msg)
            })


def setup_structured_logging(
    level: str = "INFO",
    format_json: bool = True,
    include_console: bool = True
):
    """
    Configura logging estructurado para toda la aplicación.
    
    Args:
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_json: Si True, usa formato JSON; si False, formato legible
        include_console: Si True, incluye handler de console
        
    Example:
        # En producción
        setup_structured_logging(level="INFO", format_json=True)
        
        # En desarrollo
        setup_structured_logging(level="DEBUG", format_json=False)
    """
    # Determinar formatter
    if format_json:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Configurar handler
    if include_console:
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
    
        # Configurar root logger
        root_logger = logging.getLogger()
        root_logger.handlers = []  # Limpiar handlers existentes
        root_logger.addHandler(handler)
        root_logger.setLevel(level)
    
    logging.info(f"Structured logging configurado: level={level}, json={format_json}")


class ContextLogger:
    """
    Logger que automáticamente incluye contexto y campos custom.
    
    Proporciona métodos de logging mejorados que aceptan campos adicionales
    como kwargs, facilitando logging estructurado.
    
    Example:
        logger = ContextLogger(__name__)
        
        # Log con campos adicionales
        logger.info(
            "Usuario autenticado",
            user_id="123",
            ip="192.168.1.1",
            duration_ms=45
        )
        
        # Log de error con contexto
        try:
            risky_operation()
        except Exception as e:
            logger.error(
                "Operación falló",
                operation="risky_operation",
                error_type=type(e).__name__
            )
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def debug(self, message: str, **kwargs):
        """Log debug con campos custom."""
        extra = {'custom_fields': kwargs}
        self.logger.debug(message, extra=extra)
    
    def info(self, message: str, **kwargs):
        """Log info con campos custom."""
        extra = {'custom_fields': kwargs}
        self.logger.info(message, extra=extra)
    
    def warning(self, message: str, **kwargs):
        """Log warning con campos custom."""
        extra = {'custom_fields': kwargs}
        self.logger.warning(message, extra=extra)
    
    def error(self, message: str, **kwargs):
        """Log error con campos custom."""
        extra = {'custom_fields': kwargs}
        self.logger.error(message, extra=extra)
    
    def critical(self, message: str, **kwargs):
        """Log critical con campos custom."""
        extra = {'custom_fields': kwargs}
        self.logger.critical(message, extra=extra)
    
    def exception(self, message: str, **kwargs):
        """Log exception con traceback completo."""
        extra = {'custom_fields': kwargs}
        self.logger.exception(message, extra=extra)


def set_request_context(**kwargs):
    """
    Establece contexto para el request actual.
    
    El contexto se incluirá automáticamente en todos los logs
    dentro del mismo contexto de ejecución (útil con async/threading).
    
    Args:
        **kwargs: Campos de contexto (request_id, user_id, session_id, etc.)
        
    Example:
        set_request_context(
            request_id="req-123",
            user_id="user-456",
            session_id="sess-789"
        )
        
        logger.info("Procesando búsqueda")
        # Log incluirá automáticamente request_id, user_id, session_id
    """
    current = request_context.get().copy()
    current.update(kwargs)
    request_context.set(current)


def clear_request_context():
    """Limpia el contexto de request actual."""
    request_context.set({})


def get_request_context() -> Dict[str, Any]:
    """Obtiene el contexto de request actual."""
    return request_context.get().copy()


class LoggingContext:
    """
    Context manager para agregar contexto temporal a logs.
    
    Example:
        with LoggingContext(operation="search", query="test"):
            logger.info("Ejecutando búsqueda")
            # Log incluirá operation y query
    """
    
    def __init__(self, **kwargs):
        self.context = kwargs
        self.previous_context = None
    
    def __enter__(self):
        self.previous_context = get_request_context()
        set_request_context(**self.context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        request_context.set(self.previous_context)


def log_function_call(logger: ContextLogger = None):
    """
    Decorator para loggear entrada/salida de funciones.
    
    Args:
        logger: Logger a usar (default: crea uno con nombre de función)
        
    Example:
        @log_function_call()
        def process_data(user_id: str):
            return f"Processed {user_id}"
    """
    def decorator(func):
        nonlocal logger
        if logger is None:
            logger = ContextLogger(func.__module__)
        
        def wrapper(*args, **kwargs):
            logger.debug(
                f"Calling {func.__name__}",
                function=func.__name__,
                args_count=len(args),
                kwargs_keys=list(kwargs.keys())
            )
            
            try:
                result = func(*args, **kwargs)
                logger.debug(
                    f"Completed {func.__name__}",
                    function=func.__name__,
                    success=True
                )
                return result
            except Exception as e:
                logger.error(
                    f"Failed {func.__name__}",
                    function=func.__name__,
                    error_type=type(e).__name__,
                    error_message=str(e)
                )
                raise
        
        return wrapper
    return decorator

