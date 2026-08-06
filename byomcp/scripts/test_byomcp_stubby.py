#!/usr/bin/env python3
"""Internal stubby test for SetUpDataConnector via LOAS / stubby."""

import sys
import os

# Add parent of google3 directory to sys.path
citc_root = "/google/src/cloud/upasanapati/implement_bq_mcp_skill"
if citc_root not in sys.path:
  sys.path.insert(0, citc_root)

from google3.google.cloud.discoveryengine.v1main import data_connector_service_pb2
from google3.cloud.ml.discoveryengine.schema import data_connector_pb2
from google3.net.rpc.python import pywraprpc
from google3.net.rpc.python import rpcutil


def main():
  project = "961872179590"  # bq-dataframes-demo / test project
  collection_id = "test_bq_mcp_stubby"
  
  target_blade = "blade:cloud-discovery-engine-esf-assistant-service-preprod"
  print(f"Connecting to DataConnectorService on {target_blade}...")

  channel = rpcutil.GetNewChannel(target_blade)
  stub = data_connector_service_pb2.DataConnectorService.NewRPC2Stub(channel=channel)

  req = data_connector_service_pb2.SetUpDataConnectorRequest()
  req.parent = f"projects/{project}/locations/global"
  req.collection_id = collection_id
  req.collection_display_name = "Test BQ MCP Stubby"

  dc = req.data_connector
  dc.data_source = "custom_mcp"
  dc.data_source_version = 1.0
  dc.connector_modes.extend([
      data_connector_pb2.DataConnector.ConnectorMode.FEDERATED,
      data_connector_pb2.DataConnector.ConnectorMode.ACTIONS,
  ])
  dc.params["mcp_server_source"] = "BYO_MCP"
  dc.params["unused_auth_param"] = "dummy_value"

  action_cfg = dc.action_config
  action_cfg.is_action_configured = True
  action_cfg.create_bap_connection = True
  action_cfg.action_params["instance_uri"] = "https://bigquery.googleapis.com/mcp"
  action_cfg.action_params["auth_uri"] = "https://accounts.google.com/o/oauth2/v2/auth"
  action_cfg.action_params["token_uri"] = "https://oauth2.googleapis.com/token"
  action_cfg.action_params["client_id"] = "test-client-id.apps.googleusercontent.com"
  action_cfg.action_params["client_secret"] = "test-client-secret"
  action_cfg.action_params["scopes"] = "https://www.googleapis.com/auth/bigquery"
  action_cfg.action_params["mcp_server_description"] = "BigQuery MCP Server connects to Google BigQuery."
  action_cfg.action_params["mcp_agent_instructions"] = "Use BigQuery tools to list datasets and run queries."

  print("Sending SetUpDataConnector stubby RPC...")
  rpc = pywraprpc.RPC()
  try:
    resp = stub.SetUpDataConnector(req, rpc=rpc)
    print("\n[SUCCESS] Response from SetUpDataConnector:")
    print(resp)
  except pywraprpc.RPCException as e:
    print(f"\nRPC Error (status code {rpc.Status()}): {e}", file=sys.stderr)


if __name__ == "__main__":
  main()
