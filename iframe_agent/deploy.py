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

# Import the agent builder
from agent import my_chat_agent_builder

def _get_bearer_token():
    try:
        credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        request = Request()
        credentials.refresh(request)
        return credentials.token
    except Exception as e:
        print(f"Error getting credentials: {e}")
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
        print("✓ Agent registered successfully in Gemini Enterprise!")
        return response.json()
    print(f"✗ Registration failed with status code: {response.status_code}")
    print(f"Response: {response.text}")
    response.raise_for_status()

def main():
    load_dotenv()

    project_id = os.environ.get("PROJECT_ID")
    location = os.environ.get("LOCATION", "us-central1")
    storage = os.environ.get("STORAGE_BUCKET")
    app_id = os.environ.get("GEMINI_ENTERPRISE_APP_ID")
    api_endpoint = f"{location}-aiplatform.googleapis.com"

    if not all([project_id, storage, app_id]):
        print("Missing required environment variables. Please check .env file.")
        return

    print("=" * 80)
    print("  IFrame A2UI Agent - Deployment")
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

    client = vertexai.Client(
        project=project_id,
        location=location,
        http_options=types.HttpOptions(
            api_version="v1beta1",
        ),
    )

    # Instantiate the agent to get the card
    ref_agent = my_chat_agent_builder()
    card = ref_agent.get_agent_card()

    # Register with Vertex AI's A2aAgent
    a2a_agent = A2aAgent(
        agent_card=card,
        agent_executor_builder=my_chat_agent_builder
    )
    a2a_agent.set_up()

    config = {
        "display_name": "iframe_a2ui_agent",
        "description": "Agent with iFrame and A2UI support",
        "staging_bucket": storage,
        "requirements": [
            "google-cloud-aiplatform[agent_engines,adk]",
            "google-genai>=1.27.0",
            "cloudpickle",
            "pydantic",
            "protobuf==5.29.3",
        ],
        "http_options": {
            "api_version": "v1beta1",
        },
        "max_instances": 1,
        "env_vars": {
            "NUM_WORKERS": "1",
            "PROJECT_ID": project_id,
        },
        "extra_packages": [
            "agent.py",
            "a2a",
        ],
    }

    print("⏳ Deploying to Agent Engine (this may take 5-10 minutes)...")
    remote_agent = client.agent_engines.create(agent=a2a_agent, config=config)
    remote_engine_resource = remote_agent.api_resource.name
    print(f"✓ Remote agent created: {remote_engine_resource}")

    # Use the local card object instead of fetching it from the remote endpoint
    # This avoids the 400 Bad Request error if the endpoint is not exposed
    print("✓ Using local card definition...")
    a2ui_agent_card_json = card.model_dump()

    # Helper to remove null fields that cause Gemini Enterprise registration to fail
    def clean_none(obj):
        if isinstance(obj, dict):
            return {k: clean_none(v) for k, v in obj.items() if v is not None}
        elif isinstance(obj, list):
            return [clean_none(v) for v in obj if v is not None]
        else:
            return obj

    a2ui_agent_card_json = clean_none(a2ui_agent_card_json)

    # Ensure A2UI capabilities are present in the card for Gemini Enterprise
    a2ui_agent_card_json["capabilities"] = {
        "streaming": False,
        "extensions": [{
            "uri": "https://a2ui.org/a2a-extension/a2ui/v0.8",
            "description": "Ability to render A2UI",
            "required": False,
            "params": {
                "supportedCatalogIds": [
                    "https://a2ui.org/specification/v0_8/standard_catalog_definition.json",
                    "https://vertexaisearch.cloud.google.com/a2ui/v0_8/gemini_enterprise_custom_catalog.json"
                ]
            },
        }],
    }
    
    # Update the URL in the card to point to the deployed Reasoning Engine
    a2ui_agent_card_json["url"] = f"https://{location}-aiplatform.googleapis.com/v1beta1/{remote_engine_resource}/a2a"
    
    a2ui_agent_card_str = json.dumps(a2ui_agent_card_json)

    # Register in Gemini Enterprise
    _register_agent_on_gemini_enterprise(
        project_id=project_id,
        app_id=app_id,
        agent_card=a2ui_agent_card_str,
        agent_name="iframe_a2ui_agent_v12",
        display_name="IFrame A2UI Agent v12",
        description="An agent that renders an iframe Kanban board using A2UI.",
        agent_authorization=os.environ.get("AGENT_AUTHORIZATION"),
    )

    print("=" * 80)
    print("  Deployment Complete!")
    print("=" * 80)

if __name__ == "__main__":
    main()
