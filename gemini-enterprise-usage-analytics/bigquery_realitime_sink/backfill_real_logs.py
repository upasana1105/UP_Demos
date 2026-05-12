import os
import json
import subprocess
from google.cloud import bigquery

# ==============================================================================
# KPMG Analytics Real Log Backfiller (Expanded History Search Window)
# ==============================================================================
# Expands the log query window limit to 1000 entries to automatically discover
# organic historical CreateAgent lifecycle events from previous days.

PROJECT_ID = "uppdemos"
GE_PREFIX = "ge_raw_logs_"

client = bigquery.Client(project=PROJECT_ID)

def main():
    print("📡 Connecting to GCP Cloud Logging History (1000 entries search window)...")
    
    cmd = [
        "gcloud", "logging", "read",
        'logName:"gemini_enterprise_user_activity"',
        f"--project={PROJECT_ID}",
        "--format=json",
        "--limit=1000"  # EXPANDED LOOKBACK WINDOW FOR ORGANIC LIFECYCLE LOOKUPS
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logs = json.loads(result.stdout)
        print(f"✓ Successfully retrieved {len(logs)} organic historical logs from Cloud Logging.")
    except Exception as e:
        print(f"✗ Error reading from Cloud Logging: {e}")
        return

    print("\n🚀 Syncing history into native BigQuery schemas...")
    success_count = 0
    for log in logs:
        payload = log.get("jsonPayload")
        if not payload:
            continue
            
        method = payload.get("logMetadata", {}).get("methodName")
        if not method:
            continue
            
        table_ref = f"{PROJECT_ID}.{GE_PREFIX}{method.lower()}.discoveryengine_googleapis_com_gemini_enterprise_user_activity"
        
        timestamp = log.get("timestamp")
        if timestamp and "." in timestamp and timestamp.endswith("Z"):
            parts = timestamp.split(".")
            micro_part = parts[1][:-1][:6]
            timestamp = f"{parts[0]}.{micro_part}Z"
            
        insert_id = log.get("insertId", "")
        
        row_to_insert = {
            "timestamp": timestamp,
            "jsonPayload": payload,
            "insertId": insert_id
        }
        
        try:
            errors = client.insert_rows_json(table_ref, [row_to_insert])
            if not errors:
                success_count += 1
        except Exception as e:
            if "Not found" in str(e):
                pass
            else:
                print(f"⚠ Error backfilling row to {method}: {e}")
                
    print(f"\n✨ Sync complete! {success_count} total historical logs loaded into BigQuery.")

if __name__ == "__main__":
    main()
