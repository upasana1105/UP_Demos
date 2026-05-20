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

def delete_auths():
  load_dotenv()
  project_id = os.environ.get("PROJECT_ID")
  
  bearer_token = _get_bearer_token()
  headers = {
      "Authorization": f"Bearer {bearer_token}",
      "X-Goog-User-Project": project_id,
  }
  
  # List of auth IDs to clean up
  auth_ids = ["a2ui-auth-v4", "a2ui-auth-v5", "a2ui-auth-v6", "a2ui-auth-v7", "a2ui-auth-v8", "a2ui-auth-v10"]
  
  for auth_id in auth_ids:
      url = f"https://global-discoveryengine.googleapis.com/v1alpha/projects/{project_id}/locations/global/authorizations/{auth_id}"
      print(f"Deleting auth resource: {url}")
      response = requests.delete(url, headers=headers)
      print(f"Status: {response.status_code}")
      print(response.text)
      print("-" * 40)

if __name__ == "__main__":
    delete_auths()
