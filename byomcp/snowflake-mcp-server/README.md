# Snowflake Managed MCP Server Setup

This guide walks through setting up a Snowflake Managed MCP Server and connecting it to a Gemini Enterprise (GE) app using OAuth authentication.

## **Architecture**

```
GCP Agent (Gemini) → OAuth → Snowflake MCP Server → SQL Execution → Your Data
```

---

## **Part 1: Snowflake Setup**

Run the following SQL commands in your Snowflake worksheet as `ACCOUNTADMIN` (or appropriate roles as specified).

### **Step 1: Create a Dedicated Role and Grants**
This creates a role `MCP_ROLE` with limited access to your database and warehouse.
Replace `<your_snowflake_user>` with your actual Snowflake username.

```sql
USE ROLE ACCOUNTADMIN;

-- Create Role
CREATE ROLE IF NOT EXISTS MCP_ROLE;

-- Database & Schema Access
-- (Ensure your database and schema exist, e.g., DASH_MCP_DB.DATA)
GRANT USAGE ON DATABASE DASH_MCP_DB TO ROLE MCP_ROLE;
GRANT USAGE ON SCHEMA DASH_MCP_DB.DATA TO ROLE MCP_ROLE;

-- Table access (Grant select on tables you want to expose)
GRANT SELECT ON TABLE DASH_MCP_DB.DATA.FACT_RISK_ASSESSMENTS TO ROLE MCP_ROLE;
GRANT SELECT ON TABLE DASH_MCP_DB.DATA.DIM_CUSTOMERS TO ROLE MCP_ROLE;

-- Warehouse access
GRANT USAGE ON WAREHOUSE DASH_WH_S TO ROLE MCP_ROLE;
GRANT OPERATE ON WAREHOUSE DASH_WH_S TO ROLE MCP_ROLE;

-- Assign to your user
GRANT ROLE MCP_ROLE TO USER <your_snowflake_user>;
GRANT ROLE MCP_ROLE TO ROLE SYSADMIN;
```

### **Step 2: Create OAuth Security Integration**
This allows GCP to authenticate with Snowflake.

```sql
USE ROLE ACCOUNTADMIN;

CREATE OR REPLACE SECURITY INTEGRATION MY_OAUTH_INT
  TYPE = OAUTH
  ENABLED = TRUE
  OAUTH_CLIENT = CUSTOM
  OAUTH_CLIENT_TYPE = 'CONFIDENTIAL'
  OAUTH_REDIRECT_URI = 'https://vertexaisearch.cloud.google.com/oauth-redirect'
  OAUTH_ISSUE_REFRESH_TOKENS = TRUE
  OAUTH_REFRESH_TOKEN_VALIDITY = 7776000
  OAUTH_USE_SECONDARY_ROLES = IMPLICIT
  COMMENT = 'OAuth integration for GCP MCP access';

-- Retrieve Client ID and Secret (CRITICAL: Save these for GCP setup)
SELECT SYSTEM$SHOW_OAUTH_CLIENT_SECRETS('MY_OAUTH_INT');
DESCRIBE SECURITY INTEGRATION MY_OAUTH_INT;
```
*Save the `OAUTH_CLIENT_ID` and the client secret returned by the query.*

### **Step 3: Create Semantic View (Optional)**
A semantic view defines your data model so Cortex Analyst can translate natural language into SQL.
Example:
```sql
USE ROLE ACCOUNTADMIN;

CREATE OR REPLACE SEMANTIC VIEW DASH_MCP_DB.DATA.RISK_ASSESSMENT_SV
  TABLES (
    customers AS DASH_MCP_DB.DATA.DIM_CUSTOMERS
      PRIMARY KEY (CUSTOMER_ID)
      COMMENT = 'Customer dimension table',
    risk_assessments AS DASH_MCP_DB.DATA.FACT_RISK_ASSESSMENTS
      PRIMARY KEY (ASSESSMENT_ID)
      COMMENT = 'Risk assessment fact table'
  )
  RELATIONSHIPS (
    risk_to_customer AS
      risk_assessments (CUSTOMER_ID) REFERENCES customers
  )
  FACTS (
    risk_assessments.risk_score AS RISK_SCORE
  )
  DIMENSIONS (
    customers.first_name AS FIRST_NAME,
    customers.last_name AS LAST_NAME,
    customers.email AS EMAIL,
    customers.segment AS CUSTOMER_SEGMENT,
    risk_assessments.risk_category AS RISK_CATEGORY,
    risk_assessments.assessment_date AS ASSESSMENT_DATE
  )
  METRICS (
    customers.customer_count AS COUNT(CUSTOMER_ID)
  )
  COMMENT = 'Semantic view for customer risk assessment analysis';
```

