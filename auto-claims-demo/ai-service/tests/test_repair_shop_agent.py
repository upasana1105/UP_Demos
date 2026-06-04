import pytest
from unittest.mock import patch, MagicMock, AsyncMock

@pytest.mark.asyncio
async def test_repair_shop_agent_service():
    from repair_shop_agent import RepairShopAgentService
    svc = RepairShopAgentService()

    with patch.object(svc, 'get_registry_repair_shop_agent', return_value=MagicMock()):
        with patch('repair_shop_agent.VertexAiSessionService') as mock_sess:
            mock_sess_inst = MagicMock()
            mock_sess_inst.create_session = AsyncMock(return_value=MagicMock(id="1"))
            mock_sess.return_value = mock_sess_inst

            with patch('repair_shop_agent.VertexAiMemoryBankService') as mock_mem:
                mock_mem_inst = MagicMock()
                mock_mem_inst.add_session_to_memory = AsyncMock()
                mock_mem.return_value = mock_mem_inst

                with patch('repair_shop_agent.Runner') as mock_runner:
                    mock_runner_inst = MagicMock()
                    async def mock_run_async(*args, **kwargs):
                        yield '{"shops": [{"name": "Mocked Auto"}]}'
                    mock_runner_inst.run_async = mock_run_async
                    mock_runner.return_value = mock_runner_inst

                    res = await svc.run_repair_shop_agent("12345", "IL", "Toyota", "Camry", "dent")
                    # Result might be parsed as dict or list
                    assert res is not None

def test_repair_shop_agent_get_agent():
    from repair_shop_agent import RepairShopAgentService
    svc = RepairShopAgentService()
    with patch('repair_shop_agent.os.environ.get', return_value="test"):
        with patch('repair_shop_agent.RemoteA2aAgent') as mock_remote:
            mock_remote.return_value = MagicMock()
            # It will still hit agent retrieval or fallback code
            svc.get_repair_shop_agent()
            pass
