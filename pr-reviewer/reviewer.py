#!/usr/bin/env python3
"""
PR Code Reviewer — Gemini Managed Agents API demo.

Demo beats:
  1. Background execution  — agent starts async, you can disconnect
  2. Step matching         — code_execution + MCP run server-side automatically
  3. requires_action       — get_coding_standards() pauses to client; creds never leave
  4. Remote MCP            — Jira updated via your self-hosted MCP server

Usage:
  python reviewer.py <github_repo_url> <jira_project_key>
  python reviewer.py --resume <interaction_id>

  Example:
    python reviewer.py https://github.com/upasana1105/UP_Demos DEMO

Jira MCP: https://jira-mcp-server-850431687571.us-central1.run.app/mcp (Cloud Run, no ngrok needed)
"""

import json
import os
import sys
import time

from dotenv import load_dotenv
from google import genai

from standards import get_coding_standards

load_dotenv()

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")  # optional for public repos (read-only)
JIRA_MCP_URL = os.environ["JIRA_MCP_URL"]

AGENT = "antigravity-preview-05-2026"

client = genai.Client(api_key=GEMINI_API_KEY)

# Custom function — will trigger requires_action (runs client-side)
GET_CODING_STANDARDS_TOOL = {
    "type": "function",
    "name": "get_coding_standards",
    "description": (
        "Retrieves this company's internal coding standards for a given team. "
        "Must be called before reviewing any PR."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "team": {
                "type": "string",
                "enum": ["backend", "frontend", "data"],
                "description": "Which team's standards to fetch.",
            }
        },
        "required": ["team"],
    },
}


def _poll(interaction_id: str) -> object:
    """Poll until the interaction leaves in_progress."""
    interaction = client.interactions.get(id=interaction_id)
    elapsed = 0
    while interaction.status == "in_progress":
        print(f"  ⏳ [{elapsed}s] status={interaction.status} id={interaction_id[:30]}...")
        time.sleep(6)
        elapsed += 6
        interaction = client.interactions.get(id=interaction_id)
        if elapsed > 300:
            print("  ⚠️  5 min timeout — last known status:", interaction.status)
            break
    print(f"  ✅ Exited poll: status={interaction.status}")
    return interaction


def _handle_requires_action(interaction, environment, tools, environment_id=None) -> object:
    """Execute pending client-side function calls and resume the interaction."""
    executed_ids = {
        s.id for s in interaction.steps if s.type == "function_result"
    }
    pending = [
        s for s in interaction.steps
        if s.type == "function_call" and s.id not in executed_ids
    ]

    if not pending:
        print("  ⚠️  requires_action but no pending function calls — check steps")
        return interaction

    results = []
    for call in pending:
        print(f"  🔒 Client executing: {call.name}({call.arguments})")
        print("     (coding standards never sent to sandbox — stays here)")

        if call.name == "get_coding_standards":
            team = call.arguments.get("team", "backend")
            data = get_coding_standards(team)
            results.append({
                "type": "function_result",
                "call_id": call.id,
                "result": [{"type": "text", "text": json.dumps(data)}],
            })
        else:
            results.append({
                "type": "function_result",
                "call_id": call.id,
                "result": [{"type": "text", "text": json.dumps({"error": f"Unknown function: {call.name}"})}],
            })

    print("  ↩️  Submitting results, agent resuming...")

    env = {"type": "remote", "environment_id": environment_id} if environment_id else environment

    resumed = client.interactions.create(
        agent=AGENT,
        previous_interaction_id=interaction.id,
        environment=env,
        tools=tools,
        background=True,
        input=results,
    )
    print(f"  🔄 Resumed interaction ID: {resumed.id}")
    return _poll(resumed.id)


