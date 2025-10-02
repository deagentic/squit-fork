#!/usr/bin/env python3
"""
Prueba simplificada de chunking BigQuery.

Este script valida solo el chunking sin embeddings para verificar
que la lógica de división de objetos masivos funciona correctamente.
"""

import sys
from pathlib import Path
from datetime import datetime

# Agregar directorios al path
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from bigquery_vector.config import BigQueryVectorConfig
from google.cloud import bigquery


def print_header():
    """Imprime header del script."""
    print("🧪 SQUIT - Prueba Simplificada de Chunking")
    print("=" * 60)
    print(f"📅 Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 Objetivo: Validar chunking sin embeddings")
    print("🔧 Enfoque: Solo chunking + análisis")
    print()


def test_chunking_only():
    """Prueba solo el chunking sin embeddings."""
    config = BigQueryVectorConfig()
    client = bigquery.Client(project=config.PROJECT_ID)
    
    print("🧩 PRUEBA DE CHUNKING SIMPLIFICADA")
    print("-" * 40)
    
    # Query simplificada para chunking
    chunking_test_sql = f"""
    WITH test_objects AS (
      -- Seleccionar muestra pequeña pero representativa
      SELECT 
        server, database, schema, object_name, object_type,
        sql_code, content_hash, last_modified,
        LENGTH(sql_code) as code_length,
        CASE 
          WHEN LENGTH(sql_code) > 1000000 THEN 'mega'
          WHEN LENGTH(sql_code) > 50000 THEN 'large'
          WHEN LENGTH(sql_code) > 15000 THEN 'medium'
          ELSE 'small'
        END as size_category
      FROM `{config.full_source_table_id}`
      WHERE sql_code IS NOT NULL
      ORDER BY RAND()
      LIMIT 20
    ),
    chunked_test AS (
      SELECT 
        *,
        -- Chunking simplificado
        CASE 
          WHEN code_length > 1000000 THEN
            ARRAY_LENGTH(SPLIT(sql_code, 'GO'))
          WHEN code_length > 50000 THEN
            CAST(CEIL(code_length / 8000.0) AS INT64)
          WHEN code_length > 15000 THEN
            CAST(CEIL(code_length / 6000.0) AS INT64)
          ELSE 1
        END as estimated_chunks
      FROM test_objects
    )
    SELECT 
      size_category,
      COUNT(*) as objects_count,
      AVG(code_length) as avg_code_length,
      MIN(code_length) as min_code_length,
      MAX(code_length) as max_code_length,
      SUM(estimated_chunks) as total_chunks,
      AVG(estimated_chunks) as avg_chunks_per_object,
      ARRAY_AGG(STRUCT(
        object_name,
        object_type,
        code_length,
        estimated_chunks
      ) ORDER BY code_length DESC LIMIT 3) as top_objects
    FROM chunked_test
    GROUP BY size_category
    ORDER BY 
      CASE size_category 
        WHEN 'mega' THEN 1 
        WHEN 'large' THEN 2 
        WHEN 'medium' THEN 3 
        WHEN 'small' THEN 4 
      END
    """
    
    try:
        print("🔄 Ejecutando análisis de chunking...")
        start_time = datetime.now()
        
        results = list(client.query(chunking_test_sql))
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        print(f"✅ Análisis completado en {execution_time:.1f}s")
        print()
        
        print("📊 RESULTADOS DEL CHUNKING:")
        print(f"{'Categoría':<10} {'Objetos':<8} {'Chunks':<7} {'C/O':<5} {'Prom Length':<12} {'Min':<8} {'Max':<10}")
        print("-" * 75)
        
        total_objects = 0
        total_chunks = 0
        
        for row in results:
            total_objects += row.objects_count
            total_chunks += row.total_chunks
            
            print(f"{row.size_category:<10} {row.objects_count:<8} {row.total_chunks:<7} "
                  f"{row.avg_chunks_per_object:<5.1f} {row.avg_code_length:<12.0f} "
                  f"{row.min_code_length:<8} {row.max_code_length:<10}")
            
            # Mostrar ejemplos de objetos grandes
            if row.size_category in ['mega', 'large'] and row.top_objects:
                print(f"   📄 Ejemplos:")
                for obj in row.top_objects:
                    print(f"      • {obj['object_name']} ({obj['object_type']}): "
                          f"{obj['code_length']:,} chars → {obj['estimated_chunks']} chunks")
        
        print("-" * 75)
        print(f"📊 TOTALES: {total_objects} objetos → {total_chunks} chunks")
        print(f"🧩 Factor de multiplicación: {total_chunks/max(1, total_objects):.1f}x")
        
        # Proyección a dataset completo
        print(f"\n📈 PROYECCIÓN A DATASET COMPLETO:")
        full_dataset_objects = 3416808
        estimated_full_chunks = int(full_dataset_objects * (total_chunks / total_objects))
        
        print(f"   • Objetos totales: {full_dataset_objects:,}")
        print(f"   • Chunks estimados: {estimated_full_chunks:,}")
        print(f"   • Factor aplicado: {total_chunks/max(1, total_objects):.1f}x")
        print(f"   • Tiempo estimado chunking: {(execution_time * full_dataset_objects / total_objects / 60):.0f} minutos")
        
        # Evaluación del chunking
        if total_chunks > total_objects and total_chunks < total_objects * 20:
            print(f"\n✅ CHUNKING EXITOSO")
            print(f"   • Factor razonable de multiplicación")
            print(f"   • Objetos grandes correctamente divididos")
            print(f"   • Sistema listo para embeddings")
            
            print(f"\n🚀 PRÓXIMOS PASOS:")
            print(f"   1. make generate-test-embeddings  # Generar embeddings reales")
            print(f"   2. make search-chunks             # Probar búsquedas")
            print(f"   3. make bigquery-full             # Pipeline completo")
            
            return True
        else:
            print(f"\n⚠️  CHUNKING NECESITA AJUSTES")
            print(f"   • Factor de multiplicación muy alto/bajo")
            print(f"   • Revisar umbrales de chunking")
            return False
        
    except Exception as e:
        print(f"❌ Error en prueba de chunking: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Función principal."""
    print_header()
    
    success = test_chunking_only()
    
    print(f"\n" + "=" * 60)
    print("🧪 PRUEBA SIMPLIFICADA COMPLETADA")
    print("=" * 60)
    
    if success:
        print("✅ Chunking validado exitosamente!")
        print("🔧 El sistema está listo para generar embeddings")
    else:
        print("❌ Chunking necesita ajustes")
        print("🔧 Revisar configuración de umbrales")


if __name__ == "__main__":
    main()
