#!/usr/bin/env python3
"""
Script ejecutor robusto del BigQuery Vector Pipeline.

Este script ejecuta el pipeline completo con:
- Tracking de progreso persistente
- Checkpoint/recovery automático
- Logging detallado
- Reportes ejecutivos

Uso:
    # Pipeline completo
    python scripts/run_bigquery_pipeline.py
    
    # Saltar etapas específicas
    python scripts/run_bigquery_pipeline.py --skip-chunks
    python scripts/run_bigquery_pipeline.py --skip-embeddings
    
    # Ver histórico de runs
    python scripts/run_bigquery_pipeline.py --list-runs
    
    # Ver reporte de un run específico
    python scripts/run_bigquery_pipeline.py --report RUN_ID
"""

import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Agregar app al path
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from bigquery_vector.config import BigQueryVectorConfig
from bigquery_vector.chunking_pipeline import BigQueryChunkingPipeline
from bigquery_vector.progress_tracker import ProgressTracker


def setup_logging(verbose: bool = False):
    """Configura logging del script."""
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(f"pipeline_{datetime.now().strftime('%Y%m%d')}.log")
        ]
    )


def print_banner():
    """Imprime banner del sistema."""
    print("\n" + "=" * 80)
    print("🎯 SQUIT - BigQuery Vector Pipeline")
    print("=" * 80)
    print(f"📅 Ejecutado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🔧 Sistema: Chunking Inteligente + Embeddings Gemini + Vector Search")
    print("📊 Tracking: Persistente con checkpoint/recovery")
    print("=" * 80)
    print()


def run_pipeline(args):
    """Ejecuta el pipeline completo."""
    print_banner()
    
    # Configurar
    config = BigQueryVectorConfig()
    pipeline = BigQueryChunkingPipeline(config)
    
    print(f"📋 Configuración:")
    print(f"   Proyecto: {config.PROJECT_ID}")
    print(f"   Dataset: {config.DATASET_ID}")
    print(f"   Tabla chunks: {config.CHUNKS_TABLE}")
    print(f"   Tabla embeddings: {config.EMBEDDINGS_TABLE}")
    print(f"   Modelo: {config.EMBEDDING_MODEL}")
    print(f"   Dimensiones: {config.EMBEDDING_DIMENSIONS}")
    print()
    
    # Ejecutar pipeline
    try:
        run_id = pipeline.run_full_pipeline(
            skip_chunks=args.skip_chunks,
            skip_embeddings=args.skip_embeddings,
            skip_index=args.skip_index
        )
        
        print(f"\n✅ Pipeline completado exitosamente")
        print(f"📊 Run ID: {run_id}")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error ejecutando pipeline: {e}")
        logging.exception("Pipeline falló")
        return 1


def list_runs(args):
    """Lista los últimos runs del pipeline."""
    config = BigQueryVectorConfig()
    tracker = ProgressTracker(config)
    
    print_banner()
    print("📋 Histórico de Runs\n")
    
    runs = tracker.get_all_runs(
        pipeline_name="bigquery_vector_pipeline",
        limit=args.limit
    )
    
    if not runs:
        print("No hay runs registrados")
        return 0
    
    print(f"{'Run ID':<40} {'Inicio':<20} {'Etapas':<10} {'Estado':<15}")
    print("-" * 90)
    
    for run in runs:
        completed = run['completed_stages']
        total = run['total_stages']
        failed = run['failed_stages']
        
        status = "✅ Completo" if completed == total else "❌ Fallido" if failed > 0 else "🔄 En progreso"
        
        print(f"{run['run_id']:<40} {str(run['started_at'])[:19]:<20} {f'{completed}/{total}':<10} {status:<15}")
    
    print()
    return 0


def show_report(args):
    """Muestra reporte detallado de un run."""
    config = BigQueryVectorConfig()
    tracker = ProgressTracker(config)
    
    print_banner()
    
    tracker.print_progress_report(args.run_id)
    
    return 0


