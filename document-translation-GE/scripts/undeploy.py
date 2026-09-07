"""
Agent Framework — Undeploy Script

Removes agents from Gemini Enterprise and provides guidance for Agent Engine cleanup.

Usage:
    # Undeploy a single agent
    python scripts/undeploy.py employee_verification

    # Undeploy multiple agents
    python scripts/undeploy.py employee_verification benefits_enrollment

    # Undeploy ALL agents
    python scripts/undeploy.py --all

    # List deployed agents (from config)
    python scripts/undeploy.py --list
"""

import argparse
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv
from google.auth import default
from google.auth.transport.requests import Request

# Add project root to sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from agents._base.config_loader import load_agent_config, list_available_agents


def _get_bearer_token() -> str | None:
    """Gets a bearer token for authenticating with Google Cloud."""
    try:
        credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        request = Request()
        credentials.refresh(request)
        return credentials.token
    except Exception as e:
        print(f"  ✗ Error getting credentials: {e}")
        return None


def _get_de_hostname(ge_location: str) -> str:
    """Return the correct Discovery Engine API hostname for the given GE location."""
    if ge_location == "global":
        return "discoveryengine.googleapis.com"
    return f"{ge_location}-discoveryengine.googleapis.com"


def _list_ge_agents(project_id: str, app_id: str, ge_location: str = "global") -> list[dict]:
    """List agents registered in Gemini Enterprise."""
    de_hostname = _get_de_hostname(ge_location)
    api_endpoint = (
        f"https://{de_hostname}/v1alpha/projects/{project_id}/"
        f"locations/{ge_location}/collections/default_collection/engines/{app_id}/"
        "assistants/default_assistant/agents"
    )

    bearer_token = _get_bearer_token()
    if not bearer_token:
        return []

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
        "X-Goog-User-Project": project_id,
    }

    response = requests.get(api_endpoint, headers=headers)
    if response.status_code == 200:
        return response.json().get("agents", [])
    return []


def _unregister_agent(project_id: str, app_id: str, agent_name: str, ge_location: str = "global") -> bool:
    """Unregister an agent from Gemini Enterprise."""
    de_hostname = _get_de_hostname(ge_location)
    api_endpoint = (
        f"https://{de_hostname}/v1alpha/projects/{project_id}/"
        f"locations/{ge_location}/collections/default_collection/engines/{app_id}/"
        f"assistants/default_assistant/agents/{agent_name}"
    )

    bearer_token = _get_bearer_token()
    if not bearer_token:
        return False

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
        "X-Goog-User-Project": project_id,
    }

    response = requests.delete(api_endpoint, headers=headers)
    return response.status_code in (200, 204, 404)


def undeploy_agent(agent_name: str, project_id: str, app_id: str, location: str, ge_location: str = "global") -> bool:
    """Undeploy a single agent."""
    print(f"  ⏳ Unregistering '{agent_name}_agent' from Gemini Enterprise...")

    success = _unregister_agent(
        project_id=project_id,
        app_id=app_id,
        agent_name=f"{agent_name}_agent",
        ge_location=ge_location,
    )

    if success:
        print(f"  ✓ Unregistered from Gemini Enterprise")
    else:
        print(f"  ✗ Failed to unregister from Gemini Enterprise")

    # Provide Agent Engine cleanup guidance
    print(f"  ℹ To also delete the Agent Engine resource:")
    print(f"    gcloud ai reasoning-engines list --region={location} --format='table(name,displayName)'")
    print(f"    gcloud ai reasoning-engines delete <RESOURCE_ID> --region={location}")

    return success


def main():
    load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))

    parser = argparse.ArgumentParser(
        description="Agent Framework — Undeploy agents from Gemini Enterprise",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/undeploy.py employee_verification        # Undeploy one agent
  python scripts/undeploy.py agent1 agent2                # Undeploy multiple
  python scripts/undeploy.py --all                        # Undeploy all agents
  python scripts/undeploy.py --list                       # List registered agents
        """,
    )

    parser.add_argument(
        "agents",
        nargs="*",
        help="Agent name(s) to undeploy (matches config/<name>.yaml)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Undeploy all agents found in config/",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List agents currently registered in Gemini Enterprise",
    )

    args = parser.parse_args()

    project_id = os.environ.get("PROJECT_ID")
    app_id = os.environ.get("GEMINI_ENTERPRISE_APP_ID")
    location = os.environ.get("LOCATION", "us-central1")

    # --list: show registered agents
    if args.list:
        print("=" * 60)
        print("  Agent Framework — Registered in Gemini Enterprise")
        print("=" * 60)
        agents = _list_ge_agents(project_id, app_id)
        if not agents:
            print("  No agents found (or API error)")
        else:
            for agent in agents:
                name = agent.get("name", "?")
                display = agent.get("displayName", "?")
                print(f"  • {name} ({display})")
        print("=" * 60)
        return

    # Determine agents
    if args.all:
        agent_names = list_available_agents()
        if not agent_names:
            print("✗ No agent configs found in config/")
            sys.exit(1)
    elif args.agents:
        agent_names = args.agents
    else:
        parser.print_help()
        sys.exit(1)

    # Header
    print()
    print("=" * 80)
    print(f"  Agent Framework — Undeploy")
    print(f"  Project: {project_id} | Region: {location}")
    print("=" * 80)
    print()

    # Process
    results = {}
    total = len(agent_names)

    ge_location = os.environ.get("GE_LOCATION", "global")

    for idx, agent_name in enumerate(agent_names, 1):
        print(f"[{idx}/{total}] Undeploying: {agent_name}")
        success = undeploy_agent(agent_name, project_id, app_id, location, ge_location=ge_location)
        results[agent_name] = success
        print()

    # Summary
    succeeded = sum(1 for v in results.values() if v)
    failed = total - succeeded

    print("=" * 80)
    if failed == 0:
        print(f"  ✓ {succeeded}/{total} agents undeployed successfully")
    else:
        print(f"  ⚠ {succeeded}/{total} succeeded, {failed}/{total} failed")
        for name, success in results.items():
            status = "✓" if success else "✗"
            print(f"    {status} {name}")
    print("=" * 80)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
