#!/usr/bin/env python3
"""
Script para configurar conexión remota a Vertex AI.

Este script configura la conexión necesaria para usar ML.GENERATE_EMBEDDING
con modelos remotos de Vertex AI según la documentación oficial.
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
    print("🔗 SQUIT - Setup Vertex AI Connection")
    print("=" * 60)
    print(f"📅 Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 Objetivo: Configurar conexión remota Vertex AI")
    print("🔧 Basado en: ML.GENERATE_EMBEDDING docs")
    print()


def create_vertex_ai_connection():
    """Crea conexión a Vertex AI para BigQuery ML."""
    config = BigQueryVectorConfig()
    client = bigquery.Client(project=config.PROJECT_ID)
    
    print("🔗 CREANDO CONEXIÓN VERTEX AI")
    print("-" * 35)
    
    connection_id = "vertex_ai_connection"
    
    try:
        # Método 1: Usar BigQuery API directamente
        from google.cloud.bigquery_connection_v1 import ConnectionServiceClient
        from google.cloud.bigquery_connection_v1.types import Connection, CloudResourceProperties
        
        connection_client = ConnectionServiceClient()
        parent = f"projects/{config.PROJECT_ID}/locations/us"
        
        try:
            # Verificar si ya existe
            connection_name = f"{parent}/connections/{connection_id}"
            existing = connection_client.get_connection(name=connection_name)
            
            print(f"✅ Conexión existente: {connection_id}")
            print(f"   • Service Account: {existing.cloud_resource.service_account_id}")
            return connection_id
            
        except Exception:
            # Crear nueva conexión
            print(f"🔄 Creando nueva conexión...")
            
            connection = Connection()
            connection.cloud_resource = CloudResourceProperties()
            
            created = connection_client.create_connection(
                parent=parent,
                connection_id=connection_id,
                connection=connection
            )
            
            print(f"✅ Conexión creada!")
            print(f"   • ID: {connection_id}")
            print(f"   • Service Account: {created.cloud_resource.service_account_id}")
            
            return connection_id
            
    except ImportError:
        # Método 2: Usar gcloud CLI
        print("🔄 Intentando con gcloud CLI...")
        
        import subprocess
        
        try:
            # Verificar si existe
            check_cmd = [
                "gcloud", "alpha", "bq", "connections", "describe", 
                connection_id, "--location=us", 
                f"--project={config.PROJECT_ID}"
            ]
            
            result = subprocess.run(check_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Conexión existente encontrada: {connection_id}")
                return connection_id
            else:
                # Crear nueva conexión
                create_cmd = [
                    "gcloud", "alpha", "bq", "connections", "create",
                    "--connection-type=CLOUD_RESOURCE",
                    "--location=us",
                    f"--project={config.PROJECT_ID}",
                    connection_id
                ]
                
                result = subprocess.run(create_cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"✅ Conexión creada con gcloud!")
                    print(f"   • ID: {connection_id}")
                    return connection_id
                else:
                    print(f"❌ Error con gcloud: {result.stderr}")
                    
        except Exception as e:
            print(f"❌ Error con gcloud: {e}")
    
    except Exception as e:
        print(f"❌ Error creando conexión: {e}")
    
    # Método 3: Instrucciones manuales
    print(f"\n🔧 CREAR CONEXIÓN MANUALMENTE:")
    print(f"```bash")
    print(f"# Opción 1: gcloud CLI")
    print(f"gcloud alpha bq connections create \\")
    print(f"  --connection-type=CLOUD_RESOURCE \\")
    print(f"  --location=us \\")
    print(f"  --project={config.PROJECT_ID} \\")
    print(f"  {connection_id}")
    print(f"")
    print(f"# Opción 2: BigQuery Console")
    print(f"# 1. Ve a BigQuery > External connections")
    print(f"# 2. CREATE CONNECTION")
    print(f"# 3. Connection type: Vertex AI")
    print(f"# 4. Connection ID: {connection_id}")
    print(f"# 5. Location: us")
    print(f"```")
    
    return None


def create_embedding_model(connection_id: str):
    """Crea modelo remoto para embeddings."""
    config = BigQueryVectorConfig()
    client = bigquery.Client(project=config.PROJECT_ID)
    
    print(f"\n🤖 CREANDO MODELO DE EMBEDDINGS")
    print("-" * 35)
    
    create_model_sql = f"""
    CREATE OR REPLACE MODEL `{config.PROJECT_ID}.{config.DATASET_ID}.text_embedding_model`
    REMOTE WITH CONNECTION `{config.PROJECT_ID}.us.{connection_id}`
    OPTIONS(ENDPOINT = '{config.EMBEDDING_MODEL}')
    """
    
    try:
        job = client.query(create_model_sql)
        job.result()
        
        print("✅ Modelo de embeddings creado exitosamente!")
        print(f"   • Modelo: {config.PROJECT_ID}.{config.DATASET_ID}.text_embedding_model")
        print(f"   • Endpoint: {config.EMBEDDING_MODEL}")
        print(f"   • Conexión: {connection_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creando modelo: {e}")
        return False


def test_embedding_generation():
    """Prueba la generación de embeddings."""
    config = BigQueryVectorConfig()
    client = bigquery.Client(project=config.PROJECT_ID)
    
    print(f"\n🧪 PROBANDO GENERACIÓN DE EMBEDDINGS")
    print("-" * 40)
    
    test_sql = f"""
    SELECT *
    FROM ML.GENERATE_EMBEDDING(
      MODEL `{config.PROJECT_ID}.{config.DATASET_ID}.text_embedding_model`,
      (SELECT "Stored procedure para autenticacion de usuarios" AS content),
      STRUCT(TRUE AS flatten_json_output)
    )
    """
    
    try:
        print("🔄 Generando embedding de prueba...")
        results = list(client.query(test_sql))
        
        if results:
            embedding = results[0].ml_generate_embedding_result
            print(f"✅ Embedding generado exitosamente!")
            print(f"   • Dimensiones: {len(embedding.embeddings) if hasattr(embedding, 'embeddings') else 'N/A'}")
            print(f"   • Tipo: {type(embedding)}")
            
            return True
        else:
            print(f"❌ No se generó embedding")
            return False
            
    except Exception as e:
        print(f"❌ Error probando embeddings: {e}")
        return False


def show_usage_examples():
    """Muestra ejemplos de uso basados en la documentación."""
    config = BigQueryVectorConfig()
    
    print(f"\n📝 EJEMPLOS DE USO")
    print("-" * 25)
    
    print("🔧 1. CREAR MODELO REMOTO:")
    print("```sql")
    print(f"CREATE OR REPLACE MODEL `{config.PROJECT_ID}.{config.DATASET_ID}.text_embedding_model`")
    print(f"REMOTE WITH CONNECTION `{config.PROJECT_ID}.us.vertex_ai_connection`")
    print(f"OPTIONS(ENDPOINT = '{config.EMBEDDING_MODEL}');")
    print("```")
    
    print(f"\n🎯 2. GENERAR EMBEDDINGS:")
    print("```sql")
    print("SELECT *")
    print("FROM ML.GENERATE_EMBEDDING(")
    print(f"  MODEL `{config.PROJECT_ID}.{config.DATASET_ID}.text_embedding_model`,")
    print("  (SELECT chunk_content AS content FROM my_chunks_table),")
    print("  STRUCT(TRUE AS flatten_json_output)")
    print(");")
    print("```")
    
    print(f"\n🔍 3. BÚSQUEDA VECTORIAL:")
    print("```sql")
    print("SELECT chunk_id, distance")
    print("FROM VECTOR_SEARCH(")
    print(f"  TABLE `{config.PROJECT_ID}.{config.DATASET_ID}.chunk_embeddings`,")
    print("  'embedding',")
    print("  (SELECT ml_generate_embedding_result.embeddings")
    print("   FROM ML.GENERATE_EMBEDDING(...)),")
    print("  top_k => 10")
    print(");")
    print("```")


def main():
    """Función principal."""
    print_header()
    
    # Paso 1: Crear conexión
    connection_id = create_vertex_ai_connection()
    
    if connection_id:
        # Paso 2: Crear modelo
        model_created = create_embedding_model(connection_id)
        
        if model_created:
            # Paso 3: Probar embeddings
            test_success = test_embedding_generation()
            
            if test_success:
                print(f"\n✅ SETUP COMPLETADO EXITOSAMENTE")
                print("=" * 40)
                print("🚀 Sistema listo para embeddings reales!")
                print("📋 Próximos pasos:")
                print("   1. make test-chunks     # Probar con embeddings reales")
                print("   2. make bigquery-full   # Pipeline completo")
            else:
                print(f"\n⚠️  SETUP PARCIAL")
                print("🔧 Modelo creado pero embeddings fallan")
        else:
            print(f"\n❌ SETUP FALLÓ")
            print("🔧 No se pudo crear modelo de embeddings")
    else:
        print(f"\n❌ SETUP FALLÓ") 
        print("🔧 No se pudo crear conexión Vertex AI")
    
    # Mostrar ejemplos independientemente del resultado
    show_usage_examples()
    
    print(f"\n" + "=" * 60)
    print("🔗 SETUP VERTEX AI CONNECTION COMPLETADO")
    print("=" * 60)


if __name__ == "__main__":
    main()
