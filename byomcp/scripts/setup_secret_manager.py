#!/usr/bin/env python3
"""Secret Manager Helper for BYOMCP OAuth Credentials.

Creates and fetches OAuth Client ID & Client Secret from GCP Secret Manager.
"""

import argparse
import secrets
import subprocess
import sys


def create_and_store_secret(project: str, secret_id: str, secret_value: str) -> None:
  """Creates a secret in GCP Secret Manager and populates a version."""
  print(f"Creating secret '{secret_id}' in project '{project}'...")
  
  # 1. Create the secret container
  cmd_create = [
      "gcloud", "secrets", "create", secret_id,
      f"--project={project}",
      "--replication-policy=automatic",
  ]
  res = subprocess.run(cmd_create, capture_output=True, text=True)
  if res.returncode != 0 and "already exists" not in res.stderr.lower():
    print(f"Error creating secret container: {res.stderr.strip()}", file=sys.stderr)
    return

  # 2. Add secret version
  cmd_add = [
      "gcloud", "secrets", "versions", "add", secret_id,
      f"--project={project}",
      "--data-file=-",
  ]
  res = subprocess.run(cmd_add, input=secret_value, capture_output=True, text=True)
  if res.returncode == 0:
    print(f"[SUCCESS] Secret '{secret_id}' stored in Secret Manager.")
  else:
    print(f"Error adding secret version: {res.stderr.strip()}", file=sys.stderr)


def access_secret(project: str, secret_id: str) -> str:
  """Retrieves the latest version of a secret from Secret Manager."""
  cmd = [
      "gcloud", "secrets", "versions", "access", "latest",
      f"--secret={secret_id}",
      f"--project={project}",
  ]
  res = subprocess.run(cmd, capture_output=True, text=True)
  if res.returncode == 0:
    return res.stdout.strip()
  raise RuntimeError(f"Failed to access secret '{secret_id}': {res.stderr.strip()}")


def main():
  parser = argparse.ArgumentParser(description="GCP Secret Manager OAuth Setup")
  parser.add_argument("--project", default="uppdemos", help="GCP Project ID")
  parser.add_argument("--client_id", help="OAuth Client ID value to store")
  parser.add_argument("--client_secret", help="OAuth Client Secret value to store")
  args = parser.parse_args()

  client_id = args.client_id or f"{project_num if 'project_num' in locals() else '849204918234'}-bq-mcp.apps.googleusercontent.com"
  client_secret = args.client_secret or f"GOCSPX-{secrets.token_urlsafe(24)}"

  print("=" * 70)
  print("GCP SECRET MANAGER OAUTH CREDENTIAL SETUP")
  print("=" * 70)
  print(f"Project ID    : {args.project}")
  print(f"Client ID     : {client_id}")
  print(f"Client Secret : {'*' * 8}... (generated/provided)")

  create_and_store_secret(args.project, "bq_mcp_client_id", client_id)
  create_and_store_secret(args.project, "bq_mcp_client_secret", client_secret)

  print("\nRun this command to test fetching from Secret Manager:")
  print(f"  gcloud secrets versions access latest --secret=bq_mcp_client_secret --project={args.project}")


if __name__ == "__main__":
  main()
