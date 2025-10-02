#!/usr/bin/env python3
"""
Monitor en tiempo real del BigQuery Vector Pipeline.

Este script monitorea el progreso del pipeline en ejecución
y muestra métricas actualizadas cada N segundos.

Uso:
    # Monitorear run más reciente
    python scripts/monitor_pipeline.py
    
    # Monitorear run específico
    python scripts/monitor_pipeline.py --run-id RUN_ID
    
    # Intervalo personalizado
    python scripts/monitor_pipeline.py --interval 5
"""

import sys
import time
import argparse
from pathlib import Path
from datetime import datetime

# Agregar app al path
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from bigquery_vector.config import BigQueryVectorConfig
from bigquery_vector.progress_tracker import ProgressTracker


def clear_screen():
    """Limpia la pantalla."""
    print("\033[2J\033[H", end="")


def format_duration(seconds):
    """Formatea duración en segundos a formato legible."""
    if seconds is None:
        return "N/A"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"


def print_progress_bar(percentage, width=50):
    """Imprime barra de progreso visual."""
    filled = int(width * percentage / 100)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {percentage:.1f}%"


def monitor_run(run_id: str, interval: int = 3):
    """
    Monitorea un run específico.
    
    Args:
        run_id: ID del run a monitorear.
        interval: Intervalo de actualización en segundos.
    """
    config = BigQueryVectorConfig()
    tracker = ProgressTracker(config)
    
    print(f"🔍 Monitoreando run: {run_id}")
    print(f"📊 Actualizando cada {interval}s (Ctrl+C para salir)")
    print()
    
    try:
        while True:
            clear_screen()
            
            # Header
            print("=" * 100)
            print(f"📊 MONITOR DEL PIPELINE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 100)
            print(f"Run ID: {run_id}")
            print()
            
            # Obtener estado actual
            summary = tracker.get_run_summary(run_id)
            
            if not summary['stages']:
                print("⚠️  No hay datos disponibles para este run")
                break
            
            # Resumen general
            total = summary['total_stages']
            completed = summary['completed_stages']
            failed = summary['failed_stages']
            running = total - completed - failed
            
            print("📈 Resumen General:")
            print(f"   Total Etapas: {total}")
            print(f"   ✅ Completadas: {completed}")
            print(f"   🔄 En progreso: {running}")
            print(f"   ❌ Fallidas: {failed}")
            print()
            
            # Progreso por etapa
            print("📋 Etapas:")
            print()
            
            all_completed = True
            for stage in summary['stages']:
                status = stage['status']
                progress = stage.get('progress_percentage', 0)
                processed = stage.get('items_processed', 0)
                total_items = stage.get('items_total', 0)
                
                # Icono según estado
                if status == 'completed':
                    icon = "✅"
                elif status == 'failed':
                    icon = "❌"
                    all_completed = False
                elif status == 'running':
                    icon = "🔄"
                    all_completed = False
                else:
                    icon = "⏸️"
                    all_completed = False
                
                # Nombre de etapa formateado
                stage_name = stage['pipeline_stage'].replace('_', ' ').title()
                
                print(f"   {icon} {stage_name:<25}")
                
                # Barra de progreso
                if progress > 0:
                    print(f"      {print_progress_bar(progress, width=60)}")
                
                # Items procesados
                if total_items > 0:
                    print(f"      Items: {processed:,} / {total_items:,}")
                
                # Duración
                if stage.get('duration_seconds'):
                    duration = format_duration(stage['duration_seconds'])
                    print(f"      Duración: {duration}")
                elif status == 'running':
                    started = stage.get('started_at')
                    if started:
                        elapsed = (datetime.now() - started.replace(tzinfo=None)).total_seconds()
                        print(f"      Tiempo transcurrido: {format_duration(elapsed)}")
                
                print()
            
            # Métricas destacadas
            if summary['metrics']:
                print("📊 Métricas Clave:")
                
                # Filtrar métricas importantes
                key_metrics = [
                    'chunks_created',
                    'embeddings_created',
                    'unique_objects',
                    'avg_chunk_length',
                    'duration_seconds'
                ]
                
                for metric in summary['metrics']:
                    if metric['metric_name'] in key_metrics:
                        name = metric['metric_name'].replace('_', ' ').title()
                        value = metric['metric_value']
                        
                        # Formatear según tipo
                        if 'duration' in metric['metric_name']:
                            formatted_value = format_duration(value)
                        elif value >= 1000:
                            formatted_value = f"{value:,.0f}"
                        else:
                            formatted_value = f"{value:.2f}"
                        
                        print(f"   • {name}: {formatted_value}")
                
                print()
            
            # Errores recientes
            if summary['errors']:
                print("⚠️  Errores Recientes:")
                for error in summary['errors'][:3]:
                    stage = error.get('pipeline_stage', 'Unknown')
                    message = error.get('error_message', 'No message')[:80]
                    print(f"   • {stage}: {message}")
                print()
            
            # Footer
            print("=" * 100)
            
            if all_completed:
                print("✅ Pipeline completado")
                break
            
            # Esperar antes de actualizar
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n\n⏸️  Monitoreo detenido por usuario")
        print("=" * 100)


def get_latest_run():
    """Obtiene el run más reciente."""
    config = BigQueryVectorConfig()
    tracker = ProgressTracker(config)
    
    runs = tracker.get_all_runs(
        pipeline_name="bigquery_vector_pipeline",
        limit=1
    )
    
    if runs:
        return runs[0]['run_id']
    return None


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Monitor del BigQuery Vector Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--run-id',
                       help='ID del run a monitorear (default: más reciente)')
    parser.add_argument('--interval', type=int, default=3,
                       help='Intervalo de actualización en segundos (default: 3)')
    
    args = parser.parse_args()
    
    # Determinar run a monitorear
    run_id = args.run_id
    
    if not run_id:
        print("🔍 Buscando run más reciente...")
        run_id = get_latest_run()
        
        if not run_id:
            print("❌ No se encontraron runs del pipeline")
            print("💡 Ejecuta: python scripts/run_bigquery_pipeline.py")
            return 1
    
    # Monitorear
    monitor_run(run_id, args.interval)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
