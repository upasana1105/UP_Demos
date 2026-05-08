import os
import requests
from google.auth import default
from google.auth.transport.requests import Request
from dotenv import load_dotenv
import json

def _get_bearer_token():
    credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    request = Request()
    credentials.refresh(request)
    return credentials.token

def main():
    load_dotenv()
    project_id = os.environ.get("PROJECT_ID", "uppdemos")
    app_id = os.environ.get("GEMINI_ENTERPRISE_APP_ID", "gemini-enterprise-gm_1771086459519")
    
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
    
    print(f"Fetching registered agents from Gemini Enterprise ({app_id})...")
    response = requests.get(api_endpoint, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        agents = data.get("agents", [])
        print(f"Found {len(agents)} agents:")
        for a in agents:
            print("-" * 60)
            print(f"Name: {a.get('name')}")
            print(f"DisplayName: {a.get('displayName')}")
            auth_cfg = a.get("authorization_config", {})
            print(f"Authorization Config: {auth_cfg}")
    else:
        print(f"Failed to list agents: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    main()
