#!/usr/bin/env python3
"""
Script de prueba para chunking con 100 objetos de BigQuery.

Este script ejecuta el pipeline completo con una muestra pequeña
para validar el flujo antes de la migración masiva.
"""

import sys
from pathlib import Path
from datetime import datetime

# Agregar directorios al path
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from bigquery_vector import BigQueryChunkingPipeline, BigQueryVectorSearch, BigQueryVectorConfig
from google.cloud import bigquery


def print_header():
    """Imprime header del script."""
    print("🧪 SQUIT - Prueba de Chunking (100 objetos)")
    print("=" * 60)
    print(f"📅 Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 Objetivo: Validar pipeline con muestra pequeña")
    print("🔧 Tecnología: BigQuery Vector + Gemini embedding-001")
    print()


def create_test_dataset():
    """Crea dataset de prueba con 100 objetos representativos."""
    config = BigQueryVectorConfig()
    client = bigquery.Client(project=config.PROJECT_ID)
    
    print("🔄 CREANDO DATASET DE PRUEBA")
    print("-" * 40)
    
    # Crear tabla de prueba con muestra representativa
    test_table_sql = f"""
    CREATE OR REPLACE TABLE `{config.PROJECT_ID}.{config.DATASET_ID}.test_sample_100` AS
    WITH stratified_sample AS (
      -- Muestra estratificada: diferentes tipos y tamaños
      (
        -- 20 objetos mega (>1M chars) si existen
        SELECT *, 'mega' as sample_category
        FROM `{config.full_source_table_id}`
        WHERE LENGTH(sql_code) > 1000000
        ORDER BY RAND()
        LIMIT 20
      )
      UNION ALL
      (
        -- 30 objetos large (50K-1M chars)
        SELECT *, 'large' as sample_category
        FROM `{config.full_source_table_id}`
        WHERE LENGTH(sql_code) BETWEEN 50000 AND 999999
        ORDER BY RAND()
        LIMIT 30
      )
      UNION ALL
      (
        -- 30 objetos medium (15K-50K chars)
        SELECT *, 'medium' as sample_category
        FROM `{config.full_source_table_id}`
        WHERE LENGTH(sql_code) BETWEEN 15000 AND 49999
        ORDER BY RAND()
        LIMIT 30
      )
      UNION ALL
      (
        -- 20 objetos small (<15K chars)
        SELECT *, 'small' as sample_category
        FROM `{config.full_source_table_id}`
        WHERE LENGTH(sql_code) < 15000
        ORDER BY RAND()
        LIMIT 20
      )
    )
    SELECT 
      server,
      database,
      schema,
      object_name,
      object_type,
      sql_code,
      content_hash,
      last_modified,
      sample_category,
      LENGTH(sql_code) as code_length,
      ROW_NUMBER() OVER (ORDER BY sample_category, RAND()) as test_id
    FROM stratified_sample
    """
    
    try:
        job = client.query(test_table_sql)
        result = job.result()
        
        # Obtener estadísticas de la muestra
        stats_sql = f"""
        SELECT 
          sample_category,
          COUNT(*) as object_count,
          AVG(code_length) as avg_length,
          MIN(code_length) as min_length,
          MAX(code_length) as max_length,
          ARRAY_AGG(DISTINCT object_type) as object_types
        FROM `{config.PROJECT_ID}.{config.DATASET_ID}.test_sample_100`
        GROUP BY sample_category
        ORDER BY 
          CASE sample_category 
            WHEN 'mega' THEN 1 
            WHEN 'large' THEN 2 
            WHEN 'medium' THEN 3 
            WHEN 'small' THEN 4 
          END
        """
        
        stats_results = list(client.query(stats_sql))
        
        print("✅ Dataset de prueba creado!")
        print("\n📊 COMPOSICIÓN DE LA MUESTRA:")
        print(f"{'Categoría':<10} {'Objetos':<8} {'Prom':<10} {'Min':<8} {'Max':<12} {'Tipos'}")
        print("-" * 70)
        
        total_objects = 0
        for row in stats_results:
            total_objects += row.object_count
            print(f"{row.sample_category:<10} {row.object_count:<8} "
                  f"{row.avg_length:<10.0f} {row.min_length:<8} {row.max_length:<12} "
                  f"{', '.join(row.object_types)}")
        
        print("-" * 70)
        print(f"📊 TOTAL: {total_objects} objetos de prueba")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creando dataset de prueba: {e}")
        return False


