"""
Base A2UI Executor — Shared A2A protocol handler for all agents.

Each agent creates a thin subclass that just specifies which agent config
to load. All A2A/A2UI parsing, session management, and response handling
lives here.

Usage:
    class MyAgentExecutor(BaseA2UIExecutor):
        AGENT_CONFIG_NAME = "my_agent"
"""

import logging
import re
import json
import uuid
from typing import List

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    TaskState, TextPart, DataPart, UnsupportedOperationError,
    Message, Role, Part,
)
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

from agents._base.config_loader import load_agent_config

logger = logging.getLogger(__name__)

A2UI_MIME_TYPE = "application/json+a2ui"
A2UI_OPEN_TAG = "<a2ui-json>"
A2UI_CLOSE_TAG = "</a2ui-json>"

_A2UI_BLOCK_RE = re.compile(
    f"{re.escape(A2UI_OPEN_TAG)}(.*?){re.escape(A2UI_CLOSE_TAG)}", re.DOTALL
)


# ---------------------------------------------------------------------------
# Shared parsing helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Action-to-query builder (config-driven)
# ---------------------------------------------------------------------------

def build_query_from_action(action_name: str, context: dict, actions_config: dict) -> str:
    """Convert a UI action into a natural language query using config templates.

    Args:
        action_name: The action name from the A2UI button click.
        context: The action context dict from the button.
        actions_config: The 'agent.actions' section from the YAML config.
    """
    action_def = actions_config.get(action_name)

    if action_def is None:
        return f"User submitted a UI action: {action_name} with data: {context}"

    template = action_def.get("template", "")
    field_keys = action_def.get("fields", [])

    # Build fields string if this action has field definitions
    if field_keys:
        fields_parts = []
        for key in field_keys:
            if key in context:
                fields_parts.append(f"{key}={context[key]}")
        context["fields"] = ", ".join(fields_parts)

    # Format template with context values
    try:
        return template.format(**context)
    except KeyError:
        # Fallback: just dump what we have
        return f"{action_name}: {context}"


# ---------------------------------------------------------------------------
# Base Executor
# ---------------------------------------------------------------------------

class BaseA2UIExecutor(AgentExecutor):
    """Base A2A executor with A2UI support. Subclass and set AGENT_CONFIG_NAME."""

    # Subclasses MUST override this
    AGENT_CONFIG_NAME: str = None

    def __init__(self):
        if self.AGENT_CONFIG_NAME is None:
            raise ValueError(
                f"{self.__class__.__name__} must set AGENT_CONFIG_NAME "
                f"(e.g., AGENT_CONFIG_NAME = 'employee_verification')"
            )
        self.agent = None
        self.runner = None
        self._config = None

    def _get_config(self) -> dict:
        """Load and cache the agent config."""
        if self._config is None:
            self._config = load_agent_config(self.AGENT_CONFIG_NAME)
        return self._config

    def _init_agent(self):
        """Lazy-initialize the ADK agent and Runner."""
        if self.agent is not None:
            return

        # Import here to avoid circular imports at module level
        agent_module_name = f"agents.{self.AGENT_CONFIG_NAME}.agent"
        import importlib
        agent_module = importlib.import_module(agent_module_name)
        self.agent = agent_module.get_agent()

        config = self._get_config()
        agent_name = config.get("agent", {}).get("name", self.AGENT_CONFIG_NAME)

        self.runner = Runner(
            app_name=agent_name,
            agent=self.agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )
        logger.info(f"{self.__class__.__name__} initialized runner for {agent_name}")

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute a request — handles both text input and UI button actions."""
        self._init_agent()
        config = self._get_config()

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
            actions_config = config.get("agent", {}).get("actions", {})
            query = build_query_from_action(action_name, action_context, actions_config)
        else:
            query = context.get_user_input()

        logger.info(f"{self.__class__.__name__} executing query: {query}")

        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        await updater.submit()
        await updater.start_work()

        try:
            # Get or create session
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
            logger.error(
                f"Error in {self.__class__.__name__}: {e}", exc_info=True
            )
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
