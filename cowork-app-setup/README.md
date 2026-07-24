# 💻 Gemini Enterprise (GoGo) Cowork App End-to-End Setup & Testing Guide

This guide provides a comprehensive, end-to-end walkthrough for installing, configuring, and verifying the **Gemini Enterprise (GoGo) Desktop App** and enabling native 3P enterprise connectors (Jira, Salesforce, GitHub, Slack, Outlook, Teams, OneDrive, SharePoint, ServiceNow, BigQuery) and Google Workspace MCP tools.

---

## 📋 1. Required Information & Where to Find It

Gather the following parameters before starting:

| Information | Parameter | Where to Find |
| :--- | :--- | :--- |
| **GCP Project ID** | `<PROJECT_ID>` | **GCP Console**: Top navbar dropdown.<br>**Terminal**: `gcloud config get-value project` |
| **GCP Project Number** | `<PROJECT_NUMBER>` | **GCP Console**: Home Dashboard → **Project info** card.<br>**Terminal**: `gcloud projects describe <PROJECT_ID> --format="value(projectNumber)"` |
| **GE Instance Config ID** | `<CONFIG_ID>` | **Web App**: Open [Gemini Enterprise Web App](https://vertexaisearch.cloud.google.com). Look at URL: `https://vertexaisearch.cloud.google.com/home/cid/<CONFIG_ID>`. The UUID following `/cid/` is your Config ID.<br>**GCP Console**: Vertex AI Search & Conversation → Engines → Engine Details → **Copy Config Link**. |
| **GCP Admin Email** | `<ADMIN_EMAIL>` | Account owning project resources & 3P OAuth consents (`gcloud auth list`). |
| **Desktop App Email** | `<APP_EMAIL>` | Account signed into the Electron Desktop App UI (bottom-left corner of app window). |

---

## 🚀 2. Fast Setup (First-Time User Quickstart)

If you are setting this up for the first time, clone/navigate to the setup directory and run the interactive setup tool:

```bash
# 1. Clone the repository (or navigate to the setup folder)
git clone https://github.com/upasana1105/UP_Demos.git
cd UP_Demos/cowork-app-setup

# 2. Run the automated setup tool
python3 setup_cowork_app.py
```

---

## 🛠 3. Manual Step-by-Step E2E Setup

### Step 1: Install Desktop App
1. Extract your GoGo release archive (e.g. `gogo_20260720_213014.zip`).
2. Run `install.sh`:
   ```bash
   cd ~/Downloads/gogo_release_folder
   ./install.sh --skip-verify
   ```

### Step 2: Configure GCP Credentials & IAM Permissions
```bash
# Set active project and ADC quota project
gcloud config set project <PROJECT_ID>
gcloud auth login <ADMIN_EMAIL>
gcloud auth application-default login
gcloud auth application-default set-quota-project <PROJECT_ID>

# Grant Discovery Engine Admin role to the desktop app user
gcloud projects add-iam-policy-binding <PROJECT_ID> \
  --member="user:<APP_EMAIL>" \
  --role="roles/discoveryengine.admin"
```

### Step 3: Deploy & Update Model Configurations (`model_configs.json`)

> **Note:** If using the automated installer (`python3 setup_cowork_app.py`), **Step 3 is handled automatically** — the installer prompts for your Project ID and updates the JSON file.

If configuring manually, update `model_configs.json` to replace `"cloud_project"` and `"default_cloud_project"` with your `<PROJECT_ID>` before deploying to `~/cowork_workspace/.cowork/`:

```bash
# 1. Copy model_configs.json to .cowork workspace
cp ~/Downloads/model_configs.json ~/cowork_workspace/.cowork/model_configs.json

# 2. Update cloud_project and default_cloud_project to your GCP Project ID
python3 -c "
import json
p = '/Users/upasanapati/cowork_workspace/.cowork/model_configs.json'
with open(p, 'r') as f:
    d = json.load(f)
for m in d.get('models', []):
    m['cloud_project'] = '<PROJECT_ID>'
if 'catalog' in d and 'providers' in d['catalog']:
    d['catalog']['providers']['default_cloud_project'] = '<PROJECT_ID>'
with open(p, 'w') as f:
    json.dump(d, f, indent=2)
"
```

### Step 4: Configure Native Discovery Engine (Dynamic Lookup)
Update `discovery_engine.json` with your `configId` and `projectNumber`, deploy to `.cowork`, and remove static connector overrides:

```bash
# 1. Copy template and update configId / projectNumber
cp ~/Downloads/discovery_engine.json ~/cowork_workspace/.cowork/discovery_engine.json

# 2. Remove static connectors file to enable dynamic lookup
rm -f ~/cowork_workspace/.cowork/discovery_engine_connectors.json
```

### Step 5: Launch App
```bash
killall "Gemini Enterprise" 2>/dev/null || true
rm -rf "$HOME/Library/Application Support/ge-desktop-electron/Cache"*
rm -rf "$HOME/Library/Application Support/ge-desktop-electron/Local Storage"
open "/Applications/Gemini Enterprise.app"
```

---

## 🧪 4. End-to-End Verification & Testing

### Test 1: Desktop App UI Login
- Launch **Gemini Enterprise.app**.
- Verify that your `<APP_EMAIL>` is signed in at the bottom-left corner.

### Test 2: Dynamic 3P Connector Tool Verification
- In the left sidebar, click **Connected apps** / **Customize**.
- Verify that **GEMINI ENTERPRISE** dynamically discovers and lists your 3P enterprise connectors (Jira, Salesforce, GitHub, Slack, Outlook, Teams, OneDrive, SharePoint, ServiceNow, BigQuery) with active tool counts.

### Test 3: LLM Chat Inference
- Open a new chat session in the app.
- Send a prompt: *"Explain how Gemini 2.5 Flash works on Vertex AI."*
- Confirm that response stream returns successfully using your Vertex AI quota on `<PROJECT_ID>`.

### Test 4: Enterprise Tool & Search Queries
- Test Federated Search in Chat:
  - *"Search Salesforce for recent accounts and leads."*
  - *"Find Jira tickets assigned to me."*
  - *"Check my Slack channels for recent project updates."*
- Test Workspace Actions in Chat:
  - *"List my Google Calendar events for today."*
  - *"Search my Gmail inbox for recent messages."*
