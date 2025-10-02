#!/usr/bin/env python3
"""
Script para verificar acceso a BigQuery y configuración correcta.

Este script valida que podemos acceder a los datos antes de ejecutar pruebas.
"""

import sys
from pathlib import Path
from datetime import datetime

# Agregar directorios al path
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from squit_client import BigQueryClient
from bigquery_vector.config import BigQueryVectorConfig
from google.cloud import bigquery


def print_header():
    """Imprime header del script."""
    print("🔍 SQUIT - Verificación de Acceso BigQuery")
    print("=" * 60)
    print(f"📅 Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 Objetivo: Validar configuración y acceso")
    print()


def verify_credentials():
    """Verifica credenciales de Google Cloud."""
    print("🔐 VERIFICANDO CREDENCIALES")
    print("-" * 30)
    
    try:
        client = bigquery.Client()
        
        # Test básico de conexión
        test_query = "SELECT 1 as test"
        result = list(client.query(test_query))
        
        print("✅ Credenciales válidas")
        print(f"   • Proyecto activo: {client.project}")
        print(f"   • Ubicación por defecto: {client.location or 'US'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error de credenciales: {e}")
        print("\n🔧 SOLUCIONES:")
        print("   1. Verifica GOOGLE_APPLICATION_CREDENTIALS")
        print("   2. Ejecuta: gcloud auth application-default login")
        print("   3. Verifica permisos BigQuery")
        return False


def verify_dataset_access():
    """Verifica acceso al dataset y tabla principal."""
    print("\n📊 VERIFICANDO ACCESO A DATOS")
    print("-" * 35)
    
    try:
        # Usar configuración original del cliente
        squit_client = BigQueryClient()
        
        print(f"🔍 Configuración SQUIT Client:")
        print(f"   • Proyecto: {squit_client.config.PROJECT_ID}")
        print(f"   • Dataset: {squit_client.config.DATASET_ID}")
        print(f"   • Tabla: {squit_client.config.TABLE_ID}")
        print(f"   • Full ID: {squit_client.config.full_table_id}")
        
        # Verificar acceso a la tabla
        table_info = squit_client.get_table_info()
        
        print(f"\n✅ Acceso a tabla confirmado:")
        print(f"   • Registros: {table_info['num_rows']:,}")
        print(f"   • Tamaño: {table_info['num_bytes']:,} bytes")
        print(f"   • Ubicación: {table_info['location']}")
        print(f"   • Columnas: {len(table_info['schema'])}")
        
        # Mostrar schema resumido
        print(f"\n📋 SCHEMA PRINCIPAL:")
        for i, (name, field_type, desc) in enumerate(table_info['schema'][:8], 1):
            print(f"   {i:2d}. {name:<15} | {field_type}")
        if len(table_info['schema']) > 8:
            print(f"   ... y {len(table_info['schema']) - 8} columnas más")
        
        return True
        
    except Exception as e:
        print(f"❌ Error accediendo a datos: {e}")
        print("\n🔧 POSIBLES CAUSAS:")
        print("   1. Dataset no existe o nombre incorrecto")
        print("   2. Sin permisos de lectura")
        print("   3. Tabla en ubicación diferente")
        print("   4. Proyecto incorrecto")
        return False


def verify_sample_data():
    """Verifica que podemos obtener datos de muestra."""
    print("\n🎯 VERIFICANDO DATOS DE MUESTRA")
    print("-" * 35)
    
    try:
        squit_client = BigQueryClient()
        
        # Query simple para obtener muestra
        sample_query = f"""
        SELECT 
          object_type,
          COUNT(*) as count,
          AVG(LENGTH(sql_code)) as avg_length,
          MIN(LENGTH(sql_code)) as min_length,
          MAX(LENGTH(sql_code)) as max_length
        FROM `{squit_client.config.full_table_id}`
        WHERE sql_code IS NOT NULL
        GROUP BY object_type
        ORDER BY count DESC
        LIMIT 10
        """
        
        print("🔄 Ejecutando query de muestra...")
        sample_results = squit_client.execute_query(sample_query)
        
        if not sample_results.empty:
            print("✅ Datos de muestra obtenidos:")
            print(f"{'Tipo':<12} {'Count':<8} {'Prom':<8} {'Min':<6} {'Max':<10}")
            print("-" * 50)
            
            total_objects = 0
            for _, row in sample_results.iterrows():
                total_objects += row['count']
                print(f"{row['object_type']:<12} {row['count']:<8} "
                      f"{row['avg_length']:<8.0f} {row['min_length']:<6} {row['max_length']:<10}")
            
            print("-" * 50)
            print(f"📊 Total objetos disponibles: {total_objects:,}")
            
            # Verificar objetos grandes para prueba
            large_objects_query = f"""
            SELECT COUNT(*) as mega_count
            FROM `{squit_client.config.full_table_id}`
            WHERE LENGTH(sql_code) > 1000000
            """
            
            large_result = squit_client.execute_query(large_objects_query)
            mega_count = large_result.iloc[0]['mega_count'] if not large_result.empty else 0
            
            print(f"🔥 Objetos mega (>1M chars): {mega_count}")
            
            if mega_count > 0:
                print("✅ Datos suficientes para prueba completa")
            else:
                print("⚠️  No hay objetos mega - ajustaremos umbrales")
            
            return True
        else:
            print("❌ No se obtuvieron datos de muestra")
            return False
            
    except Exception as e:
        print(f"❌ Error obteniendo muestra: {e}")
        return False


