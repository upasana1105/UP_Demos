from google.adk.agents.llm_agent import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from translator_tool import adaptive_translate_tool, read_csv_glossary, inspect_translation_proof
from audit_tool import get_pdf_text
from pydantic import BaseModel
from typing import List, Optional

class AuditFinding(BaseModel):
    issue: str
    original_text: str
    translated_text: str
    impact: str
    recommendation: str

class AuditReport(BaseModel):
    overall_score: int
    accuracy_score: int
    fluency_score: int
    tone_score: int
    confidence_index: int
    audit_findings: List[AuditFinding]
    executive_summary: str
    translated_file_path: str

def audit_translation(source_file: str, translated_file: str) -> dict:
    source_text = get_pdf_text(source_file)
    translated_text = get_pdf_text(translated_file)
    return {
        "source_content": source_text[:10000],
        "translated_content": translated_text[:10000]
    }

# Unified Finance Architect Agent (Optimized for Speed)
root_agent = LlmAgent(
    name="FinanceArchitect",
    model="gemini-2.5-flash",
    description="A high-speed agent for financial translation and semantic auditing.",
    instruction="""You are the KPMG Finance Architect. Your goal is a fast, accurate, and professional translation pipeline.

### WORKFLOW:
1. **Intelligence**: Extract text from 'file_path' and store as 'source_text'. Identify all numerical scales (Trillions, Billions).
   - **CRITICAL NUMERICAL RULE**: English 1 Trillion = German 1 Billion. English 1 Billion = German 1 Milliarde.
2. **Translate**: Call 'adaptive_translate_tool' to get the PDF.
3. **Elite Audit**:
   - Call 'audit_translation' to compare source vs result.
   - Use 'inspect_translation_proof' (Powered by Gemini Pro) with the 'source_text' context to verify glossary adherence. 
   - **NUMERICAL CROSS-CHECK**: If the translation tool produced a 1,000x error (e.g., "trillion" -> "Milliarden"), you MUST explicitly flag this in your report.
4. **Final Response**: Output the 'AuditReport' JSON. 
   - **CORRECTION LAYER**: In the 'executive_summary', if a numerical scale error was found in the PDF, you MUST provide the correct figure (e.g., "Note: The PDF shows 'Milliarden', but the correct value is 'Billionen'").
""",
    tools=[adaptive_translate_tool, read_csv_glossary, get_pdf_text, inspect_translation_proof, audit_translation],
    output_schema=AuditReport
)

if __name__ == "__main__":
    import asyncio
    async def main():
        runner = Runner(
            app_name="translation_demo",
            agent=root_agent,
            session_service=InMemorySessionService()
        )
        print("Finance Architect Ready.")
    asyncio.run(main())
