"""
Agent Framework — Generic Deployment Script

Deploys one or more agents to Agent Engine and registers them in Gemini Enterprise.
All agent configuration is read from YAML files in config/.

Usage:
    # Deploy a single agent
    python scripts/deploy.py employee_verification

    # Deploy multiple specific agents
    python scripts/deploy.py employee_verification benefits_enrollment

    # Deploy ALL agents (every YAML in config/)
    python scripts/deploy.py --all

    # List available agents
    python scripts/deploy.py --list

    # Dry run — show what would be deployed
    python scripts/deploy.py employee_verification --dry-run

    # Undeploy an agent from Agent Engine
    python scripts/deploy.py employee_verification --undeploy
"""

import argparse
import importlib
import json
import os
import sys
import time
from pathlib import Path

import httpx
import requests
import urllib3
import vertexai
from a2a.types import AgentSkill
from dotenv import load_dotenv
from google.auth import default
from google.auth.transport.requests import Request
from google.genai import types
from vertexai.preview.reasoning_engines import A2aAgent
from vertexai.preview.reasoning_engines.templates.a2a import create_agent_card

# Add project root to sys.path so we can import agents/tools
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from agents._base.config_loader import load_agent_config, list_available_agents

# Import setup_agent_auth helpers inline to avoid circular imports
from scripts.setup_agent_auth import (
    _get_project_number,
    _check_auth_exists,
    _create_auth,
    _update_env_file,
    _SSL_VERIFY,
)

# Suppress InsecureRequestWarning when SSL verification is disabled
if _SSL_VERIFY is False:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


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
    """Return the correct Discovery Engine API hostname for the given GE location.

    Args:
        ge_location: The Gemini Enterprise region ('global', 'us', 'eu', etc.)

    Returns:
        The correct API hostname string.
    """
    if ge_location == "global":
        return "discoveryengine.googleapis.com"
    return f"{ge_location}-discoveryengine.googleapis.com"


def _register_agent_on_gemini_enterprise(
    project_id: str,
    app_id: str,
    agent_card: str,
    agent_name: str,
    display_name: str,
    description: str,
    agent_authorization: str | None = None,
    ge_location: str = "global",
) -> dict | None:
    """Register an Agent Engine agent in Gemini Enterprise."""
    de_hostname = _get_de_hostname(ge_location)
    api_endpoint = (
        f"https://{de_hostname}/v1alpha/projects/{project_id}/"
        f"locations/{ge_location}/collections/default_collection/engines/{app_id}/"
        "assistants/default_assistant/agents"
    )

    payload = {
        "name": agent_name,
        "displayName": display_name,
        "description": description,
        "a2aAgentDefinition": {"jsonAgentCard": agent_card},
    }

    if agent_authorization:
        payload["authorization_config"] = {"agent_authorization": agent_authorization}

    bearer_token = _get_bearer_token()
    if not bearer_token:
        return None

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
        "X-Goog-User-Project": project_id,
    }

    response = requests.post(api_endpoint, headers=headers, json=payload, verify=_SSL_VERIFY)

    if response.status_code == 200:
        return response.json()

    # Log the full error for debugging — always show the complete response body
    print(f"  ✗ GE registration failed (HTTP {response.status_code})")
    print(f"    URL: {api_endpoint}")
    print(f"    Response: {response.text}")
    if agent_authorization:
        print(f"    Auth resource used: {agent_authorization}")
    return None


def _set_agent_access_policy(
    project_id: str,
    app_id: str,
    agent_name: str,
    access_policy: str = "ALL_USERS",
    ge_location: str = "global",
) -> bool:
    """Set the access policy for a registered GE agent (who can see/use it).

    Args:
        project_id: GCP project ID.
        app_id: Gemini Enterprise app ID.
        agent_name: The agent name as registered in GE (e.g. 'employee_verification_agent').
        access_policy: 'ALL_USERS' (visible to all org users) or 'ADMINS_ONLY' (default in GE).
        ge_location: GE app region ('global', 'us', 'eu').

    Returns:
        True if successful, False otherwise.
    """
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

    payload = {"sharingConfig": {"scope": access_policy}}
    params = {"updateMask": "sharingConfig"}

    response = requests.patch(
        api_endpoint, headers=headers, json=payload, params=params, verify=_SSL_VERIFY
    )

    if response.status_code == 200:
        return True

    print(f"  ⚠ Could not set access policy (HTTP {response.status_code}): {response.text}")
    return False


