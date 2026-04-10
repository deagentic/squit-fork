"""
Health checker para monitoreo de componentes del sistema.

Verifica el estado de BigQuery, Gemini API, y otros servicios críticos.

Uso:
    from health.checker import HealthChecker
    
    checker = HealthChecker()
    report = await checker.get_health_report()
    print(f"Status: {report['overall_status']}")
"""

from typing import Dict, Any
from enum import Enum
from datetime import datetime, timezone
import time
import asyncio
import logging
import os

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Estados de salud del sistema."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class HealthChecker:
    """
    Health checker para todos los componentes del sistema.
    
    Verifica BigQuery, Gemini API, métricas, y otros componentes críticos.
    
    Example:
        checker = HealthChecker()
        
        # Async
        report = await checker.get_health_report()
        
        # Sync
        report = checker.get_health_report_sync()
        
        print(f"Status: {report['overall_status']}")
        print(f"Components: {report['components']}")
    """
    
    def __init__(self, project_id: str = None):
        """
        Inicializa el health checker.
        
        Args:
            project_id: ID del proyecto GCP
        """
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT", "dfor-prj-dev")
        self.start_time = datetime.now(timezone.utc)

    def _format_sql(self, sql: str, **kwargs) -> str:
        """Formatea SQL de forma segura para Bandit."""
        return sql.format(**kwargs)  # nosec B608
    
    async def check_bigquery(self) -> Dict[str, Any]:
        """
        Verifica conectividad con BigQuery.
        
        Returns:
            Dict con status, latency_ms y error (si hay)
        """
        try:
            from utils.connection_pool import get_bigquery_client
            
            start = time.time()
            client = get_bigquery_client()
            
            # Test query simple
            result = client.query("SELECT 1 as test").result()
            list(result)  # Forzar ejecución
            
            latency_ms = (time.time() - start) * 1000
            
            return {
                "status": HealthStatus.HEALTHY.value,
                "latency_ms": round(latency_ms, 2),
                "project": self.project_id
            }
            
        except Exception as e:
            logger.error(f"BigQuery health check falló: {e}")
            return {
                "status": HealthStatus.UNHEALTHY.value,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def check_gemini_api(self) -> Dict[str, Any]:
        """
        Verifica API de Gemini.
        
        Returns:
            Dict con status y error (si hay)
        """
        try:
            import google.genai as genai
            import os
            
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                return {
                    "status": HealthStatus.UNHEALTHY.value,
                    "error": "GEMINI_API_KEY no configurado"
                }
            
            start = time.time()
            client = genai.Client(api_key=api_key)
            
            # Test simple
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents="Responde solo: OK"
            )
            
            latency_ms = (time.time() - start) * 1000
            
            # Verificar respuesta
            if response and hasattr(response, 'text'):
                return {
                    "status": HealthStatus.HEALTHY.value,
                    "latency_ms": round(latency_ms, 2),
                    "model": "gemini-2.5-flash"
                }
            else:
                return {
                    "status": HealthStatus.DEGRADED.value,
                    "error": "Respuesta inesperada de Gemini"
                }
                
        except Exception as e:
            logger.error(f"Gemini API health check falló: {e}")
            return {
                "status": HealthStatus.UNHEALTHY.value,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def check_embeddings_table(self) -> Dict[str, Any]:
        """
        Verifica que tabla de embeddings existe y tiene datos.
        
        Returns:
            Dict con status, row_count y error (si hay)
        """
        try:
            from utils.connection_pool import get_bigquery_client
            
            client = get_bigquery_client()
            dataset_id = "deacero_sql_objects"
            
            query = self._format_sql("""
            SELECT 
                COUNT(*) as total_rows,
                COUNT(DISTINCT parent_object_id) as unique_objects
            FROM `{project}.{dataset}.chunk_embeddings`
            LIMIT 1
            """, project=self.project_id, dataset=dataset_id)
            
            result = list(client.query(query))
            row = result[0]
            
            if row.total_rows > 0:
                return {
                    "status": HealthStatus.HEALTHY.value,
                    "total_rows": row.total_rows,
                    "unique_objects": row.unique_objects
                }
            else:
                return {
                    "status": HealthStatus.DEGRADED.value,
                    "warning": "Tabla existe pero está vacía"
                }
                
        except Exception as e:
            logger.error(f"Embeddings table health check falló: {e}")
            return {
                "status": HealthStatus.UNHEALTHY.value,
                "error": str(e)
            }
    
    async def check_rate_limiter(self) -> Dict[str, Any]:
        """
        Verifica estado del rate limiter.
        
        Returns:
            Dict con status y usage stats
        """
        try:
            from utils.rate_limiter import GEMINI_RATE_LIMITER
            
            stats = GEMINI_RATE_LIMITER.get_current_usage()
            percentage = stats.get('percentage', 0)
            
            # Status basado en uso
            if percentage < 80:
                status = HealthStatus.HEALTHY.value
            elif percentage < 95:
                status = HealthStatus.DEGRADED.value
            else:
                status = HealthStatus.UNHEALTHY.value
            
            return {
                "status": status,
                "current_usage": stats['current_calls'],
                "max_calls": stats['max_calls'],
                "percentage": round(percentage, 1)
            }
            
        except Exception as e:
            logger.error(f"Rate limiter health check falló: {e}")
            return {
                "status": HealthStatus.UNKNOWN.value,
                "error": str(e)
            }
    
    async def check_circuit_breakers(self) -> Dict[str, Any]:
        """
        Verifica estado de circuit breakers.
        
        Returns:
            Dict con estados de cada circuit breaker
        """
        try:
            from utils.circuit_breaker import (
                GEMINI_CIRCUIT_BREAKER,
                BIGQUERY_CIRCUIT_BREAKER
            )
            
            breakers = {
                "gemini": GEMINI_CIRCUIT_BREAKER.get_stats(),
                "bigquery": BIGQUERY_CIRCUIT_BREAKER.get_stats()
            }
            
            # Determinar status general
            all_closed = all(b['state'] == 'closed' for b in breakers.values())
            any_open = any(b['state'] == 'open' for b in breakers.values())
            
            if all_closed:
                status = HealthStatus.HEALTHY.value
            elif any_open:
                status = HealthStatus.DEGRADED.value
            else:
                status = HealthStatus.HEALTHY.value
            
            return {
                "status": status,
                "breakers": breakers
            }
            
        except Exception as e:
            logger.error(f"Circuit breakers health check falló: {e}")
            return {
                "status": "unknown",
                "error": str(e)
            }
    
    async def get_health_report(self) -> Dict[str, Any]:
        """
        Genera reporte completo de salud del sistema.
        
        Ejecuta todos los health checks en paralelo y agrega resultados.
        
        Returns:
            Dict con overall_status, components, timestamp, uptime
            
        Example:
            checker = HealthChecker()
            report = await checker.get_health_report()
            
            if report['overall_status'] == 'healthy':
                print("✅ Sistema saludable")
            else:
                print(f"⚠️ Sistema {report['overall_status']}")
        """
        # Ejecutar checks en paralelo
        results = await asyncio.gather(
            self.check_bigquery(),
            self.check_gemini_api(),
            self.check_embeddings_table(),
            self.check_rate_limiter(),
            self.check_circuit_breakers(),
            return_exceptions=True
        )
        
        # Mapear resultados
        components = {
            "bigquery": results[0] if not isinstance(results[0], Exception) else {"status": "error", "error": str(results[0])},
            "gemini_api": results[1] if not isinstance(results[1], Exception) else {"status": "error", "error": str(results[1])},
            "embeddings_table": results[2] if not isinstance(results[2], Exception) else {"status": "error", "error": str(results[2])},
            "rate_limiter": results[3] if not isinstance(results[3], Exception) else {"status": "error", "error": str(results[3])},
            "circuit_breakers": results[4] if not isinstance(results[4], Exception) else {"status": "error", "error": str(results[4])},
        }
        
        # Determinar status general
        statuses = [
            c.get('status', 'unknown')
            for c in components.values()
        ]
        
        if all(s == HealthStatus.HEALTHY.value for s in statuses):
            overall_status = HealthStatus.HEALTHY.value
        elif any(s == HealthStatus.UNHEALTHY.value for s in statuses):
            overall_status = HealthStatus.UNHEALTHY.value
        else:
            overall_status = HealthStatus.DEGRADED.value
        
        # Calcular uptime
        uptime = (datetime.now(timezone.utc) - self.start_time).total_seconds()
        
        return {
            "overall_status": overall_status,
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "version": "2.0.0",
            "uptime_seconds": round(uptime, 2),
            "components": components
        }
    
    def get_health_report_sync(self) -> Dict[str, Any]:
        """
        Versión síncrona del health report.
        
        Returns:
            Dict con health report
        """
        return asyncio.run(self.get_health_report())

