import sys
from unittest.mock import MagicMock

# Base mock setups for ai-service testing
mock_google = MagicMock()
mock_google.__path__ = []
mock_google.__spec__ = MagicMock()

sys.modules['google'] = mock_google
sys.modules['google.cloud'] = MagicMock()
sys.modules['google.cloud.storage'] = MagicMock()
sys.modules['google.cloud.bigquery'] = MagicMock()
sys.modules['google.auth'] = MagicMock()
sys.modules['google.auth.transport'] = MagicMock()
sys.modules['google.auth.transport.requests'] = MagicMock()
sys.modules['google.adk'] = MagicMock()
sys.modules['google.adk.agents'] = MagicMock()
sys.modules['google.adk.tools'] = MagicMock()
sys.modules['google.adk.tools.mcp_tool'] = MagicMock()
sys.modules['google.adk.tools.mcp_tool.mcp_session_manager'] = MagicMock()
sys.modules['google.adk.apps'] = MagicMock()
sys.modules['google.adk.models'] = MagicMock()
sys.modules['google.adk.memory'] = MagicMock()
sys.modules['google.genai'] = MagicMock()
sys.modules['google.genai.types'] = MagicMock()
sys.modules['google.adk.plugins'] = MagicMock()
sys.modules['google.adk.plugins.bigquery_agent_analytics_plugin'] = MagicMock()

sys.modules['cv2'] = MagicMock()
sys.modules['numpy'] = MagicMock()
sys.modules['PIL'] = MagicMock()
sys.modules['torch'] = MagicMock()
sys.modules['ultralytics'] = MagicMock()
sys.modules['huggingface_hub'] = MagicMock()
sys.modules['a2a'] = MagicMock()
sys.modules['a2a.client'] = MagicMock()
sys.modules['a2a.types'] = MagicMock()

import os
os.environ["MOCK_MODE"] = "true"

sys.modules['google.adk.runners'] = MagicMock()
sys.modules['google.adk.sessions'] = MagicMock()
sys.modules['fastapi.concurrency'] = MagicMock()
sys.modules['google.adk.agents.remote_a2a_agent'] = MagicMock()
sys.modules['google.adk.cli'] = MagicMock()
sys.modules['google.adk.cli.adk_web_server'] = MagicMock()
sys.modules['google.adk.telemetry'] = MagicMock()
sys.modules['google.adk.telemetry.google_cloud'] = MagicMock()
sys.modules['google.adk.telemetry.setup'] = MagicMock()
import google.auth
google.auth.default = MagicMock(return_value=(MagicMock(), "test-project"))
sys.modules['google.auth'] = google.auth
