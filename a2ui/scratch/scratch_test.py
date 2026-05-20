import os
from dotenv import load_dotenv
import vertexai
from google.genai import types

load_dotenv()

project_id = os.environ.get("PROJECT_ID")
location = os.environ.get("LOCATION")
storage = os.environ.get("STORAGE_BUCKET")

print(f"Initializing Vertex AI with project={project_id}, location={location}, storage={storage}...")
vertexai.init(
    project=project_id,
    location=location,
    staging_bucket=storage,
)
print("Vertex AI initialized!")

print("Creating vertexai.Client with v1beta1...")
client = vertexai.Client(
    project=project_id,
    location=location,
    http_options=types.HttpOptions(
        api_version="v1beta1",
    ),
)
print("Client created!")
