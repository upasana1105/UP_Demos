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
import csv
import random
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, PolicyHolder

DATABASE_PATH = os.environ.get("DATABASE_PATH", "claims.db")
engine = create_engine(f"sqlite:///{DATABASE_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

FIRST_NAMES = ["John", "Jane", "Michael", "Sarah", "David", "Emily", "Robert", "Jessica", "William", "Jennifer"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]

def init_db():
    Base.metadata.create_all(bind=engine)
    seed_policy_holders()

def seed_policy_holders():
    db = SessionLocal()
    try:
        count = db.query(PolicyHolder).count()
        if count > 0:
            print("Policy holders already seeded.")
            return

        print("Seeding PolicyHolders table from local CSV...")
        csv_path = os.path.join(os.path.dirname(__file__), "data", "insurance_claims.csv")
        if not os.path.exists(csv_path):
            print(f"CSV file not found at: {csv_path}")
            return

        random.seed(42)  # For deterministic names matching some tests if needed

        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)  # Skip header

            policy_holders = []
            for row in reader:
                if not row:
                    continue
                
                try:
                    # Helper functions for safe parsing
                    months = int(row[0]) if row[0] else 0
                    age = int(row[1]) if row[1] else 0
                    policy_num = row[2]
                    
                    try:
                        bind_date = datetime.strptime(row[3], "%Y-%m-%d")
                    except ValueError:
                        bind_date = datetime.utcnow()
                        
                    policy_state = row[4]
                    policy_csl = row[5]
                    deductible = int(row[6]) if row[6] else 0
                    premium = float(row[7]) if row[7] else 0.0
                    umbrella = int(row[8]) if row[8] else 0
                    zip_code = int(row[9]) if row[9] else 0
                    sex = row[10]
                    education = row[11]
                    occupation = row[12]
                    hobbies = row[13]
                    relationship = row[14]
                    gains = int(row[15]) if row[15] else 0
                    loss = int(row[16]) if row[16] else 0
                    
                    auto_make = row[35]
                    auto_model = row[36]
                    auto_year = int(row[37]) if row[37] else 0

                    holder = PolicyHolder(
                        first_name=random.choice(FIRST_NAMES),
                        last_name=random.choice(LAST_NAMES),
                        months_as_customer=months,
                        age=age,
                        policy_number=policy_num,
                        policy_bind_date=bind_date,
                        policy_state=policy_state,
                        policy_csl=policy_csl,
                        policy_deductible=deductible,
                        policy_annual_premium=premium,
                        umbrella_limit=umbrella,
                        insured_zip=zip_code,
                        insured_sex=sex,
                        insured_education_level=education,
                        insured_occupation=occupation,
                        insured_hobbies=hobbies,
                        insured_relationship=relationship,
                        capital_gains=gains,
                        capital_loss=loss,
                        auto_make=auto_make,
                        auto_model=auto_model,
                        auto_year=auto_year
                    )
                    policy_holders.append(holder)
                except Exception as e:
                    print(f"Error parsing row: {e}")

            if policy_holders:
                db.bulk_save_objects(policy_holders)
                db.commit()
                print(f"Successfully seeded {len(policy_holders)} PolicyHolders.")
    finally:
        db.close()
