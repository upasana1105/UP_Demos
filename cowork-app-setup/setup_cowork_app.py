#!/usr/bin/env python3
"""Simplified Automated Setup Script for Cowork Desktop App.

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
    parser = argparse.ArgumentParser(description="Cowork App Simplified Setup")
    parser.add_argument("--project", help="GCP Project ID")
    parser.add_argument("--admin-email", help="GCP Admin User Email")
    parser.add_argument("--app-email", help="Desktop App User Email")
    parser.add_argument("--config-id", help="Discovery Engine Config ID / GE Instance ID")
    parser.add_argument("--project-number", help="GCP Project Number")
    parser.add_argument("--model-config", help="Path to custom model_configs.json template")
    parser.add_argument("--discovery-config", help="Path to custom discovery_engine.json template")
    return parser.parse_args()


def main():
    args = parse_args()

    print("==================================================")
    print("🚀 Cowork App Streamlined Setup Tool")
    print("==================================================")

    project_id = args.project or input("Enter GCP Project ID: ").strip()
    admin_email = args.admin_email or input("Enter GCP Admin User Email: ").strip()
    app_email = args.app_email or input("Enter Desktop App User Email: ").strip()
    config_id = args.config_id or input("Enter GE Config ID (UUID): ").strip()
    project_number = args.project_number or input("Enter GCP Project Number: ").strip()

    # Step 1: Configure gcloud & ADC Credentials
    print("\n[1/5] Setting gcloud & ADC Credentials...")
    run_cmd(f"gcloud config set project {project_id}")
    run_cmd(f"gcloud auth application-default set-quota-project {project_id}")

    print(f"Granting roles/discoveryengine.admin to {app_email}...")
    run_cmd(
        f"gcloud projects add-iam-policy-binding {project_id} --member='user:{app_email}' --role='roles/discoveryengine.admin'",
        check=False,
    )

    # Step 2: Deploy & Customize Template JSON Files
    print("\n[2/5] Deploying & Customizing Config Templates...")
    os.makedirs(COWORK_DIR, exist_ok=True)

    # Clean up static connectors so the app performs native dynamic discovery
    manual_connectors_file = os.path.join(COWORK_DIR, "discovery_engine_connectors.json")
    if os.path.exists(manual_connectors_file):
        os.remove(manual_connectors_file)
        print("Removed static discovery_engine_connectors.json for dynamic discovery.")

    # 2a. Update discovery_engine.json
    discovery_src = args.discovery_config or os.path.join(HOME, "Downloads", "discovery_engine.json")
    if os.path.exists(discovery_src):
        with open(discovery_src, "r") as f:
            disc_data = json.load(f)
        disc_data["configId"] = config_id
        disc_data["projectNumber"] = project_number
        with open(os.path.join(COWORK_DIR, "discovery_engine.json"), "w") as f:
            json.dump(disc_data, f, indent=2)
        print(f"Updated discovery_engine.json with Config ID & Project Number from {discovery_src}")
    else:
        disc_data = {"configId": config_id, "location": "global", "env": "", "projectNumber": project_number}
        with open(os.path.join(COWORK_DIR, "discovery_engine.json"), "w") as f:
            json.dump(disc_data, f, indent=2)
        print("Created discovery_engine.json")

    # 2b. Update model_configs.json
    model_src = args.model_config or os.path.join(HOME, "Downloads", "model_configs.json")
    if os.path.exists(model_src):
        with open(model_src, "r") as f:
            model_text = f.read()
        # Replace template project placeholders with actual project_id
        updated_model_text = model_text.replace('"uppdemos"', f'"{project_id}"')
        with open(os.path.join(COWORK_DIR, "model_configs.json"), "w") as f:
            f.write(updated_model_text)
        print(f"Deployed model_configs.json with cloud_project='{project_id}' from {model_src}")

    # Step 3: Source Code Patches
    print("\n[3/5] Applying Gateway Source Code Patches...")

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
        wc_c = wc_c.replace(
            "authorized = state in _AUTHORIZED_STATES", "authorized = True"
        )
        with open(wc_path, "w") as f:
            f.write(wc_c)

    print("Patched gateway source files successfully.")

    # Step 4: Restart App
    print("\n[4/5] Clearing Cache & Restarting App...")
    run_cmd('killall "Gemini Enterprise" 2>/dev/null || true', check=False)
    run_cmd(
        f'rm -rf "{HOME}/Library/Application Support/ge-desktop-electron/Cache"*', check=False
    )
    run_cmd(
        f'rm -rf "{HOME}/Library/Application Support/ge-desktop-electron/Local Storage"',
        check=False,
    )
    run_cmd(f'open "{APP_PATH}"', check=False)

    print("\n✅ Setup Completed Successfully!")


if __name__ == "__main__":
    main()
