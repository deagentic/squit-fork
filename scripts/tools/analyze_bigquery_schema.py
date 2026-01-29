#!/usr/bin/env python3
"""
Script para analizar el schema y datos de BigQuery antes de la migración.

Este script obtiene información detallada sobre la estructura de datos
para optimizar el proceso de migración.
"""

import sys
from pathlib import Path

# Agregar directorios al path
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from squit_client import BigQueryClient
import pandas as pd
import json


def analyze_table_schema():
    """Analiza el schema completo de la tabla."""
    print("=" * 80)
    print("📊 ANÁLISIS DEL SCHEMA DE BIGQUERY")
    print("=" * 80)
    
    try:
        client = BigQueryClient()
        print("✅ Cliente BigQuery inicializado")
        
        # Obtener información de la tabla
        table_info = client.get_table_info()
        
        print(f"\n📋 INFORMACIÓN GENERAL:")
        print(f"   • Proyecto: {table_info['project']}")
        print(f"   • Dataset: {table_info['dataset']}")
        print(f"   • Tabla: {table_info['table_id']}")
        print(f"   • Registros: {table_info['num_rows']:,}")
        print(f"   • Tamaño: {table_info['num_bytes']:,} bytes")
        print(f"   • Ubicación: {table_info['location']}")
        
        # Mostrar schema detallado
        print(f"\n🏗️ SCHEMA DE LA TABLA ({len(table_info['schema'])} columnas):")
        print("-" * 60)
        for i, (name, field_type, description) in enumerate(table_info['schema'], 1):
            desc = description if description else "Sin descripción"
            print(f"   {i:2d}. {name:<20} | {field_type:<15} | {desc}")
        
        return table_info
        
    except Exception as e:
        print(f"❌ Error obteniendo schema: {e}")
        return None


def detect_code_column(client):
    """Detecta qué columna contiene el código SQL."""
    try:
        # Intentar con sql_code primero
        test_query = f"SELECT sql_code FROM `{client.config.full_table_id}` LIMIT 1"
        client.execute_query(test_query)
        return "sql_code"
    except:
        try:
            # Intentar con definition
            test_query = f"SELECT definition FROM `{client.config.full_table_id}` LIMIT 1"
            client.execute_query(test_query)
            return "definition"
        except:
            # Fallback - revisar schema
            table_info = client.get_table_info()
            for name, field_type, desc in table_info['schema']:
                if 'code' in name.lower() or 'definition' in name.lower():
                    return name
            return "sql_code"  # Fallback por defecto


def analyze_data_sample():
    """Analiza una muestra de datos para entender su estructura."""
    print(f"\n" + "=" * 80)
    print("🔍 ANÁLISIS DE MUESTRA DE DATOS")
    print("=" * 80)
    
    try:
        client = BigQueryClient()
        
        # Detectar columna de código
        code_column = detect_code_column(client)
        print(f"🔍 Columna de código detectada: {code_column}")
        
        # Query para obtener muestra representativa
        query = f"""
        SELECT 
            server,
            database,
            schema,
            object_name,
            object_type,
            last_modified,
            CHAR_LENGTH({code_column}) as code_length,
            SUBSTR({code_column}, 1, 200) as code_preview
        FROM `{client.config.full_table_id}`
        WHERE {code_column} IS NOT NULL
        ORDER BY RAND()
        LIMIT 10
        """
        
        print("🔄 Ejecutando query de muestra...")
        sample_data = client.execute_query(query)
        
        if sample_data.empty:
            print("⚠️ No se obtuvieron datos de muestra")
            return None
        
        print(f"✅ Obtenidos {len(sample_data)} registros de muestra")
        
        # Análisis de la muestra
        print(f"\n📊 ANÁLISIS DE LA MUESTRA:")
        print("-" * 60)
        
        # Distribución por tipo de objeto
        type_dist = sample_data['object_type'].value_counts()
        print(f"\n🏷️ TIPOS DE OBJETOS EN MUESTRA:")
        for obj_type, count in type_dist.items():
            print(f"   • {obj_type}: {count}")
        
        # Distribución por servidor
        server_dist = sample_data['server'].value_counts()
        print(f"\n🖥️ SERVIDORES EN MUESTRA:")
        for server, count in server_dist.items():
            print(f"   • {server}: {count}")
        
        # Estadísticas de longitud de código SQL
        print(f"\n📏 ESTADÍSTICAS DE LONGITUD SQL:")
        print(f"   • Promedio: {sample_data['code_length'].mean():.0f} caracteres")
        print(f"   • Mínimo: {sample_data['code_length'].min():,} caracteres")
        print(f"   • Máximo: {sample_data['code_length'].max():,} caracteres")
        print(f"   • Mediana: {sample_data['code_length'].median():.0f} caracteres")
        
        # Mostrar algunos ejemplos de código
        print(f"\n💾 EJEMPLOS DE CÓDIGO SQL:")
        print("-" * 60)
        for i, row in sample_data.head(3).iterrows():
            print(f"\n📄 Ejemplo {i+1}: {row['object_name']} ({row['object_type']})")
            print(f"   Servidor: {row['server']} | Base: {row['database']}")
            print(f"   Longitud: {row['code_length']:,} chars")
            print(f"   Preview: {row['code_preview'][:150]}...")
        
        return sample_data
        
    except Exception as e:
        print(f"❌ Error analizando muestra: {e}")
        return None


