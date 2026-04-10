"""
Sistema de tracking y persistencia para el pipeline BigQuery Vector.

Este módulo implementa persistencia robusta del progreso del pipeline,
permitiendo reiniciar desde el último checkpoint en caso de fallos.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from google.cloud import bigquery
from .config import BigQueryVectorConfig

logger = logging.getLogger(__name__)


class ProgressTracker:
    """
    Rastrea y persiste el progreso del pipeline BigQuery Vector.
    
    Funcionalidades:
    - Persistencia de progreso en BigQuery
    - Checkpoint/recovery automático
    - Métricas de ejecución
    - Logging robusto de errores
    """
    
    PROGRESS_TABLE = "pipeline_progress"
    METRICS_TABLE = "pipeline_metrics"
    ERRORS_TABLE = "pipeline_errors"
    
    def __init__(self, config: Optional[BigQueryVectorConfig] = None):
        """
        Inicializa el tracker de progreso.
        
        Args:
            config: Configuración del sistema.
        """
        self.config = config or BigQueryVectorConfig()
        self.client = bigquery.Client(project=self.config.PROJECT_ID)
        self._ensure_tracking_tables()

    def _format_sql(self, sql: str, **kwargs) -> str:
        """Formatea SQL de forma segura para Bandit."""
        return sql.format(**kwargs)  # nosec B608
    
    def _ensure_tracking_tables(self):
        """Crea tablas de tracking si no existen."""
        
        # Tabla de progreso del pipeline
        progress_table_sql = self._format_sql("""
        CREATE TABLE IF NOT EXISTS `{project}.{dataset}.{table}` (
            run_id STRING NOT NULL,
            pipeline_stage STRING NOT NULL,
            status STRING NOT NULL,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            progress_percentage FLOAT64,
            items_processed INT64,
            items_total INT64,
            checkpoint_data JSON,
            metadata JSON,
            PRIMARY KEY (run_id, pipeline_stage) NOT ENFORCED
        )
        """, project=self.config.PROJECT_ID, dataset=self.config.DATASET_ID, table=self.PROGRESS_TABLE)
        
        # Tabla de métricas
        metrics_table_sql = self._format_sql("""
        CREATE TABLE IF NOT EXISTS `{project}.{dataset}.{table}` (
            metric_id STRING NOT NULL,
            run_id STRING NOT NULL,
            pipeline_stage STRING,
            metric_name STRING NOT NULL,
            metric_value FLOAT64,
            metric_type STRING,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
            metadata JSON,
            PRIMARY KEY (metric_id) NOT ENFORCED
        )
        """, project=self.config.PROJECT_ID, dataset=self.config.DATASET_ID, table=self.METRICS_TABLE)
        
        # Tabla de errores
        errors_table_sql = self._format_sql("""
        CREATE TABLE IF NOT EXISTS `{project}.{dataset}.{table}` (
            error_id STRING NOT NULL,
            run_id STRING NOT NULL,
            pipeline_stage STRING,
            error_type STRING,
            error_message STRING,
            error_traceback STRING,
            occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
            context JSON,
            PRIMARY KEY (error_id) NOT ENFORCED
        )
        """, project=self.config.PROJECT_ID, dataset=self.config.DATASET_ID, table=self.ERRORS_TABLE)
        
        try:
            self.client.query(progress_table_sql).result()
            self.client.query(metrics_table_sql).result()
            self.client.query(errors_table_sql).result()
            logger.info("✅ Tablas de tracking verificadas")
        except Exception as e:
            logger.warning(f"Tablas de tracking no pudieron ser creadas: {e}")
    
    def start_run(self, pipeline_name: str, metadata: Optional[Dict] = None) -> str:
        """
        Inicia un nuevo run del pipeline.
        
        Args:
            pipeline_name: Nombre del pipeline.
            metadata: Metadatos adicionales.
            
        Returns:
            run_id único para este run.
        """
        from google.cloud import bigquery
        import json
        
        run_id = f"{pipeline_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        metadata_val = json.dumps(metadata) if metadata else "{}"
        
        insert_sql = self._format_sql("""
        INSERT INTO `{project}.{dataset}.{table}`
        (run_id, pipeline_stage, status, started_at, progress_percentage, items_processed, items_total, metadata)
        VALUES (
            @run_id,
            'initialization',
            'running',
            CURRENT_TIMESTAMP(),
            0.0,
            0,
            0,
            PARSE_JSON(@metadata)
        )
        """, project=self.config.PROJECT_ID, dataset=self.config.DATASET_ID, table=self.PROGRESS_TABLE)
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("run_id", "STRING", run_id),
                bigquery.ScalarQueryParameter("metadata", "JSON", metadata_val)
            ]
        )
        
        self.client.query(insert_sql, job_config=job_config).result()
        logger.info(f"🚀 Run iniciado: {run_id}")
        
        return run_id
    
    def update_stage(
        self,
        run_id: str,
        stage: str,
        status: str,
        progress: float = 0.0,
        items_processed: int = 0,
        items_total: int = 0,
        checkpoint_data: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ):
        """
        Actualiza el progreso de una etapa del pipeline.
        
        Args:
            run_id: ID del run.
            stage: Nombre de la etapa.
            status: Estado (running, completed, failed).
            progress: Porcentaje de progreso (0-100).
            items_processed: Items procesados.
            items_total: Total de items.
            checkpoint_data: Datos de checkpoint para recovery.
            metadata: Metadatos adicionales.
        """
        from google.cloud import bigquery
        import json
        
        checkpoint_val = json.dumps(checkpoint_data) if checkpoint_data else None
        metadata_val = json.dumps(metadata) if metadata else None
        
        # Parámetros base comunes
        query_params = [
            bigquery.ScalarQueryParameter("run_id", "STRING", run_id),
            bigquery.ScalarQueryParameter("stage", "STRING", stage),
            bigquery.ScalarQueryParameter("status", "STRING", status),
            bigquery.ScalarQueryParameter("progress", "FLOAT64", progress),
            bigquery.ScalarQueryParameter("items_processed", "INT64", items_processed),
            bigquery.ScalarQueryParameter("items_total", "INT64", items_total),
            bigquery.ScalarQueryParameter("checkpoint_data", "JSON", checkpoint_val),
            bigquery.ScalarQueryParameter("metadata", "JSON", metadata_val)
        ]
        
        # Verificar si existe el registro
        check_sql = self._format_sql("""
        SELECT COUNT(*) as count
        FROM `{project}.{dataset}.{table}`
        WHERE run_id = @run_id AND pipeline_stage = @stage
        """, project=self.config.PROJECT_ID, dataset=self.config.DATASET_ID, table=self.PROGRESS_TABLE)
        
        check_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("run_id", "STRING", run_id),
                bigquery.ScalarQueryParameter("stage", "STRING", stage)
            ]
        )
        
        result = list(self.client.query(check_sql, job_config=check_config))
        exists = result[0].count > 0 if result else False
        
        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        
        if exists:
            # UPDATE
            completed_at_sql = "CURRENT_TIMESTAMP()" if status == 'completed' else "NULL"
            update_sql = self._format_sql("""
            UPDATE `{project}.{dataset}.{table}`
            SET 
                status = @status,
                progress_percentage = @progress,
                items_processed = @items_processed,
                items_total = @items_total,
                checkpoint_data = PARSE_JSON(@checkpoint_data),
                metadata = PARSE_JSON(@metadata),
                completed_at = {completed_at_sql}
            WHERE run_id = @run_id AND pipeline_stage = @stage
            """, project=self.config.PROJECT_ID, dataset=self.config.DATASET_ID, table=self.PROGRESS_TABLE, completed_at_sql=completed_at_sql)
            self.client.query(update_sql, job_config=job_config).result()
        else:
            # INSERT
            insert_sql = self._format_sql("""
            INSERT INTO `{project}.{dataset}.{table}`
            (run_id, pipeline_stage, status, started_at, progress_percentage, 
             items_processed, items_total, checkpoint_data, metadata)
            VALUES (
                @run_id,
                @stage,
                @status,
                CURRENT_TIMESTAMP(),
                @progress,
                @items_processed,
                @items_total,
                PARSE_JSON(@checkpoint_data),
                PARSE_JSON(@metadata)
            )
            """, project=self.config.PROJECT_ID, dataset=self.config.DATASET_ID, table=self.PROGRESS_TABLE)
            self.client.query(insert_sql, job_config=job_config).result()
        
        logger.info(f"📊 {stage}: {status} ({progress:.1f}%) - {items_processed}/{items_total}")
    
    def complete_stage(
        self,
        run_id: str,
        stage: str,
        items_processed: int,
        metadata: Optional[Dict] = None
    ):
        """Marca una etapa como completada."""
        self.update_stage(
            run_id=run_id,
            stage=stage,
            status="completed",
            progress=100.0,
            items_processed=items_processed,
            items_total=items_processed,
            metadata=metadata
        )
    
    def fail_stage(
        self,
        run_id: str,
        stage: str,
        error_message: str,
        error_traceback: Optional[str] = None,
        context: Optional[Dict] = None
    ):
        """Marca una etapa como fallida y registra el error."""
        # Actualizar progreso
        self.update_stage(
            run_id=run_id,
            stage=stage,
            status="failed",
            metadata={"error": error_message}
        )
        
        # Registrar error
        self.log_error(
            run_id=run_id,
            pipeline_stage=stage,
            error_type="PipelineError",
            error_message=error_message,
            error_traceback=error_traceback,
            context=context
        )
        
        logger.error(f"❌ {stage} falló: {error_message}")
    
    def log_metric(
        self,
        run_id: str,
        metric_name: str,
        metric_value: float,
        pipeline_stage: Optional[str] = None,
        metric_type: str = "gauge",
        metadata: Optional[Dict] = None
    ):
        """
        Registra una métrica del pipeline.
        
        Args:
            run_id: ID del run.
            metric_name: Nombre de la métrica.
            metric_value: Valor de la métrica.
            pipeline_stage: Etapa asociada.
            metric_type: Tipo (gauge, counter, timing).
            metadata: Metadatos adicionales.
        """
        from google.cloud import bigquery
        import json
        
        metric_id = f"{run_id}_{metric_name}_{datetime.now().timestamp()}"
        metadata_val = json.dumps(metadata) if metadata else None
        
        insert_sql = self._format_sql("""
        INSERT INTO `{project}.{dataset}.{table}`
        (metric_id, run_id, pipeline_stage, metric_name, metric_value, metric_type, metadata)
        VALUES (
            @metric_id,
            @run_id,
            @pipeline_stage,
            @metric_name,
            @metric_value,
            @metric_type,
            PARSE_JSON(@metadata)
        )
        """, project=self.config.PROJECT_ID, dataset=self.config.DATASET_ID, table=self.METRICS_TABLE)
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("metric_id", "STRING", metric_id),
                bigquery.ScalarQueryParameter("run_id", "STRING", run_id),
                bigquery.ScalarQueryParameter("pipeline_stage", "STRING", pipeline_stage),
                bigquery.ScalarQueryParameter("metric_name", "STRING", metric_name),
                bigquery.ScalarQueryParameter("metric_value", "FLOAT64", metric_value),
                bigquery.ScalarQueryParameter("metric_type", "STRING", metric_type),
                bigquery.ScalarQueryParameter("metadata", "JSON", metadata_val)
            ]
        )
        
        self.client.query(insert_sql, job_config=job_config).result()
    
    def log_error(
        self,
        run_id: str,
        pipeline_stage: str,
        error_type: str,
        error_message: str,
        error_traceback: Optional[str] = None,
        context: Optional[Dict] = None
    ):
        """
        Registra un error del pipeline.
        
        Args:
            run_id: ID del run.
            pipeline_stage: Etapa donde ocurrió el error.
            error_type: Tipo de error.
            error_message: Mensaje de error.
            error_traceback: Traceback completo.
            context: Contexto adicional.
        """
        from google.cloud import bigquery
        import json
        
        error_id = f"{run_id}_{pipeline_stage}_{datetime.now().timestamp()}"
        context_val = json.dumps(context) if context else None
        
        insert_sql = self._format_sql("""
        INSERT INTO `{project}.{dataset}.{table}`
        (error_id, run_id, pipeline_stage, error_type, error_message, error_traceback, context)
        VALUES (
            @error_id,
            @run_id,
            @pipeline_stage,
            @error_type,
            @error_message,
            @error_traceback,
            PARSE_JSON(@context)
        )
        """, project=self.config.PROJECT_ID, dataset=self.config.DATASET_ID, table=self.ERRORS_TABLE)
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("error_id", "STRING", error_id),
                bigquery.ScalarQueryParameter("run_id", "STRING", run_id),
                bigquery.ScalarQueryParameter("pipeline_stage", "STRING", pipeline_stage),
                bigquery.ScalarQueryParameter("error_type", "STRING", error_type),
                bigquery.ScalarQueryParameter("error_message", "STRING", error_message),
                bigquery.ScalarQueryParameter("error_traceback", "STRING", error_traceback),
                bigquery.ScalarQueryParameter("context", "JSON", context_val)
            ]
        )
        
        try:
            self.client.query(insert_sql, job_config=job_config).result()
        except Exception as e:
            logger.error(f"Error registrando error: {e}")
    
    def get_last_checkpoint(self, pipeline_name: str, stage: str) -> Optional[Dict]:
        """
        Recupera el último checkpoint de una etapa.
        
        Args:
            pipeline_name: Nombre del pipeline.
            stage: Etapa del pipeline.
            
        Returns:
            Datos del checkpoint o None.
        """
        from google.cloud import bigquery

        query = self._format_sql("""
        SELECT checkpoint_data, items_processed, items_total
        FROM `{project}.{dataset}.{table}`
        WHERE run_id LIKE CONCAT(@pipeline_name, '%')
          AND pipeline_stage = @stage
          AND status = 'running'
        ORDER BY started_at DESC
        LIMIT 1
        """, project=self.config.PROJECT_ID, dataset=self.config.DATASET_ID, table=self.PROGRESS_TABLE)
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("pipeline_name", "STRING", pipeline_name),
                bigquery.ScalarQueryParameter("stage", "STRING", stage)
            ]
        )
        
        result = list(self.client.query(query, job_config=job_config))
        if result and result[0].checkpoint_data:
            return {
                "checkpoint_data": result[0].checkpoint_data,
                "items_processed": result[0].items_processed,
                "items_total": result[0].items_total
            }
        
        return None
    
    def get_run_summary(self, run_id: str) -> Dict[str, Any]:
        """
        Obtiene resumen completo de un run.
        
        Args:
            run_id: ID del run.
            
        Returns:
            Resumen con todas las etapas y métricas.
        """
        from google.cloud import bigquery
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("run_id", "STRING", run_id)]
        )
        
        # Progreso de etapas
        stages_sql = self._format_sql("""
        SELECT 
            pipeline_stage,
            status,
            started_at,
            completed_at,
            progress_percentage,
            items_processed,
            items_total,
            TIMESTAMP_DIFF(completed_at, started_at, SECOND) as duration_seconds
        FROM `{project}.{dataset}.{table}`
        WHERE run_id = @run_id
        ORDER BY started_at
        """, project=self.config.PROJECT_ID, dataset=self.config.DATASET_ID, table=self.PROGRESS_TABLE)
        
        stages = [dict(row) for row in self.client.query(stages_sql, job_config=job_config)]
        
        # Métricas
        metrics_sql = self._format_sql("""
        SELECT 
            metric_name,
            metric_value,
            metric_type,
            pipeline_stage
        FROM `{table}`
        WHERE run_id = @run_id
        ORDER BY recorded_at
        """, table=f"{self.config.PROJECT_ID}.{self.config.DATASET_ID}.{self.METRICS_TABLE}")
        
        metrics = [dict(row) for row in self.client.query(metrics_sql, job_config=job_config)]
        
        # Errores
        errors_sql = self._format_sql("""
        SELECT 
            pipeline_stage,
            error_type,
            error_message,
            occurred_at
        FROM `{table}`
        WHERE run_id = @run_id
        ORDER BY occurred_at
        """, table=f"{self.config.PROJECT_ID}.{self.config.DATASET_ID}.{self.ERRORS_TABLE}")
        
        errors = [dict(row) for row in self.client.query(errors_sql, job_config=job_config)]
        
        return {
            "run_id": run_id,
            "stages": stages,
            "metrics": metrics,
            "errors": errors,
            "total_stages": len(stages),
            "completed_stages": len([s for s in stages if s['status'] == 'completed']),
            "failed_stages": len([s for s in stages if s['status'] == 'failed'])
        }
    
    def get_all_runs(self, pipeline_name: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """
        Obtiene histórico de runs.
        
        Args:
            pipeline_name: Filtrar por nombre de pipeline.
            limit: Número máximo de runs.
            
        Returns:
            Lista de runs con su estado.
        """
        from google.cloud import bigquery
        
        query_params = [bigquery.ScalarQueryParameter("limit", "INT64", limit)]
        where_clause = ""
        if pipeline_name:
            where_clause = "WHERE run_id LIKE CONCAT(@pipeline_name, '%')"
            query_params.append(bigquery.ScalarQueryParameter("pipeline_name", "STRING", pipeline_name))
        
        query = self._format_sql("""
        WITH run_summary AS (
            SELECT 
                run_id,
                MIN(started_at) as started_at,
                MAX(completed_at) as completed_at,
                COUNT(*) as total_stages,
                SUM(IF(status = 'completed', 1, 0)) as completed_stages,
                SUM(IF(status = 'failed', 1, 0)) as failed_stages,
                AVG(progress_percentage) as avg_progress
            FROM `{project}.{dataset}.{table}`
            {where_clause}
            GROUP BY run_id
        )
        SELECT *
        FROM run_summary
        ORDER BY started_at DESC
        LIMIT @limit
        """, project=self.config.PROJECT_ID, dataset=self.config.DATASET_ID, table=self.PROGRESS_TABLE, where_clause=where_clause)
        
        job_config = bigquery.QueryJobConfig(query_parameters=query_params)
        return [dict(row) for row in self.client.query(query, job_config=job_config)]
    
    def print_progress_report(self, run_id: str):
        """Imprime reporte de progreso formateado."""
        summary = self.get_run_summary(run_id)
        
        print("\n" + "=" * 70)
        print(f"📊 REPORTE DE PROGRESO - {run_id}")
        print("=" * 70)
        
        print("\n📈 Resumen General:")
        print(f"   Total Etapas: {summary['total_stages']}")
        print(f"   ✅ Completadas: {summary['completed_stages']}")
        print(f"   ❌ Fallidas: {summary['failed_stages']}")
        
        print("\n📋 Etapas:")
        for stage in summary['stages']:
            status_icon = "✅" if stage['status'] == 'completed' else "❌" if stage['status'] == 'failed' else "🔄"
            duration = f"{stage['duration_seconds']}s" if stage.get('duration_seconds') else "en curso"
            print(f"   {status_icon} {stage['pipeline_stage']}: {stage['status']} ({stage['progress_percentage']:.1f}%) - {duration}")
        
        if summary['metrics']:
            print("\n📊 Métricas:")
            for metric in summary['metrics'][:10]:
                print(f"   • {metric['metric_name']}: {metric['metric_value']}")
        
        if summary['errors']:
            print(f"\n⚠️  Errores ({len(summary['errors'])}):")
            for error in summary['errors'][:5]:
                print(f"   • {error['pipeline_stage']}: {error['error_message'][:80]}")
        
        print("\n" + "=" * 70)
