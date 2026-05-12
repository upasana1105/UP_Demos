import os
from google.cloud import bigquery

# ==============================================================================
# KPMG Analytics Mock Data Cleanup Script
# ==============================================================================
# This script safely deletes all mock test rows from your raw BigQuery tables,
# leaving real user data completely untouched.

PROJECT_ID = "uppdemos"
GE_PREFIX = "ge_raw_logs_"
NLM_PREFIX = "nlm_raw_logs_"

client = bigquery.Client(project=PROJECT_ID)

# The 15 Gemini Methods + 6 NotebookLM methods
GE_METHODS = [
    "assist", "streamassist", "search", "answerquery", 
    "createengine", "updateengine", "setiampolicy", 
    "createagent", "updateagent", "createagentrequest", 
    "generategroundedcontent", "updatedataconnector", 
    "addcontextfile", "uploadsessionfile", "writeuserevent"
]

NLM_METHODS = [
    "createnotebook", "sharenotebook", "batchdeletenotebooks", 
    "getnotebook", "interactsources", "generatefreeformstreamed"
]

def delete_mock_from_table(table_name):
    # Scans the JSON payload for the "is_mock": true safety flag
    query = f"""
    DELETE FROM `{table_name}`
    WHERE JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.logmetadata.is_mock') = 'true'
    """
    try:
        job = client.query(query)
        job.result() # Wait for execution
        print(f"✓ Cleaned mock data from {table_name}")
    except Exception as e:
        # The table might not have the row if no mock data was added to it
        if "Not found" not in str(e):
            print(f"⚠ Warning cleaning {table_name}: {e}")

def main():
    print("🧹 Starting BQ Mock Data Cleanup...")

    for method in GE_METHODS:
        table = f"{PROJECT_ID}.{GE_PREFIX}{method}.discoveryengine_googleapis_com_gemini_enterprise_user_activity"
        delete_mock_from_table(table)

    for method in NLM_METHODS:
        table = f"{PROJECT_ID}.{NLM_PREFIX}{method}.discoveryengine_googleapis_com_gemini_enterprise_user_activity"
        delete_mock_from_table(table)

    print("\n✨ Cleanup complete! All mock rows safely removed.")

if __name__ == "__main__":
    main()
