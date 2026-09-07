"""
Agent Framework — Agent Authorization Setup Script

Creates (or verifies) the Gemini Enterprise agent_authorization resource
needed for A2UI/A2A agent integration. This is a one-time setup step
that must be done before deploying agents.

The authorization resource allows Gemini Enterprise to call your Agent Engine
agents on behalf of users via OAuth 2.0.

Usage:
    # Create auth resource using credentials from .env
    python scripts/setup_agent_auth.py

    # Check if auth resource already exists (no-op if it does)
    python scripts/setup_agent_auth.py --check

    # Force recreate (delete + create)
    python scripts/setup_agent_auth.py --force

Prerequisites:
    1. Set OAUTH_CLIENT_ID and OAUTH_CLIENT_SECRET in your .env file.
       Get these from: GCP Console → APIs & Services → Credentials → OAuth 2.0 Client IDs
    2. The OAuth client must have these redirect URIs configured:
         https://vertexaisearch.cloud.google.com/oauth-redirect
         https://vertexaisearch.cloud.google.com/static/oauth/oauth.html
    3. Set GE_LOCATION in .env to match where your Gemini Enterprise app is provisioned
       ('global', 'us', or 'eu').

After running this script, copy the printed resource name into your .env:
    AGENT_AUTHORIZATION=projects/PROJECT_NUMBER/locations/LOCATION/authorizations/agent-auth-v1
"""

import argparse
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv
from google.auth import default
from google.auth.transport.requests import Request

# =============================================================================
# SSL / Certificate handling
# =============================================================================
# On Windows corporate machines with a custom CA (e.g. Zscaler, Netskope),
# Python's requests library may fail with CERTIFICATE_VERIFY_FAILED.
# Set REQUESTS_CA_BUNDLE in your .env to the path of your corporate CA bundle,
# or set SSL_VERIFY=false to disable verification (not recommended for production).
_SSL_VERIFY: bool | str = True
_ssl_verify_env = os.environ.get("SSL_VERIFY", "").strip().lower()
if _ssl_verify_env in ("false", "0", "no"):
    _SSL_VERIFY = False
elif _ssl_verify_env:
    _SSL_VERIFY = _ssl_verify_env  # treat as path to CA bundle
elif os.environ.get("REQUESTS_CA_BUNDLE"):
    _SSL_VERIFY = os.environ.get("REQUESTS_CA_BUNDLE")

# Authorization resources are ALWAYS in the global Discovery Engine location,
# regardless of where the Gemini Enterprise app is provisioned.
_AUTH_LOCATION = "global"
_AUTH_DE_HOSTNAME = "discoveryengine.googleapis.com"

# Add project root to sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


# =============================================================================
# Helpers
# =============================================================================

def _get_bearer_token() -> str | None:
    """Gets a bearer token for authenticating with Google Cloud."""
    try:
        credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        request = Request()
        credentials.refresh(request)
        return credentials.token
    except Exception as e:
        print(f"  ✗ Error getting credentials: {e}")
        print("    Please run: gcloud auth application-default login")
        return None


def _get_de_hostname(ge_location: str) -> str:
    """Return the correct Discovery Engine API hostname for the given GE location."""
    if ge_location == "global":
        return "discoveryengine.googleapis.com"
    return f"{ge_location}-discoveryengine.googleapis.com"


def _get_project_number(project_id: str) -> str | None:
    """Resolve a project ID to its numeric project number."""
    bearer_token = _get_bearer_token()
    if not bearer_token:
        return None

    url = f"https://cloudresourcemanager.googleapis.com/v1/projects/{project_id}"
    headers = {"Authorization": f"Bearer {bearer_token}"}
    response = requests.get(url, headers=headers, verify=_SSL_VERIFY)

    if response.status_code == 200:
        return response.json().get("projectNumber")
    print(f"  ✗ Could not resolve project number for '{project_id}': {response.text}")
    return None


def _check_auth_exists(
    project_number: str,
    ge_location: str,  # kept for API compatibility but auth is always global
    auth_id: str,
    project_id: str,
) -> dict | None:
    """Check if an authorization resource already exists. Returns the resource dict or None.

    Note: Authorization resources are always in the global Discovery Engine location,
    regardless of where the Gemini Enterprise app is provisioned.
    """
    # Auth resources are always global — ignore ge_location for the auth API
    url = (
        f"https://{_AUTH_DE_HOSTNAME}/v1alpha/projects/{project_number}/"
        f"locations/{_AUTH_LOCATION}/authorizations/{auth_id}"
    )

    bearer_token = _get_bearer_token()
    if not bearer_token:
        return None

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "X-Goog-User-Project": project_id,
    }

    response = requests.get(url, headers=headers, verify=_SSL_VERIFY)
    if response.status_code == 200:
        return response.json()
    return None