### **Step 4: Create the MCP Server**
Define the tools exposed by the MCP server.

```sql
USE ROLE ACCOUNTADMIN;

CREATE OR REPLACE MCP SERVER DASH_MCP_DB.DATA.DASH_MCP_SERVER
FROM SPECIFICATION $$
tools:
  - name: "risk_assessment_analyst"
    type: "CORTEX_ANALYST_MESSAGE"
    title: "Risk Assessment Analyst"
    description: "Translates natural language questions about customer risk assessments into SQL. Returns SQL."
    config:
      semantic_view: DASH_MCP_DB.DATA.RISK_ASSESSMENT_SV
  - name: "SQL_Execution_Tool"
    type: "SYSTEM_EXECUTE_SQL"
    title: "SQL Execution Tool"
    description: "Executes SQL queries against Snowflake."
    config:
      warehouse: DASH_WH_S
      read_only: false
      query_timeout: 300
$$;
```

### **Step 5: Grant Access and Configure Network Policy**
Grant `MODIFY` privilege to the role.

```sql
GRANT USAGE ON MCP SERVER DASH_MCP_DB.DATA.DASH_MCP_SERVER TO ROLE MCP_ROLE;
GRANT MODIFY ON MCP SERVER DASH_MCP_DB.DATA.DASH_MCP_SERVER TO ROLE MCP_ROLE;
```

Configure Network Policy to allow GCP IPs (adjust allowed IPs as needed):
```sql
CREATE OR REPLACE NETWORK POLICY MCP_NETWORK_POLICY
  ALLOWED_IP_LIST = (
    '35.190.0.0/16',       -- GCP us-central1 range
    '172.253.0.0/16',      -- Google API infrastructure
    '<your_local_ip>/32'   -- Your own IP for Snowsight access
  )
  COMMENT = 'Network policy for MCP access from GCP';

ALTER USER <your_snowflake_user> SET NETWORK_POLICY = MCP_NETWORK_POLICY;
```

---

## **Part 2: GCP Configuration**

In your GCP Agent configuration (Vertex AI Agent Builder), use these connection parameters:

| Parameter | Value |
| ----- | ----- |
| **MCP Server URL** | `https://<your-account>.snowflakecomputing.com/api/v2/databases/DASH_MCP_DB/schemas/DATA/mcp-servers/DASH_MCP_SERVER/sse` |
| **Authorization URL** | `https://<your-account>.snowflakecomputing.com/oauth/authorize` |
| **Token URL** | `https://<your-account>.snowflakecomputing.com/oauth/token-request` |
| **Client ID** | *[From Step 2]* |
| **Client Secret** | *[From Step 2]* |
| **Scope** | `session:role:MCP_ROLE` |

> [!IMPORTANT]
> The MCP Server URL must end with `/sse`.

### **GCP Allowlist (Google Internal)**
If you are using this within Google-internal projects, you must allowlist your Snowflake instance in:
`google3/cloud/ml/discoveryengine/common/allowlist/google_internal/data_source_allowlist_config.textproto`

Example entry:
```textproto
# Project: your-project-name (Number: <project_number>)
project_allowlist {
  key: <project_number>
  value {
    is_allow1p_connector: true
    permitted3p_uris: "https://<your-account>.snowflakecomputing.com"
  }
}
```
