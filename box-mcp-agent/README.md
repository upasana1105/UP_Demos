# 🚀 Universal Box MCP Connector for Gemini Enterprise

This repository provides an enterprise-grade **Model Context Protocol (MCP)** onboarding and configuration guide for connecting the official **Box Native MCP Server** (`https://mcp.box.com`) directly to **Gemini Enterprise**.

Built specifically to empower AI agents with secure, seamless access to your corporate Box repository, this integration enables fully autonomous document discovery, deep content extraction, and folder navigation across your Box enterprise tenant while enforcing strict governance and user-level access controls.

---

## 🌟 Core Enterprise Capabilities

- **Autonomous Folder Navigation:** AI agents can seamlessly navigate your Box enterprise folder hierarchy, list directory contents, and locate files using natural, human-readable names without requiring end users to know complex Box file IDs or GUIDs.
- **Multi-Format Document Intelligence:** Supports reading, extracting, and summarizing content across diverse enterprise document formats stored in Box, including Word documents (`.docx`), PDFs (`.pdf`), Excel spreadsheets (`.xlsx`), PowerPoint presentations (`.pptx`), and plain text files.
- **Enterprise Security & Governance:** Leverages Box's native OAuth 2.0 authentication model. All data access is strictly scoped to the authenticated user's permissions in Box, ensuring zero data leakage across departmental boundaries.

---

## 🛠️ Supported Action Catalog

Connecting this native server empowers your Gemini Enterprise AI with advanced read and discovery capabilities across your entire Box ecosystem:

### 🔍 Discovery & Read Actions (Instant, Interruption-Free Streaming)

#### 1. Search Box Files & Folders
Allows the AI agent to discover relevant corporate documents and folders across your Box organization based on keywords, project names, or metadata.
- *Example Prompt:* `"Search Box for any files or folders related to 'Project Falcon' or 'Q1 Budget'."`

#### 2. List Folder Contents
Explores the directory structure, listing all files, subfolders, and metadata within a specific Box folder location.
- *Example Prompt:* `"List all files and subfolders inside my 'Gemini Enterprise Demo' folder in Box."`

#### 3. Get File Metadata
Retrieves detailed properties for any specific Box file, including creation date, last modified timestamp, file size, author details, and direct web links.
- *Example Prompt:* `"Get the metadata and last modified time for Employee_Handbook_2026.pdf."`

#### 4. Read Document Content
Streams clean, extracted text directly to the AI agent from Word documents (`.docx`), PDFs (`.pdf`), Excel spreadsheets (`.xlsx`), PowerPoint presentations (`.pptx`), and text files for instant summarization, Q&A, or comparative analysis.
- *Example Prompt:* `"Read the text content of Project_Falcon_Overview.docx in Box and give me a 3-bullet executive summary."`

---

## 📋 Prerequisites: Box Developer Console Setup

Before connecting Gemini Enterprise, register and configure your Box application:

1. Log into the **Box Admin Console** (as a Box Admin) or the **Box Developer Console**.
2. In the left sidebar, click **Integrations** -> search for **Box MCP server**.
3. Hover over the Box MCP server application card and click **Configure** (or create a new Custom App with OAuth 2.0 authentication).
4. Under **Additional Configuration**, click **+ Add Integration Credentials** (or expand your existing credentials).
5. Enter an integration name (e.g., `Gemini Enterprise Box MCP`) and click **Save**.
6. Expand the details of your newly created entry and copy your **Client ID** and **Client Secret**.
7. Under **OAuth 2.0 Redirect URIs**, paste the exact redirect URI provided by Gemini Enterprise (e.g., `https://vertexaisearch.cloud.google.com/oauth-redirect`).
   *(⚠️ Important: Ensure there are no trailing slashes `/` or leading blank spaces).*
8. Under **Access Scopes**, ensure **Content Actions** (and/or `root_readwrite`) is enabled.
9. Click **Save Changes**.

---

## 🔗 Connecting to Gemini Enterprise (Official Onboarding Guide)

Follow these official enterprise onboarding steps to securely register the Box Native MCP Server in your Gemini Enterprise environment:

