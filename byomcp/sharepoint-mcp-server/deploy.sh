#!/bin/bash

# Configuration
SERVICE_NAME="sharepoint-mcp-server"
REGION="us-central1"

# Load environment variables from .env if it exists
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

echo "🚀 Starting deployment of $SERVICE_NAME to Cloud Run..."

# Build and deploy
gcloud run deploy "$SERVICE_NAME" \
  --source . \
  --region "$REGION" \
  --project "uppdemos" \
  --allow-unauthenticated \
  --port 3000 \
  --set-env-vars "MS_GRAPH_TENANT_ID=$MS_GRAPH_TENANT_ID,MS_GRAPH_CLIENT_ID=$MS_GRAPH_CLIENT_ID,MS_GRAPH_CLIENT_SECRET=$MS_GRAPH_CLIENT_SECRET"

echo "✅ Deployment complete!"
