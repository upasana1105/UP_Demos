#!/usr/bin/env python3
"""Simplified End-to-End Cowork App Setup & Testing Tool.

Automates the complete E2E installation, configuration, credential setup,
and dynamic 3P connector discovery for Gemini Enterprise (GoGo).
"""

import json
import os
import shutil
import subprocess
import sys

APP_PATH = "/Applications/Gemini Enterprise.app"
HOME = os.path.expanduser("~")
COWORK_DIR = os.path.join(HOME, "cowork_workspace", ".cowork")


def run_cmd(cmd, check=True):
    print(f"👉 Executing: {cmd}")
    res = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    if check and res.returncode != 0:
        print(f"❌ Command failed:\n{res.stderr}")
        sys.exit(1)
    return res.stdout.strip()


def prompt_input(label, default=""):
    prompt_str = f"Enter {label}" + (f" [{default}]: " if default else ": ")
    val = input(prompt_str).strip()
    return val if val else default


def main():
    print("==================================================")
    print("🚀 Gemini Enterprise (GoGo) End-to-End Setup Tool")
    print("==================================================")

    # Gather required user inputs
    project_id = prompt_input("GCP Project ID")
    project_number = prompt_input("GCP Project Number")
    config_id = prompt_input("Discovery Engine Config ID (GE Instance UUID)")
    admin_email = prompt_input("GCP Admin Email (owning project resources)")
    app_email = prompt_input("Desktop App User Email (signed into desktop UI)")

    download_dir = prompt_input(
        "Path to Downloads folder", os.path.join(HOME, "Downloads")
    )

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
    run_cmd(f"gcloud config set project {project_id}")
    run_cmd(f"gcloud auth application-default set-quota-project {project_id}")

    print(f"Granting roles/discoveryengine.admin to {app_email}...")
    run_cmd(
        f"gcloud projects add-iam-policy-binding {project_id} --member='user:{app_email}' --role='roles/discoveryengine.admin'",
        check=False,
    )

    # Step 2: Ensure .cowork Directory & Deploy model_configs.json
    print("\n[2/5] Deploying Model Configurations...")
    os.makedirs(COWORK_DIR, exist_ok=True)

    model_src = os.path.join(download_dir, "model_configs.json")
    if os.path.exists(model_src):
        with open(model_src, "r") as f:
            model_text = f.read()
        # Replace default template project placeholders with user project_id
        updated_model_text = model_text.replace('"uppdemos"', f'"{project_id}"')
        with open(os.path.join(COWORK_DIR, "model_configs.json"), "w") as f:
            f.write(updated_model_text)
        print(f"Deployed model_configs.json (cloud_project: {project_id})")
    else:
        print(f"⚠️ Warning: {model_src} not found. Skipping model_configs copy.")

    # Step 3: Deploy discovery_engine.json & Remove Static Connectors
    print("\n[3/5] Setting up Native Discovery Engine Configuration...")
    manual_connectors = os.path.join(COWORK_DIR, "discovery_engine_connectors.json")
    if os.path.exists(manual_connectors):
        os.remove(manual_connectors)
        print("Removed static discovery_engine_connectors.json for native dynamic lookup.")

    discovery_src = os.path.join(download_dir, "discovery_engine.json")
    if os.path.exists(discovery_src):
        with open(discovery_src, "r") as f:
            disc_data = json.load(f)
        disc_data["configId"] = config_id
        disc_data["projectNumber"] = project_number
        with open(os.path.join(COWORK_DIR, "discovery_engine.json"), "w") as f:
            json.dump(disc_data, f, indent=2)
        print(f"Updated discovery_engine.json with Config ID & Project Number from {discovery_src}")
    else:
        disc_data = {
            "configId": config_id,
            "location": "global",
            "env": "",
            "projectNumber": project_number,
        }
        with open(os.path.join(COWORK_DIR, "discovery_engine.json"), "w") as f:
            json.dump(disc_data, f, indent=2)
        print("Created discovery_engine.json")

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

    # Step 5: Launch App & Verification Guidance
    print("\n[5/5] Launching Gemini Enterprise Desktop App...")
    run_cmd(f'open "{APP_PATH}"', check=False)

    print("\n==================================================")
    print("✅ Setup Completed Successfully!")
    print("==================================================")
    print("🧪 How to Verify & Test Your Setup:")
    print("  1. Sign into the app UI with: " + app_email)
    print("  2. Go to Connected Apps / Customize in the app side menu.")
    print("  3. Verify that 3P connectors (Jira, Salesforce, GitHub, Slack, etc.) display active toolsets.")
    print("  4. Send a test prompt in Chat:")
    print("     - 'Summarize my Jira tickets'")
    print("     - 'Search Salesforce for accounts'")
    print("     - 'List my Google Calendar events for today'")
    print("==================================================\n")


if __name__ == "__main__":
    main()
