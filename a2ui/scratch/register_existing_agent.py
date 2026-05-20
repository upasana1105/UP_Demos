import os
import sys
import json
from dotenv import load_dotenv
from google.auth import default
from google.auth.transport.requests import Request
import requests

def _get_bearer_token():
    credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    request = Request()
    credentials.refresh(request)
    return credentials.token

def register():
  load_dotenv()
  project_id = os.environ.get("PROJECT_ID")
  app_id = os.environ.get("GEMINI_ENTERPRISE_APP_ID")
  engine_id = "2880536296575467520"
  
  # Hardcode the agent card JSON directly to bypass the 400 error from engine!
  url = f"https://us-central1-aiplatform.googleapis.com/v1beta1/projects/{project_id}/locations/us-central1/reasoningEngines/{engine_id}/a2a"
  
  a2ui_agent_card_json = {
      "name": "contact lookupv1",
      "description": "Version 1: Generative agent that handles HR employee verification cards.",
      "url": url,
      "skills": [
          {
              "id": "employee-verification",
              "name": "Employee Verification",
              "description": "Look up and verify employee information using interactive cards.",
              "tags": ["employee", "hr", "verify"],
              "examples": ["Verify employee E-1001", "Look up John Smith"]
          }
      ],
      "capabilities": {
          "streaming": False,
          "extensions": [{
              "uri": "https://a2ui.org/a2a-extension/a2ui/v0.8",
              "description": "Ability to render A2UI",
              "required": False,
              "params": {
                  "supportedCatalogIds": [
                      "https://a2ui.org/specification/v0_8/standard_catalog_definition.json"
                  ]
              }
          }]
      },
      "defaultInputModes": ["text/plain"],
      "defaultOutputModes": ["text/plain"],
      "protocolVersion": "0.3.0",
      "preferredTransport": "HTTP+JSON",
      "supportsAuthenticatedExtendedCard": True,
      "version": "1.0.0"
  }
  
  a2ui_agent_card_str = json.dumps(a2ui_agent_card_json)
  
  # Registration
  api_endpoint = (
      f"https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}/"
      f"locations/global/collections/default_collection/engines/{app_id}/"
      "assistants/default_assistant/agents"
  )
  
  payload = {
      "displayName": "contact lookupv1",
      "description": "Version 1: Generative agent that handles HR employee verification cards.",
      "state": "ENABLED",
      "a2aAgentDefinition": {
          "jsonAgentCard": a2ui_agent_card_str
      },
      "authorizationConfig": {
          "agentAuthorization": "projects/850431687571/locations/global/authorizations/a2ui-auth-v17"
      }
  }
  
  bearer_token = _get_bearer_token()
  headers = {
      "Authorization": f"Bearer {bearer_token}",
      "Content-Type": "application/json",
      "X-Goog-User-Project": project_id,
  }
  
  print(f"Registering agent at: {api_endpoint}")
  response = requests.post(api_endpoint, headers=headers, json=payload)
  
  if response.status_code != 200:
      print(f"Registration failed. status: {response.status_code}, message: {response.text}")
  else:
      print("✓ Agent registered successfully on Gemini Enterprise!")
      print(response.text)

if __name__ == "__main__":
    register()
