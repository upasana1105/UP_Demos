#!/usr/bin/env python3
"""Turnkey End-to-End Provisioner for Gemini Enterprise BYOMCP Datastores.

Works on ANY GCP project (existing or brand new):
1. Overrides GCP Org Policy to turn off custom MCP restrictions (constraints/discoveryengine.managed.disableCustomMcpServerConnector).
2. Enables required GCP APIs (discoveryengine.googleapis.com, secretmanager.googleapis.com).
3. Fetches gcloud access token.
4. Securely stores OAuth Web Client credentials in GCP Secret Manager.
5. Provisions or Updates custom_mcp DataConnector with 'mcp_data' entity.
6. Verifies connector activation state and returns GCP Console URL.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from typing import Any, Dict


def get_access_token() -> str:
  """Retrieves gcloud access token."""
  for cmd in [
      ["gcloud", "auth", "application-default", "print-access-token"],
      ["gcloud", "auth", "print-access-token"],
  ]:
    try:
      proc = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=10)
      token = proc.stdout.strip()
      if token:
        return token
    except Exception:
      pass
  return ""


def disable_custom_mcp_org_policy(project: str) -> None:
  """Disables enforcement of constraints/discoveryengine.managed.disableCustomMcpServerConnector."""
  print(f"  Overriding Org Policy 'constraints/discoveryengine.managed.disableCustomMcpServerConnector' (enforce: false)...")
  policy_yaml = f"""name: projects/{project}/policies/discoveryengine.managed.disableCustomMcpServerConnector
spec:
  rules:
  - enforce: false
