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

def create_auth():
  load_dotenv()
  project_id = os.environ.get("PROJECT_ID", "uppdemos")
  auth_id = "a2ui-auth-iframe-v16"
  
  # Client ID and Secret matched exactly from reference implementation
  client_id = "850431687571-78f04l9o3tcaodpc4mf9c31809a0f227.apps.googleusercontent.com"
  client_secret = "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"
  
  api_endpoint = (
      f"https://global-discoveryengine.googleapis.com/v1alpha/projects/{project_id}/"
      f"locations/global/authorizations?authorizationId={auth_id}"
  )
  
  payload = {
    "name": f"projects/{project_id}/locations/global/authorizations/{auth_id}",
    "serverSideOauth2": {
      "clientId": client_id,
      "clientSecret": client_secret,
      "authorizationUri": f"https://accounts.google.com/o/oauth2/v2/auth?client_id={client_id}&redirect_uri=https%3A%2F%2Fvertexaisearch.cloud.google.com%2Fstatic%2Foauth%2Foauth.html&scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcloud-platform&include_granted_scopes=true&response_type=code&access_type=offline&prompt=consent",
      "tokenUri": "https://oauth2.googleapis.com/token"
    }
  }
  
  bearer_token = _get_bearer_token()
  headers = {
      "Authorization": f"Bearer {bearer_token}",
      "Content-Type": "application/json",
      "X-Goog-User-Project": project_id,
  }
  
  print(f"Creating fresh authorization resource: {auth_id}...")
  response = requests.post(api_endpoint, headers=headers, json=payload)
  print(f"Status: {response.status_code}")
  print(response.text)

if __name__ == "__main__":
    create_auth()