def suggest_corrections():
    """Sugiere correcciones basadas en la configuración detectada."""
    print("\n🔧 DIAGNÓSTICO Y CORRECCIONES")
    print("-" * 40)
    
    try:
        # Intentar listar datasets disponibles
        client = bigquery.Client()
        datasets = list(client.list_datasets())
        
        print("📊 DATASETS DISPONIBLES:")
        for dataset in datasets:
            print(f"   • {dataset.dataset_id}")
            
            # Verificar si alguno contiene tablas SQL
            try:
                tables = list(client.list_tables(dataset.dataset_id))
                sql_tables = [t for t in tables if 'sql' in t.table_id.lower()]
                if sql_tables:
                    print(f"     └─ Tablas SQL: {[t.table_id for t in sql_tables]}")
            except:
                pass
        
        # Buscar la tabla correcta
        print(f"\n🔍 BUSCANDO TABLA SQL_OBJECTS_CODE:")
        
        for dataset in datasets:
            try:
                tables = list(client.list_tables(dataset.dataset_id))
                for table in tables:
                    if 'sql_objects' in table.table_id.lower():
                        full_id = f"{client.project}.{dataset.dataset_id}.{table.table_id}"
                        print(f"   ✅ Encontrada: {full_id}")
                        
                        # Verificar estructura
                        table_ref = client.get_table(table)
                        print(f"      └─ Registros: {table_ref.num_rows:,}")
                        print(f"      └─ Ubicación: {table_ref.location}")
                        
            except Exception as e:
                continue
        
    except Exception as e:
        print(f"❌ Error listando datasets: {e}")


def create_corrected_config():
    """Crea configuración corregida basada en hallazgos."""
    print(f"\n⚙️ CONFIGURACIÓN CORREGIDA")
    print("-" * 30)
    
    print("📝 Actualiza app/bigquery_vector/config.py:")
    print("```python")
    print("# Configuración corregida")
    print('PROJECT_ID: str = "dfor-prj-dev"')
    print('DATASET_ID: str = "deacero_sql_objects"  # Corregido')
    print('SOURCE_TABLE: str = "sql_objects_code"')
    print("```")
    
    print(f"\n🔧 O verifica manualmente:")
    print("```bash")
    print("bq ls dfor-prj-dev:")
    print("bq ls dfor-prj-dev:deacero_sql_objects")
    print("```")


def main():
    """Función principal de verificación."""
    print_header()
    
    # Verificaciones paso a paso
    creds_ok = verify_credentials()
    
    if creds_ok:
        data_ok = verify_dataset_access()
        
        if data_ok:
            sample_ok = verify_sample_data()
            
            if sample_ok:
                print(f"\n✅ TODAS LAS VERIFICACIONES EXITOSAS")
                print("=" * 45)
                print("🚀 Sistema listo para prueba de chunking!")
                print("📋 Ejecuta: make test-chunks")
            else:
                print(f"\n⚠️  DATOS NO ACCESIBLES")
                suggest_corrections()
        else:
            print(f"\n❌ ACCESO A DATASET FALLÓ")
            suggest_corrections()
    else:
        print(f"\n❌ CREDENCIALES INVÁLIDAS")
        print("🔧 Configura credenciales primero")
    
    print(f"\n" + "=" * 60)
    print("🔍 VERIFICACIÓN COMPLETADA")
    print("=" * 60)


if __name__ == "__main__":
    main()
