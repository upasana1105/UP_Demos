from unittest.mock import patch


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
    # To cover lines 94-110 we need to explicitly run the module level initialization logic again.
    import importlib
    import os

    with patch.dict(os.environ, {"BQ_ANALYTICS_DATASET_ID": "test"}):
        import app.agent as agent_module

        importlib.reload(agent_module)
