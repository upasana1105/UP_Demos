import asyncio
import os
import logging
from agent import my_chat_agent_builder
from dotenv import load_dotenv

# Configure logging to see what's happening
logging.basicConfig(level=logging.INFO)

async def main():
    load_dotenv()
    
    import vertexai
    project_id = os.environ.get("PROJECT_ID", "uppdemos")
    location = os.environ.get("LOCATION", "us-central1")
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"
    os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
    os.environ["GOOGLE_CLOUD_LOCATION"] = location
    vertexai.init(project=project_id, location=location)
    
    print("Building agent...")
    agent = my_chat_agent_builder()
    
    query = "Show me the Kanban board"
    print(f"Sending query: '{query}'")
    
    # We need to mock the execution context or just call stream directly if accessible
    # stream method signature: stream(self, query: str, session_id: str)
    
    session_id = "test_session_local"
    
    try:
        async for chunk in agent.stream(query=query, session_id=session_id):
            print("\n--- Received Chunk ---")
            print(f"Is complete: {chunk.get('is_task_complete')}")
            for part in chunk.get("parts", []):
                if hasattr(part, "root") and hasattr(part.root, "text"):
                    print(f"Text Part: {part.root.text}")
                elif hasattr(part, "data"):
                    print(f"Data Part: {part.data}")
                else:
                    print(f"Other Part: {part}")
    except Exception as e:
        print(f"Error during streaming: {e}")

if __name__ == "__main__":
    asyncio.run(main())
