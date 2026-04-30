#!/bin/bash
# ==============================================================================
# Interactive Analytics Pipeline Runner
# ==============================================================================

echo "======================================================================"
echo "🌟 Gemini & NotebookLM Analytics Pipeline Wizard"
echo "======================================================================"

# 1. Prompt for environment variables
read -p "Enter Target Google Cloud PROJECT_ID: " PROMPT_PROJECT_ID
read -p "Enter Gemini APP_ID(s) (comma-separated for multiple, e.g., app_1,app_2): " PROMPT_APP_ID
read -p "Enter BigQuery Storage Location (e.g., US): " PROMPT_BQ_LOCATION
read -p "Enter Gemini Raw Dataset Prefix (default: ge_raw_logs_): " PROMPT_GE_PREFIX
read -p "Enter NotebookLM Raw Dataset Prefix (default: nlm_raw_logs_): " PROMPT_NLM_PREFIX

# Apply Defaults if left blank
export PROJECT_ID="${PROMPT_PROJECT_ID:-uppdemos}"
export APP_ID="${PROMPT_APP_ID:-gemini-enterprise-gm_1771086459519}"
export BQ_LOCATION="${PROMPT_BQ_LOCATION:-US}"
export GE_DATASET_PREFIX="${PROMPT_GE_PREFIX:-ge_raw_logs_}"
export NLM_DATASET_PREFIX="${PROMPT_NLM_PREFIX:-nlm_raw_logs_}"
export GE_TRANSFORMED_DATASET="ge_transformed"
export NLM_TRANSFORMED_DATASET="nlm_transformed"

echo ""
echo "======================================================================"
echo "📋 ARCHITECTURE PREVIEW"
echo "======================================================================"
echo "The following schemas will be automatically created in GCP:"
echo ""
echo "--- GEMINI ENTERPRISE (Total 14 Methods) ---"
echo "Dataset Sample: ${PROJECT_ID}:${GE_DATASET_PREFIX}search"
echo "Dataset Sample: ${PROJECT_ID}:${GE_DATASET_PREFIX}streamassist"
echo "Sink Names:     ge_raw_logs_search, etc."
echo ""
echo "--- NOTEBOOKLM ENTERPRISE (Total 6 Methods) ---"
echo "Dataset Sample: ${PROJECT_ID}:${NLM_DATASET_PREFIX}createnotebook"
echo "Dataset Sample: ${PROJECT_ID}:${NLM_DATASET_PREFIX}interactsources"
echo ""
echo "--- TRANSFORMED CONSOLIDATION VIEWS ---"
echo "View Name: ${PROJECT_ID}:${GE_TRANSFORMED_DATASET}.ge_logs"
echo "View Name: ${PROJECT_ID}:${NLM_TRANSFORMED_DATASET}.nlm_logs"
echo "======================================================================"

read -p "Are you perfectly happy with these dataset names? (y/N): " CONFIRM
if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo "[Aborted] Execution stopped safely. Run again to correct names!"
    exit 0
fi

echo ""
echo "🚀 Deploying infrastructure sequentially..."
echo ""

chmod +x setup_user_logs_raw.sh setup_transformed_views.sh ../enable_audit_logging.sh

echo "[Step 0] Enabling Global Usage Audit Logging..."
../enable_audit_logging.sh

echo ""
echo "[Step 1] Deploying Raw Isolated Pipelines..."
./setup_user_logs_raw.sh

echo ""
echo "[Step 2] Deploying Transformed Flattened Views..."
./setup_transformed_views.sh

echo ""
echo "Creating summary.txt..."
cat <<EOF > summary.txt
==============================================================================
DEPLOYMENT SUMMARY
==============================================================================
Date:          $(date)
Project ID:    ${PROJECT_ID}
BQ Location:   ${BQ_LOCATION}

GE Datasets:   ${GE_DATASET_PREFIX}*
NLM Datasets:  ${NLM_DATASET_PREFIX}*
Compiled:      ${GE_TRANSFORMED_DATASET}.ge_logs, ${NLM_TRANSFORMED_DATASET}.nlm_logs
==============================================================================
EOF

echo "✨ Success! Saved overview in summary.txt."
