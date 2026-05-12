# 🚀 Universal SharePoint & OneDrive MCP Connector for Gemini Enterprise

This repository provides an enterprise-grade **Model Context Protocol (MCP)** connector bridging Microsoft Graph API with **Gemini Enterprise**. 

Built specifically to empower AI agents with seamless access to your corporate knowledge base, this connector provides fully autonomous document management across your Entra ID tenant while enforcing strict governance and security compliance through Gemini Enterprise's native Action Approval dialogs.

---

## 🌟 Core Enterprise Capabilities

- **Autonomous Navigation:** AI agents can navigate your SharePoint team sites, document libraries, and nested folders using natural, human-readable names without requiring end users to know complex system IDs or GUIDs.
- **Multi-Format Intelligence:** Supports reading, extracting, and summarizing content across diverse enterprise document formats including Word documents (`.docx`), PowerPoint presentations (`.pptx`), Excel spreadsheets (`.xlsx`), and plain text files.
- **Secure Write Governance:** All data modification actions trigger Gemini Enterprise's built-in Action Approval dialog, ensuring zero data mutations occur without explicit human consent.

---

## 🛠️ Supported Action Catalog

This connector empowers your Gemini Enterprise AI with 12 advanced read and write capabilities across your entire SharePoint and OneDrive ecosystem:

### 🔍 Read Actions (Instant, Interruption-Free Streaming)

#### 1. Search SharePoint Sites
Allows the AI agent to discover relevant corporate SharePoint sites across your organization based on keywords or department names.
- *Example Prompt:* `"Search for SharePoint sites related to Sales and Marketing."`

#### 2. List Document Libraries
Retrieves all available document repositories and drives within a specific SharePoint team site.
- *Example Prompt:* `"List all document libraries in my Sales site."`

#### 3. List Library Items (Files & Folders)
Explores the directory structure, listing all files, subfolders, and metadata within a specific drive or folder location.
- *Example Prompt:* `"List all files and folders inside my Documents library."`

#### 4. Get File Metadata
Retrieves detailed properties for any specific file, including creation date, last modified time, file size, and web URLs.
- *Example Prompt:* `"Get the metadata and last modified time for summary.txt."`

#### 5. Read Document Content
Streams clean, extracted text directly to the AI agent from Word documents (`.docx`), PowerPoint presentations (`.pptx`), Excel spreadsheets (`.xlsx`), and text files for instant summarization or analysis.
- *Example Prompt:* `"Read the text content of Annual_Report.docx and give me a 3-bullet summary."`

#### 6. Get Secure Download URL
Generates temporary, secure, authenticated direct download URLs for any document in your repository.
- *Example Prompt:* `"Generate a direct download URL for my SharePoint presentation."`

---

### 🚀 Write Actions (Protected by Action Approval Consent Dialog)

#### 7. Create a New Folder
Creates a new subfolder inside any document library or parent folder using natural names.
- *Example Prompt:* `"Create a new folder named 'QuarterlyReports' in Documents."`

#### 8. Create a New Document
Surgically creates new text documents inside specified folders and populates them with AI-generated content.
- *Example Prompt:* `"Create a new document named 'summary.txt' inside my 'Quarterly Meeting notes' folder in Documents with the content 'Q1 meeting notes summary.' "`

#### 9. Update / Overwrite Document Content
Overwrites or updates the text content of an existing document instantly.
- *Example Prompt:* `"Update the content of summary.txt in Documents to say 'Record Q1 performance achieved.' "`

#### 10. Rename an Item
Renames any existing file or folder while preserving its contents and location.
- *Example Prompt:* `"Rename summary.txt in Documents to 'Final_Summary.txt'."`

#### 11. Move an Item
Moves files or folders between different directories or archive locations.
- *Example Prompt:* `"Move Final_Summary.txt from Documents into the Archive folder."`

#### 12. Delete an Item
Securely deletes unwanted files or folders from your repository.
- *Example Prompt:* `"Delete my old temporary summary file from Documents."`

---

## 📋 Prerequisites: Microsoft Entra ID Setup

