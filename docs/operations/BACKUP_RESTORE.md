# 💾 Backup & Restore Guide - SQUIT

Procedimientos para backup y recuperación de datos críticos del sistema SQUIT.

---

## 📋 Componentes a Respaldar

### Críticos (Backup Diario)
1. **chunk_embeddings** - Tabla con vectores (más costosa de regenerar)
2. **intelligent_chunks** - Chunks procesados
3. **pipeline_progress** - Tracking de progreso
4. **query_history** - Historial de consultas

### Importantes (Backup Semanal)
5. **sql_objects_code** - Objetos SQL originales (fuente)
6. **pipeline_metrics** - Métricas históricas
7. **pipeline_errors** - Log de errores

### Configuración (Backup Manual)
8. **Credenciales** - Service accounts
9. **Catálogo** - data/catalogo.csv
10. **Variables** - .env

---

## 🗓️ Estrategia de Backup

| Componente | Frecuencia | Retención | Prioridad |
|------------|-----------|-----------|-----------|
| chunk_embeddings | Diario | 30 días | 🔴 Crítico |
| intelligent_chunks | Diario | 30 días | 🔴 Crítico |
| pipeline_progress | Diario | 90 días | 🟡 Alto |
| query_history | Semanal | 180 días | 🟢 Medio |
| sql_objects_code | Mensual | 365 días | 🟢 Medio |

---

## 💾 Backup Manual

### 1. Backup de Tabla de Embeddings

```bash
# Método 1: Export a Cloud Storage (recomendado)
bq extract \
  --destination_format=PARQUET \
  --compression=SNAPPY \
  dfor-prj-dev:deacero_sql_objects.chunk_embeddings \
  gs://squit-backups/embeddings/$(date +%Y%m%d)/*.parquet

# Método 2: Export a archivo local
bq extract \
  --destination_format=NEWLINE_DELIMITED_JSON \
  dfor-prj-dev:deacero_sql_objects.chunk_embeddings \
  ./backups/embeddings_$(date +%Y%m%d).jsonl
```

### 2. Backup de Múltiples Tablas

```bash
#!/bin/bash
# backup_all.sh

DATE=$(date +%Y%m%d_%H%M%S)
PROJECT="dfor-prj-dev"
DATASET="deacero_sql_objects"
BUCKET="gs://squit-backups"

# Tablas críticas
TABLES=(
    "chunk_embeddings"
    "intelligent_chunks"
    "pipeline_progress"
    "query_history"
)

for TABLE in "${TABLES[@]}"; do
    echo "📦 Backing up $TABLE..."
    
    bq extract \
        --destination_format=PARQUET \
        --compression=SNAPPY \
        $PROJECT:$DATASET.$TABLE \
        $BUCKET/backups/$DATE/$TABLE/*.parquet
    
    echo "✅ $TABLE backed up"
done

echo "🎉 Backup completo: $DATE"
```

### 3. Backup de Credenciales (Cifrado)

```bash
# Backup cifrado de credenciales
tar -czf credentials_backup_$(date +%Y%m%d).tar.gz \
  .config/credentials.json \
  .env

# Cifrar con GPG
gpg --symmetric --cipher-algo AES256 \
  credentials_backup_$(date +%Y%m%d).tar.gz

# Subir a bucket privado
gsutil cp credentials_backup_*.tar.gz.gpg \
  gs://squit-secrets-backup/

# Limpiar local
rm credentials_backup_*
```

---

## 🔄 Restore Procedures

### 1. Restaurar Tabla de Embeddings

```bash
# Desde Cloud Storage
BACKUP_DATE="20250114_120000"

bq load \
  --source_format=PARQUET \
  --replace \
  dfor-prj-dev:deacero_sql_objects.chunk_embeddings \
  gs://squit-backups/backups/$BACKUP_DATE/chunk_embeddings/*.parquet

# Verificar restauración
bq query --nouse_legacy_sql \
  "SELECT COUNT(*) as total FROM \`dfor-prj-dev.deacero_sql_objects.chunk_embeddings\`"
```

### 2. Restaurar desde Backup Local

