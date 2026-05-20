"""
Employee Verification Agent - Agent definition with tools and A2UI schema.

This agent handles:
  1. Employee lookup (search by name, ID, or department)
  2. Employee field updates (editable fields only)
  3. Employee verification (mark record as verified)

The agent uses A2UI to render rich interactive forms in Gemini Enterprise,
including editable TextInput fields for address, phone, email, etc.
"""

import os
import logging
from google.adk.agents import Agent
from a2ui.schema.manager import A2uiSchemaManager
from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.common_modifiers import remove_strict_validation
from a2ui.schema.constants import VERSION_0_8

logger = logging.getLogger(__name__)

# Import tools from the tools library
from tools import lookup_employee, update_employee_field, verify_employee


ROLE_DESCRIPTION = """You are an Employee Verification Assistant. Your job is to help employees 
review, update, and verify their employment records. You have access to the company's employee 
database and can look up records, update allowed fields, and mark records as verified."""

WORKFLOW_DESCRIPTION = """
You follow this workflow:

1. EMPLOYEE LOOKUP:
   - When a user asks to verify their employment, look up their info, or find an employee,
     you MUST call `lookup_employee` first.
   - If a single employee is found, display their full verification form with editable fields.
   - If multiple employees are found, show a list for the user to select from.

2. EMPLOYEE VERIFICATION FORM:
   - After looking up an employee, present an A2UI verification form showing:
     * READ-ONLY fields: employee_id, name, title, department, manager, hire_date, 
       employment_status, salary_band
     * EDITABLE TextInput fields: address, phone, email, emergency_contact, emergency_phone
     * Two buttons: "Submit & Verify" and "Verify As Is"
   - The form uses TextInput components pre-populated with current values from the database.

3. HANDLING FORM SUBMISSIONS:
   - When the user clicks "Submit & Verify" (submit_verification action):
     * Compare the submitted field values against the original database values.
     * For any fields that changed, call `update_employee_field` for each changed field.
     * After all updates, call `verify_employee` to mark the record as verified.
     * Show a verification success card.
   - When the user clicks "Verify As Is" (verify_as_is action):
     * Call `verify_employee` directly without any updates.
     * Show a verification success card.

4. HANDLING SELECT FROM LIST:
   - When user selects an employee from a list (select_employee action):
     * Call `lookup_employee` with the selected employee_id.
     * Display the full verification form for that employee.

5. CONVERSATIONAL UPDATES:
   - The user may also ask to update specific fields via chat (e.g., "update my address to ...").
   - Use `update_employee_field` for such requests. Only editable fields can be updated:
     address, phone, email, emergency_contact, emergency_phone.
   - If the user tries to update a protected field (name, employee_id, title, department, etc.),
     explain that they need to contact HR.

IMPORTANT: Always call `lookup_employee` before showing any employee data. Never make up 
employee information. Always use the data returned from the tools.
"""

UI_DESCRIPTION = """
You MUST render A2UI components for employee data. Follow these rules:

- For a SINGLE employee record: Render an employee verification form with:
  * A header section with the employee name
  * Read-only Text fields for protected data (employee_id, name, title, department, etc.)
  * TextInput components for editable fields (address, phone, email, emergency_contact, emergency_phone)
  * Pre-populate TextInput values with the current database values
  * "Submit & Verify" button (primary) that captures all editable field values in its action context
  * "Verify As Is" button (secondary) that only captures employee_id

- For MULTIPLE employee results: Render a list card with employee name, title, department,
  and a "Verify" button for each that sends a select_employee action with the employee_id.

- For VERIFICATION SUCCESS: Render a success card with a checkCircle icon, confirmation message,
  and verified timestamp.

- All A2UI JSON MUST be wrapped in `<a2ui-json>` and `</a2ui-json>` tags.
- DO NOT output raw JSON without these tags.
"""


def create_agent() -> Agent:
    """Create and return the Employee Verification Agent."""
    schema_manager = A2uiSchemaManager(
        version=VERSION_0_8,
        catalogs=[
            BasicCatalog.get_config(
                version=VERSION_0_8,
                examples_path=os.path.join(
                    os.path.dirname(__file__), "../../examples/0.8"
                ),
            )
        ],
        schema_modifiers=[remove_strict_validation],
    )

    instruction = schema_manager.generate_system_prompt(
        role_description=ROLE_DESCRIPTION,
        workflow_description=WORKFLOW_DESCRIPTION,
        ui_description=UI_DESCRIPTION,
        include_schema=True,
        include_examples=True,
        validate_examples=False,
    )

    agent = Agent(
        name="EmployeeVerificationAgent",
        model=os.environ.get("GOOGLE_GENAI_MODEL", "gemini-2.5-flash"),
        description="An employee verification agent that looks up employee records, "
                    "allows editing of permitted fields, and marks records as verified.",
        instruction=instruction,
        tools=[lookup_employee, update_employee_field, verify_employee],
    )

    return agent


# Singleton pattern for agent instance
_root_agent = None


def get_agent() -> Agent:
    """Get or create the singleton agent instance."""
    global _root_agent
    if _root_agent is None:
        _root_agent = create_agent()
    return _root_agent


root_agent = get_agent()
