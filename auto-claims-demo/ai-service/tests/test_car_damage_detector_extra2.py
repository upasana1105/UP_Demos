from unittest.mock import patch, MagicMock

def test_car_damage_detector_extra_cover():
    from car_damage_detector import CarDamageDetector
    with patch('os.path.exists', return_value=True):
        with patch('car_damage_detector.YOLO') as mock_yolo:
            mock_model = MagicMock()
            mock_yolo.return_value = mock_model
            detector = CarDamageDetector(model_path="dummy.pt")

            # cover remaining _describe_location
            loc1 = detector._describe_location([0, 0, 10, 10], (100, 100))
            detector._describe_location([90, 0, 100, 10], (100, 100))
            detector._describe_location([0, 90, 10, 100], (100, 100))
            detector._describe_location([90, 90, 100, 100], (100, 100))
            detector._describe_location([40, 40, 60, 60], (100, 100))

            assert loc1 is not None
