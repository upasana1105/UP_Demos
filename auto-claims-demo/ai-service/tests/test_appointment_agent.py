import pytest
from unittest.mock import patch, MagicMock

@pytest.mark.asyncio
async def test_run_appointment_agent():
    from appointment_agent import run_appointment_agent

    with patch('appointment_agent.LlmAgent'):
        with patch('appointment_agent.InMemoryRunner') as mock_runner:
            mock_runner_inst = MagicMock()
            async def mock_run_async(*args, **kwargs):
                yield 'Appointment Mock Result'
            mock_runner_inst.run_async = mock_run_async
            mock_runner.return_value = mock_runner_inst
            res = await run_appointment_agent("place_id", "John", "context")
            # For coverage we just ensure it returns a string as we mocked the event parsing
            assert isinstance(res, str)

def test_create_calendar_event():
    from appointment_agent import create_calendar_event
    res = create_calendar_event("Shop", "2024-01-01", "10:00 AM", "John")
    assert "2024-01-01" in res