### Step 1: Create Data Store from Custom MCP Server
1. Go to **Gemini Enterprise** in the Google Cloud Console.
2. Select **Data stores** -> **Create data store**.
3. Type `"MCP"` in the search bar and select **Custom MCP Server**.
4. Fill in the connector connection profile exactly as follows:
   - **MCP Server URL:** `https://mcp.box.com`
   - **Authorization URL:** `https://account.box.com/api/oauth2/authorize`
   - **Authorization URL Parameters:** *(Leave completely blank - Box does not support Google/Microsoft offline params)*
   - **Token URL:** `https://api.box.com/oauth2/token`
   - **Client ID:** *(Paste your Box Client ID)*
   - **Client Secret:** *(Paste your Box Client Secret)*
   - **Scopes:** *(Leave completely blank - Box defaults to your app's approved console scopes)*
5. Click **Login** to authenticate with your Box account. You will see the Box consent screen. Click **Grant Access** to authorize the connection.
6. Once redirected back to Gemini Enterprise, click **Continue**.

### Step 2: Advanced Options (AI Instructions)
Fill in the Advanced Options screen to teach Gemini Enterprise's reasoning engine how to use Box:

- **MCP Server Description:**
  ```text
  Official Box native MCP server providing secure, real-time access to enterprise files, folders, and document content stored in Box. Use this server whenever a user asks to search for Box documents, list folder contents, retrieve file metadata, read/summarize document text, or navigate corporate file repositories.
  ```
- **MCP Agent Instructions:**
  ```text
  You are an expert enterprise AI assistant connected to Box via the Model Context Protocol. Follow these rules when interacting with Box tools:
  1. Autonomous Navigation: When a user asks to find a file or folder by name, first use the search or folder listing tools to locate the exact item and retrieve its unique Box file ID or folder ID.
  2. Content Summarization: When asked to summarize or analyze a document, use the file reading tool to extract the clean text content, then synthesize a clear, structured response.
  3. Security & Accuracy: Always verify file metadata (such as last modified date and author) if there are multiple files with similar names to ensure you are working with the most current version. Never guess file IDs.
  ```
- Click **Create** to finalize the datastore.

### Step 3: Enable Actions & Connect App
1. In Gemini Enterprise, go to **Data stores**, click on your newly created Box MCP datastore, and select **Actions**.
2. By default, all actions are disabled. Select all available Box discovery and read actions and click **Enable actions**.
3. Go to your Gemini Enterprise App -> **Connected data stores** -> click **Link Existing Datastore** -> select your Box MCP datastore and click **Connect**. You are fully live!

---

## 🧪 Demo Data Setup & Verification Prompts in GE

To verify your deployment, create the following sample folder structure in your Box account (`app.box.com`):

```text
📦 All Files (Root)
 ┗ 📂 Gemini Enterprise Demo
    ┣ 📂 1. Financial Reports
    ┃  ┗ 📊 Q1_Budget_Summary.xlsx (or .csv)
    ┣ 📂 2. HR & Onboarding
    ┃  ┗ 📄 Employee_Handbook_2026.pdf (or .txt)
    ┗ 📂 3. Project Specs
       ┗ 📝 Project_Falcon_Overview.docx
```

Open your Gemini Enterprise app chat and run these exact verification prompts:

1. **Search & Discovery:** `"Search Box for any files or folders related to 'Project Falcon' or 'Budget'."`
2. **Folder Navigation:** `"List all the files and subfolders inside the 'Gemini Enterprise Demo' folder in Box."`
3. **Metadata Retrieval:** `"Get the file metadata and last modified date for Employee_Handbook_2026."`
4. **Deep Summarization (Wow Test):** `"Read the content of Project_Falcon_Overview.docx in Box and give me a 3-bullet executive summary."`

---

## ⚠️ Troubleshooting Common Box OAuth Errors

- **`Error: redirect_uri_mismatch`**: The redirect URI in your Box Developer Console does not exactly match the URL Gemini Enterprise is calling from. Copy the exact `redirect_uri` from your error bar (e.g., `https://vertexaisearch.cloud.google.com/oauth-redirect`), paste it into your Box App configuration under OAuth 2.0 Redirect URIs, and click Save.
- **`Error: invalid_request` on Login**: You entered parameters into the *Authorization URL Parameters* field in Gemini Enterprise. Box strictly rejects custom Google/Microsoft parameters like `access_type=offline`. Clear that field in Gemini Enterprise so it is completely blank.
- **`Error: invalid_scope`**: You entered custom scopes in Gemini Enterprise that don't match your Box app checkboxes. Clear the *Scopes* field in Gemini Enterprise so it is completely blank.
