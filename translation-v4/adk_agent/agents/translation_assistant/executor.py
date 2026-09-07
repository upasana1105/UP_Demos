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
KPMG Translation Assistant — A2A Executor.

Handles A2A protocol execution with self-healing A2UI injection.
Automatically appends the WebFrameSrcdoc translation dashboard iframe
after translate_and_audit_document completes.
"""

import json
import logging
import uuid
from typing import List

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    TaskState, TextPart, DataPart,
    Message, Role, Part,
)

try:
    from a2a.utils import new_agent_parts_message
except ImportError:
    def new_agent_parts_message(parts, context_id, task_id):
        return Message(
            message_id=str(uuid.uuid4()),
            role=Role.agent,
            parts=parts,
        )

from google.adk.runners import Runner
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types

from .agent import get_agent, AGENT_NAME
from .components import (
    _LAST_TRANSLATION_DATA,
    generate_translation_a2ui_tool,
    A2UI_MIME_TYPE,
)

logger = logging.getLogger(__name__)

def _create_a2ui_part(data: dict) -> Part:
    return Part(root=DataPart(data=data, metadata={"mimeType": A2UI_MIME_TYPE}))

class KPMGTranslationExecutor(AgentExecutor):
    """A2A Executor that bridges ADK agent turns and programmatically attaches A2UI iframe payloads."""

    def __init__(self):
        super().__init__()
        self._agent = get_agent()
        self._runner = Runner(
            app_name=AGENT_NAME,
            agent=self._agent,
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
            artifact_service=InMemoryArtifactService(),
        )

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        await updater.submit()
        await updater.start_work()

        query = context.get_user_input() if hasattr(context, "get_user_input") else "Translate document"
        if not query and context.message and context.message.parts:
            for p in context.message.parts:
                if hasattr(p, "root") and hasattr(p.root, "text"):
                    query = p.root.text
                    break

        logger.info(f"Executing translation query: '{query}'")

        try:
            session = await self._runner.session_service.get_session(
                app_name=self._runner.app_name,
                user_id="user",
                session_id=context.context_id,
            )
            if session is None:
                session = await self._runner.session_service.create_session(
                    app_name=self._runner.app_name,
                    user_id="user",
                    state={},
                    session_id=context.context_id,
                )

            content = types.Content(role="user", parts=[types.Part(text=query)])
            before_render_id = _LAST_TRANSLATION_DATA.get("render_id")

            final_parts: List[Part] = []
            answer_text = ""

            async for event in self._runner.run_async(
                session_id=session.id,
                user_id="user",
                new_message=content,
            ):
                if hasattr(event, "is_final_response") and event.is_final_response():
                    if event.content and event.content.parts:
                        answer_text = "\n".join([p.text for p in event.content.parts if p.text])

            if answer_text:
                final_parts.append(Part(root=TextPart(text=answer_text.strip())))
            else:
                final_parts.append(Part(root=TextPart(text="Translation and financial quality audit completed.")))

            # Self-healing: Check if a translation was executed this turn
            after_render_id = _LAST_TRANSLATION_DATA.get("render_id")
            if bool(_LAST_TRANSLATION_DATA) and after_render_id != before_render_id:
                logger.info("Appending KPMG Translation Dashboard A2UI WebFrameSrcdoc payload...")
                try:
                    a2ui_raw = generate_translation_a2ui_tool(_LAST_TRANSLATION_DATA)
                    inner = a2ui_raw
                    if inner.startswith("<a2ui-json>"):
                        inner = inner[len("<a2ui-json>"):].strip()
                    if inner.endswith("</a2ui-json>"):
                        inner = inner[:-len("</a2ui-json>")].strip()
                    payload = json.loads(inner)
                    if isinstance(payload, list):
                        for item in payload:
                            final_parts.append(_create_a2ui_part(item))
                    else:
                        final_parts.append(_create_a2ui_part(payload))
                    logger.info("✓ A2UI Translation Dashboard iframe successfully appended.")
                except Exception as a2ui_err:
                    logger.error(f"Failed to append A2UI payload: {a2ui_err}", exc_info=True)

            await updater.update_status(
                TaskState.completed,
                new_agent_parts_message(
                    final_parts,
                    context.context_id,
                    context.task_id,
                ),
                final=True,
            )

        except Exception as e:
            logger.error(f"Error in KPMGTranslationExecutor: {e}", exc_info=True)
            err_msg = new_agent_parts_message(
                [Part(root=TextPart(text=f"An error occurred during translation: {e}"))],
                context.context_id,
                context.task_id,
            )
            await updater.update_status(TaskState.failed, err_msg, final=True)

    async def cancel(self, request: RequestContext, event_queue: EventQueue) -> None:
        logger.info(f"Cancellation requested for task {request.task_id}")
