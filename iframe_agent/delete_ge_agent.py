import os
import requests
from google.auth import default
from google.auth.transport.requests import Request

def _get_bearer_token():
    credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    request = Request()
    credentials.refresh(request)
    return credentials.token

def main():
    agent_resource_name = (
        "projects/850431687571/locations/global/collections/default_collection/"
        "engines/gemini-enterprise-gm_1771086459519/assistants/default_assistant/"
        "agents/18308671199588090470"
    )
    
    api_endpoint = f"https://discoveryengine.googleapis.com/v1alpha/{agent_resource_name}"
    
    bearer_token = _get_bearer_token()
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json",
        "X-Goog-User-Project": "uppdemos",
    }
    
    print(f"Deleting older agent from Gemini Enterprise: {agent_resource_name}")
    response = requests.delete(api_endpoint, headers=headers)
    
    if response.status_code in [200, 204]:
        print("✓ Older agent deleted successfully! Authorization lock released.")
    else:
        print(f"✗ Failed to delete agent: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    main()
