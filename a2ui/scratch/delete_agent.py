import os
import requests
from google.auth import default
from google.auth.transport.requests import Request
from dotenv import load_dotenv

def _get_bearer_token():
  credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
  request = Request()
  credentials.refresh(request)
  return credentials.token

def delete_agent():
  load_dotenv()
  project_id = os.environ.get("PROJECT_ID")
  app_id = os.environ.get("GEMINI_ENTERPRISE_APP_ID")
  
  # The specific agent ID to delete (using v1 auth)
  agent_id = "6348629820752014292"
  
  api_endpoint = (
      f"https://discoveryengine.googleapis.com/v1alpha/projects/{project_id}/"
      f"locations/global/collections/default_collection/engines/{app_id}/"
      f"assistants/default_assistant/agents/{agent_id}"
  )
  
  bearer_token = _get_bearer_token()
  headers = {
      "Authorization": f"Bearer {bearer_token}",
      "Content-Type": "application/json",
      "X-Goog-User-Project": project_id,
  }
  
  print(f"Deleting agent: {api_endpoint}")
  response = requests.delete(api_endpoint, headers=headers)
  print(f"Status: {response.status_code}")
  print(response.text)

if __name__ == "__main__":
    delete_agent()