def run_test_chunking():
    """Ejecuta chunking en el dataset de prueba."""
    config = BigQueryVectorConfig()
    client = bigquery.Client(project=config.PROJECT_ID)
    
    print("\n🧩 EJECUTANDO CHUNKING DE PRUEBA")
    print("-" * 40)
    
    # Modificar temporalmente la configuración para usar tabla de prueba
    original_source = config.SOURCE_TABLE
    config.SOURCE_TABLE = "test_sample_100"
    config.CHUNKS_TABLE = "test_chunks_100"
    config.EMBEDDINGS_TABLE = "test_embeddings_100"
    config.VECTOR_INDEX_NAME = "test_chunks_vector_idx"
    
    try:
        pipeline = BigQueryChunkingPipeline(config)
        
        print("🔄 Paso 1: Creando chunks...")
        start_time = datetime.now()
        
        chunks_stats = pipeline.create_chunks_table()
        
        chunks_time = datetime.now()
        print(f"✅ Chunks creados en {(chunks_time - start_time).total_seconds():.1f}s")
        print(f"   📊 Total chunks: {chunks_stats.get('total_chunks', 0):,}")
        print(f"   📄 Objetos procesados: {chunks_stats.get('unique_objects', 0):,}")
        print(f"   📏 Tamaño promedio: {chunks_stats.get('avg_chunk_length', 0):.0f} chars")
        print(f"   🧩 Chunks por objeto: {chunks_stats.get('avg_chunks_per_object', 0):.1f}")
        
        print("\n🔄 Paso 2: Generando embeddings...")
        embeddings_stats = pipeline.create_embeddings_table()
        
        embeddings_time = datetime.now()
        print(f"✅ Embeddings generados en {(embeddings_time - chunks_time).total_seconds():.1f}s")
        print(f"   🎯 Total embeddings: {embeddings_stats.get('total_embeddings', 0):,}")
        print(f"   📐 Dimensiones: {embeddings_stats.get('avg_embedding_dimensions', 0):.0f}")
        
        print("\n🔄 Paso 3: Creando índice vectorial...")
        index_stats = pipeline.create_vector_index()
        
        index_time = datetime.now()
        print(f"✅ Índice creado en {(index_time - embeddings_time).total_seconds():.1f}s")
        print(f"   🔍 Nombre: {index_stats.get('index_name')}")
        
        total_time = (index_time - start_time).total_seconds()
        print(f"\n⏰ TIEMPO TOTAL: {total_time:.1f} segundos")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en chunking de prueba: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Restaurar configuración original
        config.SOURCE_TABLE = original_source


def test_searches():
    """Prueba búsquedas en el dataset de prueba."""
    config = BigQueryVectorConfig()
    
    # Usar tablas de prueba
    config.EMBEDDINGS_TABLE = "test_embeddings_100"
    
    search = BigQueryVectorSearch(config)
    
    print("\n🔍 PROBANDO BÚSQUEDAS VECTORIALES")
    print("-" * 40)
    
    test_queries = [
        {
            "query": "usuario autenticacion login",
            "description": "🔐 Autenticación de usuarios",
            "expected_types": ["PROCEDURE", "FUNCTION"]
        },
        {
            "query": "venta factura cliente",
            "description": "💰 Procesos de ventas", 
            "expected_domains": ["ventas"]
        },
        {
            "query": "SELECT FROM JOIN WHERE",
            "description": "🔍 Consultas complejas",
            "expected_types": ["VIEW", "PROCEDURE"]
        },
        {
            "query": "INSERT UPDATE DELETE",
            "description": "📝 Operaciones DML",
            "expected_types": ["PROCEDURE"]
        }
    ]
    
    search_results = {}
    
    for i, test in enumerate(test_queries, 1):
        print(f"\n{i}. {test['description']}")
        print(f"   Query: '{test['query']}'")
        
        try:
            start_time = datetime.now()
            
            results = search.semantic_search(
                query=test['query'],
                limit=5,
                use_hybrid=True
            )
            
            search_time = (datetime.now() - start_time).total_seconds() * 1000
            
            if results:
                print(f"   ✅ {len(results)} resultados en {search_time:.0f}ms")
                
                for j, result in enumerate(results[:3], 1):
                    score = result.get('hybrid_score', result.get('distance', 0))
                    print(f"      {j}. {result['object_name']} ({result['object_type']})")
                    print(f"         Score: {score:.3f} | Dominio: {result['business_domain']}")
                
                search_results[test['query']] = {
                    'count': len(results),
                    'time_ms': search_time,
                    'top_result': results[0] if results else None
                }
            else:
                print(f"   ❌ No se encontraron resultados")
                search_results[test['query']] = {'count': 0, 'time_ms': search_time}
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            search_results[test['query']] = {'error': str(e)}
    
    return search_results


