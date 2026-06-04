# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import cv2
import numpy as np
from PIL import Image
import torch
import logging
from typing import List, Dict, Tuple, Optional, Union
import os
from ultralytics import YOLO
from huggingface_hub import hf_hub_download

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CarDamageDetector:
    """
    Car damage detection system using YOLOv11 model.

    This class handles the detection and classification of various types
    of car damage using a fine-tuned YOLOv11 model.
    """

    def __init__(self, model_path: Optional[str] = None, confidence_threshold: float = 0.5):
        """
        Initialize the car damage detector.

        Args:
            model_path (str, optional): Path to custom trained model
            confidence_threshold (float): Minimum confidence for detections
        """
        self.confidence_threshold = confidence_threshold
        self.model_path = hf_hub_download(
            repo_id="vineetsarpal/yolov11n-car-damage",
            filename="best.pt",
            # token=os.getenv("HF_TOKEN") # Optional if public
        )
        self.device = self._get_device()
        self.model = None
        self.class_names = {}

        # Damage severity mapping based on area and type
        self.severity_mapping = {
            # Glass/Lights - lower thresholds for severity
            "Front-windscreen-damage": {"light": (0, 2), "moderate": (2, 10), "severe": (10, 100)},
            "Headlight-damage": {"light": (0, 5), "moderate": (5, 20), "severe": (20, 100)},
            "Rear-windscreen-Damage": {"light": (0, 2), "moderate": (2, 10), "severe": (10, 100)},
            "Sidemirror-Damage": {"light": (0, 10), "moderate": (10, 30), "severe": (30, 100)},
            "Taillight-Damage": {"light": (0, 5), "moderate": (5, 20), "severe": (20, 100)},

            # Body Parts/Dents
            "Runningboard-Damage": {"light": (0, 5), "moderate": (5, 15), "severe": (15, 100)},
            "bonnet-dent": {"light": (0, 3), "moderate": (3, 10), "severe": (10, 100)},
            "boot-dent": {"light": (0, 3), "moderate": (3, 10), "severe": (10, 100)},
            "doorouter-dent": {"light": (0, 3), "moderate": (3, 10), "severe": (10, 100)},
            "fender-dent": {"light": (0, 3), "moderate": (3, 10), "severe": (10, 100)},
            "front-bumper-dent": {"light": (0, 3), "moderate": (3, 12), "severe": (12, 100)},
            "quaterpanel-dent": {"light": (0, 2), "moderate": (2, 8), "severe": (8, 100)},
            "rear-bumper-dent": {"light": (0, 3), "moderate": (3, 12), "severe": (12, 100)},
            "roof-dent": {"light": (0, 2), "moderate": (2, 8), "severe": (8, 100)},
        }

        # Cost estimation per damage type (base costs in USD)
        self.cost_estimates = {
            "Front-windscreen-damage": {"light": 300, "moderate": 600, "severe": 1200},
            "Headlight-damage": {"light": 200, "moderate": 500, "severe": 1000},
            "Rear-windscreen-Damage": {"light": 300, "moderate": 500, "severe": 900},
            "Runningboard-Damage": {"light": 200, "moderate": 400, "severe": 800},
            "Sidemirror-Damage": {"light": 100, "moderate": 250, "severe": 500},
            "Taillight-Damage": {"light": 150, "moderate": 300, "severe": 600},
            "bonnet-dent": {"light": 250, "moderate": 600, "severe": 1500},
            "boot-dent": {"light": 250, "moderate": 600, "severe": 1500},
            "doorouter-dent": {"light": 200, "moderate": 500, "severe": 1200},
            "fender-dent": {"light": 200, "moderate": 450, "severe": 1000},
            "front-bumper-dent": {"light": 350, "moderate": 700, "severe": 1600},
            "quaterpanel-dent": {"light": 400, "moderate": 900, "severe": 2200},
            "rear-bumper-dent": {"light": 350, "moderate": 700, "severe": 1600},
            "roof-dent": {"light": 500, "moderate": 1200, "severe": 3000},
        }

        self._load_model()

    def _get_device(self) -> str:
        """Determine the best available device for inference."""
        if torch.cuda.is_available():
            return "cuda"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"

    def _load_model(self) -> None:
        """Load the YOLO model for damage detection."""
        try:
            if os.path.exists(self.model_path):
                logger.info(f"Loading model from {self.model_path}")
                self.model = YOLO(self.model_path)
                self.class_names = self.model.names
            else:
                logger.error(f"Model not found at {self.model_path}")
                raise FileNotFoundError(f"Model file not found: {self.model_path}")

            # Move model to appropriate device
            if self.device != "cpu":
                self.model.to(self.device)

            logger.info(f"Model loaded successfully on {self.device}")

        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise RuntimeError(f"Failed to load model: {str(e)}")

    def _preprocess_image(self, image: Union[str, np.ndarray, Image.Image, bytes]) -> np.ndarray:
        """
        Preprocess image for model inference.

        Args:
            image: Input image (path, numpy array, PIL Image, or bytes)

        Returns:
            np.ndarray: Preprocessed image array
        """
        if isinstance(image, str):
            # Load from file path
            img = cv2.imread(image)
            if img is None:
                raise ValueError(f"Could not load image from {image}")
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        elif isinstance(image, Image.Image):
            # Convert PIL Image to numpy array
            img = np.array(image)
        elif isinstance(image, np.ndarray):
            # Use numpy array directly
            img = image.copy()
        elif isinstance(image, bytes):
            # Convert bytes to numpy array
            nparr = np.frombuffer(image, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                 raise ValueError("Could not decode image bytes")
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        else:
            raise TypeError("Image must be a file path, PIL Image, numpy array, or bytes")

        return img

    def _calculate_damage_area(self, bbox: List[int], image_shape: Tuple[int, int]) -> float:
        """
        Calculate the percentage of image area covered by damage.

        Args:
            bbox: Bounding box coordinates [x1, y1, x2, y2]
            image_shape: Image dimensions (height, width)

        Returns:
            float: Percentage of image area covered by damage
        """
        x1, y1, x2, y2 = bbox
        damage_area = (x2 - x1) * (y2 - y1)
        total_area = image_shape[0] * image_shape[1]
        return (damage_area / total_area) * 100

    def _classify_severity(self, damage_type: str, area_percentage: float) -> str:
        """
        Classify damage severity based on type and area coverage.

        Args:
            damage_type: Type of damage detected
            area_percentage: Percentage of image area covered

        Returns:
            str: Severity level ('light', 'moderate', 'severe')
        """
        if damage_type not in self.severity_mapping:
            return "moderate"  # Default classification

        thresholds = self.severity_mapping[damage_type]

        if area_percentage <= thresholds["light"][1]:
            return "light"
        elif area_percentage <= thresholds["moderate"][1]:
            return "moderate"
        else:
            return "severe"

    def _estimate_repair_cost(self, damage_type: str, severity: str, area_percentage: float) -> int:
        """
        Estimate repair cost based on damage type and severity.

        Args:
            damage_type: Type of damage
            severity: Severity level
            area_percentage: Area coverage percentage

        Returns:
            int: Estimated repair cost in USD
        """
        if damage_type not in self.cost_estimates:
            return 0

        base_cost = self.cost_estimates[damage_type][severity]

        # Apply area multiplier for larger damages
        area_multiplier = max(1.0, area_percentage / 10.0)
        estimated_cost = int(base_cost * area_multiplier)

        return estimated_cost

    def detect_damage(self, image: Union[str, np.ndarray, Image.Image, bytes]) -> Dict:
        """
        Detect damage in a car image.

        Args:
            image: Input image (path, numpy array, PIL Image, or bytes)

        Returns:
            Dict: Detection results containing damages and metadata
        """
        try:
            # Preprocess image
            img_array = self._preprocess_image(image)
            original_shape = img_array.shape[:2]  # (height, width)

            # Run inference
            results = self.model(img_array, conf=self.confidence_threshold, verbose=False)

            # Process results
            detections = []

            if len(results) > 0 and results[0].boxes is not None:
                boxes = results[0].boxes

                for i in range(len(boxes)):
                    # Extract bounding box coordinates
                    bbox = boxes.xyxy[i].cpu().numpy().astype(int).tolist()
                    confidence = float(boxes.conf[i].cpu().numpy())
                    class_id = int(boxes.cls[i].cpu().numpy())

                    # Map class ID to damage type
                    damage_type = self.class_names.get(class_id, "unknown")

                    # Calculate damage area percentage
                    area_percentage = self._calculate_damage_area(bbox, original_shape)

                    # Classify severity
                    severity = self._classify_severity(damage_type, area_percentage)

                    # Estimate repair cost
                    estimated_cost = self._estimate_repair_cost(damage_type, severity, area_percentage)

                    detection = {
                        "type": damage_type,
                        "severity": severity,
                        "confidence": confidence,
                        "bbox": bbox,
                        "area_percentage": round(area_percentage, 2),
                        "estimated_cost": estimated_cost,
                        "location": self._describe_location(bbox, original_shape)
                    }

                    detections.append(detection)

            # Create result summary
            result = {
                "image_shape": original_shape,
                "total_damages": len(detections),
                "damages": detections,
                "total_estimated_cost": sum([d["estimated_cost"] for d in detections]),
                "highest_severity": self._get_highest_severity(detections),
                "processing_info": {
                    "model_used": "vineetsarpal/yolov11n-car-damage",
                    "device": self.device,
                    "confidence_threshold": self.confidence_threshold
                }
            }

            return result

        except Exception as e:
            logger.error(f"Error during damage detection: {str(e)}")
            raise RuntimeError(f"Damage detection failed: {str(e)}")

    def _describe_location(self, bbox: List[int], image_shape: Tuple[int, int]) -> str:
        """
        Describe the location of damage on the vehicle.

        Args:
            bbox: Bounding box coordinates
            image_shape: Image dimensions

        Returns:
            str: Human-readable location description
        """
        x1, y1, x2, y2 = bbox
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2

        height, width = image_shape

        # Determine horizontal position
        if center_x < width / 3:
            horizontal = "left"
        elif center_x > 2 * width / 3:
            horizontal = "right"
        else:
            horizontal = "center"

        # Determine vertical position
        if center_y < height / 3:
            vertical = "upper"
        elif center_y > 2 * height / 3:
            vertical = "lower"
        else:
            vertical = "middle"

        return f"{vertical} {horizontal}"

    def _get_highest_severity(self, detections: List[Dict]) -> str:
        """
        Determine the highest severity level among all detections.

        Args:
            detections: List of detection dictionaries

        Returns:
            str: Highest severity level
        """
        if not detections:
            return "none"

        severity_levels = {"light": 1, "moderate": 2, "severe": 3}
        max_severity_value = max([severity_levels.get(d["severity"], 0) for d in detections])

        for severity, value in severity_levels.items():
            if value == max_severity_value:
                return severity

        return "light"
