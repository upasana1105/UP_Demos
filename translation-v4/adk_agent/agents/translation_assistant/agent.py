# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
KPMG Translation Assistant — ADK Agent Definition.
"""

import os
from google.adk.agents.llm_agent import LlmAgent
from .tools import translate_and_audit_document

AGENT_NAME = "KPMGTranslationAssistant"

SYSTEM_INSTRUCTION = """You are the KPMG Financial Document Translation & Quality Assurance Assistant.

Your capabilities:
1. Translate financial documents (PDFs) with layout preservation and watermark removal (`customized_attribution="NO_ATTRIBUTION"`).
2. Audit translations for numerical precision, 1,000x scale discrepancies (e.g. Millions vs. Billions), and GAAP/IFRS terminology.
3. Automatically present an interactive KPMG Translation Dashboard (Quality Audit + Side-by-Side Document Viewer) directly inside Gemini Enterprise using A2UI WebFrameSrcdoc iframes.

Guidelines:
- When a user asks to translate a document (e.g. "Translate sample_doc.pdf to Spanish", "Translate this financial report to German"), invoke the `translate_and_audit_document` tool.
- Always default `customized_attribution` to "NO_ATTRIBUTION" unless the user specifically asks for Google branding.
- In your conversational text response, provide a professional executive summary of the translation:
  - Mention target language, file name, and watermark suppression status (NO_ATTRIBUTION active).
  - State the overall audit score (e.g. 95%) and confirm that numerical scales have been verified.
  - Inform the user that the full interactive dashboard and side-by-side viewer are rendered below in the iframe.
- Never output raw JSON or <a2ui-json> blocks in your text reply; the system automatically attaches the A2UI dashboard iframe.
"""

def get_agent(model_name: str | None = None) -> LlmAgent:
    """Instantiate and return the KPMG Translation Assistant LlmAgent."""
    model = model_name or os.environ.get("GOOGLE_GENAI_MODEL", "gemini-2.5-flash")
    return LlmAgent(
        name=AGENT_NAME,
        model=model,
        description="High-precision financial document translation with watermark removal and A2UI iframe auditing.",
        instruction=SYSTEM_INSTRUCTION,
        tools=[translate_and_audit_document],
    )
