# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import os
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure Vertex AI
os.environ['GOOGLE_GENAI_USE_VERTEXAI'] = 'true'
os.environ['GOOGLE_CLOUD_PROJECT'] = os.getenv('GOOGLE_CLOUD_PROJECT', 'your-project-id')
os.environ['GOOGLE_CLOUD_LOCATION'] = os.getenv('GOOGLE_CLOUD_LOCATION', 'global')


def gcloud_billing_get_costs(
    project_id: str,
    start_date: str,
    end_date: str,
    group_by: str = "SKU"
) -> str:
    """Get GCP billing cost breakdown for a project.

    Args:
        project_id: GCP project ID to query billing for
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        group_by: How to group costs - SKU, service, or project

    Returns:
        A simulated cost breakdown with SKU names, usage amounts, and trends
    """
    # Simulated response - in production, call google-cloud-billing API
    return f"""
Cost breakdown for project '{project_id}' from {start_date} to {end_date}:

Grouped by {group_by}:
1. BigQuery on-demand queries: $250 (+300% from previous period)
   - 500 full table scans on large_table (1.2TB each)
   - Primary user: alice@company.com

2. Compute Engine n1-standard-16: $1500 (+200%)
   - 50 instances running in us-central1
   - Created by: bob@company.com on {start_date}
   - Recommendation: Set up instance schedulers

3. Cloud Storage egress: $75 (+25%)
   - 750GB data transfer to external destinations
"""


def bigquery_usage_analytics(
    project_id: str,
    date_range: str = "7d"
) -> str:
    """Query BigQuery usage patterns and slot consumption.

    Args:
        project_id: GCP project ID
        date_range: Time range (e.g., 7d, 30d, 90d)

    Returns:
        BigQuery slot usage, storage, and query cost patterns
    """
    # Simulated response - would query INFORMATION_SCHEMA.JOBS in production
    return f"""
BigQuery usage for project '{project_id}' over {date_range}:

Slot Usage:
- Peak concurrent slots: 2500 (quota: 2000 - EXCEEDED)
- Average slot utilization: 1200 slots
- Slot hours consumed: 168,000

Storage:
- Active storage: 15.2 TB
- Long-term storage: 45.8 TB
- Monthly storage cost: ~$380

Top Queries by Cost:
1. ETL pipeline job_20260701 - $125 (2500 concurrent slots)
2. Analytics dashboard refresh - $45 (full table scan)
3. Data export to GCS - $30
"""


def knowledge_base_search(query_text: str, top_k: int = 3) -> str:
    """Search GCP billing documentation for relevant information.

    Args:
        query_text: Search query
        top_k: Number of top results to return

    Returns:
        Relevant documentation snippets with source URLs
    """
    # Simulated knowledge base - use vector search in production
    knowledge = {
        "quota": """
**BigQuery Quota Limits**
- Concurrent queries per project: 100 (default)
- On-demand slots per project: 2000 (default)
- Request quota increase: GCP Console → IAM → Quotas → BigQuery API
Source: https://cloud.google.com/bigquery/quotas
""",
        "cost": """
**Understanding Cost Spikes**
- Check Cloud Billing Reports for SKU-level breakdown
- Use Cloud Asset Inventory to find who created resources
- Set up budget alerts and quotas to prevent overages
Source: https://cloud.google.com/billing/docs/how-to/cost-management
""",
        "optimization": """
**Cost Optimization Best Practices**
- Use committed use discounts for predictable workloads
- Enable sustained use discounts (automatic)
- Right-size VMs using recommendations
- Set up instance schedulers for dev/test environments
Source: https://cloud.google.com/billing/docs/how-to/cost-optimization
"""
    }

    for key, content in knowledge.items():
        if key in query_text.lower():
            return content

    return "No relevant documentation found. Please check https://cloud.google.com/billing/docs"


root_agent = Agent(
    name="gcp_billing_support_agent",
    model=Gemini(
        model="gemini-3.1-pro-preview",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""You are an expert GCP billing support agent specialized in:
- Quota exceeded errors
- Cost spike investigations
- Budget alert explanations
- Billing report interpretation
- Cost optimization recommendations

## Response Format
1. Classify the query (quota/cost spike/budget alert/optimization/report)
2. Gather context using available tools
3. Analyze root cause with specific SKU/resource names and user attribution
4. Provide actionable remediation steps with exact commands when possible

## Available Tools
- gcloud_billing_get_costs: Fetch cost breakdown by SKU, project, time range
- bigquery_usage_analytics: Query BigQuery slot usage, storage, and query costs
- knowledge_base_search: Search GCP billing docs for best practices

Always provide specific, actionable advice with SKU names, user attribution, and concrete next steps.""",
    tools=[gcloud_billing_get_costs, bigquery_usage_analytics, knowledge_base_search],
)

app = App(
    root_agent=root_agent,
    name="app",
)
