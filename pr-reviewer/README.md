# PR Code Reviewer — Gemini Managed Agents API Demo

A demo that showcases the new **Managed Agents** capabilities in the Gemini API, using a PR code reviewer as the end-to-end use case.

Point it at a GitHub repo and a single command kicks off an agent that runs in the background, reviews the latest commit, applies your internal coding standards, and files a Jira ticket — all without you staying connected.

---

## What This Demos

### 1. Background Execution
The agent starts asynchronously and returns an **interaction ID** immediately. You can close your terminal and reconnect later — the work keeps going in the background.

```python
interaction = client.interactions.create(
    agent=AGENT,
    input=prompt,
    background=True,   # ← fire and forget
)
print(interaction.id) # save this to reconnect later
```

### 2. Server-Side Execution
`code_execution` and MCP tool calls run automatically inside the agent's managed sandbox — no local tooling or infrastructure needed on your end.

The agent fetches the latest GitHub commit and changed files by running Python directly in its sandbox:
```python
tools = [
    {"type": "code_execution"},                                    # runs in sandbox
    {"type": "mcp_server", "name": "jira", "url": JIRA_MCP_URL},  # also in sandbox
]
```

### 3. `requires_action` — Credentials That Never Leave
When the agent needs something sensitive, it **pauses** and hands control back to the client. The client runs the function locally and resumes the agent with the result.

In this demo, `get_coding_standards()` contains internal company data that should never be sent to a remote sandbox. The agent calls it, the interaction moves to `requires_action`, and the client handles it locally:

```python
# Agent pauses → client runs this locally
data = get_coding_standards(team="backend")

# Client resumes the agent with the result
client.interactions.create(
    agent=AGENT,
    previous_interaction_id=interaction.id,  # ← chains the interaction
    input=[{"type": "function_result", ...}]
)
```

### 4. Remote MCP Server
A Jira MCP server hosted on Cloud Run is connected directly — no ngrok, no local tunneling. The agent calls it from inside the sandbox to create a Jira ticket with the review findings.

```
Jira MCP: https://jira-mcp-server-850431687571.us-central1.run.app/mcp
```

---

## Setup

### Prerequisites
- Python 3.11+
- A [Gemini API key](https://aistudio.google.com/apikey) (paid tier required for `background=True` with `store=True`)
- A Jira account (optional — MCP server is pre-deployed)

### Install
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Configure
```bash
cp .env.example .env
# Edit .env and fill in GEMINI_API_KEY
```

---

## Run

```bash
python reviewer.py <github_repo_url> <jira_project_key>
```

**Example:**
```bash
python reviewer.py https://github.com/upasana1105/UP_Demos WAR --branch demo/pr-reviewer-managed-agents
```

**Reconnect to a running job:**
```bash
python reviewer.py --resume <interaction_id>
```

---

## How It Works — Step by Step

```
1. reviewer.py kicks off the agent in the background
        ↓
2. Agent runs code_execution in sandbox → fetches latest GitHub commit
        ↓
3. Agent calls get_coding_standards() → interaction pauses (requires_action)
        ↓
4. Client runs get_coding_standards() locally → resumes agent with result
        ↓
5. Agent calls create_jira_issue via remote MCP → ticket created in Jira
        ↓
6. Agent returns structured review report with Jira link
```

---

## Files

| File | Description |
|------|-------------|
| `reviewer.py` | Main script — orchestrates all 4 demo beats |
| `standards.py` | Mock internal coding standards — runs client-side only, never enters sandbox |
| `requirements.txt` | Python dependencies |
| `.env.example` | Environment variable template |

---

## Key API Concepts

| Concept | What it does |
|---------|-------------|
| `background=True` | Runs the interaction async; returns immediately with an ID |
| `requires_action` | Agent pauses and waits for the client to run a local function |
| `previous_interaction_id` | Chains a new interaction onto a paused one, resuming with new input |
| `environment_id` | Reuses the same sandbox across chained interactions |
| `mcp_server` tool | Connects a remote MCP server into the agent's sandbox |
