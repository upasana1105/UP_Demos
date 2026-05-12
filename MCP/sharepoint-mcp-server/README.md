# 🚀 Universal SharePoint & OneDrive MCP Connector for Gemini Enterprise

This repository provides a production-ready, enterprise-grade **Model Context Protocol (MCP)** server bridging Microsoft Graph API with **Gemini Enterprise**. 

Built specifically for high-performance AI agentic workflows, this connector features autonomous LLM prompt engineering, universal tenant-wide drive resolution, recursive folder discovery, zero-dependency binary extraction (Word, PowerPoint, Excel), and strict compliance with Gemini Enterprise's Action Approval consent dialogs for write mutations.

---

## 🌟 Enterprise Architectural Highlights

1. **Universal Tenant-Wide Drive Resolution (`resolveDriveId`):** End users can refer to document libraries by human-readable names (e.g., `"Documents"`). The backend container automatically scans all accessible SharePoint team sites across your Entra ID tenant to locate the exact alphanumeric Drive GUID behind the scenes.
2. **Recursive Drive & Folder Search (`resolveItemId`):** End users can target deeply nested folders by name (e.g., `"Quarterly Meeting notes"`). The container performs a recursive Graph API drive search (`/root/search(q=...)`) to locate the exact Folder GUID instantly.
3. **Multi-Format Binary Text Stripper:** Includes high-speed Mammoth extraction for Word (`.docx`) and a custom, zero-dependency XML regex stripper for PowerPoint (`.pptx`) and Excel (`.xlsx`).
4. **Action Approval Security Compliance:** All write mutations (`createFolder`, `createFile`, `updateFile`, `rename`, `move`, `delete`) are annotated with `"destructiveHint": true` and `"readOnlyHint": false`, ensuring Gemini Enterprise pops up its secure consent dialog before modifying corporate records.

---

## 📋 Prerequisites: Microsoft Entra ID Setup

Before deploying the server, register a Microsoft Entra ID (formerly Azure AD) OAuth application:

1. Go to the **Microsoft Entra Admin Center** -> **App registrations** -> **New registration**.
2. Name your app (e.g., `Gemini-Enterprise-SharePoint-MCP`).
3. Under **Supported account types**, choose **Accounts in this organizational directory only**.
4. Under **API permissions**, add the following Microsoft Graph Delegated permissions:
   - `Files.ReadWrite.All`
   - `Sites.ReadWrite.All`
   - `User.Read`
5. Grant **Admin Consent** for your tenant.
6. Under **Certificates & secrets**, create a new **Client Secret**. Save the Secret Value.
7. Under **Overview**, note your **Application (client) ID** and **Directory (tenant) ID**.

---

## 💻 Local Development & Testing

1. Clone the repository and install dependencies:
   ```bash
   npm install
   ```
2. Create a `.env` file in the root directory:
   ```env
   MICROSOFT_CLIENT_ID="your-entra-client-id"
   MICROSOFT_CLIENT_SECRET="your-entra-client-secret"
   MICROSOFT_TENANT_ID="your-entra-tenant-id"
   PORT=8080
   ```
3. Run the local development server:
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

*Note: The deployment script automatically builds your Dockerfile, pushes it to Artifact Registry, and deploys it to Cloud Run.* 
Once deployed, note your live Cloud Run URL (e.g., `https://sharepoint-mcp-server-850431687571.us-central1.run.app`).

---

## 🔗 Connecting to Gemini Enterprise (BYO MCP)

To integrate this custom server into your Gemini Enterprise workspace:

1. Open your **Gemini Enterprise Admin / Actions Panel**.
2. Select **Add Custom Action / BYO MCP Server**.
3. Enter the following configuration:
   - **Name:** `SharePoint & OneDrive Universal MCP`
   - **Endpoint URL:** `https://sharepoint-mcp-server-850431687571.us-central1.run.app`
   - **Authentication:** Select `OAuth 2.0` (or pass your service authentication headers).
4. Click **Save & Reload custom actions**.

---

## 🛠️ Complete Tool Catalog & Example Prompts

Your Gemini Enterprise AI can now execute all 12 advanced read and write tools using pure natural language commands:

### 🔍 Read Actions (Instant Streaming)
- **Search SharePoint Sites:** *"Search for SharePoint sites related to Sales and Marketing."*
- **List Document Libraries:** *"List all document libraries in my Sales site."*
- **List Library Items:** *"List all files and folders inside my Documents library."*
- **Get File Metadata:** *"Get the metadata and last modified time for summary.txt."*
- **Read Document Content (Word, PPTX, Excel, Text):** *"Read the extracted text content of Annual_Report.docx and give me a 3-bullet summary."*
- **Get Binary Download URL:** *"Generate a direct download URL for my SharePoint document."*

### 🚀 Write Actions (Protected by Action Approval Dialog)
- **Create a Folder:** *"Create a new folder named 'QuarterlyReports' in Documents."*
- **Create a Document:** *"Create a new document named 'summary.txt' inside my 'Quarterly Meeting notes' folder in Documents with the content 'Q1 meeting notes summary.' "*
- **Update/Overwrite Document:** *"Update the content of summary.txt in Documents to say 'Record Q1 performance achieved.' "*
- **Rename Item:** *"Rename summary.txt in Documents to 'Final_Summary.txt'."*
- **Move Item:** *"Move Final_Summary.txt from Documents into the Archive folder."*
- **Delete Item:** *"Delete my old temporary summary file from Documents."*

---

## 🛡️ Security & Governance
This server enforces strict enterprise boundaries. Write tools will **never** execute without explicit human confirmation via the Gemini Enterprise UI approval dialog, ensuring complete protection against unintended AI mutations.
