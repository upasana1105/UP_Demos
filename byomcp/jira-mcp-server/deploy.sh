#!/bin/bash

# Configuration
SERVICE_NAME="jira-mcp-server"
REGION="us-central1" # You can change this to your preferred region

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
  --set-env-vars "ATLASSIAN_BASE_URL=$ATLASSIAN_BASE_URL,ATLASSIAN_EMAIL=$ATLASSIAN_EMAIL,ATLASSIAN_API_TOKEN=$ATLASSIAN_API_TOKEN"

echo "✅ Deployment complete!"
