#!/usr/bin/env python3
"""End-to-End Programmatic Workflow for BigQuery BYOMCP in Gemini Enterprise.

This script demonstrates how external customers and developers can programmatically:
1. Provision a custom_mcp (BYOMCP) datastore for BigQuery MCP via REST API.
2. Query the Gemini Enterprise agent programmatically via StreamAssist REST API.
"""

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, Optional


class GeminiEnterpriseClient:
  """Client for programmatic Gemini Enterprise DataConnector and Assistant APIs."""

  def __init__(
      self,
      project_id: str,
      location: str = "global",
      access_token: Optional[str] = None,
      hostname: str = "discoveryengine.googleapis.com",
  ):
    self.project_id = project_id
    self.location = location
    self.hostname = hostname
    self.access_token = access_token or self._get_adc_access_token()

  def _get_adc_access_token(self) -> str:
    """Gets access token via gcloud application-default print-access-token."""
    try:
      proc = subprocess.run(
          ["gcloud", "auth", "application-default", "print-access-token"],
          capture_output=True,
          text=True,
          check=True,
          timeout=15,
      )
      return proc.stdout.strip()
    except Exception as e:  # pylint: disable=broad-except
      print(f"Notice: ADC token retrieval: {e}", file=sys.stderr)
      return ""

  def _headers(self) -> Dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "x-goog-user-project": self.project_id,
    }
    if self.access_token:
      headers["Authorization"] = f"Bearer {self.access_token}"
    return headers

  def setup_byomcp_datastore(
      self,
      collection_id: str,
      instance_uri: str,
      client_id: str,
      client_secret: str,
      collection_display_name: Optional[str] = None,
      auth_uri: str = "https://accounts.google.com/o/oauth2/v2/auth",
      token_uri: str = "https://oauth2.googleapis.com/token",
      scopes: str = "https://www.googleapis.com/auth/bigquery",
      mcp_server_source: str = "BYO_MCP",
      mcp_server_description: str = "BigQuery MCP Server connects to Google BigQuery.",
      mcp_agent_instructions: str = "Use BigQuery tools to list datasets, inspect schemas, and query tables.",
      dry_run: bool = False,
  ) -> Dict[str, Any]:
    """Programmatically provisions a custom_mcp (BYOMCP) datastore."""
    parent = f"projects/{self.project_id}/locations/{self.location}"
    url = f"https://{self.hostname}/v1/{parent}:setUpDataConnector"

    payload = {
        "parent": parent,
        "collectionId": collection_id,
        "collectionDisplayName": collection_display_name or collection_id,
        "dataConnector": {
            "dataSource": "custom_mcp",
            "dataSourceVersion": 1.0,
            "connectorModes": ["FEDERATED", "ACTIONS"],
            "params": {
                "mcp_server_source": mcp_server_source,
                "unused_auth_param": "dummy_value",
            },
            "actionConfig": {
                "isActionConfigured": True,
                "createBapConnection": True,
                "actionParams": {
                    "instance_uri": instance_uri,
                    "auth_uri": auth_uri,
                    "token_uri": token_uri,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "scopes": scopes,
                    "mcp_server_description": mcp_server_description,
                    "mcp_agent_instructions": mcp_agent_instructions,
                },
            },
        },
    }

    if dry_run:
      print("[DRY RUN] SetUpDataConnector Payload:")
      print(json.dumps(payload, indent=2))
      return payload

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=self._headers(), method="POST")

    try:
      with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
      raise RuntimeError(f"HTTP Error {e.code}: {e.read().decode('utf-8')}") from e

  def stream_assist_query(
      self,
      engine_id: str,
      prompt: str,
  ) -> Dict[str, Any]:
    """Programmatically sends a query to the Gemini Enterprise Assistant API."""
    url = f"https://{self.hostname}/v1/projects/{self.project_id}/locations/{self.location}/collections/default/engines/{engine_id}:streamAssist"

    payload = {
        "query": {
            "text": prompt
        }
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=self._headers(), method="POST")

    try:
      with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
      raise RuntimeError(f"HTTP Error {e.code}: {e.read().decode('utf-8')}") from e


def main():
  import argparse
  parser = argparse.ArgumentParser(description="Programmatic BigQuery BYOMCP Pipeline")
  parser.add_argument("--project", required=True, help="GCP Project ID")
  parser.add_argument("--collection_id", default="bq_mcp_datastore", help="Collection ID")
  parser.add_argument("--client_id", default="YOUR_CLIENT_ID", help="OAuth Client ID")
  parser.add_argument("--client_secret", default="YOUR_CLIENT_SECRET", help="OAuth Client Secret")
  parser.add_argument("--dry_run", action="store_true", help="Print payloads without executing")
  args = parser.parse_args()

  client = GeminiEnterpriseClient(project_id=args.project)

  print("1. Programmatically setting up BYOMCP BigQuery DataConnector...")
  response = client.setup_byomcp_datastore(
      collection_id=args.collection_id,
      instance_uri="https://bigquery.googleapis.com/mcp",
      client_id=args.client_id,
      client_secret=args.client_secret,
      dry_run=args.dry_run,
  )
  print(json.dumps(response, indent=2))


if __name__ == "__main__":
  main()
