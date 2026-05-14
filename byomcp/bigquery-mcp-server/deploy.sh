#!/bin/bash

# Configuration
PROJECT_ID=$(gcloud config get-value project)
SERVICE_NAME="bigquery-mcp-server"
REGION="us-central1"

echo "Deploying $SERVICE_NAME to project $PROJECT_ID in region $REGION..."

# Build and Deploy to Cloud Run
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME .
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated

echo "Deployment complete!"
gcloud run services describe $SERVICE_NAME --region $REGION --format='value(status.url)'
