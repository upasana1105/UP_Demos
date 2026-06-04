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
from google.adk.tools import google_search, load_memory

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools import LongRunningFunctionTool
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


async def auto_save_session_to_memory_callback(callback_context):
    await callback_context._invocation_context.memory_service.add_session_to_memory(
        callback_context._invocation_context.session
    )


# Repair Shop Agent Definition
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
    name="RepairShopAgent",
    model=RefreshingGemini(model=MODEL_NAME),
    description="Finds local auto repair shops using Google Search.",
    instruction="""
    You are an expert assistant helping users find auto repair shops.
    The user will provide their location (Zip Code, City, State), Vehicle details (Make, Model, Year), and Damage description.

    Your task:
    1. Use Google Search to find 3-5 highly-rated auto body repair shops near the provided location.
    2. Look for shops that specialize in the specific vehicle make or type of damage if possible.
    3. Return a JSON list of objects. Each object must have the following keys:
       - "name": The name of the shop.
       - "address": The full address of the shop.
       - "rating": The average rating (e.g., 4.5) as a number, or null if not found.
       - "phone": The phone number, or null if not found.
       - "reasoning": A brief explanation of why this shop is a good fit (e.g., "Specializes in BMW repair", "High rating for dent removal").

    IMPORTANT:
    - Output ONLY valid JSON.
    - Do not include markdown formatting (like ```json ... ```).
    - If you cannot find any shops, return an empty list [].
    """,
    tools=[google_search, load_memory],
    after_agent_callback=auto_save_session_to_memory_callback,
    output_key="shops",
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
