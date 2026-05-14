#!/bin/bash

# Configuration
SERVICE_NAME="snowflake-mcp-proxy"
REGION="us-central1"
PROJECT_ID=$(gcloud config get-value project)

# Print current project for verification
echo "Using GCP Project: $PROJECT_ID"

if [ -z "$PROJECT_ID" ]; then
  echo "Error: No active GCP project configured in your gcloud CLI."
  echo "Please run: gcloud config set project <your-project-id>"
  exit 1
fi

# Build image using Cloud Build (No local Docker daemon needed)
echo "🚀 Building container image using Cloud Build..."
gcloud builds submit --tag "gcr.io/$PROJECT_ID/$SERVICE_NAME" .

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
# We will use variables for the secrets to make it safe and reusable!
gcloud run deploy "$SERVICE_NAME" \
  --image "gcr.io/$PROJECT_ID/$SERVICE_NAME" \
  --platform managed \
  --region "$REGION" \
  --allow-unauthenticated \
  --set-env-vars="SNOWFLAKE_ACCOUNT=dikgrbu-tv54598,SNOWFLAKE_USER=upasanapati,SNOWFLAKE_PASSWORD=Femdonkey@12345,SNOWFLAKE_WAREHOUSE=COMPUTE_WH,SNOWFLAKE_DATABASE=SNOWFLAKE_SAMPLE_DATA,SNOWFLAKE_SCHEMA=TPCH_SF1"

echo "✅ Success! Get the 'Service URL' from the output above and use it in Vertex AI!"
