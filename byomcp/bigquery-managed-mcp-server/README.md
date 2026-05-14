# 🚀 Google-Managed BigQuery MCP Connector for Gemini Enterprise

This repository provides the official enterprise onboarding and configuration guide (modeled after Sannya Dang's official Google-managed MCP standards) for connecting the **Google-Managed BigQuery Native MCP Server** directly to **Gemini Enterprise**.

Unlike custom Cloud Run proxy deployments, this managed connector is fully native to Google Cloud. It leverages Google's official OAuth 2.0 endpoints and your Google Cloud Project's native IAM permissions to provide AI agents with secure, zero-infrastructure access to your BigQuery data warehouse.

---

## 🌟 Core Enterprise Capabilities

- **Zero-Infrastructure Execution:** No Cloud Run containers, Dockerfiles, or proxy middleware required. Gemini Enterprise connects directly to Google's managed BigQuery MCP infrastructure out of the box.
- **Enterprise IAM & Security Governance:** Uses Google's official OAuth 2.0 authorization code flow. Every BigQuery query executed by the AI agent is strictly scoped to the authenticated end-user's IAM permissions (`roles/bigquery.dataViewer`, `roles/bigquery.jobUser`), ensuring absolute data governance.
- **Autonomous Schema Discovery & SQL Intelligence:** AI agents can autonomously explore available datasets, inspect table schemas, and execute dynamic GoogleSQL queries to summarize enterprise metrics in real time.

---

## 🛠️ Supported Action Catalog

Connecting this managed server empowers your Gemini Enterprise AI with 4 core database exploration and analytical capabilities:

### 🔍 Discovery Actions (Instant, Interruption-Free Streaming)

#### 1. List Datasets
Allows the AI agent to discover all available BigQuery datasets within the active Google Cloud project.
- *Example Prompt:* `"List all available datasets in our BigQuery project."`

#### 2. List Tables
Retrieves all tables and views contained within a specific BigQuery dataset.
- *Example Prompt:* `"List all tables in the 'enterprise_analytics' dataset."`

#### 3. Get Table Schema
Retrieves the exact column definitions, data types, and descriptions for any specific BigQuery table.
- *Example Prompt:* `"Get the table schema and column definitions for the 'q1_financials' table."`

---

### 🚀 Analytical Actions (Protected by Action Approval Consent Dialog)

#### 4. Execute SQL Query
Executes dynamic, AI-generated GoogleSQL queries against your BigQuery tables to calculate metrics, summarize trends, or extract specific records.
- *Example Prompt:* `"Run a SQL query against the 'q1_financials' table to calculate the total revenue by department."`

---

## 📋 Prerequisites: Google Cloud OAuth Client Setup

Before configuring Gemini Enterprise, create an official Google Cloud OAuth Web Client ID:

1. In the Google Cloud Console, go to **APIs & Services** -> **Credentials**.
2. Click **Create credentials** -> **OAuth Client ID**.
3. **Application Type:** `Web Application`.
4. **Name:** `Gemini Enterprise Managed BigQuery MCP`.
5. **Authorized redirect URIs:** Add the exact redirect URI provided by Gemini Enterprise (typically `https://vertexaisearch.cloud.google.com/oauth-redirect`).
   *(⚠️ Important: Make sure there are no trailing slashes `/` at the end or blank spaces).*
6. Click **Create**. Save your generated **Client ID** and **Client Secret**.
7. Ensure the **BigQuery API** (`bigquery.googleapis.com`) is enabled in your Google Cloud project.

---

## 🔗 Connecting to Gemini Enterprise (Official Onboarding Guide)

Follow these official enterprise onboarding steps to securely register the Google-Managed BigQuery MCP Server in your Gemini Enterprise environment:

### Step 1: Create Data Store from Custom MCP Server
1. Go to **Gemini Enterprise** in the Google Cloud Console.
2. Select **Data stores** -> **Create data store**.
3. Type `"MCP"` in the search bar and select **Custom MCP Server**.
4. Fill in the connector connection profile using Google's official managed endpoints:
   - **MCP Server URL:** `https://bigquery.googleapis.com/mcp` *(or your environment's specific Google-managed BigQuery MCP endpoint)*
   - **Authorization URL:** `https://accounts.google.com/o/oauth2/v2/auth`
   - **Authorization URL Parameters:** `&access_type=offline&prompt=consent` *(Ensures GE receives a refresh token for long-lived background agent access)*
   - **Token URL:** `https://oauth2.googleapis.com/token`
   - **Client ID:** *(Paste your Google Cloud OAuth Client ID)*
   - **Client Secret:** *(Paste your Google Cloud OAuth Client Secret)*
   - **Scopes:** `https://www.googleapis.com/auth/cloud-platform` *(or `https://www.googleapis.com/auth/bigquery`)*
5. Click **Login** to authenticate with your Google Cloud account. You will see the standard Google consent screen asking to allow access to your BigQuery data. Click **Allow**.
6. Once redirected back to Gemini Enterprise, click **Continue**.

### Step 2: Advanced Options (AI Instructions)
Fill in the Advanced Options screen to teach Gemini Enterprise's reasoning engine how to use BigQuery:

- **MCP Server Description:**
  ```text
  Official Google-managed BigQuery MCP server providing secure, real-time access to Google Cloud BigQuery datasets and tables. Use this server whenever a user asks to list datasets, explore table schemas, or run SQL queries to analyze enterprise data.
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
1. In Gemini Enterprise, go to **Data stores**, click on your newly created BigQuery Managed MCP datastore, and select **Actions**.
2. By default, all actions are disabled. Select all 4 discovery and SQL execution actions and click **Enable actions**.
3. Go to your Gemini Enterprise App -> **Connected data stores** -> click **Link Existing Datastore** -> select your BigQuery Managed MCP datastore and click **Connect**. You are fully live!

---

## 🧪 Verification Prompts in Gemini Enterprise

Open your Gemini Enterprise app chat and run these exact verification prompts:

1. **Dataset Discovery:** `"List all available datasets in our BigQuery project."`
2. **Table Discovery:** `"List all tables in the [your_dataset_name] dataset."`
3. **Schema Inspection:** `"Get the table schema for [your_table_name] in [your_dataset_name]."`
4. **Analytics Execution:** `"Run a SQL query to count the total number of rows in [your_table_name]."`

---

## ⚠️ Troubleshooting Common Google OAuth Errors

- **`Error 400: redirect_uri_mismatch`**: The redirect URI in your Google Cloud OAuth Client settings does not exactly match the URL Gemini Enterprise is calling from. Copy the exact `redirect_uri` from your error bar (e.g., `https://vertexaisearch.cloud.google.com/oauth-redirect`), paste it into your Google Cloud Credentials console under Authorized Redirect URIs, and click Save.
- **`Error 403: access_denied`**: The user logging in does not have sufficient IAM permissions in the Google Cloud project (e.g., missing `BigQuery Data Viewer` or `BigQuery Job User` roles). Grant the necessary IAM roles in the IAM & Admin console.
