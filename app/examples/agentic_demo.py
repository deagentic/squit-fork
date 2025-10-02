#!/usr/bin/env python3
"""
Demo del sistema Agentic RAG para análisis de código SQL.

Este script demuestra las capacidades del sistema multi-agente
para analizar código legacy almacenado en BigQuery.
"""

import os
import sys
from pathlib import Path

# Agregar directorios al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agentic_rag import WeaviateClient, MasterAgent, IngestionPipeline
from agentic_rag.config import WeaviateConfig, AgentConfig
from squit_client import BigQueryClient
from squit_client.exceptions import SquitError
from squit_client.utils import setup_logging, suppress_warnings


def check_environment() -> bool:
    """Verifica que las variables de entorno estén configuradas."""
    required_vars = ["OPENAI_API_KEY", "GOOGLE_APPLICATION_CREDENTIALS"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Variables de entorno faltantes: {', '.join(missing_vars)}")
        print("\nConfigura las variables:")
        print("export OPENAI_API_KEY='tu-api-key'")
        print("export GOOGLE_APPLICATION_CREDENTIALS='/path/to/credentials.json'")
        return False
    
    return True


def setup_weaviate_schema(weaviate_client: WeaviateClient) -> bool:
    """Configura el schema de Weaviate."""
    print("🔧 Configurando schema de Weaviate...")
    
    try:
        # Verificar salud de Weaviate
        health = weaviate_client.health_check()
        if health["status"] != "healthy":
            print(f"❌ Weaviate no está saludable: {health}")
            return False
        
        print("✅ Weaviate está funcionando correctamente")
        
        # Crear schema
        if weaviate_client.create_schema():
            print("✅ Schema creado exitosamente")
            
            # Mostrar estadísticas
            stats = weaviate_client.get_collection_stats()
            print("📊 Collections creadas:")
            for collection, count in stats.items():
                print(f"  • {collection}: {count} objetos")
            
            return True
        else:
            print("❌ Error creando schema")
            return False
            
    except Exception as e:
        print(f"❌ Error configurando Weaviate: {e}")
        return False


def run_sample_ingestion(
    bigquery_client: BigQueryClient, 
    weaviate_client: WeaviateClient
) -> bool:
    """Ejecuta ingesta de muestra para testing."""
    print("\n📥 Ejecutando ingesta de muestra...")
    
    try:
        # Crear pipeline
        pipeline = IngestionPipeline(bigquery_client, weaviate_client)
        
        # Ingestar muestra pequeña para testing
        filters = {
            "object_type": ["PROCEDURE", "VIEW"],  # Solo tipos importantes
            "server": "SRVDBDES05\\BASCULA",  # Servidor específico
        }
        
        stats = pipeline.run_full_ingestion(limit=50, filters=filters)
        
        print("✅ Ingesta completada:")
        print(f"  • Procesados: {stats['processed']}")
        print(f"  • Exitosos: {stats['success']}")
        print(f"  • Errores: {stats['errors']}")
        print(f"  • Saltados: {stats['skipped']}")
        
        if stats["success"] > 0:
            print("✅ Datos disponibles para consultas agentic")
            return True
        else:
            print("⚠️  No se procesaron datos exitosamente")
            return False
            
    except Exception as e:
        print(f"❌ Error en ingesta: {e}")
        return False


def demo_agentic_queries(master_agent: MasterAgent) -> None:
    """Demuestra consultas agentic."""
    print("\n🤖 Demo de Consultas Agentic")
    print("=" * 40)
    
    # Consultas de ejemplo
    demo_queries = [
        "¿Dónde está la lógica de autenticación de usuarios?",
        "¿Qué procedimientos manejan facturación?",
        "Busca código relacionado con inventario",
        "¿Hay patrones de seguridad en el código?",
    ]
    
    for i, query in enumerate(demo_queries, 1):
        print(f"\n{i}. Consulta: '{query}'")
        print("-" * 50)
        
        try:
            # Procesar consulta con el agente maestro
            response = master_agent.process_query(query)
            
            # Mostrar respuesta
            if "error" in response:
                print(f"❌ Error: {response['error']}")
            else:
                print(f"🤖 Respuesta: {response.get('response', 'Sin respuesta')}")
                
                # Mostrar detalles de agentes si están disponibles
                if "agent_responses" in response:
                    agent_resp = response["agent_responses"]
                    
                    if "code_search" in agent_resp:
                        search_results = agent_resp["code_search"].get("total_found", 0)
                        print(f"🔍 Objetos encontrados: {search_results}")
                    
                    if "dependency" in agent_resp:
                        deps = agent_resp["dependency"].get("total_dependencies", 0)
                        print(f"🔗 Dependencias analizadas: {deps}")
        
        except Exception as e:
            print(f"❌ Error procesando consulta: {e}")


def main():
    """Función principal del demo."""
    print("🚀 SQUIT Agentic RAG - Demo Phase 1")
    print("=" * 50)
    
    # Configurar entorno
    suppress_warnings()
    setup_logging("INFO")
    
    # Verificar configuración
    if not check_environment():
        sys.exit(1)
    
    try:
        # 1. Inicializar clientes
        print("\n🔗 Inicializando conexiones...")
        
        bigquery_client = BigQueryClient()
        print("✅ BigQuery conectado")
        
        weaviate_client = WeaviateClient()
        print("✅ Weaviate conectado")
        
        # 2. Configurar schema
        if not setup_weaviate_schema(weaviate_client):
            print("❌ Error configurando Weaviate")
            sys.exit(1)
        
        # 3. Ejecutar ingesta de muestra
        if not run_sample_ingestion(bigquery_client, weaviate_client):
            print("⚠️  Continuando sin ingesta...")
        
        # 4. Inicializar agente maestro
        print("\n🧠 Inicializando agente maestro...")
        master_agent = MasterAgent(weaviate_client)
        print("✅ Sistema agentic listo")
        
        # 5. Demo de consultas
        demo_agentic_queries(master_agent)
        
        print("\n🎉 Demo completado exitosamente!")
        print("📚 El sistema Agentic RAG está funcionando")
        print("🔗 Weaviate UI: http://localhost:8080")
        
    except SquitError as e:
        print(f"❌ Error del sistema SQUIT: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        sys.exit(1)
    finally:
        # Limpiar conexiones
        try:
            weaviate_client.close()
        except:
            pass


if __name__ == "__main__":
    main()
