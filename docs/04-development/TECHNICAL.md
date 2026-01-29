# SQUIT - Documentación Técnica

## Arquitectura del Sistema

### Componentes Principales

#### 1. Cliente BigQuery (`squit_client/client.py`)
- **Propósito**: Interfaz principal para interactuar con BigQuery
- **Características**:
  - Autenticación automática con cuentas de servicio
  - Manejo robusto de errores con excepciones personalizadas
  - Logging detallado para debugging
  - Validación de consultas con dry-run
  - Límites configurables para evitar timeouts

#### 2. Configuración (`squit_client/config.py`)
- **Propósito**: Centralizar toda la configuración del sistema
- **Características**:
  - Detección automática de credenciales
  - Configuración de límites y formatos
  - Rutas y parámetros del proyecto

#### 3. Excepciones (`squit_client/exceptions.py`)
- **Propósito**: Manejo específico de errores
- **Tipos**:
  - `SquitError`: Base para todas las excepciones
  - `ConnectionError`: Problemas de conectividad
  - `QueryError`: Errores en consultas SQL
  - `AuthenticationError`: Problemas de autenticación
  - `ConfigurationError`: Errores de configuración

## Esquema de la Base de Datos

### Tabla: `dfor-prj-dev.deacero_sql_objects.sql_objects_code`

| Columna | Tipo | Descripción | Índice |
|---------|------|-------------|--------|
| `server` | STRING | Servidor SQL de origen | ✅ |
| `database` | STRING | Base de datos | ✅ |
| `schema` | STRING | Esquema de la base de datos | - |
| `object_name` | STRING | Nombre del objeto SQL | ✅ |
| `file_name` | STRING | Archivo fuente original | - |
| `object_type` | STRING | Tipo (PROCEDURE, TABLE, VIEW, etc.) | ✅ |
| `path` | STRING | Ruta completa del archivo | - |
| `sql_code` | STRING | Código SQL completo | - |
| `content_hash` | STRING | Hash MD5 del contenido | ✅ |
| `last_modified` | TIMESTAMP | Última modificación | ✅ |
| `commit_sha` | STRING | SHA del commit Git | - |
| `executed_at` | TIMESTAMP | Timestamp de ejecución | - |
| `is_deleted` | BOOLEAN | Marcado como eliminado | - |
| `deleted_at` | TIMESTAMP | Fecha de eliminación | - |

### Estadísticas de la Tabla
- **Total de registros**: 3,416,808
- **Tamaño**: 12.55 GB
- **Servidores únicos**: 275
- **Bases de datos únicas**: 582
- **Tipos de objetos**: 7

### Distribución por Tipo de Objeto
1. **PROCEDURE**: 2,111,700 (61.8%)
2. **TABLE**: 609,684 (17.84%)
3. **VIEW**: 423,882 (12.41%)
4. **INDEX**: 143,848 (4.21%)
5. **FUNCTION**: 75,423 (2.21%)
6. **TRIGGER**: 50,507 (1.48%)
7. **UNKNOWN**: 1,764 (0.05%)

## Arquitectura Docker

### Imagen de Producción
```dockerfile
# Multi-stage build para optimización
FROM python:3.12-slim-bookworm as builder
# ... instalar dependencias ...

FROM gcr.io/distroless/python3-debian12:latest
# ... imagen final minimalista ...
```

**Características**:
- **Base**: Distroless (sin shell, más segura)
- **Tamaño**: ~150MB (optimizada)
- **Seguridad**: Sin vulnerabilidades conocidas
- **Performance**: Inicio rápido (<5 segundos)

### Imagen de Desarrollo
```dockerfile
FROM quay.io/jupyter/scipy-notebook:python-3.12
# ... con Jupyter Lab y herramientas de desarrollo ...
```

**Características**:
- **Jupyter Lab**: Entorno interactivo completo
- **Extensiones**: Git, LSP, formateo automático
- **Herramientas**: Black, isort, mypy, flake8

## API del Cliente

### Clase Principal: `BigQueryClient`

#### Inicialización
```python
client = BigQueryClient(credentials_path=None)
```
- **credentials_path**: Opcional, auto-detecta si no se especifica

#### Métodos Principales

##### `get_table_info() -> Dict[str, Any]`
Obtiene metadatos completos de la tabla.

**Retorna**:
```python
{
    "table_id": "sql_objects_code",
    "project": "dfor-prj-dev", 
    "dataset": "deacero_sql_objects",
    "num_rows": 3416808,
    "num_bytes": 12555015981,
    "created": datetime,
    "modified": datetime,
    "location": "us-central1",
    "schema": [("column", "type", "description"), ...]
}
```

##### `execute_query(query: str, limit: int = None, dry_run: bool = False) -> pd.DataFrame`
Ejecuta consulta SQL personalizada.