def analyze_data_distribution():
    """Analiza la distribución completa de datos."""
    print(f"\n" + "=" * 80)
    print("📈 ANÁLISIS DE DISTRIBUCIÓN COMPLETA")
    print("=" * 80)
    
    try:
        client = BigQueryClient()
        
        # Estadísticas generales
        stats = client.get_statistics()
        print(f"📊 ESTADÍSTICAS GENERALES:")
        print(f"   • Total objetos: {stats['total_objects']:,}")
        print(f"   • Servidores únicos: {stats['unique_servers']:,}")
        print(f"   • Bases de datos: {stats['unique_databases']:,}")
        print(f"   • Tipos de objetos: {stats['unique_object_types']:,}")
        
        # Top tipos de objetos
        top_types = client.get_top_objects_by_type(limit=15)
        print(f"\n🏷️ TOP TIPOS DE OBJETOS:")
        print("-" * 40)
        for _, row in top_types.iterrows():
            print(f"   • {row['object_type']:<20} | {row['count']:>8,} ({row['percentage']:>5.1f}%)")
        
        # Top servidores
        top_servers = client.get_top_servers(limit=10)
        print(f"\n🖥️ TOP SERVIDORES:")
        print("-" * 50)
        for _, row in top_servers.iterrows():
            print(f"   • {row['server']:<25} | {row['object_count']:>8,} objetos")
        
        return {
            'stats': stats,
            'top_types': top_types,
            'top_servers': top_servers
        }
        
    except Exception as e:
        print(f"❌ Error analizando distribución: {e}")
        return None


def analyze_problematic_data():
    """Analiza datos que pueden causar problemas en la migración."""
    print(f"\n" + "=" * 80)
    print("⚠️ ANÁLISIS DE DATOS PROBLEMÁTICOS")
    print("=" * 80)
    
    try:
        client = BigQueryClient()
        
        # Detectar columna de código
        code_column = detect_code_column(client)
        
        # Objetos con código SQL muy largo
        query_long = f"""
        SELECT 
            object_name,
            object_type,
            server,
            CHAR_LENGTH({code_column}) as length
        FROM `{client.config.full_table_id}`
        WHERE CHAR_LENGTH({code_column}) > 50000
        ORDER BY length DESC
        LIMIT 10
        """
        
        print("🔄 Analizando objetos con código muy largo...")
        long_objects = client.execute_query(query_long)
        
        if not long_objects.empty:
            print(f"⚠️ OBJETOS CON CÓDIGO MUY LARGO (>{50000:,} chars):")
            for _, row in long_objects.iterrows():
                print(f"   • {row['object_name']} ({row['object_type']}) - {row['length']:,} chars")
        else:
            print("✅ No hay objetos con código excesivamente largo")
        
        # Objetos con caracteres especiales problemáticos
        query_special = f"""
        SELECT 
            object_name,
            object_type,
            server,
            CASE 
                WHEN {code_column} LIKE '%\\n%' THEN 'newlines'
                WHEN {code_column} LIKE '%\\"%' THEN 'double_quotes'
                WHEN {code_column} LIKE "%'%" THEN 'single_quotes'
                WHEN {code_column} LIKE '%\\\\%' THEN 'backslashes'
                ELSE 'other'
            END as issue_type
        FROM `{client.config.full_table_id}`
        WHERE {code_column} LIKE '%\\n%' 
           OR {code_column} LIKE '%\\"%' 
           OR {code_column} LIKE "%'%"
           OR {code_column} LIKE '%\\\\%'
        LIMIT 20
        """
        
        print(f"\n🔄 Analizando objetos con caracteres especiales...")
        special_objects = client.execute_query(query_special)
        
        if not special_objects.empty:
            issue_counts = special_objects['issue_type'].value_counts()
            print(f"⚠️ OBJETOS CON CARACTERES ESPECIALES:")
            for issue, count in issue_counts.items():
                print(f"   • {issue}: {count} objetos")
        else:
            print("✅ No se detectaron caracteres especiales problemáticos")
        
        return {
            'long_objects': long_objects,
            'special_objects': special_objects
        }
        
    except Exception as e:
        print(f"❌ Error analizando datos problemáticos: {e}")
        return None


