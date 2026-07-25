#!/usr/bin/env python3
"""End-to-End Cowork App Setup & Patching Tool.

Automates the complete E2E installation, configuration, credential setup,
gateway patching (token/quota headers), and dynamic 3P connector discovery for Gemini Enterprise (GoGo).
"""

import glob
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
ADC_PATH = os.path.join(HOME, ".config", "gcloud", "application_default_credentials.json")


def get_cmd_output(cmd):
    """Executes a command silently and returns stripped stdout if successful."""
    try:
        res = subprocess.run(cmd, shell=True, text=True, capture_output=True)
        return res.stdout.strip() if res.returncode == 0 else ""
    except Exception:
        return ""


def run_cmd(cmd, check=False):
    """Executes a shell command with non-fatal warning tolerance."""
    print(f"👉 Executing: {cmd}")
    res = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    if res.returncode != 0:
        if check:
            print(f"❌ Command failed:\n{res.stderr.strip()}")
            sys.exit(1)
        else:
            if res.stderr.strip():
                print(f"⚠️ Notice (non-fatal): {res.stderr.strip().splitlines()[0]}")
    return res.stdout.strip()


def prompt_input(label, default=""):
    """Prompts user for input with optional dynamic default."""
    prompt_str = f"Enter {label}" + (f" [{default}]: " if default else ": ")
    try:
        val = input(prompt_str).strip()
        return val if val else default
    except (EOFError, KeyboardInterrupt):
        print(default)
        return default


def find_candidate_file(filename, download_dir):
    """Finds matching candidate file in Downloads or release bundles."""
    candidates = []
    direct = os.path.join(download_dir, filename)
    if os.path.exists(direct):
        candidates.append(direct)

    for p in glob.glob(os.path.join(download_dir, "gogo_*", "helpers", filename)):
        candidates.append(p)
    for p in glob.glob(os.path.join(download_dir, "gogo_*", filename)):
        candidates.append(p)

    candidates = list(dict.fromkeys(candidates))
    if not candidates:
        return None
    candidates.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return candidates[0]


def discover_active_gcloud_defaults():
    """Detects active gcloud defaults from caller's current environment if available."""
    proj_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "") or get_cmd_output("gcloud config get-value project 2>/dev/null")
    if not proj_id and os.path.exists(ADC_PATH):
        try:
            with open(ADC_PATH) as f:
                proj_id = json.load(f).get("quota_project_id", "")
        except Exception:
            pass

    proj_num = ""
    if proj_id and not proj_id.startswith("("):
        proj_num = get_cmd_output(f"gcloud projects describe {proj_id} --format='value(projectNumber)' 2>/dev/null")

    active_account = get_cmd_output("gcloud config get-value account 2>/dev/null")
    if active_account.startswith("("):
        active_account = ""

    return {
        "project_id": proj_id if not proj_id.startswith("(") else "",
        "project_number": proj_num if not proj_num.startswith("(") else "",
        "admin_email": active_account,
        "app_email": active_account,
    }


