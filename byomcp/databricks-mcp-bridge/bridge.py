import os
import sys
import httpx
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse

from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

app = FastAPI(title="Databricks Managed MCP Bridge")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration (loads from environment variables, defaults to placeholder values)
DATABRICKS_PAT = os.environ.get("DATABRICKS_PAT", "YOUR_DATABRICKS_PAT")
DATABRICKS_WORKSPACE = os.environ.get("DATABRICKS_WORKSPACE", "https://dbc-XXXX.cloud.databricks.com")

# Default target MCP server (Databricks SQL)
DEFAULT_TARGET_URL = f"{DATABRICKS_WORKSPACE}/api/2.0/mcp/sql"

@app.get("/")
async def health():
    return {"status": "active", "message": "Databricks Managed MCP Bridge is running."}

# 1. Mock OAuth Endpoints to satisfy Gemini Enterprise connection profile
@app.get("/auth")
@app.get("/mcp/sql/auth")
@app.get("/mcp/genie/{genie_space_id}/auth")
async def oauth_authorize(redirect_uri: str, state: str):
    print(f"[OAUTH] Intercepted Authorize request. Redirecting to {redirect_uri}")
    # Immediately redirect back with a mock auth code
    return RedirectResponse(url=f"{redirect_uri}?code=mock_code&state={state}")

@app.post("/token")
@app.get("/token")
@app.post("/mcp/sql/token")
@app.post("/mcp/genie/{genie_space_id}/token")
async def oauth_token():
    print("[OAUTH] Intercepted Token request. Returning mock token.")
    # Return a mock token
    return JSONResponse(content={
        "access_token": "mock_token",
        "token_type": "Bearer",
        "expires_in": 3600,
        "refresh_token": "mock_refresh_token"
    })

# 2. Forward MCP Requests directly to Databricks Managed MCP Server
@app.post("/mcp/sql")
@app.get("/mcp/sql")
@app.post("/mcp/genie/{genie_space_id}")
@app.get("/mcp/genie/{genie_space_id}")
@app.post("/mcp")
@app.get("/mcp")
async def forward_mcp_request(request: Request, genie_space_id: str = None):
    # Get raw body
    body_bytes = await request.body()
    
    # Parse the request to check if it is a tools/list method
    is_tools_list = False
    try:
        import json
        req_json = json.loads(body_bytes.decode("utf-8"))
        if req_json.get("method") == "tools/list":
            is_tools_list = True
    except Exception:
        pass
        
    # Determine the real target URL based on request path
    path = request.url.path
    if "/mcp/sql" in path:
        target_url = f"{DATABRICKS_WORKSPACE}/api/2.0/mcp/sql"
    elif "/mcp/genie/" in path and genie_space_id:
        target_url = f"{DATABRICKS_WORKSPACE}/api/2.0/mcp/genie/{genie_space_id}"
    else:
        target_url = DEFAULT_TARGET_URL
    
    # Dynamically switch target URL based on client header if needed
    client_target = request.headers.get("X-MCP-Target-URL")
    if client_target:
        target_url = client_target

    print(f"[MCP] Forwarding request to Databricks Managed MCP: {target_url}")
    
    headers = {
        "Authorization": f"Bearer {DATABRICKS_PAT}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                target_url,
                content=body_bytes,
                headers=headers,
                timeout=60.0
            )
            
            # Forward response headers except connection metadata
            excluded_headers = ["content-encoding", "content-length", "transfer-encoding", "connection"]
            resp_headers = {
                k: v for k, v in resp.headers.items()
                if k.lower() not in excluded_headers
            }
            
            # If this was a tools/list request, parse the JSON and inject annotations
            if is_tools_list and resp.status_code == 200:
                try:
                    import json
                    resp_json = resp.json()
                    if "result" in resp_json and "tools" in resp_json["result"]:
                        for tool in resp_json["result"]["tools"]:
                            name = tool.get("name", "").lower()
                            existing_ann = tool.get("annotations", {})
                            
                            # If native annotations already exist from the Databricks server, preserve them!
                            if "readOnlyHint" in existing_ann or "destructiveHint" in existing_ann:
                                ro_hint = existing_ann.get("readOnlyHint", not existing_ann.get("destructiveHint", False))
                                dest_hint = existing_ann.get("destructiveHint", not ro_hint)
                                tool["annotations"] = {
                                    "readOnlyHint": bool(ro_hint),
                                    "destructiveHint": bool(dest_hint)
                                }
                                continue
                            
                            # Fallback classification for other workspace tools
                            if any(x in name for x in ["list", "schema", "get", "search", "info", "desc", "read_only", "readonly", "poll", "query"]):
                                tool["annotations"] = {
                                    "readOnlyHint": True,
                                    "destructiveHint": False
                                }
                            else:
                                tool["annotations"] = {
                                    "readOnlyHint": False,
                                    "destructiveHint": True
                                }
                        # Serialize modified JSON
                        modified_content = json.dumps(resp_json).encode("utf-8")
                        resp_headers["content-length"] = str(len(modified_content))
                        return Response(
                            content=modified_content,
                            status_code=200,
                            headers=resp_headers
                        )
                except Exception as parse_err:
                    print(f"[WARNING] Failed to parse and annotate tools/list response: {parse_err}")
            
            return Response(
                content=resp.content,
                status_code=resp.status_code,
                headers=resp_headers
            )
        except Exception as e:
            print(f"[ERROR] Bridge Forwarding Error: {e}")
            raise HTTPException(status_code=500, detail=f"Bridge Forwarding Error: {e}")
