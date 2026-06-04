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

import os
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.sessions import VertexAiSessionService
from google.adk.memory import VertexAiMemoryBankService
from google.adk.agents import SequentialAgent
from google.adk.runners import Runner
from google.genai.types import Content, Part
import json
import re
import httpx
from a2a.client import ClientConfig, ClientFactory
from a2a.types import TransportProtocol

factory = None

from shared_auth import GoogleAuth

class ClaimAgentService:
    def __init__(self):
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        
        self.assessor_agent_url = os.getenv("ASSESSOR_AGENT_URL")
        self.processor_agent_url = os.getenv("PROCESSOR_AGENT_URL")
        self.agent_engine_enabled = os.getenv("AGENT_ENGINE_ENABLED", "false")
        
        self.assessor_agent_card_url = f"{self.assessor_agent_url}/a2a/v1/card" if self.assessor_agent_url else ""
        self.processor_agent_card_url = f"{self.processor_agent_url}/a2a/v1/card" if self.processor_agent_url else ""
        
        self.httpx_client = httpx.AsyncClient(
            auth=GoogleAuth(),
            timeout=120,
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

    def get_assessor_agent(self):
        if not self.assessor_agent_card_url:
            return None
        return RemoteA2aAgent(
            name="assessor_agent",
            description=(
                "Assess damage severity based on findings."
            ),
            agent_card=self.assessor_agent_card_url,
            a2a_client_factory=self.factory,
        )

    def get_processor_agent(self):
        if not self.processor_agent_card_url:
            return None
        return RemoteA2aAgent(
            name="processor_agent",
            description=(
                "Generate repair cost and decision."
            ),
            agent_card=self.processor_agent_card_url,
            a2a_client_factory=self.factory,
        )

    def get_registry_assessor_agent(self):
        if not self.registry:
            raise ValueError("AgentRegistry is not configured or unavailable.")
        agents_list = self.registry.list_agents(
            filter_str="displayName:AssessorAgent", page_size=1
        )
        a2a_server_name = agents_list.get("agents", [])[0]["name"] if agents_list.get("agents") else None

        if not a2a_server_name:
            raise ValueError("AssessorAgent not found in Agent Registry")

        return self.registry.get_remote_a2a_agent(a2a_server_name, httpx_client=self.httpx_client)

    def get_registry_processor_agent(self):
        if not self.registry:
            raise ValueError("AgentRegistry is not configured or unavailable.")
        agents_list = self.registry.list_agents(
            filter_str="displayName:ProcessorAgent", page_size=1
        )
        a2a_server_name = agents_list.get("agents", [])[0]["name"] if agents_list.get("agents") else None

        if not a2a_server_name:
            raise ValueError("ProcessorAgent not found in Agent Registry")

        return self.registry.get_remote_a2a_agent(a2a_server_name, httpx_client=self.httpx_client)

    # Helper to run the agent
    async def run_claims_agent(self, findings: list[str], address: str = "") -> dict:
        """
        Runs the sequential agent with the provided findings and address.
        Returns the final result dictionary.
        """

        # Initialize AgentRegistry with header_provider and credentials
        # every time so that the latest headers and injected

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

        # self.assessor_agent = self.get_assessor_agent()
        self.assessor_agent = self.get_registry_assessor_agent()
        
        # self.processor_agent = self.get_processor_agent()
        self.processor_agent = self.get_registry_processor_agent()        

        session_service = VertexAiSessionService(
            project=self.project_id,
            location=self.location,
            agent_engine_id=self.reasoning_engine_id
        )

        memory_service = VertexAiMemoryBankService(agent_engine_id=self.reasoning_engine_id)

        if not self.assessor_agent or not self.processor_agent:
             return {
                "decision": "Error",
                "reasoning": "Agents not properly initialized. Make sure assessing and processing agents are set.",
                "estimate": {}
            }

        # Sequential Agent
        claims_sequential_agent = SequentialAgent(
            name="ClaimsSequentialAgent",
            sub_agents=[self.assessor_agent, self.processor_agent],
            description="Assess damage and process claim sequentially."
        )

        # Prepare input text
        findings_text = "\n".join([f"- {f}" for f in findings])
        prompt_text = f"Here are the damage findings from the vehicle images:\n{findings_text}\n\nPlease assess and process this claim."
        if address:
             prompt_text += f"\n\nThe incident occurred at: {address}."

        # Create Content object
        prompt_content = Content(parts=[Part(text=prompt_text)])

        runner = Runner(
            agent=claims_sequential_agent,
            app_name=self.reasoning_engine_id,
            session_service=session_service,
            memory_service=memory_service,
        )
        user_id = "system" # internal usage

        session = await session_service.create_session(
           app_name=self.reasoning_engine_id,
           user_id=user_id
        )

        final_text = ""

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
             return {
                "decision": "Error",
                "reasoning": "No response text received from agent.",
                "estimate": {}
            }

        try:
            # Improved JSON extraction
            cleaned_text = final_text.strip()

            # Try to find JSON block if mixed with other text
            json_match = re.search(r'\{.*\}', cleaned_text, re.DOTALL)
            if json_match:
                potential_json = json_match.group(0)
                # Try parsing the finding
                try:
                    return json.loads(potential_json)
                except json.JSONDecodeError:
                    # If that failed, maybe it has markdown blocks
                    pass

            # Markdown cleanup fallback
            if "```json" in cleaned_text:
                cleaned_text = cleaned_text.split("```json")[1].split("```")[0]
            elif "```" in cleaned_text:
                cleaned_text = cleaned_text.split("```")[1].split("```")[0]

            return json.loads(cleaned_text.strip())
        except Exception as e:
            print(f"Error parsing agent response: {e}. Raw: {final_text}")
            return {
                "decision": "Error",
                "reasoning": f"Failed to parse agent response: {str(e)}",
                "estimate": {},
                "raw": final_text
            }

claim_agent_service = ClaimAgentService()
