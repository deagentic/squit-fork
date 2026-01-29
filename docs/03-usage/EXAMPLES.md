# SQUIT - Ejemplos de Uso

## Ejemplos Básicos

### 1. Inicialización y Conexión

```python
from squit_client import BigQueryClient
from squit_client.exceptions import SquitError

try:
    # Inicialización automática
    client = BigQueryClient()
    
    # Validar conexión
    if client.validate_connection():
        print("✅ Conexión exitosa")
    else:
        print("❌ Error en conexión")
        
except SquitError as e:
    print(f"Error: {e}")
```

### 2. Información de la Tabla

```python
# Obtener metadatos completos
info = client.get_table_info()

print(f"Tabla: {info['table_id']}")
print(f"Registros: {info['num_rows']:,}")
print(f"Tamaño: {info['num_bytes']:,} bytes")
print(f"Ubicación: {info['location']}")

# Mostrar esquema
print("\nColumnas:")
for name, type_name, description in info['schema']:
    print(f"  • {name}: {type_name}")
    if description:
        print(f"    {description}")
```

### 3. Estadísticas Rápidas

```python
# Estadísticas generales
stats = client.get_statistics()

print(f"Total objetos: {stats['total_objects']:,}")
print(f"Servidores únicos: {stats['unique_servers']}")
print(f"Bases de datos: {stats['unique_databases']}")
print(f"Tipos de objetos: {stats['unique_object_types']}")
print(f"Última modificación: {stats['newest_modification']}")
```

## Consultas y Búsquedas

### 4. Muestra de Datos

```python
# Obtener los 10 registros más recientes
sample = client.get_sample_data(10)
print(sample[['server', 'database', 'object_name', 'object_type']])

# Obtener muestra más grande
large_sample = client.get_sample_data(100)
```

### 5. Búsquedas Simples

```python
# Buscar por nombre de objeto
results = client.search_objects("usuario")

# Buscar en código SQL
results = client.search_objects(
    search_term="INSERT INTO",
    search_columns=["sql_code"]
)

# Buscar con límite específico
results = client.search_objects("login", limit=50)
```

### 6. Búsquedas Avanzadas

```python
# Filtrar por tipo de objeto
procedures = client.search_objects(
    search_term="usuario",
    object_types=["PROCEDURE", "FUNCTION"]
)

# Filtrar por servidor
server_objects = client.search_objects(
    search_term="login",
    servers=["SRVDBDES05\\BASCULA", "DCSDTII02\\SQL2008"]
)

# Búsqueda completa con todos los filtros
advanced_results = client.search_objects(
    search_term="authentication",
    search_columns=["object_name", "sql_code"],
    object_types=["PROCEDURE"],
    servers=["SRVDBDES05\\BASCULA"],
    limit=25
)
```

### 7. Análisis por Servidor

```python
# Top servidores con más objetos
top_servers = client.get_top_servers(10)

for _, row in top_servers.iterrows():
    print(f"{row['server']}: {row['object_count']:,} objetos")
    print(f"  • {row['database_count']} bases de datos")
    print(f"  • {row['object_type_count']} tipos de objetos")

# Objetos de una base de datos específica
db_objects = client.get_objects_by_database(
    server="SRVDBDES05\\BASCULA",
    database="TiSeguridad",
    limit=50
)
```

### 8. Análisis por Tipo de Objeto

```python
# Distribución de tipos de objetos
object_types = client.get_top_objects_by_type(10)

for _, row in object_types.iterrows():
    print(f"{row['object_type']}: {row['count']:,} ({row['percentage']}%)")
```

## Consultas SQL Personalizadas

### 9. Consultas Básicas

```python
# Consulta simple
query = """
SELECT server, COUNT(*) as count
FROM `dfor-prj-dev.deacero_sql_objects.sql_objects_code`
WHERE object_type = 'PROCEDURE'
GROUP BY server
ORDER BY count DESC
LIMIT 10
"""

results = client.execute_query(query)
print(results)
```

### 10. Consultas con Validación

