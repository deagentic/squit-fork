#!/usr/bin/env python3
"""
Script para análisis avanzado de datos en BigQuery.

Este script proporciona análisis detallado del codebase usando
BigQuery SQL nativo y métricas de calidad de chunks.
"""

import sys
from pathlib import Path
from datetime import datetime

# Agregar directorios al path
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from bigquery_vector import BigQueryVectorConfig
from google.cloud import bigquery


def print_header():
    """Imprime header del script."""
    print("📊 SQUIT - Análisis Avanzado BigQuery")
    print("=" * 60)
    print(f"📅 Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 Objetivo: Análisis profundo del codebase")
    print("🔧 Tecnología: BigQuery Analytics + SQL nativo")
    print()


def analyze_source_data():
    """Analiza los datos fuente antes del chunking."""
    config = BigQueryVectorConfig()
    client = bigquery.Client(project=config.PROJECT_ID)
    
    print("🔍 ANÁLISIS DE DATOS FUENTE")
    print("=" * 40)
    
    source_analysis_sql = f"""
    WITH source_stats AS (
      SELECT 
        object_type,
        server,
        COUNT(*) as object_count,
        AVG(LENGTH(sql_code)) as avg_code_length,
        MIN(LENGTH(sql_code)) as min_code_length,
        MAX(LENGTH(sql_code)) as max_code_length,
        STDDEV(LENGTH(sql_code)) as stddev_code_length,
        
        -- Objetos que necesitarán chunking
        COUNT(CASE WHEN LENGTH(sql_code) > {config.MEGA_OBJECT_THRESHOLD} THEN 1 END) as mega_objects,
        COUNT(CASE WHEN LENGTH(sql_code) > {config.LARGE_OBJECT_THRESHOLD} THEN 1 END) as large_objects,
        COUNT(CASE WHEN LENGTH(sql_code) > {config.MEDIUM_OBJECT_THRESHOLD} THEN 1 END) as medium_objects,
        
        -- Distribución de complejidad
        AVG(
          (LENGTH(sql_code) / 1000) + 
          (ARRAY_LENGTH(REGEXP_EXTRACT_ALL(UPPER(sql_code), r'\\bJOIN\\b')) * 2) +
          (ARRAY_LENGTH(REGEXP_EXTRACT_ALL(UPPER(sql_code), r'\\bSELECT\\b')) * 1)
        ) as avg_complexity
        
      FROM `{config.full_source_table_id}`
      WHERE sql_code IS NOT NULL
      GROUP BY object_type, server
    )
    SELECT 
      object_type,
      server,
      object_count,
      ROUND(avg_code_length, 0) as avg_code_length,
      min_code_length,
      max_code_length,
      ROUND(stddev_code_length, 0) as stddev_code_length,
      mega_objects,
      large_objects,
      medium_objects,
      ROUND(avg_complexity, 2) as avg_complexity
    FROM source_stats
    ORDER BY object_count DESC
    """
    
    try:
        results = list(client.query(source_analysis_sql))
        
        print("📊 ESTADÍSTICAS POR TIPO Y SERVIDOR:")
        print(f"{'Tipo':<12} {'Servidor':<20} {'Objetos':<8} {'Prom':<8} {'Min':<6} {'Max':<10} {'Mega':<5} {'Large':<6} {'Compl':<6}")
        print("-" * 85)
        
        total_objects = 0
        total_mega = 0
        total_large = 0
        
        for row in results:
            total_objects += row.object_count
            total_mega += row.mega_objects
            total_large += row.large_objects
            
            print(f"{row.object_type:<12} {row.server[:19]:<20} {row.object_count:<8} "
                  f"{row.avg_code_length:<8.0f} {row.min_code_length:<6} {row.max_code_length:<10} "
                  f"{row.mega_objects:<5} {row.large_objects:<6} {row.avg_complexity:<6}")
        
        print("-" * 85)
        print(f"📊 RESUMEN TOTAL:")
        print(f"   • Total objetos: {total_objects:,}")
        print(f"   • Objetos mega (>1M chars): {total_mega:,} ({total_mega/total_objects*100:.1f}%)")
        print(f"   • Objetos large (>50K chars): {total_large:,} ({total_large/total_objects*100:.1f}%)")
        
        # Estimación de chunks
        estimated_chunks = total_objects + (total_mega * 50) + (total_large * 5)
        print(f"   • Chunks estimados: ~{estimated_chunks:,}")
        
    except Exception as e:
        print(f"❌ Error analizando datos fuente: {e}")