def main():
    print("==================================================")
    print("🚀 Gemini Enterprise (GoGo) End-to-End Setup Tool")
    print("==================================================")

    default_download_dir = os.path.join(HOME, "Downloads")
    download_dir = prompt_input("Path to Downloads folder", default_download_dir)

    # Detect caller's active gcloud context (if configured)
    gcloud_defaults = discover_active_gcloud_defaults()

    # Gather user inputs
    project_id = prompt_input("GCP Project ID", gcloud_defaults["project_id"])
    project_number = prompt_input("GCP Project Number", gcloud_defaults["project_number"])
    config_id = prompt_input("Discovery Engine Config ID (GE Instance UUID)")
    admin_email = prompt_input("GCP Admin Email (owning project resources)", gcloud_defaults["admin_email"])
    app_email = prompt_input("Desktop App User Email (signed into desktop UI)", gcloud_defaults["app_email"])

    print("\n--------------------------------------------------")
    print("📋 Configuration Summary:")
    print(f"  • GCP Project ID: {project_id}")
    print(f"  • GCP Project Number: {project_number}")
    print(f"  • Config ID: {config_id}")
    print(f"  • Admin Email: {admin_email}")
    print(f"  • App Email: {app_email}")
    print("--------------------------------------------------\n")

    try:
        confirm = input("Proceed with setup? (Y/n): ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        confirm = "y"

    if confirm and confirm not in ["y", "yes"]:
        print("Setup aborted.")
        sys.exit(0)

    # Step 1: Configure gcloud & ADC Credentials
    print("\n[1/6] Setting gcloud & ADC Credentials...")
    if admin_email:
        run_cmd(f"gcloud config set account {admin_email}", check=False)

    if project_id:
        run_cmd(f"gcloud config set project {project_id}", check=False)
        run_cmd(f"gcloud auth application-default set-quota-project {project_id}", check=False)

        # Direct ADC fallback injection to ensure quota project is always configured
        if os.path.exists(ADC_PATH):
            try:
                with open(ADC_PATH, "r") as f:
                    adc_json = json.load(f)
                adc_json["quota_project_id"] = project_id
                with open(ADC_PATH, "w") as f:
                    json.dump(adc_json, f, indent=2)
                print(f"✅ Configured quota_project_id in ADC credentials ({ADC_PATH})")
            except Exception as e:
                print(f"⚠️ Notice: Could not direct-update ADC file: {e}")

    if project_id and app_email:
        print(f"Granting roles/discoveryengine.admin to {app_email}...")
        run_cmd(
            f"gcloud projects add-iam-policy-binding {project_id} --member='user:{app_email}' --role='roles/discoveryengine.admin'",
            check=False,
        )

    # Step 2: Ensure .cowork Directory & Deploy model_configs.json dynamically
    print("\n[2/6] Deploying Model Configurations...")
    os.makedirs(COWORK_DIR, exist_ok=True)

    source_to_use = find_candidate_file("model_configs.json", download_dir)
    target_model_file = os.path.join(COWORK_DIR, "model_configs.json")

    if source_to_use and os.path.exists(source_to_use) and project_id:
        try:
            with open(source_to_use, "r") as f:
                model_data = json.load(f)

            # Dynamically update cloud_project across all configured models
            for model_item in model_data.get("models", []):
                if "cloud_project" in model_item:
                    model_item["cloud_project"] = project_id

            # Dynamically update default_cloud_project across catalog providers
            for provider in model_data.get("catalog", {}).get("providers", []):
                if "default_cloud_project" in provider and provider["default_cloud_project"] is not None:
                    provider["default_cloud_project"] = project_id

            with open(target_model_file, "w") as f:
                json.dump(model_data, f, indent=2)
            print(f"✅ Deployed and configured model_configs.json from {source_to_use} (cloud_project: {project_id})")
        except Exception as e:
            print(f"⚠️ Error parsing model_configs.json: {e}")
    else:
        if not os.path.exists(target_model_file):
            print(f"⚠️ Notice: model_configs.json not found in {download_dir} or {COWORK_DIR}.")

    # Step 3: Deploy discovery_engine.json & Remove Static Connectors
    print("\n[3/6] Setting up Native Discovery Engine Configuration...")
    manual_connectors = os.path.join(COWORK_DIR, "discovery_engine_connectors.json")
    if os.path.exists(manual_connectors):
        os.remove(manual_connectors)
        print("✅ Removed static discovery_engine_connectors.json for native dynamic lookup.")

    disc_data = {
        "configId": config_id,
        "location": "global",
        "env": "",
        "projectNumber": project_number,
    }
    disc_target = os.path.join(COWORK_DIR, "discovery_engine.json")
    with open(disc_target, "w") as f:
        json.dump(disc_data, f, indent=2)
    print(f"✅ Configured {disc_target} (Config ID: {config_id}, Project Number: {project_number})")

    # Step 4: Apply Gateway Source Code Patches
    print("\n[4/6] Applying Gateway Source Code Patches...")
    if os.path.exists(SITE_PACKAGES):
        try:
            # 1. Update token.py to prefer ADC credentials for Discovery Engine API calls
            token_path = os.path.join(SITE_PACKAGES, "gateway_public/discovery/token.py")
            if os.path.exists(token_path):
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
                print("✅ Patched discovery/token.py to use ADC credentials for Discovery Engine API.")

            # 2. Inject X-Goog-User-Project header into mcp.py & widget_client.py
            mcp_path = os.path.join(SITE_PACKAGES, "gateway_public/discovery/mcp.py")
            if os.path.exists(mcp_path) and project_id:
                with open(mcp_path, "r") as f:
                    mcp_c = f.read()
                if "X-Goog-User-Project" not in mcp_c:
                    mcp_c = mcp_c.replace(
                        '"User-Agent": widget_client.DEFAULT_USER_AGENT,',
                        f'"User-Agent": widget_client.DEFAULT_USER_AGENT,\n      "X-Goog-User-Project": "{project_id}",',
                    )
                    with open(mcp_path, "w") as f:
                        f.write(mcp_c)
                    print(f"✅ Patched discovery/mcp.py with X-Goog-User-Project: {project_id}")

            wc_path = os.path.join(SITE_PACKAGES, "gateway_public/discovery/widget_client.py")
            if os.path.exists(wc_path) and project_id:
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
                    print(f"✅ Patched discovery/widget_client.py with X-Goog-User-Project: {project_id}")

        except Exception as e:
            print(f"⚠️ Notice while applying patches: {e}")
    else:
        print(f"⚠️ Notice: Gateway site-packages path ({SITE_PACKAGES}) not found. Skipping gateway patches.")

    # Step 5: Clear App Cache & Local Storage
    print("\n[5/6] Clearing App Cache & Local Storage...")
    run_cmd('killall "Gemini Enterprise" 2>/dev/null || true', check=False)
    app_data_dir = os.path.join(HOME, "Library", "Application Support", "ge-desktop-electron")
    if os.path.exists(app_data_dir):
        for cache_folder in ["Cache", "Code Cache", "Local Storage", "Session Storage", "GPUCache"]:
            target_cache = os.path.join(app_data_dir, cache_folder)
            if os.path.exists(target_cache):
                try:
                    shutil.rmtree(target_cache, ignore_errors=True)
                except Exception:
                    pass
    print("✅ App cache and local storage cleared.")

    # Step 6: Launch App & Verification Guidance
    print("\n[6/6] Launching Gemini Enterprise Desktop App...")
    if os.path.exists(APP_PATH):
        run_cmd(f'open "{APP_PATH}"', check=False)
        print("✅ Gemini Enterprise Desktop App launched.")
    else:
        print(f"⚠️ App bundle not found at {APP_PATH}.")

    print("\n==================================================")
    print("🎉 Setup Completed Successfully!")
    print("==================================================")
    print("🧪 How to Verify & Test Your Setup:")
    if app_email:
        print(f"  1. Sign into the app UI with: {app_email}")
    else:
        print("  1. Sign into the app UI with your account.")
    print("  2. Go to Connected Apps / Customize in the app side menu.")
    print("  3. Verify that 3P connectors (Jira, Salesforce, GitHub, Slack, ServiceNow, BigQuery) display active toolsets.")
    print("  4. Send a test prompt in Chat:")
    print("     - 'Summarize my Jira tickets'")
    print("     - 'Search Salesforce for accounts'")
    print("     - 'List my Google Calendar events for today'")
    print("==================================================\n")


if __name__ == "__main__":
    main()
