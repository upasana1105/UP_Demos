#!/bin/bash
# ==============================================================================
# Script: deploy_gcs_pipeline.sh
# Description: Installs the batch BQ external table and abstraction view
#              over exported Cloud Logging files in Google Cloud Storage.
# ==============================================================================

set -e

PROJECT_ID="${PROJECT_ID:-uppdemos}"
BQ_LOCATION="${BQ_LOCATION:-US}"
GCS_DATASET="${GCS_DATASET:-ge_gcs_batch_logs}"
GCS_URI="${GCS_URI:-gs://${PROJECT_ID}-ge-raw-logs/discoveryengine.googleapis.com/gemini_enterprise_user_activity}"

SQL_FILE="$(dirname "$0")/gcs_transformed.sql"

echo "======================================================================"
echo "Deploying GCS Batched Logs Analytical Stack..."
echo "Project: ${PROJECT_ID}"
echo "Dataset: ${GCS_DATASET}"
echo "Source GCS Bucket: ${GCS_URI}"
echo "======================================================================"

# 1. Create BigQuery Dataset
bq mk -f -d --location="${BQ_LOCATION}" "${PROJECT_ID}:${GCS_DATASET}" || true

# 2. Create Cloud Logging Sink to GCS
echo "-> Deploying Cloud Logging Sink to GCS..."
GCS_TEMP="${GCS_URI#gs://}"
GCS_BUCKET_NAME="${GCS_TEMP%%/*}"
SINK_NAME="ge_gcs_batch_sink"
FILTER="logName=\"projects/${PROJECT_ID}/logs/discoveryengine.googleapis.com%2Fgemini_enterprise_user_activity\""

if gcloud logging sinks describe "$SINK_NAME" --project="${PROJECT_ID}" >/dev/null 2>&1; then
    echo "-> Sink exists, updating..."
    SINK_PARAMS=$(gcloud logging sinks update "$SINK_NAME" "storage.googleapis.com/${GCS_BUCKET_NAME}" \
        --log-filter="${FILTER}" --project="${PROJECT_ID}" --format=json)
else
    echo "-> Sink does not exist, creating..."
    SINK_PARAMS=$(gcloud logging sinks create "$SINK_NAME" "storage.googleapis.com/${GCS_BUCKET_NAME}" \
        --log-filter="${FILTER}" --project="${PROJECT_ID}" --format=json)
fi

WRITER_IDENTITY=$(echo "$SINK_PARAMS" | python3 -c "import sys, json; print(json.load(sys.stdin)['writerIdentity'])")

echo "-> Granting storage write permissions to sink identity..."
gcloud projects add-iam-policy-binding "${PROJECT_ID}" --member="$WRITER_IDENTITY" --role="roles/storage.objectCreator" > /dev/null

# 3. Deploy SQL External Table and Views
echo "-> Deploying SQL External Table and Views..."
cat "$SQL_FILE" | \
sed "s/\${PROJECT_ID}/${PROJECT_ID}/g" | \
sed "s/\${GCS_DATASET}/${GCS_DATASET}/g" | \
sed "s|\${GCS_URI}|${GCS_URI}|g" | \
bq query --use_legacy_sql=false --project_id="${PROJECT_ID}" > /dev/null

echo ""
echo "[Success] Successfully created abstracted GCS Analytical views!"
