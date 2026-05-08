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

print(f"Listing Reasoning Engines in {project_id} / {location}...")
try:
    # List engines
    engines = client.agent_engines.list()
    for engine in engines:
        try:
            print(f"ID: {engine.api_resource.name}")
            print(f"Display Name: {engine.api_resource.display_name}")
        except Exception as e:
            print(f"Could not get name directly: {e}")
        print(f"Details: {engine}")
except Exception as e:
    print(f"Error: {e}")
