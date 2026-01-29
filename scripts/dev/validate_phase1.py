#!/usr/bin/env python3
"""
Script de validación para Phase 1 del sistema Agentic RAG.

Verifica que todos los componentes estén funcionando correctamente
antes de proceder a la siguiente fase.
"""

import os
import sys
import time
from pathlib import Path

# Cargar variables de entorno desde .env
from dotenv import load_dotenv
load_dotenv()

# Agregar directorios al path
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))


def check_environment() -> bool:
    """Verifica configuración del entorno."""
    print("🔍 Verificando configuración del entorno...")
    
    required_vars = {
        "GEMINI_API_KEY": "Gemini API key para embeddings y agentes",
        "GOOGLE_APPLICATION_CREDENTIALS": "Credenciales de Google Cloud",
    }
    
    missing = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing.append(f"  ❌ {var}: {description}")
        else:
            print(f"  ✅ {var}: Configurado")
    
    if missing:
        print("\n❌ Variables faltantes:")
        print("\n".join(missing))
        return False
    
    return True


def check_dependencies() -> bool:
    """Verifica que las dependencias estén instaladas."""
    print("\n📦 Verificando dependencias...")
    
    dependencies = [
        ("weaviate", "weaviate-client"),
        ("google.genai", "google-genai"),
        ("pandas", "pandas"),
        ("google.cloud.bigquery", "google-cloud-bigquery"),
    ]
    
    missing = []
    for module, package in dependencies:
        try:
            __import__(module)
            print(f"  ✅ {package}: Disponible")
        except ImportError:
            missing.append(f"  ❌ {package}: No instalado")
    
    if missing:
        print("\n❌ Dependencias faltantes:")
        print("\n".join(missing))
        print("\nInstala con: pip install -r requirements.txt")
        return False
    
    return True


def check_bigquery_connection() -> bool:
    """Verifica conexión con BigQuery."""
    print("\n🔗 Verificando conexión BigQuery...")
    
    try:
        from squit_client import BigQueryClient
        
        client = BigQueryClient()
        
        # Test de conexión simple
        test_query = f"""
        SELECT COUNT(*) as total
        FROM `{client.config.full_table_id}`
        LIMIT 1
        """
        
        result = client.execute_query(test_query)
        
        if not result.empty:
            total = result.iloc[0]["total"]
            print(f"  ✅ BigQuery: Conectado ({total:,} objetos disponibles)")
            return True
        else:
            print("  ❌ BigQuery: Sin datos")
            return False
            
    except Exception as e:
        print(f"  ❌ BigQuery: Error - {e}")
        return False


def check_weaviate_connection() -> bool:
    """Verifica conexión con Weaviate."""
    print("\n🔗 Verificando conexión Weaviate...")
    
    try:
        from agentic_rag import WeaviateClient
        
        client = WeaviateClient()
        health = client.health_check()
        
        if health["status"] == "healthy":
            print("  ✅ Weaviate: Conectado y saludable")
            print(f"  📍 URL: {health['url']}")
            print(f"  🔑 Gemini configurado: {health.get('gemini_configured', False)}")
            
            # Mostrar collections
            collections = health.get("collections", {})
            if collections:
                print("  📊 Collections:")
                for name, count in collections.items():
                    print(f"    • {name}: {count} objetos")
            
            return True
        else:
            print(f"  ❌ Weaviate: Estado {health['status']}")
            if "error" in health:
                print(f"    Error: {health['error']}")
            return False
            
    except Exception as e:
        print(f"  ❌ Weaviate: Error - {e}")
        print("  💡 Tip: Ejecuta 'make agentic-setup' primero")
        return False


def check_schema_creation() -> bool:
    """Verifica que el schema de Weaviate esté creado."""
    print("\n🏗️ Verificando schema de Weaviate...")
    
    try:
        from agentic_rag import WeaviateClient
        
        client = WeaviateClient()
        
        # Intentar crear schema (idempotente)
        if client.create_schema():
            print("  ✅ Schema: Configurado correctamente")
            
            # Verificar collections específicas
            expected_collections = ["CodeObjects", "Dependencies", "Metadata", "CodePatterns"]
            
            for collection_name in expected_collections:
                try:
                    collection = client.get_collection(collection_name)
                    print(f"    ✅ {collection_name}: Disponible")
                except Exception:
                    print(f"    ❌ {collection_name}: No disponible")
                    return False
            
            return True
        else:
            print("  ❌ Schema: Error en creación")
            return False
            
    except Exception as e:
        print(f"  ❌ Schema: Error - {e}")
        return False


