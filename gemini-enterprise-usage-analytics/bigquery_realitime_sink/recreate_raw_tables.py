import os
from google.cloud import bigquery

# ==============================================================================
# Recreate Raw Tables with Flexible JSON Schema
# ==============================================================================
# Drops the rigid placeholder tables and creates new tables where 'jsonPayload'
# is a JSON type. This allows inserting rich mock logs without schema errors.

PROJECT_ID = "uppdemos"
GE_PREFIX = "ge_raw_logs_"
NLM_PREFIX = "nlm_raw_logs_"

client = bigquery.Client(project=PROJECT_ID)

GE_METHODS = [
    "search", "assist", "streamassist", "answerquery", 
    "createengine", "updateengine", "setiampolicy", 
    "createagent", "updateagent", "createagentrequest", 
    "generategroundedcontent", "updatedataconnector", 
    "addcontextfile", "uploadsessionfile", "writeuserevent"
]

NLM_METHODS = [
    "createnotebook", "sharenotebook", "batchdeletenotebooks", 
    "getnotebook", "interactsources", "generatefreeformstreamed"
]

def recreate_table(dataset_prefix, method):
    dataset_id = f"{dataset_prefix}{method}"
    table_id = f"{PROJECT_ID}.{dataset_id}.discoveryengine_googleapis_com_gemini_enterprise_user_activity"
    
    print(f"Dropping table: {table_id}")
    client.delete_table(table_id, not_found_ok=True)
    
    # Define flexible schema (jsonPayload as JSON type)
    schema = [
        bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("jsonPayload", "JSON", mode="NULLABLE"),
        bigquery.SchemaField("insertId", "STRING", mode="NULLABLE")
    ]
    
    table = bigquery.Table(table_id, schema=schema)
    table.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY,
        field="timestamp"
    )
    
    print(f"Creating table: {table_id}")
    client.create_table(table)

def main():
    for method in GE_METHODS:
        recreate_table(GE_PREFIX, method)
    for method in NLM_METHODS:
        recreate_table(NLM_PREFIX, method)
    print("✓ All raw tables recreated with flexible JSON schemas.")

if __name__ == "__main__":
    main()
