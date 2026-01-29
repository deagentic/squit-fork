# 🚀 Deployment Guide - SQUIT

Guía completa para desplegar SQUIT a producción.

---

## 📋 Pre-requisitos

### Google Cloud Platform
- ✅ Proyecto GCP activo
- ✅ Service Account con permisos:
  - BigQuery Data Viewer
  - BigQuery Job User
  - BigQuery Data Editor
  - Vertex AI User
- ✅ Dataset BigQuery creado
- ✅ Vertex AI connection configurado

### APIs Habilitadas
- ✅ BigQuery API
- ✅ Vertex AI API
- ✅ Secret Manager API (recomendado)

### Credenciales
- ✅ Service Account JSON
- ✅ Gemini API Key

---

## 🏗️ Arquitectura de Deployment

```
Production Environment:
├── BigQuery (data warehouse)
│   ├── sql_objects_code (~3.4M rows)
│   ├── intelligent_chunks (~5-10M rows)
│   └── chunk_embeddings (768-dim vectors)
├── Vertex AI (embeddings)
│   └── gemini-embedding-001
├── Gemini API (LLM)
│   └── gemini-2.5-flash
└── SQUIT App (containerized)
    ├── CLI Interactive
    └── API REST (futuro)
```

---

## 🐳 Deployment con Docker

### Paso 1: Preparar Configuración

```bash
# 1. Crear archivo de producción
cp .env.template .env.production

# 2. Editar configuración
nano .env.production
```

**Configuración de producción**:
```bash
# Entorno
SQUIT_ENV=production

# Google Cloud
GOOGLE_CLOUD_PROJECT=tu-proyecto-prod
GOOGLE_APPLICATION_CREDENTIALS=.config/credentials.production.json

# Gemini
GEMINI_API_KEY=tu-api-key-prod
GEMINI_CHAT_MODEL=gemini-2.5-flash

# Configuración de sistema
LOG_LEVEL=WARNING
LOG_FORMAT_JSON=true
MAX_SEARCH_LIMIT=100
RATE_LIMIT_CALLS=60
ENABLE_CACHING=true
```

### Paso 2: Build y Deploy

```bash
# 1. Build imagen de producción
docker build -t squit:production -f Dockerfile.cli .

# 2. Tag para registry
docker tag squit:production gcr.io/tu-proyecto/squit:latest

# 3. Push a Google Container Registry
docker push gcr.io/tu-proyecto/squit:latest

# 4. Deploy
# Opción A: Cloud Run
gcloud run deploy squit \
  --image gcr.io/tu-proyecto/squit:latest \
  --platform managed \
  --region us-central1 \
  --memory 2Gi

# Opción B: GKE
kubectl apply -f k8s/deployment.yaml
```

---

## 🔐 Secrets Management

### Usar Google Secret Manager (Recomendado)

```bash
# 1. Crear secrets
gcloud secrets create gemini-api-key \
  --data-file=- <<< "$GEMINI_API_KEY"

gcloud secrets create bigquery-credentials \
  --data-file=.config/credentials.json

# 2. Dar permisos al service account
gcloud secrets add-iam-policy-binding gemini-api-key \
  --member="serviceAccount:squit-sa@tu-proyecto.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# 3. Actualizar código para usar Secret Manager
# Ver app/config/secrets_manager.py
```

---

## ⚙️ Configuración de Producción

### Variables de Entorno Críticas

| Variable | Valor Producción | Notas |
|----------|-----------------|-------|
| `SQUIT_ENV` | `production` | Activa config de prod |
| `LOG_LEVEL` | `WARNING` | Solo warnings/errors |
| `LOG_FORMAT_JSON` | `true` | Para agregación |
| `MAX_SEARCH_LIMIT` | `100` | Límite alto |
| `RATE_LIMIT_CALLS` | `60` | 60 req/min |
| `ENABLE_CACHING` | `true` | Cache activado |
| `RETRY_MAX_ATTEMPTS` | `5` | Más reintentos |

### Recursos Recomendados

| Componente | CPU | Memoria | Notas |
|-----------|-----|---------|-------|
| CLI App | 1 CPU | 2 GB | Uso interactivo |
| API REST | 2 CPU | 4 GB | Si se implementa |
| Pipeline | 4 CPU | 8 GB | Para ETL completo |

---

## 📊 Monitoring en Producción

### Logs Estructurados

**Configurar log sink** a Cloud Logging:
```bash
# En tu código, habilitar JSON logging
from utils.structured_logging import setup_structured_logging
setup_structured_logging(level="WARNING", format_json=True)
```