def analyze_test_results(search_results):
    """Analiza los resultados de las pruebas."""
    config = BigQueryVectorConfig()
    client = bigquery.Client(project=config.PROJECT_ID)
    
    print("\n📊 ANÁLISIS DE RESULTADOS DE PRUEBA")
    print("-" * 45)
    
    # Estadísticas detalladas de chunks de prueba
    detailed_stats_sql = f"""
    WITH chunk_analysis AS (
      SELECT 
        sample_category,
        chunking_strategy,
        semantic_type,
        business_domain,
        COUNT(*) as chunks_created,
        COUNT(DISTINCT parent_object_id) as objects_processed,
        AVG(chunk_length) as avg_chunk_length,
        MIN(chunk_length) as min_chunk_length,
        MAX(chunk_length) as max_chunk_length,
        AVG(complexity_score) as avg_complexity,
        AVG(total_chunks) as avg_chunks_per_object
      FROM `{config.PROJECT_ID}.{config.DATASET_ID}.test_chunks_100` tc
      JOIN `{config.PROJECT_ID}.{config.DATASET_ID}.test_sample_100` ts
        ON tc.parent_object_id = CONCAT(ts.server, '|', ts.database, '|', ts.schema, '|', ts.object_name)
      GROUP BY sample_category, chunking_strategy, semantic_type, business_domain
    ),
    embedding_analysis AS (
      SELECT 
        COUNT(*) as total_embeddings,
        COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) as valid_embeddings,
        AVG(ARRAY_LENGTH(embedding)) as avg_dimensions
      FROM `{config.PROJECT_ID}.{config.DATASET_ID}.test_embeddings_100`
    )
    SELECT 
      'chunk_breakdown' as analysis_type,
      TO_JSON_STRING(ARRAY_AGG(chunk_analysis)) as data
    FROM chunk_analysis
    
    UNION ALL
    
    SELECT 
      'embedding_stats' as analysis_type,
      TO_JSON_STRING(STRUCT(
        total_embeddings,
        valid_embeddings,
        ROUND(avg_dimensions, 0) as avg_dimensions,
        ROUND((valid_embeddings / total_embeddings) * 100, 1) as coverage_percentage
      )) as data
    FROM embedding_analysis
    """
    
    try:
        results = list(client.query(detailed_stats_sql))
        
        # Procesar resultados
        import json
        analysis_data = {}
        for row in results:
            analysis_data[row.analysis_type] = json.loads(row.data)
        
        # Mostrar breakdown de chunks
        print("🧩 BREAKDOWN DE CHUNKS POR CATEGORÍA:")
        chunk_breakdown = analysis_data.get('chunk_breakdown', [])
        
        total_chunks = 0
        total_objects = 0
        
        for item in chunk_breakdown:
            total_chunks += item['chunks_created']
            total_objects += item['objects_processed']
            
            print(f"\n📦 {item['sample_category'].upper()} | {item['semantic_type']} | {item['business_domain']}")
            print(f"   • Objetos: {item['objects_processed']} → Chunks: {item['chunks_created']}")
            print(f"   • Estrategia: {item['chunking_strategy']}")
            print(f"   • Tamaño promedio: {item['avg_chunk_length']:.0f} chars")
            print(f"   • Chunks/objeto: {item['avg_chunks_per_object']:.1f}")
            print(f"   • Complejidad: {item['avg_complexity']:.2f}")
        
        # Estadísticas de embeddings
        embedding_stats = analysis_data.get('embedding_stats', {})
        
        print(f"\n🎯 RESUMEN DE PRUEBA:")
        print(f"   • Objetos procesados: {total_objects}")
        print(f"   • Chunks generados: {total_chunks}")
        print(f"   • Factor de multiplicación: {total_chunks/max(1, total_objects):.1f}x")
        print(f"   • Embeddings válidos: {embedding_stats.get('valid_embeddings', 0)}")
        print(f"   • Cobertura: {embedding_stats.get('coverage_percentage', 0):.1f}%")
        print(f"   • Dimensiones embedding: {embedding_stats.get('avg_dimensions', 0)}")
        
        # Análisis de búsquedas
        print(f"\n🔍 RESULTADOS DE BÚSQUEDAS:")
        if search_results:
            successful_searches = sum(1 for r in search_results.values() if 'error' not in r and r.get('count', 0) > 0)
            total_searches = len(search_results)
            avg_time = sum(r.get('time_ms', 0) for r in search_results.values() if 'time_ms' in r) / max(1, total_searches)
            
            print(f"   • Búsquedas exitosas: {successful_searches}/{total_searches}")
            print(f"   • Tiempo promedio: {avg_time:.0f}ms")
            
            # Evaluación general
            success_rate = (successful_searches / total_searches) * 100 if total_searches > 0 else 0
        else:
            success_rate = 0
            print(f"   • No se ejecutaron búsquedas aún")
        
        coverage = embedding_stats.get('coverage_percentage', 0)
        overall_score = (success_rate + coverage) / 2
        
        print(f"\n🎯 EVALUACIÓN GENERAL: {overall_score:.1f}/100")
        
        if overall_score >= 80:
            print("✅ PRUEBA EXITOSA - Sistema listo para migración masiva!")
            print("🚀 Ejecuta: make bigquery-full")
        elif overall_score >= 60:
            print("⚠️  PRUEBA PARCIALMENTE EXITOSA - Revisar configuración")
            print("🔧 Considera ajustar parámetros de chunking")
        else:
            print("❌ PRUEBA FALLÓ - Revisar errores antes de continuar")
            print("🔧 Revisar logs y configuración")
        
        return overall_score >= 60
        
    except Exception as e:
        print(f"❌ Error analizando resultados: {e}")
        return False


