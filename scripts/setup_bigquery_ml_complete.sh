#!/bin/bash
#
# Setup completo de BigQuery ML con Vertex AI
# Basado en documentación oficial de Google Cloud
#

set -e

PROJECT_ID="dfor-prj-dev"
DATASET_ID="deacero_sql_objects"
REGION="us"
CONNECTION_ID="vertex_ai_connection"
MODEL_NAME="text_embedding_model"

echo "🔗 SQUIT - Setup BigQuery ML + Vertex AI"
echo "=========================================="
echo "📅 $(date)"
echo "🎯 Proyecto: $PROJECT_ID"
echo "📊 Dataset: $DATASET_ID"
echo ""

# Paso 1: Verificar que las APIs estén habilitadas
echo "🔍 Paso 1: Verificando APIs..."
echo "   • BigQuery API"
echo "   • BigQuery Connection API"
echo "   • Vertex AI API"
echo ""

# Paso 2: Crear conexión a Vertex AI usando bq CLI
echo "🔗 Paso 2: Creando conexión a Vertex AI..."
echo ""

# Intentar crear la conexión (ignorar si ya existe)
bq mk --connection \
  --location=$REGION \
  --project_id=$PROJECT_ID \
  --connection_type=CLOUD_RESOURCE \
  $CONNECTION_ID 2>/dev/null || echo "ℹ️  Conexión ya existe o no se pudo crear"

# Verificar la conexión
echo ""
echo "🔍 Verificando conexión..."
bq show --connection --project_id=$PROJECT_ID --location=$REGION $CONNECTION_ID || {
  echo "❌ Error: La conexión no se pudo crear"
  echo ""
  echo "🔧 CREACIÓN MANUAL:"
  echo "1. Ve a: https://console.cloud.google.com/bigquery"
  echo "2. Proyecto: $PROJECT_ID"
  echo "3. Menú > External connections > CREATE CONNECTION"
  echo "4. Connection type: Vertex AI Remote Models"
  echo "5. Connection ID: $CONNECTION_ID"
  echo "6. Location: $REGION"
  echo ""
  exit 1
}

# Paso 3: Obtener service account de la conexión
echo ""
echo "🔍 Paso 3: Obteniendo Service Account..."
SERVICE_ACCOUNT=$(bq show --connection --format=json --project_id=$PROJECT_ID --location=$REGION $CONNECTION_ID | python3 -c "import sys, json; print(json.load(sys.stdin)['cloudResource']['serviceAccountId'])")

echo "   • Service Account: $SERVICE_ACCOUNT"
echo ""

# Paso 4: Dar permisos al service account
echo "🔐 Paso 4: Configurando permisos..."
echo "   ℹ️  El service account necesita rol 'Vertex AI User'"
echo ""
echo "   Ejecuta manualmente:"
echo "   gcloud projects add-iam-policy-binding $PROJECT_ID \\"
echo "     --member=\"serviceAccount:$SERVICE_ACCOUNT\" \\"
echo "     --role=\"roles/aiplatform.user\""
echo ""

# Paso 5: Crear modelo remoto
echo "🤖 Paso 5: Creando modelo de embeddings..."
echo ""

CREATE_MODEL_SQL="CREATE OR REPLACE MODEL \`$PROJECT_ID.$DATASET_ID.$MODEL_NAME\`
REMOTE WITH CONNECTION \`$PROJECT_ID.$REGION.$CONNECTION_ID\`
OPTIONS(ENDPOINT = 'text-embedding-004');"

echo "SQL a ejecutar:"
echo "$CREATE_MODEL_SQL"
echo ""

bq query --use_legacy_sql=false "$CREATE_MODEL_SQL" || {
  echo "❌ Error creando modelo"
  echo ""
  echo "🔧 Crear modelo manualmente en BigQuery Console:"
  echo "```sql"
  echo "$CREATE_MODEL_SQL"
  echo "```"
  exit 1
}

# Paso 6: Probar el modelo
echo ""
echo "🧪 Paso 6: Probando modelo de embeddings..."
echo ""

TEST_SQL="SELECT *
FROM ML.GENERATE_EMBEDDING(
  MODEL \`$PROJECT_ID.$DATASET_ID.$MODEL_NAME\`,
  (SELECT 'Stored procedure para autenticacion de usuarios' AS content),
  STRUCT(TRUE AS flatten_json_output)
)
LIMIT 1;"

bq query --use_legacy_sql=false "$TEST_SQL" || {
  echo "❌ Error probando modelo"
  exit 1
}

echo ""
echo "✅ SETUP COMPLETADO EXITOSAMENTE"
echo "=================================="
echo ""
echo "🎯 Modelo creado: $PROJECT_ID.$DATASET_ID.$MODEL_NAME"
echo "🔗 Conexión: $PROJECT_ID.$REGION.$CONNECTION_ID"
echo "📊 Endpoint: text-embedding-004"
echo ""
echo "🚀 PRÓXIMOS PASOS:"
echo "   1. make create-chunks      # Crear chunks con embeddings reales"
echo "   2. make search-chunks      # Probar búsquedas vectoriales"
echo "   3. make bigquery-full      # Pipeline completo"
echo ""
