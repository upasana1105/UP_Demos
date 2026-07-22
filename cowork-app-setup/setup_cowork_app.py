#!/usr/bin/env python3
"""Robust End-to-End Cowork App Setup & Testing Tool.

Automates the complete E2E installation, configuration, credential setup,
and dynamic 3P connector discovery for Gemini Enterprise (GoGo).
No hardcoded project IDs, project numbers, config IDs, or user emails.
"""

import json
import os
import shutil
import subprocess
import sys

APP_PATH = "/Applications/Gemini Enterprise.app"
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
    val = input(prompt_str).strip()
    return val if val else default


def discover_dynamic_defaults(download_dir):
    """Dynamically detects configuration defaults from the caller's active environment."""
    # 1. Detect Project ID
    proj_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "") or get_cmd_output("gcloud config get-value project 2>/dev/null")
    if not proj_id and os.path.exists(ADC_PATH):
        try:
            with open(ADC_PATH) as f:
                proj_id = json.load(f).get("quota_project_id", "")
        except Exception:
            pass

    # 2. Detect Project Number
    proj_num = ""
    if proj_id:
        proj_num = get_cmd_output(f"gcloud projects describe {proj_id} --format='value(projectNumber)' 2>/dev/null")

    # 3. Detect Discovery Engine Config ID & Project Number fallback from local JSON configs
    config_id = ""
    candidate_paths = [
        os.path.join(COWORK_DIR, "discovery_engine.json"),
        os.path.join(download_dir, "discovery_engine.json"),
    ]
    for p in candidate_paths:
        if os.path.exists(p):
            try:
                with open(p) as f:
                    data = json.load(f)
                    if not config_id:
                        config_id = data.get("configId", "")
                    if not proj_num:
                        proj_num = str(data.get("projectNumber", ""))
            except Exception:
                pass

    # 4. Detect Active Accounts
    active_account = get_cmd_output("gcloud config get-value account 2>/dev/null")

    return {
        "project_id": proj_id,
        "project_number": proj_num,
        "config_id": config_id,
        "admin_email": active_account,
        "app_email": active_account,
    }


def main():
    print("==================================================")
    print("🚀 Gemini Enterprise (GoGo) End-to-End Setup Tool")
    print("==================================================")

    default_download_dir = os.path.join(HOME, "Downloads")
    download_dir = prompt_input("Path to Downloads folder", default_download_dir)

    # Dynamically detect environment defaults
    defaults = discover_dynamic_defaults(download_dir)

    # Gather user inputs (using dynamic defaults when available)
    project_id = prompt_input("GCP Project ID", defaults["project_id"])
    project_number = prompt_input("GCP Project Number", defaults["project_number"])
    config_id = prompt_input("Discovery Engine Config ID (GE Instance UUID)", defaults["config_id"])
    admin_email = prompt_input("GCP Admin Email (owning project resources)", defaults["admin_email"])
    app_email = prompt_input("Desktop App User Email (signed into desktop UI)", defaults["app_email"])

    print("\n--------------------------------------------------")
    print("📋 Configuration Summary:")
    print(f"  • GCP Project ID: {project_id}")
    print(f"  • GCP Project Number: {project_number}")
    print(f"  • Config ID: {config_id}")
    print(f"  • Admin Email: {admin_email}")
    print(f"  • App Email: {app_email}")
    print("--------------------------------------------------\n")

    confirm = input("Proceed with setup? (Y/n): ").strip().lower()
    if confirm and confirm not in ["y", "yes"]:
        print("Setup aborted.")
        sys.exit(0)

    # Step 1: Configure gcloud & ADC Credentials
    print("\n[1/5] Setting gcloud & ADC Credentials...")
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
    print("\n[2/5] Deploying Model Configurations...")
    os.makedirs(COWORK_DIR, exist_ok=True)

    model_src = os.path.join(download_dir, "model_configs.json")
    target_model_file = os.path.join(COWORK_DIR, "model_configs.json")

    source_to_use = None
    if os.path.exists(model_src):
        source_to_use = model_src
    elif os.path.exists(target_model_file):
        source_to_use = target_model_file

    if source_to_use and project_id:
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
            print(f"✅ Deployed and configured model_configs.json (cloud_project: {project_id})")
        except Exception as e:
            print(f"⚠️ Error parsing model_configs.json: {e}")
    else:
        if not os.path.exists(target_model_file):
            print(f"⚠️ Warning: model_configs.json not found in {download_dir} or {COWORK_DIR}.")

    # Step 3: Deploy discovery_engine.json & Remove Static Connectors
    print("\n[3/5] Setting up Native Discovery Engine Configuration...")
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

    # Step 4: Clear App Cache & Local Storage
    print("\n[4/5] Clearing App Cache & Local Storage...")
    run_cmd('killall "Gemini Enterprise" 2>/dev/null || true', check=False)
    run_cmd(
        f'rm -rf "{HOME}/Library/Application Support/ge-desktop-electron/Cache"*',
        check=False,
    )
    run_cmd(
        f'rm -rf "{HOME}/Library/Application Support/ge-desktop-electron/Local Storage"',
        check=False,
    )
    print("✅ App cache and local storage cleared.")

    # Step 5: Launch App & Verification Guidance
    print("\n[5/5] Launching Gemini Enterprise Desktop App...")
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