```bash
# Load desde archivo local
bq load \
  --source_format=NEWLINE_DELIMITED_JSON \
  --replace \
  dfor-prj-dev:deacero_sql_objects.chunk_embeddings \
  ./backups/embeddings_20250114.jsonl

# Con schema explícito
bq load \
  --source_format=NEWLINE_DELIMITED_JSON \
  --replace \
  --schema=schema/embeddings_schema.json \
  dfor-prj-dev:deacero_sql_objects.chunk_embeddings \
  ./backups/embeddings_20250114.jsonl
```

### 3. Restaurar Credenciales

```bash
# 1. Descargar backup cifrado
gsutil cp gs://squit-secrets-backup/credentials_backup_20250114.tar.gz.gpg .

# 2. Descifrar
gpg --decrypt credentials_backup_20250114.tar.gz.gpg > credentials_backup.tar.gz

# 3. Extraer
tar -xzf credentials_backup.tar.gz

# 4. Verificar
ls -la .config/credentials.json .env
```

---

## 🤖 Backup Automatizado

### Script de Backup Automático

```python
# scripts/tools/automated_backup.py
"""
Backup automatizado de tablas críticas.
"""

from google.cloud import bigquery, storage
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AutomatedBackup:
    def __init__(self, project_id: str, dataset_id: str, backup_bucket: str):
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.backup_bucket = backup_bucket
        self.bq_client = bigquery.Client(project=project_id)
        self.storage_client = storage.Client()
    
    def backup_table(self, table_name: str) -> str:
        """Hace backup de una tabla a Cloud Storage."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        destination_uri = (
            f"gs://{self.backup_bucket}/backups/{timestamp}/"
            f"{table_name}/*.parquet"
        )
        
        table_id = f"{self.project_id}.{self.dataset_id}.{table_name}"
        
        job_config = bigquery.ExtractJobConfig(
            destination_format=bigquery.DestinationFormat.PARQUET,
            compression=bigquery.Compression.SNAPPY
        )
        
        extract_job = self.bq_client.extract_table(
            table_id,
            destination_uri,
            job_config=job_config
        )
        
        extract_job.result()
        
        logger.info(f"✅ Backup completado: {table_name} → {destination_uri}")
        return destination_uri
    
    def backup_all_critical(self):
        """Hace backup de todas las tablas críticas."""
        critical_tables = [
            "chunk_embeddings",
            "intelligent_chunks",
            "pipeline_progress",
            "query_history"
        ]
        
        results = {}
        for table in critical_tables:
            try:
                uri = self.backup_table(table)
                results[table] = {"status": "success", "uri": uri}
            except Exception as e:
                logger.error(f"❌ Error backing up {table}: {e}")
                results[table] = {"status": "error", "error": str(e)}
        
        return results

if __name__ == "__main__":
    backup = AutomatedBackup(
        project_id="dfor-prj-dev",
        dataset_id="deacero_sql_objects",
        backup_bucket="squit-backups"
    )
    
    results = backup.backup_all_critical()
    print(f"Backup completado: {results}")
```

### Cron Job (Cloud Scheduler)

```bash
# Crear Cloud Scheduler job para backup diario
gcloud scheduler jobs create http squit-daily-backup \
  --schedule="0 2 * * *" \
  --uri="https://tu-backup-function-url.run.app/backup" \
  --http-method=POST \
  --time-zone="America/Mexico_City"
```

---

## 🔍 Verificación de Backups

### Listar Backups Disponibles

```bash
# Ver backups en Cloud Storage
gsutil ls gs://squit-backups/backups/

# Ver backups recientes
gsutil ls gs://squit-backups/backups/ | tail -10

# Verificar tamaño
gsutil du -sh gs://squit-backups/backups/20250114_120000/
```

### Validar Integridad

```bash
# Cargar backup a tabla temporal y validar
bq load \
  --source_format=PARQUET \
  dfor-prj-dev:deacero_sql_objects.chunk_embeddings_test \
  gs://squit-backups/backups/20250114_120000/chunk_embeddings/*.parquet

# Comparar count
bq query --nouse_legacy_sql "
SELECT 
  (SELECT COUNT(*) FROM \`dfor-prj-dev.deacero_sql_objects.chunk_embeddings\`) as prod,
  (SELECT COUNT(*) FROM \`dfor-prj-dev.deacero_sql_objects.chunk_embeddings_test\`) as backup
"

# Limpiar tabla temporal
bq rm -f dfor-prj-dev:deacero_sql_objects.chunk_embeddings_test
```

---

## 🚨 Recovery Scenarios

### Scenario 1: Tabla Corrupta

