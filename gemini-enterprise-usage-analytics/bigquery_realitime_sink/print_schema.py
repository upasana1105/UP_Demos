from google.cloud import bigquery

client = bigquery.Client(project="uppdemos")

table_id = "uppdemos.ge_raw_logs_assist.discoveryengine_googleapis_com_gemini_enterprise_user_activity"

print(f"Fetching schema for {table_id}...")
try:
    table = client.get_table(table_id)
    for field in table.schema:
        print(f"- {field.name} ({field.field_type})")
        if field.fields:
            for subfield in field.fields:
                print(f"  + {subfield.name} ({subfield.field_type})")
except Exception as e:
    print(f"Error: {e}")
