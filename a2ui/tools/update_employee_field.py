"""Tool: update_employee_field - Updates an allowed field in an employee's BigQuery record."""

import json
import logging
import os

from google.cloud import bigquery

logger = logging.getLogger(__name__)

PROJECT_ID = os.environ.get("PROJECT_ID", "kpmg-452019")
DATASET_ID = "employee_verification"
TABLE_ID = "employee_records"
FULL_TABLE = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

# Fields the employee is allowed to update
EDITABLE_FIELDS = {
    "address",
    "phone",
    "email",
    "emergency_contact",
    "emergency_phone",
}

# Fields that are protected and cannot be updated
PROTECTED_FIELDS = {
    "employee_id",
    "name",
    "title",
    "department",
    "hire_date",
    "termination_date",
    "employment_status",
    "manager",
    "salary_band",
    "verified",
    "verified_date",
}


def update_employee_field(
    employee_id: str,
    field_name: str,
    new_value: str,
) -> str:
    """Update a specific field in an employee's record in the employee database.

    Use this tool when the user wants to update or change their employee
    information. Only certain fields can be updated by the employee:
    address, phone, email, emergency_contact, and emergency_phone.

    Fields like name, employee_id, title, department, hire_date, salary_band,
    and employment_status are PROTECTED and cannot be updated through this tool.
    If the user tries to update a protected field, this tool will return an error.

    After updating, the verified status is reset to false so the record needs
    re-verification.

    Args:
        employee_id: The employee's unique identifier (e.g., 'E-1001').
        field_name: The name of the field to update. Must be one of:
                    address, phone, email, emergency_contact, emergency_phone.
        new_value: The new value to set for the field.
    """
    logger.info("--- TOOL CALLED: update_employee_field ---")
    logger.info(f"  - employee_id: {employee_id}, field: {field_name}, new_value: {new_value}")

    # Validate field name
    field_name_lower = field_name.lower().strip()

    if field_name_lower in PROTECTED_FIELDS:
        msg = (
            f"Field '{field_name}' is protected and cannot be updated by the employee. "
            f"Protected fields include: {', '.join(sorted(PROTECTED_FIELDS))}. "
            f"Please contact HR to update this field."
        )
        logger.warning(f"  - Rejected: {msg}")
        return json.dumps({"success": False, "error": msg})

    if field_name_lower not in EDITABLE_FIELDS:
        msg = (
            f"Field '{field_name}' is not a recognized editable field. "
            f"Editable fields are: {', '.join(sorted(EDITABLE_FIELDS))}."
        )
        logger.warning(f"  - Rejected: {msg}")
        return json.dumps({"success": False, "error": msg})

    try:
        client = bigquery.Client(project=PROJECT_ID)

        # Update the field and reset verification status
        query = f"""
            UPDATE `{FULL_TABLE}`
            SET {field_name_lower} = @new_value,
                verified = FALSE,
                verified_date = NULL
            WHERE employee_id = @employee_id
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("new_value", "STRING", new_value),
                bigquery.ScalarQueryParameter("employee_id", "STRING", employee_id),
            ]
        )

        result = client.query(query, job_config=job_config).result()
        rows_affected = result.num_dml_affected_rows

        if rows_affected == 0:
            msg = f"No employee found with ID '{employee_id}'."
            logger.warning(f"  - {msg}")
            return json.dumps({"success": False, "error": msg})

        logger.info(f"  - Success: Updated {field_name_lower} for {employee_id}")
        return json.dumps({
            "success": True,
            "message": f"Successfully updated {field_name} to '{new_value}' for employee {employee_id}.",
            "employee_id": employee_id,
            "field_updated": field_name_lower,
            "new_value": new_value,
            "note": "Verification status has been reset. Please verify the record again.",
        })

    except Exception as e:
        logger.error(f"  - Error updating BigQuery: {e}", exc_info=True)
        return json.dumps({"success": False, "error": str(e)})
