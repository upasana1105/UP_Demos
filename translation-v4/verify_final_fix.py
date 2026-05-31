import asyncio
import os
from main import root_agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

async def verify_correction_layer():
    app_name = "VerificationApp"
    user_id = "test-user"
    session_id = "test-session"
    
    session_service = InMemorySessionService()
    await session_service.create_session(app_name=app_name, user_id=user_id, session_id=session_id)
    
    runner = Runner(
        app_name=app_name,
        agent=root_agent,
        session_service=session_service
    )
    
    file_path = "/Users/upasanapati/shrinkAI experiment/Antigravity_Experiments/UP_Demos/translation/uploads/5g-edge-computing-value-opportunity.pdf"
    target_lang = "de"
    glossary_id = "kpmg-5g-german"
    
    user_message = (
        f"Please translate the financial document located at '{file_path}' "
        f"into the target language '{target_lang}'. "
        f"CRITICAL INSTRUCTION: Use glossary_id '{glossary_id}'. "
        "\n\nPerform a deep audit and explicitly mention any numerical scale corrections in your executive summary."
    )
    
    print("--- Running End-to-End Verification ---")
    async for event in runner.run_async(
        session_id=session_id,
        user_id=user_id,
        new_message=types.Content(role="user", parts=[types.Part(text=user_message)])
    ):
        if event.is_final_response():
            print("\n--- FINAL AGENT RESPONSE ---")
            print(event.content.parts[0].text)

if __name__ == "__main__":
    asyncio.run(verify_correction_layer())
