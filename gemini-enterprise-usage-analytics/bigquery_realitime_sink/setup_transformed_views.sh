#!/bin/bash
# ==============================================================================
# Setup Transformed Views for Gemini Enterprise & NotebookLM Logs
# ==============================================================================

set -e # Exit immediately on error

PROJECT_ID="${PROJECT_ID:-uppdemos}"
BQ_LOCATION="${BQ_LOCATION:-US}"

GE_TRANSFORMED_DATASET="${GE_TRANSFORMED_DATASET:-ge_transformed}"
NLM_TRANSFORMED_DATASET="${NLM_TRANSFORMED_DATASET:-nlm_transformed}"

GE_DATASET_PREFIX="${GE_DATASET_PREFIX:-ge_raw_logs_}"
NLM_DATASET_PREFIX="${NLM_DATASET_PREFIX:-nlm_raw_logs_}"

SQL_GE="${SQL_GE:-$(dirname "$0")/ge_transformed.sql}"
SQL_NLM="${SQL_NLM:-$(dirname "$0")/nlm_transformed.sql}"

echo "======================================================================"
echo "Starting deployment of transformed views in project: ${PROJECT_ID}"
echo "GE Transformed Dataset: ${GE_TRANSFORMED_DATASET}"
echo "NLM Transformed Dataset: ${NLM_TRANSFORMED_DATASET}"
echo "======================================================================"

echo "-> Verifying Destination Datasets..."
bq mk -f -d --location="${BQ_LOCATION}" "${PROJECT_ID}:${GE_TRANSFORMED_DATASET}" || true
bq mk -f -d --location="${BQ_LOCATION}" "${PROJECT_ID}:${NLM_TRANSFORMED_DATASET}" || true

echo "-> Deploying Gemini Enterprise (GE) Logs View..."

if [ ! -f "$SQL_GE" ]; then
  echo "[Error] file not found: $SQL_GE"
  exit 1
fi

cat "$SQL_GE" | \
sed "s/\${PROJECT_ID}/${PROJECT_ID}/g" | \
sed "s/\${GE_TRANSFORMED_DATASET}/${GE_TRANSFORMED_DATASET}/g" | \
sed "s/\${GE_DATASET_PREFIX}/${GE_DATASET_PREFIX}/g" | \
bq query --use_legacy_sql=false --project_id="${PROJECT_ID}"

echo "----------------------------------------------------------------------"
echo "[Caution] If you encounter a 'Not found: Table' error above, it means"
echo "          your newly created sinks have not captured any real user logs"
echo "          yet. BigQuery materializes sink tables on first insert."
echo ""
echo "          Generate a few active logs in your Gemini/NotebookLM engines,"
echo "          then simply re-run this setup_transformed_views.sh script!"
echo "----------------------------------------------------------------------"

echo "[Success] GE View deployed."

echo "-> Deploying NotebookLM (NLM) Logs View..."

if [ ! -f "$SQL_NLM" ]; then
  echo "[Error] file not found: $SQL_NLM"
  exit 1
fi

cat "$SQL_NLM" | \
sed "s/\${PROJECT_ID}/${PROJECT_ID}/g" | \
sed "s/\${NLM_TRANSFORMED_DATASET}/${NLM_TRANSFORMED_DATASET}/g" | \
sed "s/\${NLM_DATASET_PREFIX}/${NLM_DATASET_PREFIX}/g" | \
bq query --use_legacy_sql=false --project_id="${PROJECT_ID}"

echo "[Success] NLM View deployed."

echo "======================================================================"
echo "Deployment Complete!"
echo "======================================================================"
