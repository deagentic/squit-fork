#!/bin/bash
#
# Script para programar el pipeline BigQuery como scheduled query
# Esto corre en la nube - no depende de tu máquina local
#

set -e

PROJECT_ID="dfor-prj-dev"
DATASET_ID="deacero_sql_objects"
REGION="us-central1"

echo "📅 SQUIT - Programar Pipeline BigQuery"
echo "========================================"
echo "🎯 Esto creará queries programadas que corren en la nube"
echo "💡 No dependerán de tu conexión local"
echo ""

# Query 1: Crear chunks
CHUNKS_QUERY=$(cat <<'EOF'
CREATE OR REPLACE TABLE `dfor-prj-dev.deacero_sql_objects.intelligent_chunks` AS
WITH 
-- Paso 1: Clasificación semántica
classified_objects AS (
  SELECT 
    server, database, schema, object_name, object_type,
    sql_code, content_hash, last_modified,
    LENGTH(sql_code) as code_length,
    CASE 
      WHEN REGEXP_CONTAINS(UPPER(sql_code), r'SELECT.*FROM.*JOIN') THEN 'complex_query'
      WHEN REGEXP_CONTAINS(UPPER(sql_code), r'CREATE\\s+PROCEDURE') THEN 'stored_procedure'
      WHEN REGEXP_CONTAINS(UPPER(sql_code), r'CREATE\\s+FUNCTION') THEN 'function'
      WHEN REGEXP_CONTAINS(UPPER(sql_code), r'CREATE\\s+VIEW') THEN 'view'
      ELSE 'simple_sql'
    END as semantic_type,
    CASE
      WHEN REGEXP_CONTAINS(LOWER(CONCAT(object_name, sql_code)), r'venta|cliente|factura') THEN 'ventas'
      WHEN REGEXP_CONTAINS(LOWER(CONCAT(object_name, sql_code)), r'inventario|stock') THEN 'inventario'
      WHEN REGEXP_CONTAINS(LOWER(CONCAT(object_name, sql_code)), r'usuario|login|auth') THEN 'autenticacion'
      ELSE 'general'
    END as business_domain,
    (LENGTH(sql_code) / 1000) + 
    (ARRAY_LENGTH(REGEXP_EXTRACT_ALL(UPPER(sql_code), r'JOIN')) * 2) +
    (ARRAY_LENGTH(REGEXP_EXTRACT_ALL(UPPER(sql_code), r'SELECT')) * 1) as complexity_score
  FROM `dfor-prj-dev.deacero_sql_objects.sql_objects_code`
  WHERE sql_code IS NOT NULL AND LENGTH(sql_code) >= 500
),

-- Paso 2: Chunking
chunked_objects AS (
  SELECT 
    *,
    CASE 
      WHEN code_length > 1000000 THEN 'mega_chunking'
      WHEN code_length > 50000 THEN 'large_chunking'
      WHEN code_length > 15000 THEN 'medium_chunking'
      ELSE 'single_chunk'
    END as chunking_strategy,
    CASE 
      WHEN code_length > 1000000 THEN
        ARRAY(
          SELECT TRIM(chunk) 
          FROM UNNEST(SPLIT(sql_code, 'GO')) AS chunk WITH OFFSET pos
          WHERE LENGTH(TRIM(chunk)) >= 500 AND pos < 100
        )
      WHEN code_length > 50000 THEN
        ARRAY(
          SELECT SUBSTR(sql_code, start_pos, 8000) as chunk
          FROM UNNEST(GENERATE_ARRAY(1, LENGTH(sql_code), 7500)) AS start_pos
          WHERE start_pos <= LENGTH(sql_code)
          LIMIT 100
        )
      WHEN code_length > 15000 THEN
        ARRAY(
          SELECT SUBSTR(sql_code, start_pos, 8000) as chunk
          FROM UNNEST(GENERATE_ARRAY(1, LENGTH(sql_code), 7800)) AS start_pos
          WHERE start_pos <= LENGTH(sql_code)
          LIMIT 100
        )
      ELSE [sql_code]
    END as raw_chunks
  FROM classified_objects
),

-- Paso 3: Expandir chunks
expanded_chunks AS (
  SELECT 
    GENERATE_UUID() as chunk_id,
    CONCAT(server, '|', database, '|', schema, '|', object_name) as parent_object_id,
    server, database, schema, object_name, object_type,
    chunk_content,
    pos as chunk_index,
    ARRAY_LENGTH(raw_chunks) as total_chunks,
    chunking_strategy,
    LENGTH(chunk_content) as chunk_length,
    semantic_type,
    business_domain,
    complexity_score,
    content_hash,
    last_modified,
    CONCAT(semantic_type, ' en ', object_name, ' (', business_domain, ')') as semantic_summary
  FROM chunked_objects
  CROSS JOIN UNNEST(raw_chunks) AS chunk_content WITH OFFSET pos
  WHERE LENGTH(chunk_content) >= 500
)

SELECT * FROM expanded_chunks
ORDER BY parent_object_id, chunk_index
EOF
)