def analyze_chunking_quality():
    """Analiza la calidad del chunking realizado."""
    config = BigQueryVectorConfig()
    client = bigquery.Client(project=config.PROJECT_ID)
    
    print("\n🧩 ANÁLISIS DE CALIDAD DE CHUNKING")
    print("=" * 45)
    
    # Verificar si existe la tabla de chunks
    try:
        table_ref = client.get_table(config.full_chunks_table_id)
    except:
        print("❌ Tabla de chunks no encontrada. Ejecuta primero: make create-chunks")
        return
    
    quality_analysis_sql = f"""
    WITH chunking_quality AS (
      SELECT 
        chunking_strategy,
        semantic_type,
        business_domain,
        
        -- Estadísticas básicas
        COUNT(*) as total_chunks,
        COUNT(DISTINCT parent_object_id) as unique_objects,
        AVG(chunk_length) as avg_chunk_length,
        MIN(chunk_length) as min_chunk_length,
        MAX(chunk_length) as max_chunk_length,
        STDDEV(chunk_length) as stddev_chunk_length,
        
        -- Distribución de chunks por objeto
        AVG(total_chunks) as avg_chunks_per_object,
        MAX(total_chunks) as max_chunks_per_object,
        
        -- Calidad semántica
        AVG(complexity_score) as avg_complexity,
        AVG(ARRAY_LENGTH(semantic_tags)) as avg_semantic_tags,
        AVG(ARRAY_LENGTH(references_to)) as avg_references,
        
        -- Distribución de tamaños
        COUNT(CASE WHEN chunk_length < {config.MIN_CHUNK_SIZE} THEN 1 END) as too_small_chunks,
        COUNT(CASE WHEN chunk_length > {config.MAX_CHUNK_SIZE} THEN 1 END) as too_large_chunks,
        COUNT(CASE WHEN chunk_length BETWEEN {config.MIN_CHUNK_SIZE} AND {config.MAX_CHUNK_SIZE} THEN 1 END) as optimal_chunks
        
      FROM `{config.full_chunks_table_id}`
      GROUP BY chunking_strategy, semantic_type, business_domain
    )
    SELECT 
      chunking_strategy,
      semantic_type,
      business_domain,
      total_chunks,
      unique_objects,
      ROUND(avg_chunk_length, 0) as avg_chunk_length,
      min_chunk_length,
      max_chunk_length,
      ROUND(avg_chunks_per_object, 1) as avg_chunks_per_object,
      max_chunks_per_object,
      ROUND(avg_complexity, 2) as avg_complexity,
      ROUND(avg_semantic_tags, 1) as avg_semantic_tags,
      too_small_chunks,
      optimal_chunks,
      too_large_chunks,
      ROUND((optimal_chunks / total_chunks) * 100, 1) as optimal_percentage
    FROM chunking_quality
    ORDER BY total_chunks DESC
    """
    
    try:
        results = list(client.query(quality_analysis_sql))
        
        print("📊 CALIDAD POR ESTRATEGIA DE CHUNKING:")
        print(f"{'Estrategia':<15} {'Tipo':<12} {'Dominio':<12} {'Chunks':<7} {'Objs':<5} {'Prom':<6} {'C/O':<4} {'Opt%':<5}")
        print("-" * 75)
        
        total_chunks = 0
        total_optimal = 0
        
        for row in results[:15]:  # Top 15
            total_chunks += row.total_chunks
            total_optimal += row.optimal_chunks
            
            print(f"{row.chunking_strategy[:14]:<15} {row.semantic_type[:11]:<12} "
                  f"{row.business_domain[:11]:<12} {row.total_chunks:<7} {row.unique_objects:<5} "
                  f"{row.avg_chunk_length:<6.0f} {row.avg_chunks_per_object:<4.1f} {row.optimal_percentage:<5.1f}")
        
        print("-" * 75)
        print(f"📊 CALIDAD GENERAL:")
        overall_optimal = (total_optimal / total_chunks) * 100 if total_chunks > 0 else 0
        print(f"   • Chunks en rango óptimo: {overall_optimal:.1f}%")
        print(f"   • Total chunks analizados: {total_chunks:,}")
        
    except Exception as e:
        print(f"❌ Error analizando calidad de chunking: {e}")