def _unregister_agent_from_gemini_enterprise(
    project_id: str,
    app_id: str,
    agent_name: str,
    ge_location: str = "global",
) -> bool:
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

    response = requests.delete(api_endpoint, headers=headers, verify=_SSL_VERIFY)
    return response.status_code in (200, 204, 404)


# =============================================================================
# Deploy / Undeploy a single agent
# =============================================================================

def deploy_agent(agent_name: str, dry_run: bool = False) -> bool:
    """Deploy a single agent to Agent Engine and register in Gemini Enterprise.

    Args:
        agent_name: Name matching config/<agent_name>.yaml
        dry_run: If True, just print config without deploying.

    Returns:
        True if successful, False otherwise.
    """
    # Load config
    try:
        config = load_agent_config(agent_name)
    except FileNotFoundError as e:
        print(f"  ✗ {e}")
        return False

    agent_cfg = config.get("agent", {})
    deploy_cfg = config.get("deploy", {})

    model = agent_cfg.get("model", os.environ.get("GOOGLE_GENAI_MODEL", "gemini-2.5-flash"))
    display_name = agent_cfg.get("display_name", agent_name)
    description = agent_cfg.get("description", "")
    tool_paths = agent_cfg.get("tools", [])
    skills_cfg = deploy_cfg.get("skills", [])

    # Environment
    project_id = os.environ.get("PROJECT_ID")
    location = deploy_cfg.get("region", os.environ.get("LOCATION", "us-central1"))
    storage = os.environ.get("STORAGE_BUCKET")
    app_id = os.environ.get("GEMINI_ENTERPRISE_APP_ID")
    api_endpoint = f"{location}-aiplatform.googleapis.com"
    api_version = deploy_cfg.get("api_version", "v1beta1")

    print(f"  ├── Model: {model}")
    print(f"  ├── Tools: {len(tool_paths)} tools")
    print(f"  ├── Skills: {len(skills_cfg)} skills defined")

    if dry_run:
        print(f"  ├── Region: {location}")
        print(f"  ├── Display Name: {display_name}")
        print(f"  ├── Description: {description[:80]}...")
        print(f"  ├── Tool paths:")
        for tp in tool_paths:
            print(f"  │   - {tp}")
        print(f"  ├── Skills:")
        for s in skills_cfg:
            print(f"  │   - {s.get('name', s.get('id', '?'))}")
        print(f"  └── 🔍 DRY RUN — nothing deployed")
        return True

    # Initialize Vertex AI
    vertexai.init(
        project=project_id,
        location=location,
        api_endpoint=api_endpoint,
        staging_bucket=storage,
    )

    client = vertexai.Client(
        project=project_id,
        location=location,
        http_options=types.HttpOptions(api_version=api_version),
    )

    # Build skills from config
    skills = []
    for skill_def in skills_cfg:
        skills.append(AgentSkill(
            id=skill_def.get("id", ""),
            name=skill_def.get("name", ""),
            description=skill_def.get("description", ""),
            tags=skill_def.get("tags", []),
            examples=skill_def.get("examples", []),
        ))

    # Default I/O modes
    defaults = config.get("deploy", {})
    input_modes = defaults.get("default_input_modes", ["text/plain"])
    output_modes = defaults.get("default_output_modes", ["text/plain"])

    # Create agent card
    agent_card = create_agent_card(
        agent_name=display_name,
        description=description,
        skills=skills,
        default_input_modes=input_modes,
        default_output_modes=output_modes,
    )

    # Dynamically import the executor class
    executor_module_path = f"agents.{agent_name}.executor"
    try:
        executor_module = importlib.import_module(executor_module_path)
    except ImportError as e:
        print(f"  ✗ Could not import executor from {executor_module_path}: {e}")
        return False

    # Find the executor class (first AgentExecutor subclass in the module)
    # Supports both BaseA2UIExecutor subclasses (have AGENT_CONFIG_NAME) and
    # standalone executors like AuditIssueTrackerExecutor (have no AGENT_CONFIG_NAME).
    executor_class = None
    from a2a.server.agent_execution import AgentExecutor as _AgentExecutor
    for attr_name in dir(executor_module):
        attr = getattr(executor_module, attr_name)
        if (
            isinstance(attr, type)
            and issubclass(attr, _AgentExecutor)
            and attr is not _AgentExecutor
            and attr_name not in ("BaseA2UIExecutor", "AgentExecutor")
        ):
            executor_class = attr
            break

    if executor_class is None:
        print(f"  ✗ No executor class found in {executor_module_path}")
        return False

    # Create A2aAgent
    a2a_agent = A2aAgent(
        agent_card=agent_card,
        agent_executor_builder=executor_class,
    )
    a2a_agent.set_up()

    # Build requirements
    base_reqs = config.get("deploy", {}).get("base_requirements", [])
    extra_reqs = deploy_cfg.get("extra_requirements", [])
    all_requirements = base_reqs + extra_reqs

    # Build extra packages
    extra_packages = deploy_cfg.get("extra_packages", [])

    # Build env vars
    env_vars = deploy_cfg.get("env_vars", {})
    env_vars["PROJECT_ID"] = project_id

    # Deploy config
    deploy_config = {
        "display_name": f"{agent_name}_agent",
        "description": description,
        "agent_framework": deploy_cfg.get("agent_framework", "google-adk"),
        "staging_bucket": storage,
        "gcs_dir_name": agent_name,
        "requirements": all_requirements,
        "http_options": {"api_version": api_version},
        "max_instances": deploy_cfg.get("max_instances", 1),
        "extra_packages": extra_packages,
        "env_vars": env_vars,
    }

    print(f"  ⏳ Deploying to Agent Engine...")
    start_time = time.time()

    try:
        remote_agent = client.agent_engines.create(agent=a2a_agent, config=deploy_config)
    except Exception as e:
        print(f"  ✗ Deployment failed: {e}")
        return False

    elapsed = time.time() - start_time
    remote_engine_resource = remote_agent.api_resource.name
    print(f"  ✓ Deployed: {remote_engine_resource} ({elapsed:.0f}s)")

    # Fetch A2A card from deployed agent
    a2a_endpoint = f"https://{api_endpoint}/{api_version}/{remote_engine_resource}/a2a/v1/card"
    bearer_token = _get_bearer_token()
    if not bearer_token:
        print(f"  ✗ Could not get bearer token for card fetch")
        return False

    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
    }

    try:
        # Use verify=False for httpx if SSL verification is disabled
        httpx_verify = False if _SSL_VERIFY is False else True
        response = httpx.get(a2a_endpoint, headers=headers, verify=httpx_verify)
        response.raise_for_status()
        a2ui_agent_card_json = response.json()
    except Exception as e:
        print(f"  ✗ Could not fetch A2A card: {e}")
        return False

    # Add A2UI capabilities
    a2ui_cfg = agent_cfg.get("a2ui", {})
    extension_uri = a2ui_cfg.get(
        "extension_uri", "https://a2ui.org/a2a-extension/a2ui/v0.8"
    )
    catalog_url = a2ui_cfg.get(
        "catalog_url",
        "https://a2ui.org/specification/v0_8/standard_catalog_definition.json",
    )

    ge_custom_catalog = "https://vertexaisearch.cloud.google.com/a2ui/v0_8/gemini_enterprise_custom_catalog.json"
    supported_catalogs = [catalog_url]
    if ge_custom_catalog not in supported_catalogs:
        supported_catalogs.append(ge_custom_catalog)

    a2ui_agent_card_json["capabilities"] = {
        "streaming": False,
        "extensions": [{
            "uri": extension_uri,
            "description": "Ability to render A2UI",
            "required": False,
            "params": {
                "supportedCatalogIds": supported_catalogs
            },
        }],
    }
    a2ui_agent_card_str = json.dumps(a2ui_agent_card_json)

    # -------------------------------------------------------------------------
    # Resolve per-agent authorization resource
    # -------------------------------------------------------------------------
    ge_location = os.environ.get("GE_LOCATION", "global")
    agent_authorization = None

    # Check for per-agent auth ID in config (preferred pattern)
    auth_id = deploy_cfg.get("agent_authorization_id")
    if auth_id:
        project_number = _get_project_number(project_id)
        if project_number:
            existing = _check_auth_exists(project_number, ge_location, auth_id, project_id)
            if existing:
                agent_authorization = existing.get(
                    "name",
                    f"projects/{project_number}/locations/global/authorizations/{auth_id}"
                )
                print(f"  ✓ Auth resource exists: {agent_authorization}")
            else:
                oauth_client_id = os.environ.get("OAUTH_CLIENT_ID")
                oauth_client_secret = os.environ.get("OAUTH_CLIENT_SECRET")
                if oauth_client_id and oauth_client_secret:
                    print(f"  ⏳ Creating auth resource '{auth_id}'...")
                    result_auth = _create_auth(
                        project_number=project_number,
                        ge_location=ge_location,
                        auth_id=auth_id,
                        project_id=project_id,
                        oauth_client_id=oauth_client_id,
                        oauth_client_secret=oauth_client_secret,
                    )
                    if result_auth:
                        agent_authorization = result_auth.get(
                            "name",
                            f"projects/{project_number}/locations/global/authorizations/{auth_id}"
                        )
                        print(f"  ✓ Created auth resource: {agent_authorization}")
                    else:
                        print(f"  ✗ Could not create auth resource '{auth_id}' — GE registration will fail without OAuth")
                else:
                    print(f"  ⚠ Missing OAUTH_CLIENT_ID/SECRET — cannot create auth resource '{auth_id}'")
        else:
            print(f"  ⚠ Missing project number — skipping auth resource resolution")
    else:
        # Fallback to global AGENT_AUTHORIZATION env var
        agent_authorization = os.environ.get("AGENT_AUTHORIZATION")

    # -------------------------------------------------------------------------
    # Delete any existing GE registration for this agent before re-registering
    # This ensures we always register with the correct (latest) auth resource
    # -------------------------------------------------------------------------
    print(f"  ⏳ Removing any existing GE registration for '{agent_name}_agent'...")
    _unregister_agent_from_gemini_enterprise(
        project_id=project_id,
        app_id=app_id,
        agent_name=f"{agent_name}_agent",
        ge_location=ge_location,
    )

    # Register in Gemini Enterprise
    result = _register_agent_on_gemini_enterprise(
        project_id=project_id,
        app_id=app_id,
        agent_card=a2ui_agent_card_str,
        agent_name=f"{agent_name}_agent",
        display_name=display_name,
        description=description,
        agent_authorization=agent_authorization,
        ge_location=ge_location,
    )

    if result:
        print(f"  ✓ Registered in Gemini Enterprise")

        # Set access policy — who can see and use this agent in GE
        # Default: ALL_USERS (visible to everyone in the org)
        # Override per-agent in config YAML: deploy.ge_access_policy: "ADMINS_ONLY"
        access_policy = deploy_cfg.get("ge_access_policy", "ALL_USERS")
        print(f"  ⏳ Setting access policy to '{access_policy}'...")
        if _set_agent_access_policy(
            project_id=project_id,
            app_id=app_id,
            agent_name=f"{agent_name}_agent",
            access_policy=access_policy,
            ge_location=ge_location,
        ):
            print(f"  ✓ Access policy set to '{access_policy}' — agent is visible to all org users")
        else:
            print(f"  ⚠ Could not set access policy — you may need to enable the agent manually in the GE console")
    else:
        print(f"  ⚠ Agent deployed but GE registration failed")

    return True