**Problema**: chunk_embeddings corrupta o con datos malos.

**Solución**:
```bash
# 1. Identificar último backup bueno
gsutil ls gs://squit-backups/backups/ | grep chunk_embeddings

# 2. Crear tabla temporal con backup
bq load --replace \
  dfor-prj-dev:deacero_sql_objects.chunk_embeddings_backup \
  gs://squit-backups/backups/YYYYMMDD_HHMMSS/chunk_embeddings/*.parquet

# 3. Verificar datos
bq query "SELECT COUNT(*), AVG(ARRAY_LENGTH(embedding)) FROM \`..._backup\`"

# 4. Swap tablas
bq cp --force \
  dfor-prj-dev:deacero_sql_objects.chunk_embeddings \
  dfor-prj-dev:deacero_sql_objects.chunk_embeddings_old

bq cp --force \
  dfor-prj-dev:deacero_sql_objects.chunk_embeddings_backup \
  dfor-prj-dev:deacero_sql_objects.chunk_embeddings

# 5. Verificar sistema
python3 scripts/prod/verify_bigquery_access.py
```

### Scenario 2: Pérdida Completa de Dataset

**Problema**: Dataset completo eliminado accidentalmente.

**Solución**:
```bash
# 1. Recrear dataset
bq mk --dataset \
  --location=us-central1 \
  dfor-prj-dev:deacero_sql_objects

# 2. Restaurar todas las tablas desde backup más reciente
BACKUP_DATE="20250114_120000"
TABLES=("chunk_embeddings" "intelligent_chunks" "pipeline_progress")

for TABLE in "${TABLES[@]}"; do
    bq load --replace \
      dfor-prj-dev:deacero_sql_objects.$TABLE \
      gs://squit-backups/backups/$BACKUP_DATE/$TABLE/*.parquet
done

# 3. Recrear índice vectorial
python3 -c "
from app.bigquery_vector.chunking_pipeline import BigQueryChunkingPipeline
pipeline = BigQueryChunkingPipeline()
pipeline.create_vector_index()
"

# 4. Verificar integridad completa
python3 scripts/dev/validate_phase1.py
```

### Scenario 3: Pipeline Interrumpido

**Problema**: Pipeline de embeddings interrumpido a mitad de camino.

**Solución**:
```bash
# 1. Verificar último checkpoint
python3 scripts/run_bigquery_pipeline.py --list-runs

# 2. Continuar desde checkpoint
python3 scripts/run_bigquery_pipeline.py --skip-chunks

# O restaurar desde backup y reiniciar
# (si checkpoint está corrupto)
```

---

## 🔐 Backup de Secrets

### Backup Seguro

```bash
# 1. Crear bucket privado para secrets
gsutil mb -l us-central1 -b on gs://squit-secrets-private/

# 2. Habilitar cifrado
gsutil encryption set -k \
  projects/tu-proyecto/locations/us-central1/keyRings/squit/cryptoKeys/secrets \
  gs://squit-secrets-private/

# 3. Backup cifrado
tar -czf secrets.tar.gz .config/ .env data/catalogo.csv
gpg --symmetric --cipher-algo AES256 secrets.tar.gz
gsutil cp secrets.tar.gz.gpg gs://squit-secrets-private/$(date +%Y%m%d)/

# 4. Limpiar local
rm secrets.tar.gz secrets.tar.gz.gpg
```

### Restore de Secrets

```bash
# 1. Descargar
gsutil cp gs://squit-secrets-private/20250114/secrets.tar.gz.gpg .

# 2. Descifrar
gpg --decrypt secrets.tar.gz.gpg > secrets.tar.gz

# 3. Extraer
tar -xzf secrets.tar.gz

# 4. Verificar
ls -la .config/credentials.json .env data/catalogo.csv
```

---

## 📊 Monitoreo de Backups

### Verificar Backups Recientes

```bash
# Script de verificación
#!/bin/bash
# check_backups.sh

echo "🔍 Verificando backups recientes..."

BUCKET="gs://squit-backups/backups"
HOURS_AGO=24

# Buscar backups recientes
RECENT_BACKUPS=$(gsutil ls -l $BUCKET/*/*.parquet | \
  awk -v cutoff=$(date -d "$HOURS_AGO hours ago" +%s) \
  '$2 > cutoff {print $3}' | wc -l)

if [ $RECENT_BACKUPS -gt 0 ]; then
    echo "✅ $RECENT_BACKUPS backups encontrados (últimas $HOURS_AGO horas)"
else
    echo "⚠️ Sin backups recientes. Ejecutar backup inmediatamente."
fi
```

