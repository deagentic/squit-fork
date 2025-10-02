# SQUIT - API Reference

## BigQueryClient

### Clase Principal

```python
class BigQueryClient:
    """Cliente para acceder a la tabla sql_objects_code en BigQuery."""
```

### Constructor

```python
def __init__(self, credentials_path: Optional[str] = None) -> None
```

**Parámetros:**
- `credentials_path` (opcional): Ruta al archivo JSON de credenciales

**Excepciones:**
- `AuthenticationError`: Si no se pueden cargar credenciales
- `ConnectionError`: Si no se puede conectar a BigQuery

### Métodos Principales

#### `get_table_info() -> Dict[str, Any]`

Obtiene información básica de la tabla.

**Retorna:**
```python
{
    "table_id": str,
    "project": str,
    "dataset": str,
    "num_rows": int,
    "num_bytes": int,
    "created": datetime,
    "modified": datetime,
    "location": str,
    "schema": List[Tuple[str, str, str]]  # (name, type, description)
}
```

**Excepciones:**
- `ConnectionError`: Si no se puede acceder a la tabla

#### `execute_query(query: str, limit: Optional[int] = None, dry_run: bool = False) -> pd.DataFrame`

Ejecuta una consulta SQL personalizada.

**Parámetros:**
- `query`: Consulta SQL a ejecutar
- `limit`: Límite opcional de filas (máximo 50,000)
- `dry_run`: Si True, solo valida la consulta sin ejecutarla

**Retorna:**
- `pd.DataFrame`: Resultados de la consulta

**Excepciones:**
- `QueryError`: Si hay error en la consulta
- `ValidationError`: Si los parámetros son inválidos

#### `search_objects(...) -> pd.DataFrame`

Busca objetos SQL por término de búsqueda.

```python
def search_objects(
    self,
    search_term: str,
    search_columns: Optional[List[str]] = None,
    object_types: Optional[List[str]] = None,
    servers: Optional[List[str]] = None,
    limit: int = 100,
) -> pd.DataFrame
```

**Parámetros:**
- `search_term`: Término a buscar (requerido)
- `search_columns`: Columnas donde buscar (default: ["object_name", "sql_code"])
- `object_types`: Filtrar por tipos específicos
- `servers`: Filtrar por servidores específicos
- `limit`: Límite de resultados

**Excepciones:**
- `ValidationError`: Si el término de búsqueda está vacío

#### `get_statistics() -> Dict[str, Any]`

Obtiene estadísticas generales de la tabla.

**Retorna:**
```python
{
    "total_objects": int,
    "unique_servers": int,
    "unique_databases": int,
    "unique_object_types": int,
    "oldest_modification": datetime,
    "newest_modification": datetime
}
```

#### `get_sample_data(limit: int = 10) -> pd.DataFrame`

Obtiene una muestra de datos de la tabla.

**Parámetros:**
- `limit`: Número de filas a retornar

**Retorna:**
- `pd.DataFrame`: Muestra de datos ordenada por última modificación

#### `export_data(query: str, filename: str, format_type: str = "csv") -> bool`

Exporta resultados de consulta a archivo.

**Parámetros:**
- `query`: Consulta SQL a ejecutar
- `filename`: Nombre del archivo de salida
- `format_type`: Formato de exportación ("csv", "json", "parquet")

**Retorna:**
- `bool`: True si la exportación fue exitosa

**Excepciones:**
- `ConfigurationError`: Si el formato no está soportado
- `ExportError`: Si falla la exportación

### Métodos Auxiliares

#### `get_top_objects_by_type(limit: int = 10) -> pd.DataFrame`

Obtiene los tipos de objetos más comunes.

#### `get_top_servers(limit: int = 10) -> pd.DataFrame`

Obtiene los servidores con más objetos.

#### `get_object_details(object_name: str, server: str) -> pd.DataFrame`

Obtiene detalles completos de un objeto específico.

#### `get_objects_by_database(server: str, database: str, limit: int = 100) -> pd.DataFrame`

Obtiene objetos de una base de datos específica.

#### `validate_connection() -> bool`

Valida la conexión a BigQuery.

## Excepciones

### Jerarquía de Excepciones

```
SquitError (base)
├── ConnectionError
├── QueryError
├── AuthenticationError
├── ConfigurationError
├── ValidationError
└── ExportError
```

### Descripción de Excepciones

