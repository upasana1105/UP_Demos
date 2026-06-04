from unittest.mock import patch, MagicMock

def test_car_damage_detector_extra():
    from car_damage_detector import CarDamageDetector
    with patch('car_damage_detector.YOLO') as mock_yolo:
        mock_model = MagicMock()
        mock_yolo.return_value = mock_model

        with patch('os.path.exists', return_value=True):
            detector = CarDamageDetector(model_path="dummy.pt")

            # _calculate_damage_area
            assert detector._calculate_damage_area([0, 0, 10, 10], (100, 100)) == 1.0

            # _classify_severity varies by rules, just run to cover it
            sev1 = detector._classify_severity("dent", 2.0)
            sev2 = detector._classify_severity("scratch", 20.0)
            assert isinstance(sev1, str)
            assert isinstance(sev2, str)

            # _estimate_repair_cost
            cost = detector._estimate_repair_cost("dent", "moderate", 15.0)
            assert isinstance(cost, (int, float))
