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

import os
import shutil
from typing import List, Optional
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session, joinedload
import httpx
import json

from models import Claim, Photo, AnalysisResult, Estimate, PolicyHolder
from database import init_db, SessionLocal
from gcs_utils import upload_file_to_gcs, generate_signed_url
from mcp_client import resolve_address_via_mcp

PORT = int(os.environ.get("PORT", "8080"))
AI_SERVICE_URL = os.environ.get("AI_SERVICE_URL", "http://localhost:8000")
BUCKET_NAME = os.environ.get("BUCKET_NAME", "")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure uploads folder exists
os.makedirs("./uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="./uploads"), name="uploads")

# DB Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/ping")
async def ping():
    return {"message": "pong"}

# Get policyholder details
@app.get("/api/policies/{number}")
async def get_policy(number: str, db: Session = Depends(get_db)):
    policy = db.query(PolicyHolder).filter(PolicyHolder.policy_number == number).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy

# List all claims
@app.get("/api/claims")
async def list_claims(policy_number: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Claim).options(joinedload(Claim.photos), joinedload(Claim.estimates))
    if policy_number:
        query = query.filter(Claim.policy_number == policy_number)
    claims = query.all()
    
    # Process signed URLs
    for claim in claims:
        for photo in claim.photos:
            photo.url = generate_signed_url(BUCKET_NAME, photo.url)
            
    return claims

# Get single claim details
@app.get("/api/claims/{claim_id}")
async def get_claim(claim_id: int, db: Session = Depends(get_db)):
    claim = db.query(Claim).options(
        joinedload(Claim.photos).joinedload(Photo.analysis_result),
        joinedload(Claim.estimates)
    ).filter(Claim.id == claim_id).first()
    
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
        
    for photo in claim.photos:
        photo.url = generate_signed_url(BUCKET_NAME, photo.url)
        
    return claim

# Update claim status
@app.patch("/api/claims/{claim_id}")
@app.put("/api/claims/{claim_id}")
async def update_claim(claim_id: int, request: Request, db: Session = Depends(get_db)):
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
        
    body = await request.json()
    if "status" in body:
        claim.status = body["status"]
    if "severity" in body:
        claim.severity = body["severity"]
        
    db.commit()
    db.refresh(claim)
    return claim

# Delete claim
@app.delete("/api/claims/{claim_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_claim(claim_id: int, db: Session = Depends(get_db)):
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
        
    db.delete(claim)
    db.commit()
    return None

# Create claim with photo uploads
@app.post("/api/claims", status_code=status.HTTP_201_CREATED)
async def create_claim(
    policy_number: str = Form(...),
    customer_name: str = Form(""),
    description: str = Form(""),
    accident_date: str = Form(""),
    incident_city: str = Form(""),
    incident_state: str = Form(""),
    incident_type: str = Form(""),
    collision_type: str = Form(""),
    severity: str = Form(""),
    files: List[UploadFile] = File([]),
    db: Session = Depends(get_db)
):
    parsed_date = None
    if accident_date:
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z"):
            try:
                # Strip timezone suffix if standard parsing fails
                clean_date = accident_date.split(".")[0].rstrip("Z")
                parsed_date = datetime.strptime(clean_date, "%Y-%m-%dT%H:%M:%S" if "T" in clean_date else "%Y-%m-%d")
                break
            except ValueError:
                continue
        if not parsed_date:
            raise HTTPException(status_code=400, detail="Invalid accident date format. Use YYYY-MM-DD or ISO-8601")

    claim = Claim(
        policy_number=policy_number,
        customer_name=customer_name,
        description=description,
        status="New",
        accident_date=parsed_date,
        incident_city=incident_city,
        incident_state=incident_state,
        incident_type=incident_type,
        collision_type=collision_type,
        severity=severity
    )
    db.add(claim)
    db.commit()
    db.refresh(claim)

    policy_upload_dir = f"./uploads/{policy_number}"
    os.makedirs(policy_upload_dir, exist_ok=True)

    for file in files:
        if not file.filename:
            continue
        
        # Save file locally
        local_filename = os.path.basename(file.filename)
        local_path = os.path.join(policy_upload_dir, local_filename)
        with open(local_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # GCS URL format: policyNumber/filename
        gcs_object_name = f"{policy_number}/{local_filename}"
        
        # Attempt GCS upload if bucket configured
        uploaded_gcs = False
        if BUCKET_NAME:
            with open(local_path, "rb") as local_file:
                uploaded_gcs = upload_file_to_gcs(BUCKET_NAME, gcs_object_name, local_file)

        # Store path: Store gcs path if uploaded successfully, else local path prefix
        photo_url = gcs_object_name if uploaded_gcs else f"uploads/{policy_number}/{local_filename}"
        
        photo = Photo(claim_id=claim.id, url=photo_url)
        db.add(photo)

    db.commit()
    db.refresh(claim)
    
    # Sign URLs for response
    for photo in claim.photos:
        photo.url = generate_signed_url(BUCKET_NAME, photo.url)
        
    return claim

# Trigger AI analysis for a claim
@app.post("/api/claims/{claim_id}/analyze")
async def analyze_claim(claim_id: int, db: Session = Depends(get_db)):
    claim = db.query(Claim).options(joinedload(Claim.photos)).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    if not BUCKET_NAME:
        # If GCS not configured, we'll try to analyze local files if the AI service runs mock or locally.
        # But let's log warning
        print("Warning: BUCKET_NAME not configured. Passing local fallback URIs or empty to AI Service.")
        
    claim.status = "Analyzing"
    db.commit()

    file_uris = []
    for photo in claim.photos:
        # If photo url starts with uploads/, it means it is local
        if photo.url.startswith("uploads/"):
            # Can we use GCS? If not, let's construct mock gs:// or pass as local path
            # But the real AI service expects gs://bucket/policy/filename
            # Let's construct a mock URI if bucket_name is empty, e.g. gs://mock-bucket/path
            file_uris.append(f"gs://mock-bucket/{photo.url.replace('uploads/', '')}")
        else:
            # It's already the GCS path (e.g. policyNumber/filename)
            file_uris.append(f"gs://{BUCKET_NAME}/{photo.url}")

    address = claim.incident_city
    if claim.incident_state:
        address = f"{claim.incident_city}, {claim.incident_state}"

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            resp = await client.post(
                f"{AI_SERVICE_URL}/process-claims",
                json={"file_uris": file_uris, "address": address}
            )
            if resp.status_code != 200:
                claim.status = "Failed"
                db.commit()
                raise HTTPException(status_code=502, detail=f"AI Service returned status code {resp.status_code}")
                
            ai_data = resp.json()
        except Exception as e:
            claim.status = "Failed"
            db.commit()
            raise HTTPException(status_code=502, detail=f"Failed to connect to AI Service: {str(e)}")

    # Update photo analyses
    photo_analyses = ai_data.get("photo_analyses", {})
    for photo in claim.photos:
        # Try to match key
        # key could be gs://bucket/policy/filename or policy/filename
        matching_key = None
        for key in photo_analyses.keys():
            if photo.url in key or key.endswith(photo.url):
                matching_key = key
                break
                
        if not matching_key:
            # Fallback check
            filename = photo.url.split("/")[-1]
            for key in photo_analyses.keys():
                if filename in key:
                    matching_key = key
                    break

        if matching_key:
            detections_list = photo_analyses[matching_key]
            detections_str = json.dumps(detections_list)
            parts = list(set([d["label"] for d in detections_list]))
            parts_str = ",".join(parts)
            severity_val = "Unknown"
            if detections_list:
                # Get highest severity or just "moderate"
                severity_val = detections_list[0].get("severity", "moderate")

            analysis = db.query(AnalysisResult).filter(AnalysisResult.photo_id == photo.id).first()
            if not analysis:
                analysis = AnalysisResult(
                    photo_id=photo.id,
                    quality_score="Good",
                    detections=detections_str,
                    parts_detected=parts_str,
                    severity=severity_val
                )
                db.add(analysis)
            else:
                analysis.detections = detections_str
                analysis.parts_detected = parts_str
                analysis.severity = severity_val
                
    # Update Estimate
    agent_result = ai_data.get("agent_result", {})
    estimate_info = agent_result.get("estimate", {})
    total_cost = estimate_info.get("total_cost", 0.0)
    items_list = estimate_info.get("items", [])
    items_str = json.dumps(items_list)

    # Save estimate
    estimate = db.query(Estimate).filter(Estimate.claim_id == claim.id).first()
    if not estimate:
        estimate = Estimate(
            claim_id=claim.id,
            total_amount=total_cost,
            items=items_str,
            source="AI Agent"
        )
        db.add(estimate)
    else:
        estimate.total_amount = total_cost
        estimate.items = items_str
        estimate.source = "AI Agent"

    claim.status = "Assessed"
    claim.severity = agent_result.get("decision", "Approved") # Or severity decision
    db.commit()
    
    # Reload and return claim
    db.refresh(claim)
    for photo in claim.photos:
        photo.url = generate_signed_url(BUCKET_NAME, photo.url)
        
    return claim

# Find repair shops near the policyholder
@app.post("/api/claims/{claim_id}/repair-shops")
async def find_repair_shops(claim_id: int, db: Session = Depends(get_db)):
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    policy = db.query(PolicyHolder).filter(PolicyHolder.policy_number == claim.policy_number).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policyholder not found")

    damage_type = claim.description or "auto body repair"
    req_body = {
        "zip_code": str(policy.insured_zip),
        "state": policy.policy_state,
        "make": policy.auto_make,
        "model": policy.auto_model,
        "damage_type": damage_type
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            resp = await client.post(f"{AI_SERVICE_URL}/find-repair-shops", json=req_body)
            if resp.status_code != 200:
                raise HTTPException(status_code=502, detail="AI Service failed to find repair shops")
            return resp.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Failed to connect to AI Service: {str(e)}")

# Proxy request to AI service for booking
@app.post("/api/claims/{claim_id}/book-appointment")
async def book_appointment(claim_id: int, request: Request, db: Session = Depends(get_db)):
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    body = await request.json()
    session_id = body.get("session_id")
    message = body.get("message")
    shop_name = body.get("shop_name", "Unknown Shop")
    customer_name = body.get("customer_name", claim.customer_name)

    req_body = {
        "session_id": session_id,
        "message": message,
        "context": {
            "shop_name": shop_name,
            "customer_name": customer_name
        }
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            resp = await client.post(f"{AI_SERVICE_URL}/book-appointment", json=req_body)
            if resp.status_code != 200:
                raise HTTPException(status_code=502, detail="AI Service failed to book appointment")
            return resp.json()
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Failed to connect to AI Service: {str(e)}")

# Resolve address endpoint
@app.post("/api/resolve-address")
async def resolve_address(request: Request):
    body = await request.json()
    address = body.get("address")
    if not address:
        raise HTTPException(status_code=400, detail="Address is required")

    try:
        result = await resolve_address_via_mcp(address)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
