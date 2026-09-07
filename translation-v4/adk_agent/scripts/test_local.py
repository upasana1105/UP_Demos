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
Local verification harness for KPMG Translation Assistant A2A Executor.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# Add adk_agent root to sys.path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv
load_dotenv(_ROOT / ".env")

import vertexai
from a2a.server.agent_execution import RequestContext
from a2a.server.events import EventQueue
from a2a.types import TaskState, TextPart, DataPart, Part, Message, MessageSendParams
from agents.translation_assistant.executor import KPMGTranslationExecutor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class MockEventQueue(EventQueue):
    def __init__(self):
        self.events = []

    async def enqueue_event(self, event):
        self.events.append(event)
        print(f"\n[EventQueue] Event received: {type(event).__name__}")
        if hasattr(event, "status"):
            state = getattr(event.status, "state", None)
            print(f"  State: {state}")
            msg = getattr(event.status, "message", None)
            if msg and hasattr(msg, "parts"):
                for idx, p in enumerate(msg.parts):
                    if hasattr(p, "root"):
                        r = p.root
                        if isinstance(r, TextPart):
                            print(f"  Part {idx} (Text): {r.text[:120]}...")
                        elif isinstance(r, DataPart):
                            print(f"  Part {idx} (Data, mime={r.metadata.get('mimeType')}): {str(r.data)[:120]}...")

async def main():
    project_id = os.getenv("PROJECT_ID", "uppdemos")
    location = os.getenv("LOCATION", "us-central1")
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"
    os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
    os.environ["GOOGLE_CLOUD_LOCATION"] = location
    vertexai.init(project=project_id, location=location)

    print("=" * 70)
    print("  Testing KPMG Translation Assistant Executor Locally")
    print("=" * 70)
    print(f"  Project:  {project_id}")
    print(f"  Location: {location}")

    executor = KPMGTranslationExecutor()
    event_queue = MockEventQueue()

    user_query = "Translate sample_doc.pdf to Spanish using NO_ATTRIBUTION"
    print(f"\nUser Query: '{user_query}'")

    context = RequestContext(
        request=MessageSendParams(
            message=Message(
                message_id="msg_001",
                role="user",
                parts=[Part(root=TextPart(text=user_query))],
            )
        ),
        task_id="test_task_001",
        context_id="test_context_001",
    )

    await executor.execute(context, event_queue)

    print("\n" + "=" * 70)
    print("  Verification Results")
    print("=" * 70)

    found_a2ui = False
    html_content = ""
    for ev in event_queue.events:
        msg = getattr(ev.status, "message", None) if hasattr(ev, "status") else None
        if msg and hasattr(msg, "parts"):
            for p in msg.parts:
                r = getattr(p, "root", None)
                if isinstance(r, DataPart) and r.metadata.get("mimeType") == "application/json+a2ui":
                    found_a2ui = True
                    # Extract the HTML from WebFrameSrcdoc
                    items = [r.data] if isinstance(r.data, dict) else r.data
                    for item in items:
                        if isinstance(item, dict):
                            su = item.get("surfaceUpdate", {})
                            for comp in su.get("components", []):
                                wf = comp.get("component", {}).get("WebFrameSrcdoc", {})
                                if wf and "htmlContent" in wf:
                                    html_content = wf["htmlContent"].get("literalString", "")
                                    break

    if found_a2ui:
        print("✓ Successfully generated A2UI DataPart (application/json+a2ui)")
        if html_content:
            print("✓ Successfully generated WebFrameSrcdoc HTML payload")
            preview_file = _ROOT / "kpmg_dashboard_preview.html"
            with open(preview_file, "w", encoding="utf-8") as f:
                f.write(html_content)
            print(f"✓ Saved local HTML preview to: {preview_file}")
            print(f"✓ CSP Meta Check: {'connect-src \'none\'' in html_content}")
            print(f"✓ Watermark Tag Check: {'NO_ATTRIBUTION' in html_content}")
        else:
            print("✗ WebFrameSrcdoc htmlContent was empty!")
    else:
        print("✗ No A2UI DataPart found in event queue!")

if __name__ == "__main__":
    asyncio.run(main())
