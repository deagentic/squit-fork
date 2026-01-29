# 🔧 Troubleshooting Guide - SQUIT

Guía completa para resolver problemas comunes del sistema SQUIT.

---

## 🚨 Problemas Comunes

### 1. Error: "Faltan variables de ambiente"

**Síntoma**:
```
❌ ERROR: Faltan variables de ambiente: GEMINI_API_KEY, GOOGLE_CLOUD_PROJECT
```

**Causa**: Archivo `.env` no configurado o variables no cargadas.

**Solución**:
```bash
# 1. Verificar que .env existe
ls -la .env

# 2. Verificar contenido
cat .env

# 3. Si no existe, copiar template
cp .env.template .env

# 4. Editar y agregar tus valores
nano .env

# Variables requeridas:
# GOOGLE_CLOUD_PROJECT=tu-proyecto-id
# GOOGLE_APPLICATION_CREDENTIALS=.config/credentials.json
# GEMINI_API_KEY=tu-api-key
# GEMINI_CHAT_MODEL=gemini-2.5-flash
```

---

### 2. Error: "BigQuery connection failed"

**Síntoma**:
```
❌ Error: 403 Permission denied on project
```

**Causa**: Credenciales incorrectas o permisos insuficientes.

**Solución**:
```bash
# 1. Verificar credenciales
ls -la .config/credentials.json

# 2. Verificar que apunta al archivo correcto
echo $GOOGLE_APPLICATION_CREDENTIALS

# 3. Verificar permisos del service account
gcloud projects get-iam-policy $GOOGLE_CLOUD_PROJECT \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount"

# Permisos requeridos:
# - BigQuery Data Viewer
# - BigQuery Job User
# - BigQuery Data Editor

# 4. Probar conexión
python3 scripts/prod/verify_bigquery_access.py
```

---

### 3. Error: "Gemini API no responde"

**Síntoma**:
```
❌ Error: 401 Unauthorized
```

**Causa**: API key inválida o expirada.

**Solución**:
```bash
# 1. Verificar API key
echo $GEMINI_API_KEY

# 2. Probar API key directamente
curl -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"test"}]}]}' \
  "https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key=$GEMINI_API_KEY"

# 3. Si falla, generar nueva key
# → https://makersuite.google.com/app/apikey

# 4. Actualizar en .env
nano .env
# GEMINI_API_KEY=tu-nueva-key
```

---

### 4. Error: "Rate limit exceeded"

**Síntoma**:
```
❌ Error: 429 Too Many Requests
```

**Causa**: Excediste la cuota de la API de Gemini.

**Solución**:
```bash
# 1. Verificar configuración de rate limiting
python3 -c "
from app.config.environments import get_env_config
config = get_env_config()
print(f'RATE_LIMIT_CALLS: {config[\"RATE_LIMIT_CALLS\"]}')
"

# 2. Reducir tasa en .env (si necesario)
# RATE_LIMIT_CALLS=30  # Más conservador

# 3. Esperar algunos minutos antes de reintentar

# 4. Verificar cuota en Google Cloud Console
# → APIs & Services → Enabled APIs → Gemini API → Quotas
```

---

### 5. Error: "Circuit breaker is OPEN"

**Síntoma**:
```
❌ Circuit breaker is OPEN. Retry in 45s
```

**Causa**: El servicio falló repetidamente, circuit breaker lo protege.

**Solución**:
```bash
# Esto es NORMAL y PROTEGE tu sistema

# 1. Esperar el timeout (45-60s)
# 2. El circuit breaker probará recovery automáticamente

# 3. Si persiste, verificar servicio downstream:
# - BigQuery: make health
# - Gemini API: curl test

# 4. Ver logs para diagnosticar causa raíz
grep "ERROR" *.log | tail -20
```

---

### 6. Error: "Connection pool timeout"

**Síntoma**:
```
❌ Timeout waiting for BigQuery connection
```

**Causa**: Pool de conexiones saturado o conexión corrupta.

**Solución**:
```python
# Resetear connection pool
python3 -c "
from app.utils.connection_pool import BigQueryConnectionPool
pool = BigQueryConnectionPool()
pool.reset()
print('✅ Connection pool reseteado')
"

# O reiniciar aplicación
make squit-rebuild
```

---

### 7. Docker: "Container exits immediately"

**Síntoma**:
```
ERROR: Container squit-cli exited with code 1
```

