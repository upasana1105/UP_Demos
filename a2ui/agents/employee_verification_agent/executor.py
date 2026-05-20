"""
Employee Verification Executor - A2A protocol handler.

Handles:
  - Text queries (user types in chat)
  - A2UI button actions (submit_verification, verify_as_is, select_employee)
  - Parses A2UI JSON from LLM responses and wraps them as DataParts

Compatible with a2a-sdk 0.3.x (pydantic-based TextPart/DataPart/Part/Message).
"""

import logging
import re
import json
import uuid
from typing import List

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import TaskState, TextPart, DataPart, UnsupportedOperationError, Message, Role, Part
from a2a.utils.errors import ServerError

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

from .agent import get_agent

logger = logging.getLogger(__name__)

A2UI_MIME_TYPE = "application/json+a2ui"
A2UI_OPEN_TAG = "<a2ui-json>"
A2UI_CLOSE_TAG = "</a2ui-json>"

_A2UI_BLOCK_RE = re.compile(
    f"{re.escape(A2UI_OPEN_TAG)}(.*?){re.escape(A2UI_CLOSE_TAG)}", re.DOTALL
)


def _sanitize_json(raw: str) -> str:
    """Remove markdown code fences from JSON strings."""
    s = raw.strip()
    if s.startswith("```json"):
        s = s[len("```json"):]
    elif s.startswith("```"):
        s = s[len("```"):]
    if s.endswith("```"):
        s = s[:-len("```")]
    return s.strip()


def _create_a2ui_part(data: dict) -> Part:
    """Create an A2UI DataPart."""
    return Part(root=DataPart(data=data, metadata={"mimeType": A2UI_MIME_TYPE}))


def parse_response_to_parts(content: str) -> List[Part]:
    """Parse LLM response text, extracting A2UI JSON blocks as DataParts."""
    matches = list(_A2UI_BLOCK_RE.finditer(content))
    if not matches:
        clean = content.strip()
        return [Part(root=TextPart(text=clean))] if clean else []

    parts: List[Part] = []
    last_end = 0

    for match in matches:
        start, end = match.span()
        text_before = content[last_end:start].strip()
        if text_before:
            parts.append(Part(root=TextPart(text=text_before)))
        try:
            json_str = _sanitize_json(match.group(1))
            payload = json.loads(json_str)
            if isinstance(payload, list):
                for item in payload:
                    parts.append(_create_a2ui_part(item))
            else:
                parts.append(_create_a2ui_part(payload))
        except Exception as e:
            logger.error(f"Failed to parse A2UI JSON block: {e}")
        last_end = end

    trailing = content[last_end:].strip()
    if trailing:
        parts.append(Part(root=TextPart(text=trailing)))

    return parts


def _build_query_from_action(action_name: str, context: dict) -> str:
    """Convert a UI action into a natural language query for the agent."""

    if action_name == "submit_verification":
        employee_id = context.get("employeeId", "Unknown")
        fields = []
        for key in ["address", "phone", "email", "emergencyContact", "emergencyPhone"]:
            if key in context:
                fields.append(f"{key}={context[key]}")
        fields_str = ", ".join(fields)
        return (
            f"SUBMIT_VERIFICATION: Employee {employee_id} submitted their verification form. "
            f"The submitted field values are: {fields_str}. "
            f"Compare these with the current database values. For any changed fields, "
            f"call update_employee_field for each change. Then call verify_employee. "
            f"Show a verification success card."
        )

    elif action_name == "verify_as_is":
        employee_id = context.get("employeeId", "Unknown")
        return (
            f"VERIFY_AS_IS: Employee {employee_id} confirmed their information is correct. "
            f"Call verify_employee with employee_id={employee_id} to mark them as verified. "
            f"Show a verification success card."
        )

    elif action_name == "select_employee":
        employee_id = context.get("employeeId", "Unknown")
        employee_name = context.get("employeeName", "")
        return (
            f"SELECT_EMPLOYEE: User selected employee {employee_name} (ID: {employee_id}). "
            f"Call lookup_employee with employee_id={employee_id} to get their full record, "
            f"then display the employee verification form with all their data."
        )

    elif action_name == "dismiss_modal":
        return "The user dismissed a confirmation dialog. Ask if there's anything else they need."

    else:
        return f"User submitted a UI action: {action_name} with data: {context}"


class EmployeeVerificationExecutor(AgentExecutor):
    """A2A executor for the Employee Verification Agent."""

    def __init__(self):
        self.agent = None
        self.runner = None

    def _init_agent(self):
        """Lazy-initialize the agent and runner."""
        if self.agent is None:
            self.agent = get_agent()
            self.runner = Runner(
                app_name="EmployeeVerificationAgent",
                agent=self.agent,
                artifact_service=InMemoryArtifactService(),
                session_service=InMemorySessionService(),
                memory_service=InMemoryMemoryService(),
            )
            logger.info("EmployeeVerificationExecutor initialized runner")

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute a request — handles both text input and UI button actions."""
        self._init_agent()

        query = ""
        ui_event_part = None

        # Check for A2UI button action in the message parts
        if context.message and context.message.parts:
            for part in context.message.parts:
                if isinstance(part.root, DataPart) and "userAction" in part.root.data:
                    ui_event_part = part.root.data["userAction"]
                    break

        if ui_event_part:
            logger.info(f"Received A2UI ClientEvent: {ui_event_part}")
            action_name = ui_event_part.get("name")
            action_context = ui_event_part.get("context", {})
            query = _build_query_from_action(action_name, action_context)
        else:
            query = context.get_user_input()

        logger.info(f"EmployeeVerificationExecutor executing query: {query}")

        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        await updater.submit()
        await updater.start_work()

        try:
            # Get or create session (maintains conversation context)
            session = await self.runner.session_service.get_session(
                app_name=self.runner.app_name,
                user_id="user",
                session_id=context.context_id,
            )
            if session is None:
                session = await self.runner.session_service.create_session(
                    app_name=self.runner.app_name,
                    user_id="user",
                    state={},
                    session_id=context.context_id,
                )

            content = types.Content(role="user", parts=[types.Part(text=query)])

            async for event in self.runner.run_async(
                session_id=session.id,
                user_id="user",
                new_message=content,
            ):
                if hasattr(event, "is_final_response") and event.is_final_response():
                    answer_text = ""
                    if event.content and event.content.parts:
                        answer_text = "\n".join(
                            [part.text for part in event.content.parts if part.text]
                        )

                    if answer_text:
                        final_parts = parse_response_to_parts(answer_text)
                        await updater.update_status(
                            TaskState.completed,
                            new_agent_parts_message(
                                final_parts,
                                context.context_id,
                                context.task_id,
                            ),
                            final=True,
                        )
                    else:
                        await updater.update_status(
                            TaskState.completed,
                            new_agent_parts_message(
                                [Part(root=TextPart(text="No response generated."))],
                                context.context_id,
                                context.task_id,
                            ),
                            final=True,
                        )
                    break

        except Exception as e:
            logger.error(f"Error in EmployeeVerificationExecutor: {e}", exc_info=True)
            await updater.update_status(
                TaskState.failed,
                message=Message(
                    message_id=str(uuid.uuid4()),
                    role=Role.agent,
                    parts=[TextPart(text=f"An error occurred: {str(e)}")]
                ),
            )
            raise

    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        raise ServerError(error=UnsupportedOperationError())
