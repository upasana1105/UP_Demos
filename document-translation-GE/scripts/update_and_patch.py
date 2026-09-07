import os
import sys
import time
import json
from pathlib import Path

import requests
from google.auth import default
from google.auth.transport.requests import Request
from google.genai import types
import vertexai
from vertexai.preview.reasoning_engines import A2aAgent
from vertexai.preview.reasoning_engines.templates.a2a import create_agent_card
from a2a.types import AgentSkill

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))
from agents._base.config_loader import load_agent_config
from agents.translation_assistant.executor import KPMGTranslationExecutor

def main():
    config = load_agent_config("translation_assistant")
    agent_cfg = config.get("agent", {})
    deploy_cfg = config.get("deploy", {})

    project_id = "uppdemos"
    location = "us-central1"
    storage = "gs://uppdemos-agent-staging"
    api_endpoint = f"{location}-aiplatform.googleapis.com"
    api_version = "v1beta1"

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

    skills = [
        AgentSkill(
            id="kpmg-financial-translation",
            name="Financial Document Translation & Watermark Suppression",
            description="Translates financial PDF documents preserving formatting, suppressing watermarks via NO_ATTRIBUTION, performing semantic quality audits, and displaying interactive side-by-side dashboards.",
            tags=["translation", "kpmg", "financial", "attribution", "audit", "iframe"],
            examples=["Translate sample_doc.pdf to Spanish using NO_ATTRIBUTION"],
        )
    ]

    agent_card = create_agent_card(
        agent_name=agent_cfg.get("display_name", "KPMG Financial Document Translator"),
        description=agent_cfg.get("description", "Translates financial documents"),
        skills=skills,
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain", "application/json+a2ui"],
    )

    a2a_agent = A2aAgent(
        agent_card=agent_card,
        agent_executor_builder=KPMGTranslationExecutor,
    )
    a2a_agent.set_up()

    base_reqs = deploy_cfg.get("base_requirements", [])
    extra_reqs = deploy_cfg.get("extra_requirements", [])
    all_requirements = base_reqs + extra_reqs
    extra_packages = deploy_cfg.get("extra_packages", ["agents"])
    env_vars = deploy_cfg.get("env_vars", {})
    env_vars["PROJECT_ID"] = project_id

    deploy_config = {
        "display_name": "translation_assistant_agent",
        "description": agent_cfg.get("description", ""),
        "agent_framework": deploy_cfg.get("agent_framework", "google-adk"),
        "staging_bucket": storage,
        "gcs_dir_name": "translation_assistant",
        "requirements": all_requirements,
        "http_options": {"api_version": api_version},
        "max_instances": 1,
        "extra_packages": extra_packages,
        "env_vars": env_vars,
    }

    print("Deploying Reasoning Engine to Agent Engine...")
    start_time = time.time()
    remote_agent = client.agent_engines.create(agent=a2a_agent, config=deploy_config)
    elapsed = time.time() - start_time
    resource_name = remote_agent.api_resource.name
    print(f"✓ Deployed: {resource_name} in {elapsed:.0f}s")

    # Patch Discovery Engine Agent
    credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    req = Request()
    credentials.refresh(req)
    token = credentials.token

    engine_id = "app-for-connector-test_1771194937552"
    agent_id = "345992554252828106"
    new_a2a_url = f"https://us-central1-aiplatform.googleapis.com/v1beta1/{resource_name}/a2a"
    agent_url = f"https://discoveryengine.googleapis.com/v1alpha/projects/850431687571/locations/global/collections/default_collection/engines/{engine_id}/assistants/default_assistant/agents/{agent_id}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Goog-User-Project": project_id,
    }

    curr = requests.get(agent_url, headers=headers).json()
    card = json.loads(curr["a2aAgentDefinition"]["jsonAgentCard"])
    card["url"] = new_a2a_url
    card["defaultOutputModes"] = ["text/plain", "application/json+a2ui"]
    patch_resp = requests.patch(
        f"{agent_url}?updateMask=a2aAgentDefinition",
        headers=headers,
        json={"a2aAgentDefinition": {"jsonAgentCard": json.dumps(card)}}
    )
    print(f"✓ Patched Discovery Engine agent: status {patch_resp.status_code}")
    print(f"  New URL: {new_a2a_url}")

if __name__ == "__main__":
    main()