def analyze_embedding_coverage():
    """Analiza la cobertura y calidad de embeddings."""
    config = BigQueryVectorConfig()
    client = bigquery.Client(project=config.PROJECT_ID)
    
    print("\n🎯 ANÁLISIS DE COBERTURA DE EMBEDDINGS")
    print("=" * 45)
    
    # Verificar si existe la tabla de embeddings
    try:
        table_ref = client.get_table(config.full_embeddings_table_id)
    except:
        print("❌ Tabla de embeddings no encontrada. Ejecuta primero: make create-chunks")
        return
    
    embedding_analysis_sql = f"""
    WITH embedding_stats AS (
      SELECT 
        semantic_type,
        business_domain,
        COUNT(*) as total_chunks,
        COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) as chunks_with_embeddings,
        COUNT(CASE WHEN embedding IS NULL THEN 1 END) as chunks_without_embeddings,
        AVG(ARRAY_LENGTH(embedding)) as avg_embedding_dimensions,
        AVG(chunk_length) as avg_chunk_length,
        AVG(complexity_score) as avg_complexity
      FROM `{config.full_embeddings_table_id}`
      GROUP BY semantic_type, business_domain
    )
    SELECT 
      semantic_type,
      business_domain,
      total_chunks,
      chunks_with_embeddings,
      chunks_without_embeddings,
      ROUND((chunks_with_embeddings / total_chunks) * 100, 1) as coverage_percentage,
      ROUND(avg_embedding_dimensions, 0) as avg_embedding_dimensions,
      ROUND(avg_chunk_length, 0) as avg_chunk_length,
      ROUND(avg_complexity, 2) as avg_complexity
    FROM embedding_stats
    ORDER BY total_chunks DESC
    """
    
    try:
        results = list(client.query(embedding_analysis_sql))
        
        print("📊 COBERTURA DE EMBEDDINGS:")
        print(f"{'Tipo':<12} {'Dominio':<12} {'Total':<6} {'Con Emb':<7} {'Sin Emb':<7} {'Cob%':<5} {'Dims':<5}")
        print("-" * 65)
        
        total_chunks = 0
        total_with_embeddings = 0
        
        for row in results:
            total_chunks += row.total_chunks
            total_with_embeddings += row.chunks_with_embeddings
            
            print(f"{row.semantic_type[:11]:<12} {row.business_domain[:11]:<12} "
                  f"{row.total_chunks:<6} {row.chunks_with_embeddings:<7} "
                  f"{row.chunks_without_embeddings:<7} {row.coverage_percentage:<5.1f} "
                  f"{row.avg_embedding_dimensions:<5.0f}")
        
        print("-" * 65)
        overall_coverage = (total_with_embeddings / total_chunks) * 100 if total_chunks > 0 else 0
        print(f"📊 COBERTURA GENERAL: {overall_coverage:.1f}%")
        print(f"   • Total chunks: {total_chunks:,}")
        print(f"   • Con embeddings: {total_with_embeddings:,}")
        print(f"   • Sin embeddings: {total_chunks - total_with_embeddings:,}")
        
    except Exception as e:
        print(f"❌ Error analizando embeddings: {e}")


