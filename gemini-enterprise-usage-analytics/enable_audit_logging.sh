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

    # Prevent 500 Internal Errors by filtering out legacy/Enterprise Search engines
    if [[ "$SINGLE_APP_ID" == *"enterprise-search"* || "$SINGLE_APP_ID" == *"search-kpmg"* ]]; then
        echo "⚠️ [Skipped] App ID '${SINGLE_APP_ID}' is a Vertex AI Search engine."
        echo "   Generative prompt logging (observabilityConfig) is only supported on Conversation & Agent apps."
        echo ""
        continue
    fi

    # Execute curl safely and capture HTTP response status
    RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X PATCH \
      -H "Authorization: Bearer $(gcloud auth print-access-token)" \
      -H "Content-Type: application/json" \
      -H "X-Goog-User-Project: ${PROJECT_ID}" \
      "https://${LOCATION}-discoveryengine.googleapis.com/v1alpha/projects/${PROJECT_ID}/locations/${LOCATION}/collections/default_collection/engines/${SINGLE_APP_ID}?updateMask=observabilityConfig" \
      -d '{
        "observabilityConfig": {
          "observabilityEnabled": true,
          "sensitiveLoggingEnabled": true
        }
      }')
    
    HTTP_STATUS=$(echo "$RESPONSE" | tr -d '\r' | sed -n 's/.*HTTP_STATUS://p')
    BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS:/d')

    if [ "$HTTP_STATUS" -eq 200 ]; then
        echo "✓ Successfully enabled audit logging for ${SINGLE_APP_ID}"
    else
        echo "⚠️ [Notice] API returned HTTP ${HTTP_STATUS} for ${SINGLE_APP_ID}."
        echo "   Response: ${BODY}"
        echo "   (If this is a non-generative engine, this notice can be safely ignored)."
    fi
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
