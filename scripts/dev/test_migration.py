#!/usr/bin/env python3
"""
Script para probar migración con 10 objetos.

Valida que el pipeline completo funcione antes de la migración masiva.
"""

import os
import sys
import time
from pathlib import Path

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv()

# Agregar directorios al path
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))


def wait_for_weaviate(max_attempts=10):
    """Espera a que Weaviate esté listo."""
    import requests
    
    print("🔄 Esperando a que Weaviate esté listo...")
    
    for attempt in range(max_attempts):
        try:
            response = requests.get("http://localhost:8080/v1/.well-known/ready", timeout=5)
            if response.status_code == 200:
                print("✅ Weaviate está listo!")
                return True
        except:
            pass
        
        print(f"   Intento {attempt + 1}/{max_attempts}... esperando 3s")
        time.sleep(3)
    
    return False


def test_migration_10_objects():
    """Prueba migración con 10 objetos."""
    print("🧪 PRUEBA DE MIGRACIÓN - 10 Objetos")
    print("=" * 50)
    
    try:
        # 1. Verificar conexiones
        print("\n1. 🔗 Verificando conexiones...")
        
        from squit_client import BigQueryClient
        bigquery_client = BigQueryClient()
        print("   ✅ BigQuery: Conectado")
        
        if not wait_for_weaviate(5):
            print("   ❌ Weaviate: No disponible")
            return False
        
        from agentic_rag import WeaviateClient, IngestionPipeline
        weaviate_client = WeaviateClient()
        print("   ✅ Weaviate: Conectado")
        
        # 2. Configurar schema
        print("\n2. 🏗️ Configurando schema...")
        if weaviate_client.create_schema():
            print("   ✅ Schema: Configurado")
        else:
            print("   ❌ Schema: Error")
            return False
        
        # 3. Ejecutar migración de prueba
        print("\n3. 📥 Ejecutando migración de 10 objetos...")
        pipeline = IngestionPipeline(bigquery_client, weaviate_client)
        
        # Filtros para objetos importantes y pequeños
        filters = {
            "object_type": ["PROCEDURE", "VIEW"],
            "server": "srvpreprobd\\PTIOPEROFI",  # Servidor con objetos recientes
        }
        
        print("   🔄 Procesando objetos más recientes...")
        stats = pipeline.run_full_ingestion(limit=10, filters=filters)
        
        # 4. Mostrar resultados
        print("\n4. 📊 Resultados de migración:")
        print(f"   • Procesados: {stats['processed']}")
        print(f"   • Exitosos: {stats['success']}")
        print(f"   • Errores: {stats['errors']}")
        print(f"   • Saltados: {stats['skipped']}")
        
        if 'embeddings_generated' in stats:
            print(f"   • Embeddings: {stats['embeddings_generated']}")
        if 'ai_analysis_completed' in stats:
            print(f"   • Análisis IA: {stats['ai_analysis_completed']}")
        
        # 5. Verificar datos en Weaviate
        print("\n5. 🔍 Verificando datos en Weaviate...")
        collection_stats = weaviate_client.get_collection_stats()
        
        for collection, count in collection_stats.items():
            print(f"   • {collection}: {count} objetos")
        
        # 6. Probar búsqueda
        if collection_stats.get("CodeObjects", 0) > 0:
            print("\n6. 🔍 Probando búsqueda semántica...")
            results = weaviate_client.search_code_objects(
                query="usuario seguridad",
                limit=3,
                hybrid=True,
            )
            
            print(f"   ✅ Búsqueda: {len(results)} resultados encontrados")
            for i, result in enumerate(results, 1):
                print(f"      {i}. {result['object_name']} ({result['object_type']})")
        
        # 7. Evaluación final
        success_rate = (stats['success'] / max(1, stats['processed'])) * 100
        
        print(f"\n📈 Tasa de éxito: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("✅ Migración de prueba EXITOSA")
            print("🚀 Sistema listo para migración completa")
            return True
        else:
            print("⚠️  Migración de prueba con problemas")
            print("🔧 Revisar configuración antes de migración completa")
            return False
            
    except Exception as e:
        print(f"\n❌ Error en migración de prueba: {e}")
        return False


def main():
    """Función principal."""
    print("🧪 SQUIT Agentic RAG - Prueba de Migración")
    print("Validando pipeline con 10 objetos...")
    
    success = test_migration_10_objects()
    
    if success:
        print("\n🎉 ¡Prueba de migración exitosa!")
        print("\n📋 Próximos pasos:")
        print("   1. Revisar objetos migrados en Weaviate UI: http://localhost:8080")
        print("   2. Probar consultas agentic con datos reales")
        print("   3. Proceder con migración completa si todo se ve bien")
        
        print("\n💡 Comandos sugeridos:")
        print("   make agentic-dev     # Explorar datos en Jupyter")
        print("   make agentic-ingest  # Migración completa (1,000 objetos)")
    else:
        print("\n⚠️  Revisar errores antes de continuar")
        print("   Ver logs: make agentic-logs")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
