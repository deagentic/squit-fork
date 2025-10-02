#!/usr/bin/env python3
"""
Script para extraer código SQL desde SQL Server y cargarlo a BigQuery.

Este script automatiza todo el proceso de extracción desde tus servidores SQL Server
y carga a BigQuery, preparando todo para SQUIT.

Uso:
    python scripts/extract_sql_server_code.py --config extraction_config.yml
    
Ejemplo de config (extraction_config.yml):
    sql_servers:
      - host: "SERVER1\\INSTANCE"
        databases:
          - "DB1"
          - "DB2"
      - host: "SERVER2"
        databases:
          - "DB3"
    
    bigquery:
      project: "tu-proyecto"
      dataset: "tu_dataset"
      table: "sql_objects_code"
    
    options:
      batch_size: 1000
      include_system_objects: false
"""

import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import hashlib
import yaml

# Agregar app al path
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config(config_file: str) -> Dict[str, Any]:
    """Carga configuración desde archivo YAML."""
    with open(config_file, 'r') as f:
        return yaml.safe_load(f)


def extract_from_sql_server(server: str, database: str, options: Dict = None) -> List[Dict]:
    """
    Extrae objetos SQL de un servidor.
    
    Args:
        server: Nombre del servidor (ej: SERVER\\INSTANCE)
        database: Nombre de la base de datos
        options: Opciones de extracción
        
    Returns:
        Lista de objetos extraídos
    """
    try:
        import pyodbc
    except ImportError:
        logger.error("pyodbc no instalado. Ejecuta: pip install pyodbc")
        return []
    
    options = options or {}
    include_system = options.get('include_system_objects', False)
    
    logger.info(f"Conectando a {server}.{database}...")
    
    try:
        conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes"
        conn = pyodbc.connect(conn_str, timeout=30)
        cursor = conn.cursor()
        
        # Query para extraer objetos
        query = """
        SELECT 
            @@SERVERNAME as server,
            DB_NAME() as database,
            SCHEMA_NAME(o.schema_id) as schema_name,
            o.name as object_name,
            o.type_desc as object_type,
            OBJECT_DEFINITION(o.object_id) as sql_code,
            o.modify_date as last_modified,
            USER_NAME(o.principal_id) as owner
        FROM sys.objects o
        WHERE o.type IN (
            'P',   -- Stored Procedures
            'FN',  -- Scalar Functions
            'IF',  -- Inline Table-Valued Functions
            'TF',  -- Table-Valued Functions
            'V',   -- Views
            'TR'   -- Triggers
        )
        AND OBJECT_DEFINITION(o.object_id) IS NOT NULL
        """
        
        if not include_system:
            query += " AND o.is_ms_shipped = 0"
        
        query += " ORDER BY o.type_desc, o.name"
        
        logger.info(f"  Extrayendo objetos...")
        cursor.execute(query)
        
        objects = []
        for row in cursor:
            if row.sql_code:  # Solo si tiene código
                sql_code = row.sql_code.strip()
                objects.append({
                    "server": row.server,
                    "database": row.database,
                    "schema": row.schema_name or "dbo",
                    "object_name": row.object_name,
                    "object_type": row.object_type,
                    "sql_code": sql_code,
                    "content_hash": hashlib.md5(sql_code.encode()).hexdigest(),
                    "last_modified": row.last_modified.isoformat() if row.last_modified else None,
                    "created_at": datetime.now().isoformat(),
                    "row_count": sql_code.count('\n') + 1,
                    "size_bytes": len(sql_code.encode('utf-8')),
                    "owner": row.owner
                })
        
        conn.close()
        logger.info(f"  ✅ {len(objects)} objetos extraídos")
        return objects
        
    except Exception as e:
        logger.error(f"  ❌ Error: {e}")
        return []


