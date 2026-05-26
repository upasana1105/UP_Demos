# Databricks Managed MCP Integration Guide & Proxy Bridge 🚀

This repository contains the comprehensive onboarding guide, codebase, and visual execution flow for connecting your **Databricks Managed MCP Server** directly to **Gemini Enterprise** (Vertex AI Search and Conversation).

---

## 🏗️ Deployment Tracks

### 🔵 Track A: Direct Native OIDC OAuth (Paid Accounts)
Establishes a direct, secure, and zero-infrastructure connection between Gemini Enterprise and Databricks by registering Gemini as a trusted OAuth client.

#### 🔑 Required Databricks Setup & Prerequisites
To configure native OIDC OAuth, verify the following settings in Databricks:
1. **Account Admin Role**: Managing custom OAuth integrations requires **Account Admin** privileges globally at the Account level ([accounts.cloud.databricks.com](https://accounts.cloud.databricks.com)). Workspace Admin rights are not sufficient.
2. **Locate Account ID**: Retrieve your unique Account ID from the bottom-left corner of your Databricks Account Console.
3. **User Identity Mapping**: Ensure your authenticating Google Workspace user emails exactly match your Databricks user accounts (configured via federated SSO/SCIM).
4. **Access Permissions**: Users must hold `Can Use` rights on the target **SQL Warehouse** and `SELECT` rights in **Unity Catalog** for target schemas/tables.

#### Phase 1: Register Custom OAuth App in Databricks
*   **Option 1 (Automated SDK Script)**: Set your `ACCOUNT_ID` and run `create_databricks_oauth.py` (located in the `scratch` folder) to register the client in 5 seconds via browser-based SSO.
*   **Option 2 (Manual Console Setup)**: Navigate to **Settings** ➡️ **App integrations** ➡️ **Add integration** ➡️ **Custom OAuth App** and register with:
    *   **Redirect URIs**: `https://vertexaisearch.cloud.google.com/oauth-redirect`
    *   **Client Type**: Confidential (Generates Client Secret)
    *   **Scopes**: Check `all-apis`, `sql`, `offline_access`, `openid`, and `profile`

#### Phase 2: Register in Gemini Enterprise
Create a new **Custom MCP Server** data store in the Vertex AI Search console using these values:
*   **MCP Server URL**: `https://<workspace-host>/api/2.0/mcp/sql`
*   **Authorization URL**: `https://<workspace-host>/oidc/v1/authorize` (Append `&access_type=offline&prompt=consent`)
*   **Token URL**: `https://<workspace-host>/oidc/v1/token`
*   **Scopes**: `all-apis offline_access openid profile`

---

### 🟢 Track B: Fallback Cloud Run Proxy Bridge (Trial & Free Accounts)
A lightweight, secure proxy bridge that mocks the OAuth 2.0 handshake and automatically injects your workspace **Personal Access Token (PAT)**. Ideal for environments with restricted account administration or trials.

#### 📁 Project Codebase Files
The bridge is fully implemented as standalone files in this directory:
*   [bridge.py](bridge.py): FastAPI proxy server intercepting OAuth handshakes and dynamically injecting `readOnlyHint: true` metadata for background, prompt-free query execution.
*   [Dockerfile](Dockerfile): Docker container build file optimized for serverless execution.
*   [requirements.txt](requirements.txt): Package dependencies.
*   [run_bridge.sh](run_bridge.sh): Automated terminal launcher supporting local execution and immediate GCP Cloud Run deployment.

#### 🚀 Quick Deployment & Setup
1. **Deploy to Cloud Run**: Run `./run_bridge.sh` and select **Option 2** (Production) to deploy as a private service (`--no-allow-unauthenticated`).
2. **IAM Invoker Bindings**: Authorize your developer account and Vertex AI discovery engine service account:
   ```bash
   # Grant invoker to Vertex AI Search Service Agent
   PROJECT_NUMBER=$(gcloud projects describe YOUR_GCP_PROJECT_ID --format="value(projectNumber)")
   gcloud run services add-iam-policy-binding databricks-mcp-bridge \
       --region us-central1 \
       --member="serviceAccount:service-${PROJECT_NUMBER}@gcp-sa-discoveryengine.iam.gserviceaccount.com" \
       --role="roles/run.invoker"
   ```
3. **Gemini Registration**: Create a Custom MCP data store pointing to the bridge endpoints (`https://<bridge-host>/mcp/sql`), using `mock_client`/`mock_secret` as credentials.

---

## 🧪 Verification & Live Chat Charting

Once successfully connected via either Track A or Track B, standard users can query catalogs and instruct Gemini 3.5 to write and execute Python code (via secure Code Interpreter) to plot high-resolution graphics natively in the chat pane.

### 📸 Visual Integration Flow & Sample Outputs

````carousel
![1. Enable Connectors Panel](/Users/upasanapati/shrinkAI experiment/Antigravity_Experiments/UP_Demos/byomcp/databricks-mcp-bridge/screenshots/connector_panel.png)
<!-- slide -->
![2. Prompt Execution State](/Users/upasanapati/shrinkAI experiment/Antigravity_Experiments/UP_Demos/byomcp/databricks-mcp-bridge/screenshots/thinking_state.png)
<!-- slide -->
![3. Beautiful Seaborn Chart Response](/Users/upasanapati/shrinkAI experiment/Antigravity_Experiments/UP_Demos/byomcp/databricks-mcp-bridge/screenshots/seaborn_chart.png)
````
