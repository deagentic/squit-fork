# Revisión de Mejoras Enterprise: `BigQueryClient`

## Resumen Ejecutivo
El archivo `squit/app/squit_client/client.py` ha sido refactorizado para elevar el cliente de BigQuery a estándares **Enterprise / Producción**. Se abordaron vulnerabilidades críticas de seguridad (Inyección SQL), se solucionaron riesgos de concurrencia en entornos web (*Thread-Safety*) y se integraron métricas clave de observabilidad (latencia y consumo de bytes).

**Estado de los Tests:** `4/4 Passed` (Cobertura completa de los nuevos requerimientos).

---

## Cambios Detallados por Categoría

### 1. 🛡️ Seguridad: Prevención de SQL Injection (Crítico)
**Problema:** Los métodos de búsqueda (`search_objects`, `get_object_details`, `get_objects_by_database`) concatenaban directamente el *input* del usuario dentro de las consultas SQL usando interpolación de cadenas (`f"{object_name}"`). Esto abría la puerta a ataques de inyección SQL (ej. `'; DROP TABLE sql_objects; --`).

**Solución Implementada:**
*   Se eliminó la interpolación de *strings* para los valores de entrada de los usuarios.
*   Se implementó el uso de la API nativa de parametrización de Google Cloud BigQuery (`QueryJobConfig(query_parameters=[...])`).
*   Se utilizaron parámetros escalares (`ScalarQueryParameter`) para textos y parámetros de array (`ArrayQueryParameter`) para el filtro de múltiples elementos con `UNNEST()` (como los tipos de objetos o listas de servidores).

### 2. 🚦 Concurrencia: Thread-Safety
**Problema:** La inicialización del cliente BigQuery en `__init__` o a través de la propiedad `@property client` podía sufrir de "condiciones de carrera" (*race conditions*) si múltiples hilos (ej. peticiones de una aplicación web Uvicorn/FastAPI) intentaban inicializar la conexión al mismo tiempo.

**Solución Implementada:**
*   Se introdujo un cerrojo de concurrencia explícito: `self._lock = threading.Lock()`.
*   Se implementó el patrón *Thread-Safe Lazy Initialization* usando el bloque `with self._lock:` alrededor de `_initialize_client` y del acceso a la propiedad `@property client`. Esto garantiza que la instanciación de red/BigQuery sea única en entornos multihilo.

### 3. 📊 Observabilidad: Métricas de Rendimiento y Costos
**Problema:** El registro original (`logger`) solo indicaba si la consulta se ejecutó y cuántas filas devolvió, pero carecía de información crítica para el control de la facturación en la nube (bytes escaneados) y del rendimiento real de respuesta de la API (latencia).

**Solución Implementada:**
*   **Latencia:** Se implementó un temporizador con `time.time()` alrededor de la ejecución del `query_job`. Se agregó un log explícito: `Latencia de la consulta: X.XXs`.
*   **Costos (Bytes Procesados):** Se extrajo el atributo nativo `query_job.total_bytes_processed` tras la ejecución exitosa (o en *dry-run*) y se integró en la salida de los logs: `Consulta ejecutada exitosamente. Filas: Y, Bytes procesados: Z`.

---

## Resultados de la Suite de Pruebas (`test_client_enterprise.py`)
Se ejecutaron los tests específicos creados para validar estos 3 requerimientos. Los resultados confirman la correcta mitigación de los riesgos:

```text
============================= test session starts ==============================
platform darwin -- Python 3.13.7, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/manuelcastiblanco/Documents/Deacero/squit
configfile: pyproject.toml
plugins: cov-7.1.0, bdd-8.1.0, anyio-4.13.0
collected 4 items

app/tests/test_client_enterprise.py ....                                 [100%]

============================== 4 passed in 0.02s ===============================
```

### Casos de Uso Validados:
1.  **`test_search_objects_sql_injection`:** Verificó que el *input* malicioso se envía como parámetro (`job_config.query_parameters > 0`) y no en la consulta plana. *(Pasó).*
2.  **`test_get_object_details_sql_injection`:** Validó la parametrización de atributos `object_name` y `server`. *(Pasó).*
3.  **`test_client_initialization_thread_safety`:** Simuló 10 hilos intentando obtener el cliente BigQuery concurrentemente sin generar un error de inestabilidad o dobles instancias. *(Pasó).*
4.  **`test_execute_query_logs_latency_and_rows`:** Comprobó que el *LogCaptureFixture* contenía las palabras clave "Latencia", "Filas" y "Bytes procesados". *(Pasó).*
