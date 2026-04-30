#!/bin/bash
# ==============================================================================
# Script: setup_user_logs_raw.sh
# Description: Automates the creation of isolated BigQuery datasets and
#              Cloud Logging sinks to natively track Gemini Enterprise and
#              NotebookLM Enterprise metrics cleanly.
# ==============================================================================

PROJECT_ID="${PROJECT_ID:-uppdemos}"
APP_ID="${APP_ID:-gemini-enterprise-gm_1771086459519}"
LOCATION="${LOCATION:-global}"
BQ_LOCATION="${BQ_LOCATION:-US}"

GE_DATASET_PREFIX="${GE_DATASET_PREFIX:-ge_raw_logs_}"
GE_SINK_PREFIX="${GE_SINK_PREFIX:-ge_raw_logs_}"

NLM_DATASET_PREFIX="${NLM_DATASET_PREFIX:-nlm_raw_logs_}"
NLM_SINK_PREFIX="${NLM_SINK_PREFIX:-nlm_raw_logs_}"

GE_METHODS=(
  "Search"
  "Assist"
  "StreamAssist"
  "AnswerQuery"
  "CreateEngine"
  "UpdateEngine"
  "SetIamPolicy"
  "CreateAgent"
  "UpdateAgent"
  "CreateAgentRequest"
  "GenerateGroundedContent"
  "UpdateDataConnector"
  "AddContextFile"
  "UploadSessionFile"
  "WriteUserEvent"
)

NLM_METHODS=(
  "CreateNotebook"
  "ShareNotebook"
  "BatchDeleteNotebooks"
  "GetNotebook"
  "InteractSources"
  "GenerateFreeFormStreamed"
)

BASE_LOG_NAME="projects/${PROJECT_ID}/logs/discoveryengine.googleapis.com%2Fgemini_enterprise_user_activity"

echo "======================================================================"
echo "Deploying Gemini Enterprise sinks (Prefix: ${GE_DATASET_PREFIX})..."
echo "======================================================================"

for METHOD in "${GE_METHODS[@]}"; do
    echo "--------------------------------------------------------"
    echo "Deploying GE isolation for method: ${METHOD}..."
    
    LOWER_METHOD=$(echo "$METHOD" | tr '[:upper:]' '[:lower:]')
    DATASET_NAME="${GE_DATASET_PREFIX}${LOWER_METHOD}"
    SINK_NAME="${GE_SINK_PREFIX}${LOWER_METHOD}"
    
    bq mk -f -d --location="${BQ_LOCATION}" "$DATASET_NAME" || true
    
    FILTER="logName=\"${BASE_LOG_NAME}\" AND jsonPayload.logMetadata.methodName=\"${METHOD}\""
    
    SINK_PARAMS=$(gcloud logging sinks create "$SINK_NAME" "bigquery.googleapis.com/projects/${PROJECT_ID}/datasets/${DATASET_NAME}" \
        --log-filter="${FILTER}" --use-partitioned-tables --format=json 2>/dev/null || \
        gcloud logging sinks update "$SINK_NAME" "bigquery.googleapis.com/projects/${PROJECT_ID}/datasets/${DATASET_NAME}" \
        --log-filter="${FILTER}" --use-partitioned-tables --format=json)
        
    WRITER_IDENTITY=$(echo "$SINK_PARAMS" | python3 -c "import sys, json; print(json.load(sys.stdin)['writerIdentity'])")
    
    gcloud projects add-iam-policy-binding "${PROJECT_ID}" --member="$WRITER_IDENTITY" --role="roles/bigquery.dataEditor" > /dev/null
done

echo "======================================================================"
echo "Deploying NotebookLM sinks (Prefix: ${NLM_DATASET_PREFIX})..."
echo "======================================================================"

for METHOD in "${NLM_METHODS[@]}"; do
    echo "--------------------------------------------------------"
    echo "Deploying NotebookLM isolation for method: ${METHOD}..."
    
    LOWER_METHOD=$(echo "$METHOD" | tr '[:upper:]' '[:lower:]')
    DATASET_NAME="${NLM_DATASET_PREFIX}${LOWER_METHOD}"
    SINK_NAME="${NLM_SINK_PREFIX}${LOWER_METHOD}"
    
    bq mk -f -d --location="${BQ_LOCATION}" "$DATASET_NAME" || true
    
    FILTER="logName=\"${BASE_LOG_NAME}\" AND jsonPayload.logMetadata.methodName=\"${METHOD}\""
    
    SINK_PARAMS=$(gcloud logging sinks create "$SINK_NAME" "bigquery.googleapis.com/projects/${PROJECT_ID}/datasets/${DATASET_NAME}" \
        --log-filter="${FILTER}" --use-partitioned-tables --format=json 2>/dev/null || \
        gcloud logging sinks update "$SINK_NAME" "bigquery.googleapis.com/projects/${PROJECT_ID}/datasets/${DATASET_NAME}" \
        --log-filter="${FILTER}" --use-partitioned-tables --format=json)
        
    WRITER_IDENTITY=$(echo "$SINK_PARAMS" | python3 -c "import sys, json; print(json.load(sys.stdin)['writerIdentity'])")
    
    gcloud projects add-iam-policy-binding "${PROJECT_ID}" --member="$WRITER_IDENTITY" --role="roles/bigquery.dataEditor" > /dev/null
done

echo "[Success] Both GE and NLM cleanly deployed!"