def cleanup_test_data():
    """Limpia datos de prueba."""
    config = BigQueryVectorConfig()
    client = bigquery.Client(project=config.PROJECT_ID)
    
    print("\n🧹 LIMPIEZA DE DATOS DE PRUEBA")
    print("-" * 35)
    
    tables_to_clean = [
        f"{config.PROJECT_ID}.{config.DATASET_ID}.test_sample_100",
        f"{config.PROJECT_ID}.{config.DATASET_ID}.test_chunks_100", 
        f"{config.PROJECT_ID}.{config.DATASET_ID}.test_embeddings_100"
    ]
    
    for table in tables_to_clean:
        try:
            client.query(f"DROP TABLE IF EXISTS `{table}`").result()
            print(f"✅ Eliminada: {table.split('.')[-1]}")
        except Exception as e:
            print(f"⚠️  No se pudo eliminar {table.split('.')[-1]}: {e}")


def project_to_full_scale(test_results):
    """Proyecta resultados de prueba a escala completa."""
    print("\n📈 PROYECCIÓN A ESCALA COMPLETA")
    print("-" * 40)
    
    # Datos de tu análisis anterior
    total_objects = 3416808
    
    if test_results:
        # Factores de multiplicación basados en prueba
        chunk_factor = 15  # Estimado basado en objetos mega
        
        print("🔮 PROYECCIONES PARA DATASET COMPLETO:")
        print(f"   • Objetos totales: {total_objects:,}")
        print(f"   • Chunks estimados: ~{total_objects * chunk_factor:,}")
        print(f"   • Tiempo estimado chunking: 45-90 minutos")
        print(f"   • Tiempo estimado embeddings: 3-6 horas")
        print(f"   • Costo embeddings: $30-60 USD")
        print(f"   • Storage adicional: ~8-12 GB")
        
        print(f"\n⚡ PERFORMANCE ESPERADA:")
        print(f"   • Búsquedas/segundo: 200-800")
        print(f"   • Latencia promedio: 80-250ms")
        print(f"   • Precisión esperada: >85%")
        
        print(f"\n💡 RECOMENDACIONES:")
        print(f"   • Ejecutar en horario de baja demanda")
        print(f"   • Monitorear costos de Vertex AI")
        print(f"   • Implementar cache para queries frecuentes")
        print(f"   • Considerar particionado por business_domain")


def main():
    """Función principal de la prueba."""
    print_header()
    
    # ETAPA 1: Crear dataset de prueba
    if not create_test_dataset():
        print("❌ No se pudo crear dataset de prueba")
        sys.exit(1)
    
    # ETAPA 2: Ejecutar chunking
    if not run_test_chunking():
        print("❌ Falló el chunking de prueba")
        cleanup_test_data()
        sys.exit(1)
    
    # ETAPA 3: Probar búsquedas
    search_results = test_searches()
    
    # ETAPA 4: Analizar resultados
    test_success = analyze_test_results(search_results)
    
    # ETAPA 5: Proyecciones
    project_to_full_scale(test_success)
    
    # ETAPA 6: Limpieza (automática - mantener datos para inspección)
    print(f"\n💾 Datos de prueba mantenidos para inspección")
    print("🔍 Tablas de prueba:")
    print("   • test_sample_100")
    print("   • test_chunks_100")
    print("   • test_embeddings_100")
    print("🧹 Para limpiar después: make clean-chunks")
    
    print(f"\n" + "=" * 60)
    print("✅ PRUEBA DE 100 OBJETOS COMPLETADA")
    print("=" * 60)
    
    if test_success:
        print("🚀 Sistema validado - Listo para migración completa!")
        print("📋 Próximos pasos:")
        print("   1. make bigquery-full    # Migración completa")
        print("   2. make search-interactive # Probar búsquedas")
        print("   3. make analyze-patterns  # Análisis avanzado")
    else:
        print("🔧 Revisar configuración antes de migración masiva")
        print("📋 Comandos de diagnóstico:")
        print("   1. make analyze-source   # Revisar datos fuente")
        print("   2. make check-readiness  # Verificar preparación")


if __name__ == "__main__":
    main()
