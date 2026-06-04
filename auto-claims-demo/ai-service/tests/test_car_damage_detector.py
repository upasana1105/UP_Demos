from unittest.mock import patch, MagicMock

def test_car_damage_detector_load_success():
    from car_damage_detector import CarDamageDetector
    with patch('os.path.exists', return_value=True):
        with patch('car_damage_detector.YOLO') as mock_yolo:
            mock_model = MagicMock()
            mock_yolo.return_value = mock_model
            detector = CarDamageDetector(model_path="dummy.pt")
            assert detector is not None

def test_car_damage_detector_detect():
    from car_damage_detector import CarDamageDetector
    with patch('os.path.exists', return_value=True):
        with patch('car_damage_detector.YOLO') as mock_yolo:
            mock_model = MagicMock()

            mock_result = MagicMock()
            mock_box = MagicMock()
            mock_box.cls.cpu().numpy.return_value = [0]
            mock_box.conf.cpu().numpy.return_value = [0.9]
            # Need to return an iterable that can be unpacked to 4 values
            mock_box_item = MagicMock()
            mock_box_item.cpu().numpy().astype().tolist.return_value = [0, 0, 10, 10]
            mock_box.xyxy = [mock_box_item]
            mock_result.boxes = mock_box
            mock_result.boxes.__len__ = MagicMock(return_value=1)

            mock_result.names = {0: "dent"}
            mock_model.return_value = [mock_result]

            mock_yolo.return_value = mock_model
            detector = CarDamageDetector(model_path="dummy.pt")

            with patch('PIL.Image.open') as mock_img:
                mock_opened = MagicMock()
                mock_opened.convert.return_value = MagicMock()
                mock_img.return_value = mock_opened

                with patch('car_damage_detector.np.array', return_value=MagicMock()) as mock_np:
                    mock_np.return_value.shape = (100, 100, 3)
                    with patch.object(detector, '_preprocess_image', return_value=mock_np.return_value):
                        res = detector.detect_damage(b"fakebytes")
                        assert "highest_severity" in res

def test_car_damage_detector_highest_severity():
    from car_damage_detector import CarDamageDetector
    with patch('os.path.exists', return_value=True):
        with patch('car_damage_detector.YOLO'):
            detector = CarDamageDetector(model_path="dummy.pt")
            assert detector._get_highest_severity([]) == "none"
            assert detector._get_highest_severity([{"severity": "light"}]) == "light"
            assert detector._get_highest_severity([{"severity": "light"}, {"severity": "severe"}]) == "severe"

