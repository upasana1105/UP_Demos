import pytest
from unittest.mock import patch, MagicMock, AsyncMock

@pytest.mark.asyncio
async def test_ping():
    from main import ping
    res = await ping()
    assert 'message' in res

@pytest.mark.asyncio
async def test_process_claims():
    from main import process_claims, ClaimsRequest
    import main

    with patch('main.run_in_threadpool') as mock_pool:
        # Mock run_in_threadpool returning bytes first, then dict
        mock_pool.side_effect = [b'test', {
            "highest_severity": "moderate",
            "damages": [
                {"type": "scratch", "confidence": 0.9, "bbox": [0,0,10,10], "area_percentage": 0.5, "severity": "moderate", "estimated_cost": 500, "location": "door"}
            ],
            "image_shape": [100, 100]
        }]

        with patch('main.claim_agent_service') as mock_agent:
            mock_agent.run_claims_agent = AsyncMock(return_value={"decision": "Approved"})
            req = ClaimsRequest(file_uris=["gs://test/image.jpg"], address="123 Test")
            main.MOCK_MODE = False

            with patch('main.detector') as mock_detector:
                # the detector runs via threadpool, mocked above, but it must be initialized
                mock_detector.detect_damage = MagicMock()
                res = await process_claims(req)
                assert res.findings is not None

            main.MOCK_MODE = True

@pytest.mark.asyncio
async def test_find_repair_shops():
    from main import find_repair_shops, RepairShopRequest
    import main
    main.MOCK_MODE = False
    with patch('main.repair_shop_agent_service') as mock_rs_agent:
        mock_rs_agent.run_repair_shop_agent = AsyncMock(return_value=[{"name": "Mock Auto"}])
        req = RepairShopRequest(zip_code="12345", state="IL", make="Toyota", model="Camry", damage_type="dent", context="notes")
        res = await find_repair_shops(req)
        assert res.shops[0]["name"] == "Mock Auto"
    main.MOCK_MODE = True

@pytest.mark.asyncio
async def test_book_appointment():
    from main import book_appointment, AppointmentRequest
    import main
    main.MOCK_MODE = False
    with patch('main.run_appointment_agent') as mock_run:
        mock_run.return_value = "Confirmed"
        req = AppointmentRequest(session_id="1", message="Hi", context={})
        res = await book_appointment(req)
        assert res.agent_message == "Confirmed"
    main.MOCK_MODE = True