def _delete_auth(
    project_number: str,
    ge_location: str,  # kept for API compatibility but auth is always global
    auth_id: str,
    project_id: str,
) -> bool:
    """Delete an existing authorization resource.

    Note: Authorization resources are always in the global Discovery Engine location.
    """
    # Auth resources are always global
    url = (
        f"https://{_AUTH_DE_HOSTNAME}/v1alpha/projects/{project_number}/"
        f"locations/{_AUTH_LOCATION}/authorizations/{auth_id}"
    )

    bearer_token = _get_bearer_token()
    if not bearer_token:
        return False

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "X-Goog-User-Project": project_id,
    }

    response = requests.delete(url, headers=headers, verify=_SSL_VERIFY)
    return response.status_code in (200, 204, 404)


def _create_auth(
    project_number: str,
    ge_location: str,  # kept for API compatibility but auth is always global
    auth_id: str,
    project_id: str,
    oauth_client_id: str,
    oauth_client_secret: str,
) -> dict | None:
    """Create a new authorization resource.

    Note: Authorization resources are always in the global Discovery Engine location,
    regardless of where the Gemini Enterprise app is provisioned.
    """
    # Auth resources are always global
    url = (
        f"https://{_AUTH_DE_HOSTNAME}/v1alpha/projects/{project_number}/"
        f"locations/{_AUTH_LOCATION}/authorizations?authorizationId={auth_id}"
    )

    # Build the authorization URI — GE requires the full OAuth2 authorization URL
    # including all required query parameters. The redirect URI must be registered
    # in the OAuth client's allowed redirect URIs in GCP Console.
    redirect_uri = "https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fstatic%2Foauth%2Foauth.html"
    authorization_uri = (
        f"https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={oauth_client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcloud-platform"
        f"&include_granted_scopes=true"
        f"&response_type=code"
        f"&access_type=offline"
        f"&prompt=consent"
    )

    payload = {
        "serverSideOauth2": {
            "clientId": oauth_client_id,
            "clientSecret": oauth_client_secret,
            "tokenUri": "https://oauth2.googleapis.com/token",
            "authorizationUri": authorization_uri,
        }
    }

    bearer_token = _get_bearer_token()
    if not bearer_token:
        return None

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
        "X-Goog-User-Project": project_id,
    }

    response = requests.post(url, headers=headers, json=payload, verify=_SSL_VERIFY)

    if response.status_code == 200:
        return response.json()

    print(f"  ✗ Failed to create authorization (HTTP {response.status_code}):")
    print(f"    {response.text}")
    return None


def _update_env_file(resource_name: str) -> bool:
    """Update the AGENT_AUTHORIZATION value in the .env file."""
    env_path = _PROJECT_ROOT / ".env"
    if not env_path.exists():
        return False

    content = env_path.read_text()
    lines = content.splitlines(keepends=True)
    updated = False
    new_lines = []

    for line in lines:
        if line.startswith("AGENT_AUTHORIZATION="):
            new_lines.append(f"AGENT_AUTHORIZATION={resource_name}\n")
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        # Add it if not present
        new_lines.append(f"AGENT_AUTHORIZATION={resource_name}\n")

    env_path.write_text("".join(new_lines))
    return True


# =============================================================================
# Main
# =============================================================================

