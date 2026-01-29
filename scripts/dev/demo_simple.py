#!/usr/bin/env python3
"""
Demo Simple del Sistema Agentic SQUIT.

Script limpio para probar el sistema con queries reales.
SIN hardcodear, SIN mocks, SIN fallbacks.

Uso:
    python3 scripts/demo_simple.py
"""

import os
import sys
from pathlib import Path

# Cargar .env
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                value = value.strip('"').strip("'")
                if key == 'GOOGLE_APPLICATION_CREDENTIALS' and not value.startswith('/'):
                    value = str((Path(__file__).parent.parent / value).absolute())
                os.environ[key] = value

# Agregar app al path
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from agentic_adk import MasterAgent


def print_header():
    """Imprime header."""
    print("\n" + "=" * 80)
    print("🎯 SQUIT - \"SQL Quit\": Democratizando Código Legacy")
    print("=" * 80)
    print("🤖 Motor: Búsqueda Inteligente Multi-Etapa con Gemini 2.5 Flash")
    print("📊 Datos: 2.9M objetos SQL reales en BigQuery")
    print("🔍 Estrategia: Router LLM → Multi-Query → Hybrid Search → Reranking → Iteración")
    print("=" * 80)


def run_query(agent: MasterAgent, query: str, query_num: int):
    """Ejecuta una query y muestra resultados."""
    print(f"\n{'=' * 80}")
    print(f"QUERY {query_num}: {query}")
    print("=" * 80)
    print("🔄 Procesando con motor inteligente...")
    print("   1. Router LLM extrayendo keywords...")
    print("   2. Multi-query generando variaciones...")
    print("   3. Hybrid search en código SQL...")
    print("   4. Reranking resultados...")
    print()
    
    response = agent.process(query)
    
    print("🤖 RESPUESTA:")
    print("-" * 80)
    print(response)
    print("-" * 80)
    print(f"📊 Longitud: {len(response)} caracteres")


def main():
    """Función principal."""
    print_header()
    
    # Validar configuración
    required_vars = ['GEMINI_API_KEY', 'GOOGLE_CLOUD_PROJECT']
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print(f"\n❌ ERROR: Faltan variables de ambiente: {', '.join(missing)}")
        print("\n💡 Configura en .env:")
        for var in missing:
            print(f"   {var}=tu-valor")
        return 1
    
    print("\n✅ Configuración validada")
    print(f"   - GEMINI_API_KEY: ***{os.getenv('GEMINI_API_KEY', '')[-4:]}")
    print(f"   - GOOGLE_CLOUD_PROJECT: {os.getenv('GOOGLE_CLOUD_PROJECT')}")
    
    # Inicializar agente
    print("\n🚀 Inicializando MasterAgent...")
    try:
        agent = MasterAgent()
        print("✅ Agente listo con motor de búsqueda multi-etapa")
    except Exception as e:
        print(f"\n❌ ERROR inicializando agente: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Queries de demostración
    demo_queries = [
        "¿Dónde está la lógica de inventario en el código?",
        "Busca procedimientos que trabajen con fechas y vencimientos",
        "Procedimientos de ventas y facturación",
        "Código SQL que calcule precios o costos",
        "¿Qué objetos trabajan con clientes?",
    ]
    
    print(f"\n📋 Ejecutando {len(demo_queries)} queries de demostración...")
    input("\n[Presiona Enter para comenzar...]")
    
    for i, query in enumerate(demo_queries, 1):
        run_query(agent, query, i)
        
        if i < len(demo_queries):
            input(f"\n[Presiona Enter para query {i+1}...]")
    
    # Resumen final
    print("\n" + "=" * 80)
    print("✅ DEMO COMPLETADA CON ÉXITO")
    print("=" * 80)
    print("\n📊 Estadísticas:")
    print(f"   - Queries ejecutadas: {len(demo_queries)}")
    print(f"   - Motor: Búsqueda inteligente multi-etapa")
    print(f"   - Modelo: Gemini 2.5 Flash")
    print(f"   - Datos: 2.9M rows reales en BigQuery")
    print("\n🎯 Modo interactivo disponible:")
    print("   python3 scripts/demo_agentic_adk.py")
    print("\n" + "=" * 80)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
