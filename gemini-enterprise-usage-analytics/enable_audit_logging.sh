#!/bin/bash
# ==============================================================================
# Script: enable_audit_logging.sh
# Description: Enables Usage Audit Logging and sensitive request/response logs
#              globally for Gemini Enterprise and NotebookLM via Discovery Engine API.
# ==============================================================================

set -e

PROJECT_ID="${PROJECT_ID:-uppdemos}"
APP_ID="${APP_ID:-gemini-enterprise-gm_1771086459519}"
LOCATION="${LOCATION:-global}"

# ------------------------------------------------------------------------------
# 1. Enable Usage Audit Logging for Gemini Enterprise
# ------------------------------------------------------------------------------
IFS=',' read -ra APP_ID_ARRAY <<< "$APP_ID"
for SINGLE_APP_ID in "${APP_ID_ARRAY[@]}"; do
    SINGLE_APP_ID=$(echo "$SINGLE_APP_ID" | xargs)
    if [ -z "$SINGLE_APP_ID" ] || [ "$SINGLE_APP_ID" = "your_app_id" ]; then
        continue
    fi

    echo "======================================================================"
    echo "Enabling Usage Audit Logging for Gemini Enterprise (App: ${SINGLE_APP_ID})..."
    echo "======================================================================"

    curl -X PATCH -H "Authorization: Bearer $(gcloud auth print-access-token)" \
    -H "Content-Type: application/json" \
    -H "X-Goog-User-Project: ${PROJECT_ID}" \
    "https://${LOCATION}-discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_ID}/locations/${LOCATION}/collections/default_collection/engines/${SINGLE_APP_ID}?updateMask=observabilityConfig" \
    -d '{
      "observabilityConfig": {
        "observabilityEnabled": true,
        "sensitiveLoggingEnabled": true
      }
    }'
    echo ""
done

# ------------------------------------------------------------------------------
# 2. Enable Usage Audit Logging for NotebookLM Enterprise
# ------------------------------------------------------------------------------
if [ "$PROJECT_ID" != "your_project_id" ]; then
    echo "======================================================================"
    echo "Enabling Usage Audit Logging for NotebookLM Enterprise (Project: ${PROJECT_ID})..."
    echo "======================================================================"

    curl -X PATCH -H "Authorization: Bearer $(gcloud auth print-access-token)" \
    -H "Content-Type: application/json" \
    -H "X-Goog-User-Project: ${PROJECT_ID}" \
    "https://${LOCATION}-discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_ID}?updateMask=customerProvidedConfig.notebooklmConfig.observabilityConfig" \
    -d '{
      "customerProvidedConfig": {
        "notebooklmConfig": {
          "observabilityConfig": {
            "observabilityEnabled": true,
            "sensitiveLoggingEnabled": true
          }
        }
      }
    }'
    echo ""
fi

echo "✅ Audit Logging Configuration Successfully Completed!"