def run_review(repo_url: str, jira_project: str, branch: str = "") -> None:
    print(f"\n🔍 Starting PR review")
    print(f"   Repo:         {repo_url}")
    print(f"   Jira project: {jira_project}")
    print(f"   Jira MCP:     {JIRA_MCP_URL}\n")

    repo_path = repo_url.replace("https://github.com/", "")
    commits_url = f"https://api.github.com/repos/{repo_path}/commits?per_page=1"
    if branch:
        commits_url += f"&sha={branch}"

    github_comment_instruction = ""
    if GITHUB_TOKEN:
        github_comment_instruction = f"""
4. Post your review as a commit comment on GitHub:
   POST https://api.github.com/repos/{repo_path}/commits/{{commit_sha}}/comments
   body: {{"body": "<your full review>"}}
   Your Authorization header is pre-configured.
"""
    else:
        github_comment_instruction = "4. (Skipping GitHub comment — no token configured)"

    prompt = f"""
You are a code reviewer. Do exactly these steps in order:

1. Run this Python code to get the latest commit SHA and changed files:

   import requests, json
   r = requests.get("{commits_url}")
   commit = r.json()[0]
   sha = commit["sha"][:7]
   full_sha = commit["sha"]
   author = commit["commit"]["author"]["name"]
   message = commit["commit"]["message"].splitlines()[0]
   files_url = commit["url"]
   detail = requests.get(files_url).json()
   files = [f["filename"] for f in detail.get("files", [])[:2]]
   print("SHA:", sha)
   print("Author:", author)
   print("Message:", message)
   print("Files:", files)

2. Call get_coding_standards with team="backend".

3. For each file, write 3-5 bullet findings based on the filename and standards.
   Do NOT fetch file contents — review based on filename and path only.

4. Call create_jira_issue with:
   - projectKey: "{jira_project}"
   - issueType: "Task"
   - summary: "Code Review: {repo_path}@<sha>"
   - description: structured findings with sha, author, files, and top findings per file

5. Print a final structured report in this exact format:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REVIEW REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COMMIT ANALYZED
  Repo:    {repo_path}
  SHA:     <sha>
  Author:  <author>
  Message: <commit message>

FILES REVIEWED
  • <file 1>
  • <file 2>

FINDINGS
  [<file 1>]
  • <finding 1>
  • <finding 2>
  • <finding 3>

  [<file 2>]
  • <finding 1>
  • <finding 2>
  • <finding 3>

ACTIONS TAKEN
  GitHub:  Reviewed commit {repo_path}@<sha> (no PR — direct commit review)
  Jira:    Created ticket <ticket key>: https://upasanapati.atlassian.net/browse/<ticket key>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

    # ── Beat 1: Background kick-off ────────────────────────────────────────────
    print("🚀 Beat 1 — Kicking off background job (you could close this terminal now)")

    if GITHUB_TOKEN and GITHUB_TOKEN != "your_github_pat_here":
        environment = {
            "type": "remote",
            "network": {
                "allowlist": [
                    {
                        "domain": "api.github.com",
                        "transform": [{"Authorization": f"Bearer {GITHUB_TOKEN}"}],
                    }
                ]
            },
        }
    else:
        environment = "remote"

    tools = [
        {"type": "code_execution"},
        {"type": "mcp_server", "name": "jira", "url": JIRA_MCP_URL},
        GET_CODING_STANDARDS_TOOL,
    ]

    interaction = client.interactions.create(
        agent=AGENT,
        input=prompt,
        environment=environment,
        tools=tools,
        background=True,
    )

    print(f"   Interaction ID: {interaction.id}")
    print("   Save this ID — you can reconnect later with:")
    print(f"   python reviewer.py --resume {interaction.id}\n")

    # ── Beat 2: Poll (server-side execution) ───────────────────────────────────
    print("📡 Beat 2 — Polling (code_execution + Jira MCP running server-side)")
    interaction = _poll(interaction.id)

    # Capture environment_id so resumed interactions reuse the same sandbox
    env_id = getattr(interaction, "environment_id", None)
    if env_id:
        print(f"   Environment ID: {env_id} (sandbox will be reused)")

    # ── Beat 3: requires_action (coding standards function) ────────────────────
    if interaction.status == "requires_action":
        print("\n⚡ Beat 3 — requires_action: agent needs internal data from client")
        interaction = _handle_requires_action(interaction, environment, tools, env_id)

        while interaction.status == "requires_action":
            env_id = getattr(interaction, "environment_id", env_id)
            interaction = _handle_requires_action(interaction, environment, tools, env_id)

    # ── Final output ───────────────────────────────────────────────────────────
    if interaction.status == "completed":
        print("\n✅ Review complete!\n")
        print("─" * 60)
        print(interaction.output_text)
        print("─" * 60)
        print(f"\nEnvironment ID (reuse for follow-up): {getattr(interaction, 'environment_id', 'n/a')}")
    else:
        print(f"\n❌ Ended with status: {interaction.status}")
        if hasattr(interaction, "error"):
            print(f"   Error: {interaction.error}")


def resume(interaction_id: str) -> None:
    """Reconnect to a background job by ID."""
    print(f"\n🔄 Reconnecting to {interaction_id}...")
    interaction = _poll(interaction_id)

    if interaction.status == "requires_action":
        interaction = _handle_requires_action(interaction, "remote", [GET_CODING_STANDARDS_TOOL])
        while interaction.status == "requires_action":
            interaction = _handle_requires_action(interaction, "remote", [GET_CODING_STANDARDS_TOOL])

    if interaction.status == "completed":
        print("\n✅ Done!\n")
        print(interaction.output_text)
    else:
        print(f"Status: {interaction.status}")


if __name__ == "__main__":
    args = sys.argv[1:]

    # Parse optional --branch flag
    branch = ""
    if "--branch" in args:
        idx = args.index("--branch")
        branch = args[idx + 1]
        args = args[:idx] + args[idx + 2:]

    if len(args) == 2 and args[0] == "--resume":
        resume(args[1])
    elif len(args) == 2:
        run_review(args[0], args[1], branch)
    elif len(args) == 1 and not args[0].startswith("--"):
        run_review(args[0], "WAR", branch)
    else:
        print(__doc__)
        sys.exit(1)
