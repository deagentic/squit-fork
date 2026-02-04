"""
Sistema de métricas thread-safe para observabilidad.

Proporciona collectors para gauge, counter e histogram metrics,
permitiendo tracking de latencia, throughput y uso del sistema.

Uso:
    from utils.metrics import get_metrics
    
    metrics = get_metrics()
    
    # Timer context manager
    with metrics.timer("search_latency"):
        results = search(query)
    
    # Increment counter
    metrics.increment("searches_total")
    
    # Set gauge
    metrics.gauge("active_sessions", 42)
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timezone
from collections import defaultdict
import threading
import time
import logging

logger = logging.getLogger(__name__)


@dataclass
class Metric:
    """Representa una métrica individual."""
    name: str
    value: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tags: Dict[str, str] = field(default_factory=dict)
    metric_type: str = "gauge"  # gauge, counter, histogram


class MetricsCollector:
    """
    Collector de métricas thread-safe.
    
    Permite registrar métricas de diferentes tipos (gauge, counter, histogram)
    y obtener resúmenes estadísticos.
    
    Thread-safe para uso en aplicaciones multi-threaded.
    
    Example:
        metrics = MetricsCollector()
        
        # Gauge: valor instantáneo
        metrics.gauge("memory_usage_mb", 1024.5)
        
        # Counter: valor acumulativo
        metrics.increment("requests_total")
        metrics.increment("errors_total", value=2)
        
        # Histogram: para distribuciones
        metrics.histogram("response_time_ms", 125.3)
        
        # Timer context manager
        with metrics.timer("operation_duration"):
            do_operation()
        
        # Obtener resumen
        summary = metrics.get_summary()
    """
    
    def __init__(self):
        self.metrics: Dict[str, List[Metric]] = defaultdict(list)
        self.lock = threading.Lock()
        self.start_time = datetime.now(timezone.utc)
    
    def gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """
        Registra métrica gauge (valor instantáneo).
        
        Args:
            name: Nombre de la métrica
            value: Valor actual
            tags: Tags opcionales para segmentación
        """
        with self.lock:
            self.metrics[name].append(
                Metric(
                    name=name,
                    value=value,
                    tags=tags or {},
                    metric_type="gauge"
                )
            )
    
    def increment(
        self,
        name: str,
        value: float = 1.0,
        tags: Optional[Dict[str, str]] = None
    ):
        """
        Incrementa contador.
        
        Args:
            name: Nombre del contador
            value: Valor a incrementar (default: 1.0)
            tags: Tags opcionales
        """
        with self.lock:
            self.metrics[name].append(
                Metric(
                    name=name,
                    value=value,
                    tags=tags or {},
                    metric_type="counter"
                )
            )
    
    def histogram(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None
    ):
        """
        Registra valor para histograma (distribuciones).
        
        Args:
            name: Nombre de la métrica
            value: Valor observado
            tags: Tags opcionales
        """
        with self.lock:
            self.metrics[name].append(
                Metric(
                    name=name,
                    value=value,
                    tags=tags or {},
                    metric_type="histogram"
                )
            )
    
    def timer(self, name: str, tags: Optional[Dict[str, str]] = None):
        """
        Context manager para medir tiempo de ejecución.
        
        Args:
            name: Nombre de la métrica
            tags: Tags opcionales
            
        Returns:
            MetricTimer context manager
        """
        return MetricTimer(self, name, tags or {})
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Obtiene resumen estadístico de todas las métricas.
        
        Returns:
            Dict con estadísticas por métrica (count, sum, avg, min, max, p50, p95, p99)
        """
        with self.lock:
            summary = {}
            
            for name, metrics_list in self.metrics.items():
                if not metrics_list:
                    continue
                
                values = [m.value for m in metrics_list]
                metric_type = metrics_list[0].metric_type
                
                # Estadísticas básicas
                stats = {
                    "type": metric_type,
                    "count": len(values),
                    "sum": sum(values),
                    "avg": sum(values) / len(values) if values else 0,
                    "min": min(values) if values else 0,
                    "max": max(values) if values else 0,
                }
                
                # Percentiles para histogramas
                if metric_type == "histogram" and len(values) > 0:
                    sorted_values = sorted(values)
                    stats["p50"] = self._percentile(sorted_values, 50)
                    stats["p95"] = self._percentile(sorted_values, 95)
                    stats["p99"] = self._percentile(sorted_values, 99)
                
                summary[name] = stats
            
            # Agregar metadatos
            summary["_metadata"] = {
                "uptime_seconds": (datetime.now(timezone.utc) - self.start_time).total_seconds(),
                "total_metrics": sum(len(m) for m in self.metrics.values())
            }
            
            return summary
    
    def get_metric_history(
        self,
        name: str,
        limit: int = 100
    ) -> List[Metric]:
        """
        Obtiene historial de una métrica específica.
        
        Args:
            name: Nombre de la métrica
            limit: Máximo número de valores a retornar
            
        Returns:
            Lista de métricas (más recientes primero)
        """
        with self.lock:
            metrics_list = self.metrics.get(name, [])
            return list(reversed(metrics_list[-limit:]))
    
    def reset(self):
        """Resetea todas las métricas."""
        with self.lock:
            self.metrics.clear()
            self.start_time = datetime.now(timezone.utc)
            logger.info("Métricas reseteadas")
    
    def reset_metric(self, name: str):
        """Resetea una métrica específica."""
        with self.lock:
            if name in self.metrics:
                self.metrics[name].clear()
                logger.debug(f"Métrica '{name}' reseteada")
    
    @staticmethod
    def _percentile(sorted_values: List[float], percentile: int) -> float:
        """Calcula percentil de lista ordenada."""
        if not sorted_values:
            return 0
        
        index = int((percentile / 100.0) * len(sorted_values))
        index = min(index, len(sorted_values) - 1)
        return sorted_values[index]


