import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import {
    CallToolRequestSchema,
    ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { BigQuery } from "@google-cloud/bigquery";
import { createServer } from "http";
import { Readable } from 'stream';
import axios from 'axios';
import dotenv from "dotenv";

dotenv.config();

const bigquery = new BigQuery();

// Helper to get BigQuery client with optional user token from Authorization header
const getBigQueryClient = (req) => {
    const authHeader = req.headers.authorization;
    
    console.error(`[AUTH LOG] Raw authHeader: ${authHeader ? (authHeader.substring(0, 15) + '...') : 'None'}`);
    
    if (authHeader && authHeader.toLowerCase().startsWith('bearer ') && authHeader !== 'Bearer mock_bq_token') {
        const token = authHeader.substring(7);
        console.error("[AUTH LOG] Detected Real User Token - Connecting with User Identity (Auto-Discovery On)");
        return new BigQuery({ 
            token: token
        });
    }
    
    console.error("[AUTH LOG] Falling back to Default Credentials (Service Account)");
    return bigquery;
};

const server = createServer(async (req, res) => {
    // Standard CORS headers
    res.setHeader("Access-Control-Allow-Origin", "*");
    res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
    res.setHeader("Access-Control-Allow-Headers", "Content-Type, Mcp-Session-Id, Mcp-Protocol-Version, Authorization, Accept");

    if (req.method === "OPTIONS") {
        res.statusCode = 204;
        res.end();
        return;
    }

    const host = req.headers.host || 'localhost';
    const url = new URL(req.url, `http://${host}`);

    if (url.pathname === "/mcp") {
        let bodyChunks = [];
        req.on('data', chunk => bodyChunks.push(chunk));
        req.on('end', async () => {
            const fullBody = Buffer.concat(bodyChunks).toString();
            try {
                const parsedBody = JSON.parse(fullBody || '{}');
                
                // 1. Intercept Handshake
                if (parsedBody.method === "initialize") {
                    res.writeHead(200, {
                        ...res.getHeaders(),
                        "Content-Type": "application/json"
                    });
                    return res.end(JSON.stringify({
                        jsonrpc: "2.0",
                        id: parsedBody.id || 1,
                        result: {
                            protocolVersion: "2024-11-05",
                            capabilities: { tools: {} },
                            serverInfo: { name: "bigquery-proxy", version: "1.0.0" }
                        }
                    }));
                }

                // 2. Intercept Discovery (The fix for Vertex UI)
                if (parsedBody.method === "tools/list") {
                    res.writeHead(200, {
                        ...res.getHeaders(),
                        "Content-Type": "application/json"
                    });
                    return res.end(JSON.stringify({
                        jsonrpc: "2.0",
                        id: parsedBody.id || 1,
                        result: {
                            tools: [
                                {
                                    name: "execute_sql",
                                    description: "Execute a BigQuery SQL query",
                                    inputSchema: {
                                        type: "object",
                                        properties: {
                                            query: { type: "string", description: "The SQL query to execute" }
                                        },
                                        required: ["query"]
                                    }
                                },
                                {
                                    name: "list_datasets",
                                    description: "List datasets in the project",
                                    inputSchema: { type: "object", properties: {} }
                                }
                            ]
                        }
                    }));
                }

                // 3. Auto-Correction for LLM Hallucinations (Catching Python-like methods!)
                let method = parsedBody.method;
                if (method && (method.includes("list_datasets") || method.includes("execute_sql"))) {
                    console.error(`[LLM REPAIR] Auto-correcting hallucinated method '${method}' to 'tools/call'! 🥳🎯`);
                    method = "tools/call";
                    
                    // If it was execute_sql, try to extract the query from parameters if it hallucinated them
                    if (!parsedBody.params || !parsedBody.params.name) {
                        parsedBody.params = parsedBody.params || {};
                        parsedBody.params.name = method.includes("execute_sql") ? "execute_sql" : "list_datasets";
                    }
                }

                if (method === "tools/call") {
                    const { name, arguments: args } = parsedBody.params;
                    console.error(`Received manual tools/call for tool: ${name}`);
                    const bqClient = getBigQueryClient(req);
                    
                    try {
                        let resultText = "";
                        if (name === "execute_sql") {
                            const [rows] = await bqClient.query({ query: args.query });
                            resultText = JSON.stringify(rows, null, 2);
                        } else if (name === "list_datasets") {
                            const [datasets] = await bqClient.getDatasets();
                            resultText = datasets.map(d => d.id).join(', ');
                        } else if (name === "list_tables") {
                            const [tables] = await bqClient.dataset(args.datasetId).getTables();
                            resultText = tables.map(t => t.id).join(', ');
                        } else if (name === "get_table_schema") {
                            const [metadata] = await bqClient.dataset(args.datasetId).table(args.tableId).getMetadata();
                            resultText = JSON.stringify(metadata.schema, null, 2);
                        } else {
                            throw new Error(`Tool not found: ${name}`);
                        }

                        res.writeHead(200, { "Content-Type": "application/json" });
                        res.end(JSON.stringify({
                            jsonrpc: "2.0",
                            id: parsedBody.id || 1,
                            result: {
                                content: [{ type: "text", text: resultText }]
                            }
                        }));
                    } catch (error) {
                        res.writeHead(200, { "Content-Type": "application/json" });
                        res.end(JSON.stringify({
                            jsonrpc: "2.0",
                            id: parsedBody.id || 1,
                            result: {
                                content: [{ type: "text", text: `Error: ${error.message}` }],
                                isError: true
                            }
                        }));
                    }
                }
            } catch (e) {
                // Ignore parsing errors for streaming or non-JSON paths
            }

            try {
                const transport = new StreamableHTTPServerTransport({
                    sessionIdGenerator: undefined,
                    enableJsonResponse: true
                });

                const mcpServer = new Server({
                    name: "bigquery-mcp-server",
                    version: "1.0.0",
                }, {
                    capabilities: { tools: {} },
                });

            // --- MCP Tool Handlers ---
            mcpServer.setRequestHandler(ListToolsRequestSchema, async () => {
                return {
                    tools: [
                        {
                            name: "execute_sql",
                            description: "Execute a BigQuery SQL query",
                            inputSchema: {
                                type: "object",
                                properties: {
                                    query: { type: "string", description: "The SQL query to execute" }
                                },
                                required: ["query"]
                            },
                        },
                        {
                            name: "list_datasets",
                            description: "List datasets in the current project",
                            inputSchema: { type: "object", properties: {} },
                        },
                        {
                            name: "list_tables",
                            description: "List tables in a specific dataset",
                            inputSchema: {
                                type: "object",
                                properties: {
                                    datasetId: { type: "string", description: "The ID of the dataset" }
                                },
                                required: ["datasetId"]
                            },
                        },
                        {
                            name: "get_table_schema",
                            description: "Get the schema of a specific table",
                            inputSchema: {
                                type: "object",
                                properties: {
                                    datasetId: { type: "string", description: "The ID of the dataset" },
                                    tableId: { type: "string", description: "The ID of the table" }
                                },
                                required: ["datasetId", "tableId"]
                            },
                        }
                    ],
                };
            });

            mcpServer.setRequestHandler(CallToolRequestSchema, async (request) => {
                const { name, arguments: args } = request.params;
                console.error(`Received CallToolRequest for tool: ${name}`);
                
                const bqClient = getBigQueryClient(req);
                
                try {
                    if (name === "execute_sql") {
                        const [rows] = await bqClient.query({ query: args.query });
                        return { content: [{ type: "text", text: JSON.stringify(rows, null, 2) }] };
                    }
                    if (name === "list_datasets") {
                        const [datasets] = await bqClient.getDatasets();
                        const result = datasets.map(d => d.id);
                        return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
                    }
                    if (name === "list_tables") {
                        const [tables] = await bqClient.dataset(args.datasetId).getTables();
                        const result = tables.map(t => t.id);
                        return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
                    }
                    if (name === "get_table_schema") {
                        const [metadata] = await bqClient.dataset(args.datasetId).table(args.tableId).getMetadata();
                        return { content: [{ type: "text", text: JSON.stringify(metadata.schema, null, 2) }] };
                    }
                    throw new Error(`Tool not found: ${name}`);
                } catch (error) {
                    console.error(`Error in tool execution:`, error.message);
                    return { 
                        content: [{ type: "text", text: `Error: ${error.message}` }], 
                        isError: true 
                    };
                }
            });

                // Create mock request to pass to SDK transport since we consumed the stream
                const mockReq = new Readable();
                mockReq._read = () => {};
                mockReq.push(fullBody);
                mockReq.push(null);
                mockReq.headers = req.headers;
                mockReq.url = req.url;
                mockReq.method = req.method;

                const reqProxy = new Proxy(mockReq, {
                    get(target, prop, receiver) {
                        if (prop === 'headers') {
                            return {
                                ...target.headers,
                                'accept': 'application/json, text/event-stream'
                            };
                        }
                        return Reflect.get(target, prop, receiver);
                    }
                });

                await transport.handleRequest(reqProxy, res);
            } catch (error) {
                console.error("Transport error:", error);
                if (!res.headersSent) {
                    res.statusCode = 500;
                    res.end("Internal Server Error: " + error.message);
                }
            }
        });
        return;
    }

    // --- Mock OAuth ---
    if (url.pathname === "/auth") {
        const redirect_uri = url.searchParams.get("redirect_uri");
        const state = url.searchParams.get("state");
        res.statusCode = 302;
        res.setHeader("Location", `${redirect_uri}?code=mock_bq_code&state=${state}`);
        res.end();
        return;
    }

    if (url.pathname === "/token") {
        res.setHeader("Content-Type", "application/json");
        res.end(JSON.stringify({
            access_token: "mock_bq_token",
            token_type: "Bearer",
            expires_in: 3600,
            refresh_token: "mock_bq_refresh"
        }));
        return;
    }

    // --- Health Check ---
    if (url.pathname === "/") {
        res.end("BigQuery MCP Server is active.");
        return;
    }

    res.statusCode = 404;
    res.end("Not Found");
});

const PORT = parseInt(process.env.PORT || "3000");
server.listen(PORT, () => {
    console.error(`BigQuery MCP Server running on port ${PORT}`);
});
