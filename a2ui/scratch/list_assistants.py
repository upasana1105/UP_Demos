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

def list_assistants():
  load_dotenv()
  project_id = os.environ.get("PROJECT_ID")
  app_id = os.environ.get("GEMINI_ENTERPRISE_APP_ID")
  
  api_endpoint = (
      f"https://global-discoveryengine.googleapis.com/v1alpha/projects/{project_id}/"
      f"locations/global/collections/default_collection/engines/{app_id}/assistants"
  )
  
  bearer_token = _get_bearer_token()
  headers = {
      "Authorization": f"Bearer {bearer_token}",
      "X-Goog-User-Project": project_id,
  }
  
  print(f"Listing assistants at: {api_endpoint}")
  response = requests.get(api_endpoint, headers=headers)
  print(f"Status: {response.status_code}")
  print(response.text)

if __name__ == "__main__":
    list_assistants()
