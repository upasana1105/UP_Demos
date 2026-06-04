# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools import LongRunningFunctionTool, load_memory
from google.genai import types
import logging
from google.adk.plugins.bigquery_agent_analytics_plugin import (
    BigQueryAgentAnalyticsPlugin,
    BigQueryLoggerConfig,
)
from google.cloud import bigquery

import os
import google.auth

try:
    _, project_id = google.auth.default()
    if project_id:
        os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
        os.environ["GOOGLE_CLOUD_QUOTA_PROJECT"] = project_id
except Exception:
    pass

if not os.environ.get("GOOGLE_CLOUD_LOCATION"):
    os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

if not os.environ.get("GOOGLE_MAPS_API_KEY"):
    raise ValueError(
        "GOOGLE_MAPS_API_KEY environment variable is not set. Please ensure it is provided."
    )


# Tool for generating mock repair costs
def generate_repair_cost(severity: str, state: str = "") -> dict:
    """Generates itemized repair costs based on severity and state."""
    labor_multiplier = 1.0
    if state:
        state_lower = state.lower()
        if "ny" in state_lower or "new york" in state_lower:
            labor_multiplier = 1.5
        elif "ca" in state_lower or "california" in state_lower:
            labor_multiplier = 1.3

    severity = severity.lower()
    if "simple" in severity:
        base_labor = 200.00
        adjusted_labor = base_labor * labor_multiplier
        total_parts = 500.00
        return {
            "items": [
                {"part": "Bumper Repair", "cost": 350.00},
                {"part": "Labor (2 hours)", "cost": adjusted_labor},
                {"part": "Paint Touch-up", "cost": 150.00},
            ],
            "total_labor": adjusted_labor,
            "total_parts": total_parts,
            "total_cost": adjusted_labor + total_parts,
        }
    else:  # Complex
        base_labor = 1000.00
        adjusted_labor = base_labor * labor_multiplier
        total_parts = 3500.00
        return {
            "items": [
                {"part": "Fender Replacement", "cost": 1200.00},
                {"part": "Door Panel Repair", "cost": 800.00},
                {"part": "Labor (10 hours)", "cost": adjusted_labor},
                {"part": "Painting & Blending", "cost": 1500.00},
            ],
            "total_labor": adjusted_labor,
            "total_parts": total_parts,
            "total_cost": adjusted_labor + total_parts,
        }


async def auto_save_session_to_memory_callback(callback_context):
    await callback_context._invocation_context.memory_service.add_session_to_memory(
        callback_context._invocation_context.session
    )


def header_provider(context=None):
    import os
    from opentelemetry.propagate import inject

    headers = {}
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    print(f"DEBUG: header_provider - GOOGLE_MAPS_API_KEY is set: {bool(api_key)}")
    if api_key:
        headers["x-goog-api-key"] = api_key

    otel_headers = {}
    inject(otel_headers)
    headers.update(otel_headers)
    return headers


def get_maps_toolset() -> McpToolset:
    from opentelemetry.propagate import inject

    headers = {
        "X-Goog-Api-Key": os.environ.get("GOOGLE_MAPS_API_KEY"),
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }

    otel_headers = {}
    inject(otel_headers)
    headers.update(otel_headers)

    return McpToolset(
        connection_params=StreamableHTTPConnectionParams(
            url="https://mapstools.googleapis.com/mcp", headers=headers
        )
    )


def get_registry_maps_toolset() -> McpToolset:
    try:
        from google.adk.integrations.agent_registry import AgentRegistry

        registry = AgentRegistry(
            project_id=os.environ.get("GOOGLE_CLOUD_PROJECT"),
            location="global",
            header_provider=header_provider,
        )
        servers = registry.list_mcp_servers(
            filter_str="displayName:mapstools.googleapis.com", page_size=1
        )
        mcp_server_name = servers.get("mcpServers", [])[0]["name"]
        maps_toolset = registry.get_mcp_toolset(mcp_server_name)
        return maps_toolset
    except ImportError:
        print("AgentRegistry could not be imported")
        return None
    except Exception as e:
        print(f"Error getting maps toolset: {e}")
        return None


# --- Agents Definition ---
MODEL_NAME = os.environ.get("MODEL", "gemini-2.5-flash")


class RefreshingGemini(Gemini):
    @property
    def api_client(self):
        if "api_client" in self.__dict__:
            del self.__dict__["api_client"]
        return super().api_client

    @property
    def _live_api_client(self):
        if "_live_api_client" in self.__dict__:
            del self.__dict__["_live_api_client"]
        return super()._live_api_client


root_agent = Agent(
    name="ProcessorAgent",
    model=RefreshingGemini(
        model=MODEL_NAME,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    description="Generate repair cost and decision.",
    instruction="""
    You are a claims processor.
    Based on the 'severity' determined by the AssessorAgent and the incident address:
    1. Call the 'search_places' tool from the Maps MCP server with the address to resolve the location.
    2. Extract the state (e.g. NY, CA) from the search_places result. If the tool call fails or no state is found, default to "".
    3. You MUST call the 'generate_repair_cost' tool with the severity and the extracted state (or "" if unknown).
    4. Determine the decision:
       - If Simple: 'Approved'.
       - If Complex: 'Review Required'.

    Output a valid JSON object with the following structure:
    {
        "decision": "Approved" or "Review Required",
        "estimate": {result from generate_repair_cost tool},
        "reasoning": "Brief explanation of the decision."
    }
    IMPORTANT: Ensure the 'estimate' field directly contains the object returned by the tool (it has keys "items", "total_labor", "total_parts", "total_cost"). Do NOT wrap it in another key like 'generate_repair_cost_response'.
    
    Do not output markdown code blocks. Just the raw JSON string.
    """,
    tools=[
        generate_repair_cost,
        load_memory,
        get_maps_toolset(),
        # get_registry_maps_toolset()
    ],
    after_agent_callback=auto_save_session_to_memory_callback,
    output_key="final_result",
)

# Initialize BigQuery Analytics
_plugins = []
_project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
_dataset_id = os.environ.get("BQ_ANALYTICS_DATASET_ID", "adk_agent_analytics")
_location = os.environ.get("BQ_ANALYTICS_DATASET_LOCATION", "US")

if _project_id:
    try:
        bq = bigquery.Client(project=_project_id)
        bq.create_dataset(f"{_project_id}.{_dataset_id}", exists_ok=True)

        _plugins.append(
            BigQueryAgentAnalyticsPlugin(
                project_id=_project_id,
                dataset_id=_dataset_id,
                location=_location,
                config=BigQueryLoggerConfig(
                    gcs_bucket_name=os.environ.get("BQ_ANALYTICS_GCS_BUCKET"),
                    connection_id=os.environ.get("BQ_ANALYTICS_CONNECTION_ID"),
                ),
            )
        )
    except Exception as e:
        logging.warning(f"Failed to initialize BigQuery Analytics: {e}")

app = App(
    root_agent=root_agent,
    name="app",
    plugins=_plugins,
)