def load_to_bigquery(objects: List[Dict], project: str, dataset: str, table: str, batch_size: int = 1000):
    """
    Carga objetos a BigQuery.
    
    Args:
        objects: Lista de objetos a cargar
        project: Proyecto de BigQuery
        dataset: Dataset de BigQuery
        table: Tabla de BigQuery
        batch_size: Tamaño de batch para carga
    """
    try:
        from google.cloud import bigquery
    except ImportError:
        logger.error("google-cloud-bigquery no instalado. Ejecuta: pip install google-cloud-bigquery")
        return
    
    if not objects:
        logger.warning("No hay objetos para cargar")
        return
    
    logger.info(f"Cargando {len(objects)} objetos a BigQuery...")
    
    client = bigquery.Client(project=project)
    table_id = f"{project}.{dataset}.{table}"
    
    # Schema de la tabla
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND",
        schema=[
            bigquery.SchemaField("server", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("database", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("schema", "STRING"),
            bigquery.SchemaField("object_name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("object_type", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("sql_code", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("content_hash", "STRING"),
            bigquery.SchemaField("last_modified", "TIMESTAMP"),
            bigquery.SchemaField("created_at", "TIMESTAMP"),
            bigquery.SchemaField("row_count", "INTEGER"),
            bigquery.SchemaField("size_bytes", "INTEGER"),
            bigquery.SchemaField("owner", "STRING"),
        ],
    )
    
    # Cargar en batches
    for i in range(0, len(objects), batch_size):
        batch = objects[i:i + batch_size]
        logger.info(f"  Cargando batch {i // batch_size + 1} ({len(batch)} objetos)...")
        
        try:
            job = client.load_table_from_json(batch, table_id, job_config=job_config)
            job.result()  # Esperar a que complete
            logger.info(f"  ✅ Batch cargado")
        except Exception as e:
            logger.error(f"  ❌ Error en batch: {e}")
    
    logger.info(f"✅ Carga completada: {len(objects)} objetos en {table_id}")


def print_banner():
    """Imprime banner del script."""
    print("\n" + "=" * 80)
    print("🎯 SQUIT - Extracción de Código SQL Legacy")
    print("=" * 80)
    print(f"📅 Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 Objetivo: Extraer código de SQL Server → BigQuery")
    print("=" * 80)
    print()


def create_example_config(output_file: str = "extraction_config.yml"):
    """Crea archivo de configuración de ejemplo."""
    example_config = {
        "sql_servers": [
            {
                "host": "SERVER1\\INSTANCE",
                "databases": ["DB1", "DB2", "DB3"]
            },
            {
                "host": "SERVER2",
                "databases": ["DB4"]
            }
        ],
        "bigquery": {
            "project": "tu-proyecto-gcp",
            "dataset": "tu_dataset",
            "table": "sql_objects_code"
        },
        "options": {
            "batch_size": 1000,
            "include_system_objects": False
        }
    }
    
    with open(output_file, 'w') as f:
        yaml.dump(example_config, f, default_flow_style=False)
    
    logger.info(f"✅ Archivo de configuración de ejemplo creado: {output_file}")
    print(f"\nEdita {output_file} con tus servidores y ejecuta:")
    print(f"  python scripts/extract_sql_server_code.py --config {output_file}")


def validate_dependencies():
    """Valida que las dependencias estén instaladas."""
    missing = []
    
    try:
        import pyodbc
    except ImportError:
        missing.append("pyodbc")
    
    try:
        from google.cloud import bigquery
    except ImportError:
        missing.append("google-cloud-bigquery")
    
    try:
        import yaml
    except ImportError:
        missing.append("pyyaml")
    
    if missing:
        logger.error("❌ Dependencias faltantes:")
        for dep in missing:
            print(f"  - {dep}")
        print("\nInstala con:")
        print(f"  pip install {' '.join(missing)}")
        return False
    
    return True


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Extrae código SQL de SQL Server y carga a BigQuery",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  # Crear configuración de ejemplo
  %(prog)s --create-config
  
  # Ejecutar extracción
  %(prog)s --config extraction_config.yml
  
  # Modo dry-run (sin cargar a BigQuery)
  %(prog)s --config extraction_config.yml --dry-run
        """
    )
    
    parser.add_argument('--config', help='Archivo de configuración YAML')
    parser.add_argument('--create-config', action='store_true',
                       help='Crear archivo de configuración de ejemplo')
    parser.add_argument('--dry-run', action='store_true',
                       help='Extraer sin cargar a BigQuery (solo reporte)')
    parser.add_argument('--output', default='extraction_config.yml',
                       help='Nombre del archivo de config a crear')
    
    args = parser.parse_args()
    
    print_banner()
    
    # Crear config de ejemplo
    if args.create_config:
        create_example_config(args.output)
        return 0
    
    # Validar dependencias
    if not validate_dependencies():
        return 1
    
    # Cargar configuración
    if not args.config:
        logger.error("❌ Debes proporcionar --config o usar --create-config")
        return 1
    
    try:
        config = load_config(args.config)
    except Exception as e:
        logger.error(f"❌ Error cargando configuración: {e}")
        return 1
    
    # Extraer de todos los servidores
    all_objects = []
    
    for server_config in config.get('sql_servers', []):
        host = server_config['host']
        databases = server_config.get('databases', [])
        
        for database in databases:
            logger.info(f"\n📦 {host}.{database}")
            objects = extract_from_sql_server(
                host,
                database,
                config.get('options', {})
            )
            all_objects.extend(objects)
    
    # Reporte
    print("\n" + "=" * 80)
    print("📊 RESUMEN DE EXTRACCIÓN")
    print("=" * 80)
    print(f"Total objetos extraídos: {len(all_objects)}")
    
    if all_objects:
        # Estadísticas por tipo
        from collections import Counter
        types = Counter(obj['object_type'] for obj in all_objects)
        print("\nPor tipo:")
        for obj_type, count in types.most_common():
            print(f"  {obj_type}: {count}")
        
        # Estadísticas por servidor
        servers = Counter(obj['server'] for obj in all_objects)
        print(f"\nPor servidor:")
        for server, count in servers.items():
            print(f"  {server}: {count}")
    
    # Cargar a BigQuery (si no es dry-run)
    if not args.dry_run and all_objects:
        bq_config = config.get('bigquery', {})
        options = config.get('options', {})
        
        load_to_bigquery(
            all_objects,
            bq_config.get('project'),
            bq_config.get('dataset'),
            bq_config.get('table'),
            options.get('batch_size', 1000)
        )
    elif args.dry_run:
        logger.info("\n🔍 Modo dry-run: no se cargó a BigQuery")
    
    print("\n" + "=" * 80)
    print("✅ ¡Proceso completado!")
    print("=" * 80)
    
    if not args.dry_run and all_objects:
        print("\n🎯 Siguiente paso:")
        print("  python scripts/run_bigquery_pipeline.py --validate")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
