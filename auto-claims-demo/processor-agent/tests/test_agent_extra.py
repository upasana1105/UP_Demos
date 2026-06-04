from unittest.mock import MagicMock, patch


def test_refreshing_gemini_properties():
    import app.agent as agent_module

    agent_module.Gemini.api_client = property(lambda self: "MockBaseClient")
    agent_module.Gemini._live_api_client = property(lambda self: "MockLiveClient")

    gem = agent_module.RefreshingGemini(model_name="test")
    gem.__dict__["api_client"] = "OldClient"
    gem.__dict__["_live_api_client"] = "OldLiveClient"

    assert gem.api_client == "MockBaseClient"
    assert gem._live_api_client == "MockLiveClient"

def test_big_query_init():
    import importlib
    import os
    with patch.dict(os.environ, {"BQ_ANALYTICS_DATASET_ID": "test"}):
        import app.agent as agent_module
        importlib.reload(agent_module)

def test_generate_repair_cost():
    import app.agent as agent_module
    res = agent_module.generate_repair_cost("severe", state="NY")
    assert res["total_cost"] > 0
    res = agent_module.generate_repair_cost("moderate", state="CA")
    assert res["total_cost"] > 0
    res = agent_module.generate_repair_cost("light", state="")
    assert res["total_cost"] > 0

def test_header_provider():
    import app.agent as agent_module
    headers = agent_module.header_provider()
    # Ensure checking proper header name
    assert "x-goog-api-key" in {k.lower(): v for k, v in headers.items()}

def test_get_maps_toolset():
    import app.agent as agent_module
    res = agent_module.get_maps_toolset()
    assert res is not None

def test_get_registry_maps_toolset():
    import app.agent as agent_module
    with patch('google.adk.integrations.agent_registry.AgentRegistry') as mock_reg:
        mock_reg_inst = MagicMock()
        mock_reg_inst.get_mcp_toolset.return_value = "mcp"
        mock_reg.return_value = mock_reg_inst

        # we have to inject into sys.modules because it does a local import inside the function
        import sys
        sys.modules['google.adk.integrations'] = MagicMock()
        sys.modules['google.adk.integrations.agent_registry'] = MagicMock()
        sys.modules['google.adk.integrations.agent_registry'].AgentRegistry = mock_reg

        res = agent_module.get_registry_maps_toolset()
        assert res == "mcp"
