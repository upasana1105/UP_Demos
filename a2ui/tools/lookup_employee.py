"""Tool: lookup_employee - Fetches employee records from BigQuery."""

import json
import logging
import os

from google.cloud import bigquery

logger = logging.getLogger(__name__)

PROJECT_ID = os.environ.get("PROJECT_ID", "kpmg-452019")
DATASET_ID = "employee_verification"
TABLE_ID = "employee_records"
FULL_TABLE = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"


def lookup_employee(
    name: str = None,
    employee_id: str = None,
    department: str = None,
) -> str:
    """Look up employee records from the employee database.

    Use this tool when the user wants to find, search, view, or verify employee
    information. Returns employee details including name, employee_id, title,
    department, address, phone, email, emergency contact, employment status,
    hire date, and verification status.

    You can search by name (partial match), exact employee_id, or department.
    If no parameters are provided, returns all employees.

    Args:
        name: Employee name to search for (partial match supported).
        employee_id: Exact employee ID to look up (e.g., 'E-1001').
        department: Filter by department name (partial match supported).
    """
    logger.info("--- TOOL CALLED: lookup_employee ---")
    logger.info(f"  - name: {name}, employee_id: {employee_id}, department: {department}")

    try:
        client = bigquery.Client(project=PROJECT_ID)

        conditions = []
        params = []

        if employee_id:
            conditions.append("employee_id = @employee_id")
            params.append(bigquery.ScalarQueryParameter("employee_id", "STRING", employee_id))

        if name:
            conditions.append("LOWER(name) LIKE CONCAT('%', LOWER(@name), '%')")
            params.append(bigquery.ScalarQueryParameter("name", "STRING", name))

        if department:
            conditions.append("LOWER(department) LIKE CONCAT('%', LOWER(@department), '%')")
            params.append(bigquery.ScalarQueryParameter("department", "STRING", department))

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"SELECT * FROM `{FULL_TABLE}` {where_clause} LIMIT 50"

        job_config = bigquery.QueryJobConfig(query_parameters=params) if params else None
        results = client.query(query, job_config=job_config).result()

        employees = []
        for row in results:
            emp = dict(row)
            # Convert date/datetime objects to strings for JSON serialization
            for key, value in emp.items():
                if hasattr(value, "isoformat"):
                    emp[key] = value.isoformat()
                elif isinstance(value, bool):
                    emp[key] = value
            employees.append(emp)

        logger.info(f"  - Found {len(employees)} matching employees.")
        return json.dumps(employees)

    except Exception as e:
        logger.error(f"  - Error querying BigQuery: {e}", exc_info=True)
        return json.dumps({"error": str(e)})
