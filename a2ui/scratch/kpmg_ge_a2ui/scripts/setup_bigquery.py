"""
BigQuery Setup Script - Creates dataset, table, and loads mock employee data.

Run this once before deploying the agent:
    python scripts/setup_bigquery.py

This will create:
    - Dataset: employee_verification
    - Table: employee_records
    - 6 mock employee records
"""

import os
import sys

from dotenv import load_dotenv
from google.cloud import bigquery

# Load .env from project root
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

PROJECT_ID = os.environ.get("PROJECT_ID", "kpmg-452019")
DATASET_ID = "employee_verification"
TABLE_ID = "employee_records"
LOCATION = os.environ.get("LOCATION", "us-central1")

SCHEMA = [
    bigquery.SchemaField("employee_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("name", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("title", "STRING"),
    bigquery.SchemaField("department", "STRING"),
    bigquery.SchemaField("location", "STRING"),
    bigquery.SchemaField("address", "STRING"),
    bigquery.SchemaField("phone", "STRING"),
    bigquery.SchemaField("email", "STRING"),
    bigquery.SchemaField("emergency_contact", "STRING"),
    bigquery.SchemaField("emergency_phone", "STRING"),
    bigquery.SchemaField("manager", "STRING"),
    bigquery.SchemaField("employment_status", "STRING"),
    bigquery.SchemaField("hire_date", "DATE"),
    bigquery.SchemaField("termination_date", "DATE"),
    bigquery.SchemaField("salary_band", "STRING"),
    bigquery.SchemaField("verified", "BOOLEAN"),
    bigquery.SchemaField("verified_date", "TIMESTAMP"),
]

MOCK_DATA = [
    {
        "employee_id": "E-1001",
        "name": "John Smith",
        "title": "Senior Financial Analyst",
        "department": "Finance",
        "location": "New York",
        "address": "456 Oak Avenue, Apt 12B, New York, NY 10001",
        "phone": "(555) 123-4567",
        "email": "john.smith@kpmg-demo.com",
        "emergency_contact": "Jane Smith",
        "emergency_phone": "(555) 987-6543",
        "manager": "Sarah Chen",
        "employment_status": "Active",
        "hire_date": "2021-03-15",
        "termination_date": None,
        "salary_band": "Band 4",
        "verified": False,
        "verified_date": None,
    },
    {
        "employee_id": "E-1002",
        "name": "Maria Garcia",
        "title": "Tax Consultant",
        "department": "Tax Advisory",
        "location": "Chicago",
        "address": "789 Elm Street, Suite 300, Chicago, IL 60601",
        "phone": "(555) 234-5678",
        "email": "maria.garcia@kpmg-demo.com",
        "emergency_contact": "Carlos Garcia",
        "emergency_phone": "(555) 876-5432",
        "manager": "David Kim",
        "employment_status": "Active",
        "hire_date": "2019-08-01",
        "termination_date": None,
        "salary_band": "Band 5",
        "verified": False,
        "verified_date": None,
    },
    {
        "employee_id": "E-1003",
        "name": "Raj Patel",
        "title": "IT Security Specialist",
        "department": "Technology",
        "location": "San Francisco",
        "address": "123 Pine Road, San Francisco, CA 94102",
        "phone": "(555) 345-6789",
        "email": "raj.patel@kpmg-demo.com",
        "emergency_contact": "Priya Patel",
        "emergency_phone": "(555) 765-4321",
        "manager": "Lisa Wong",
        "employment_status": "Active",
        "hire_date": "2022-01-10",
        "termination_date": None,
        "salary_band": "Band 4",
        "verified": False,
        "verified_date": None,
    },
    {
        "employee_id": "E-1004",
        "name": "Emily Johnson",
        "title": "Audit Manager",
        "department": "Audit & Assurance",
        "location": "Dallas",
        "address": "321 Maple Drive, Dallas, TX 75201",
        "phone": "(555) 456-7890",
        "email": "emily.johnson@kpmg-demo.com",
        "emergency_contact": "Michael Johnson",
        "emergency_phone": "(555) 654-3210",
        "manager": "Robert Williams",
        "employment_status": "Active",
        "hire_date": "2018-06-20",
        "termination_date": None,
        "salary_band": "Band 6",
        "verified": True,
        "verified_date": "2025-12-01T10:30:00Z",
    },
    {
        "employee_id": "E-1005",
        "name": "David Lee",
        "title": "Advisory Consultant",
        "department": "Advisory",
        "location": "Los Angeles",
        "address": "567 Cedar Lane, Los Angeles, CA 90001",
        "phone": "(555) 567-8901",
        "email": "david.lee@kpmg-demo.com",
        "emergency_contact": "Susan Lee",
        "emergency_phone": "(555) 543-2109",
        "manager": "Jennifer Martinez",
        "employment_status": "On Leave",
        "hire_date": "2020-11-05",
        "termination_date": None,
        "salary_band": "Band 3",
        "verified": False,
        "verified_date": None,
    },
    {
        "employee_id": "E-1006",
        "name": "Sarah Williams",
        "title": "HR Business Partner",
        "department": "Human Resources",
        "location": "Atlanta",
        "address": "890 Birch Boulevard, Atlanta, GA 30301",
        "phone": "(555) 678-9012",
        "email": "sarah.williams@kpmg-demo.com",
        "emergency_contact": "Tom Williams",
        "emergency_phone": "(555) 432-1098",
        "manager": "Patricia Brown",
        "employment_status": "Active",
        "hire_date": "2017-02-14",
        "termination_date": None,
        "salary_band": "Band 5",
        "verified": False,
        "verified_date": None,
    },
]


def main():
    print(f"Setting up BigQuery for project: {PROJECT_ID}")
    print(f"Dataset: {DATASET_ID}, Table: {TABLE_ID}")
    print("=" * 60)

    client = bigquery.Client(project=PROJECT_ID)

    # 1. Create dataset
    dataset_ref = bigquery.Dataset(f"{PROJECT_ID}.{DATASET_ID}")
    dataset_ref.location = LOCATION
    try:
        dataset = client.create_dataset(dataset_ref, exists_ok=True)
        print(f"✓ Dataset '{DATASET_ID}' ready (location: {dataset.location})")
    except Exception as e:
        print(f"✗ Error creating dataset: {e}")
        sys.exit(1)

    # 2. Create table
    table_ref = bigquery.Table(f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}", schema=SCHEMA)
    try:
        table = client.create_table(table_ref, exists_ok=True)
        print(f"✓ Table '{TABLE_ID}' ready ({len(SCHEMA)} columns)")
    except Exception as e:
        print(f"✗ Error creating table: {e}")
        sys.exit(1)

    # 3. Check if data already exists
    count_query = f"SELECT COUNT(*) as cnt FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`"
    try:
        result = list(client.query(count_query).result())
        existing_count = result[0].cnt
        if existing_count > 0:
            print(f"⚠ Table already has {existing_count} rows. Skipping data load.")
            print("  To reload, delete existing rows first:")
            print(f"  DELETE FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}` WHERE TRUE")
            return
    except Exception:
        pass  # Table might be newly created

    # 4. Load mock data
    job_config = bigquery.LoadJobConfig(
        schema=SCHEMA,
    )
    try:
        load_job = client.load_table_from_json(
            MOCK_DATA,
            f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}",
            job_config=job_config,
        )
        load_job.result()  # Wait for job to complete
        print(f"✓ Loaded {len(MOCK_DATA)} mock employee records via load job")
    except Exception as e:
        print(f"✗ Error loading data: {e}")
        sys.exit(1)
    print("=" * 60)
    print("BigQuery setup complete!")
    print(f"\nVerify with: bq query --use_legacy_sql=false 'SELECT employee_id, name, department FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`'")


if __name__ == "__main__":
    main()
