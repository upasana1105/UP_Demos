# 🛠 `setup_cowork_app.py` Generalized Setup Guide

`setup_cowork_app.py` is an automated setup and patching tool for the **Cowork Desktop App (Gemini Enterprise / GoGo)**. It automates environment configuration, workspace setup, dynamic Discovery Engine 3P connector discovery, and source code patching.

---

## 📋 Required Information & Where to Find It

Before running the setup tool, gather the following 5 parameters for your GCP environment:

| Parameter | Command Flag | Description | Where to Find |
| :--- | :--- | :--- | :--- |
| **GCP Project ID** | `--project` | The GCP project ID hosting Vertex AI and Discovery Engine. | **GCP Console**: Top navigation dropdown.<br>**Terminal**: `gcloud config get-value project` |
| **GCP Admin Email** | `--admin-email` | GCP admin user owning project resources & 3P OAuth consents. | **GCP Console**: User account in top-right avatar.<br>**Terminal**: `gcloud config get-value account` |
| **Desktop App Email** | `--app-email` | Email signed into the Gemini Enterprise Desktop App UI. | **Desktop App**: Displayed at the bottom-left corner of the app screen. |
| **GE Config ID (CID)** | `--config-id` | Discovery Engine Config UUID (`cid`). | **Web App**: Open [Gemini Enterprise Web App](https://vertexaisearch.cloud.google.com). Look at URL: `https://vertexaisearch.cloud.google.com/home/cid/<CONFIG_ID>`.<br>**GCP Console**: Vertex AI Search & Conversation → Engines → Engine Details → **Copy Config Link**. |
| **GCP Project Number** | `--project-number` | Numerical GCP project ID. | **GCP Console**: Home Dashboard → Project info card.<br>**Terminal**: `gcloud projects describe <PROJECT_ID> --format="value(projectNumber)"` |

---

## 🚀 How to Run

### Option A: Non-Interactive One-Liner (Recommended)
Replace the `<PLACEHOLDERS>` with your actual values:

```bash
python3 setup_cowork_app.py \
  --project <YOUR_PROJECT_ID> \
  --admin-email <YOUR_ADMIN_EMAIL> \
  --app-email <YOUR_APP_EMAIL> \
  --config-id <YOUR_CONFIG_ID> \
  --project-number <YOUR_PROJECT_NUMBER>
```

### Option B: Interactive Mode
Run the script without flags and enter your values when prompted:

```bash
python3 setup_cowork_app.py
```

---

## ⚙️ What the Script Does (Automated Steps)

1. **`gcloud` & ADC Setup**: Sets `<YOUR_PROJECT_ID>` as active core & quota project in `gcloud`. Grants `roles/discoveryengine.admin` IAM permissions to your desktop app user.
2. **Workspace & Model Setup**: Ensures `~/cowork_workspace/.cowork/` exists and deploys `model_configs.json` configured for your GCP project.
3. **Dynamic Discovery Engine Setup**: Removes static `discovery_engine_connectors.json` and creates `discovery_engine.json` (`configId` + `projectNumber`). At startup, Cowork Gateway calls `lookupWidgetConfig` to dynamically discover all active collections at runtime.
4. **Gateway Code Patches**:
   - Modifies `token.py` to use ADC (`<YOUR_ADMIN_EMAIL>`) for Discovery Engine API calls so 3P OAuth authorizations bound to the project are recognized.
   - Modifies `mcp.py` & `widget_client.py` to inject `"X-Goog-User-Project": "<YOUR_PROJECT_ID>"` headers into all requests to prevent 403 quota errors.
5. **Cache Clearance & App Restart**: Wipes Electron local storage & cache (`~/Library/Application Support/ge-desktop-electron`) and launches `/Applications/Gemini Enterprise.app`.
