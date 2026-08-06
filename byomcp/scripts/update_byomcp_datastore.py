#!/usr/bin/env python3
"""Update existing Bring-Your-Own-MCP (custom_mcp) datastore with real OAuth credentials."""

import argparse
import json
import sys
import urllib.error
import urllib.request
from typing import Any, Dict


def update_data_connector(
    project: str,
    location: str,
    collection_id: str,
    client_id: str,
    client_secret: str,
    access_token: str,
    hostname: str = "discoveryengine.googleapis.com",
) -> Dict[str, Any]:
  """PATCHs UpdateDataConnector REST request to update OAuth credentials."""
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
              "instance_uri": "https://bigquery.googleapis.com/mcp",
              "mcp_server_source": "BYO_MCP",
              "auth_uri": "https://accounts.google.com/o/oauth2/v2/auth",
              "token_uri": "https://oauth2.googleapis.com/token",
              "client_id": client_id,
              "client_secret": client_secret,
              "scopes": "https://www.googleapis.com/auth/bigquery",
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
  parser = argparse.ArgumentParser(description="Update custom_mcp OAuth credentials")
  parser.add_argument("--project", default="uppdemos")
  parser.add_argument("--location", default="global")
  parser.add_argument("--collection_id", default="bigquery_mcp_datastore_v2")
  parser.add_argument("--client_id", required=True)
  parser.add_argument("--client_secret", required=True)
  parser.add_argument("--access_token", required=True)
  args = parser.parse_args()

  print("=" * 70)
  print("UPDATING BYOMCP DATASTORE OAUTH CREDENTIALS")
  print("=" * 70)
  print(f"Target Collection : {args.collection_id}")
  print(f"Client ID         : {args.client_id}")

  try:
    resp = update_data_connector(
        project=args.project,
        location=args.location,
        collection_id=args.collection_id,
        client_id=args.client_id,
        client_secret=args.client_secret,
        access_token=args.access_token,
    )
    print("\n[SUCCESS] DataConnector successfully updated with real OAuth credentials!")
    print(json.dumps(resp, indent=2))
  except Exception as e:
    print(f"\n[ERROR] Failed to update data connector: {e}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
  main()
