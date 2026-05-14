# Jira MCP Server — Session Summary

> Use this document to onboard a new AI assistant or resume work in a new conversation.

---

## What Was Built

A **Jira MCP Server** deployed to **Google Cloud Run** that exposes Jira tools via the MCP (Model Context Protocol) Streamable HTTP transport. It is designed to be connected to **Gemini Enterprise** as a third-party MCP data store.

---

## Current Status: ✅ Deployed & Verified via `curl`

The server is live and responding correctly to `tools/list` and `tools/call` requests via `curl`. The next step is to complete the **Gemini Enterprise UI configuration** so Gemini can actually call the tools.

---

## Live URLs

| Endpoint        | URL                                                                        |
|-----------------|---------------------------------------------------------------------------|
| **Service**     | `https://jira-mcp-server-850431687571.us-central1.run.app`                |
| **MCP**         | `https://jira-mcp-server-850431687571.us-central1.run.app/mcp`            |
| **Auth (mock)** | `https://jira-mcp-server-850431687571.us-central1.run.app/auth`           |
| **Token (mock)**| `https://jira-mcp-server-850431687571.us-central1.run.app/token`          |

---

## GCP Details

- **Project:** `uppdemos`
- **Service Name:** `jira-mcp-server`
- **Region:** `us-central1`
- **Latest Revision:** `jira-mcp-server-00014-f9m`

---

## Tools Implemented

| Tool Name                | Description                                  |
|--------------------------|----------------------------------------------|
| `get_jira_current_user`  | Returns the authenticated Jira user profile  |
| `list_jira_projects`     | Lists all accessible Jira projects           |
| `get_jira_issue`         | Fetch a specific issue by key (e.g., WAR-123)|
| `search_jira_issues`     | Run JQL queries (uses `POST /search/jql`)    |
| `create_jira_issue`      | Create new Jira tickets                      |

---

## Key Files

| File             | Purpose                                                              |
|------------------|----------------------------------------------------------------------|
| `index.js`       | Main server — MCP handlers, HTTP server, mock OAuth, header proxy    |
| `Dockerfile`     | Containerizes the Node.js app for Cloud Run                          |
| `deploy.sh`      | One-command deployment script (`./deploy.sh`)                        |
| `.env`           | Local env vars (`ATLASSIAN_BASE_URL`, `ATLASSIAN_EMAIL`, `ATLASSIAN_API_TOKEN`) |
| `package.json`   | Dependencies: `@modelcontextprotocol/sdk`, `axios`, `dotenv`         |

---

## Environment Variables (set on Cloud Run)

```
ATLASSIAN_BASE_URL=https://upasanapati.atlassian.net
ATLASSIAN_EMAIL=upasanapati@gmail.com
ATLASSIAN_API_TOKEN=<redacted — already configured on Cloud Run>
```
**Project:** `uppdemos` (Confirmed by user)

---

## Architecture & Key Design Decisions

### 1. Native Node.js `http` Server (no Express/Hono)
We use `createServer` from Node's `http` module directly. Express and Hono both interfered with the MCP SDK's internal request body parsing.

### 2. Fresh Transport & Server Per Request
The `StreamableHTTPServerTransport` AND `Server` (SDK) are instantiated **inside** the `/mcp` request handler for every incoming POST. The SDK throws `"Stateless transport cannot be reused across requests"` if you try to share a single instance, and reusing the `Server` instance with a fresh transport causes `"Already connected to a transport"` errors.

### 3. Header Proxy for Cloud Run
Cloud Run's reverse proxy modifies/drops HTTP headers. The MCP SDK strictly validates the `Accept` header. We use a JavaScript `Proxy` object to forcefully inject `'accept': 'application/json, text/event-stream'` on every request before it reaches the SDK.

### 4. `enableJsonResponse: true`
This SDK option returns standard JSON responses instead of Server-Sent Event streams. Without it, Cloud Run prematurely terminates the SSE connection during long-running Jira API calls (like `list_jira_projects`), causing 500 errors.

### 5. API Changes
- `search_jira_issues`: Uses `POST /rest/api/3/search/jql` because `GET /rest/api/3/search` and `POST /rest/api/3/search` (legacy) returned a 410 Gone error.

### 6. Mock OAuth
The `/auth` and `/token` endpoints implement a mock OAuth 2.0 flow. The `/token` endpoint returns `access_token`, `token_type`, `expires_in`, and `refresh_token` (Gemini Enterprise requires the refresh token).

---

## Bugs Fixed During This Session

| Bug | Root Cause | Fix |
|-----|-----------|-----|
| 500 on `/mcp` POST | Express `json()` middleware consumed the request body before the MCP SDK could read it | Removed Express entirely, switched to native Node `http` server |
| 500 on `tools/call` (Cloud Run only) | Cloud Run proxy modified `Accept` header casing, failing SDK strict validation | Added JavaScript `Proxy` to normalize headers |
| 500 on `tools/call` (async tools) | SSE stream terminated prematurely by Cloud Run | Enabled `enableJsonResponse: true` |
| "Failed to obtain refresh token" in Gemini UI | Mock `/token` endpoint didn't return `refresh_token` | Added `refresh_token: "mock_refresh"` to response |
| 500 on second request to `/mcp` | Stateless `StreamableHTTPServerTransport` instance was reused globally across requests | Moved transport instantiation inside the per-request handler |
| "Already connected to a transport" error | `mcpServer` instance was reused with fresh transport | Moved `mcpServer` instantiation inside the per-request handler |
| 410 on `search_jira_issues` | `GET /rest/api/3/search` API was removed/deprecated | Updated to use `POST /rest/api/3/search/jql` |

---

## Gemini Enterprise Configuration (Ready)

In the Google Cloud Console under **Gemini Enterprise > Extensions > Data Stores > MCP Server**:

| Field              | Value                                                              |
|--------------------|--------------------------------------------------------------------|
| MCP Server URL     | `https://jira-mcp-server-850431687571.us-central1.run.app/mcp`    |
| Authorization URL  | `https://jira-mcp-server-850431687571.us-central1.run.app/auth`   |
| Token URL          | `https://jira-mcp-server-850431687571.us-central1.run.app/token`  |
| Client ID          | `test`                                                             |
| Client Secret      | `test`                                                             |
| Scopes             | `openid`                                                           |
| Tools              | `get_jira_current_user list_jira_projects get_jira_issue search_jira_issues create_jira_issue` |

---

## How to Test Locally

```bash
cd /Users/upasanapati/shrinkAI\ experiment/Antigravity_Experiments/UP_Demos/MCP/jira-mcp-server

# Start server
node index.js

# Test create_issue
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc": "2.0", "method": "tools/call", "id": "1", "params": {"name": "create_jira_issue", "arguments": {"projectKey": "WAR", "summary": "Test issue", "issueType": "Task"}}}'
```

---

## How to Deploy

```bash
cd /Users/upasanapati/shrinkAI\ experiment/Antigravity_Experiments/UP_Demos/MCP/jira-mcp-server
./deploy.sh
```

---

## What's Next

1. **Complete Gemini Enterprise connection** — Configure Data Store with above URLs.
2. **Test end-to-end in Gemini** — Ask Gemini "Create a Jira issue for..."
