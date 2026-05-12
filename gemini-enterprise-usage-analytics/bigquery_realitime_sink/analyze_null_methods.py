import os
from google.cloud import bigquery

client = bigquery.Client(project="uppdemos")

query_view = """
SELECT 
  methodName,
  JSON_VALUE(request, '$.userEvent.eventType') as eventType,
  COUNT(*) as count
FROM `uppdemos.ge_transformed.ge_logs`
GROUP BY 1, 2
"""

query_raw = """
SELECT 
  JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.logmetadata.methodname') as methodName,
  JSON_VALUE(TO_JSON_STRING(jsonPayload), '$.request.userEvent.eventType') as eventType,
  COUNT(*) as count
FROM `uppdemos.ge_raw_logs_writeuserevent.discoveryengine_googleapis_com_gemini_enterprise_user_activity`
GROUP BY 1, 2
"""

print("Querying transformed view...")
try:
    results = client.query(query_view).result()
    print("Transformed View Results:")
    for row in results:
        print(f"Method: {row.methodName} | EventType: {row.eventType} | Count: {row.count}")
except Exception as e:
    print(f"Error querying view: {e}")

print("\nQuerying raw writeuserevent table...")
try:
    results = client.query(query_raw).result()
    print("Raw Results:")
    for row in results:
        print(f"Method: {row.methodName} | EventType: {row.eventType} | Count: {row.count}")
except Exception as e:
    print(f"Error querying raw table: {e}")