class MetricTimer:
    """
    Context manager para medir tiempo de ejecución.
    
    Usado internamente por MetricsCollector.timer()
    """
    
    def __init__(
        self,
        collector: MetricsCollector,
        name: str,
        tags: Dict[str, str]
    ):
        self.collector = collector
        self.name = name
        self.tags = tags
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        # Agregar tag de éxito/error
        tags = self.tags.copy()
        tags["success"] = "false" if exc_type else "true"
        
        self.collector.histogram(
            f"{self.name}_seconds",
            duration,
            tags
        )


class AggregatedMetrics:
    """
    Métricas agregadas con ventana de tiempo.
    
    Mantiene métricas por ventanas de tiempo (ej: último minuto, última hora)
    y descarta datos antiguos automáticamente.
    
    Example:
        metrics = AggregatedMetrics(window_size=60)  # 60 segundos
        
        metrics.record("requests", 1)
        metrics.record("latency_ms", 125)
        
        # Obtener métricas de última ventana
        summary = metrics.get_window_summary()
    """
    
    def __init__(self, window_size: float = 60.0):
        """
        Args:
            window_size: Tamaño de ventana en segundos
        """
        self.window_size = window_size
        self.metrics: Dict[str, List[tuple]] = defaultdict(list)  # (timestamp, value)
        self.lock = threading.Lock()
    
    def record(self, name: str, value: float):
        """Registra valor con timestamp."""
        with self.lock:
            now = time.time()
            self.metrics[name].append((now, value))
            self._cleanup(name, now)
    
    def _cleanup(self, name: str, now: float):
        """Elimina valores fuera de la ventana."""
        cutoff = now - self.window_size
        self.metrics[name] = [
            (ts, val) for ts, val in self.metrics[name]
            if ts >= cutoff
        ]
    
    def get_window_summary(self) -> Dict[str, Any]:
        """Obtiene resumen de ventana actual."""
        with self.lock:
            now = time.time()
            summary = {}
            
            for name, values_list in self.metrics.items():
                self._cleanup(name, now)
                
                if not values_list:
                    continue
                
                values = [v for _, v in values_list]
                summary[name] = {
                    "count": len(values),
                    "sum": sum(values),
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "rate_per_second": len(values) / self.window_size
                }
            
            return summary


# Singleton global metrics collector
_global_metrics_collector: Optional[MetricsCollector] = None
_global_lock = threading.Lock()


def get_metrics() -> MetricsCollector:
    """
    Obtiene el collector global de métricas (singleton).
    
    Returns:
        MetricsCollector global
    """
    global _global_metrics_collector
    
    if _global_metrics_collector is None:
        with _global_lock:
            if _global_metrics_collector is None:
                _global_metrics_collector = MetricsCollector()
    
    return _global_metrics_collector

