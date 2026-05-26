import logging
import os
from typing import Any, Optional, List, Protocol, Union
from collections.abc import AsyncIterable
import uuid

# A2A SDK Imports
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    Part,
    TextPart,
    DataPart,
    TransportProtocol,
    TaskState,
    Message
)
from a2a.utils import new_task

# Google ADK Imports
from google.adk.agents.llm_agent import LlmAgent
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.sessions import InMemorySessionService
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.tools import base_tool, base_toolset, ToolContext
from google.genai import types

BaseTool = base_tool.BaseTool
BaseToolset = base_toolset.BaseToolset

logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# Constants & HTML Templates
# ---------------------------------------------------------

A2UI_EXTENSION_BASE_URI = "https://a2ui.org/a2a-extension/a2ui"
A2UI_MIME_TYPE = "application/json+a2ui"

AGENT_A2UI_COMPONENTS = {
    "type": "ARRAY",
    "description": "A list containing all UI components for the surface.",
    "items": {
        "type": "OBJECT",
        "properties": {
            "id": {"type": "STRING"},
            "weight": {"type": "NUMBER"},
            "component": {
                "type": "OBJECT",
                "properties": {
                    "Text": {
                        "type": "OBJECT",
                        "properties": {
                            "text": {
                                "type": "OBJECT",
                                "properties": {
                                    "literalString": {"type": "STRING"},
                                    "path": {"type": "STRING"}
                                }
                            },
                            "usageHint": {
                                "type": "STRING",
                                "enum": ["h1", "h2", "h3", "h4", "h5", "caption", "body"]
                            }
                        },
                        "required": ["text"]
                    },
                    "Image": {
                        "type": "OBJECT",
                        "properties": {
                            "url": {
                                "type": "OBJECT",
                                "properties": {
                                    "literalString": {"type": "STRING"},
                                    "path": {"type": "STRING"}
                                }
                            },
                            "fit": {"type": "STRING", "enum": ["contain", "cover", "fill", "none", "scale-down"]},
                            "usageHint": {"type": "STRING", "enum": ["icon", "avatar", "smallFeature", "mediumFeature", "largeFeature", "header"]}
                        },
                        "required": ["url"]
                    },
                    "WebFrameSrcdoc": {
                        "type": "OBJECT",
                        "description": "Renders a specific application view (like Jira or a Dashboard).",
                        "properties": {
                            "view_type": {
                                "type": "STRING",
                                "description": "The name of the UI component to render. Use 'IssueTracker' for Jira tickets.",
                                "enum": ["IssueTracker", "UserProfile", "AnalyticsChart"]
                            },
                            "height": {"type": "NUMBER"}
                        },
                        "required": ["view_type"]
                    },
                    "WebFrameUrl": {
                        "type": "OBJECT",
                        "description": "Renders a specific webpage in an iframe",
                        "properties": {
                            "url": {
                                "type": "OBJECT",
                                "properties": {
                                    "literalString": {"type": "STRING"},
                                    "path": {"type": "STRING"},
                                },
                            },
                            "height": {"type": "NUMBER"},
                        },
                        "required": ["url"],
                    }
                }
            }
        },
        "required": ["id", "component"]
    }
}

