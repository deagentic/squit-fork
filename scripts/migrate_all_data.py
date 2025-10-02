#!/usr/bin/env python3
"""
Script para migrar todos los datos de BigQuery a Weaviate.

Este script ejecuta la migración completa del codebase legacy
con monitoreo de progreso y manejo de errores robusto.
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv()

# Agregar directorios al path
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))


def print_header():
    """Imprime header del script."""
    print("🚀 SQUIT Agentic RAG - Migración Completa")
    print("=" * 55)
    print(f"📅 Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 Objetivo: Migrar 3.4M objetos SQL BigQuery → Weaviate")
    print()


def verify_prerequisites():
    """Verifica que todos los prerequisitos estén cumplidos."""
    print("🔍 Verificando prerequisitos...")
    
    # Verificar variables de entorno
    required_vars = ["GEMINI_API_KEY", "GOOGLE_APPLICATION_CREDENTIALS"]
    for var in required_vars:
        if not os.getenv(var):
            print(f"❌ Variable faltante: {var}")
            return False
        else:
            print(f"✅ {var}: Configurado")
    
    # Verificar conexión a Weaviate
    try:
        import requests
        response = requests.get("http://weaviate:8080/v1/.well-known/ready", timeout=5)
        if response.status_code == 200:
            print("✅ Weaviate: Conectado y saludable")
        else:
            print(f"❌ Weaviate: Estado {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Weaviate: Error de conexión - {e}")
        return False
    
    print("✅ Todos los prerequisitos cumplidos")
    return True


def get_migration_strategy():
    """Determina la estrategia de migración basada en el tamaño de datos."""
    try:
        from squit_client import BigQueryClient
        
        bq = BigQueryClient()
        stats = bq.get_statistics()
        total_objects = stats.get("total_objects", 0)
        
        print(f"📊 Total de objetos en BigQuery: {total_objects:,}")
        
        # Definir estrategia basada en volumen con paralelismo optimizado
        if total_objects <= 10000:
            strategy = "SMALL"
            batch_size = 200
            parallel_workers = 4
            estimated_time = "15-30 minutos"
        elif total_objects <= 100000:
            strategy = "MEDIUM"
            batch_size = 500
            parallel_workers = 6
            estimated_time = "1-2 horas"
        else:
            strategy = "LARGE"
            batch_size = 500  # Reducido para objetos mega
            parallel_workers = 6  # Reducido para evitar timeouts
            estimated_time = "6-12 horas"
        
        print(f"📋 Estrategia: {strategy}")
        print(f"⚙️  Batch size: {batch_size}")
        print(f"🔄 Workers: {parallel_workers}")
        print(f"⏰ Tiempo estimado: {estimated_time}")
        
        return {
            "strategy": strategy,
            "batch_size": batch_size,
            "parallel_workers": parallel_workers,
            "total_objects": total_objects,
            "estimated_time": estimated_time,
        }
        
    except Exception as e:
        print(f"❌ Error obteniendo estadísticas: {e}")
        return None


def save_checkpoint(phase_name, stats):
    """Guarda punto de control de la migración."""
    import json
    from datetime import datetime
    
    checkpoint = {
        "phase": phase_name,
        "timestamp": datetime.now().isoformat(),
        "stats": stats,
    }
    
    with open("/tmp/migration_checkpoint.json", "w") as f:
        json.dump(checkpoint, f, indent=2)
    
    print(f"💾 Checkpoint guardado: {phase_name}")


def load_checkpoint():
    """Carga el último checkpoint si existe."""
    import json
    import os
    
    if os.path.exists("/tmp/migration_checkpoint.json"):
        with open("/tmp/migration_checkpoint.json", "r") as f:
            checkpoint = json.load(f)
        print(f"📂 Checkpoint encontrado: {checkpoint['phase']} - {checkpoint['timestamp']}")
        return checkpoint
    return None


def execute_migration_phase(phase_name, filters, limit, description):
    """Ejecuta una fase específica de migración con checkpoints."""
    print(f"\n🔄 {phase_name}: {description}")
    print("-" * 50)
    
    # Verificar si esta fase ya se completó
    checkpoint = load_checkpoint()
    if checkpoint and checkpoint.get("phase") == phase_name:
        if checkpoint.get("stats", {}).get("success", 0) > 0:
            print(f"✅ {phase_name} ya completada - saltando...")
            return True
    
    try:
        from agentic_rag import WeaviateClient, IngestionPipeline
        from squit_client import BigQueryClient
        
        # Inicializar componentes
        bq = BigQueryClient()
        wv = WeaviateClient()
        pipeline = IngestionPipeline(bq, wv)
        
        # Configurar schema si es la primera fase
        if phase_name == "FASE 1":
            print("🏗️ Configurando schema...")
            if not wv.create_schema():
                print("❌ Error configurando schema")
                return False
            print("✅ Schema configurado")
        
        # Ejecutar migración
        print(f"📥 Procesando hasta {limit:,} objetos...")
        if filters:
            print(f"🔍 Filtros aplicados: {filters}")
        
        start_time = time.time()
        stats = pipeline.run_full_ingestion(limit=limit, filters=filters)
        end_time = time.time()
        
        duration = end_time - start_time
        
        # Mostrar resultados
        print(f"\n📊 Resultados de {phase_name}:")
        print(f"   • Procesados: {stats['processed']:,}")
        print(f"   • Exitosos: {stats['success']:,}")
        print(f"   • Errores: {stats['errors']:,}")
        print(f"   • Saltados: {stats['skipped']:,}")
        
        if 'embeddings_generated' in stats:
            print(f"   • Embeddings: {stats['embeddings_generated']:,}")
        if 'ai_analysis_completed' in stats:
            print(f"   • Análisis IA: {stats['ai_analysis_completed']:,}")
        
        print(f"   • Duración: {duration/60:.1f} minutos")
        
        # Verificar estado de collections
        collection_stats = wv.get_collection_stats()
        total_migrated = collection_stats.get("CodeObjects", 0)
        print(f"   • Total en Weaviate: {total_migrated:,} objetos")
        
        # Calcular tasa de éxito
        success_rate = (stats['success'] / max(1, stats['processed'])) * 100
        print(f"   • Tasa de éxito: {success_rate:.1f}%")
        
        # Evaluar éxito de la fase
        if success_rate >= 80 and stats['success'] > 0:
            print(f"✅ {phase_name} EXITOSA")
            # Guardar checkpoint del éxito
            save_checkpoint(phase_name, stats)
            return True
        else:
            print(f"❌ {phase_name} FALLÓ")
            return False
            
    except Exception as e:
        print(f"❌ Error en {phase_name}: {e}")
        import traceback
        traceback.print_exc()
        return False


def execute_full_migration():
    """Ejecuta la migración completa en fases."""
    print("\n🚀 Iniciando migración completa...")
    
    # Fase 1: Objetos críticos (PROCEDURES y FUNCTIONS)
    phase1_filters = {
        "object_type": ["PROCEDURE", "FUNCTION"],
    }
    
    if not execute_migration_phase(
        "FASE 1", 
        phase1_filters, 
        50000,  # 50K objetos críticos
        "Procedimientos y Funciones (lógica de negocio)"
    ):
        return False
    
    # Fase 2: Views importantes
    phase2_filters = {
        "object_type": ["VIEW"],
    }
    
    if not execute_migration_phase(
        "FASE 2", 
        phase2_filters, 
        30000,  # 30K views
        "Vistas y consultas complejas"
    ):
        return False
    
    # Fase 3: Triggers y constraints
    phase3_filters = {
        "object_type": ["TRIGGER", "INDEX"],
    }
    
    if not execute_migration_phase(
        "FASE 3", 
        phase3_filters, 
        20000,  # 20K triggers/indexes
        "Triggers e índices"
    ):
        return False
    
    # Fase 4: Resto de objetos (sin límite)
    phase4_filters = None  # Sin filtros = todos los objetos restantes
    
    if not execute_migration_phase(
        "FASE 4", 
        phase4_filters, 
        None,  # Sin límite = todos
        "Objetos restantes (tablas, etc.)"
    ):
        return False
    
    return True


def generate_migration_report():
    """Genera reporte final de migración."""
    print("\n📋 REPORTE FINAL DE MIGRACIÓN")
    print("=" * 55)
    
    try:
        from agentic_rag import WeaviateClient
        
        wv = WeaviateClient()
        collection_stats = wv.get_collection_stats()
        
        print("📊 Estado final de collections:")
        total_objects = 0
        for name, count in collection_stats.items():
            print(f"   • {name}: {count:,} objetos")
            if name == "CodeObjects":
                total_objects = count
        
        print(f"\n📈 Resumen:")
        print(f"   • Total migrado: {total_objects:,} objetos")
        print(f"   • Vector database: Weaviate 1.27.0")
        print(f"   • Embeddings: Gemini embedding-001 (768D)")
        print(f"   • LLM: Gemini 2.5 Flash")
        
        # Probar búsqueda final
        if total_objects > 0:
            print(f"\n🔍 Prueba de búsqueda final:")
            results = wv.search_code_objects(
                query="usuario autenticacion login",
                limit=5,
                hybrid=True,
            )
            
            print(f"   ✅ Encontrados: {len(results)} objetos relevantes")
            for i, result in enumerate(results, 1):
                name = result.get("object_name", "Unknown")
                obj_type = result.get("object_type", "Unknown")
                server = result.get("server", "Unknown")
                print(f"      {i}. {name} ({obj_type}) - {server}")
        
        print(f"\n🎉 ¡MIGRACIÓN COMPLETADA EXITOSAMENTE!")
        print(f"🚀 Sistema Agentic RAG listo para uso en producción")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generando reporte: {e}")
        return False


def main():
    """Función principal de migración."""
    print_header()
    
    # Verificar prerequisitos
    if not verify_prerequisites():
        print("\n❌ Prerequisitos no cumplidos")
        print("🔧 Ejecuta 'make agentic-setup' primero")
        sys.exit(1)
    
    # Obtener estrategia de migración
    strategy = get_migration_strategy()
    if not strategy:
        print("\n❌ No se pudo determinar estrategia de migración")
        sys.exit(1)
    
    # Confirmación del usuario
    print(f"\n⚠️  CONFIRMACIÓN DE MIGRACIÓN")
    print(f"📊 Se migrarán ~{strategy['total_objects']:,} objetos")
    print(f"⏰ Tiempo estimado: {strategy['estimated_time']}")
    print(f"💰 Costo estimado Gemini: ~$10-50 USD (embeddings)")
    print()
    
    # En contenedor Docker, proceder automáticamente
    # En modo interactivo, se podría agregar confirmación
    
    print("🚀 Iniciando migración automática...")
    
    # Ejecutar migración completa
    start_total = time.time()
    
    if execute_full_migration():
        end_total = time.time()
        total_duration = end_total - start_total
        
        print(f"\n⏰ Duración total: {total_duration/3600:.1f} horas")
        
        # Generar reporte final
        if generate_migration_report():
            print("\n📋 Próximos pasos:")
            print("   1. Explorar datos: make agentic-dev")
            print("   2. Probar consultas: make agentic-demo-full")
            print("   3. Proceder a Phase 2: Agentes avanzados")
            
            sys.exit(0)
        else:
            print("\n⚠️  Migración completada pero reporte falló")
            sys.exit(1)
    else:
        print("\n❌ Migración falló")
        print("🔧 Revisar logs para detalles")
        sys.exit(1)


if __name__ == "__main__":
    main()
