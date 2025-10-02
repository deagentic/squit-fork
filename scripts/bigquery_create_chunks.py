#!/usr/bin/env python3
"""
Script para crear chunks inteligentes en BigQuery.

Este script ejecuta el pipeline completo de chunking usando SQL nativo,
optimizado para objetos SQL masivos con embeddings semánticos.
"""

import sys
from pathlib import Path
from datetime import datetime

# Agregar directorios al path
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from bigquery_vector import BigQueryChunkingPipeline, BigQueryVectorConfig


def print_header():
    """Imprime header del script."""
    print("🧠 SQUIT - Chunking Inteligente 100% BigQuery")
    print("=" * 60)
    print(f"📅 Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 Objetivo: Crear chunks semánticamente coherentes")
    print("🔧 Tecnología: BigQuery SQL nativo + Gemini embeddings")
    print()


def main():
    """Función principal."""
    print_header()
    
    try:
        # Inicializar pipeline
        config = BigQueryVectorConfig()
        pipeline = BigQueryChunkingPipeline(config)
        
        print("🔍 Configuración:")
        print(f"   • Proyecto: {config.PROJECT_ID}")
        print(f"   • Dataset: {config.DATASET_ID}")
        print(f"   • Tabla fuente: {config.SOURCE_TABLE}")
        print(f"   • Tabla chunks: {config.CHUNKS_TABLE}")
        print(f"   • Modelo embedding: gemini-embedding-001")
        print()
        
        print("⚠️  IMPORTANTE:")
        print("   • Este proceso corre EN LA NUBE (BigQuery)")
        print("   • Puedes cerrar tu laptop sin problemas")
        print("   • No afecta si pierdes conexión")
        print()
        
        # ETAPA 1: Crear tabla de chunks
        print("🚀 ETAPA 1: Creando chunks inteligentes...")
        print("-" * 50)
        print("⏰ Tiempo estimado: 1-2 horas")
        print("🔄 Ejecutando query en BigQuery...")
        
        chunks_stats = pipeline.create_chunks_table()
        
        print("✅ Chunks creados exitosamente!")
        print(f"   📊 Total chunks: {chunks_stats.get('total_chunks', 0):,}")
        print(f"   📄 Objetos únicos: {chunks_stats.get('unique_objects', 0):,}")
        print(f"   📏 Tamaño promedio: {chunks_stats.get('avg_chunk_length', 0):.0f} chars")
        print(f"   🧩 Chunks por objeto: {chunks_stats.get('avg_chunks_per_object', 0):.1f}")
        print()
        
        # ETAPA 2: Generar embeddings
        print("🚀 ETAPA 2: Generando embeddings con gemini-embedding-001...")
        print("-" * 50)
        print("⏰ Tiempo estimado: 3-5 horas")
        print("💰 Costo estimado: $30-60 USD")
        print("🔄 Ejecutando query en BigQuery...")
        
        embeddings_stats = pipeline.create_embeddings_table()
        
        print("✅ Embeddings generados exitosamente!")
        print(f"   🎯 Total embeddings: {embeddings_stats.get('total_embeddings', 0):,}")
        print(f"   📄 Objetos con embeddings: {embeddings_stats.get('unique_objects_with_embeddings', 0):,}")
        print(f"   📐 Dimensiones: {embeddings_stats.get('avg_embedding_dimensions', 0):.0f}")
        print()
        
        # ETAPA 3: Crear índice vectorial
        print("🚀 ETAPA 3: Creando índice vectorial...")
        print("-" * 50)
        
        index_stats = pipeline.create_vector_index()
        
        if index_stats.get('status') == 'created':
            print("✅ Índice vectorial creado!")
            print(f"   🔍 Nombre: {index_stats.get('index_name')}")
        else:
            print(f"ℹ️  Índice: {index_stats.get('status')}")
            print(f"   💡 {index_stats.get('recommendation', '')}")
        print()
        
        # ETAPA 4: Reporte final
        print("📋 REPORTE FINAL")
        print("=" * 60)
        
        report = pipeline.get_chunking_report()
        summary = report.get('summary', {})
        
        print("🎯 RESUMEN:")
        print(f"   • Total chunks: {summary.get('total_chunks', 0):,}")
        print(f"   • Objetos: {summary.get('unique_objects', 0):,}")
        print(f"   • Complejidad promedio: {summary.get('avg_complexity', 0):.2f}")
        
        print(f"\n✅ PIPELINE COMPLETADO")
        print("=" * 60)
        print("🔍 Próximos pasos:")
        print("   • make search-chunks      # Probar búsquedas")
        print("   • make search-interactive # Modo interactivo")
        print("   • make analyze-patterns   # Análisis avanzado")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\n🔧 SOLUCIÓN:")
        print("   • Verifica que el modelo gemini_embedding_model exista")
        print("   • Verifica permisos de Vertex AI")
        print("   • El query seguirá corriendo en BigQuery aunque falle aquí")
        print(f"\n📊 Monitorear manualmente:")
        print("   https://console.cloud.google.com/bigquery?project=dfor-prj-dev")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