def analyze_search_readiness():
    """Analiza si el sistema está listo para búsquedas."""
    config = BigQueryVectorConfig()
    client = bigquery.Client(project=config.PROJECT_ID)
    
    print("\n🚀 ANÁLISIS DE PREPARACIÓN PARA BÚSQUEDAS")
    print("=" * 50)
    
    # Verificar índices vectoriales
    index_check_sql = f"""
    SELECT 
      index_name,
      table_name,
      index_status,
      coverage_percentage,
      last_refresh_time
    FROM `{config.PROJECT_ID}.{config.DATASET_ID}.INFORMATION_SCHEMA.VECTOR_INDEXES`
    WHERE table_name = '{config.CHUNKS_TABLE}' OR table_name = '{config.EMBEDDINGS_TABLE}'
    """
    
    try:
        index_results = list(client.query(index_check_sql))
        
        print("🔍 ESTADO DE ÍNDICES VECTORIALES:")
        if index_results:
            for row in index_results:
                print(f"  • {row.index_name}")
                print(f"    └─ Tabla: {row.table_name}")
                print(f"    └─ Estado: {row.index_status}")
                print(f"    └─ Cobertura: {row.coverage_percentage:.1f}%")
                print(f"    └─ Última actualización: {row.last_refresh_time}")
        else:
            print("  ❌ No se encontraron índices vectoriales")
            print("  🔧 Ejecuta: make create-chunks para crearlos")
        
        # Estadísticas generales de preparación
        readiness_sql = f"""
        SELECT 
          COUNT(*) as total_embeddings,
          COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) as valid_embeddings,
          COUNT(DISTINCT semantic_type) as semantic_types_covered,
          COUNT(DISTINCT business_domain) as business_domains_covered,
          AVG(complexity_score) as avg_complexity,
          COUNT(DISTINCT parent_object_id) as unique_objects_covered
        FROM `{config.full_embeddings_table_id}`
        WHERE embedding IS NOT NULL
        """
        
        readiness_results = list(client.query(readiness_sql))
        
        if readiness_results:
            stats = readiness_results[0]
            print(f"\n📊 ESTADÍSTICAS DE PREPARACIÓN:")
            print(f"  • Embeddings válidos: {stats.valid_embeddings:,}")
            print(f"  • Objetos únicos cubiertos: {stats.unique_objects_covered:,}")
            print(f"  • Tipos semánticos: {stats.semantic_types_covered}")
            print(f"  • Dominios de negocio: {stats.business_domains_covered}")
            print(f"  • Complejidad promedio: {stats.avg_complexity:.2f}")
            
            # Evaluación de preparación
            readiness_score = 0
            if stats.valid_embeddings > 1000:
                readiness_score += 25
            if stats.unique_objects_covered > 100:
                readiness_score += 25
            if stats.semantic_types_covered >= 5:
                readiness_score += 25
            if len(index_results) > 0:
                readiness_score += 25
            
            print(f"\n🎯 PUNTUACIÓN DE PREPARACIÓN: {readiness_score}/100")
            
            if readiness_score >= 75:
                print("✅ Sistema listo para búsquedas avanzadas!")
                print("🔍 Ejecuta: make search-chunks para probar")
            elif readiness_score >= 50:
                print("⚠️  Sistema parcialmente listo")
                print("🔧 Considera ejecutar: make create-chunks nuevamente")
            else:
                print("❌ Sistema no está listo para búsquedas")
                print("🔧 Ejecuta: make create-chunks primero")
        
    except Exception as e:
        print(f"❌ Error analizando preparación: {e}")


def generate_recommendations():
    """Genera recomendaciones basadas en el análisis."""
    print("\n💡 RECOMENDACIONES DEL SISTEMA")
    print("=" * 40)
    
    recommendations = [
        "🎯 Para objetos mega (>1M chars): Considera chunking manual adicional",
        "📊 Monitorea la calidad de embeddings regularmente",
        "🔍 Usa búsquedas híbridas para mejor precisión",
        "⚡ Actualiza índices vectoriales semanalmente",
        "📈 Analiza patrones de uso para optimizar chunks",
        "🧠 Considera fine-tuning de embeddings para tu dominio",
        "🔧 Implementa cache para búsquedas frecuentes",
        "📋 Documenta queries SQL complejas para reutilización",
    ]
    
    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. {rec}")


def main():
    """Función principal."""
    print_header()
    
    mode = sys.argv[1].lower() if len(sys.argv) > 1 else "all"
    
    if mode in ["all", "source"]:
        analyze_source_data()
    
    if mode in ["all", "chunks"]:
        analyze_chunking_quality()
    
    if mode in ["all", "embeddings"]:
        analyze_embedding_coverage()
    
    if mode in ["all", "readiness"]:
        analyze_search_readiness()
    
    if mode == "all":
        generate_recommendations()
    
    print(f"\n✅ ANÁLISIS COMPLETADO")
    print("=" * 30)
    print("🔍 Otros análisis disponibles:")
    print("  • python3 scripts/bigquery_analyze_data.py source")
    print("  • python3 scripts/bigquery_analyze_data.py chunks")
    print("  • python3 scripts/bigquery_analyze_data.py embeddings")
    print("  • python3 scripts/bigquery_analyze_data.py readiness")


if __name__ == "__main__":
    main()
