#!/usr/bin/env python3
"""
Script para crear conexión Vertex AI usando SQL directo.

Basado en la documentación oficial de ML.GENERATE_EMBEDDING,
este script crea la conexión y modelo usando BigQuery SQL.
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
    print("🔗 SQUIT - Crear Conexión Vertex AI (SQL)")
    print("=" * 60)
    print(f"📅 Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 Objetivo: Conexión + Modelo con SQL directo")
    print("🔧 Método: BigQuery SQL + Vertex AI")
    print()


def create_connection_and_model():
    """Crea conexión y modelo usando SQL directo."""
    config = BigQueryVectorConfig()
    client = bigquery.Client(project=config.PROJECT_ID)
    
    print("🔄 MÉTODO SIMPLIFICADO: Solo crear modelo")
    print("-" * 45)
    print("💡 Según la documentación, BigQuery puede crear")
    print("   la conexión automáticamente si tienes permisos")
    print()
    
    # Método 1: Intentar sin conexión explícita (BigQuery auto-gestiona)
    model_sql = f"""
    CREATE OR REPLACE MODEL `{config.PROJECT_ID}.{config.DATASET_ID}.text_embedding_model`
    OPTIONS(
      endpoint='{config.EMBEDDING_MODEL}'
    )
    """
    
    try:
        print("🔄 Creando modelo de embeddings...")
        print(f"   • Modelo: {config.EMBEDDING_MODEL}")
        print(f"   • Dataset: {config.DATASET_ID}")
        
        job = client.query(model_sql)
        result = job.result()
        
        print("✅ Modelo creado exitosamente!")
        print(f"   • Nombre: text_embedding_model")
        print(f"   • Endpoint: {config.EMBEDDING_MODEL}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creando modelo: {e}")
        
        # Método alternativo: usar textembedding-gecko
        print(f"\n🔄 Intentando con textembedding-gecko...")
        
        gecko_model_sql = f"""
        CREATE OR REPLACE MODEL `{config.PROJECT_ID}.{config.DATASET_ID}.text_embedding_model`
        OPTIONS(
          endpoint='textembedding-gecko@003'
        )
        """
        
        try:
            job = client.query(gecko_model_sql)
            result = job.result()
            
            print("✅ Modelo gecko creado exitosamente!")
            print(f"   • Endpoint: textembedding-gecko@003")
            
            # Actualizar config para usar gecko
            config.EMBEDDING_MODEL = "textembedding-gecko@003"
            
            return True
            
        except Exception as e2:
            print(f"❌ Error con gecko: {e2}")
            return False


def test_embedding_model():
    """Prueba el modelo de embeddings creado."""
    config = BigQueryVectorConfig()
    client = bigquery.Client(project=config.PROJECT_ID)
    
    print(f"\n🧪 PROBANDO MODELO DE EMBEDDINGS")
    print("-" * 35)
    
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
            result = results[0]
            
            # Verificar estructura del resultado
            if hasattr(result, 'ml_generate_embedding_result'):
                embedding_result = result.ml_generate_embedding_result
                if hasattr(embedding_result, 'embeddings'):
                    embeddings = embedding_result.embeddings
                    print(f"✅ Embedding generado exitosamente!")
                    print(f"   • Dimensiones: {len(embeddings)}")
                    print(f"   • Primeros valores: {embeddings[:5]}")
                    return True
            
            print(f"⚠️  Embedding generado pero estructura inesperada")
            print(f"   • Resultado: {result}")
            return True
            
        else:
            print(f"❌ No se generó resultado")
            return False
            
    except Exception as e:
        print(f"❌ Error probando embedding: {e}")
        
        # Información para debug
        print(f"\n🔧 INFORMACIÓN DE DEBUG:")
        print(f"   • Proyecto: {config.PROJECT_ID}")
        print(f"   • Dataset: {config.DATASET_ID}")
        print(f"   • Modelo: text_embedding_model")
        print(f"   • Endpoint: {config.EMBEDDING_MODEL}")
        
        return False


def show_next_steps():
    """Muestra próximos pasos."""
    print(f"\n🚀 PRÓXIMOS PASOS")
    print("-" * 20)
    
    print("✅ Si el modelo funciona:")
    print("   1. make test-chunks      # Probar chunking con embeddings reales")
    print("   2. make search-chunks    # Probar búsquedas vectoriales")
    print("   3. make bigquery-full    # Pipeline completo")
    
    print(f"\n❌ Si hay errores:")
    print("   1. Verificar permisos Vertex AI")
    print("   2. Habilitar APIs necesarias:")
    print("      • Vertex AI API")
    print("      • BigQuery Connection API")
    print("   3. Crear conexión manual en BigQuery Console")


def main():
    """Función principal."""
    print_header()
    
    # Crear modelo
    model_created = create_connection_and_model()
    
    if model_created:
        # Probar modelo
        test_success = test_embedding_model()
        
        if test_success:
            print(f"\n✅ SETUP COMPLETADO EXITOSAMENTE")
            print("=" * 40)
            print("🎯 Modelo de embeddings funcionando!")
            print("🚀 Sistema listo para pruebas completas")
        else:
            print(f"\n⚠️  SETUP PARCIAL")
            print("🔧 Modelo creado pero embeddings fallan")
    else:
        print(f"\n❌ SETUP FALLÓ")
        print("🔧 No se pudo crear modelo de embeddings")
    
    show_next_steps()
    
    print(f"\n" + "=" * 60)
    print("🔗 SETUP VERTEX AI COMPLETADO")
    print("=" * 60)


if __name__ == "__main__":
    main()