def undeploy_agent(agent_name: str) -> bool:
    """Undeploy an agent from Agent Engine and unregister from Gemini Enterprise.

    Note: This unregisters from GE. To fully remove the Agent Engine resource,
    you would need the resource name. Use `gcloud` or the console for that.

    Args:
        agent_name: Name matching config/<agent_name>.yaml

    Returns:
        True if successful, False otherwise.
    """
    project_id = os.environ.get("PROJECT_ID")
    app_id = os.environ.get("GEMINI_ENTERPRISE_APP_ID")

    print(f"  ⏳ Unregistering from Gemini Enterprise...")

    ge_location = os.environ.get("GE_LOCATION", "global")
    success = _unregister_agent_from_gemini_enterprise(
        project_id=project_id,
        app_id=app_id,
        agent_name=f"{agent_name}_agent",
        ge_location=ge_location,
    )

    if success:
        print(f"  ✓ Unregistered from Gemini Enterprise")
        print(f"  ℹ To delete the Agent Engine resource, use:")
        print(f"    gcloud ai reasoning-engines list --region=us-central1")
        print(f"    gcloud ai reasoning-engines delete <RESOURCE_ID> --region=us-central1")
    else:
        print(f"  ✗ Failed to unregister from Gemini Enterprise")

    return success


