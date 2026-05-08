import os
import vertexai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
project_id = os.environ.get("PROJECT_ID")
location = os.environ.get("LOCATION", "us-central1")

vertexai.init(project=project_id, location=location)
client = vertexai.Client(
    project=project_id,
    location=location,
    http_options=types.HttpOptions(
        api_version="v1beta1",
    ),
)

# List of engine IDs to delete (based on previous failures and older versions)
engines_to_delete = [
    "4432989540390535168"
]

for engine_id in engines_to_delete:
    resource_name = f"projects/{project_id}/locations/{location}/reasoningEngines/{engine_id}"
    print(f"Attempting to delete: {resource_name}")
    try:
        # The SDK might use delete() method
        client.agent_engines.delete(name=resource_name)
        print(f"✓ Delete request sent for {engine_id}")
    except Exception as e:
        print(f"✗ Failed to delete {engine_id}: {e}")
