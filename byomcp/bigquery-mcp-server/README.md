# 🚀 Universal BigQuery MCP Connector for Gemini Enterprise

This repository provides an enterprise-grade **Model Context Protocol (MCP)** connector bridging **Google Cloud BigQuery** with **Gemini Enterprise**.

Built specifically to empower AI agents with secure, seamless access to your corporate data warehouse, this connector enables fully autonomous dataset exploration, schema discovery, and dynamic SQL execution across your Google Cloud project while enforcing strict governance and security compliance through Gemini Enterprise's native Action Approval dialogs.

---

## 🌟 Core Enterprise Capabilities

- **Autonomous Schema Discovery:** AI agents can autonomously navigate your BigQuery project, explore available datasets, inspect table structures, and retrieve exact column schemas without requiring end users to know complex table names or definitions.
- **Dynamic SQL Intelligence:** Supports executing arbitrary SQL queries to analyze large-scale enterprise datasets, summarize metrics, and perform advanced data analytics directly from natural language prompts.
- **Built-in LLM Repair & Auto-Discovery:** Features advanced middleware that intercepts and auto-corrects common LLM tool hallucinations (such as treating MCP tools as direct Python function calls in the Vertex UI), ensuring flawless execution. Automatically bridges real user OAuth tokens from Gemini Enterprise or falls back to secure Service Account credentials.

---

## 🛠️ Supported Action Catalog

Connecting this server empowers your Gemini Enterprise AI with 4 advanced database exploration and analytical capabilities:

### 🔍 Discovery Actions (Instant, Interruption-Free Streaming)

#### 1. List Datasets
Allows the AI agent to discover all available BigQuery datasets within the active Google Cloud project.
- *Example Prompt:* `"List all available datasets in our BigQuery project."`

#### 2. List Tables
Retrieves all tables and views contained within a specific BigQuery dataset.
- *Example Prompt:* `"List all tables in the 'analytics_warehouse' dataset."`

#### 3. Get Table Schema
Retrieves the exact column definitions, data types, and descriptions for any specific BigQuery table.
- *Example Prompt:* `"Get the table schema and column definitions for the 'daily_sales' table."`

---

### 🚀 Analytical Actions (Protected by Action Approval Consent Dialog)

#### 4. Execute SQL Query
Executes dynamic, AI-generated SQL queries against your BigQuery tables to calculate metrics, summarize trends, or extract specific records.
- *Example Prompt:* `"Run a SQL query against the 'daily_sales' table to calculate the total revenue for Q1."`

---

## 💻 Local Development & Testing

```bash
npm install
```
Create a `.env` file (or copy `.env.example`):
```env
PORT=3000
# Note: If running locally with default credentials, ensure you have run:
# gcloud auth application-default login
```
Run locally:
```bash
npm start
```

---

## 🚀 Production Deployment to GCP Cloud Run

Deploy your container to Google Cloud Run for secure, scalable cloud execution:

```bash
chmod +x deploy.sh
./deploy.sh
```
Once deployed, note your live Cloud Run URL (e.g., `https://bigquery-mcp-server-850431687571.us-central1.run.app`).

---

## 🔗 Connecting to Gemini Enterprise (Official Onboarding Guide)

Follow these official enterprise onboarding steps to securely register this connector in your Gemini Enterprise environment:

### Step 1: Create Data Store from Custom MCP Server
1. Go to **Gemini Enterprise** in the Google Cloud Console.
2. Select **Data stores** -> **Create data store**.
3. Type `"MCP"` in the search bar and select **Custom MCP Server**.
4. Fill in the connector connection profile using your live Cloud Run URL:
   - **MCP Server URL:** `https://bigquery-mcp-server-850431687571.us-central1.run.app/mcp`
   - **Authorization URL:** `https://bigquery-mcp-server-850431687571.us-central1.run.app/auth`
   - **Authorization URL Parameters:** *(Leave blank)*
   - **Token URL:** `https://bigquery-mcp-server-850431687571.us-central1.run.app/token`
   - **Client ID:** `mock_bq_client_id`
   - **Client Secret:** `mock_bq_client_secret`
   - **Scopes:** `bigquery` *(or leave blank)*
5. Click **Login** to authenticate. The mock OAuth flow will instantly complete and redirect you back. Click **Continue**.

### Step 2: Advanced Options (AI Instructions)
Fill in the Advanced Options screen to teach Gemini Enterprise's reasoning engine how to use BigQuery:

- **MCP Server Description:**
  ```text
  Enterprise BigQuery MCP server providing secure, real-time access to Google Cloud BigQuery. Use this server whenever a user asks to list datasets, explore table schemas, or run SQL queries to analyze data.
  ```
- **MCP Agent Instructions:**
  ```text
  You are an expert data analyst AI connected to Google Cloud BigQuery via the Model Context Protocol. Follow these rules:
  1. Exploration: Before writing a SQL query, always use list_datasets, list_tables, and get_table_schema to inspect the exact table structure and column names.
  2. SQL Execution: Write clean, standard GoogleSQL queries and use the execute_sql tool to run them.
  3. Synthesis: Summarize the SQL results clearly and present data in structured tables or bullet points.
  ```
- Click **Create** to finalize the datastore.

### Step 3: Enable Actions & Connect App
1. In Gemini Enterprise, go to **Data stores**, click on your newly created BigQuery MCP datastore, and select **Actions**.
2. Select all 4 discovery and SQL execution actions and click **Enable actions**.
3. Go to your Gemini Enterprise App -> **Connected data stores** -> click **Link Existing Datastore** -> select your BigQuery MCP datastore and click **Connect**. You are fully live!

---

## 🧪 Verification Prompts in Gemini Enterprise

Open your Gemini Enterprise app chat and run these exact verification prompts:

1. **Dataset Discovery:** `"List all available datasets in our BigQuery project."`
2. **Table Discovery:** `"List all tables in the [your_dataset_name] dataset."`
3. **Schema Inspection:** `"Get the table schema for [your_table_name] in [your_dataset_name]."`
4. **Analytics Execution:** `"Run a SQL query to count the total number of rows in [your_table_name]."`