- **`SquitError`**: Excepción base para todos los errores de SQUIT
- **`ConnectionError`**: Problemas de conectividad con BigQuery
- **`QueryError`**: Errores en la ejecución de consultas SQL
- **`AuthenticationError`**: Problemas de autenticación con Google Cloud
- **`ConfigurationError`**: Errores de configuración del cliente
- **`ValidationError`**: Errores de validación de datos de entrada
- **`ExportError`**: Errores durante la exportación de datos

## Configuración

### Clase Config

```python
class Config:
    """Configuración centralizada del cliente SQUIT."""
```

### Constantes Principales

```python
PROJECT_ID = "dfor-prj-dev"
DATASET_ID = "deacero_sql_objects"
TABLE_ID = "sql_objects_code"

DEFAULT_QUERY_LIMIT = 1000
MAX_QUERY_LIMIT = 50000
MIN_QUERY_LIMIT = 1

SUPPORTED_EXPORT_FORMATS = ["csv", "json", "parquet"]
DEFAULT_SEARCH_COLUMNS = ["object_name", "sql_code"]
```

### Métodos de Configuración

#### `get_credentials_path(custom_path: Optional[str] = None) -> Optional[str]`

Obtiene la ruta de las credenciales de Google Cloud.

#### `validate_query_limit(limit: int) -> int`

Valida y ajusta el límite de consulta.

#### `validate_export_format(format_type: str) -> str`

Valida el formato de exportación.

## Utilidades

### Funciones Auxiliares

#### `setup_logging(level: str = "INFO") -> None`

Configura el sistema de logging.

#### `suppress_warnings() -> None`

Suprime warnings específicos de BigQuery y gRPC.

#### `format_number(number: int) -> str`

Formatea números con separadores de miles.

#### `truncate_text(text: str, max_length: int = 50) -> str`

Trunca texto a una longitud máxima.

#### `validate_file_path(file_path: str) -> bool`

Valida que una ruta de archivo sea válida.

#### `filter_important_errors(stderr_content: str) -> List[str]`

Filtra errores importantes del output de stderr.

## Ejemplos de Uso

### Inicialización Básica

```python
from squit_client import BigQueryClient

# Con credenciales automáticas
client = BigQueryClient()

# Con credenciales específicas
client = BigQueryClient("/path/to/credentials.json")
```

### Consultas Básicas

```python
# Información de la tabla
info = client.get_table_info()
print(f"Tabla tiene {info['num_rows']:,} registros")

# Muestra de datos
sample = client.get_sample_data(10)
print(sample)

# Estadísticas
stats = client.get_statistics()
print(f"Total objetos: {stats['total_objects']:,}")
```

### Búsquedas

```python
# Búsqueda simple
results = client.search_objects("usuario")

# Búsqueda filtrada
results = client.search_objects(
    search_term="login",
    object_types=["PROCEDURE", "FUNCTION"],
    servers=["SERVER1"],
    limit=50
)
```

### Consultas Personalizadas

```python
query = """
SELECT object_type, COUNT(*) as count
FROM `dfor-prj-dev.deacero_sql_objects.sql_objects_code`
WHERE server = 'SRVDBDES05\\BASCULA'
GROUP BY object_type
ORDER BY count DESC
"""

results = client.execute_query(query, limit=100)
```

### Exportación

```python
# Exportar a CSV
success = client.export_data(query, "resultados.csv", "csv")

# Exportar a JSON
success = client.export_data(query, "resultados.json", "json")

# Exportar a Parquet
success = client.export_data(query, "resultados.parquet", "parquet")
```

## Manejo de Errores

### Patrón Recomendado

```python
from squit_client import BigQueryClient
from squit_client.exceptions import SquitError, ConnectionError, QueryError

try:
    client = BigQueryClient()
    results = client.execute_query("SELECT * FROM table")
    
except ConnectionError as e:
    print(f"Error de conexión: {e}")
except QueryError as e:
    print(f"Error en consulta: {e}")
except SquitError as e:
    print(f"Error general: {e}")
except Exception as e:
    print(f"Error inesperado: {e}")
```

## Límites y Restricciones

### Límites de Consulta
- **Mínimo**: 1 fila
- **Máximo**: 50,000 filas
- **Por defecto**: 1,000 filas

### Formatos de Exportación
- **CSV**: Valores separados por comas
- **JSON**: JavaScript Object Notation
- **Parquet**: Formato columnar Apache Parquet

### Columnas de Búsqueda por Defecto
- `object_name`: Nombre del objeto SQL
- `sql_code`: Código SQL completo
