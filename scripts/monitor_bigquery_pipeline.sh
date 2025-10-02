#!/bin/bash
#
# Script para monitorear el progreso del pipeline BigQuery
# Ejecuta esto desde otra terminal mientras el pipeline corre
#

PROJECT_ID="dfor-prj-dev"
DATASET_ID="deacero_sql_objects"
REGION="us-central1"

echo "📊 SQUIT - Monitor Pipeline BigQuery"
echo "====================================="
echo ""

# Función para mostrar progreso de chunks
check_chunks_progress() {
  echo "🧩 PROGRESO DE CHUNKING:"
  echo ""
  
  bq query --use_legacy_sql=false --project_id=$PROJECT_ID --location=$REGION \
    "SELECT 
       COUNT(*) as total_chunks,
       COUNT(DISTINCT parent_object_id) as unique_objects,
       AVG(chunk_length) as avg_chunk_length,
       MAX(complexity_score) as max_complexity,
       FORMAT_TIMESTAMP('%Y-%m-%d %H:%M:%S', MAX(CURRENT_TIMESTAMP())) as last_update
     FROM \`$PROJECT_ID.$DATASET_ID.intelligent_chunks\`" 2>/dev/null || echo "   ⏳ Tabla de chunks aún no existe..."
  
  echo ""
}

# Función para mostrar progreso de embeddings
check_embeddings_progress() {
  echo "🎯 PROGRESO DE EMBEDDINGS:"
  echo ""
  
  bq query --use_legacy_sql=false --project_id=$PROJECT_ID --location=$REGION \
    "SELECT 
       COUNT(*) as total_embeddings,
       COUNT(DISTINCT parent_object_id) as unique_objects,
       AVG(ARRAY_LENGTH(embedding)) as avg_dimensions,
       FORMAT_TIMESTAMP('%Y-%m-%d %H:%M:%S', MAX(embedding_created_at)) as last_update
     FROM \`$PROJECT_ID.$DATASET_ID.chunk_embeddings\`
     WHERE embedding IS NOT NULL" 2>/dev/null || echo "   ⏳ Tabla de embeddings aún no existe..."
  
  echo ""
}

# Función para mostrar jobs activos
check_active_jobs() {
  echo "🔄 JOBS ACTIVOS EN BIGQUERY:"
  echo ""
  
  bq ls -j --project_id=$PROJECT_ID --location=$REGION --max_results=5 --format=pretty
  
  echo ""
}

# Loop de monitoreo
echo "🔍 Monitoreando pipeline..."
echo "💡 Presiona Ctrl+C para salir"
echo ""

while true; do
  clear
  echo "📊 SQUIT - Monitor Pipeline BigQuery"
  echo "====================================="
  echo "⏰ $(date)"
  echo ""
  
  check_active_jobs
  check_chunks_progress
  check_embeddings_progress
  
  echo "🔄 Actualizando en 30 segundos..."
  echo "💡 Presiona Ctrl+C para salir"
  
  sleep 30
done
