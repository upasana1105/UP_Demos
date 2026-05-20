"""
Deployment script for the Employee Verification Agent.

This script:
  1. Initializes Vertex AI
  2. Creates the A2A agent with the EmployeeVerificationExecutor
  3. Deploys it to Agent Engine
  4. Registers it in Gemini Enterprise

Usage:
    python deploy.py
    # or with uv:
    uv run deploy.py
"""

import json
import os

from a2a.types import AgentSkill
from vertexai.preview.reasoning_engines.templates.a2a import create_agent_card
from dotenv import load_dotenv
from google.auth import default
from google.auth.transport.requests import Request
from google.genai import types
import httpx
import requests
import vertexai
from vertexai.preview.reasoning_engines import A2aAgent

# Import the executor
from agents.employee_verification_agent.executor import EmployeeVerificationExecutor


def _get_bearer_token():
    """Gets a bearer token for authenticating with Google Cloud."""
    try:
        credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        request = Request()
        credentials.refresh(request)
        return credentials.token
    except Exception as e:
        print(f"Error getting credentials: {e}")
        print(
            "Please ensure you have authenticated with 'gcloud auth "
            "application-default login'."
        )
    return None


def _register_agent_on_gemini_enterprise(
    project_id: str,
    app_id: str,
    agent_card: str,
    agent_name: str,
    display_name: str,
    description: str,
    agent_authorization: str | None = None,
):
    """Register an Agent Engine to Gemini Enterprise."""
    api_endpoint = (
        f"https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}/"
        f"locations/global/collections/default_collection/engines/{app_id}/"
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
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
        "X-Goog-User-Project": project_id,
    }

    response = requests.post(api_endpoint, headers=headers, json=payload)

    if response.status_code == 200:
        print("✓ Agent registered successfully!")
        return response.json()
    print(f"✗ Registration failed with status code: {response.status_code}")
    print(f"Response: {response.text}")
    response.raise_for_status()


def main():
    load_dotenv()

    project_id = os.environ.get("PROJECT_ID")
    location = os.environ.get("LOCATION")
    storage = os.environ.get("STORAGE_BUCKET")
    app_id = os.environ.get("GEMINI_ENTERPRISE_APP_ID")
    api_endpoint = f"{location}-aiplatform.googleapis.com"

    print("=" * 80)
    print("  Employee Verification Agent - Deployment")
    print("=" * 80)
    print(f"  Project:  {project_id}")
    print(f"  Location: {location}")
    print(f"  Bucket:   {storage}")
    print(f"  App ID:   {app_id}")
    print("=" * 80)

    vertexai.init(
        project=project_id,
        location=location,
        api_endpoint=api_endpoint,
        staging_bucket=storage,
    )
    print("✓ Vertex AI initialized.")

    client = vertexai.Client(
        project=project_id,
        location=location,
        http_options=types.HttpOptions(
            api_version="v1beta1",
        ),
    )
    print("✓ Vertex AI client created.")

    # Define skills
    skill_lookup = AgentSkill(
        id="employee-lookup",
        name="Employee Lookup",
        description="Search and find employee records by name, employee ID, or department.",
        tags=["employee", "lookup", "search", "hr"],
        examples=[
            "Find employee John Smith",
            "Look up employee E-1001",
            "Show me employees in the Finance department",
            "List all employees",
        ],
    )

    skill_update = AgentSkill(
        id="employee-update",
        name="Employee Field Update",
        description="Update editable employee fields like address, phone, email, and emergency contact.",
        tags=["employee", "update", "edit", "hr"],
        examples=[
            "Update my address to 123 Main St",
            "Change my phone number to 555-1234",
            "Update emergency contact to John Doe",
        ],
    )

    skill_verify = AgentSkill(
        id="employee-verification",
        name="Employee Verification",
        description="Verify employee records, review employment details, and mark records as verified.",
        tags=["employee", "verification", "verify", "hr"],
        examples=[
            "Verify my employment",
            "I need to verify my employee record",
            "Mark my record as verified",
        ],
    )

    skill_a2ui = AgentSkill(
        id="a2ui-ui-rendering",
        name="A2UI UI Rendering",
        description="Generate rich interactive forms and cards using the A2UI protocol, "
                    "including verification forms with editable fields and success cards.",
        tags=["a2ui", "ui", "form", "card"],
        examples=[
            "Show my employee verification form",
            "Display employee search results",
        ],
    )

    agent_card = create_agent_card(
        agent_name="Employee Verification Agent",
        description="An HR agent that helps employees review, update, and verify their employment records. "
                    "Renders interactive verification forms with editable fields using A2UI.",
        skills=[skill_lookup, skill_update, skill_verify, skill_a2ui],
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
    )

    print(f"✓ Agent card created.")

    # Create A2aAgent with the executor
    a2ui_agent = A2aAgent(
        agent_card=agent_card,
        agent_executor_builder=EmployeeVerificationExecutor,
    )
    a2ui_agent.set_up()
    print("✓ Local agent created and tested.")

    # Deploy configuration
    config = {
        "display_name": "employee_verification_agent",
        "description": (
            "Employee Verification Agent - reviews, updates, and verifies "
            "employee records using A2UI forms and BigQuery backend."
        ),
        "agent_framework": "google-adk",
        "staging_bucket": storage,
        "gcs_dir_name": "employee_verification",
        "requirements": [],
        "extra_packages": [
            "agents/employee_verification_agent",
            "tools",
            "examples",
            "pyproject.toml",
        ],
        "http_options": {
            "api_version": "v1beta1",
        },
        "max_instances": 1,
        "env_vars": {
            "NUM_WORKERS": "1",
            "PROJECT_ID": project_id,
        },
    }

    print("⏳ Deploying to Agent Engine (this may take 5-10 minutes)...")
    remote_agent = client.agent_engines.create(agent=a2ui_agent, config=config)

    remote_engine_resource = remote_agent.api_resource.name
    print(f"✓ Remote agent created: {remote_engine_resource}")

    # Fetch the A2A card from the deployed agent
    a2a_endpoint = f"https://{api_endpoint}/v1beta1/{remote_engine_resource}/a2a/v1/card"
    bearer_token = _get_bearer_token()
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
    }

    print(f"✓ A2A endpoint: {a2a_endpoint}")

    response = httpx.get(a2a_endpoint, headers=headers)
    response.raise_for_status()
    a2ui_agent_card_json = response.json()

    # Add A2UI capabilities to the agent card
    a2ui_agent_card_json["capabilities"] = {
        "streaming": False,
        "extensions": [{
            "uri": "https://a2ui.org/a2a-extension/a2ui/v0.8",
            "description": "Ability to render A2UI",
            "required": False,
            "params": {
                "supportedCatalogIds": [
                    "https://a2ui.org/specification/v0_8/standard_catalog_definition.json"
                ]
            },
        }],
    }
    a2ui_agent_card_str = json.dumps(a2ui_agent_card_json)
    print("✓ A2UI agent card fetched and enhanced.")

    # Register in Gemini Enterprise
    enterprise_agent = _register_agent_on_gemini_enterprise(
        project_id=project_id,
        app_id=app_id,
        agent_card=a2ui_agent_card_str,
        agent_name="employee_verification_agent",
        display_name="Employee Verification Agent",
        description="An HR agent for employee verification with A2UI forms and BigQuery backend.",
        agent_authorization=os.environ.get("AGENT_AUTHORIZATION"),
    )

    print(enterprise_agent)
    print("=" * 80)
    print("  Deployment Complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
