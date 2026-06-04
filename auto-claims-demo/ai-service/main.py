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

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from typing import List, Dict, Any, Optional
from google.cloud import storage

# Local imports
from claims_agent import claim_agent_service
from repair_shop_agent import repair_shop_agent_service
from appointment_agent import run_appointment_agent
from car_damage_detector import CarDamageDetector
from fastapi.concurrency import run_in_threadpool
from telemetry import setup_telemetry

from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

import google.auth

PORT = int(os.environ.get("PORT", "8000"))

setup_telemetry()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HTTPXClientInstrumentor().instrument()
FastAPIInstrumentor.instrument_app(app)

# Configuration
MOCK_MODE = os.environ.get("MOCK_MODE", "false").lower() == "true"

try:
    _, project_id = google.auth.default()
except Exception:
    project_id = "mock-project-id"

PROJECT_ID = os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
REGION = os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "us-central1")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "True")
os.environ.setdefault("GOOGLE_CLOUD_QUOTA_PROJECT", project_id)

# Initialize storage client once
storage_client = None
if not MOCK_MODE:
    try:
        storage_client = storage.Client()
    except Exception as e:
        print(f"Failed to initialize storage client: {e}")

# Initialize Car Damage Detector
detector = None
try:
    detector = CarDamageDetector()
except Exception as e:
    print(f"Failed to initialize CarDamageDetector: {e}")

class Detection(BaseModel):
    label: str
    box: List[float] # [x_min, y_min, x_max, y_max] normalized 0-1
    score: float = 1.0 # Default score if not provided by genai

class ClaimsRequest(BaseModel):
    file_uris: List[str]
    address: Optional[str] = ""

class ClaimsProcessResponse(BaseModel):
    findings: List[str]
    agent_result: Dict[str, Any]
    photo_analyses: Dict[str, List[Detection]] # Key is URI or filename

class RepairShopRequest(BaseModel):
    zip_code: str
    state: str
    make: str
    model: str
    damage_type: str

class RepairShopResponse(BaseModel):
    shops: List[Dict[str, Any]]

class AppointmentRequest(BaseModel):
    session_id: str
    message: str
    context: Optional[Dict[str, Any]] = None

class AppointmentResponse(BaseModel):
    agent_message: str

def read_image_from_gcs(uri: str) -> bytes:
    """Reads image content from GCS URI gs://bucket/path"""
    if not uri.startswith("gs://"):
        raise ValueError(f"Invalid GCS URI: {uri}")

    parts = uri[5:].split("/", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid GCS URI format: {uri}")

    bucket_name, blob_name = parts

    if storage_client is None:
        raise RuntimeError("Storage client not initialized")

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    return blob.download_as_bytes()

@app.get("/ping")
async def ping():
    return {"message": "AI Service is running"}

@app.post("/process-claims", response_model=ClaimsProcessResponse)
async def process_claims(request: ClaimsRequest):
    print(f"Processing {len(request.file_uris)} URIs for claims agent.")

    aggregated_findings = []
    photo_analyses = {}

    for uri in request.file_uris:
        try:
            if MOCK_MODE:
                # In mock mode, we skip real GCS reading and real detection
                # But to keep the structure consistent, let's pretend we found something
                # or just use empty if that's what's expected.
                # The original code mocked content = b"mock content".
                # And then detect_bounding_boxes(mock_content) would return mock boxes if MOCK_MODE inside vision.py.
                # Here we are bypassing vision.py.
                # We can call detector.detect_damage(mock_bytes) but detector might fail or try to load image.
                # So let's handle MOCK_MODE here explicitly if we want mock detections.

                # However, the user request is to use the HuggingFace model.
                # If MOCK_MODE is true, we should probably return mock data directly without calling the model,
                # OR call the model if it can run offline?
                # The original code:
                # if MOCK_MODE: content = b"mock content"
                # boxes = detect_bounding_boxes(content) -> inside vision.py checked MOCK_MODE again.

                # Let's replicate simple mock behavior here to avoid calling heavy model in mock mode if desired.
                detections = [
                    Detection(label="mock_dent", box=[0.1, 0.1, 0.2, 0.2], score=0.9)
                ]
                aggregated_findings.append("mock_dent")
                photo_analyses[uri] = detections
                continue

            else:
                # Use run_in_threadpool for blocking GCS I/O
                content = await run_in_threadpool(read_image_from_gcs, uri)

            # Use YOLO to detect damages
            detections = []

            if detector:
                try:
                     # Run detection in threadpool since it's CPU bound (or GPU bound via C++ extensions)
                    result = await run_in_threadpool(detector.detect_damage, content)
                    height, width = result['image_shape']

                    for d in result['damages']:
                        x1, y1, x2, y2 = d['bbox']
                        # Normalize to 0-1
                        box_normalized = [
                            x1 / width,
                            y1 / height,
                            x2 / width,
                            y2 / height
                        ]

                        detections.append(Detection(
                            label=d['type'],
                            box=box_normalized,
                            score=d['confidence']
                        ))

                        aggregated_findings.append(d['type'])
                except Exception as e:
                    print(f"Error running detector on {uri}: {e}")
            else:
                print("Detector not initialized")

            photo_analyses[uri] = detections

        except Exception as e:
            print(f"Error processing file {uri}: {e}")
            photo_analyses[uri] = []

    # Run Sequential Agent
    if not aggregated_findings:
        aggregated_findings = ["No visible damage detected."]

    if MOCK_MODE:
        agent_response = mock_claims_agent_response(aggregated_findings)
    else:
        agent_response = await claim_agent_service.run_claims_agent(aggregated_findings, request.address)

    return ClaimsProcessResponse(
        findings=aggregated_findings,
        agent_result=agent_response,
        photo_analyses=photo_analyses
    )

@app.post("/find-repair-shops", response_model=RepairShopResponse)
async def find_repair_shops(request: RepairShopRequest):
    print(f"Finding repair shops for {request.make} {request.model} near {request.zip_code}")

    if MOCK_MODE:
        return mock_repair_shop_search()

    shops = await repair_shop_agent_service.run_repair_shop_agent(
        request.zip_code,
        request.state,
        request.make,
        request.model,
        request.damage_type
    )
    return RepairShopResponse(shops=shops)

@app.post("/book-appointment", response_model=AppointmentResponse)
async def book_appointment(request: AppointmentRequest):
    print(f"Booking appointment session {request.session_id}")

    response = await run_appointment_agent(
        request.session_id,
        request.message,
        request.context
    )

    return AppointmentResponse(agent_message=response)

def mock_repair_shop_search():
    return {
        "shops": [
            {
                "name": "Joe's Auto Body",
                "address": "123 Main St, Springfield, IL",
                "rating": 4.5,
                "phone": "555-123-4567",
                "reasoning": "High rating and close to your location."
            },
            {
                "name": "Expert Collision Center",
                "address": "456 Elm St, Springfield, IL",
                "rating": 4.8,
                "phone": "555-987-6543",
                "reasoning": "Specializes in collision repair."
            }
        ]
    }

def mock_claims_agent_response(findings):
    return {
        "decision": "Approved",
        "reasoning": "Damage is minor and consistent with description (MOCK).",
        "estimate": {
            "items": [
                {"part": "Bumper Repair", "cost": 350.00},
                {"part": "Labor (2 hours)", "cost": 200.00},
                {"part": "Paint Touch-up", "cost": 150.00}
            ],
            "total_cost": 700.00
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
