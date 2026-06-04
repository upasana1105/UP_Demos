import pytest
from unittest.mock import patch, MagicMock

@pytest.fixture
def test_claims_agent():
    import claims_agent
    return claims_agent

def test_imports():
    import main
    assert main.app is not None

@pytest.mark.asyncio
async def test_process_claims_mock_mode():
    import main
    request = MagicMock()
    request.file_uris = ["gs://test/image.jpg"]
    request.address = "123 Test St"

    with patch('main.read_image_from_gcs', return_value=b'test_image'):
        with patch('main.detector') as mock_detector:
            mock_detector.detect_damage.return_value = {
                "highest_severity": "moderate",
                "damages": [
                    {"type": "scratch", "confidence": 0.9, "bbox": [0,0,10,10]}
                ],
                "image_shape": [100, 100]
            }
            res = await main.process_claims(request)

            assert res.findings is not None
            assert res.agent_result is not None

@pytest.mark.asyncio
async def test_resolve_repair_shops():
    import main
    request = MagicMock()
    request.address = "123 Test St"
    res = await main.find_repair_shops(request)
    assert res['shops'][0]['name'] == "Joe's Auto Body"

@pytest.mark.asyncio
async def test_schedule_appointment():
    import main
    request = MagicMock()
    request.place_id = "test_place"
    request.customer_name = "John Doe"
    request.phone_number = "123-456-7890"

    with patch('main.run_appointment_agent', return_value="Mocked Schedule"):
        res = await main.book_appointment(request)
        assert res.agent_message == "Mocked Schedule"

def test_car_damage_detector():
    from car_damage_detector import CarDamageDetector
    with patch('os.path.exists', return_value=False):
        with pytest.raises(RuntimeError):
            CarDamageDetector(model_path="dummy.pt")

def test_claim_agent_service():
    from claims_agent import ClaimAgentService
    svc = ClaimAgentService()
    assert svc is not None

def test_repair_shop_agent_service():
    from repair_shop_agent import RepairShopAgentService
    svc = RepairShopAgentService()
    assert svc is not None

def test_shared_auth():
    from shared_auth import GoogleAuth
    auth = GoogleAuth()
    assert auth is not None
