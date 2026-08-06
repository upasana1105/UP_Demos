#!/usr/bin/env python3
"""Programmatic creation of Bring-Your-Own-MCP (custom_mcp) datastores in Gemini Enterprise."""

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, Optional


def parse_args() -> argparse.Namespace:
  """Parses command line arguments."""
  parser = argparse.ArgumentParser(
      description="Create a custom_mcp (BYOMCP) datastore in Gemini Enterprise."
  )
  parser.add_argument(
      "--project",
      required=True,
      help="Target GCP project ID or project number.",
  )
  parser.add_argument(
      "--location",
      default="global",
      help="GCP location for the collection/datastore. Default: global.",
  )
  parser.add_argument(
      "--collection_id",
      required=True,
      help="ID for the collection / datastore (e.g. bq_mcp_datastore).",
  )
  parser.add_argument(
      "--collection_display_name",
      default="",
      help="Display name for the collection. Defaults to collection_id if omitted.",
  )
  parser.add_argument(
      "--instance_uri",
      default="https://bigquery.googleapis.com/mcp",
      help="Target MCP server base URL (e.g. https://bigquery.googleapis.com/mcp).",
  )
  parser.add_argument(
      "--mcp_server_source",
      default="BYO_MCP",
      choices=["BYO_MCP", "BYO_MCP_INTERNAL"],
      help="Source identifier for MCP server. Default: BYO_MCP.",
  )
  parser.add_argument(
      "--client_id",
      default="849204918234-bq-mcp.apps.googleusercontent.com",
      help="OAuth Client ID.",
  )
  parser.add_argument(
      "--client_secret",
      default="dummy_secret",
      help="OAuth Client Secret.",
  )
  parser.add_argument(
      "--auth_uri",
      default="https://accounts.google.com/o/oauth2/v2/auth",
      help="OAuth authorization endpoint URL.",
  )
  parser.add_argument(
      "--token_uri",
      default="https://oauth2.googleapis.com/token",
      help="OAuth token endpoint URL.",
  )
  parser.add_argument(
      "--scopes",
      default="https://www.googleapis.com/auth/bigquery",
      help="OAuth scopes.",
  )
  parser.add_argument(
      "--endpoint_hostname",
      default="discoveryengine.googleapis.com",
      help="Discovery Engine API endpoint hostname. Default: discoveryengine.googleapis.com.",
  )
  parser.add_argument(
      "--access_token",
      default="",
      help="OAuth bearer access token for Discovery Engine API calls. If omitted, fetched via gcloud ADC.",
  )
  parser.add_argument(
      "--dry_run",
      action="store_true",
      help="Construct and display the request payload without making the API call.",
  )
  return parser.parse_args()


def get_gcloud_access_token() -> str:
  """Retrieves an access token using gcloud ADC."""
  try:
    proc = subprocess.run(
        ["gcloud", "auth", "application-default", "print-access-token"],
        capture_output=True,
        text=True,
        check=True,
        timeout=15,
    )
    token = proc.stdout.strip()
    if token:
      return token
  except Exception as e:  # pylint: disable=broad-except
    print(f"Warning: Could not fetch gcloud ADC token ({e}).", file=sys.stderr)
  return ""


def build_setup_request_payload(args: argparse.Namespace) -> Dict[str, Any]:
  """Constructs the SetUpDataConnector request body as a dictionary."""
  display_name = args.collection_display_name or args.collection_id
  parent = f"projects/{args.project}/locations/{args.location}"

  params = {
      "oauth_access_token": "dummy_value",
  }

  action_params = {
      "instance_uri": args.instance_uri,
      "mcp_server_source": args.mcp_server_source,
      "auth_uri": args.auth_uri,
      "token_uri": args.token_uri,
      "client_id": args.client_id,
      "client_secret": args.client_secret,
      "scopes": args.scopes,
  }

  payload = {
      "parent": parent,
      "collectionId": args.collection_id,
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
          "params": params,
          "actionConfig": {
              "isActionConfigured": True,
              "createBapConnection": True,
              "actionParams": action_params,
          },
      },
  }
  return payload


def send_setup_request(
    hostname: str,
    project: str,
    location: str,
    payload: Dict[str, Any],
    access_token: str,
) -> Dict[str, Any]:
  """POSTs SetUpDataConnector REST request to Discovery Engine."""
  parent = f"projects/{project}/locations/{location}"
  url = f"https://{hostname}/v1/{parent}:setUpDataConnector"

  data = json.dumps(payload).encode("utf-8")
  headers = {
      "Content-Type": "application/json",
      "x-goog-user-project": project,
  }
  if access_token:
    headers["Authorization"] = f"Bearer {access_token}"

  req = urllib.request.Request(url, data=data, headers=headers, method="POST")

  try:
    with urllib.request.urlopen(req, timeout=120) as resp:
      resp_text = resp.read().decode("utf-8")
      return json.loads(resp_text)
  except urllib.error.HTTPError as e:
    err_body = e.read().decode("utf-8")
    raise RuntimeError(
        f"HTTP Error {e.code} {e.reason}: {err_body}"
    ) from e
  except urllib.error.URLError as e:
    raise RuntimeError(f"Network error: {e.reason}") from e


def main() -> None:
  args = parse_args()

  payload = build_setup_request_payload(args)

  print("=" * 70)
  print("GEMINI ENTERPRISE BYOMCP DATASTORE PROVISIONER")
  print("=" * 70)
  print(f"Target Project   : {args.project}")
  print(f"Collection ID    : {args.collection_id}")
  print(f"Data Source Type : custom_mcp")
  print(f"MCP Server Source: {args.mcp_server_source}")
  print(f"MCP Server URL   : {args.instance_uri}")

  if args.dry_run:
    print("\n[DRY RUN MODE] Constructed SetUpDataConnectorRequest Payload:")
    print(json.dumps(payload, indent=2))
    print("\nDry run completed successfully.")
    return

  access_token = args.access_token or get_gcloud_access_token()
  if not access_token:
    print("\n[WARNING] No access token provided and gcloud ADC token unavailable.")
    print("Sending request without Authorization header (may fail unless unauthenticated endpoint).")

  print("\nSending SetUpDataConnector request...")
  try:
    response = send_setup_request(
        hostname=args.endpoint_hostname,
        project=args.project,
        location=args.location,
        payload=payload,
        access_token=access_token,
    )
    print("\n[SUCCESS] SetUpDataConnector operation submitted successfully!")
    print(json.dumps(response, indent=2))
  except Exception as e:  # pylint: disable=broad-except
    print(f"\n[ERROR] Failed to set up data connector: {e}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
  main()