**Parámetros**:
- `query`: Consulta SQL válida
- `limit`: Límite de filas (máximo 50,000)
- `dry_run`: Solo validar sin ejecutar

**Ejemplo**:
```python
df = client.execute_query("""
    SELECT server, COUNT(*) as count
    FROM `dfor-prj-dev.deacero_sql_objects.sql_objects_code`
    WHERE object_type = 'PROCEDURE'
    GROUP BY server
    ORDER BY count DESC
    LIMIT 10
""")
```

##### `search_objects(search_term: str, ...) -> pd.DataFrame`
Búsqueda avanzada de objetos SQL.

**Parámetros**:
- `search_term`: Término a buscar
- `search_columns`: Columnas donde buscar (default: object_name, sql_code)
- `object_types`: Filtrar por tipos específicos
- `servers`: Filtrar por servidores específicos
- `limit`: Límite de resultados

**Ejemplo**:
```python
results = client.search_objects(
    search_term="usuario",
    search_columns=["object_name", "sql_code"],
    object_types=["PROCEDURE", "FUNCTION"],
    servers=["SRVDBDES05\\BASCULA"],
    limit=100
)
```

##### `export_data(query: str, filename: str, format_type: str = "csv") -> bool`
Exporta resultados a archivo.

**Formatos soportados**:
- `csv`: Valores separados por comas
- `json`: JavaScript Object Notation
- `parquet`: Formato columnar Apache Parquet

## Configuración Avanzada

### Variables de Entorno
```bash
# Credenciales de Google Cloud
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# Configuración de Python
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1

# Logging
LOG_LEVEL=INFO
```

### Límites y Configuración
```python
# En config.py
DEFAULT_QUERY_LIMIT = 1000
MAX_QUERY_LIMIT = 50000
SUPPORTED_EXPORT_FORMATS = ["csv", "json", "parquet"]
```

## Optimización de Consultas

### Mejores Prácticas
1. **Usar LIMIT**: Siempre limitar resultados grandes
2. **Filtros específicos**: WHERE clauses eficientes
3. **Selección de columnas**: SELECT solo columnas necesarias
4. **Índices**: Aprovechar columnas indexadas (server, object_type, etc.)

### Consultas Optimizadas
```sql
-- ✅ BUENA: Específica y con límite
SELECT server, object_name, object_type
FROM `dfor-prj-dev.deacero_sql_objects.sql_objects_code`
WHERE object_type = 'PROCEDURE'
  AND server = 'SRVDBDES05\BASCULA'
ORDER BY last_modified DESC
LIMIT 100;

-- ❌ MALA: Sin filtros ni límites
SELECT *
FROM `dfor-prj-dev.deacero_sql_objects.sql_objects_code`;
```

## Monitoreo y Logging

### Niveles de Log
- **DEBUG**: Información detallada de debugging
- **INFO**: Operaciones normales
- **WARNING**: Situaciones que requieren atención
- **ERROR**: Errores que no detienen la ejecución
- **CRITICAL**: Errores críticos que detienen el sistema

### Métricas Importantes
- Tiempo de respuesta de consultas
- Bytes procesados por BigQuery
- Número de filas retornadas
- Errores de conexión y autenticación

## Seguridad

### Autenticación
- **Cuenta de servicio**: Método recomendado para producción
- **Credenciales de usuario**: Solo para desarrollo
- **Variables de entorno**: Para configuración segura

### Mejores Prácticas
1. **Principio de menor privilegio**: Solo permisos necesarios
2. **Rotación de credenciales**: Cambiar periódicamente
3. **Monitoreo de acceso**: Logs de auditoría
4. **Cifrado**: Credenciales cifradas en reposo

## Troubleshooting

### Errores Comunes

#### Error de Autenticación
```
AuthenticationError: Error al inicializar cliente BigQuery
```
**Solución**: Verificar credenciales y permisos

#### Error de Conexión
```
ConnectionError: Tabla no encontrada
```
**Solución**: Verificar ID de tabla y permisos de acceso

#### Error de Consulta
```
QueryError: Error en la consulta SQL: Invalid table name
```
**Solución**: Verificar sintaxis SQL y nombres de tabla

### Comandos de Diagnóstico
```bash
# Verificar conectividad
make health

# Ver logs detallados
make logs

# Ejecutar tests
make test

# Verificar configuración
docker-compose config
```

## Performance

### Benchmarks
- **Consulta simple**: ~2-3 segundos
- **Consulta compleja**: ~5-10 segundos
- **Exportación CSV (1K filas)**: ~1 segundo
- **Exportación Parquet (10K filas)**: ~3 segundos

### Optimizaciones Implementadas
- Reutilización de conexiones BigQuery
- Cache de metadatos de tabla
- Validación de consultas antes de ejecución
- Límites automáticos para prevenir timeouts
