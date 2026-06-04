from unittest.mock import patch, MagicMock

def test_claims_agent_get_registry():
    from claims_agent import ClaimAgentService
    svc = ClaimAgentService()
    svc.registry = MagicMock()

    with patch('claims_agent.os.environ.get', side_effect=lambda x, default=None: "mock_id" if x == "GOOGLE_CLOUD_PROJECT" else default):
        pass

    with patch.object(svc, 'registry') as mock_reg:
        mock_reg.get_agent.return_value = MagicMock()
        a = svc.get_registry_assessor_agent()
        b = svc.get_registry_processor_agent()
        assert a is not None
        assert b is not None