### Alertas de Backup

```bash
# Cloud Monitoring alert para backups faltantes
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="SQUIT Backup Missing" \
  --condition-display-name="No backups en 25 horas" \
  --condition-threshold-value=0 \
  --condition-threshold-duration=90000s \
  --condition-filter='resource.type="gcs_bucket" AND metric.type="storage.googleapis.com/storage/object_count"'
```

---

## 🧪 Testing de Recovery

### Dry Run Recovery

```bash
# 1. Crear dataset de testing
bq mk --dataset test_recovery

# 2. Restaurar a dataset temporal
bq load \
  dfor-prj-dev:test_recovery.chunk_embeddings_test \
  gs://squit-backups/backups/latest/chunk_embeddings/*.parquet

# 3. Validar datos
bq query --nouse_legacy_sql "
SELECT 
    COUNT(*) as total_rows,
    COUNT(DISTINCT parent_object_id) as unique_objects,
    AVG(ARRAY_LENGTH(embedding)) as avg_dimensions
FROM \`dfor-prj-dev.test_recovery.chunk_embeddings_test\`
"

# 4. Limpiar
bq rm -r -f dfor-prj-dev:test_recovery
```

---

## 📅 Calendario de Backups

### Diario (2:00 AM)
```bash
0 2 * * * /path/to/backup_critical_tables.sh
```

### Semanal (Domingo 3:00 AM)
```bash
0 3 * * 0 /path/to/backup_all_tables.sh
```

### Mensual (Día 1, 4:00 AM)
```bash
0 4 1 * * /path/to/backup_full_dataset.sh
```

---

## 💰 Costos de Backup

### Estimaciones

| Tabla | Tamaño | Backup Cost/mes | Storage Cost/mes |
|-------|--------|-----------------|------------------|
| chunk_embeddings | ~50 GB | $10 | $1.25 |
| intelligent_chunks | ~10 GB | $2 | $0.25 |
| pipeline_progress | ~100 MB | $0.10 | $0.01 |
| **Total** | **~60 GB** | **~$12** | **~$1.50** |

**Total mensual estimado**: ~$15 USD

### Optimización de Costos

```bash
# 1. Usar Nearline storage para backups >30 días
gsutil mb -c NEARLINE gs://squit-backups-nearline/

# 2. Lifecycle policy para mover backups viejos
cat > lifecycle.json <<EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "SetStorageClass", "storageClass": "NEARLINE"},
        "condition": {"age": 30}
      },
      {
        "action": {"type": "SetStorageClass", "storageClass": "COLDLINE"},
        "condition": {"age": 90}
      },
      {
        "action": {"type": "Delete"},
        "condition": {"age": 365}
      }
    ]
  }
}
EOF

gsutil lifecycle set lifecycle.json gs://squit-backups/
```

---

## 🔍 Auditoría de Backups

### Log de Backups

```bash
# Ver historial de backups
gcloud logging read \
  "resource.type=gcs_bucket AND \
   resource.labels.bucket_name=squit-backups AND \
   protoPayload.methodName=storage.objects.create" \
  --limit=50 \
  --format=json

# Crear alerta si backup falla
gcloud alpha monitoring policies create \
  --notification-channels=EMAIL_CHANNEL \
  --display-name="SQUIT Backup Failed" \
  --condition-display-name="Backup job failed" \
  --condition-filter='severity=ERROR AND resource.type="cloud_scheduler_job"'
```

---

## 📞 Contacto en Emergencias

- **DevOps Team**: devops@deacero.com
- **Data Team**: ktouma@deacero.com
- **On-Call**: +52-XXX-XXX-XXXX

---

## ✅ Checklist de Recovery Test

- [ ] Backup automático funcionando (verificar últimas 24h)
- [ ] Restore de tabla test exitoso
- [ ] Restore de credenciales funcional
- [ ] Alertas de backup configuradas
- [ ] Documentación actualizada
- [ ] Equipo entrenado en procedimientos
- [ ] Recovery time <30 minutos validado

---

**Última actualización**: 2025-01-14  
**Próxima revisión**: 2025-02-14  
**Responsable**: Karim Touma

