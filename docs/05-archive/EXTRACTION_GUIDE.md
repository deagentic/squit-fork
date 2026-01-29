# Guía Rápida de Extracción de Código Legacy

Esta guía te ayuda a extraer tu código SQL legacy y prepararlo para SQUIT.

## 🎯 Objetivo

Mover tu código SQL desde tus servidores de producción a BigQuery para democratizarlo con SQUIT.

## ⚡ Quick Start (3 opciones)

### Opción 1: Script Automatizado (Recomendado)

```bash
# 1. Crear configuración
python scripts/extract_sql_server_code.py --create-config

# 2. Editar extraction_config.yml con tus servidores

# 3. Extraer y cargar
python scripts/extract_sql_server_code.py --config extraction_config.yml
```

### Opción 2: SQL Manual + bq load

```bash
# 1. Ejecutar query SQL en tus servidores (ver README.md)
# 2. Exportar a CSV
# 3. Cargar con bq:
bq load --source_format=CSV \
  tu-proyecto:tu_dataset.sql_objects_code \
  export.csv
```

### Opción 3: Script Python Personalizado

Ver ejemplo completo en README.md sección "Preparar tu Código Legacy".

## 📋 Contrato de Datos

Tu tabla en BigQuery debe tener este schema:

```sql
CREATE TABLE sql_objects_code (
    server STRING NOT NULL,
    database STRING NOT NULL,
    schema STRING,
    object_name STRING NOT NULL,
    object_type STRING NOT NULL,
    sql_code STRING NOT NULL,
    content_hash STRING,
    last_modified TIMESTAMP,
    created_at TIMESTAMP,
    row_count INT64,
    size_bytes INT64,
    owner STRING
);
```

## ✅ Checklist

- [ ] Identificar servidores con código legacy
- [ ] Instalar dependencias: `pip install pyodbc google-cloud-bigquery pyyaml`
- [ ] Crear configuración: `python scripts/extract_sql_server_code.py --create-config`
- [ ] Editar `extraction_config.yml`
- [ ] Ejecutar extracción
- [ ] Validar: `python scripts/run_bigquery_pipeline.py --validate`
- [ ] Democratizar: `python scripts/run_bigquery_pipeline.py`

## 🆘 Problemas Comunes

### "pyodbc no instalado"
```bash
pip install pyodbc
```

### "No se puede conectar a SQL Server"
- Verificar nombre del servidor
- Verificar que tienes permisos
- Probar: `Trusted_Connection=yes` o usar usuario/password

### "Tabla no existe en BigQuery"
```bash
bq mk --dataset tu-proyecto:tu_dataset
```

## 📚 Más Info

Ver README.md sección "📦 Preparar tu Código Legacy para SQUIT" para:
- Scripts SQL para SQL Server, MySQL, PostgreSQL, Oracle
- Script Python completo
- Opciones avanzadas
- Tips de optimización