```python
# Validar consulta sin ejecutar
complex_query = """
SELECT 
    server,
    database,
    object_type,
    COUNT(*) as object_count,
    AVG(LENGTH(sql_code)) as avg_code_length
FROM `dfor-prj-dev.deacero_sql_objects.sql_objects_code`
GROUP BY server, database, object_type
HAVING object_count > 100
ORDER BY object_count DESC
"""

# Dry run para validar
client.execute_query(complex_query, dry_run=True)
print("✅ Consulta válida")

# Ejecutar con límite
results = client.execute_query(complex_query, limit=50)
```

### 11. Análisis Temporal

```python
# Objetos modificados recientemente
recent_query = """
SELECT 
    server,
    database,
    object_name,
    object_type,
    last_modified
FROM `dfor-prj-dev.deacero_sql_objects.sql_objects_code`
WHERE last_modified >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
ORDER BY last_modified DESC
"""

recent_objects = client.execute_query(recent_query, limit=100)
```

### 12. Búsqueda de Patrones en Código

```python
# Buscar procedimientos que usan transacciones
transaction_query = """
SELECT 
    server,
    database,
    object_name,
    SUBSTR(sql_code, 1, 200) as code_preview
FROM `dfor-prj-dev.deacero_sql_objects.sql_objects_code`
WHERE object_type = 'PROCEDURE'
AND (
    sql_code LIKE '%BEGIN TRANSACTION%'
    OR sql_code LIKE '%COMMIT%'
    OR sql_code LIKE '%ROLLBACK%'
)
ORDER BY last_modified DESC
"""

transaction_procs = client.execute_query(transaction_query, limit=20)
```

## Exportación de Datos

### 13. Exportación a CSV

```python
# Exportar resultados a CSV
export_query = """
SELECT 
    server,
    database,
    object_name,
    object_type,
    last_modified
FROM `dfor-prj-dev.deacero_sql_objects.sql_objects_code`
WHERE object_type = 'VIEW'
ORDER BY server, database, object_name
"""

success = client.export_data(
    query=export_query,
    filename="views_inventory.csv",
    format_type="csv"
)

if success:
    print("✅ Datos exportados exitosamente")
```

### 14. Exportación a JSON

```python
# Exportar estadísticas a JSON
stats_query = """
SELECT 
    server,
    COUNT(*) as total_objects,
    COUNT(DISTINCT database) as databases,
    COUNT(DISTINCT object_type) as object_types
FROM `dfor-prj-dev.deacero_sql_objects.sql_objects_code`
GROUP BY server
ORDER BY total_objects DESC
"""

client.export_data(
    query=stats_query,
    filename="server_statistics.json",
    format_type="json"
)
```

### 15. Exportación a Parquet (Optimizada)

```python
# Para grandes volúmenes de datos
large_export_query = """
SELECT *
FROM `dfor-prj-dev.deacero_sql_objects.sql_objects_code`
WHERE server = 'SRVDBDES05\\BASCULA'
"""

# Parquet es más eficiente para grandes datasets
client.export_data(
    query=large_export_query,
    filename="bascula_objects.parquet",
    format_type="parquet"
)
```

## Casos de Uso Específicos

### 16. Auditoría de Código

```python
# Buscar procedimientos que modifican datos sensibles
audit_query = """
SELECT 
    server,
    database,
    object_name,
    last_modified
FROM `dfor-prj-dev.deacero_sql_objects.sql_objects_code`
WHERE object_type = 'PROCEDURE'
AND (
    sql_code LIKE '%DELETE%'
    OR sql_code LIKE '%UPDATE%'
    OR sql_code LIKE '%DROP%'
)
AND database IN ('TiSeguridad', 'Usuarios', 'Finanzas')
ORDER BY last_modified DESC
"""

audit_results = client.execute_query(audit_query)
```

### 17. Inventario de Bases de Datos

```python
# Obtener inventario completo por servidor
inventory_query = """
SELECT 
    server,
    database,
    object_type,
    COUNT(*) as count
FROM `dfor-prj-dev.deacero_sql_objects.sql_objects_code`
GROUP BY server, database, object_type
ORDER BY server, database, count DESC
"""

inventory = client.execute_query(inventory_query)

# Agrupar por servidor
for server in inventory['server'].unique():
    server_data = inventory[inventory['server'] == server]
    print(f"\n📊 {server}:")
    
    for _, row in server_data.iterrows():
        print(f"  {row['database']}.{row['object_type']}: {row['count']}")
```

