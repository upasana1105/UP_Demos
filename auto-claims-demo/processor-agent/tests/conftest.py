import os
import sys
from unittest.mock import MagicMock


# 1. Provide the tuple-returning callable that google.auth.default expects
def fake_default(*args, **kwargs):
    mock_creds = MagicMock()
    mock_creds.valid = True
    mock_creds.token = "abc"
    return (mock_creds, "test-project")

# 2. Setup Google namespaces correctly
mock_google = MagicMock()
mock_google.__path__ = []
mock_google.__spec__ = MagicMock()
sys.modules['google'] = mock_google

mock_cloud = MagicMock()
mock_cloud.__path__ = []
mock_cloud.__spec__ = MagicMock()
sys.modules['google.cloud'] = mock_cloud

# 3. Handle specific mocked sub-modules
sys.modules['google.cloud.storage'] = MagicMock()
sys.modules['google.cloud.bigquery'] = MagicMock()
sys.modules['google.cloud.logging'] = MagicMock()

# 4. Handle google.auth explicit structure
mock_auth = MagicMock()
mock_auth.__path__ = []
mock_auth.__spec__ = MagicMock()
mock_auth.default = fake_default
sys.modules['google.auth'] = mock_auth
sys.modules['google.auth.transport'] = MagicMock()
sys.modules['google.auth.transport.requests'] = MagicMock()

# 5. Handle google.adk explicit structure
sys.modules['google.adk'] = MagicMock()
sys.modules['google.adk.agents'] = MagicMock()
sys.modules['google.adk.tools'] = MagicMock()
sys.modules['google.adk.tools.mcp_tool'] = MagicMock()
sys.modules['google.adk.tools.mcp_tool.mcp_session_manager'] = MagicMock()
sys.modules['google.adk.apps'] = MagicMock()
sys.modules['google.adk.models'] = MagicMock()

# 6. Class mock for Gemini
class MockGemini:
    def __init__(self, **kwargs):
        self.model_name = kwargs.get("model_name")
    def _get_auth_headers(self):
        return {"Authorization": "Bearer abc"}

sys.modules['google.adk.models.gemini'] = MagicMock()
sys.modules['google.adk.models'].Gemini = MockGemini
sys.modules['google.adk.models.Gemini'] = MockGemini

# 7. Other mocked modules
sys.modules['google.genai'] = MagicMock()
sys.modules['google.genai.types'] = MagicMock()
sys.modules['google.adk.plugins'] = MagicMock()
sys.modules['google.adk.plugins.bigquery_agent_analytics_plugin'] = MagicMock()

sys.modules['google.adk.a2a'] = MagicMock()
sys.modules['google.adk.a2a.executor'] = MagicMock()
sys.modules['google.adk.a2a.executor.a2a_agent_executor'] = MagicMock()
sys.modules['google.adk.a2a.utils'] = MagicMock()
sys.modules['google.adk.a2a.utils.agent_card_builder'] = MagicMock()
sys.modules['google.adk.artifacts'] = MagicMock()
sys.modules['google.adk.sessions'] = MagicMock()
sys.modules['google.adk.memory'] = MagicMock()
sys.modules['google.adk.runners'] = MagicMock()
sys.modules['google.adk.cli'] = MagicMock()
sys.modules['google.adk.cli.adk_web_server'] = MagicMock()
sys.modules['google.adk.telemetry'] = MagicMock()
sys.modules['google.adk.telemetry.google_cloud'] = MagicMock()
sys.modules['google.adk.telemetry.setup'] = MagicMock()

sys.modules['a2a'] = MagicMock()
sys.modules['a2a.types'] = MagicMock()
sys.modules['vertexai'] = MagicMock()
sys.modules['vertexai.preview'] = MagicMock()
sys.modules['vertexai.preview.reasoning_engines'] = MagicMock()
sys.modules['nest_asyncio'] = MagicMock()
sys.modules['fastapi'] = MagicMock()
sys.modules['fastapi.responses'] = MagicMock()
sys.modules['httpx'] = MagicMock()

os.environ["MOCK_MODE"] = "true"
