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

print(f"Scanning for all iframe reasoning engines in {project_id} / {location}...")
try:
    engines = client.agent_engines.list()
    for engine in engines:
        try:
            name = engine.api_resource.name
            display_name = engine.api_resource.display_name
            if "iframe" in display_name.lower() or "a2ui" in display_name.lower():
                print(f"Attempting to delete Reasoning Engine: {name} ({display_name})")
                try:
                    client.agent_engines.delete(name=name)
                    print(f"✓ Delete request sent for {name}")
                except Exception as e:
                    print(f"✗ Failed to delete {name}: {e}")
        except Exception as e:
            pass
except Exception as e:
    print(f"Error listing engines: {e}")