### 18. Búsqueda de Dependencias

```python
# Buscar objetos que referencian una tabla específica
dependency_query = """
SELECT 
    server,
    database,
    object_name,
    object_type
FROM `dfor-prj-dev.deacero_sql_objects.sql_objects_code`
WHERE sql_code LIKE '%Usuarios%'
AND object_type IN ('PROCEDURE', 'VIEW', 'FUNCTION')
ORDER BY object_type, object_name
"""

dependencies = client.execute_query(dependency_query)
```

### 19. Análisis de Complejidad

```python
# Analizar complejidad de procedimientos por longitud de código
complexity_query = """
SELECT 
    server,
    database,
    object_name,
    LENGTH(sql_code) as code_length,
    CASE 
        WHEN LENGTH(sql_code) < 1000 THEN 'Simple'
        WHEN LENGTH(sql_code) < 5000 THEN 'Medio'
        WHEN LENGTH(sql_code) < 20000 THEN 'Complejo'
        ELSE 'Muy Complejo'
    END as complexity_level
FROM `dfor-prj-dev.deacero_sql_objects.sql_objects_code`
WHERE object_type = 'PROCEDURE'
ORDER BY code_length DESC
"""

complexity_analysis = client.execute_query(complexity_query, limit=100)
```

### 20. Monitoreo de Cambios

```python
# Objetos modificados en las últimas 24 horas
changes_query = """
SELECT 
    server,
    database,
    object_name,
    object_type,
    last_modified,
    commit_sha
FROM `dfor-prj-dev.deacero_sql_objects.sql_objects_code`
WHERE last_modified >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
ORDER BY last_modified DESC
"""

recent_changes = client.execute_query(changes_query)

if not recent_changes.empty:
    print(f"📈 {len(recent_changes)} objetos modificados en 24h:")
    for _, row in recent_changes.iterrows():
        print(f"  • {row['object_name']} ({row['object_type']}) - {row['server']}")
else:
    print("📊 No hay cambios recientes")
```

## Mejores Prácticas

### Optimización de Consultas

1. **Usar límites**: Siempre especificar LIMIT para consultas exploratorias
2. **Filtros específicos**: Usar WHERE clauses eficientes
3. **Selección de columnas**: SELECT solo las columnas necesarias
4. **Dry run**: Validar consultas complejas antes de ejecutar

### Manejo de Errores

1. **Captura específica**: Usar excepciones específicas en lugar de Exception genérica
2. **Logging apropiado**: Usar el sistema de logging para debugging
3. **Validación temprana**: Validar parámetros antes de ejecutar operaciones costosas

### Performance

1. **Reutilizar cliente**: No crear múltiples instancias innecesariamente
2. **Batch operations**: Agrupar operaciones relacionadas
3. **Usar Storage API**: Automáticamente habilitada para mejor performance
4. **Exportación eficiente**: Usar Parquet para grandes volúmenes

## Comandos CLI

### Uso de la Interfaz de Línea de Comandos

```bash
# Información básica
python -m squit_client.cli info

# Muestra de datos
python -m squit_client.cli sample --limit 20

# Búsqueda
python -m squit_client.cli search "usuario" --type PROCEDURE --limit 10

# Estadísticas
python -m squit_client.cli stats --limit 15

# Consulta personalizada
python -m squit_client.cli query "SELECT * FROM table LIMIT 5"

# Exportar resultados
python -m squit_client.cli query "SELECT * FROM table" --output results.csv --format csv

# Validar consulta
python -m squit_client.cli query "SELECT * FROM table" --dry-run

# Validar conexión
python -m squit_client.cli validate
```

## Scripts de Ejemplo

### Disponibles en `app/examples/`

1. **`basic_usage.py`**: Ejemplo básico con todas las operaciones principales
2. **`run_clean.py`**: Ejecución sin warnings para producción
3. **`example_usage.py`**: Ejemplo completo con logging detallado

### Ejecutar Ejemplos

```bash
# Desde Docker
make demo              # Ejemplo básico limpio
make demo-clean        # Sin warnings
make demo-verbose      # Con logging completo

# Localmente
python app/examples/basic_usage.py
python app/examples/run_clean.py
```
