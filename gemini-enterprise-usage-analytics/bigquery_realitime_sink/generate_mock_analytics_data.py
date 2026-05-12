import os
import random
import json
import datetime
from google.cloud import bigquery

# ==============================================================================
# KPMG Analytics Mock Data Generator (Including Today May 3)
# ==============================================================================
# Updates get_random_timestamp to generate logs up to May 3 (today) so they 
# appear at the very top of your dashboard and query results.

PROJECT_ID = "uppdemos"
GE_PREFIX = "ge_raw_logs_"
NLM_PREFIX = "nlm_raw_logs_"

client = bigquery.Client(project=PROJECT_ID)

USERS = [
    "admin@upasanapati.altostrat.com",
    "upasanapati@google.com",
    "mock_user@kpmg.com"
]

AGENTS = [
    "hr-assistant-v2",
    "it-helpdesk-pro",
    "finance-analyzer",
    "legal-doc-reviewer",
    "marketing-copilot"
]

PROMPTS_AND_REPLIES = [
    ("show me my jira tickets", "I have pulled up your Jira tickets for review."),
    ("Show me the opportunities for the North region", "I found two opportunities for the North region."),
    ("Employ verification", "Hello Upasana, it seems there are multiple employee records."),
    ("can you give me the urls of the latest policies?", "Here are the requested policy URLs."),
    ("what is my latest email from HR?", "You received an email from HR regarding benefits yesterday.")
]

NOTEBOOK_PROMPTS = [
    "Create a Study Guide for the project documentation.",
    "Generate a Briefing Doc for the upcoming audit.",
    "Can you create an FAQ on the new compliance guidelines?",
    "Build a Timeline for the product launch roadmap."
]

FEEDBACK_COMMENTS = [
    "Perfect retrieval of my Jira issues.",
    "Did not find the correct sales opportunity.",
    "The policy link is broken.",
    "Very helpful HR response.",
    "The summary missed the key financial ratios."
]

def get_random_timestamp():
    start_date = datetime.datetime(2026, 4, 28, tzinfo=datetime.timezone.utc)
    # Crucial Fix: Set end_date to include May 3 (today!)
    end_date = datetime.datetime(2026, 5, 3, 23, 59, 59, tzinfo=datetime.timezone.utc)
    time_between = end_date - start_date
    random_seconds = random.randrange(int(time_between.total_seconds()))
    return start_date + datetime.timedelta(seconds=random_seconds)

