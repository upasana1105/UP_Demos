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
    project_id = "uppdemos"
    app_id = "gemini-enterprise-gm_1771086459519"
    list_endpoint = (
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
    print(f"Scanning Gemini Enterprise ({app_id}) for iframe agents...")
    response = requests.get(list_endpoint, headers=headers)
    if response.status_code == 200:
        agents = response.json().get("agents", [])
        for a in agents:
            name = a.get("name")
            display_name = a.get("displayName", "")
            if "iframe" in display_name.lower() or "a2ui" in display_name.lower():
                delete_url = f"https://discoveryengine.googleapis.com/v1alpha/{name}"
                print(f"Deleting Gemini Enterprise Agent: {name} ({display_name})")
                del_resp = requests.delete(delete_url, headers=headers)
                if del_resp.status_code in [200, 204]:
                    print(f"✓ Successfully deleted {display_name}")
                else:
                    print(f"✗ Failed to delete {display_name}: {del_resp.status_code} - {del_resp.text}")
    else:
        print(f"✗ Failed to list agents: {response.status_code} - {response.text}")

if __name__ == "__main__":
    main()
