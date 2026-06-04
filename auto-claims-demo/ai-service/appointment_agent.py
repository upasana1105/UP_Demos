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

from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from google.genai.types import Content, Part
from google.adk.plugins.bigquery_agent_analytics_plugin import (
    BigQueryAgentAnalyticsPlugin,
    BigQueryLoggerConfig,
)
from google.cloud import bigquery
import os
import logging

MOCK_MODE = os.environ.get("MOCK_MODE", "false").lower() == "true"
mock_sessions = {}

# Initialize BigQuery Analytics
_plugins = []
if not MOCK_MODE:
    _project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    _dataset_id = os.environ.get("BQ_ANALYTICS_DATASET_ID", "adk_agent_analytics")
    _location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

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

# Mock Tool for Appointment Booking
def create_calendar_event(shop_name: str, date: str, time: str, customer_name: str) -> str:
    """
    Creates a calendar event for a repair appointment.

    Args:
        shop_name: The name of the repair shop.
        date: The date of the appointment (e.g., "2023-10-27").
        time: The time of the appointment (e.g., "14:00").
        customer_name: The name of the customer.

    Returns:
        A confirmation message string.
    """
    print(f"DEBUG: Booking appointment at {shop_name} for {customer_name} on {date} at {time}")
    return f"Appointment confirmed: {shop_name} on {date} at {time} for {customer_name}."

# Appointment Agent Definition
MODEL_NAME = os.environ.get("MODEL", "gemini-2.5-flash")

appointment_agent = LlmAgent(
    name="AppointmentAgent",
    model=MODEL_NAME,
    description=" helps users book appointments at repair shops.",
    instruction="""
    You are a helpful assistant for booking auto repair appointments.
    Your goal is to help the user schedule an appointment at a specific repair shop.

    1. Greet the user and confirm the repair shop they want to book with (if provided in context).
    2. Ask for the preferred date and time for the appointment.
    3. Once you have the date and time, ask for the customer's name if you don't already have it.
    4. When you have all the details (Shop Name, Date, Time, Customer Name), call the `create_calendar_event` tool to book the appointment.
    5. Confirm the booking to the user with the details returned by the tool.

    Be polite and professional. Keep your responses concise.
    """,
    tools=[create_calendar_event]
)

# In-memory session store
# Key: session_id, Value: InMemoryRunner instance
sessions = {}

async def run_appointment_agent(session_id: str, user_message: str, context: dict = None) -> str:
    """
    Runs the appointment agent for a given session.

    Args:
        session_id: unique identifier for the conversation session.
        user_message: the message from the user.
        context: optional dictionary with initial context (e.g., shop_name, customer_name).

    Returns:
        The agent's response text.
    """
    if MOCK_MODE:
        state = mock_sessions.get(session_id, "start")

        if state == "start":
            mock_sessions[session_id] = "booking"
            return "Hello! When would you like to schedule your appointment?"

        if state == "booking":
            mock_sessions[session_id] = "done"
            shop = "the shop"
            cust = "Customer"
            if context:
                shop = context.get('shop_name', shop)
                cust = context.get('customer_name', cust)
            return f"Appointment confirmed: {shop} on {user_message} for {cust}."

        return "I've already booked your appointment. Is there anything else?"

    # Get or create runner
    if session_id not in sessions:
        runner = InMemoryRunner(agent=appointment_agent, plugins=_plugins)
        runner.auto_create_session = True
        sessions[session_id] = runner

        # If context is provided for a new session, inject it as a system prompt or initial user message
        if context:
            initial_context = f"Context: User wants to book at '{context.get('shop_name', 'Unknown Shop')}'."
            if context.get('customer_name'):
                initial_context += f" Customer Name: {context.get('customer_name')}."

            # We can treat this as a hidden system message or just prepend it to the first user message.
            # However, LlmAgent usually handles conversation history.
            # Let's just prepend it to the user message for the first turn effectively.
            user_message = f"{initial_context}\n\nUser: {user_message}"

    runner = sessions[session_id]
    user_id = "user" # Simple user ID for now

    # Construct content
    prompt_content = Content(parts=[Part(text=user_message)])

    final_text = ""

    # Run the agent
    # Note: run_async yields events. We need to collect the text response.
    try:
        async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=prompt_content):
            if hasattr(event, 'text') and event.text:
                final_text += event.text
            elif isinstance(event, str):
                final_text += event
            elif hasattr(event, 'content') and event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        final_text += part.text

    except Exception as e:
        print(f"Error running appointment agent: {e}")
        return "I'm sorry, I encountered an error processing your request."

    return final_text
