# Databricks Managed MCP Bridge 🚀

This is a lightweight, high-performance FastAPI proxy bridge designed to connect **Databricks Managed MCP Servers** directly with **Gemini Enterprise** (Vertex AI Search and Conversation).

## Overview

The bridge facilitates rapid integration for environments where direct, native account-level OIDC OAuth setup is not feasible (e.g., restricted administrative accounts, trial accounts, or Community Edition setups). It performs three critical roles:

1. **Mock OAuth 2.0 Protocol**: Mimics the OAuth authorization and token exchange endpoints expected by Gemini Enterprise's Custom MCP connection profile.
2. **Authentication & Token Injection**: Automatically intercepts and forwards all incoming MCP JSON-RPC requests to your private Databricks Workspace MCP endpoint, injecting your workspace **Personal Access Token (PAT)** seamlessly.
3. **Popup-Free Read Execution**: Intercepts the `tools/list` response and automatically injects `readOnlyHint: true` annotations for all standard database operations, allowing seamless background execution without disruptive client confirmation dialogues.

---

## Project Structure

```text
databricks-mcp-bridge/
├── bridge.py             # The FastAPI proxy bridge application
├── Dockerfile            # Multi-stage build for Cloud Run deployment
├── requirements.txt      # Python dependency definitions
├── run_bridge.sh         # Terminal-driven automated runner & deployment script
├── .env.example          # Template for local environment variables
└── README.md             # Project documentation
```

---

## Configuration & Environment Variables

The bridge loads configuration from environment variables. For local development, you can specify these inside a `.env` file:

| Variable | Description | Example |
| :--- | :--- | :--- |
| `DATABRICKS_PAT` | Your Databricks Workspace Personal Access Token (PAT) | `dapiXXXXXX` |
| `DATABRICKS_WORKSPACE` | The target workspace URL | `https://dbc-XXXX.cloud.databricks.com` |

---

## Local Development Setup

### 1. Install Dependencies & Start Server
Run the automated setup bash script and choose **Option 1**:
```bash
chmod +x run_bridge.sh
./run_bridge.sh
```
*Alternatively, to set it up manually:*
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn bridge:app --host 0.0.0.0 --port 8080 --reload
```

---

## Deploying to GCP Cloud Run

To deploy the container to Google Cloud Run, use the automated setup bash script and choose **Option 2**:
```bash
./run_bridge.sh
```

*Or deploy manually using `gcloud`:*
```bash
gcloud run deploy databricks-mcp-bridge \
    --source . \
    --port 8080 \
    --region us-central1 \
    --set-env-vars="DATABRICKS_PAT=dapiXXXXXX,DATABRICKS_WORKSPACE=https://dbc-XXXX.cloud.databricks.com" \
    --no-allow-unauthenticated
```

> [!IMPORTANT]
> Using `--no-allow-unauthenticated` ensures your bridge is locked down from public internet traffic. 

### Authorize Vertex AI Invoker Permissions
Provide invoker rights to your developer user and the Vertex AI Discovery Engine service account:
```bash
PROJECT_NUMBER=$(gcloud projects describe YOUR_GCP_PROJECT_ID --format="value(projectNumber)")

# Grant invoker to your user
gcloud run services add-iam-policy-binding databricks-mcp-bridge \
    --region us-central1 \
    --member="user:your-email@company.com" \
    --role="roles/run.invoker"
    
# Grant invoker to Vertex AI Search Service Agent
gcloud run services add-iam-policy-binding databricks-mcp-bridge \
    --region us-central1 \
    --member="serviceAccount:service-${PROJECT_NUMBER}@gcp-sa-discoveryengine.iam.gserviceaccount.com" \
    --role="roles/run.invoker"
```

---

## Connecting with Gemini Enterprise

In the **Vertex AI Search and Conversation** console, configure your Custom MCP Datastore:

| Field | Value |
| :--- | :--- |
| **MCP Server URL** | `https://<bridge-host>/mcp/sql` |
| **Authorization URL** | `https://<bridge-host>/mcp/sql/auth` |
| **Token URL** | `https://<bridge-host>/mcp/sql/token` |
| **Client ID** | `mock_client` |
| **Client Secret** | `mock_secret` |
| **Scopes** | `sql` |
