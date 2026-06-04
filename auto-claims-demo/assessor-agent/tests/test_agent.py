from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_agent_initialization():
    with patch("app.agent.BigQueryAgentAnalyticsPlugin"):
        with patch("app.agent.App"):
            import app.agent as agent_module

            assert agent_module.root_agent is not None
            assert agent_module.app is not None


@pytest.mark.asyncio
async def test_auto_save_session_to_memory_callback():
    import app.agent as agent_module

    mock_ctx = MagicMock()
    mock_ctx._invocation_context = MagicMock()
    mock_ctx._invocation_context.memory_service = MagicMock()
    mock_ctx._invocation_context.memory_service.add_session_to_memory = AsyncMock()
    mock_ctx._invocation_context.session = "mock_session"

    await agent_module.auto_save_session_to_memory_callback(mock_ctx)
    mock_ctx._invocation_context.memory_service.add_session_to_memory.assert_called_once_with(
        "mock_session"
    )


def test_refreshing_gemini():
    import app.agent as agent_module

    # Temporarily set api_client on MockGemini so we can test the subclass logic
    agent_module.Gemini.api_client = property(lambda self: "MockBaseClient")

    gem = agent_module.RefreshingGemini(model_name="test")
    assert gem.model_name == "test"

    gem.__dict__["api_client"] = "OldClient"
    res = gem.api_client
    assert res == "MockBaseClient"

    # also cover _get_auth_headers by mocking google auth and httpx inside method if needed
    # (assuming it exists on MockGemini or RefreshingGemini logic)