def insert_rows_dml(table_name, rows):
    print(f"Inserting {len(rows)} rows into {table_name} via DML...")
    for row in rows:
        query = f"""
        INSERT INTO `{table_name}` (timestamp, jsonPayload, insertId)
        VALUES (@timestamp, PARSE_JSON(@jsonPayload), @insertId)
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("timestamp", "TIMESTAMP", row["timestamp"]),
                bigquery.ScalarQueryParameter("jsonPayload", "STRING", json.dumps(row["jsonPayload"])),
                bigquery.ScalarQueryParameter("insertId", "STRING", row.get("insertId", ""))
            ]
        )
        try:
            client.query(query, job_config=job_config).result()
        except Exception as e:
            print(f"⚠ DML Error on {table_name}: {e}")
            break
    print(f"✓ Finished DML inserts for {table_name}")

def main():
    print("🚀 Generating DML test data including May 3 (today)...")

    # 1. Gemini Chat Logs (StreamAssist & Search)
    chat_rows = []
    for i in range(30):
        ts = get_random_timestamp()
        user = random.choice(USERS)
        agent = random.choice(AGENTS)
        method = random.choice(["StreamAssist", "Search"])
        session_id = f"session-{random.randint(1000, 9999)}"
        query, reply = random.choice(PROMPTS_AND_REPLIES)
        
        payload = {
            "logmetadata": {
                "servicelabel": "GEMINI_ENTERPRISE",
                "methodname": method,
                "servicename": "projects/850431687571/locations/global/collections/default_collection/engines/gemini-enterprise-gm_1771086459519",
                "is_mock": "true"
            },
            "useriamprincipal": user,
            "request": {
                "name": f"projects/850431687571/locations/global/collections/default_collection/engines/{agent}",
                "query": query,
                "groundingConfig": {
                    "webSearchEnabled": random.choice([True, False])
                }
            },
            "servicetextreply": reply,
            "response": {
                "attributiontoken": f"token-{random.randint(100000, 999999)}",
                "answer": {
                    "name": f"projects/850431687571/locations/global/collections/default_collection/engines/gemini-enterprise-gm_1771086459519/sessions/{session_id}/assistAnswers/answer-{i}"
                }
            }
        }
        
        row = {
            "timestamp": ts,
            "jsonPayload": payload,
            "insertId": f"mock-chat-{i}-{ts.timestamp()}"
        }
        chat_rows.append(row)
        
    assist_table = f"{PROJECT_ID}.{GE_PREFIX}assist.discoveryengine_googleapis_com_gemini_enterprise_user_activity"
    stream_table = f"{PROJECT_ID}.{GE_PREFIX}streamassist.discoveryengine_googleapis_com_gemini_enterprise_user_activity"
    insert_rows_dml(assist_table, chat_rows[:15])
    insert_rows_dml(stream_table, chat_rows[15:])

    # 2. File Attachments
    file_rows = []
    for i in range(5):
        ts = get_random_timestamp()
        user = random.choice(USERS)
        agent = random.choice(AGENTS)
        
        payload = {
            "logmetadata": {
                "servicelabel": "GEMINI_ENTERPRISE",
                "methodname": "UploadSessionFile",
                "servicename": "projects/850431687571/locations/global/collections/default_collection/engines/gemini-enterprise-gm_1771086459519",
                "is_mock": "true"
            },
            "useriamprincipal": user,
            "request": {
                "name": f"projects/850431687571/locations/global/collections/default_collection/engines/{agent}",
                "fileName": f"document_v{i}.pdf",
                "sizeBytes": random.randint(50000, 5000000)
            }
        }
        
        row = {
            "timestamp": ts,
            "jsonPayload": payload,
            "insertId": f"mock-file-{i}-{ts.timestamp()}"
        }
        file_rows.append(row)
        
    upload_table = f"{PROJECT_ID}.{GE_PREFIX}uploadsessionfile.discoveryengine_googleapis_com_gemini_enterprise_user_activity"
    insert_rows_dml(upload_table, file_rows)

    # 3. Agent Creation (CreateAgent lifecycle)
    create_rows = []
    for i, agent in enumerate(AGENTS):
        ts = get_random_timestamp()
        user = random.choice(USERS)
        
        payload = {
            "logmetadata": {
                "servicelabel": "GEMINI_ENTERPRISE",
                "methodname": "CreateAgent",
                "servicename": "projects/850431687571/locations/global/collections/default_collection/engines/gemini-enterprise-gm_1771086459519",
                "is_mock": "true"
            },
            "useriamprincipal": user,
            "request": {
                "name": f"projects/850431687571/locations/global/collections/default_collection/engines/{agent}",
                "agent": {
                    "displayName": agent.replace("-", " ").title()
                }
            }
        }
        
        row = {
            "timestamp": ts,
            "jsonPayload": payload,
            "insertId": f"mock-create-{i}-{ts.timestamp()}"
        }
        create_rows.append(row)
        
    create_table = f"{PROJECT_ID}.{GE_PREFIX}createagent.discoveryengine_googleapis_com_gemini_enterprise_user_activity"
    insert_rows_dml(create_table, create_rows)

    # 4. User Feedback
    feedback_rows = []
    for i in range(10):
        ts = get_random_timestamp()
        user = random.choice(USERS)
        agent = random.choice(AGENTS)
        session_id = f"session-{random.randint(1000, 9999)}"
        is_like = random.choice([True, False])
        feedback_type = "LIKE" if is_like else "DISLIKE"
        comment = "" if is_like else random.choice(FEEDBACK_COMMENTS)
        
        payload = {
            "logmetadata": {
                "servicelabel": "GEMINI_ENTERPRISE",
                "methodname": "WriteUserEvent",
                "servicename": "projects/850431687571/locations/global/collections/default_collection/engines/gemini-enterprise-gm_1771086459519",
                "is_mock": "true"
            },
            "useriamprincipal": user,
            "request": {
                "name": f"projects/850431687571/locations/global/collections/default_collection/engines/{agent}",
                "userEvent": {
                    "eventType": "add-feedback",
                    "feedback": {
                        "feedbackType": feedback_type,
                        "comment": comment,
                        "conversationInfo": {
                            "session": f"collections/default_collection/engines/gemini-enterprise-gm_1771086459519/sessions/{session_id}"
                        }
                    }
                }
            }
        }
        
        row = {
            "timestamp": ts,
            "jsonPayload": payload,
            "insertId": f"mock-fb-{i}-{ts.timestamp()}"
        }
        feedback_rows.append(row)
        
    write_table = f"{PROJECT_ID}.{GE_PREFIX}writeuserevent.discoveryengine_googleapis_com_gemini_enterprise_user_activity"
    insert_rows_dml(write_table, feedback_rows)

    print("\n✨ KPI-aligned test data including today (May 3) successfully generated!")

if __name__ == "__main__":
    main()
