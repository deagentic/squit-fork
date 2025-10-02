#!/usr/bin/env python3
"""
Script para búsquedas vectoriales en BigQuery.

Este script permite realizar búsquedas semánticas avanzadas
en los chunks generados usando BigQuery Vector Search nativo.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Agregar directorios al path
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from bigquery_vector.config import BigQueryVectorConfig
from bigquery_vector.vector_search import BigQueryVectorSearch


def print_header():
    """Imprime header del script."""
    print("🔍 SQUIT - Vector Search 100% BigQuery")
    print("=" * 60)
    print(f"📅 Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 Objetivo: Búsquedas semánticas inteligentes")
    print("🔧 Tecnología: BigQuery Vector Search + Gemini")
    print()


def demo_searches():
    """Ejecuta búsquedas de demostración."""
    config = BigQueryVectorConfig()
    search = BigQueryVectorSearch(config)
    
    # Búsquedas de ejemplo
    demo_queries = [
        {
            "query": "autenticacion usuario login password",
            "description": "🔐 Búsqueda: Autenticación de usuarios",
            "filters": {"object_types": ["PROCEDURE", "FUNCTION"]}
        },
        {
            "query": "venta factura cliente pedido",
            "description": "💰 Búsqueda: Procesos de ventas",
            "filters": {"business_domains": ["ventas"]}
        },
        {
            "query": "inventario stock almacen producto",
            "description": "📦 Búsqueda: Gestión de inventario",
            "filters": {"semantic_types": ["complex_query", "stored_procedure"]}
        },
        {
            "query": "reporte dashboard analytics estadisticas",
            "description": "📊 Búsqueda: Reportes y analytics",
            "filters": {"min_complexity": 5.0}
        },
    ]
    
    for demo in demo_queries:
        print(demo["description"])
        print("-" * 50)
        
        try:
            results = search.semantic_search(
                query=demo["query"],
                limit=5,
                **demo["filters"]
            )
            
            if results:
                print(f"✅ Encontrados {len(results)} resultados:")
                for i, result in enumerate(results, 1):
                    print(f"\n  {i}. {result['object_name']} ({result['object_type']})")
                    print(f"     🏢 Dominio: {result['business_domain']}")
                    print(f"     🎯 Tipo: {result['semantic_type']}")
                    print(f"     📊 Complejidad: {result['complexity_score']:.1f}")
                    print(f"     📝 Resumen: {result['semantic_summary']}")
                    if 'hybrid_score' in result:
                        print(f"     🎯 Relevancia: {result['hybrid_score']:.3f}")
                    print(f"     📄 Preview: {result['chunk_preview'][:100]}...")
            else:
                print("❌ No se encontraron resultados")
            
        except Exception as e:
            print(f"❌ Error en búsqueda: {e}")
        
        print()


def interactive_search():
    """Modo de búsqueda interactiva."""
    config = BigQueryVectorConfig()
    search = BigQueryVectorSearch(config)
    
    print("🔍 MODO INTERACTIVO")
    print("=" * 30)
    print("Ingresa tu consulta o 'exit' para salir")
    print()
    
    while True:
        try:
            query = input("🔍 Búsqueda: ").strip()
            
            if query.lower() in ['exit', 'quit', 'salir']:
                print("👋 ¡Hasta luego!")
                break
            
            if not query:
                continue
            
            print(f"\n🔄 Buscando: {query}")
            results = search.semantic_search(query=query, limit=10, use_hybrid=True)
            
            if results:
                print(f"✅ {len(results)} resultados encontrados:\n")
                
                for i, result in enumerate(results, 1):
                    score = result.get('hybrid_score', result.get('distance', 0))
                    print(f"{i:2d}. {result['object_name']} ({result['object_type']})")
                    print(f"    📊 Score: {score:.3f} | 🏢 {result['business_domain']} | 🎯 {result['semantic_type']}")
                    print(f"    📝 {result['semantic_summary']}")
                    print(f"    💾 {result['chunk_preview'][:150]}...")
                    print()
                
                # Opción para ver más detalles
                detail_choice = input("¿Ver detalles de algún resultado? (número o Enter): ").strip()
                if detail_choice.isdigit():
                    idx = int(detail_choice) - 1
                    if 0 <= idx < len(results):
                        result = results[idx]
                        print(f"\n📄 DETALLES COMPLETOS:")
                        print(f"Objeto: {result['object_name']}")
                        print(f"Tipo: {result['object_type']}")
                        print(f"Chunk: {result['chunk_index']}/{result['total_chunks']}")
                        
                        # Obtener chunks completos del objeto
                        chunks = search.get_object_chunks(result['parent_object_id'])
                        print(f"\n🧩 CHUNKS DEL OBJETO ({len(chunks)} total):")
                        for chunk in chunks:
                            marker = "👉" if chunk['chunk_id'] == result['chunk_id'] else "  "
                            print(f"{marker} Chunk {chunk['chunk_index']}: {chunk['semantic_summary']}")
            else:
                print("❌ No se encontraron resultados")
            
            print("\n" + "-" * 50)
            
        except KeyboardInterrupt:
            print("\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


def analyze_patterns():
    """Analiza patrones en el codebase."""
    config = BigQueryVectorConfig()
    search = BigQueryVectorSearch(config)
    
    print("📊 ANÁLISIS DE PATRONES DEL CODEBASE")
    print("=" * 60)
    
    try:
        patterns = search.analyze_codebase_patterns()
        
        # Análisis por dominio de negocio
        print("\n🏢 ANÁLISIS POR DOMINIO DE NEGOCIO:")
        business_domains = patterns.get('business_domains', [])
        for domain in sorted(business_domains, key=lambda x: x['chunks_count'], reverse=True):
            print(f"  • {domain['business_domain'].upper()}")
            print(f"    └─ {domain['chunks_count']:,} chunks | {domain['objects_count']:,} objetos")
            print(f"    └─ Complejidad promedio: {domain['avg_complexity']:.1f}")
            print(f"    └─ Tipos: {', '.join(domain['semantic_types'])}")
        
        # Análisis por tipo semántico
        print("\n🎯 ANÁLISIS POR TIPO SEMÁNTICO:")
        semantic_types = patterns.get('semantic_types', [])
        for sem_type in sorted(semantic_types, key=lambda x: x['chunks_count'], reverse=True):
            print(f"  • {sem_type['semantic_type'].upper()}")
            print(f"    └─ {sem_type['chunks_count']:,} chunks")
            print(f"    └─ Complejidad: {sem_type['avg_complexity']:.1f}")
            print(f"    └─ Tamaño promedio: {sem_type['avg_chunk_length']:.0f} chars")
        
        # Objetos más complejos
        print("\n🔥 TOP OBJETOS MÁS COMPLEJOS:")
        complex_objects = patterns.get('complex_objects', [])
        for i, obj in enumerate(complex_objects, 1):
            print(f"  {i:2d}. {obj['object_name']} ({obj['object_type']})")
            print(f"      └─ Complejidad: {obj['max_complexity']:.1f} | {obj['chunks_count']} chunks")
            print(f"      └─ Dominio: {obj['business_domain']}")
        
    except Exception as e:
        print(f"❌ Error analizando patrones: {e}")


def create_search_functions():
    """Crea funciones SQL reutilizables."""
    config = BigQueryVectorConfig()
    search = BigQueryVectorSearch(config)
    
    print("🔧 CREANDO FUNCIONES SQL REUTILIZABLES")
    print("=" * 60)
    
    try:
        functions = search.create_search_functions()
        
        print("✅ Funciones creadas exitosamente:")
        for name, full_name in functions.items():
            print(f"  • {name}: {full_name}")
        
        print(f"\n📝 EJEMPLOS DE USO:")
        print(f"```sql")
        print(f"-- Búsqueda semántica básica")
        print(f"SELECT * FROM `{config.PROJECT_ID}.{config.DATASET_ID}.semantic_search`(")
        print(f"  'autenticacion usuario login', 10")
        print(f");")
        print()
        print(f"-- Búsqueda por dominio")
        print(f"SELECT * FROM `{config.PROJECT_ID}.{config.DATASET_ID}.search_by_domain`(")
        print(f"  'factura venta cliente', 'ventas', 5")
        print(f");")
        print(f"```")
        
    except Exception as e:
        print(f"❌ Error creando funciones: {e}")


def main():
    """Función principal."""
    print_header()
    
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        
        if mode == "demo":
            demo_searches()
        elif mode == "interactive":
            interactive_search()
        elif mode == "patterns":
            analyze_patterns()
        elif mode == "functions":
            create_search_functions()
        else:
            print(f"❌ Modo desconocido: {mode}")
            print("Modos disponibles: demo, interactive, patterns, functions")
            sys.exit(1)
    else:
        # Modo por defecto: demo
        demo_searches()
        
        print("\n🎯 OTROS MODOS DISPONIBLES:")
        print("  • python3 scripts/bigquery_search_chunks.py interactive")
        print("  • python3 scripts/bigquery_search_chunks.py patterns") 
        print("  • python3 scripts/bigquery_search_chunks.py functions")


if __name__ == "__main__":
    main()