ISSUE_TRACKER = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="Content-Security-Policy" content="connect-src 'none'">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kanban Board</title>
    <style>
        /* Design System Variables */
        :root {
            --b500: #0747A6; /* Global nav blue */
            --b400: #0052CC; /* Primary buttons/links */
            --n0: #FFFFFF;
            --n10: #FAFBFC; /* App background */
            --n20: #F4F5F7; /* Hover states */
            --n30: #EBECF0; /* Column background */
            --n40: #DFE1E6; /* Borders */
            --n100: #7A869A; /* Secondary text */
            --n500: #42526E; /* Subheadings */
            --n800: #172B4D; /* Primary text */
            --card-shadow: 0 1px 2px rgba(9, 30, 66, 0.25);
            --focus-ring: 0 0 0 2px #4C9AFF;
        }

        * {
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, "Fira Sans", "Droid Sans", "Helvetica Neue", sans-serif;
            margin: 0;
            display: flex;
            height: 100vh;
            background-color: var(--n0);
            color: var(--n800);
            overflow: hidden;
            font-size: 14px;
        }

        /* Custom Scrollbars */
        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #C1C7D0; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #A5ADBA; }

        /* --- NAVIGATION --- */
        /* Global Sidebar (Dark Blue) */
        .global-nav {
            width: 64px;
            background-color: var(--b500);
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 16px 0;
            flex-shrink: 0;
            z-index: 100;
        }

        .nav-item {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            margin-bottom: 12px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background 0.2s;
            color: white;
            font-weight: bold;
            font-size: 18px;
        }

        .nav-item.logo {
            background: #2684FF; /* Logo icon color */
            margin-bottom: 24px;
        }

        .nav-item:not(.logo):hover { background: rgba(255, 255, 255, 0.2); }

        /* Project Sidebar (Light Gray) */
        .project-nav {
            width: 240px;
            background-color: var(--n10);
            border-right: 1px solid var(--n40);
            display: flex;
            flex-direction: column;
            padding: 24px 16px;
            flex-shrink: 0;
        }

        .project-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 24px;
        }

        .project-icon {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, #FF7A00, #FFB800);
            border-radius: 3px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        }

        .project-info h3 { margin: 0; font-size: 14px; font-weight: 600; }
        .project-info p { margin: 2px 0 0 0; font-size: 12px; color: var(--n100); }

        .menu-item {
            padding: 8px 12px;
            border-radius: 3px;
            cursor: pointer;
            color: var(--n500);
            margin-bottom: 4px;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .menu-item:hover { background-color: var(--n30); }
        .menu-item.active {
            background-color: #E6EFFC;
            color: var(--b400);
            font-weight: 500;
        }

        /* --- MAIN CONTENT --- */
        main {
            flex-grow: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            background-color: var(--n0);
        }

        header {
            padding: 24px 40px 0;
        }

        .breadcrumb {
            font-size: 12px;
            color: var(--n100);
            margin-bottom: 12px;
        }

        h2 {
            margin: 0 0 16px 0;
            font-weight: 500;
            font-size: 24px;
            letter-spacing: -0.01em;
        }

        .filters {
            display: flex;
            gap: 16px;
            padding: 0 40px 24px;
            align-items: center;
        }

        .search-bar {
            padding: 6px 12px;
            border: 2px solid var(--n40);
            border-radius: 3px;
            width: 200px;
            font-size: 14px;
            background: var(--n10);
            color: var(--n800);
            outline: none;
        }

        .search-bar:focus {
            border-color: var(--b400);
            background: var(--n0);
        }

        .filter-avatars {
            display: flex;
            margin-left: 8px;
        }

        .filter-btn {
            background: none;
            border: none;
            color: var(--n500);
            cursor: pointer;
            font-size: 14px;
            padding: 6px 12px;
            border-radius: 3px;
        }

        .filter-btn:hover { background: var(--n20); }

        /* --- BOARD & COLUMNS --- */
        .board {
            display: flex;
            padding: 0 40px 24px;
            gap: 16px;
            flex-grow: 1;
            overflow-x: auto;
            overflow-y: hidden;
            align-items: flex-start;
        }

        .column {
            background-color: var(--n30);
            width: 272px;
            min-width: 272px;
            border-radius: 3px;
            display: flex;
            flex-direction: column;
            max-height: 100%;
            transition: background-color 0.2s ease;
        }

        .column-header {
            padding: 12px 14px;
            font-size: 12px;
            font-weight: 600;
            color: var(--n100);
            text-transform: uppercase;
            letter-spacing: 0.04em;
            position: sticky;
            top: 0;
            background-color: var(--n30);
            border-radius: 3px 3px 0 0;
        }

        .task-list {
            padding: 0 8px 8px 8px;
            min-height: 100px;
            flex-grow: 1;
            overflow-y: auto;
        }

        /* --- CARDS (ISSUES) --- */
        .card {
            background: var(--n0);
            border-radius: 3px;
            padding: 12px;
            margin-bottom: 8px;
            box-shadow: var(--card-shadow);
            cursor: grab;
            transition: background 0.1s ease-in-out, box-shadow 0.1s;
            user-select: none;
            position: relative;
        }

        .card:hover {
            background: var(--n10);
        }

        .card:active {
            cursor: grabbing;
        }

        .card-title {
            font-size: 14px;
            margin-bottom: 16px;
            line-height: 1.4;
            color: var(--n800);
        }

        .card-footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .card-footer-left, .card-footer-right {
            display: flex;
            align-items: center;
            gap: 6px;
        }

        /* Icons & Tags */
        .issue-type {
            width: 16px;
            height: 16px;
            border-radius: 3px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 10px;
            color: white;
        }
        .type-task { background-color: #4BADE8; }
        .type-story { background-color: #57D9A3; }
        .type-bug { background-color: #E5493A; }

        .issue-key {
            font-size: 12px;
            color: var(--n500);
            font-weight: 500;
        }

        .priority {
            width: 16px;
            height: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
        }
        .pri-high { color: #E5493A; }
        .pri-med { color: #FF8B00; }

        .avatar {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 500;
            font-size: 11px;
            color: white;
            box-shadow: 0 0 0 2px var(--n0);
        }

        /* Drag and Drop Visual States */
        .dragging {
            opacity: 0.5;
            transform: rotate(3deg);
            box-shadow: 0 5px 10px rgba(9, 30, 66, 0.15);
        }

        .drag-over {
            background-color: #E2E4E9; /* Slightly darker grey for drop target */
        }
    </style>
</head>
<body>

    <aside class="global-nav">
        <div class="nav-item logo" title="Home">K</div>
        <div class="nav-item" title="Search">🔍</div>
        <div class="nav-item" title="Create" style="background: rgba(255,255,255,0.2);">+</div >
    </aside>

    <aside class="project-nav">
        <div class="project-header">
            <div class="project-icon">P</div>
            <div class="project-info">
                <h3>Phoenix Project</h3>
                <p>Software project</p>
            </div>
        </div>
        <div class="menu-item">📊 Roadmap</div>
        <div class="menu-item">📋 Backlog</div>
        <div class="menu-item active">📦 Active sprints</div>
        <div class="menu-item">📈 Reports</div>
        <div class="menu-item">⚙️ Project settings</div>
    </aside>

    <main>
        <header>
            <div class="breadcrumb">Projects / Phoenix Project / Active sprints</div>
            <h2>PX Sprint 1</h2>
        </header>

        <div class="filters">
            <input type="text" class="search-bar" placeholder="Search this board">
            <div class="filter-avatars">
                <div class="avatar" style="background: #0052CC; z-index: 3;">JD</div>
                <div class="avatar" style="background: #00875A; z-index: 2; margin-left: -8px;">AS</div>
                <div class="avatar" style="background: #FF5630; z-index: 1; margin-left: -8px;">MK</div>
            </div>
            <button class="filter-btn">Only My Issues</button>
            <button class="filter-btn">Recently Updated</button>
        </div>

        <div class="board">
            <div class="column" ondragover="allowDrop(event)" ondragleave="clearStatus(event)" ondrop="drop(event)">
                <div class="column-header">To Do <span style="font-weight: normal; margin-left: 4px;">2</span></div>
                <div class="task-list" id="todo">

                    <div class="card" draggable="true" ondragstart="drag(event)" id="task-1">
                        <div class="card-title">Setup project repository and CSP headers</div>
                        <div class="card-footer">
                            <div class="card-footer-left">
                                <div class="issue-type type-task" title="Task">✓</div>
                                <span class="issue-key">PX-12</span>
                            </div>
                            <div class="card-footer-right">
                                <div class="priority pri-high" title="Highest">↑</div>
                                <div class="avatar" style="background: #0052CC;">JD</div>
                            </div>
                        </div>
                    </div>

                    <div class="card" draggable="true" ondragstart="drag(event)" id="task-2">
                        <div class="card-title">Define API security protocols to prevent CSRF</div>
                        <div class="card-footer">
                            <div class="card-footer-left">
                                <div class="issue-type type-story" title="Story">🔖</div>
                                <span class="issue-key">PX-14</span>
                            </div>
                            <div class="card-footer-right">
                                <div class="priority pri-med" title="Medium">=</div>
                                <div class="avatar" style="background: #00875A;">AS</div>
                            </div>
                        </div>
                    </div>

                </div>
            </div>

            <div class="column" ondragover="allowDrop(event)" ondragleave="clearStatus(event)" ondrop="drop(event)">
                <div class="column-header">In Progress <span style="font-weight: normal; margin-left: 4px;">1</span></div>
                <div class="task-list" id="inprogress">

                    <div class="card" draggable="true" ondragstart="drag(event)" id="task-3">
                        <div class="card-title">Build Kanban drag-and-drop UI with native HTML5</div>
                        <div class="card-footer">
                            <div class="card-footer-left">
                                <div class="issue-type type-bug" title="Bug">●</div>
                                <span class="issue-key">PX-15</span>
                            </div>
                            <div class="card-footer-right">
                                <div class="priority pri-high" title="High">↑</div>
                                <div class="avatar" style="background: #FF5630;">MK</div>
                            </div>
                        </div>
                    </div>

                </div>
            </div>

            <div class="column" ondragover="allowDrop(event)" ondragleave="clearStatus(event)" ondrop="drop(event)">
                <div class="column-header">Done <span style="font-weight: normal; margin-left: 4px;">1</span></div>
                <div class="task-list" id="done">

                    <div class="card" draggable="true" ondragstart="drag(event)" id="task-4">
                        <div class="card-title">Initial requirements gathering with stakeholders</div>
                        <div class="card-footer">
                            <div class="card-footer-left">
                                <div class="issue-type type-story" title="Story">🔖</div>
                                <span class="issue-key">PX-04</span>
                            </div>
                            <div class="card-footer-right">
                                <div class="priority pri-med" title="Medium">=</div>
                                <div class="avatar" style="background: #0052CC;">JD</div>
                            </div>
                        </div>
                    </div>

                </div>
            </div>
        </div>
    </main>

    <script>
        // Prevent default behavior to allow drop
        function allowDrop(ev) {
            ev.preventDefault();
            let column = ev.target.closest('.column');
            if (column) {
                column.classList.add('drag-over');
            }
        }

        // Remove visual cue when leaving column
        function clearStatus(ev) {
            let column = ev.target.closest('.column');
            if (column) {
                column.classList.remove('drag-over');
            }
        }

        // Set the ID of the dragged card
        function drag(ev) {
            ev.dataTransfer.setData("text/plain", ev.target.closest('.card').id);
            // Slight delay to allow the drag image to generate before changing opacity
            setTimeout(() => {
                ev.target.closest('.card').classList.add('dragging');
            }, 0);
        }

        // Handle the drop event
        function drop(ev) {
            ev.preventDefault();
            const data = ev.dataTransfer.getData("text/plain");
            const draggedElement = document.getElementById(data);

            if (draggedElement) {
                draggedElement.classList.remove('dragging');

                let target = ev.target.closest('.column');
                if (target) {
                    target.classList.remove('drag-over');
                    const list = target.querySelector('.task-list');

                    // Capture the original state (list ID) before moving
                    const oldState = draggedElement.parentElement.id;
                    const newState = list.id;

                    // Move the card in the DOM
                    list.appendChild(draggedElement);

                    // If the card was moved to a different column, emit the message
                    if (oldState !== newState) {
                        // Extract the issue key (e.g., "PX-12") to pass along
                        const issueKey = draggedElement.querySelector('.issue-key')?.innerText || '';

                        // Emit the event to the parent a2ui-web-frame
                        window.parent.postMessage({
                            type: 'a2ui_action',
                            action: 'cardMoved',
                            data: {
                                taskId: draggedElement.id,
                                issueKey: issueKey,
                                oldState: oldState,
                                newState: newState,
                                widgetId: 'kanbanBoard'
                            }
                        }, '*'); // Emit to parent window
                    }
                }
            }
        }

        // Clean up drag state if dropped outside a valid target
        document.addEventListener('dragend', (ev) => {
            const draggingCard = document.querySelector('.dragging');
            if (draggingCard) {
                draggingCard.classList.remove('dragging');
            }
            document.querySelectorAll('.drag-over').forEach(col => col.classList.remove('drag-over'));
        });
    </script>
</body>
</html>
"""

UNKNOWN_COMPONENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        .unknown-component-container {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 100%;
            height: 100%;
            min-height: 200px;
            background-color: #FAFBFC;
            border: 2px dashed #DFE1E6;
            border-radius: 6px;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, sans-serif;
            padding: 32px;
            box-sizing: border-box;
        }

        .unknown-component-content {
            text-align: center;
            max-width: 320px;
        }

        .unknown-component-icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 48px;
            height: 48px;
            background-color: #EBECF0;
            color: #42526E;
            border-radius: 8px;
            margin-bottom: 16px;
            font-size: 24px;
            font-weight: bold;
        }

        .unknown-component-title {
            margin: 0 0 8px 0;
            color: #172B4D;
            font-size: 16px;
            font-weight: 600;
        }

        .unknown-component-message {
            margin: 0;
            color: #7A869A;
            font-size: 14px;
            line-height: 1.5;
        }
    </style>
</head>
<body>

    <!-- Copy everything below this line into your application -->
    <div class="unknown-component-container">
        <div class="unknown-component-content">
            <div class="unknown-component-icon">?</div>
            <h3 class="unknown-component-title">Unknown Component</h3>
            <p class="unknown-component-message">
                The requested UI component could not be found or is not currently supported in this view.
            </p>
        </div>
    </div>

</body>
</html>
"""

# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def _agent_extensions(agent_card: AgentCard) -> List[str]:
    extensions = []
    if agent_card and hasattr(agent_card, "capabilities") and agent_card.capabilities and hasattr(agent_card.capabilities, "extensions") and agent_card.capabilities.extensions:
        for ext in agent_card.capabilities.extensions:
            if ext.uri and ext.uri.startswith(A2UI_EXTENSION_BASE_URI):
                extensions.append(ext.uri)
    return extensions

def _requested_a2ui_extensions(context: RequestContext) -> List[str]:
    requested_extensions = []
    if hasattr(context, "requested_extensions") and context.requested_extensions:
        requested_extensions.extend([ext for ext in context.requested_extensions if isinstance(ext, str) and ext.startswith(A2UI_EXTENSION_BASE_URI)])
    if hasattr(context, "message") and context.message and hasattr(context.message, "extensions") and context.message.extensions:
        requested_extensions.extend([ext for ext in context.message.extensions if isinstance(ext, str) and ext.startswith(A2UI_EXTENSION_BASE_URI)])
    return requested_extensions

def _version_key(uri: str) -> tuple:
    version_str = uri.replace(f"{A2UI_EXTENSION_BASE_URI}/v", "")
    from packaging.version import parse as parse_version
    return parse_version(version_str)

def _select_newest_a2ui_extension(requested_extensions: List[str], agent_advertised_extensions: List[str]) -> Optional[str]:
    matched_extensions = [uri for uri in requested_extensions if uri in agent_advertised_extensions]
    if not matched_extensions:
        return None
    return max(matched_extensions, key=_version_key)

def try_activate_a2ui_extension(context: RequestContext, agent_card: AgentCard) -> Optional[str]:
    requested_extensions = _requested_a2ui_extensions(context)
    if not requested_extensions:
        return None
    agent_advertised_extensions = _agent_extensions(agent_card)
    if not agent_advertised_extensions:
        return None
    selected_uri = _select_newest_a2ui_extension(requested_extensions, agent_advertised_extensions)
    if selected_uri:
        context.add_activated_extension(selected_uri)
        return selected_uri.replace(f"{A2UI_EXTENSION_BASE_URI}/v", "")
    return None

# ---------------------------------------------------------
# A2UI Tooling
# ---------------------------------------------------------

class HtmlRenderManager(Protocol):
    async def render_html(self, view_type: str, data: dict[str, Any], context: Any) -> str: ...

class AppHtmlManager():
    async def render_html(self, view_type: str, data: dict[str, Any], context: Any) -> str:
        if view_type == "IssueTracker":
            return ISSUE_TRACKER
        return UNKNOWN_COMPONENT

class BaseA2UIComponentHandler():
    @classmethod
    def get_name(cls) -> str: raise NotImplementedError
    async def hydrate(self, llm_args: dict[str, Any], tool_context: ToolContext) -> dict[str, Any]: return llm_args

class WebFrameSrcdocHandler(BaseA2UIComponentHandler):
    def __init__(self, html_manager: HtmlRenderManager): self._html_manager = html_manager
    @classmethod
    def get_name(cls) -> str: return "WebFrameSrcdoc"
    async def hydrate(self, llm_args: dict[str, Any], tool_context: ToolContext) -> dict[str, Any]:
        view_type = llm_args.get("view_type")
        data_args = llm_args.get("data", {})
        try:
            html_content = await self._html_manager.render_html(view_type, data_args, tool_context)
        except Exception as e:
            logging.error(f"HTML Rendering failed for '{view_type}': {e}")
            html_content = f"<div class='error'>Failed to load {view_type}</div>"
        return {"htmlContent": {"literalString": html_content}, "interactionMode": "readOnly"}

class BeginRenderingTool(BaseTool):
    def __init__(self):
        super().__init__(name="beginRendering", description="Signals the client to begin rendering a surface.")
        self._declaration = types.FunctionDeclaration(
            name=self.name,
            description=self.description,
            parameters_json_schema={
                "type": "OBJECT",
                "properties": {
                    "surfaceId": {"type": "STRING"},
                    "root": {"type": "STRING"},
                    "styles": {"type": "OBJECT", "properties": {"font": {"type": "STRING"}, "primaryColor": {"type": "STRING"}}}
                },
                "required": ["root", "surfaceId"]
            }
        )
    def _get_declaration(self) -> types.FunctionDeclaration: return self._declaration
    async def run_async(self, *, args: dict[str, Any], tool_context: ToolContext) -> dict[str, Any]: return {"beginRendering": args}

class SurfaceUpdateTool(BaseTool):
    def __init__(self, component_schemas: dict[str, Any], handlers: list[BaseA2UIComponentHandler] | None = None):
        super().__init__(name="surfaceUpdate", description="Updates a surface with a new set of components.")
        self._handlers = {h.get_name(): h for h in (handlers or [])}
        self._declaration = types.FunctionDeclaration(
            name=self.name,
            description=self.description,
            parameters_json_schema={"type": "OBJECT", "properties": {"surfaceId": {"type": "STRING"}, "components": component_schemas}, "required": ["surfaceId", "components"]}
        )
    def _get_declaration(self) -> types.FunctionDeclaration: return self._declaration
    async def run_async(self, *, args: dict[str, Any], tool_context: ToolContext) -> dict[str, Any]:
        if "components" in args and self._handlers:
            args["components"] = await self._hydrate_components(args["components"], tool_context)
        return {"surfaceUpdate": args}
    async def _hydrate_components(self, components: list[dict[str, Any]], tool_context: ToolContext) -> list[dict[str, Any]]:
        hydrated_components = []
        for comp_node in components:
            component_wrapper = comp_node.get("component", {})
            if component_wrapper:
                comp_type = list(component_wrapper.keys())[0]
                if comp_type in self._handlers:
                    comp_data = component_wrapper[comp_type]
                    hydrated_data = await self._handlers[comp_type].hydrate(comp_data, tool_context)
                    comp_node["component"][comp_type] = hydrated_data
            hydrated_components.append(comp_node)
        return hydrated_components

class DataModelUpdateTool(BaseTool):
    def __init__(self):
        super().__init__(name="dataModelUpdate", description="Updates the data model for a surface.")
        self._declaration = types.FunctionDeclaration(
            name=self.name,
            description=self.description,
            parameters_json_schema={
                "type": "OBJECT",
                "properties": {"surfaceId": {"type": "STRING"}, "path": {"type": "STRING"}, "contents": {"type": "ARRAY", "items": {"type": "OBJECT", "properties": {"key": {"type": "STRING"}}, "required": ["key"]}}},
                "required": ["contents", "surfaceId"]
            }
        )
    def _get_declaration(self) -> types.FunctionDeclaration: return self._declaration
    async def run_async(self, *, args: dict[str, Any], tool_context: ToolContext) -> dict[str, Any]: return {"dataModelUpdate": args}

class DeleteSurfaceTool(BaseTool):
    def __init__(self):
        super().__init__(name="deleteSurface", description="Signals the client to delete the surface.")
        self._declaration = types.FunctionDeclaration(
            name=self.name,
            description=self.description,
            parameters_json_schema={"type": "OBJECT", "properties": {"surfaceId": {"type": "STRING"}}, "required": ["surfaceId"]}
        )
    def _get_declaration(self) -> types.FunctionDeclaration: return self._declaration
    async def run_async(self, *, args: dict[str, Any], tool_context: ToolContext) -> dict[str, Any]: return {"deleteSurface": args}

class A2UIToolset(BaseToolset):
    def __init__(self, component_schemas: dict[str, Any], handlers: list[BaseA2UIComponentHandler] | None = None):
        super().__init__()
        self._tools = [BeginRenderingTool(), SurfaceUpdateTool(component_schemas=component_schemas, handlers=handlers), DataModelUpdateTool(), DeleteSurfaceTool()]
    async def get_tools(self, readonly_context: Any = None) -> list[BaseTool]: return self._tools

# ---------------------------------------------------------
# Agent Executor
# ---------------------------------------------------------

ROLE_DESCRIPTION = (
    "You are a friendly, helpful chat assistant. You engage in natural"
    " conversation, answer questions, tell jokes, and help with general"
    " knowledge topics. You provide responses in plain text."
)

WORKFLOW_DESCRIPTION = """
- When the user sends a greeting, respond warmly and invite them to chat.
- When the user asks a question, provide a helpful, concise text answer.
- For complex tasks (e.g., forms, lists, detailed reports), or when asked to show the Issue Tracker or Kanban Board, you MUST provide the UI by outputting a specific JSON array of A2UI actions wrapped in `<a2ui-json>` and `</a2ui-json>` tags.
- The array MUST contain first a `beginRendering` action, followed by a `surfaceUpdate` action.
- The response must consist of your natural language response, followed strictly by the tags containing the JSON payload.

CRITICAL RENDERING RULES:
The component you name in beginRendering.root MUST be present as a components[].id in a surfaceUpdate for the same surface. If the root component ID does not appear in the surface's components map, the renderer builds an empty tree and nothing is shown.
Every beginRendering and surfaceUpdate for the same UI MUST use the same surfaceId. Messages with different surfaceIds are routed to different surfaces and will not be combined.
Concretely: if you emit beginRendering: {root: "X", surfaceId: "S"}, then you MUST also emit surfaceUpdate: {surfaceId: "S", components: [{id: "X", ...}, ...]}. The string "X" must be byte-identical in both messages.

FEW-SHOT EXAMPLES:

User: Show me the Kanban board
Assistant: Sure thing! Here is your Kanban board.
<a2ui-json>
[
  { "beginRendering": { "surfaceId": "main_surface", "root": "kanban" } },
  { "surfaceUpdate": { "surfaceId": "main_surface", "components": [ { "id": "kanban", "component": { "WebFrameSrcdoc": { "view_type": "IssueTracker", "height": 600 } } } ] } }
]
</a2ui-json>

User: help me find my jira tickets
Assistant: I have pulled up your Jira tickets for you.
<a2ui-json>
[
  { "beginRendering": { "surfaceId": "main_surface", "root": "kanban" } },
  { "surfaceUpdate": { "surfaceId": "main_surface", "components": [ { "id": "kanban", "component": { "WebFrameSrcdoc": { "view_type": "IssueTracker", "height": 600 } } } ] } }
]
</a2ui-json>

CRITICAL: You MUST follow these examples exactly and emit BOTH `beginRendering` (with root matching the component id) and `surfaceUpdate` in the array wrapped in `<a2ui-json>` tags when asked for the board or tickets. Do not output text only.
"""

UI_DESCRIPTION = """
The client parses everything between `<a2ui-json>` and `</a2ui-json>` as the UI state.
You must produce a valid JSON array containing the A2UI actions in order.
"""

class ChatAgent(AgentExecutor):
    def __init__(self, base_url: str, tools: BaseToolset):
        super().__init__()
        self.base_url = base_url
        self._agent = self._build_agent(tools)
        self._user_id = "remote_agent"
        self._runner = Runner(app_name=self._agent.name, agent=self._agent, artifact_service=InMemoryArtifactService(), session_service=InMemorySessionService(), memory_service=InMemoryMemoryService())

    def get_agent_card(self) -> AgentCard:
        capabilities = AgentCapabilities(
            streaming=False,
            extensions=[{"uri": "https://a2ui.org/a2a-extension/a2ui/v0.8", "description": "Ability to render A2UI", "required": True, "params": {"supportedCatalogIds": ["https://a2ui.org/specification/v0_8/standard_catalog_definition.json", "https://vertexaisearch.cloud.google.com/a2ui/v0_8/gemini_enterprise_custom_catalog.json"], "acceptsInlineCatalogs": True}}]
        )
        return AgentCard(name="A2UI_IFrame_Agent", description="Agent with iFrame", version="1.0.0", url=self.base_url, defaultInputModes=["text/plain", "application/json"], skills=[], defaultOutputModes=["text/plain", "application/json", "application/json+a2ui"], capabilities=capabilities, preferred_transport=TransportProtocol.http_json)

    def _build_agent(self, tools: BaseToolset) -> LlmAgent:
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        return LlmAgent(model=Gemini(model=model_name), name="chat_agent", description="A friendly chat assistant.", instruction=f"{ROLE_DESCRIPTION}\n{WORKFLOW_DESCRIPTION}\n{UI_DESCRIPTION}", tools=[])

    async def stream(self, query: str, session_id: str) -> AsyncIterable[dict[str, Any]]:
        session = await self._runner.session_service.get_session(app_name=self._agent.name, user_id=self._user_id, session_id=session_id)
        if session is None:
            session = await self._runner.session_service.create_session(app_name=self._agent.name, user_id=self._user_id, state={}, session_id=session_id)
        current_message = types.Content(role="user", parts=[types.Part.from_text(text=query)])
        
        final_parts = []
        text_responses = []
        
        async for event in self._runner.run_async(user_id=self._user_id, session_id=session.id, new_message=current_message):
            if event.is_final_response():
                for part in event.content.parts:
                    if getattr(part, "text", None):
                        text_responses.append(part.text)
                
                combined_text = "".join(text_responses)
                
                # Use regex to find content between tags
                import re
                pattern = re.compile(r"<a2ui-json>(.*?)</a2ui-json>", re.DOTALL)
                matches = list(pattern.finditer(combined_text))
                
                last_end = 0
                
                if matches:
                    for match in matches:
                        start, end = match.span()
                        text_before = combined_text[last_end:start].strip()
                        if text_before:
                            final_parts.append(Part(root=TextPart(text=text_before)))
                        
                        try:
                            json_str = match.group(1).strip()
                            # Sanitize JSON (remove code fences)
                            if json_str.startswith("```json"):
                                json_str = json_str[len("```json"):]
                            elif json_str.startswith("```"):
                                json_str = json_str[len("```"):]
                            if json_str.endswith("```"):
                                json_str = json_str[:-len("```")]
                            json_str = json_str.strip()
                            
                            import json
                            actions = json.loads(json_str)
                            
                            if isinstance(actions, list):
                                for action in actions:
                                    # Hydration fallback for IssueTracker
                                    if "surfaceUpdate" in action and "components" in action["surfaceUpdate"]:
                                        for comp in action["surfaceUpdate"]["components"]:
                                            if "component" in comp and "WebFrameSrcdoc" in comp["component"]:
                                                v_type = comp["component"]["WebFrameSrcdoc"].get("view_type", "IssueTracker")
                                                html_str = ISSUE_TRACKER if v_type == "IssueTracker" else UNKNOWN_COMPONENT
                                                comp["component"]["WebFrameSrcdoc"] = {
                                                    "htmlContent": {"literalString": html_str},
                                                    "interactionMode": "readOnly"
                                                }
                                    final_parts.append(
                                        Part(
                                            root=DataPart(
                                                data=action,
                                                kind="data",
                                                metadata={"mimeType": "application/json+a2ui"}
                                            )
                                        )
                                    )
                            else:
                                # Handle single object fallback
                                final_parts.append(
                                    Part(
                                        root=DataPart(
                                            data=actions,
                                            kind="data",
                                            metadata={"mimeType": "application/json+a2ui"}
                                        )
                                    )
                                )
                        except Exception as e:
                            logger.error(f"Failed to parse A2UI JSON block: {e}")
                            final_parts.append(Part(root=TextPart(text=f"\n[Error parsing UI payload: {e}]")))
                        
                        last_end = end
                    
                    trailing = combined_text[last_end:].strip()
                    if trailing:
                        final_parts.append(Part(root=TextPart(text=trailing)))
                else:
                    final_parts.append(Part(root=TextPart(text=combined_text)))
                
                yield {"is_task_complete": True, "parts": final_parts}
                return

    async def execute(self, context: Any, event_queue: Any) -> None:
        use_ui = try_activate_a2ui_extension(context, self.get_agent_card())
        query = ""
        if context.message and context.message.parts:
            for part in context.message.parts:
                if isinstance(part.root, DataPart) and "userAction" in part.root.data:
                    ui_event_part = part.root.data["userAction"]
                    action = ui_event_part.get("actionName")
                    action_context = ui_event_part.get("context", {})
                    query = f"USER_UI_EVENT: {action} with {action_context}"
        if not query:
            try: query = context.get_user_input()
            except: query = "Hello"
        task = context.current_task or new_task(context.message)
        await event_queue.enqueue_event(task)
        updater = TaskUpdater(event_queue, task.id, task.context_id)
        await updater.submit()
        await updater.start_work()
        try:
            async for chunk in self.stream(query=query, session_id=task.context_id):
                parts = chunk.get("parts", [])
                is_complete = chunk.get("is_task_complete", False)
                if parts:
                    msg = Message(message_id=str(uuid.uuid4()), role="agent", parts=parts, context_id=task.context_id)
                    if is_complete:
                        await updater.update_status(TaskState.completed, msg, final=True)
                    else:
                        await updater.update_status(TaskState.working, msg)
        except Exception as e:
            err_msg = Message(message_id=str(uuid.uuid4()), role="agent", parts=[TextPart(text=f"Error: {e}")], context_id=task.context_id)
            await updater.update_status(TaskState.failed, err_msg, final=True)
            raise

    async def cancel(self, request: Any) -> None:
        """Handles a request to cancel the current ongoing task."""
        logger.info(f"Cancellation requested for task.")
        pass

def my_chat_agent_builder():
    html_manager = AppHtmlManager()
    web_frame_handler = WebFrameSrcdocHandler(html_manager=html_manager)
    a2ui_toolset = A2UIToolset(component_schemas=AGENT_A2UI_COMPONENTS, handlers=[web_frame_handler])
    return ChatAgent(base_url="https://discoveryengine.googleapis.com", tools=a2ui_toolset)
