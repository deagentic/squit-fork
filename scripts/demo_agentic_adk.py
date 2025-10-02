#!/usr/bin/env python3
"""
Demo del Sistema Agentic ADK - Democratizando Código Legacy.

Este script demuestra cómo los agentes permiten a CUALQUIER persona
entender código SQL legacy mediante lenguaje natural.

Uso:
    # Modo interactivo
    python scripts/demo_agentic_adk.py
    
    # Demo automática
    python scripts/demo_agentic_adk.py --demo
"""

import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Agregar app al path
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from agentic_adk import MasterAgent
from agentic_adk.config import AgenticADKConfig

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def print_banner():
    """Imprime banner del demo."""
    print("\n" + "=" * 80)
    print("🎯 SQUIT - \"SQL Quit\": Democratizando Código Legacy con IA")
    print("=" * 80)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🤖 Sistema: Agentic RAG con Google ADK + Gemini 2.0")
    print("🔍 Búsqueda: BigQuery VECTOR_SEARCH (768-dim embeddings)")
    print("=" * 80)
    print()
    print("💡 MISIÓN: Liberar el conocimiento enterrado en código sin documentar")
    print("   Hacer código legacy ACCESIBLE para toda la organización")
    print()


def run_demo():
    """Ejecuta demo automática con queries pre-definidas."""
    print_banner()
    
    print("📋 DEMO AUTOMÁTICA: Casos de Uso de Democratización\n")
    
    # Inicializar agente
    try:
        agent = MasterAgent()
    except ValueError as e:
        print(f"❌ Error de configuración: {e}")
        print("\n💡 Verifica que GEMINI_API_KEY esté configurado en .env")
        return 1
    except Exception as e:
        print(f"❌ Error inicializando agente: {e}")
        return 1
    
    # Demo queries
    demo_queries = [
        {
            "title": "🔍 Caso 1: Desarrollador Nuevo - Buscar Lógica",
            "query": "¿Dónde está la lógica de autenticación de usuarios?",
            "context": "Nuevo dev que no conoce el codebase"
        },
        {
            "title": "📊 Caso 2: Arquitecto - Análisis de Impacto",
            "query": "¿Qué objetos dependen de la tabla ClientesMaster?",
            "context": "Arquitecto evaluando cambios en tabla"
        },
        {
            "title": "💼 Caso 3: Analista de Negocio - Entender Proceso",
            "query": "Explícame los procedimientos relacionados con facturación y ventas",
            "context": "Analista que necesita entender flujos de negocio"
        },
    ]
    
    for i, demo in enumerate(demo_queries, 1):
        print("\n" + "-" * 80)
        print(f"{demo['title']}")
        print(f"Contexto: {demo['context']}")
        print("-" * 80)
        print(f"\n👤 Usuario: \"{demo['query']}\"")
        print("\n🤖 SQUIT:")
        
        try:
            response = agent.process(demo['query'])
            print(response)
        except Exception as e:
            print(f"❌ Error: {e}")
        
        if i < len(demo_queries):
            input("\n[Presiona Enter para continuar...]")
    
    print("\n" + "=" * 80)
    print("✅ Demo completada")
    print("=" * 80)
    print("\n💡 Prueba el modo interactivo:")
    print("   python scripts/demo_agentic_adk.py")
    print()
    
    return 0


def run_interactive():
    """Ejecuta modo interactivo."""
    print_banner()
    
    try:
        agent = MasterAgent()
    except ValueError as e:
        print(f"❌ Error de configuración: {e}")
        print("\n💡 Verifica que GEMINI_API_KEY esté configurado en .env")
        return 1
    except Exception as e:
        print(f"❌ Error inicializando agente: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Modo interactivo
    agent.interactive()
    
    return 0


def validate_setup():
    """Valida que el setup esté completo."""
    print_banner()
    print("🔍 VALIDANDO SETUP DEL SISTEMA AGENTIC\n")
    
    checks = []
    
    # 1. Verificar GEMINI_API_KEY
    config = AgenticADKConfig()
    try:
        config.validate()
        checks.append(("✅", "GEMINI_API_KEY configurado"))
    except ValueError as e:
        checks.append(("❌", f"GEMINI_API_KEY: {e}"))
    
    # 2. Verificar BigQuery
    try:
        from google.cloud import bigquery
        client = bigquery.Client(project=config.PROJECT_ID)
        table = client.get_table(config.full_embeddings_table_id)
        checks.append(("✅", f"Tabla embeddings: {table.num_rows:,} rows"))
    except Exception as e:
        checks.append(("❌", f"BigQuery: {e}"))
    
    # 3. Verificar modelo de embeddings
    try:
        model = client.get_model(config.full_embedding_model_id)
        checks.append(("✅", f"Modelo embeddings: {model.model_type}"))
    except Exception as e:
        checks.append(("⚠️", f"Modelo embeddings: No encontrado (se creará al usarse)"))
    
    # 4. Verificar google-adk
    try:
        import google_adk
        checks.append(("✅", f"Google ADK: v{google_adk.__version__}"))
    except Exception as e:
        checks.append(("❌", f"Google ADK: No instalado"))
    
    # Imprimir resultados
    print("Resultados de Validación:")
    for icon, message in checks:
        print(f"  {icon} {message}")
    
    # Resumen
    failed = sum(1 for icon, _ in checks if icon == "❌")
    warnings = sum(1 for icon, _ in checks if icon == "⚠️")
    
    print("\n" + "=" * 80)
    if failed == 0:
        print("✅ Sistema listo para democratizar código legacy")
        print("\n💡 Ejecuta: python scripts/demo_agentic_adk.py")
    else:
        print(f"❌ {failed} checks fallidos - Revisa configuración")
        if warnings > 0:
            print(f"⚠️ {warnings} warnings - Puede funcionar pero con limitaciones")
    print("=" * 80)
    
    return 0 if failed == 0 else 1


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Demo del Sistema Agentic ADK para SQUIT",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Modo interactivo (conversación con el agente)
  %(prog)s
  
  # Demo automática con casos de uso predefinidos
  %(prog)s --demo
  
  # Validar que todo esté configurado correctamente
  %(prog)s --validate
        """
    )
    
    parser.add_argument('--demo', action='store_true',
                       help='Ejecutar demo automática')
    parser.add_argument('--validate', action='store_true',
                       help='Validar configuración del sistema')
    
    args = parser.parse_args()
    
    if args.validate:
        return validate_setup()
    elif args.demo:
        return run_demo()
    else:
        return run_interactive()


if __name__ == "__main__":
    sys.exit(main())
