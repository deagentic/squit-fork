"""
Tests para el módulo de métricas.

Tests unitarios que validan el collector de métricas thread-safe.
"""

import pytest
from unittest.mock import Mock
from utils.metrics import MetricsCollector, get_metrics
import time


class TestMetricsCollector:
    """Tests para MetricsCollector."""
    
    def test_gauge_metric(self):
        """Test que gauge registra valores instantáneos."""
        metrics = MetricsCollector()
        
        metrics.gauge("memory_usage", 1024.5)
        metrics.gauge("cpu_usage", 75.0)
        
        summary = metrics.get_summary()
        
        assert "memory_usage" in summary
        assert summary["memory_usage"]["count"] == 1
        assert summary["memory_usage"]["avg"] == 1024.5
    
    def test_increment_counter(self):
        """Test que increment suma valores."""
        metrics = MetricsCollector()
        
        metrics.increment("requests_total")
        metrics.increment("requests_total")
        metrics.increment("requests_total", value=3)
        
        summary = metrics.get_summary()
        
        assert summary["requests_total"]["count"] == 3
        assert summary["requests_total"]["sum"] == 5.0  # 1 + 1 + 3
    
    def test_histogram_with_percentiles(self):
        """Test que histogram calcula percentiles."""
        metrics = MetricsCollector()
        
        # Agregar valores de latencia
        for latency in [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]:
            metrics.histogram("latency_ms", latency)
        
        summary = metrics.get_summary()
        
        assert "latency_ms" in summary
        assert summary["latency_ms"]["count"] == 10
        assert summary["latency_ms"]["min"] == 10
        assert summary["latency_ms"]["max"] == 100
        assert summary["latency_ms"]["avg"] == 55
        
        # Verificar percentiles
        assert "p50" in summary["latency_ms"]
        assert "p95" in summary["latency_ms"]
        assert "p99" in summary["latency_ms"]
    
    def test_timer_context_manager(self):
        """Test que timer mide tiempo correctamente."""
        metrics = MetricsCollector()
        
        with metrics.timer("operation_duration"):
            time.sleep(0.01)  # 10ms
        
        summary = metrics.get_summary()
        
        assert "operation_duration_seconds" in summary
        assert summary["operation_duration_seconds"]["count"] == 1
        assert summary["operation_duration_seconds"]["avg"] >= 0.01
    
    def test_get_metric_history(self):
        """Test que get_metric_history retorna historial."""
        metrics = MetricsCollector()
        
        for i in range(5):
            metrics.gauge("test_metric", i)
        
        history = metrics.get_metric_history("test_metric", limit=10)
        
        assert len(history) == 5
        # Más recientes primero
        assert history[0].value == 4
        assert history[-1].value == 0
    
    def test_reset_metrics(self):
        """Test que reset limpia métricas."""
        metrics = MetricsCollector()
        
        metrics.increment("counter", 10)
        metrics.reset()
        
        summary = metrics.get_summary()
        assert len(summary) == 1  # Solo _metadata
    
    def test_get_metrics_singleton(self):
        """Test que get_metrics retorna singleton."""
        metrics1 = get_metrics()
        metrics2 = get_metrics()
        
        assert metrics1 is metrics2
        
        # Modificar uno debe reflejarse en otro
        metrics1.increment("test")
        summary = metrics2.get_summary()
        assert "test" in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

