"""Tool: verify_employee - Marks an employee record as verified in BigQuery."""

import json
import logging
import os
from datetime import datetime, timezone

from google.cloud import bigquery

logger = logging.getLogger(__name__)

PROJECT_ID = os.environ.get("PROJECT_ID", "kpmg-452019")
DATASET_ID = "employee_verification"
TABLE_ID = "employee_records"
FULL_TABLE = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"


def verify_employee(employee_id: str) -> str:
    """Mark an employee's record as verified in the employee database.

    Use this tool when the user confirms that their employee information is
    correct (with or without updates) and wants to mark the record as verified.
    This sets the verified flag to true and records the current timestamp as
    the verification date.

    Call this tool after the employee has reviewed their information and either:
    - Confirmed it is correct as-is, OR
    - Updated any fields and is now ready to finalize

    Args:
        employee_id: The employee's unique identifier (e.g., 'E-1001').
    """
    logger.info("--- TOOL CALLED: verify_employee ---")
    logger.info(f"  - employee_id: {employee_id}")

    try:
        client = bigquery.Client(project=PROJECT_ID)

        now = datetime.now(timezone.utc).isoformat()

        query = f"""
            UPDATE `{FULL_TABLE}`
            SET verified = TRUE,
                verified_date = @verified_date
            WHERE employee_id = @employee_id
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("verified_date", "TIMESTAMP", now),
                bigquery.ScalarQueryParameter("employee_id", "STRING", employee_id),
            ]
        )

        result = client.query(query, job_config=job_config).result()
        rows_affected = result.num_dml_affected_rows

        if rows_affected == 0:
            msg = f"No employee found with ID '{employee_id}'."
            logger.warning(f"  - {msg}")
            return json.dumps({"success": False, "error": msg})

        logger.info(f"  - Success: Verified employee {employee_id}")
        return json.dumps({
            "success": True,
            "message": f"Employee {employee_id} has been successfully verified.",
            "employee_id": employee_id,
            "verified": True,
            "verified_date": now,
        })

    except Exception as e:
        logger.error(f"  - Error updating BigQuery: {e}", exc_info=True)
        return json.dumps({"success": False, "error": str(e)})
