# 🚀 Gemini Enterprise (GoGo) Desktop App Setup Guide

Setting up **Gemini Enterprise (GoGo)** with native 3P enterprise connectors (Jira, Salesforce, GitHub, Slack, Outlook, Teams, OneDrive, SharePoint, ServiceNow, BigQuery) requires only 3 simple steps:

---

## 📋 Required Inputs

Gather these 2 parameters from your GCP project:

1. **Config ID (`configId`)**: Open [Gemini Enterprise Web App](https://vertexaisearch.cloud.google.com). Look at your browser address bar: `https://vertexaisearch.cloud.google.com/home/cid/<CONFIG_ID>`. The UUID string following `/cid/` is your Config ID.
2. **Project Number (`projectNumber`)**: Found in GCP Console Dashboard → **Project info** card (or run `gcloud projects describe <PROJECT_ID> --format="value(projectNumber)"`).

---

## 🛠 Setup Steps

### 1. Update `discovery_engine.json`
Open `/Users/upasanapati/Downloads/discovery_engine.json` and set your `configId` and `projectNumber`:

```json
{
  "configId": "<YOUR_CONFIG_ID>",
  "location": "global",
  "env": "",
  "projectNumber": "<YOUR_PROJECT_NUMBER>"
}
```

---

### 2. Copy Config & Remove Static Connectors
Run the following terminal command to deploy `discovery_engine.json` and remove static connector overrides:

```bash
cp /Users/upasanapati/Downloads/discovery_engine.json ~/cowork_workspace/.cowork/discovery_engine.json
rm -f ~/cowork_workspace/.cowork/discovery_engine_connectors.json
```

---

### 3. Restart Gemini Enterprise App
Close and restart the desktop app to enable native dynamic connector discovery:

```bash
killall "Gemini Enterprise" 2>/dev/null || true
rm -rf "$HOME/Library/Application Support/ge-desktop-electron/Cache"*
rm -rf "$HOME/Library/Application Support/ge-desktop-electron/Local Storage"
open "/Applications/Gemini Enterprise.app"
```

---

At startup, Gemini Enterprise will automatically call `lookupWidgetConfig` for your `configId` and dynamically populate all active enterprise connectors and tools natively through the UI!