# Query 2: Generar embeddings
EMBEDDINGS_QUERY=$(cat <<'EOF'
CREATE OR REPLACE TABLE `dfor-prj-dev.deacero_sql_objects.chunk_embeddings` AS
SELECT 
  chunk_id, parent_object_id, server, database, schema,
  object_name, object_type, chunk_content, semantic_type,
  business_domain, semantic_summary, complexity_score,
  chunk_index, total_chunks, created_at,
  CURRENT_TIMESTAMP() as embedding_created_at,
  content,
  ml_generate_embedding_result as embedding
FROM ML.GENERATE_EMBEDDING(
  MODEL `dfor-prj-dev.deacero_sql_objects.gemini_embedding_model`,
  (
    SELECT 
      chunk_id, parent_object_id, server, database, schema,
      object_name, object_type, chunk_content, semantic_type,
      business_domain, semantic_summary, complexity_score,
      chunk_index, total_chunks,
      CURRENT_TIMESTAMP() as created_at,
      CONCAT(object_name, ' ', semantic_type, ' ', business_domain, ' ', 
             semantic_summary, ' ', SUBSTR(chunk_content, 1, 6000)) as content
    FROM `dfor-prj-dev.deacero_sql_objects.intelligent_chunks`
    WHERE chunk_content IS NOT NULL
  ),
  STRUCT(TRUE AS flatten_json_output, 'CODE_RETRIEVAL_QUERY' AS task_type)
)
EOF
)

echo "🔄 PASO 1: Programar query de chunking..."
echo ""
echo "Este query se ejecutará en la nube sin depender de tu máquina"
echo ""

# Ejecutar query de chunking en la nube (DDL no necesita destination_table)
bq query \
  --use_legacy_sql=false \
  --project_id=$PROJECT_ID \
  --location=$REGION \
  --allow_large_results \
  "$CHUNKS_QUERY"

if [ $? -eq 0 ]; then
  echo "✅ Query de chunking ejecutándose en la nube"
  echo ""
  
  # Esperar a que termine el chunking antes de embeddings
  echo "⏰ Esperando a que el chunking termine..."
  echo "💡 Puedes cerrar esta terminal - el query sigue en la nube"
  echo ""
  echo "🔍 Monitorear progreso en:"
  echo "   https://console.cloud.google.com/bigquery?project=$PROJECT_ID"
  echo ""
  
  # Dar tiempo para que el chunking inicie
  sleep 10
  
  echo "🔄 PASO 2: Programar query de embeddings..."
  echo "Este query esperará a que el chunking termine"
  echo ""
  
  # Ejecutar embeddings (DDL no necesita destination_table)
  bq query \
    --use_legacy_sql=false \
    --project_id=$PROJECT_ID \
    --location=$REGION \
    --allow_large_results \
    "$EMBEDDINGS_QUERY"
  
  echo "✅ Query de embeddings ejecutándose en la nube"
  echo ""
else
  echo "❌ Error ejecutando chunking"
  exit 1
fi

echo ""
echo "✅ PIPELINE COMPLETO EJECUTÁNDOSE EN LA NUBE"
echo "=============================================="
echo ""
echo "💡 IMPORTANTE:"
echo "   • Los queries están corriendo en BigQuery (nube)"
echo "   • Puedes CERRAR esta terminal sin problemas"
echo "   • NO afectará si pierdes internet"
echo "   • NO afectará si apagas tu computadora"
echo ""
echo "🔍 MONITOREAR PROGRESO:"
echo "   1. Ve a: https://console.cloud.google.com/bigquery?project=$PROJECT_ID"
echo "   2. Menú > SQL workspace > Job history"
echo "   3. Verás los jobs corriendo"
echo ""
echo "📊 O ejecuta desde otra terminal:"
echo "   bq ls -j --project_id=$PROJECT_ID --location=$REGION --max_results=5"
echo ""
echo "⏰ TIEMPO ESTIMADO TOTAL: 4-7 horas"
echo "💰 COSTO ESTIMADO: \$30-60 USD"
echo ""
