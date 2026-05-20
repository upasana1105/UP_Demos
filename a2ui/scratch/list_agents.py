import os
import requests
import json
from google.auth import default
from google.auth.transport.requests import Request
from dotenv import load_dotenv

def _get_bearer_token():
  credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
  request = Request()
  credentials.refresh(request)
  return credentials.token

def list_agents():
  load_dotenv()
  project_id = os.environ.get("PROJECT_ID")
  app_id = os.environ.get("GEMINI_ENTERPRISE_APP_ID")
  
  api_endpoint = (
      f"https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}/"
      f"locations/global/collections/default_collection/engines/{app_id}/"
      "assistants/default_assistant/agents"
  )
  
  bearer_token = _get_bearer_token()
  headers = {
      "Authorization": f"Bearer {bearer_token}",
      "Content-Type": "application/json",
      "X-Goog-User-Project": project_id,
  }
  
  response = requests.get(api_endpoint, headers=headers)
  if response.status_code == 200:
      data = response.json()
      agents = data.get("agents", [])
      for agent in agents:
          name = agent.get("name")
          display_name = agent.get("displayName")
          auth_config = agent.get("authorizationConfig", {})
          print(f"Name: {name}")
          print(f"Display Name: {display_name}")
          print(f"Auth Config: {json.dumps(auth_config)}")
          print("-" * 40)
  else:
      print(f"Error: {response.status_code}")
      print(response.text)

if __name__ == "__main__":
    list_agents()

