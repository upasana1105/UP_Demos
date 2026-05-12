import os
import json
import datetime
from google.cloud import bigquery

# ==============================================================================
# KPMG Azure Data Lake Bridge (Case: 68431986)
# ==============================================================================
# This script demonstrates how KPMG can extract the standardized, future-proof 
# usage data from BigQuery and stage it for Azure Data Lake / PowerBI ingestion.

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "uppdemos")
OUTPUT_FILE = "kpmg_usage_extract.jsonl"

# Optional: If they want to push directly to Azure Blob Storage
# from azure.storage.blob import BlobServiceClient

def extract_from_bigquery():
    print(f"Connecting to BigQuery (Project: {PROJECT_ID})...")
    client = bigquery.Client(project=PROJECT_ID)
    
    # Pulling from the future-proof aggregation layer
    query = f"""
    SELECT 
      timestamp,
      serviceLabel,
      methodName,
      is_true_prompt,
      userIamPrincipal,
      userQuery,
      serviceTextReply,
      session_id,
      engine_id,
      -- Export raw JSON payloads for deep Azure analysis if needed
      TO_JSON_STRING(request) as request_json,
      TO_JSON_STRING(response) as response_json
    FROM `{PROJECT_ID}.ge_transformed.kpmg_standardized_logs`
    ORDER BY timestamp DESC
    """
    
    print("Executing extract query...")
    query_job = client.query(query)
    results = query_job.result()
    
    print(f"Writing results to {OUTPUT_FILE}...")
    count = 0
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for row in results:
            # Convert BigQuery Row to dictionary
            record = {
                "timestamp": row.timestamp.isoformat() if row.timestamp else None,
                "serviceLabel": row.serviceLabel,
                "methodName": row.methodName,
                "is_true_prompt": row.is_true_prompt,
                "userIamPrincipal": row.userIamPrincipal,
                "userQuery": row.userQuery,
                "serviceTextReply": row.serviceTextReply,
                "session_id": row.session_id,
                "engine_id": row.engine_id,
                "request_json": row.request_json,
                "response_json": row.response_json
            }
            # Write as JSON Lines (standard format for Data Lakes)
            f.write(json.dumps(record) + "\n")
            count += 1
            
    print(f"✓ Successfully extracted {count} standardized records.")
    return OUTPUT_FILE

def push_to_azure_blob(file_path):
    """
    Boilerplate for KPMG's Azure ingestion pipeline.
    """
    print("\n[Azure Integration Blueprint]")
    print("To push this file to Azure Data Lake, KPMG can use this logic:")
    print("""
    from azure.storage.blob import BlobServiceClient
    
    AZURE_CONNECTION_STRING = "DefaultEndpointsProtocol=https;AccountName=kpmgstorage;..."
    CONTAINER_NAME = "gemini-usage-data"
    
    blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
    blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob="extracts/kpmg_usage_extract.jsonl")
    
    with open("kpmg_usage_extract.jsonl", "rb") as data:
        blob_client.upload_blob(data, overwrite=True)
        
    print("Upload to Azure Data Lake complete.")
    """)

def main():
    file_path = extract_from_bigquery()
    push_to_azure_blob(file_path)

if __name__ == "__main__":
    main()