def test_basic_ingestion() -> bool:
    """Prueba ingesta básica con un objeto de muestra."""
    print("\n📥 Probando ingesta básica...")
    
    try:
        from agentic_rag import WeaviateClient, IngestionPipeline
        from squit_client import BigQueryClient
        
        # Inicializar componentes
        bigquery_client = BigQueryClient()
        weaviate_client = WeaviateClient()
        pipeline = IngestionPipeline(bigquery_client, weaviate_client)
        
        # Ingesta de muestra muy pequeña
        filters = {
            "object_type": ["PROCEDURE"],
            "server": "SRVDBDES05\\BASCULA",
        }
        
        print("  🔄 Procesando muestra de 5 objetos...")
        stats = pipeline.run_full_ingestion(limit=5, filters=filters)
        
        if stats["success"] > 0:
            print(f"  ✅ Ingesta: {stats['success']}/{stats['processed']} objetos procesados")
            return True
        else:
            print(f"  ❌ Ingesta: 0 objetos procesados exitosamente")
            print(f"    Errores: {stats['errors']}, Saltados: {stats['skipped']}")
            return False
            
    except Exception as e:
        print(f"  ❌ Ingesta: Error - {e}")
        return False


def test_agentic_queries() -> bool:
    """Prueba consultas agentic básicas."""
    print("\n🤖 Probando consultas agentic...")
    
    try:
        from agentic_rag import WeaviateClient, MasterAgent
        
        # Inicializar agente maestro
        weaviate_client = WeaviateClient()
        master_agent = MasterAgent(weaviate_client)
        
        # Consulta de prueba
        test_query = "Busca procedimientos relacionados con usuarios"
        
        print(f"  🔄 Procesando: '{test_query}'")
        response = master_agent.process_query(test_query)
        
        if "error" not in response:
            print("  ✅ Consulta agentic: Funcionando")
            print(f"    Agentes usados: {len(response.get('agent_responses', {}))}")
            return True
        else:
            print(f"  ❌ Consulta agentic: Error - {response['error']}")
            return False
            
    except Exception as e:
        print(f"  ❌ Consulta agentic: Error - {e}")
        return False


def run_validation() -> bool:
    """Ejecuta validación completa."""
    print("🚀 SQUIT Agentic RAG - Validación Phase 1")
    print("=" * 55)
    
    checks = [
        ("Entorno", check_environment),
        ("Dependencias", check_dependencies), 
        ("BigQuery", check_bigquery_connection),
        ("Weaviate", check_weaviate_connection),
        ("Schema", check_schema_creation),
        ("Ingesta", test_basic_ingestion),
        ("Consultas Agentic", test_agentic_queries),
    ]
    
    results = []
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
            
            if result:
                print(f"\n✅ {check_name}: PASSED")
            else:
                print(f"\n❌ {check_name}: FAILED")
                
        except Exception as e:
            print(f"\n💥 {check_name}: EXCEPTION - {e}")
            results.append((check_name, False))
    
    # Resumen final
    print("\n" + "=" * 55)
    print("📊 RESUMEN DE VALIDACIÓN")
    print("=" * 55)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {check_name}: {status}")
    
    print(f"\n📈 Resultado: {passed}/{total} checks pasaron")
    
    if passed == total:
        print("\n🎉 ¡Phase 1 COMPLETAMENTE VALIDADA!")
        print("🚀 El sistema Agentic RAG está listo para uso")
        print("\n📋 Próximos pasos:")
        print("  1. Ejecutar 'make agentic-demo' para demo completo")
        print("  2. Usar 'make agentic-dev' para desarrollo")
        print("  3. Proceder a Phase 2 según TODO.md")
        return True
    else:
        print(f"\n⚠️  {total - passed} checks fallaron")
        print("🔧 Revisa los errores antes de continuar")
        return False


def main():
    """Función principal."""
    success = run_validation()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