Before deploying the server, register a Microsoft Entra ID OAuth application:

1. Go to the **Microsoft Entra Admin Center** -> **App registrations** -> **New registration**.
2. Name your app (e.g., `Gemini-Enterprise-SharePoint-MCP`).
3. Choose **Accounts in this organizational directory only**.
4. Under **API permissions**, add Delegated permissions: `Files.ReadWrite.All`, `Sites.ReadWrite.All`, `User.Read`.
5. Grant **Admin Consent** for your tenant.
6. Create a **Client Secret** and note your **Client ID** and **Tenant ID**.

---

## 💻 Local Development & Testing

```bash
npm install
```
Create a `.env` file:
```env
MICROSOFT_CLIENT_ID="your-entra-client-id"
MICROSOFT_CLIENT_SECRET="your-entra-client-secret"
MICROSOFT_TENANT_ID="your-entra-tenant-id"
PORT=8080
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
Once deployed, note your live Cloud Run URL (e.g., `https://sharepoint-mcp-server-850431687571.us-central1.run.app`).

---

## 🔗 Connecting to Gemini Enterprise (Official Onboarding Guide)

Follow these official enterprise onboarding steps (modeled after Google-managed MCP standards) to securely register this connector in your Gemini Enterprise environment:

### Step 1: Create OAuth Client for Gemini Enterprise Authentication
1. In Google Cloud Console, go to **APIs & Services** -> **Credentials**.
2. Click **Create credentials** -> **OAuth Client ID**.
3. **Application Type:** `Web Application`.
4. **Authorized redirect URIs:** Add `https://vertexaisearch.cloud.google.com/oauth-redirect`.
5. Click **Create**. Save your generated **Client ID** and **Client Secret**.

### Step 2: Create Data Store from Custom MCP Server
1. Go to **Gemini Enterprise** in Google Cloud Console.
2. Select **Data stores** -> **Create data store**.
3. Type `"MCP"` in the search bar and select **Custom MCP Server**.
4. Fill in the connector connection profile for Microsoft SharePoint:
   - **MCP Server URL:** `https://sharepoint-mcp-server-850431687571.us-central1.run.app` *(your live Cloud Run deployment URL)*
   - **Authorization URL:** `https://login.microsoftonline.com/common/oauth2/v2.0/authorize`
   - **Auth URL Parameters:** `&prompt=consent`
   - **Token URL:** `https://login.microsoftonline.com/common/oauth2/v2.0/token`
   - **Client ID:** *(paste Microsoft Entra Client ID)*
   - **Client Secret:** *(paste Microsoft Entra Client Secret)*
   - **Scopes:** `Files.ReadWrite.All Sites.ReadWrite.All User.Read offline_access`
5. Click **Login** to authenticate with your Microsoft account, then click **Continue**.
6. Under **Advanced Options** (optional), enter `"SharePoint & OneDrive Universal MCP Server"`. Click Continue.
7. Choose your multi-region location (e.g., `global`), enter a Data Connector name, and click **Create**.
8. Wait a few minutes for the connector to initialize. Then go to **Data stores**, click on your newly created MCP datastore, and select **Actions**. 
9. By default, all actions are disabled. Select all 12 read and write actions and click **Enable actions**.

### Step 3: Connect Gemini Enterprise App to the MCP Server
1. Go to **Gemini Enterprise** -> select the app you'd like to connect.
2. Go to **Connected data stores** -> click **Link Existing Datastore**.
3. Select your newly created MCP Server datastore and click **Connect**.

### Step 4: Use the MCP Server within Gemini Enterprise
- **Option A (Directly in Chat):** Open your Gemini Enterprise app URL (`https://vertexaisearch.cloud.google.com/home/cid/...`). Click on the **Connector** icon in the chat bar and authorize the server.
- **Option B (Agent Designer):** In Gemini Enterprise, click `+ New Agent` -> proceed to Builder. Under **Connectors**, click the `+` sign and toggle on `SharePoint & OneDrive MCP Server`. You are fully live!
