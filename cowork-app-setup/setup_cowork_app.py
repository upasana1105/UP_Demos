#!/usr/bin/env python3
"""Native End-to-End Automated Setup Script for Cowork Desktop App.

Usage:
  python3 setup_cowork_app.py [--project PROJECT_ID] [--admin-email ADMIN_EMAIL] [--app-email APP_EMAIL] [--config-id CONFIG_ID] [--project-number PROJECT_NUMBER]
"""

import argparse
import json
import os
import shutil
import subprocess
import sys

APP_PATH = "/Applications/Gemini Enterprise.app"
SITE_PACKAGES = os.path.join(
    APP_PATH, "Contents/Resources/python/lib/python3.12/site-packages/cowork_gateway"
)
HOME = os.path.expanduser("~")
COWORK_DIR = os.path.join(HOME, "cowork_workspace", ".cowork")


def run_cmd(cmd, check=True):
    print(f"👉 Executing: {cmd}")
    res = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    if check and res.returncode != 0:
        print(f"❌ Command failed:\n{res.stderr}")
        sys.exit(1)
    return res.stdout.strip()


def parse_args():
    parser = argparse.ArgumentParser(description="Cowork App Native Automated Setup")
    parser.add_argument("--project", help="GCP Project ID (e.g. uppdemos)")
    parser.add_argument("--admin-email", help="GCP Admin User Email")
    parser.add_argument("--app-email", help="Desktop App User Email")
    parser.add_argument("--config-id", help="Discovery Engine Config ID / GE Instance ID")
    parser.add_argument("--project-number", help="GCP Project Number")
    parser.add_argument("--model-config", help="Path to custom model_configs.json")
    return parser.parse_args()


def main():
    args = parse_args()

    print("==================================================")
    print("🚀 Cowork App Native Setup Tool (Dynamic Discovery)")
    print("==================================================")

    project_id = args.project or input("Enter GCP Project ID [uppdemos]: ").strip() or "uppdemos"
    admin_email = (
        args.admin_email
        or input("Enter GCP Admin User Email [admin@upasanapati.altostrat.com]: ").strip()
        or "admin@upasanapati.altostrat.com"
    )
    app_email = (
        args.app_email
        or input("Enter Desktop App User Email [upasanapati@google.com]: ").strip()
        or "upasanapati@google.com"
    )
    config_id = (
        args.config_id
        or input("Enter Discovery Engine Config ID [e6bd94f5-0ebc-425c-8196-3ba586609f94]: ").strip()
        or "e6bd94f5-0ebc-425c-8196-3ba586609f94"
    )
    project_number = (
        args.project_number
        or input("Enter GCP Project Number [850431687571]: ").strip()
        or "850431687571"
    )

    # Step 1: Configure gcloud & ADC
    print("\n[1/5] Configuring gcloud & ADC Credentials...")
    run_cmd(f"gcloud config set project {project_id}")
    run_cmd(f"gcloud auth application-default set-quota-project {project_id}")

    # IAM Grant
    print(f"Granting roles/discoveryengine.admin to {app_email}...")
    run_cmd(
        f"gcloud projects add-iam-policy-binding {project_id} --member='user:{app_email}' --role='roles/discoveryengine.admin'",
        check=False,
    )

    # Step 2: Ensure Workspace & Model Config
    print("\n[2/5] Setting up Workspace & Model Config...")
    os.makedirs(COWORK_DIR, exist_ok=True)

    model_config_src = args.model_config or os.path.join(HOME, "Downloads", "model_configs.json")
    if os.path.exists(model_config_src):
        shutil.copy(model_config_src, os.path.join(COWORK_DIR, "model_configs.json"))
        print(f"Copied model configs from {model_config_src}")

    # Step 3: Configure Native Discovery Engine (Dynamic Connector Lookup)
    print("\n[3/5] Setting up Native Discovery Engine Configuration...")

    # Remove manual connectors file so the app dynamically loads live collections from Discovery Engine
    manual_connectors_file = os.path.join(COWORK_DIR, "discovery_engine_connectors.json")
    if os.path.exists(manual_connectors_file):
        os.remove(manual_connectors_file)
        print("Removed manual discovery_engine_connectors.json to enable native dynamic lookup.")

    engine_json = {
        "configId": config_id,
        "location": "global",
        "env": "",
        "projectNumber": project_number,
    }
    with open(os.path.join(COWORK_DIR, "discovery_engine.json"), "w") as f:
        json.dump(engine_json, f, indent=2)
    print("Created discovery_engine.json with Config ID & Project Number.")

    # Step 4: Applying Code Patches
    print("\n[4/5] Applying Gateway Source Patches...")

    token_path = os.path.join(SITE_PACKAGES, "gateway_public/discovery/token.py")
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

    mcp_path = os.path.join(SITE_PACKAGES, "gateway_public/discovery/mcp.py")
    with open(mcp_path, "r") as f:
        mcp_c = f.read()
    if "X-Goog-User-Project" not in mcp_c:
        mcp_c = mcp_c.replace(
            '"User-Agent": widget_client.DEFAULT_USER_AGENT,',
            f'"User-Agent": widget_client.DEFAULT_USER_AGENT,\n      "X-Goog-User-Project": "{project_id}",',
        )
        with open(mcp_path, "w") as f:
            f.write(mcp_c)

    wc_path = os.path.join(SITE_PACKAGES, "gateway_public/discovery/widget_client.py")
    with open(wc_path, "r") as f:
        wc_c = f.read()
    if "X-Goog-User-Project" not in wc_c:
        wc_c = wc_c.replace(
            '"User-Agent": user_agent,',
            f'"User-Agent": user_agent,\n      "X-Goog-User-Project": "{project_id}",',
        )
        with open(wc_path, "w") as f:
            f.write(wc_c)

    print("Patched token.py, mcp.py, and widget_client.py successfully.")

    # Step 5: Restart App
    print("\n[5/5] Restarting Gemini Enterprise App...")
    run_cmd('killall "Gemini Enterprise" 2>/dev/null || true', check=False)
    run_cmd(
        f'rm -rf "{HOME}/Library/Application Support/ge-desktop-electron/Cache"*', check=False
    )
    run_cmd(
        f'rm -rf "{HOME}/Library/Application Support/ge-desktop-electron/Local Storage"',
        check=False,
    )
    run_cmd(f'open "{APP_PATH}"', check=False)

    print("\n✅ Native Setup Completed Successfully!")
    print("The app will dynamically discover and load all active engine connectors from Discovery Engine.")


if __name__ == "__main__":
    main()
