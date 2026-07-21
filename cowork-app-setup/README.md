# 💻 Cowork App End-to-End Generic Setup Guide

This document provides a step-by-step guide for setting up the **Cowork Desktop App (Gemini Enterprise / GoGo)** and connecting **3P Discovery Engine Connectors** for any GCP project environment.

---

## 📋 Where to Find Your Configuration Details

Gather these 5 values from your GCP project before starting:

1. **GCP Project ID (`<YOUR_PROJECT_ID>`)**:
   - *GCP Console*: Top navigation bar dropdown menu.
   - *Terminal*: Run `gcloud config get-value project`.

2. **GCP Admin Email (`<YOUR_ADMIN_EMAIL>`)**:
   - *GCP Console*: Top-right user avatar menu.
   - *Terminal*: Run `gcloud config get-value account`.

3. **Desktop App User Email (`<YOUR_APP_EMAIL>`)**:
   - *Desktop App*: Displayed at the bottom-left corner of the Gemini Enterprise desktop app window.

4. **GE Instance Config ID / CID (`<YOUR_CONFIG_ID>`)**:
   - *Web App*: Open [Gemini Enterprise Web App](https://vertexaisearch.cloud.google.com). Look at your browser address bar: `https://vertexaisearch.cloud.google.com/home/cid/<YOUR_CONFIG_ID>`. The UUID string after `/cid/` is your Config ID.
   - *GCP Console*: Open **Vertex AI Search & Conversation** → **Engines** → Click on your engine → Click **Copy Config Link**.

5. **GCP Project Number (`<YOUR_PROJECT_NUMBER>`)**:
   - *GCP Console*: Home Dashboard → **Project info** card.
   - *Terminal*: Run `gcloud projects describe <YOUR_PROJECT_ID> --format="value(projectNumber)"`.

---

## 🚀 Step-by-Step Installation & Setup

### Step 1: Configure GCP Credentials & IAM Permissions
Open terminal and run:

```bash
# 1. Set active project and quota project
gcloud config set project <YOUR_PROJECT_ID>
gcloud auth login <YOUR_ADMIN_EMAIL>
gcloud auth application-default login
gcloud auth application-default set-quota-project <YOUR_PROJECT_ID>

# 2. Grant Discovery Engine Admin IAM role to desktop app user
gcloud projects add-iam-policy-binding <YOUR_PROJECT_ID> \
  --member="user:<YOUR_APP_EMAIL>" \
  --role="roles/discoveryengine.admin"
```

---

### Step 2: Install Desktop App & Deploy Model Configurations

1. Run `install.sh` from your GoGo release directory:
   ```bash
   cd ~/Downloads/gogo_release_folder
   ./install.sh --skip-verify
   ```

2. Copy your `model_configs.json` into `~/cowork_workspace/.cowork/model_configs.json` and ensure `"cloud_project"` points to `<YOUR_PROJECT_ID>`:
   ```json
   {
     "catalog": [
       {
         "model": "gemini-2.5-flash",
         "model_type": "vertex",
         "cloud_project": "<YOUR_PROJECT_ID>",
         "cloud_location": "us-central1"
       }
     ]
   }
   ```

---

### Step 3: Configure Native Discovery Engine (Dynamic Lookup)

Deploy `~/cowork_workspace/.cowork/discovery_engine.json` using your Config ID and Project Number:

```bash
# Remove static connectors file to enable dynamic lookup
rm -f ~/cowork_workspace/.cowork/discovery_engine_connectors.json

# Write discovery_engine.json
cat << 'EOF' > ~/cowork_workspace/.cowork/discovery_engine.json
{
  "configId": "<YOUR_CONFIG_ID>",
  "location": "global",
  "env": "",
  "projectNumber": "<YOUR_PROJECT_NUMBER>"
}
EOF
```

---

### Step 4: Apply Gateway Source Code Patches

Run the following Python snippet to patch Cowork Gateway (`/Applications/Gemini Enterprise.app/Contents/Resources/python/lib/python3.12/site-packages/cowork_gateway`):

```python
import os

site_packages = "/Applications/Gemini Enterprise.app/Contents/Resources/python/lib/python3.12/site-packages/cowork_gateway"
project_id = "<YOUR_PROJECT_ID>"

# 1. Patch token.py to prefer ADC credentials for Discovery Engine
token_path = os.path.join(site_packages, "gateway_public/discovery/token.py")
token_code = """from cowork_gateway.agent import managed_auth

def get_access_token() -> str | None:
  try:
    import google.auth, google.auth.transport.requests
    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    creds.refresh(google.auth.transport.requests.Request())
    if creds.token:
      return creds.token
  except Exception:
    pass
  token = managed_auth._read_token_file()
  if token:
    return token
  try:
    return managed_auth.get_access_token()
  except managed_auth.Error:
    return None
"""
with open(token_path, "w") as f:
  f.write(token_code)

# 2. Inject X-Goog-User-Project header in mcp.py & widget_client.py
mcp_path = os.path.join(site_packages, "gateway_public/discovery/mcp.py")
with open(mcp_path, "r") as f:
  mcp_c = f.read()
if "X-Goog-User-Project" not in mcp_c:
  mcp_c = mcp_c.replace('"User-Agent": widget_client.DEFAULT_USER_AGENT,', f'"User-Agent": widget_client.DEFAULT_USER_AGENT,\n      "X-Goog-User-Project": "{project_id}",')
  with open(mcp_path, "w") as f:
    f.write(mcp_c)

wc_path = os.path.join(site_packages, "gateway_public/discovery/widget_client.py")
with open(wc_path, "r") as f:
  wc_c = f.read()
if "X-Goog-User-Project" not in wc_c:
  wc_c = wc_c.replace('"User-Agent": user_agent,', f'"User-Agent": user_agent,\n      "X-Goog-User-Project": "{project_id}",')
  with open(wc_path, "w") as f:
    f.write(wc_c)

print("Gateway patches applied successfully!")
```

---

### Step 5: Launch & Verify

```bash
killall "Gemini Enterprise" 2>/dev/null || true
rm -rf "$HOME/Library/Application Support/ge-desktop-electron/Cache"*
rm -rf "$HOME/Library/Application Support/ge-desktop-electron/Local Storage"
open "/Applications/Gemini Enterprise.app"
```
