import asyncio
import os
import shutil
import re
import json
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

try:
    import importlib.metadata as metadata
except ImportError:
    import importlib_metadata as metadata

load_dotenv()
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
os.environ["GOOGLE_CLOUD_PROJECT"] = "uppdemos"
os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"

# Import our ADK Agent and ADK core
from main import root_agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
GLOSSARY_DIR = os.path.join(BASE_DIR, "glossaries")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(GLOSSARY_DIR, exist_ok=True)


@app.post("/api/translate")
async def translate_document(
    file: UploadFile = File(...),
    target_language: str = Form(...),
    glossary_id: str = Form(None),
    custom_glossary_path: str = Form(None)
):
    try:
        # 1. Save uploaded file
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        user_message = (
            f"Please translate the financial document located at '{os.path.abspath(file_path)}' "
            f"into the target language '{target_language}'. "
        )

        # Automatically register user's custom CSV glossary to GCP if provided
        if custom_glossary_path:
            import glossary_manager
            try:
                print(f"Syncing custom glossary to GCP...")
                registered_id = glossary_manager.create_cloud_glossary(custom_glossary_path, target_language)
                glossary_id = registered_id # Override with the newly registered ID
            except Exception as e:
                print(f"Glossary Sync Warning: {e}")

        if glossary_id:
            user_message += f"\n\nCRITICAL INSTRUCTION: When you call the 'adaptive_translate_tool', you MUST explicitly set the parameter 'glossary_id' equal to '{glossary_id}'. Do not leave it blank. "
        
        user_message += (
            "\n\nCRITICAL ENFORCEMENT SUMMARY REQUIRED: "
            "In your final response, you MUST include a detailed 'AI Enforcement Summary'. "
            "This summary must explicitly demonstrate how the glossary was 'enforced'. "
            "Provide specific examples (e.g., list 'Stop Words' like EBITDA that were strictly preserved, "
            "and other terms that were mapped). Format this summary clearly in Markdown."
        )


        # 3. Initialize the Runner and Session
        session_service = InMemorySessionService()
        app_name = "FinanceTranslatorApp"
        user_id = "user-1"
        session_id = f"session-{os.urandom(4).hex()}"
        
        await session_service.create_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id
        )

        runner = Runner(
            app_name=app_name,
            agent=root_agent,
            session_service=session_service
        )

        print(f"Running agent with session {session_id} and message: {user_message}")
        
        agent_text = ""
        # Run the agent and collect response
        async for event in runner.run_async(
            session_id=session_id,
            user_id=user_id,

            new_message=types.Content(role="user", parts=[types.Part(text=user_message)])
        ):
            if event.is_final_response():
                # Extract text from the final response content
                # Structure: event.content.parts[0].text
                agent_text = event.content.parts[0].text

        # 4. Process the Agent's structured AuditReport
        print(f"Agent raw response: {agent_text}")
        
        audit_data = {}
        try:
            # ADK might return the JSON inside a markdown block or as a raw string
            json_match = re.search(r'\{.*\}', agent_text, re.DOTALL)
            if json_match:
                audit_data = json.loads(json_match.group(0))
            else:
                audit_data = json.loads(agent_text)
        except Exception as json_err:
            print(f"JSON Parsing Error: {json_err}")
            audit_data = {"error": "Could not parse audit report", "raw": agent_text}

        # 5. Extract the output file path from the audit data or fallback
        final_file = audit_data.get("translated_file_path")
        
        if not final_file or not os.path.exists(final_file):
            # Fallback path logic
            expected_output = file_path.replace(".pdf", f"_{target_language}.pdf")
            final_file = expected_output if os.path.exists(expected_output) else None

        return {
            "status": "success",
            "audit_report": audit_data,
            "agent_reasoning": agent_text,
            "output_file": final_file
        }

    except Exception as e:
        import traceback
        return {"status": "error", "message": f"{str(e)}\n{traceback.format_exc()}"}

@app.post("/api/upload-glossary")
async def upload_glossary(file: UploadFile = File(...)):
    try:
        file_path = os.path.join(GLOSSARY_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {"status": "success", "file_path": os.path.abspath(file_path)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/view-file")
async def view_file(file_path: str):
    # Try absolute first, then check if it already starts with UPLOAD_DIR
    if os.path.isabs(file_path):
        full_path = file_path
    elif file_path.startswith(UPLOAD_DIR):
        full_path = file_path
    else:
        full_path = os.path.join(UPLOAD_DIR, file_path)
        
    if os.path.exists(full_path):
        return FileResponse(full_path, media_type="application/pdf")
    return {"error": f"File not found: {full_path}"}

@app.get("/api/download")
async def download_file(file_path: str):
    # Try absolute first, then check if it already starts with UPLOAD_DIR
    if os.path.isabs(file_path):
        full_path = file_path
    elif file_path.startswith(UPLOAD_DIR):
        full_path = file_path
    else:
        full_path = os.path.join(UPLOAD_DIR, file_path)

    if os.path.exists(full_path):
        return FileResponse(full_path, media_type="application/pdf", filename=os.path.basename(full_path))
    return {"error": f"File not found: {full_path}"}





# Serve Static Frontend (ONLY in production or when dist exists)
frontend_path = os.path.join(BASE_DIR, "frontend", "dist")
if os.path.exists(frontend_path):
    print(f"Mounting static frontend from {frontend_path}")
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