def main():
    load_dotenv(_PROJECT_ROOT / ".env")

    parser = argparse.ArgumentParser(
        description="Agent Framework — Create Gemini Enterprise agent_authorization resource",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/setup_agent_auth.py              # Create auth (skip if exists)
  python scripts/setup_agent_auth.py --check      # Only check if it exists
  python scripts/setup_agent_auth.py --force      # Delete and recreate
  python scripts/setup_agent_auth.py --id my-auth # Use a custom authorization ID
        """,
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only check if the authorization resource exists, don't create it",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Delete existing authorization and recreate it",
    )
    parser.add_argument(
        "--id",
        default="agent-auth-v1",
        dest="auth_id",
        help="Authorization resource ID (default: agent-auth-v1)",
    )
    parser.add_argument(
        "--no-update-env",
        action="store_true",
        help="Don't automatically update AGENT_AUTHORIZATION in .env",
    )

    args = parser.parse_args()

    # Read config from env
    project_id = os.environ.get("PROJECT_ID")
    ge_location = os.environ.get("GE_LOCATION", "global")
    oauth_client_id = os.environ.get("OAUTH_CLIENT_ID")
    oauth_client_secret = os.environ.get("OAUTH_CLIENT_SECRET")

    print()
    print("=" * 70)
    print("  Agent Framework — Agent Authorization Setup")
    print("=" * 70)
    print(f"  Project ID:   {project_id}")
    print(f"  GE Location:  {ge_location}")
    print(f"  Auth ID:      {args.auth_id}")
    print("=" * 70)
    print()

    # Validate required env vars
    if not project_id:
        print("✗ PROJECT_ID is not set in .env")
        sys.exit(1)

    if not args.check and not oauth_client_id:
        print("✗ OAUTH_CLIENT_ID is not set in .env")
        print("  Get it from: GCP Console → APIs & Services → Credentials → OAuth 2.0 Client IDs")
        print("  Then add to .env: OAUTH_CLIENT_ID=YOUR_CLIENT_ID")
        sys.exit(1)

    if not args.check and not oauth_client_secret:
        print("✗ OAUTH_CLIENT_SECRET is not set in .env")
        print("  Get it from: GCP Console → APIs & Services → Credentials → OAuth 2.0 Client IDs")
        print("  Then add to .env: OAUTH_CLIENT_SECRET=YOUR_CLIENT_SECRET")
        sys.exit(1)

    # Resolve project number
    print("  ⏳ Resolving project number...")
    project_number = _get_project_number(project_id)
    if not project_number:
        print(f"  ✗ Could not resolve project number for '{project_id}'")
        print("    Make sure you're authenticated: gcloud auth application-default login")
        sys.exit(1)
    print(f"  ✓ Project number: {project_number}")
    print()

    # Check if auth already exists
    print(f"  ⏳ Checking if authorization '{args.auth_id}' exists...")
    existing = _check_auth_exists(project_number, ge_location, args.auth_id, project_id)

    if existing:
        resource_name = existing.get("name", f"projects/{project_number}/locations/{ge_location}/authorizations/{args.auth_id}")
        print(f"  ✓ Authorization resource already exists:")
        print(f"    {resource_name}")
        print()

        if args.check:
            print("  ℹ --check mode: no changes made.")
            print()
            print(f"  Add this to your .env:")
            print(f"    AGENT_AUTHORIZATION={resource_name}")
            print()
            sys.exit(0)

        if not args.force:
            print("  ℹ Already exists — skipping creation. Use --force to recreate.")
            print()
            if not args.no_update_env:
                if _update_env_file(resource_name):
                    print(f"  ✓ Updated AGENT_AUTHORIZATION in .env")
                else:
                    print(f"  ℹ Add this to your .env manually:")
                    print(f"    AGENT_AUTHORIZATION={resource_name}")
            print()
            sys.exit(0)

        # --force: delete and recreate
        print(f"  ⏳ --force: deleting existing authorization...")
        if _delete_auth(project_number, ge_location, args.auth_id, project_id):
            print(f"  ✓ Deleted existing authorization")
        else:
            print(f"  ✗ Failed to delete existing authorization")
            sys.exit(1)
        print()
    else:
        print(f"  ℹ Authorization does not exist yet — will create it.")
        print()

        if args.check:
            print("  ✗ Authorization resource not found.")
            print(f"    Run without --check to create it.")
            print()
            sys.exit(1)

    # Create the authorization resource
    print(f"  ⏳ Creating authorization resource '{args.auth_id}'...")
    print(f"     OAuth Client ID: {oauth_client_id[:20]}...")
    result = _create_auth(
        project_number=project_number,
        ge_location=ge_location,
        auth_id=args.auth_id,
        project_id=project_id,
        oauth_client_id=oauth_client_id,
        oauth_client_secret=oauth_client_secret,
    )

    if not result:
        print()
        print("  ✗ Failed to create authorization resource.")
        print()
        print("  Common causes:")
        print("    • OAuth client doesn't have the required redirect URIs:")
        print("        https://vertexaisearch.cloud.google.com/oauth-redirect")
        print("        https://vertexaisearch.cloud.google.com/static/oauth/oauth.html")
        print("    • Discovery Engine API not enabled in this project")
        print("    • Insufficient permissions (need roles/discoveryengine.admin)")
        sys.exit(1)

    resource_name = result.get("name", f"projects/{project_number}/locations/{ge_location}/authorizations/{args.auth_id}")

    print()
    print("  ✓ Authorization resource created successfully!")
    print()
    print(f"  Resource name: {resource_name}")
    print()

    # Update .env
    if not args.no_update_env:
        if _update_env_file(resource_name):
            print(f"  ✓ Automatically updated AGENT_AUTHORIZATION in .env")
        else:
            print(f"  ℹ .env not found — add this manually:")
            print(f"    AGENT_AUTHORIZATION={resource_name}")
    else:
        print(f"  ℹ Add this to your .env:")
        print(f"    AGENT_AUTHORIZATION={resource_name}")

    print()
    print("  Next steps:")
    print("    1. Verify the OAuth client has the required redirect URIs in GCP Console")
    print("    2. Run: python scripts/deploy.py employee_verification")
    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