**Causa**: Error en configuración o credenciales faltantes.

**Solución**:
```bash
# 1. Ver logs completos
docker logs squit-cli

# 2. Verificar montaje de volúmenes
docker-compose --profile cli config

# 3. Verificar que archivos existen
ls -la .config/credentials.json
ls -la .env
ls -la data/catalogo.csv

# 4. Rebuild completo
make squit-clean
make squit-rebuild
```

---

### 8. Performance: "Búsquedas muy lentas"

**Síntoma**:
```
⏱️ Búsqueda tardó >10 segundos
```

**Causa**: Índice vectorial no creado o dataset muy grande.

**Solución**:
```bash
# 1. Verificar índice vectorial
python3 -c "
from app.bigquery_vector.config import BigQueryVectorConfig
config = BigQueryVectorConfig()
print(f'Índice: {config.VECTOR_INDEX_NAME}')
"

# 2. Crear índice si no existe
make create-index

# 3. Verificar tamaño de dataset
python3 scripts/tools/analyze_bigquery_schema.py

# 4. Usar límites más bajos en búsquedas
# En código: semantic_search(query, limit=5)
```

---

### 9. Memory: "Out of memory"

**Síntoma**:
```
MemoryError: Unable to allocate array
```

**Causa**: Batch size muy grande o dataset en memoria.

**Solución**:
```bash
# 1. Reducir batch size
# En config: EMBEDDING_BATCH_SIZE = 100  # En vez de 1000

# 2. Procesar en chunks más pequeños
# En código: use streaming=True

# 3. Aumentar memoria de Docker
# docker-compose.yml:
#   mem_limit: 4g
```

---

### 10. Tests: "Tests failing after changes"

**Síntoma**:
```
FAILED test_something.py
```

**Causa**: Cambios en código rompieron tests.

**Solución**:
```bash
# 1. Ejecutar tests con verbose
pytest app/tests/ -v -s

# 2. Ejecutar test específico con traceback
pytest app/tests/test_algo.py::test_function -vv

# 3. Ejecutar con debugger
pytest app/tests/test_algo.py::test_function --pdb

# 4. Ver coverage para identificar áreas no probadas
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

---

## 🔍 Comandos de Diagnóstico

### Health Check Completo
```bash
make health
```

### Verificar BigQuery
```bash
python3 scripts/prod/verify_bigquery_access.py
```

### Verificar Configuración
```bash
python3 -c "
import sys, os
from pathlib import Path
sys.path.insert(0, 'app')

print('📊 DIAGNÓSTICO DEL SISTEMA\n')

# Archivos
files = {
    '.env': Path('.env'),
    'credentials.json': Path('.config/credentials.json'),
    'catalogo.csv': Path('data/catalogo.csv')
}
for name, path in files.items():
    status = '✅' if path.exists() else '❌'
    print(f'{status} {name}: {path}')

# Variables
print('\n🔐 Variables:')
env_vars = ['GOOGLE_CLOUD_PROJECT', 'GEMINI_API_KEY']
for var in env_vars:
    val = os.getenv(var, '')
    status = '✅' if val else '❌'
    display = val[:20] + '...' if len(val) > 20 else val
    print(f'{status} {var}: {display}')

# Configuración
print('\n⚙️ Sistema:')
from bigquery_vector.config import BigQueryVectorConfig
config = BigQueryVectorConfig()
print(f'✅ BigQuery: {config.PROJECT_ID}')
print(f'✅ Dataset: {config.DATASET_ID}')
"
```

### Ver Logs
```bash
# Logs recientes
tail -f *.log

# Buscar errores
grep "ERROR" *.log | tail -20

# Logs de Docker
docker logs squit-cli --tail=50
```

---

## 📚 Recursos Adicionales

- **[Guía de Deployment](DEPLOYMENT.md)** - Desplegar a producción
- **[Backup & Restore](BACKUP_RESTORE.md)** - Procedimientos de backup
- **[Testing Guide](../04-development/TESTING.md)** - Escribir tests
- **[GitHub Issues](https://github.com/grupodeacero/squit/issues)** - Reportar bugs

---

## 🆘 ¿Aún Necesitas Ayuda?

1. **Revisa logs**: `grep "ERROR" *.log`
2. **Health check**: `make health`
3. **GitHub Issues**: Reporta el problema
4. **Email**: ktouma@deacero.com

---

**Tip**: Usa `make help` para ver todos los comandos disponibles.