def validate_system(args):
    """Valida que el sistema esté configurado correctamente."""
    print_banner()
    print("🔍 Validando Sistema\n")
    
    config = BigQueryVectorConfig()
    
    # Verificar tablas
    from google.cloud import bigquery
    client = bigquery.Client(project=config.PROJECT_ID)
    
    tables_to_check = [
        ("Tabla fuente", config.full_source_table_id),
        ("Tabla chunks", config.full_chunks_table_id),
        ("Tabla embeddings", config.full_embeddings_table_id),
    ]
    
    print("📊 Verificando Tablas:")
    for name, table_id in tables_to_check:
        try:
            table = client.get_table(table_id)
            row_count = table.num_rows
            print(f"   ✅ {name}: {row_count:,} rows")
        except Exception as e:
            print(f"   ❌ {name}: No existe o error")
    
    # Verificar modelo de embeddings
    print("\n🤖 Verificando Modelo de Embeddings:")
    try:
        model_id = f"{config.PROJECT_ID}.{config.DATASET_ID}.gemini_embedding_model"
        model = client.get_model(model_id)
        print(f"   ✅ Modelo: {model.model_type}")
    except Exception as e:
        print(f"   ❌ Modelo no existe")
    
    # Verificar índice vectorial
    print("\n📈 Verificando Índice Vectorial:")
    try:
        # Query para verificar índice
        check_index_sql = f"""
        SELECT COUNT(*) as count
        FROM `{config.PROJECT_ID}.{config.DATASET_ID}.INFORMATION_SCHEMA.VECTOR_INDEXES`
        WHERE table_name = '{config.EMBEDDINGS_TABLE}'
        """
        result = list(client.query(check_index_sql))
        if result and result[0].count > 0:
            print(f"   ✅ Índice vectorial existe")
        else:
            print(f"   ⚠️  Índice vectorial no existe (opcional)")
    except Exception as e:
        print(f"   ⚠️  No se pudo verificar índice")
    
    # Verificar tracking tables
    print("\n📋 Verificando Sistema de Tracking:")
    tracker = ProgressTracker(config)
    tracking_tables = [
        ("Progreso", tracker.PROGRESS_TABLE),
        ("Métricas", tracker.METRICS_TABLE),
        ("Errores", tracker.ERRORS_TABLE),
    ]
    
    for name, table_name in tracking_tables:
        try:
            table_id = f"{config.PROJECT_ID}.{config.DATASET_ID}.{table_name}"
            table = client.get_table(table_id)
            print(f"   ✅ {name}: OK")
        except Exception as e:
            print(f"   ❌ {name}: No existe")
    
    print("\n" + "=" * 80)
    print("✅ Validación completada")
    print("=" * 80)
    
    return 0


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="BigQuery Vector Pipeline - Chunking + Embeddings + Vector Search",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Ejecutar pipeline completo
  %(prog)s
  
  # Ejecutar solo embeddings (chunks ya existen)
  %(prog)s --skip-chunks
  
  # Ver histórico de runs
  %(prog)s --list-runs
  
  # Ver reporte de un run específico
  %(prog)s --report bigquery_vector_pipeline_20250930_143022
  
  # Validar sistema
  %(prog)s --validate
        """
    )
    
    # Opciones de ejecución
    parser.add_argument('--skip-chunks', action='store_true',
                       help='Saltar creación de chunks')
    parser.add_argument('--skip-embeddings', action='store_true',
                       help='Saltar generación de embeddings')
    parser.add_argument('--skip-index', action='store_true',
                       help='Saltar creación de índice vectorial')
    
    # Opciones de reporte
    parser.add_argument('--list-runs', action='store_true',
                       help='Listar histórico de runs')
    parser.add_argument('--limit', type=int, default=10,
                       help='Límite de runs a mostrar (default: 10)')
    parser.add_argument('--report', metavar='RUN_ID',
                       help='Mostrar reporte de un run específico')
    
    # Opciones de validación
    parser.add_argument('--validate', action='store_true',
                       help='Validar configuración del sistema')
    
    # Opciones generales
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Logging detallado')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Ejecutar acción correspondiente
    if args.list_runs:
        return list_runs(args)
    elif args.report:
        return show_report(args)
    elif args.validate:
        return validate_system(args)
    else:
        return run_pipeline(args)


if __name__ == "__main__":
    sys.exit(main())
