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

def read_logs():
  load_dotenv()
  project_id = os.environ.get("PROJECT_ID")
  
  url = "https://logging.googleapis.com/v2/entries:list"
  
  # Filter for our specific log message across all resources in the project
  payload = {
      "resourceNames": [f"projects/{project_id}"],
      "filter": '"Received a2ui ClientEvent"',
      "orderBy": "timestamp desc",
      "pageSize": 10
  }
  
  bearer_token = _get_bearer_token()
  headers = {
      "Authorization": f"Bearer {bearer_token}",
      "Content-Type": "application/json"
  }
  
  print(f"Fetching logs for project: {project_id}")
  response = requests.post(url, headers=headers, json=payload)
  print(f"Status: {response.status_code}")
  print(response.text)

if __name__ == "__main__":
    read_logs()
