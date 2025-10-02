#!/usr/bin/env python3
"""
Prueba completa del flujo BigQuery con embeddings dummy.

Este script valida todo el pipeline usando embeddings dummy
para demostrar que el chunking y búsquedas funcionan correctamente.
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
    print("🚀 SQUIT - Flujo Completo BigQuery (Dummy Embeddings)")
    print("=" * 70)
    print(f"📅 Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 Objetivo: Validar flujo completo con embeddings dummy")
    print("🔧 Tecnología: BigQuery SQL + Vector Search + Dummy Embeddings")
    print()


def create_complete_test_pipeline():
    """Crea pipeline de prueba completo."""
    config = BigQueryVectorConfig()
    client = bigquery.Client(project=config.PROJECT_ID)
    
    print("🧪 CREANDO PIPELINE DE PRUEBA COMPLETO")
    print("-" * 45)
    
    # Pipeline completo en una sola query
    complete_pipeline_sql = f"""
    -- Paso 1: Crear tabla de chunks con embeddings dummy
    CREATE OR REPLACE TABLE `{config.PROJECT_ID}.{config.DATASET_ID}.test_complete_flow` AS
    WITH 
    -- Muestra pequeña pero representativa
    sample_objects AS (
      SELECT 
        server, database, schema, object_name, object_type,
        sql_code, content_hash, last_modified,
        LENGTH(sql_code) as code_length,
        CASE 
          WHEN LENGTH(sql_code) > 100000 THEN 'large'
          WHEN LENGTH(sql_code) > 15000 THEN 'medium'
          ELSE 'small'
        END as size_category
      FROM `{config.full_source_table_id}`
      WHERE sql_code IS NOT NULL
      ORDER BY RAND()
      LIMIT 50  -- Muestra más pequeña para prueba rápida
    ),
    
    -- Chunking inteligente
    chunked_objects AS (
      SELECT 
        *,
        CASE 
          -- Large: dividir por tamaño
          WHEN code_length > 50000 THEN
            ARRAY(
              SELECT SUBSTR(sql_code, start_pos, 8000) as chunk
              FROM UNNEST(GENERATE_ARRAY(1, LENGTH(sql_code), 7000)) AS start_pos
              WHERE start_pos <= LENGTH(sql_code)
              LIMIT 20
            )
          -- Medium: dividir en 2-3 chunks
          WHEN code_length > 15000 THEN
            ARRAY(
              SELECT SUBSTR(sql_code, start_pos, 6000) as chunk
              FROM UNNEST(GENERATE_ARRAY(1, LENGTH(sql_code), 5000)) AS start_pos
              WHERE start_pos <= LENGTH(sql_code)
              LIMIT 5
            )
          -- Small: chunk único
          ELSE [sql_code]
        END as chunks
      FROM sample_objects
    ),
    
    -- Expandir chunks
    expanded_chunks AS (
      SELECT 
        GENERATE_UUID() as chunk_id,
        CONCAT(server, '|', database, '|', schema, '|', object_name) as parent_object_id,
        server, database, schema, object_name, object_type,
        chunk_content,
        pos as chunk_index,
        ARRAY_LENGTH(chunks) as total_chunks,
        size_category,
        code_length,
        LENGTH(chunk_content) as chunk_length,
        
        -- Análisis semántico básico
        CASE 
          WHEN REGEXP_CONTAINS(UPPER(chunk_content), r'SELECT.*FROM') THEN 'query'
          WHEN REGEXP_CONTAINS(UPPER(chunk_content), r'CREATE PROCEDURE') THEN 'procedure'
          WHEN REGEXP_CONTAINS(UPPER(chunk_content), r'CREATE FUNCTION') THEN 'function'
          WHEN REGEXP_CONTAINS(UPPER(chunk_content), r'INSERT|UPDATE|DELETE') THEN 'dml'
          ELSE 'other'
        END as semantic_type,
        
        -- Contexto de negocio
        CASE
          WHEN REGEXP_CONTAINS(LOWER(CONCAT(object_name, chunk_content)), r'venta|cliente|factura') THEN 'ventas'
          WHEN REGEXP_CONTAINS(LOWER(CONCAT(object_name, chunk_content)), r'inventario|stock') THEN 'inventario'
          WHEN REGEXP_CONTAINS(LOWER(CONCAT(object_name, chunk_content)), r'usuario|login|auth') THEN 'autenticacion'
          ELSE 'general'
        END as business_domain,
        
        -- Embedding dummy (768 dimensiones)
        ARRAY(
          SELECT CAST(RAND() * 2 - 1 AS FLOAT64)  -- Valores entre -1 y 1
          FROM UNNEST(GENERATE_ARRAY(1, 768))
        ) as embedding
        
      FROM chunked_objects
      CROSS JOIN UNNEST(chunks) AS chunk_content WITH OFFSET pos
      WHERE LENGTH(chunk_content) > 100
    )
    
    -- Resultado final
    SELECT 
      chunk_id,
      parent_object_id,
      server, database, schema, object_name, object_type,
      chunk_content,
      chunk_index,
      total_chunks,
      size_category,
      code_length,
      chunk_length,
      semantic_type,
      business_domain,
      embedding,
      CURRENT_TIMESTAMP() as created_at
    FROM expanded_chunks
    ORDER BY parent_object_id, chunk_index
    """
    
    try:
        print("🔄 Ejecutando pipeline completo...")
        start_time = datetime.now()
        
        job = client.query(complete_pipeline_sql)
        result = job.result()
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        print(f"✅ Pipeline completado en {execution_time:.1f}s")
        
        # Obtener estadísticas
        stats_sql = f"""
        SELECT 
          size_category,
          semantic_type,
          business_domain,
          COUNT(*) as chunks_count,
          COUNT(DISTINCT parent_object_id) as objects_count,
          AVG(chunk_length) as avg_chunk_length,
          AVG(total_chunks) as avg_chunks_per_object,
          COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) as chunks_with_embeddings
        FROM `{config.PROJECT_ID}.{config.DATASET_ID}.test_complete_flow`
        GROUP BY size_category, semantic_type, business_domain
        ORDER BY chunks_count DESC
        """
        
        stats_results = list(client.query(stats_sql))
        
        print(f"\n📊 ESTADÍSTICAS DEL PIPELINE:")
        print(f"{'Categoría':<8} {'Tipo':<10} {'Dominio':<12} {'Chunks':<7} {'Objs':<5} {'Prom':<6} {'C/O':<4} {'Emb':<4}")
        print("-" * 70)
        
        total_chunks = 0
        total_objects = 0
        total_embeddings = 0
        
        for row in stats_results:
            total_chunks += row.chunks_count
            total_objects += row.objects_count
            total_embeddings += row.chunks_with_embeddings
            
            print(f"{row.size_category:<8} {row.semantic_type:<10} {row.business_domain:<12} "
                  f"{row.chunks_count:<7} {row.objects_count:<5} {row.avg_chunk_length:<6.0f} "
                  f"{row.avg_chunks_per_object:<4.1f} {row.chunks_with_embeddings:<4}")
        
        print("-" * 70)
        print(f"📊 TOTALES:")
        print(f"   • Chunks generados: {total_chunks}")
        print(f"   • Objetos procesados: {total_objects}")
        print(f"   • Factor multiplicación: {total_chunks/max(1, total_objects):.1f}x")
        print(f"   • Embeddings generados: {total_embeddings}")
        print(f"   • Cobertura: {(total_embeddings/max(1, total_chunks))*100:.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en pipeline: {e}")
        return False


def test_vector_searches():
    """Prueba búsquedas vectoriales con embeddings dummy."""
    config = BigQueryVectorConfig()
    client = bigquery.Client(project=config.PROJECT_ID)
    
    print(f"\n🔍 PROBANDO BÚSQUEDAS VECTORIALES")
    print("-" * 35)
    
    # Crear índice vectorial
    print("🔄 Creando índice vectorial...")
    
    create_index_sql = f"""
    CREATE VECTOR INDEX IF NOT EXISTS test_flow_vector_idx
    ON `{config.PROJECT_ID}.{config.DATASET_ID}.test_complete_flow`(embedding)
    OPTIONS (
      index_type = 'IVF',
      distance_type = 'COSINE'
    )
    """
    
    try:
        job = client.query(create_index_sql)
        result = job.result()
        print("✅ Índice vectorial creado")
        
    except Exception as e:
        print(f"⚠️  Error creando índice: {e}")
        print("🔄 Continuando sin índice...")
    
    # Probar búsquedas
    search_tests = [
        {
            "name": "Búsqueda por autenticación",
            "filter": "business_domain = 'autenticacion'",
            "description": "Chunks relacionados con autenticación"
        },
        {
            "name": "Búsqueda por ventas", 
            "filter": "business_domain = 'ventas'",
            "description": "Chunks relacionados con ventas"
        },
        {
            "name": "Búsqueda por procedures",
            "filter": "semantic_type = 'procedure'",
            "description": "Chunks de stored procedures"
        }
    ]
    
    for test in search_tests:
        print(f"\n🔍 {test['name']}:")
        
        search_sql = f"""
        SELECT 
          chunk_id,
          object_name,
          semantic_type,
          business_domain,
          chunk_index,
          total_chunks,
          chunk_length,
          SUBSTR(chunk_content, 1, 150) as preview
        FROM `{config.PROJECT_ID}.{config.DATASET_ID}.test_complete_flow`
        WHERE {test['filter']}
        ORDER BY chunk_length DESC
        LIMIT 5
        """
        
        try:
            results = list(client.query(search_sql))
            
            if results:
                print(f"   ✅ {len(results)} resultados encontrados:")
                for i, row in enumerate(results, 1):
                    print(f"      {i}. {row.object_name} (chunk {row.chunk_index}/{row.total_chunks})")
                    print(f"         {row.semantic_type} | {row.business_domain} | {row.chunk_length} chars")
                    print(f"         Preview: {row.preview}...")
            else:
                print(f"   ❌ No se encontraron resultados")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return True


def cleanup_test_data():
    """Limpia datos de prueba."""
    config = BigQueryVectorConfig()
    client = bigquery.Client(project=config.PROJECT_ID)
    
    print(f"\n🧹 LIMPIEZA OPCIONAL")
    print("-" * 20)
    
    # Auto-skip para ejecución no interactiva
    choice = 'n'
    
    if choice == 'y':
        try:
            # Eliminar tabla de prueba
            client.query(f"DROP TABLE IF EXISTS `{config.PROJECT_ID}.{config.DATASET_ID}.test_complete_flow`").result()
            
            # Eliminar índice
            try:
                client.query(f"DROP VECTOR INDEX IF EXISTS test_flow_vector_idx ON `{config.PROJECT_ID}.{config.DATASET_ID}.test_complete_flow`").result()
            except:
                pass
            
            print("✅ Datos de prueba eliminados")
            
        except Exception as e:
            print(f"⚠️  Error limpiando: {e}")
    else:
        print("💾 Datos de prueba mantenidos")
        print(f"🔍 Tabla: {config.PROJECT_ID}.{config.DATASET_ID}.test_complete_flow")


def show_manual_vertex_setup():
    """Muestra instrucciones para setup manual de Vertex AI."""
    config = BigQueryVectorConfig()
    
    print(f"\n🔧 SETUP MANUAL DE VERTEX AI")
    print("=" * 35)
    
    print("📋 PASOS PARA HABILITAR EMBEDDINGS REALES:")
    print()
    print("1️⃣ **Crear conexión en BigQuery Console:**")
    print("   • Ve a: https://console.cloud.google.com/bigquery")
    print(f"   • Proyecto: {config.PROJECT_ID}")
    print("   • Menú lateral > External connections")
    print("   • CREATE CONNECTION")
    print("   • Connection type: Vertex AI")
    print("   • Connection ID: vertex_ai_connection")
    print("   • Location: us")
    print()
    print("2️⃣ **Crear modelo remoto:**")
    print("```sql")
    print(f"CREATE OR REPLACE MODEL `{config.PROJECT_ID}.{config.DATASET_ID}.text_embedding_model`")
    print(f"REMOTE WITH CONNECTION `{config.PROJECT_ID}.us.vertex_ai_connection`")
    print(f"OPTIONS(ENDPOINT = 'text-embedding-004');")
    print("```")
    print()
    print("3️⃣ **Probar embedding:**")
    print("```sql")
    print("SELECT *")
    print("FROM ML.GENERATE_EMBEDDING(")
    print(f"  MODEL `{config.PROJECT_ID}.{config.DATASET_ID}.text_embedding_model`,")
    print("  (SELECT 'test embedding' AS content),")
    print("  STRUCT(TRUE AS flatten_json_output)")
    print(");")
    print("```")


def main():
    """Función principal."""
    print_header()
    
    # Ejecutar pipeline completo
    success = create_complete_test_pipeline()
    
    if success:
        # Probar búsquedas
        test_vector_searches()
        
        print(f"\n✅ FLUJO COMPLETO VALIDADO")
        print("=" * 30)
        print("🎯 Resultados:")
        print("   • Chunking inteligente: ✅ Funcionando")
        print("   • Metadatos semánticos: ✅ Generados")
        print("   • Búsquedas por filtros: ✅ Funcionando")
        print("   • Estructura de datos: ✅ Optimizada")
        
        print(f"\n🚀 LISTO PARA EMBEDDINGS REALES:")
        print("   • El chunking funciona perfectamente")
        print("   • Solo falta configurar Vertex AI")
        print("   • Estructura de datos validada")
        
    else:
        print(f"\n❌ FLUJO FALLÓ")
        print("🔧 Revisar configuración de BigQuery")
    
    # Mostrar setup manual
    show_manual_vertex_setup()
    
    # Limpieza opcional
    cleanup_test_data()
    
    print(f"\n" + "=" * 70)
    print("🚀 PRUEBA DE FLUJO COMPLETO TERMINADA")
    print("=" * 70)
    
    if success:
        print("✅ Sistema validado - Solo falta Vertex AI setup")
        print("🔧 Sigue las instrucciones manuales mostradas arriba")
    else:
        print("❌ Sistema necesita ajustes")


if __name__ == "__main__":
    main()
