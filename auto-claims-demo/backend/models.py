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

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import datetime

Base = declarative_base()

class PolicyHolder(Base):
    __tablename__ = "policy_holders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    policy_number = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    months_as_customer = Column(Integer)
    age = Column(Integer)
    policy_bind_date = Column(DateTime)
    policy_state = Column(String)
    policy_csl = Column(String)
    policy_deductible = Column(Integer)
    policy_annual_premium = Column(Float)
    umbrella_limit = Column(Integer)
    insured_zip = Column(Integer)
    insured_sex = Column(String)
    insured_education_level = Column(String)
    insured_occupation = Column(String)
    insured_hobbies = Column(String)
    insured_relationship = Column(String)
    capital_gains = Column(Integer)
    capital_loss = Column(Integer)
    auto_make = Column(String)
    auto_model = Column(String)
    auto_year = Column(Integer)

class Claim(Base):
    __tablename__ = "claims"

    id = Column(Integer, primary_key=True, autoincrement=True)
    policy_number = Column(String)
    customer_name = Column(String)
    status = Column(String, default="New")
    description = Column(String)
    accident_date = Column(DateTime)
    incident_city = Column(String)
    incident_state = Column(String)
    incident_type = Column(String)
    collision_type = Column(String)
    severity = Column(String)
    total_loss_probability = Column(Float, default=0.0)
    action_required = Column(Boolean, default=False)

    photos = relationship("Photo", back_populates="claim", cascade="all, delete-orphan")
    estimates = relationship("Estimate", back_populates="claim", cascade="all, delete-orphan")

class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    claim_id = Column(Integer, ForeignKey("claims.id", ondelete="CASCADE"))
    url = Column(String)

    claim = relationship("Claim", back_populates="photos")
    analysis_result = relationship("AnalysisResult", uselist=False, back_populates="photo", cascade="all, delete-orphan")

class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    photo_id = Column(Integer, ForeignKey("photos.id", ondelete="CASCADE"))
    quality_score = Column(String)
    detections = Column(String)  # JSON string
    parts_detected = Column(String)  # Comma separated
    severity = Column(String)

    photo = relationship("Photo", back_populates="analysis_result")

class Estimate(Base):
    __tablename__ = "estimates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    claim_id = Column(Integer, ForeignKey("claims.id", ondelete="CASCADE"))
    total_amount = Column(Float)
    items = Column(String)  # JSON string
    source = Column(String)

    claim = relationship("Claim", back_populates="estimates")
