# Google Workspace MCP Bridge 🚀

A high-performance Model Context Protocol (MCP) server that bridges Large Language Models (including Gemini Enterprise / Vertex AI Agent Engine) directly to **Google Workspace (Sheets, Docs, Slides, and Gmail)** by wrapping the official Google Workspace CLI (`gws`).

---

## 📦 Overview

The **Google Workspace MCP Bridge** is a containerized Node.js service that implements the MCP HTTP transport layer. It translates standard JSON-RPC 2.0 tool-calling protocols into locally-executed shell commands utilizing the robust `@googleworkspace/cli` tool.

### Key Features
* **Unified Workspace Tools**: Exposes robust tools for managing Google Sheets, Google Docs, Google Slides, and Gmail.
* **Mock OAuth 2.0 Handshake**: Mimics OAuth endpoints (`/auth` and `/token`) required for seamless registration under Gemini Enterprise's custom MCP profile.
* **Dynamically Injected Authentication**: Automatically intercepts incoming HTTP request `Authorization: Bearer <token>` headers, forwarding them to the underlying Workspace CLI as the `GOOGLE_WORKSPACE_CLI_TOKEN` environment variable.
* **Cloud Run Native**: Pre-configured with a `Dockerfile` and a deployment script `deploy.sh` to push the service to GCP in seconds.

---

## 🛠️ Supported MCP Tools

The bridge exposes the following MCP tools to connected agents:

### 📊 Google Sheets
| Tool Name | Description | Required Input Parameters |
| :--- | :--- | :--- |
| `create_sheet` | Creates a new, blank Google Spreadsheet. | `title`: The name of the new sheet |
| `append_to_sheet` | Appends rows of data to a specified range. | `spreadsheetId`, `range`, `values` (array of arrays) |
| `read_sheet` | Reads and retrieves data from a spreadsheet range. | `spreadsheetId`, `range` (e.g., `Sheet1!A1:C10`) |

### ✉️ Gmail
| Tool Name | Description | Required Input Parameters |
| :--- | :--- | :--- |
| `send_email` | Sends a new email via Gmail. | `to` (recipient), `subject`, `body` |
| `reply_email` | Replies to an existing Gmail thread. | `messageId` (ID of thread/message), `body` |
| `triage_emails` | Retrieves a summary of unread inbox emails. | None |

### 📝 Google Docs
| Tool Name | Description | Required Input Parameters |
| :--- | :--- | :--- |
| `write_to_doc` | Appends a block of text to a Google Document. | `documentId`, `text` |

### 🖼️ Google Slides
| Tool Name | Description | Required Input Parameters |
| :--- | :--- | :--- |
| `create_presentation` | Creates a new Google Slides presentation. | `title` |
| `update_presentation` | Performs batch updates on a presentation. | `presentationId`, `requests` (batchUpdate JSON array) |
| `add_slide` | Appends a new slide with a specific layout. | `presentationId`, `slideLayout` (e.g., `TITLE_AND_BODY`, `BLANK`) |
| `add_text_to_slide` | Adds a text box containing text to a slide. | `presentationId`, `slideId`, `text` |

---

## 🚀 Getting Started

### Prerequisites

The bridge depends on the following packages:
* **Node.js**: Version 20.x or later
* **Workspace CLI**: `@googleworkspace/cli` (installed automatically via `npm install`)

### Local Installation & Development

1. Navigate to the workspace directory:
   ```bash
   cd UP_Demos/workspace-mcp-bridge
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Run the server:
   ```bash
   npm start
   ```
   *By default, the server starts on port `3001`. You can override this by setting the `PORT` environment variable.*

4. Verify the server is running:
   ```bash
   curl http://localhost:3001/
   # Output: Workspace MCP Bridge is active.
   ```

---

## ☁️ Deploying to GCP Cloud Run

The project includes a standard `Dockerfile` and a `deploy.sh` helper script to deploy the bridge to Google Cloud Run in a single command.

### Deploying

Run the deployment script:
```bash
chmod +x deploy.sh
./deploy.sh
```

Under the hood, this script:
1. Retrieves your currently active GCP project via the `gcloud` CLI.
2. Submits a container build using **Cloud Build**.
3. Deploys the resulting container to **Cloud Run** with unauthenticated access (so Gemini Enterprise can query the handshake endpoints).

> [!NOTE]
> Unauthenticated access is safe for the handshake interface since the MCP bridge does not store credentials or access keys. All actual Workspace operations require a valid User Bearer Token passed in the request's `Authorization` header.

---

## 🔌 Connecting to Gemini Enterprise / Vertex AI Search

To register this bridge as a Custom MCP Datastore in the **Vertex AI Search and Conversation** console:

1. Navigate to **Data stores** ➡️ **Create data store** ➡️ **Custom MCP Server**.
2. Configure the connection form using your Cloud Run URL:

| Connection Profile Field | Value / Format |
| :--- | :--- |
| **MCP Server URL \*** | `https://<YOUR_CLOUD_RUN_URL>/mcp` |
| **Authorization URL \*** | `https://<YOUR_CLOUD_RUN_URL>/auth` |
| **Authorization URL Parameters** | `&access_type=offline&prompt=consent` |
| **Token URL \*** | `https://<YOUR_CLOUD_RUN_URL>/token` |
| **Client ID \*** | `mock_client` |
| **Client Secret \*** | `mock_secret` |
| **Scopes** | `https://www.googleapis.com/auth/workspace` (or any placeholder string) |

3. Save the datastore, enable it inside the Gemini Enterprise chat interface, and authorize the connection.

---

## 🧪 Verification & Example Prompts

Once connected, try these sample prompts with Gemini Enterprise to verify everything works seamlessly:

### Gmail Triage & Follow-up
> **"Check my Gmail inbox for unread emails, summarize them, and draft a polite reply to the most recent sender thanking them for their update."**

### Data Entry to Sheets
> **"Read the latest project notes from Google Docs and write a breakdown of the action items into a new Google Sheet titled 'Project Actions'."**

### Auto-generate Presentation Slides
> **"Create a new presentation titled 'Q2 Planning' and add a blank slide. Then, insert a text box on that slide stating 'Welcome to Q2 Objectives'."**