def generate_migration_recommendations(analysis_results):
    """Genera recomendaciones para la migración basadas en el análisis."""
    print(f"\n" + "=" * 80)
    print("💡 RECOMENDACIONES PARA LA MIGRACIÓN")
    print("=" * 80)
    
    if not analysis_results:
        print("❌ No se pueden generar recomendaciones sin datos de análisis")
        return
    
    stats = analysis_results.get('stats', {})
    total_objects = stats.get('total_objects', 0)
    
    print(f"📊 Basado en {total_objects:,} objetos totales:")
    print()
    
    # Recomendaciones de paralelismo
    if total_objects > 1000000:
        print(f"🚀 PARALELISMO:")
        print(f"   • Workers recomendados: 12-16")
        print(f"   • Batch size: 2000-3000")
        print(f"   • Tiempo estimado: 6-12 horas")
    elif total_objects > 100000:
        print(f"🚀 PARALELISMO:")
        print(f"   • Workers recomendados: 8-12")
        print(f"   • Batch size: 1000-2000")
        print(f"   • Tiempo estimado: 2-6 horas")
    else:
        print(f"🚀 PARALELISMO:")
        print(f"   • Workers recomendados: 4-8")
        print(f"   • Batch size: 500-1000")
        print(f"   • Tiempo estimado: 30-120 minutos")
    
    print(f"\n💾 CHECKPOINTS:")
    print(f"   • Guardar cada 10,000 objetos procesados")
    print(f"   • Implementar recuperación automática")
    print(f"   • Logs detallados por fase")
    
    print(f"\n⚠️ MANEJO DE ERRORES:")
    print(f"   • Timeout Gemini: 60 segundos")
    print(f"   • Reintentos: 3 por objeto")
    print(f"   • Fallback para análisis JSON")
    
    print(f"\n🔧 OPTIMIZACIONES:")
    print(f"   • Filtrar por tipos más importantes primero")
    print(f"   • Procesar objetos grandes por separado")
    print(f"   • Usar rate limiting para Gemini API")


def main():
    """Función principal del análisis."""
    print("🔍 SQUIT - Análisis Pre-Migración de BigQuery")
    print("Analizando schema y datos para optimizar la migración...")
    print()
    
    # Ejecutar análisis
    schema_info = analyze_table_schema()
    sample_data = analyze_data_sample()
    distribution_data = analyze_data_distribution()
    problematic_data = analyze_problematic_data()
    
    # Generar recomendaciones
    analysis_results = {
        'schema': schema_info,
        'sample': sample_data,
        'distribution': distribution_data,
        'problematic': problematic_data
    }
    
    generate_migration_recommendations(distribution_data)
    
    print(f"\n" + "=" * 80)
    print("✅ ANÁLISIS COMPLETADO")
    print("=" * 80)
    print("El script de migración está listo para ejecutar con las configuraciones optimizadas.")
    print("Para ejecutar la migración: make migrate-all")
    print("Para monitorear: make monitor-migration")


if __name__ == "__main__":
    main()