# =============================================================================
# CLI
# =============================================================================

def main():
    load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))

    parser = argparse.ArgumentParser(
        description="Agent Framework — Deploy agents to Agent Engine + Gemini Enterprise",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/deploy.py employee_verification          # Deploy one agent
  python scripts/deploy.py agent1 agent2 agent3           # Deploy multiple
  python scripts/deploy.py --all                          # Deploy all agents
  python scripts/deploy.py --list                         # List available agents
  python scripts/deploy.py employee_verification --dry-run  # Preview config
  python scripts/deploy.py employee_verification --undeploy # Undeploy agent
        """,
    )

    parser.add_argument(
        "agents",
        nargs="*",
        help="Agent name(s) to deploy (matches config/<name>.yaml)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Deploy all agents found in config/",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available agents and exit",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deployed without actually deploying",
    )
    parser.add_argument(
        "--undeploy",
        action="store_true",
        help="Undeploy the specified agent(s) instead of deploying",
    )

    args = parser.parse_args()

    # --list: show available agents and exit
    if args.list:
        available = list_available_agents()
        print("=" * 60)
        print("  Agent Framework — Available Agents")
        print("=" * 60)
        if not available:
            print("  No agent configs found in config/")
        else:
            for name in available:
                try:
                    cfg = load_agent_config(name)
                    display = cfg.get("agent", {}).get("display_name", name)
                    model = cfg.get("agent", {}).get("model", "default")
                    tools = len(cfg.get("agent", {}).get("tools", []))
                    skills = len(cfg.get("deploy", {}).get("skills", []))
                    print(f"  • {name}")
                    print(f"    Display: {display}")
                    print(f"    Model: {model} | Tools: {tools} | Skills: {skills}")
                except Exception as e:
                    print(f"  • {name} (error loading config: {e})")
        print("=" * 60)
        return

    # Determine which agents to process
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

    # Validate all agent names first
    available = list_available_agents()
    invalid = [name for name in agent_names if name not in available]
    if invalid:
        print(f"✗ Unknown agent(s): {', '.join(invalid)}")
        print(f"  Available: {', '.join(available)}")
        sys.exit(1)

    # Header
    project_id = os.environ.get("PROJECT_ID", "?")
    location = os.environ.get("LOCATION", "us-central1")
    ge_location = os.environ.get("GE_LOCATION", "global")
    action = "Undeploy" if args.undeploy else ("Dry Run" if args.dry_run else "Deployment")

    print()
    print("=" * 80)
    print(f"  Agent Framework — {action}")
    print(f"  Project: {project_id} | Region: {location}")
    print("=" * 80)
    print()

    # -------------------------------------------------------------------------
    # Step 0: Resolve project number (needed for per-agent auth resource creation)
    # -------------------------------------------------------------------------
    _project_number = None
    if not args.undeploy and not args.dry_run:
        oauth_client_id = os.environ.get("OAUTH_CLIENT_ID")
        oauth_client_secret = os.environ.get("OAUTH_CLIENT_SECRET")
        if oauth_client_id and oauth_client_secret:
            print("  ⏳ Step 0: Resolving project number for auth resource management...")
            _project_number = _get_project_number(project_id)
            if _project_number:
                print(f"  ✓ Project number: {_project_number}")
            else:
                print(f"  ⚠ Could not resolve project number — per-agent auth creation will be skipped.")
            print()

    # Process each agent
    results = {}
    total = len(agent_names)

    for idx, agent_name in enumerate(agent_names, 1):
        print(f"[{idx}/{total}] {'Undeploying' if args.undeploy else 'Deploying'}: {agent_name}")

        if args.undeploy:
            success = undeploy_agent(agent_name)
        else:
            success = deploy_agent(agent_name, dry_run=args.dry_run)

        results[agent_name] = success
        print()

    # Summary
    succeeded = sum(1 for v in results.values() if v)
    failed = total - succeeded

    print("=" * 80)
    if failed == 0:
        print(f"  ✓ {succeeded}/{total} agents {'processed' if args.dry_run else 'completed'} successfully")
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
