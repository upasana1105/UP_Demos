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

from google.genai.types import Content, Part
import json
import re
import httpx
import os
from google.adk.sessions import VertexAiSessionService
from google.adk.memory import VertexAiMemoryBankService
from google.adk.runners import Runner
from google.adk.agents.remote_a2a_agent import AGENT_CARD_WELL_KNOWN_PATH
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from a2a.client import ClientConfig, ClientFactory
from a2a.types import TransportProtocol



from shared_auth import GoogleAuth

class RepairShopAgentService:
    def __init__(self):
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

        self.repair_shop_agent_url = os.getenv("REPAIR_SHOP_AGENT_URL")
        self.agent_engine_enabled = os.getenv("AGENT_ENGINE_ENABLED", "false")

        if self.agent_engine_enabled == "true":
            self.repair_shop_agent_card_url = f"{self.repair_shop_agent_url}/a2a/v1/card" if self.repair_shop_agent_url else ""
        else:
            self.repair_shop_agent_card_url = f"{self.repair_shop_agent_url}/a2a/app{AGENT_CARD_WELL_KNOWN_PATH}" if self.repair_shop_agent_url else ""

        self.httpx_client = httpx.AsyncClient(
            auth=GoogleAuth(),
            timeout=120.0,
        )
        self.factory = ClientFactory(
            ClientConfig(
                # Specify supported transport mechanisms
                supported_transports=[TransportProtocol.http_json],
                # Use client preferences for protocol negotiation
                use_client_preference=True,
                # Configure HTTP client with authentication            
                httpx_client=self.httpx_client,
            )
        )
        self.reasoning_engine_id = os.getenv("SHARED_AGENT_ENGINE_ID")

    @staticmethod
    def get_last_element(url_string):
        return url_string.split('/')[-1] if url_string else ""

    def get_repair_shop_agent(self):
        if not self.repair_shop_agent_card_url:
            return None
        return RemoteA2aAgent(
            name="repair_shop_agent",
            description=(
                "Finds local auto repair shops using Google Search."
            ),
            agent_card=self.repair_shop_agent_card_url,
            a2a_client_factory=self.factory,
        )

    def get_registry_repair_shop_agent(self):
        if not self.registry:
            raise ValueError("AgentRegistry is not configured or unavailable.")
        agents_list = self.registry.list_agents(
            filter_str="displayName:RepairShopAgent", page_size=1
        )
        a2a_server_name = agents_list.get("agents", [])[0]["name"] if agents_list.get("agents") else None

        if not a2a_server_name:
            raise ValueError("RepairShopAgent not found in Agent Registry")

        return self.registry.get_remote_a2a_agent(a2a_server_name, httpx_client=self.httpx_client)

    async def run_repair_shop_agent(self, zip_code: str, state: str, make: str, model: str, damage_type: str) -> list:
        """
        Runs the repair shop agent to find shops.
        Returns a list of shop dictionaries.
        """

        prompt_text = f"""
        Please find auto repair shops for a customer.
        Location: Zip Code {zip_code}, State {state}
        Vehicle: {make} {model}
        Damage: {damage_type}

        Find the best repair shops near this location.
        """

        def header_provider(context=None):
            return GoogleAuth()._get_token()


        self.registry = None
        if self.project_id:
            try:
                from google.adk.integrations.agent_registry import AgentRegistry
                self.registry = AgentRegistry(
                    project_id=self.project_id,
                    location=self.location,
                    header_provider=header_provider,
                )
            except ImportError:
                print("AgentRegistry could not be imported")

        # self.repair_shop_agent = self.get_repair_shop_agent()
        self.repair_shop_agent = self.get_registry_repair_shop_agent()

        session_service = VertexAiSessionService(
            project=self.project_id,
            location=self.location,
            agent_engine_id=self.reasoning_engine_id
        )

        memory_service = VertexAiMemoryBankService(
            project=self.project_id,
            location=self.location,
            agent_engine_id=self.reasoning_engine_id
        )

        if not self.repair_shop_agent:
            return get_auto_shops_list()

        # Create Content object
        prompt_content = Content(parts=[Part(text=prompt_text)])

        runner = Runner(
            agent=self.repair_shop_agent,
            app_name=self.reasoning_engine_id,
            session_service=session_service,
            memory_service=memory_service
        )
        user_id = "system" # internal usage

        final_text = ""

        session = await session_service.create_session(
           app_name=self.reasoning_engine_id,
           user_id=user_id
        )

        # Run asynchronously
        async for event in runner.run_async(user_id=user_id, session_id=session.id, new_message=prompt_content):
            # Accumulate text from events
            if hasattr(event, 'text') and event.text:
                final_text += event.text
            elif isinstance(event, str):
                final_text += event
            elif hasattr(event, 'content') and event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                       final_text += part.text

        await memory_service.add_session_to_memory(session)

        if not final_text:
            return get_auto_shops_list()

        try:
            # Improved JSON extraction (similar to claims_agent.py)
            cleaned_text = final_text.strip()

            # Try to find JSON block if mixed with other text
            json_match = re.search(r'\[.*\]', cleaned_text, re.DOTALL)
            if json_match:
                potential_json = json_match.group(0)
                try:
                    return json.loads(potential_json)
                except json.JSONDecodeError:
                    pass

            # Markdown cleanup fallback
            if "```json" in cleaned_text:
                cleaned_text = cleaned_text.split("```json")[1].split("```")[0]
            elif "```" in cleaned_text:
                cleaned_text = cleaned_text.split("```")[1].split("```")[0]

            return json.loads(cleaned_text.strip())
        except Exception as e:
            print(f"Error parsing repair shop agent response: {e}. Raw: {final_text}")
            return get_auto_shops_list()

repair_shop_agent_service = RepairShopAgentService()


def get_auto_shops_list():
    """
    Returns a list of auto repair shops.
    """
    shops_data = [
        {
            "name": "Bavarian Motor Experts",
            "address": "123 Auto Plaza Way, San Jose, CA 95131",
            "rating": 4.8,
            "phone": "+1-408-555-0199",
            "reasoning": "Specializes in BMW repair and factory-scheduled maintenance with certified technicians."
        },
        {
            "name": "Perfect Paintless Dent Removal",
            "address": "456 Collision Blvd, Saratoga, CA 95070",
            "rating": 4.5,
            "phone": None, # Null in JSON translates to None in Python
            "reasoning": "High rating for dent removal and highly recommended by locals for hail damage repair."
        },
        {
            "name": "Valley General Auto Care",
            "address": "789 Mechanic St, Campbell, CA 95008",
            "rating": None,
            "phone": "+1-408-555-0255",
            "reasoning": "A highly accessible local shop that works on all domestic and imported vehicle makes."
        }
    ]
    
    return shops_data