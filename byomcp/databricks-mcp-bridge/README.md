# Databricks Managed MCP Integration Guide & Proxy Bridge 🚀

This repository contains the comprehensive onboarding guide and codebase for connecting your **Databricks Managed MCP Server** directly to **Gemini Enterprise** (Vertex AI Search and Conversation).

---

## 🔵 Track A: Direct Native OIDC OAuth (Paid Accounts)

This track establishes a direct, secure, and zero-infrastructure connection between Gemini Enterprise and Databricks by registering Gemini as a trusted OAuth client.

### 🔑 Required Databricks Prerequisites & Roles
To successfully set up and authorize using native OIDC OAuth, the following administrative settings must be configured inside Databricks:

1. **Account Admin Privileges**:
   - Creating and managing custom OAuth app integrations requires **Account Admin** role permissions. 
   - **Workspace Admin** permissions are **not sufficient**, because OAuth app registration is configured globally at the Account level (via `accounts.cloud.databricks.com`), rather than within individual workspaces.

2. **Locate Your Account ID**:
   - You will need your Databricks Account ID to register the app.
   - Log in to the **Databricks Account Console** at [accounts.cloud.databricks.com](https://accounts.cloud.databricks.com) and locate the Account ID in the **bottom-left corner** of the sidebar navigation.

3. **User Provisioning & Federated Identity (SSO)**:
   - Databricks OAuth relies on identity delegation. The email address of the user authenticating via Gemini Enterprise **must exactly match** a user record inside your Databricks account.
   - Ensure your enterprise identity provider (IdP) SSO (such as Okta, Azure AD, or Google Workspace) is set up to provision/sync your users to both Google Cloud (Gemini Enterprise) and Databricks.

4. **Target SQL Compute & Unity Catalog Access Control**:
   - Under standard OAuth authorization, the user's delegated token inherits their specific permissions in Databricks.
   - Ensure target users are granted `Can Use` privileges on the specific **SQL Warehouse** compute that processes queries.
   - Ensure users are granted `SELECT` (and other DDL/DML as needed) permissions under **Unity Catalog** for the schemas, catalogs, and tables they will ask Gemini to query.

### Phase 1: Register the Custom OAuth App in Databricks

#### Option 1: Automated via Python SDK (Fastest & Google SSO Friendly)
If your account uses Google Federation SSO (Gmail) and you have Account Admin access, run the registration script (`create_databricks_oauth.py` in the `scratch` directory) locally on your machine. It triggers browser-based OAuth (User-to-Machine) to complete registration in 5 seconds.

```python
import sys
from databricks.sdk import AccountClient

ACCOUNTS_HOST = "https://accounts.cloud.databricks.com"
ACCOUNT_ID = "YOUR_DATABRICKS_ACCOUNT_ID"  # e.g., 2130c768-f030-4035-85db-736c897785ec

print("=========================================================")
print("🚀 Registering Databricks OAuth App via Google SSO")
print("=========================================================")

try:
    client = AccountClient(
        host=ACCOUNTS_HOST,
        account_id=ACCOUNT_ID,
        auth_type="oauth-u2m"
    )
    print("\nVerifying connection & admin permissions...")
    list(client.custom_app_integration.list())
except Exception as e:
    print(f"❌ Authentication failed: {e}")
    sys.exit(1)

print("Registering Custom OAuth Application 'Gemini Enterprise Databricks MCP'...")
try:
    app = client.custom_app_integration.create(
        name="Gemini Enterprise Databricks MCP",
        redirect_urls=["https://vertexaisearch.cloud.google.com/oauth-redirect"],
        scopes=["all-apis", "sql", "offline_access", "openid", "profile"],
        confidential=True
    )
    print("\n🎉 OAuth Application Registered successfully!")
    print(f"Client ID: {app.client_id}")
    print(f"Client Secret: {app.client_secret}")
except Exception as e:
    print(f"\n❌ Error registering OAuth Application: {e}")
    sys.exit(1)
```

#### Option 2: Visual Setup via Account Console
If you prefer using the UI, have an Account Admin execute these steps:
1. Log in to the **Databricks Accounts Console** at [accounts.cloud.databricks.com](https://accounts.cloud.databricks.com).
2. Go to **Settings** ➡️ **App integrations** ➡️ **Add integration**.
3. Select **Custom OAuth App**.
4. Configure the integration settings:
   *   **App Name:** `Gemini Enterprise Databricks MCP`
   *   **Redirect URIs:** Add the exact Gemini redirect URI: `https://vertexaisearch.cloud.google.com/oauth-redirect`
   *   **Client Type:** Confidential (Keep the "Generate a client secret" box checked).
   *   **Scopes:** Check `all-apis`, `sql`, `offline_access`, `openid`, and `profile`.
5. Click **Save** and copy the generated **Client ID** and **Client Secret**.

### Phase 2: Register the Data Store in Gemini Enterprise

1. In the Google Cloud Console, go to **Gemini Enterprise** (Vertex AI Search and Conversation) ➡️ **Data stores** ➡️ **Create data store**.
2. Select **Custom MCP Server**.
3. Fill in the connection form using your direct workspace endpoints:

   | Connection Field | Value to Enter |
   | :--- | :--- |
   | **MCP Server URL \*** | `https://<your-workspace-host>/api/2.0/mcp/sql` |
   | **Authorization URL \*** | `https://<your-workspace-host>/oidc/v1/authorize` |
   | **Authorization URL Parameters** | `&access_type=offline&prompt=consent` *(Provides long-lived background refresh tokens)* |
   | **Token URL \*** | `https://<your-workspace-host>/oidc/v1/token` |
   | **Client ID \*** | *(Your generated Client ID)* |
   | **Client Secret \*** | *(Your generated Client Secret)* |
   | **Scopes** | `all-apis offline_access openid profile` |

4. Click **Login** to authenticate via Google SSO and save the connection.
5. In the **Advanced Options** screen, supply the following guidelines to instruct the AI reasoning engine:
   *   **MCP Server Description:**
       ```text
       Direct, secure Databricks SQL MCP server providing access to Unity Catalog tables and schemas. Use this server when users ask to query database metrics, search tables, explore columns, or execute analytical workflows.
       ```
   *   **MCP Agent Instructions:**
       ```text
       You are an expert enterprise data analyst connected to Databricks. Follow these rules:
       1. Safety: Use 'execute_sql_read_only' for SELECT, SHOW, and DESCRIBE statements. This bypasses approval prompts and runs in the background. Use 'execute_sql' ONLY for write-based operations.
       2. Summarization: Present all SQL outcomes, row counts, and metrics in beautifully formatted markdown tables.
       ```

---

## 🟢 Track B: Fallback Cloud Run Proxy Bridge (Trial & Free Accounts)

If your Trial or Community account restricts access to Account Console settings or browser-based Account OAuth U2M login, this fallback track allows you to deploy a lightweight proxy to Cloud Run in under 2 minutes. 

The bridge mocks the OAuth 2.0 handshake for Gemini Enterprise and automatically injects your workspace **Personal Access Token (PAT)** in the background.

### Overview

The bridge performs three critical roles:
1. **Mock OAuth 2.0 Protocol**: Mimics the OAuth authorization and token exchange endpoints expected by Gemini Enterprise's Custom MCP connection profile.
2. **Authentication & Token Injection**: Automatically intercepts and forwards all incoming MCP JSON-RPC requests to your private Databricks Workspace MCP endpoint, injecting your workspace **Personal Access Token (PAT)** seamlessly.
3. **Popup-Free Read Execution**: Intercepts the `tools/list` response and automatically injects `readOnlyHint: true` annotations for all standard database operations, allowing seamless background execution without disruptive client confirmation dialogues.

### Project Structure

```text
databricks-mcp-bridge/
├── bridge.py             # The FastAPI proxy bridge application
├── Dockerfile            # Multi-stage build for Cloud Run deployment
├── requirements.txt      # Python dependency definitions
├── run_bridge.sh         # Terminal-driven automated runner & deployment script
├── .env.example          # Template for local environment variables
└── README.md             # Project documentation
```

### Configuration & Environment Variables

The bridge loads configuration from environment variables. For local development, you can specify these inside a `.env` file:

| Variable | Description | Example |
| :--- | :--- | :--- |
| `DATABRICKS_PAT` | Your Databricks Workspace Personal Access Token (PAT) | `dapiXXXXXX` |
| `DATABRICKS_WORKSPACE` | The target workspace URL | `https://dbc-XXXX.cloud.databricks.com` |

### Local Development Setup

#### 1. Install Dependencies & Start Server
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

### Deploying to GCP Cloud Run

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

#### Authorize Vertex AI Invoker Permissions
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

#### Register the Data Store in Gemini Enterprise

Configure your Custom MCP Datastore in the Vertex AI Search and Conversation console:

| Form Field | For Databricks SQL | For Genie Space (NL2SQL) |
| :--- | :--- | :--- |
| **MCP Server URL** | `https://<bridge-host>/mcp/sql` | `https://<bridge-host>/mcp/genie/{space_id}` |
| **Authorization URL** | `https://<bridge-host>/mcp/sql/auth` | `https://<bridge-host>/mcp/genie/{space_id}/auth` |
| **Auth parameters** | `&access_type=offline&prompt=consent` | `&access_type=offline&prompt=consent` |
| **Token URL** | `https://<bridge-host>/mcp/sql/token` | `https://<bridge-host>/mcp/genie/{space_id}/token` |
| **Client ID / Secret** | `mock_client` / `mock_secret` | `mock_client` / `mock_secret` |
| **Scopes** | `sql` | `genie` |

---

## 🧪 Verification & Native Chat Charting (Gemini 3.5)

Once successfully connected via Track A or Track B, open your Gemini Enterprise chat interface to run live database queries and visually plot the results natively.

### 1. Read-Only Metadata Verification (Popup-Free)
Confirm that read-only operations execute invisibly in the background without any prompt confirmation panels:
> **"List all available tables inside our Databricks workspace catalog."**

### 2. Native Python Code Execution Charts (Gemini 3.5)
Since Gemini 3.5 contains a native secure Python environment (Code Interpreter), ask it to run queries on your Databricks SQL tables and plot actual high-resolution graphic images:

#### Top-Selling Pastries (Seaborn Bar Chart)
> **"Query our Bakehouse SQL datastore to find the top 5 best-selling products in the 'Pastry' category by total sales revenue. Use your native Python code environment to generate a beautiful horizontal Seaborn bar chart representing this breakdown, with customized pastel colors and labeled data values on the bars."**

#### Historical Growth Trend (Matplotlib Line Chart)
> **"Find the monthly total sales revenue over the last year from our Databricks database. Plot this growth timeline as a high-resolution line chart using your Python interpreter, with individual data markers and a shaded grid."**

### 📸 Visual Onboarding & Charting Walkthrough

````carousel
![1. Enable Connectors Panel](/Users/upasanapati/shrinkAI experiment/Antigravity_Experiments/UP_Demos/byomcp/databricks-mcp-bridge/screenshots/connector_panel.png)
<!-- slide -->
![2. Prompt Execution State](/Users/upasanapati/shrinkAI experiment/Antigravity_Experiments/UP_Demos/byomcp/databricks-mcp-bridge/screenshots/thinking_state.png)
<!-- slide -->
![3. Beautiful Seaborn Chart Response](/Users/upasanapati/shrinkAI experiment/Antigravity_Experiments/UP_Demos/byomcp/databricks-mcp-bridge/screenshots/seaborn_chart.png)
````

