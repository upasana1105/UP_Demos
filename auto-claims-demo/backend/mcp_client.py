# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import json
import httpx
from mcp import ClientSession
from mcp.client.sse import sse_client

async def resolve_address_via_mcp(address: str) -> dict:
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_MAPS_API_KEY environment variable is not set")
        
    headers = {
        "x-goog-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }
    
    # Connect to the Maps MCP server via SSE
    async with sse_client("https://mapstools.googleapis.com/mcp", headers=headers) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            
            # Call the 'search_places' tool
            result = await session.call_tool("search_places", arguments={"textQuery": address})
            
            # Extract text content from response
            # result is a CallToolResult
            for content in result.content:
                # content can be TextContent, ImageContent, or EmbeddedResource
                # In mcp SDK, TextContent has a 'text' attribute
                if hasattr(content, "text"):
                    try:
                        return json.loads(content.text)
                    except json.JSONDecodeError:
                        return {"text": content.text}
            
            return {"content": str(result.content)}
