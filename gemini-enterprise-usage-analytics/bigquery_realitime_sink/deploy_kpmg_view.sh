#!/bin/bash
# ==============================================================================
# Script: deploy_kpmg_view.sh
# Description: Deploys the KPMG future-proof standardization view.
# ==============================================================================

set -e

PROJECT_ID="${PROJECT_ID:-uppdemos}"
GE_TRANSFORMED_DATASET="${GE_TRANSFORMED_DATASET:-ge_transformed}"
GE_DATASET_PREFIX="${GE_DATASET_PREFIX:-ge_raw_logs_}"

SQL_FILE="$(dirname "$0")/kpmg_standardized_logs.sql"

echo "======================================================================"
echo "Deploying KPMG Standardized View..."
echo "Project: ${PROJECT_ID}"
echo "Dataset: ${GE_TRANSFORMED_DATASET}"
echo "======================================================================"

if [ ! -f "$SQL_FILE" ]; then
  echo "[Error] file not found: $SQL_FILE"
  exit 1
fi

cat "$SQL_FILE" | \
sed "s/\${PROJECT_ID}/${PROJECT_ID}/g" | \
sed "s/\${GE_TRANSFORMED_DATASET}/${GE_TRANSFORMED_DATASET}/g" | \
sed "s/\${GE_DATASET_PREFIX}/${GE_DATASET_PREFIX}/g" | \
bq query --use_legacy_sql=false --project_id="${PROJECT_ID}"

echo "[Success] KPMG Future-Proof View deployed!"
