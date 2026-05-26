#!/bin/bash

# Set script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================================="
echo "🚀 Databricks Managed MCP Proxy Bridge"
echo "========================================================="

# Print usage options
echo "Choose an option:"
echo "1) Run locally (for testing)"
echo "2) Deploy to GCP Cloud Run (production)"
read -p "Enter option [1-2]: " OPTION

if [ "$OPTION" == "1" ]; then
    echo "Configuring local python environment..."
    # Check if virtual environment exists inside bridge folder, otherwise create it
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    source venv/bin/activate
    pip install -r requirements.txt --index-url https://pypi.org/simple
    
    echo "Starting Local Bridge Server on port 8080..."
    uvicorn bridge:app --host 0.0.0.0 --port 8080 --reload
    
elif [ "$OPTION" == "2" ]; then
    echo "Deploying proxy bridge to GCP Cloud Run..."
    
    # Verify gcloud CLI is logged in
    gcloud auth list
    
    # Ask for GCP Project ID if not set
    CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null)
    read -p "Enter your GCP Project ID [current: $CURRENT_PROJECT]: " PROJECT_ID
    PROJECT_ID=${PROJECT_ID:-$CURRENT_PROJECT}
    
    if [ -z "$PROJECT_ID" ]; then
        echo "Error: GCP Project ID is required."
        exit 1
    fi
    
    gcloud config set project "$PROJECT_ID"
    
    echo "Running gcloud run deploy..."
    gcloud run deploy databricks-mcp-bridge \
        --source . \
        --port 8080 \
        --allow-unauthenticated \
        --region us-central1 \
        --project "$PROJECT_ID"
        
    echo "Deployment complete! Copy the Service URL and use it inside your Gemini Enterprise MCP connection profile."
else
    echo "Invalid option."
    exit 1
fi