**Query logs en Cloud Logging**:
```
resource.type="cloud_run_revision"
jsonPayload.logger="app.agentic_adk.agents.master_agent"
severity>=WARNING
```

### Métricas

**Métricas clave a monitorear**:
- `search_latency_seconds` - Latencia de búsquedas (P50, P95, P99)
- `requests_total` - Total de requests
- `errors_total` - Total de errores
- `circuit_breaker_state` - Estado del circuit breaker
- `rate_limit_usage_percentage` - Uso del rate limiter

**Export a Cloud Monitoring**:
```python
from google.cloud import monitoring_v3

# Crear métrica custom
client = monitoring_v3.MetricServiceClient()
series = monitoring_v3.TimeSeries()
# ... configuración
client.create_time_series(name=project_name, time_series=[series])
```

---

## 🔄 Updates y Rollbacks

### Update (Zero Downtime)

```bash
# 1. Build nueva versión
docker build -t squit:v2.1.0 .

# 2. Tag y push
docker tag squit:v2.1.0 gcr.io/tu-proyecto/squit:v2.1.0
docker push gcr.io/tu-proyecto/squit:v2.1.0

# 3. Deploy gradual (Cloud Run)
gcloud run deploy squit \
  --image gcr.io/tu-proyecto/squit:v2.1.0 \
  --no-traffic  # Deploy sin tráfico

# 4. Verificar nueva versión
gcloud run services describe squit

# 5. Migrate tráfico gradualmente
gcloud run services update-traffic squit \
  --to-revisions squit-v2-1-0=50,squit-v2-0-0=50

# 6. Si funciona bien, migrar 100%
gcloud run services update-traffic squit \
  --to-latest
```

### Rollback

```bash
# Rollback inmediato a versión anterior
gcloud run services update-traffic squit \
  --to-revisions squit-v2-0-0=100
```

---

## 🧪 Smoke Tests Post-Deploy

```bash
# 1. Health check
curl https://tu-squit-url.run.app/health

# 2. Test búsqueda simple
curl -X POST https://tu-squit-url.run.app/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "inventario", "limit": 5}'

# 3. Verificar logs
gcloud logging read "resource.type=cloud_run_revision" \
  --limit 50 \
  --format json

# 4. Verificar métricas
gcloud monitoring time-series list \
  --filter='metric.type="custom.googleapis.com/squit/search_latency"' \
  --interval-end-time=$(date -u +"%Y-%m-%dT%H:%M:%SZ") \
  --interval-start-time=$(date -u -d '1 hour ago' +"%Y-%m-%dT%H:%M:%SZ")
```

---

## 🔥 Disaster Recovery

Ver [BACKUP_RESTORE.md](BACKUP_RESTORE.md) para procedimientos completos.

### Quick Recovery

```bash
# 1. Verificar backup más reciente
gsutil ls gs://squit-backups/backups/ | tail -5

# 2. Restaurar tabla crítica
python3 -c "
from scripts.backup_system import BackupManager
manager = BackupManager('tu-proyecto', 'squit-backups')
manager.restore_from_backup('20250114_120000', 'chunk_embeddings')
"

# 3. Verificar integridad
python3 scripts/prod/verify_bigquery_access.py
```

---

## 📈 Scaling

### Horizontal Scaling (GKE)

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: squit
spec:
  replicas: 3  # Escalar a 3 replicas
  template:
    spec:
      containers:
      - name: squit
        image: gcr.io/tu-proyecto/squit:latest
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
```

### Vertical Scaling

```bash
# Cloud Run: Aumentar recursos
gcloud run services update squit \
  --memory 4Gi \
  --cpu 2
```

---

## 🔒 Seguridad en Producción

### Checklist
- [ ] Service Account con permisos mínimos
- [ ] Secrets en Secret Manager (no en .env)
- [ ] VPC connector para networking privado
- [ ] Cloud Armor para DDoS protection
- [ ] Audit logging habilitado
- [ ] Backups automáticos configurados
- [ ] Monitoring y alertas activos

### Habilitar Audit Logging

```bash
gcloud projects set-iam-policy tu-proyecto \
  policy.yaml

# policy.yaml
auditConfigs:
- auditLogConfigs:
  - logType: ADMIN_READ
  - logType: DATA_READ
  - logType: DATA_WRITE
  service: bigquery.googleapis.com
```

---

## 📞 Soporte

- **Documentación**: [docs/INDEX.md](../INDEX.md)
- **Troubleshooting**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Issues**: GitHub Issues
- **Email**: ktouma@deacero.com

---

**Última actualización**: 2025-01-14  
**Mantenedor**: Karim Touma

