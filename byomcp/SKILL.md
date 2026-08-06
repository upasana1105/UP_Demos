---
name: ge-byomcp-datastore
description: >
  Creates and provisions Bring-Your-Own-MCP (BYOMCP / custom_mcp) datastores in Gemini Enterprise
  / Discovery Engine programmatically across fresh and existing GCP projects.
---

# Gemini Enterprise BYOMCP Datastore Creator

This skill provides instructions, architecture requirements, and a 1-click end-to-end provisioner script for creating Bring-Your-Own-MCP (`custom_mcp`) data connectors and datastores in Gemini Enterprise (Discovery Engine) on **both fresh and existing GCP projects**.

---

## 1-Click Turnkey Automated Provisioner

Location: [`scripts/provision_end_to_end_byomcp.py`](file:///google/src/cloud/upasanapati/implement_bq_mcp_skill/configs/users/upasanapati/_agents/skills/ge_byomcp_datastore/scripts/provision_end_to_end_byomcp.py)

### Automated 5-Step Workflow (Fresh & Existing Projects):

1. **Custom MCP Org Policy Override**:  
   Disables enforcement of `constraints/discoveryengine.managed.disableCustomMcpServerConnector` (`enforce: false`) at the project level. Skipped automatically if already disabled or if the user lacks org policy admin permissions.
2. **API Auto-Enablement**:  
   Enables `discoveryengine.googleapis.com` and `secretmanager.googleapis.com` on fresh projects via `gcloud services enable`.
3. **Secret Manager Credential Storage**:  
   Creates secrets `bq_mcp_client_id` and `bq_mcp_client_secret` in GCP Secret Manager to securely store OAuth Web client credentials.
4. **DataConnector Provisioning & Fallback**:  
   Sends a `SetUpDataConnector` REST API request with `"entities": [{"entityName": "mcp_data"}]` to create the datastore and bind the `mcp_data` child DataStore. Fallbacks gracefully to `UpdateDataConnector` (PATCH) if the collection or connector already exists.
5. **Status Verification & Console Link**:  
   Polls the connector status to verify `Connector State` and `Action State` are **`ACTIVE`**, and outputs the direct GCP Console URL.

---

## How OAuth Client & Secret Manager Automation Work

### 1. Secret Manager Automation
To keep credentials secure and prevent secrets from leaking into shell logs or process strings:
- **API Auto-Enablement**: The provisioner script automatically enables `secretmanager.googleapis.com`.
- **Automatic Secret Container Creation**: Executes `gcloud secrets create bq_mcp_client_id --project=PROJECT_ID --replication-policy=automatic` (idempotent).
- **Secure Standard-Input Ingestion**: Adds secret versions using stdin (`--data-file=-`) so client secrets are never exposed in terminal command strings:
  ```python
  cmd_add = ["gcloud", "secrets", "versions", "add", "bq_mcp_client_secret", f"--project={project}", "--data-file=-"]
  subprocess.run(cmd_add, input=client_secret_value, capture_output=True, text=True)
  ```

### 2. OAuth 2.0 Client Automation & Binding
- **3-Legged Web OAuth Requirement**: `accounts.google.com` sign-in requires a registered Google Cloud Console OAuth 2.0 **Web Application** Client ID ending in `.apps.googleusercontent.com`.
- **Redirect URI Setup**: The OAuth client MUST include the official Vertex AI Search redirect URI:  
  `https://vertexaisearch.cloud.google.com/oauth-redirect`
- **Automatic Action Configuration Payload**: The script maps the OAuth Web Client ID and secret into Gemini Enterprise's Business Application Platform (BAP) connection engine under `actionConfig.actionParams`:
  - `auth_uri`: `https://accounts.google.com/o/oauth2/v2/auth`
  - `token_uri`: `https://oauth2.googleapis.com/token`
  - `mcp_server_source`: `BYO_MCP`
  - `scopes`: `https://www.googleapis.com/auth/bigquery`

---

## Command Examples

### 1. Provisioning a Fresh GCP Project (e.g. `gemini-enterprise-prod-wif`)

```bash
python3 configs/users/upasanapati/_agents/skills/ge_byomcp_datastore/scripts/provision_end_to_end_byomcp.py \
  --project="gemini-enterprise-prod-wif" \
  --collection_id="bigquery_mcp_datastore" \
  --collection_display_name="BigQuery MCP Server" \
  --instance_uri="https://bigquery.googleapis.com/mcp" \
  --client_id="YOUR_OAUTH_CLIENT_ID.apps.googleusercontent.com" \
  --client_secret="YOUR_OAUTH_CLIENT_SECRET"
```

### 2. Updating an Existing GCP Project / Collection (e.g. `uppdemos`)

```bash
python3 configs/users/upasanapati/_agents/skills/ge_byomcp_datastore/scripts/provision_end_to_end_byomcp.py \
  --project="uppdemos" \
  --collection_id="bq-managed-mcp-v2_1775150801064" \
  --instance_uri="https://bigquery.googleapis.com/mcp" \
  --client_id="YOUR_OAUTH_CLIENT_ID.apps.googleusercontent.com" \
  --client_secret="YOUR_OAUTH_CLIENT_SECRET"
```

---

## Technical Details & API Endpoints

- **SetUpDataConnector Endpoint** (POST):
  `https://discoveryengine.googleapis.com/v1/projects/{project}/locations/{location}:setUpDataConnector`
- **UpdateDataConnector Endpoint** (PATCH):
  `https://discoveryengine.googleapis.com/v1/projects/{project}/locations/{location}/collections/{collection_id}/dataConnector?updateMask=actionConfig`
- **Required Action Configuration Payload**:
  ```json
  {
    "dataSource": "custom_mcp",
    "dataSourceVersion": 1.0,
    "connectorModes": ["FEDERATED", "ACTIONS"],
    "entities": [{"entityName": "mcp_data"}],
    "actionConfig": {
      "isActionConfigured": true,
      "createBapConnection": true,
      "actionParams": {
        "instance_uri": "https://bigquery.googleapis.com/mcp",
        "mcp_server_source": "BYO_MCP",
        "auth_uri": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": "<CLIENT_ID>.apps.googleusercontent.com",
        "client_secret": "<CLIENT_SECRET>",
        "scopes": "https://www.googleapis.com/auth/bigquery"
      }
    }
  }
  ```