"""
  with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
    f.write(policy_yaml)
    temp_path = f.name

  try:
    cmd = ["gcloud", "org-policies", "set-policy", temp_path, f"--project={project}"]
    subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=10)
    print("  [SUCCESS] Custom MCP Org Policy enforcement disabled (enforce: false).")
  except Exception as e:
    print(f"  [INFO] Org Policy override skipped or already configured ({e}).")
  finally:
    if os.path.exists(temp_path):
      os.remove(temp_path)


def enable_gcp_services(project: str) -> None:
  """Ensures required GCP APIs are enabled on fresh projects."""
  services = ["discoveryengine.googleapis.com", "secretmanager.googleapis.com"]
  print(f"  Enabling GCP APIs for project '{project}'...")
  cmd = ["gcloud", "services", "enable"] + services + [f"--project={project}"]
  subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)


def store_in_secret_manager(project: str, secret_id: str, value: str) -> None:
  """Creates a secret container in GCP Secret Manager and populates a secret version."""
  subprocess.run(
      [
          "gcloud", "secrets", "create", secret_id,
          f"--project={project}",
          "--replication-policy=automatic",
      ],
      capture_output=True,
      text=True,
      timeout=15,
  )
  cmd_add = [
      "gcloud", "secrets", "versions", "add", secret_id,
      f"--project={project}",
      "--data-file=-",
  ]
  subprocess.run(cmd_add, input=value, capture_output=True, text=True, check=True, timeout=15)


def update_datastore(
    project: str,
    location: str,
    collection_id: str,
    instance_uri: str,
    client_id: str,
    client_secret: str,
    scopes: str,
    access_token: str,
    hostname: str = "discoveryengine.googleapis.com",
) -> Dict[str, Any]:
  """PATCHs UpdateDataConnector request to update existing connector."""
  resource_name = f"projects/{project}/locations/{location}/collections/{collection_id}/dataConnector"
  url = f"https://{hostname}/v1/{resource_name}?updateMask=actionConfig"

  payload = {
      "name": resource_name,
      "dataSource": "custom_mcp",
      "dataSourceVersion": 1.0,
      "connectorModes": ["FEDERATED", "ACTIONS"],
      "entities": [
          {
              "entityName": "mcp_data",
          }
      ],
      "params": {},
      "actionConfig": {
          "isActionConfigured": True,
          "createBapConnection": True,
          "actionParams": {
              "instance_uri": instance_uri,
              "mcp_server_source": "BYO_MCP",
              "auth_uri": "https://accounts.google.com/o/oauth2/v2/auth",
              "token_uri": "https://oauth2.googleapis.com/token",
              "client_id": client_id,
              "client_secret": client_secret,
              "scopes": scopes,
          },
      },
  }

  data = json.dumps(payload).encode("utf-8")
  headers = {
      "Content-Type": "application/json",
      "x-goog-user-project": project,
      "Authorization": f"Bearer {access_token}",
  }

  req = urllib.request.Request(url, data=data, headers=headers, method="PATCH")
  with urllib.request.urlopen(req, timeout=120) as resp:
    return json.loads(resp.read().decode("utf-8"))


def provision_datastore(
    project: str,
    location: str,
    collection_id: str,
    collection_display_name: str,
    instance_uri: str,
    client_id: str,
    client_secret: str,
    scopes: str,
    access_token: str,
    hostname: str = "discoveryengine.googleapis.com",
) -> Dict[str, Any]:
  """POSTs SetUpDataConnector request to provision the BYOMCP datastore."""
  parent = f"projects/{project}/locations/{location}"
  url = f"https://{hostname}/v1/{parent}:setUpDataConnector"

  display_name = collection_display_name or collection_id

  payload = {
      "parent": parent,
      "collectionId": collection_id,
      "collectionDisplayName": display_name,
      "dataConnector": {
          "dataSource": "custom_mcp",
          "dataSourceVersion": 1.0,
          "connectorModes": ["FEDERATED", "ACTIONS"],
          "entities": [
              {
                  "entityName": "mcp_data",
              }
          ],
          "params": {
              "oauth_access_token": "dummy_value",
          },
          "actionConfig": {
              "isActionConfigured": True,
              "createBapConnection": True,
              "actionParams": {
                  "instance_uri": instance_uri,
                  "mcp_server_source": "BYO_MCP",
                  "auth_uri": "https://accounts.google.com/o/oauth2/v2/auth",
                  "token_uri": "https://oauth2.googleapis.com/token",
                  "client_id": client_id,
                  "client_secret": client_secret,
                  "scopes": scopes,
              },
          },
      },
  }

  data = json.dumps(payload).encode("utf-8")
  headers = {
      "Content-Type": "application/json",
      "x-goog-user-project": project,
      "Authorization": f"Bearer {access_token}",
  }

  req = urllib.request.Request(url, data=data, headers=headers, method="POST")
  try:
    with urllib.request.urlopen(req, timeout=120) as resp:
      return json.loads(resp.read().decode("utf-8"))
  except urllib.error.HTTPError as e:
    err_body = e.read().decode("utf-8")
    if e.code in (400, 409, 429) or "ALREADY_EXISTS" in err_body or "Quota exceeded" in err_body:
      print("  [INFO] Setting up existing connector via UpdateDataConnector...")
      return update_datastore(
          project, location, collection_id, instance_uri, client_id, client_secret, scopes, access_token, hostname
      )
    raise RuntimeError(f"HTTP Error {e.code} {e.reason}: {err_body}") from e


def verify_datastore(
    project: str,
    location: str,
    collection_id: str,
    access_token: str,
    hostname: str = "discoveryengine.googleapis.com",
) -> Dict[str, Any]:
  """Fetches dataConnector to verify state and entities."""
  resource_name = f"projects/{project}/locations/{location}/collections/{collection_id}/dataConnector"
  url = f"https://{hostname}/v1/{resource_name}"
  headers = {
      "Authorization": f"Bearer {access_token}",
      "x-goog-user-project": project,
  }
  req = urllib.request.Request(url, headers=headers, method="GET")
  with urllib.request.urlopen(req, timeout=30) as resp:
    return json.loads(resp.read().decode("utf-8"))


def main() -> None:
  parser = argparse.ArgumentParser(
      description="End-to-End Automated Provisioner for Gemini Enterprise BYOMCP Datastores."
  )
  parser.add_argument("--project", required=True, help="Target GCP Project ID")
  parser.add_argument("--location", default="global", help="GCP Location")
  parser.add_argument(
      "--collection_id",
      default="bigquery_mcp_datastore",
      help="Collection / Datastore ID",
  )
  parser.add_argument(
      "--collection_display_name",
      default="BigQuery MCP Server",
      help="Human readable display name",
  )
  parser.add_argument(
      "--instance_uri",
      default="https://bigquery.googleapis.com/mcp",
      help="Target MCP Server URL",
  )
  parser.add_argument("--client_id", required=True, help="OAuth Web Client ID (.apps.googleusercontent.com)")
  parser.add_argument("--client_secret", required=True, help="OAuth Web Client Secret")
  parser.add_argument(
      "--scopes",
      default="https://www.googleapis.com/auth/bigquery",
      help="OAuth Scopes",
  )
  parser.add_argument(
      "--access_token",
      default="",
      help="OAuth Access Token (optional; fetched via gcloud if omitted)",
  )

  args = parser.parse_args()

  print("=" * 70)
  print("GEMINI ENTERPRISE END-TO-END AUTOMATED BYOMCP PROVISIONER")
  print("=" * 70)
  print(f"GCP Project ID  : {args.project}")
  print(f"Collection ID   : {args.collection_id}")
  print(f"MCP Server URL  : {args.instance_uri}")
  print(f"OAuth Client ID : {args.client_id}")

  # Step 1: Override Custom MCP Org Policy
  print("\n[STEP 1/5] Overriding Custom MCP Org Policy...")
  try:
    disable_custom_mcp_org_policy(args.project)
  except Exception as e:
    print(f"  [INFO] Could not set Org Policy ({e}). Proceeding...")

  # Step 2: Enable APIs
  print("\n[STEP 2/5] Ensuring required GCP APIs are enabled...")
  try:
    enable_gcp_services(args.project)
    print("  [SUCCESS] GCP APIs enabled.")
  except Exception as e:
    print(f"  [WARNING] Could not auto-enable APIs ({e}). Proceeding...")

  access_token = args.access_token or get_access_token()
  if not access_token:
    print("\n[ERROR] No access token provided and gcloud token unreadable.", file=sys.stderr)
    print("Please pass --access_token=\"$(gcloud auth print-access-token)\"", file=sys.stderr)
    sys.exit(1)

  # Step 3: Store in Secret Manager
  print("\n[STEP 3/5] Storing credentials in GCP Secret Manager...")
  try:
    store_in_secret_manager(args.project, "bq_mcp_client_id", args.client_id)
    store_in_secret_manager(args.project, "bq_mcp_client_secret", args.client_secret)
    print("  [SUCCESS] OAuth credentials stored in Secret Manager.")
  except Exception as e:
    print(f"  [WARNING] Secret Manager store skipped ({e}). Continuing provisioning...")

  # Step 4: Provision SetUpDataConnector / UpdateDataConnector
  print("\n[STEP 4/5] Provisioning BYOMCP DataConnector with 'mcp_data' entity...")
  try:
    setup_resp = provision_datastore(
        project=args.project,
        location=args.location,
        collection_id=args.collection_id,
        collection_display_name=args.collection_display_name,
        instance_uri=args.instance_uri,
        client_id=args.client_id,
        client_secret=args.client_secret,
        scopes=args.scopes,
        access_token=access_token,
    )
    print("  [SUCCESS] DataConnector successfully configured!")
  except Exception as e:
    print(f"  [ERROR] DataConnector provision failed: {e}", file=sys.stderr)
    sys.exit(1)

  # Step 5: Verify Activation
  print("\n[STEP 5/5] Verifying connector status in GCP...")
  time.sleep(2)
  try:
    status_resp = verify_datastore(
        project=args.project,
        location=args.location,
        collection_id=args.collection_id,
        access_token=access_token,
    )
    state = status_resp.get("state", "UNKNOWN")
    action_state = status_resp.get("actionState", "UNKNOWN")
    entities = status_resp.get("entities", [])
    print(f"  Connector State : {state}")
    print(f"  Action State    : {action_state}")
    print(f"  Entities        : {[e.get('entityName') for e in entities]}")

    console_url = f"https://console.cloud.google.com/gemini-enterprise/locations/{args.location}/collections/{args.collection_id}/connector?project={args.project}"
    print("\n" + "=" * 70)
    print("PROVISIONING COMPLETE! View your connector in Console:")
    print(f"👉 {console_url}")
    print("=" * 70)
  except Exception as e:
    print(f"  [WARNING] Verification call failed ({e}). Datastore configured.", file=sys.stderr)


if __name__ == "__main__":
  main()
