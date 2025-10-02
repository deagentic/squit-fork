#!/usr/bin/env python3
"""
Script para monitorear el progreso de migración en tiempo real.

Muestra estadísticas actualizadas de las collections de Weaviate
durante el proceso de migración.
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


def clear_screen():
    """Limpia la pantalla."""
    os.system('clear' if os.name == 'posix' else 'cls')


def get_collection_stats():
    """Obtiene estadísticas actuales de Weaviate."""
    try:
        from agentic_rag import WeaviateClient
        
        wv = WeaviateClient()
        stats = wv.get_collection_stats()
        wv.close()
        
        return stats
        
    except Exception as e:
        return {"error": str(e)}


def display_stats(stats, iteration):
    """Muestra estadísticas formateadas."""
    clear_screen()
    
    print("📊 SQUIT Agentic RAG - Monitor de Migración")
    print("=" * 55)
    print(f"🕐 Actualización #{iteration} - {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    if "error" in stats:
        print(f"❌ Error obteniendo estadísticas: {stats['error']}")
        return
    
    total_objects = 0
    
    print("📈 Estado de Collections:")
    for collection, count in stats.items():
        print(f"   • {collection}: {count:,} objetos")
        if collection == "CodeObjects":
            total_objects = count
    
    print()
    print(f"📊 Total migrado: {total_objects:,} objetos")
    
    # Estimaciones
    if total_objects > 0:
        print(f"🎯 Progreso estimado:")
        
        # Estimar progreso basado en tipos de objetos esperados
        expected_procedures = 2_111_700
        expected_tables = 609_684
        expected_views = 423_882
        expected_total = 3_416_808
        
        progress_pct = (total_objects / expected_total) * 100
        print(f"   • Completado: {progress_pct:.1f}%")
        
        if progress_pct > 0:
            remaining = expected_total - total_objects
            print(f"   • Restantes: {remaining:,} objetos")
            
            # Estimar tiempo restante (muy aproximado)
            if iteration > 1:  # Solo después de algunas mediciones
                objects_per_minute = total_objects / (iteration * 0.5)  # Asumiendo 30s por iteración
                if objects_per_minute > 0:
                    remaining_minutes = remaining / objects_per_minute
                    print(f"   • Tiempo estimado restante: {remaining_minutes/60:.1f} horas")
    
    print()
    print("🔄 Actualizando cada 30 segundos...")
    print("💡 Presiona Ctrl+C para salir")


def monitor_migration():
    """Monitorea la migración en tiempo real."""
    print("🔍 Iniciando monitoreo de migración...")
    print("📊 Actualizaciones cada 30 segundos")
    print()
    
    iteration = 0
    
    try:
        while True:
            iteration += 1
            
            # Obtener estadísticas actuales
            stats = get_collection_stats()
            
            # Mostrar estadísticas
            display_stats(stats, iteration)
            
            # Esperar 30 segundos
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\n\n👋 Monitoreo detenido por el usuario")
        
        # Mostrar estadísticas finales
        final_stats = get_collection_stats()
        if "error" not in final_stats:
            total = final_stats.get("CodeObjects", 0)
            print(f"📊 Estado final: {total:,} objetos migrados")
        
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error en monitoreo: {e}")
        sys.exit(1)


def main():
    """Función principal."""
    monitor_migration()


if __name__ == "__main__":
    main()
