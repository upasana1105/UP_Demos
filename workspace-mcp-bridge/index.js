import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import {
    CallToolRequestSchema,
    ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { createServer } from "http";
import { Readable } from 'stream';
import { exec } from 'child_process';
import { promisify } from 'util';
import dotenv from "dotenv";
import path from "path";
import { fileURLToPath } from 'url';

dotenv.config();

const execPromise = promisify(exec);
const __dirname = path.dirname(fileURLToPath(import.meta.url));
// Path to gws in the root node_modules
const GWS_PATH = path.resolve(__dirname, "node_modules/.bin/gws");

// Helper to get environment variables for GWS, including token from request
const getGwsEnv = (req) => {
    const env = { ...process.env };
    const authHeader = req.headers.authorization;
    
    if (authHeader && authHeader.toLowerCase().startsWith('bearer ') && authHeader !== 'Bearer mock_bq_token') {
        const token = authHeader.substring(7);
        console.error("[AUTH LOG] Detected User Token - Passing to GWS");
        env.GOOGLE_WORKSPACE_CLI_TOKEN = token;
    }
    return env;
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
            console.error(`[DEBUG] Received request: ${fullBody}`);
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
                        id: parsedBody.id !== undefined ? parsedBody.id : 1,
                        result: {
                            protocolVersion: parsedBody.params?.protocolVersion || "2025-11-25",
                            capabilities: { tools: {} },
                            serverInfo: { name: "workspace-bridge", version: "1.0.0" }
                        }
                    }));
                }

                // Intercept initialized notification
                if (parsedBody.method === "notifications/initialized") {
                    res.writeHead(200, { "Content-Type": "application/json" });
                    return res.end(JSON.stringify({}));
                }

                // 2. Intercept Discovery
                if (parsedBody.method === "tools/list") {
                    res.writeHead(200, {
                        ...res.getHeaders(),
                        "Content-Type": "application/json"
                    });
                    return res.end(JSON.stringify({
                        jsonrpc: "2.0",
                        id: parsedBody.id !== undefined ? parsedBody.id : 1,
                        result: {
                            tools: [
                                {
                                    name: "create_sheet",
                                    description: "Create a new Google Sheet",
                                    inputSchema: {
                                        type: "object",
                                        properties: {
                                            title: { type: "string", description: "Title of the sheet" }
                                        },
                                        required: ["title"]
                                    }
                                },
                                {
                                    name: "append_to_sheet",
                                    description: "Append rows to a Google Sheet",
                                    inputSchema: {
                                        type: "object",
                                        properties: {
                                            spreadsheetId: { type: "string", description: "The ID of the spreadsheet" },
                                            range: { type: "string", description: "The range to append to (e.g., Sheet1!A1)" },
                                            values: { 
                                                type: "array", 
                                                items: { type: "array", items: { type: "string" } },
                                                description: "Array of arrays containing values to append"
                                            }
                                        },
                                        required: ["spreadsheetId", "range", "values"]
                                    }
                                },
                                {
                                    name: "read_sheet",
                                    description: "Read values from a spreadsheet",
                                    inputSchema: {
                                        type: "object",
                                        properties: {
                                            spreadsheetId: { type: "string", description: "The ID of the spreadsheet" },
                                            range: { type: "string", description: "The range to read (e.g., Sheet1!A1:C10)" }
                                        },
                                        required: ["spreadsheetId", "range"]
                                    }
                                },
                                {
                                    name: "write_to_doc",
                                    description: "Append text to a Google Doc",
                                    inputSchema: {
                                        type: "object",
                                        properties: {
                                            documentId: { type: "string", description: "The ID of the document" },
                                            text: { type: "string", description: "The text to append" }
                                        },
                                        required: ["documentId", "text"]
                                    }
                                },
                                {
                                    name: "send_email",
                                    description: "Send an email via Gmail",
                                    inputSchema: {
                                        type: "object",
                                        properties: {
                                            to: { type: "string", description: "Recipient email address" },
                                            subject: { type: "string", description: "Subject of the email" },
                                            body: { type: "string", description: "Body content of the email" }
                                        },
                                        required: ["to", "subject", "body"]
                                    }
                                },
                                {
                                    name: "reply_email",
                                    description: "Reply to an email thread",
                                    inputSchema: {
                                        type: "object",
                                        properties: {
                                            messageId: { type: "string", description: "ID of the message to reply to" },
                                            body: { type: "string", description: "Reply body content" }
                                        },
                                        required: ["messageId", "body"]
                                    }
                                },
                                {
                                    name: "triage_emails",
                                    description: "Show unread inbox summary",
                                    inputSchema: { type: "object", properties: {} }
                                },
                                {
                                    name: "create_presentation",
                                    description: "Create a new Google Slides presentation",
                                    inputSchema: {
                                        type: "object",
                                        properties: {
                                            title: { type: "string", description: "Title of the presentation" }
                                        },
                                        required: ["title"]
                                    }
                                },
                                {
                                    name: "update_presentation",
                                    description: "Batch update a Google Slides presentation",
                                    inputSchema: {
                                        type: "object",
                                        properties: {
                                            presentationId: { type: "string", description: "The ID of the presentation" },
                                            requests: { type: "array", description: "Array of batchUpdate requests" }
                                        },
                                        required: ["presentationId", "requests"]
                                    }
                                },
                                {
                                    name: "add_slide",
                                    description: "Add a new slide to a presentation",
                                    inputSchema: {
                                        type: "object",
                                        properties: {
                                            presentationId: { type: "string", description: "The ID of the presentation" },
                                            slideLayout: { type: "string", description: "Layout type (e.g., TITLE_AND_BODY, BLANK)" }
                                        },
                                        required: ["presentationId", "slideLayout"]
                                    }
                                },
                                {
                                    name: "add_text_to_slide",
                                    description: "Add a text box with text to a slide",
                                    inputSchema: {
                                        type: "object",
                                        properties: {
                                            presentationId: { type: "string", description: "The ID of the presentation" },
                                            slideId: { type: "string", description: "The ID of the slide" },
                                            text: { type: "string", description: "The text to add" }
                                        },
                                        required: ["presentationId", "slideId", "text"]
                                    }
                                }
                            ]
                        }
                    }));
                }

                // 3. Handle Tool Calls
                if (parsedBody.method === "tools/call") {
                    const { name, arguments: args } = parsedBody.params;
                    console.error(`Received manual tools/call for tool: ${name}`);
                    const env = getGwsEnv(req);
                    
                    try {
                        let resultText = "";
                        
                        if (name === "create_sheet") {
                            const cmd = `${GWS_PATH} sheets spreadsheets create --json '{"properties": {"title": "${args.title}"}}'`;
                            const { stdout } = await execPromise(cmd, { env });
                            resultText = stdout;
                        } else if (name === "append_to_sheet") {
                            const cmd = `${GWS_PATH} sheets spreadsheets values append --params '{"spreadsheetId": "${args.spreadsheetId}", "range": "${args.range}", "valueInputOption": "USER_ENTERED"}' --json '{"values": ${JSON.stringify(args.values)}}'`;
                            const { stdout } = await execPromise(cmd, { env });
                            resultText = stdout;
                        } else if (name === "read_sheet") {
                            const cmd = `${GWS_PATH} sheets +read --spreadsheet ${args.spreadsheetId} --range '${args.range}'`;
                            const { stdout } = await execPromise(cmd, { env });
                            resultText = stdout;
                        } else if (name === "write_to_doc") {
                            const cmd = `${GWS_PATH} docs +write --document ${args.documentId} --text "${args.text}"`;
                            const { stdout } = await execPromise(cmd, { env });
                            resultText = stdout;
                        } else if (name === "send_email") {
                            const cmd = `${GWS_PATH} gmail +send --to "${args.to}" --subject "${args.subject}" --body "${args.body}"`;
                            const { stdout } = await execPromise(cmd, { env });
                            resultText = stdout;
                        } else if (name === "reply_email") {
                            const cmd = `${GWS_PATH} gmail +reply --message-id "${args.messageId}" --body "${args.body}"`;
                            const { stdout } = await execPromise(cmd, { env });
                            resultText = stdout;
                        } else if (name === "triage_emails") {
                            const cmd = `${GWS_PATH} gmail +triage`;
                            const { stdout } = await execPromise(cmd, { env });
                            resultText = stdout;
                        } else if (name === "create_presentation") {
                            const cmd = `${GWS_PATH} slides presentations create --json '{"title": "${args.title}"}'`;
                            const { stdout } = await execPromise(cmd, { env });
                            resultText = stdout;
                        } else if (name === "update_presentation") {
                            const cmd = `${GWS_PATH} slides presentations batchUpdate --params '{"presentationId": "${args.presentationId}"}' --json '{"requests": ${JSON.stringify(args.requests)}}'`;
                            const { stdout } = await execPromise(cmd, { env });
                            resultText = stdout;
                        } else if (name === "add_slide") {
                            const requests = [{
                                createSlide: {
                                    slideLayoutReference: {
                                        predefinedLayout: args.slideLayout
                                    }
                                }
                            }];
                            const cmd = `${GWS_PATH} slides presentations batchUpdate --params '{"presentationId": "${args.presentationId}"}' --json '{"requests": ${JSON.stringify(requests)}}'`;
                            const { stdout } = await execPromise(cmd, { env });
                            resultText = stdout;
                        } else if (name === "add_text_to_slide") {
                            const elementId = `textbox_${Date.now()}`;
                            const requests = [
                                {
                                    createShape: {
                                        objectId: elementId,
                                        shapeType: "TEXT_BOX",
                                        elementProperties: {
                                            pageObjectId: args.slideId,
                                            size: { height: { magnitude: 100, unit: "PT" }, width: { magnitude: 300, unit: "PT" } },
                                            transform: { scaleX: 1, scaleY: 1, translateX: 50, translateY: 50, unit: "PT" }
                                        }
                                    }
                                },
                                {
                                    insertText: {
                                        objectId: elementId,
                                        text: args.text
                                    }
                                }
                            ];
                            const cmd = `${GWS_PATH} slides presentations batchUpdate --params '{"presentationId": "${args.presentationId}"}' --json '{"requests": ${JSON.stringify(requests)}}'`;
                            const { stdout } = await execPromise(cmd, { env });
                            resultText = stdout;
                        } else {
                            throw new Error(`Tool not found: ${name}`);
                        }

                        res.writeHead(200, { "Content-Type": "application/json" });
                        res.end(JSON.stringify({
                            jsonrpc: "2.0",
                            id: parsedBody.id !== undefined ? parsedBody.id : 1,
                            result: {
                                content: [{ type: "text", text: resultText }]
                            }
                        }));
                    } catch (error) {
                        console.error(`Error in tool execution:`, error.message);
                        res.writeHead(200, { "Content-Type": "application/json" });
                        res.end(JSON.stringify({
                            jsonrpc: "2.0",
                            id: parsedBody.id !== undefined ? parsedBody.id : 1,
                            result: {
                                content: [{ type: "text", text: `Error: ${error.message}` }],
                                isError: true
                            }
                        }));
                    }
                    return;
                }
            } catch (e) {
                console.error("Error parsing request body:", e);
            }

            // Fallback to standard SDK handling if not intercepted
            try {
                const transport = new StreamableHTTPServerTransport({
                    sessionIdGenerator: undefined,
                    enableJsonResponse: true
                });

                const mcpServer = new Server({
                    name: "workspace-bridge",
                    version: "1.0.0",
                }, {
                    capabilities: { tools: {} },
                });

                // Define tools again for the SDK
                mcpServer.setRequestHandler(ListToolsRequestSchema, async () => {
                    return {
                        tools: [
                            {
                                name: "create_sheet",
                                description: "Create a new Google Sheet",
                                inputSchema: {
                                    type: "object",
                                    properties: {
                                        title: { type: "string", description: "Title of the sheet" }
                                    },
                                    required: ["title"]
                                }
                            },
                            {
                                name: "append_to_sheet",
                                description: "Append rows to a Google Sheet",
                                inputSchema: {
                                    type: "object",
                                    properties: {
                                        spreadsheetId: { type: "string", description: "The ID of the spreadsheet" },
                                        range: { type: "string", description: "The range to append to" },
                                        values: { type: "array", items: { type: "array", items: { type: "string" } } }
                                    },
                                    required: ["spreadsheetId", "range", "values"]
                                }
                            },
                            {
                                name: "read_sheet",
                                description: "Read values from a spreadsheet",
                                inputSchema: {
                                    type: "object",
                                    properties: {
                                        spreadsheetId: { type: "string", description: "The ID of the spreadsheet" },
                                        range: { type: "string", description: "The range to read" }
                                    },
                                    required: ["spreadsheetId", "range"]
                                }
                            },
                            {
                                name: "write_to_doc",
                                description: "Append text to a Google Doc",
                                inputSchema: {
                                    type: "object",
                                    properties: {
                                        documentId: { type: "string", description: "The ID of the document" },
                                        text: { type: "string", description: "The text to append" }
                                    },
                                    required: ["documentId", "text"]
                                }
                            },
                            {
                                name: "send_email",
                                description: "Send an email via Gmail",
                                inputSchema: {
                                    type: "object",
                                    properties: {
                                        to: { type: "string", description: "Recipient email address" },
                                        subject: { type: "string", description: "Subject of the email" },
                                        body: { type: "string", description: "Body content of the email" }
                                    },
                                    required: ["to", "subject", "body"]
                                }
                            },
                            {
                                name: "reply_email",
                                description: "Reply to an email thread",
                                inputSchema: {
                                    type: "object",
                                    properties: {
                                        messageId: { type: "string", description: "ID of the message to reply to" },
                                        body: { type: "string", description: "Reply body content" }
                                    },
                                    required: ["messageId", "body"]
                                }
                            },
                            {
                                name: "triage_emails",
                                description: "Show unread inbox summary",
                                inputSchema: { type: "object", properties: {} }
                            },
                            {
                                name: "create_presentation",
                                description: "Create a new Google Slides presentation",
                                inputSchema: {
                                    type: "object",
                                    properties: {
                                        title: { type: "string", description: "Title of the presentation" }
                                    },
                                    required: ["title"]
                                }
                            },
                            {
                                name: "update_presentation",
                                description: "Batch update a Google Slides presentation",
                                inputSchema: {
                                    type: "object",
                                    properties: {
                                        presentationId: { type: "string", description: "The ID of the presentation" },
                                        requests: { type: "array", description: "Array of batchUpdate requests" }
                                    },
                                    required: ["presentationId", "requests"]
                                }
                            },
                            {
                                name: "add_slide",
                                description: "Add a new slide to a presentation",
                                inputSchema: {
                                    type: "object",
                                    properties: {
                                        presentationId: { type: "string", description: "The ID of the presentation" },
                                        slideLayout: { type: "string", description: "Layout type (e.g., TITLE_AND_BODY, BLANK)" }
                                    },
                                    required: ["presentationId", "slideLayout"]
                                }
                            },
                            {
                                name: "add_text_to_slide",
                                description: "Add a text box with text to a slide",
                                inputSchema: {
                                    type: "object",
                                    properties: {
                                        presentationId: { type: "string", description: "The ID of the presentation" },
                                        slideId: { type: "string", description: "The ID of the slide" },
                                        text: { type: "string", description: "The text to add" }
                                    },
                                    required: ["presentationId", "slideId", "text"]
                                }
                            }
                        ],
                    };
                });

                mcpServer.setRequestHandler(CallToolRequestSchema, async (request) => {
                    const { name, arguments: args } = request.params;
                    const env = getGwsEnv(req);
                    
                    try {
                        if (name === "create_sheet") {
                            const cmd = `${GWS_PATH} sheets spreadsheets create --json '{"properties": {"title": "${args.title}"}}'`;
                            const { stdout } = await execPromise(cmd, { env });
                            return { content: [{ type: "text", text: stdout }] };
                        }
                        if (name === "append_to_sheet") {
                            const cmd = `${GWS_PATH} sheets spreadsheets values append --params '{"spreadsheetId": "${args.spreadsheetId}", "range": "${args.range}", "valueInputOption": "USER_ENTERED"}' --json '{"values": ${JSON.stringify(args.values)}}'`;
                            const { stdout } = await execPromise(cmd, { env });
                            return { content: [{ type: "text", text: stdout }] };
                        }
                        if (name === "read_sheet") {
                            const cmd = `${GWS_PATH} sheets +read --spreadsheet ${args.spreadsheetId} --range '${args.range}'`;
                            const { stdout } = await execPromise(cmd, { env });
                            return { content: [{ type: "text", text: stdout }] };
                        }
                        if (name === "write_to_doc") {
                            const cmd = `${GWS_PATH} docs +write --document ${args.documentId} --text "${args.text}"`;
                            const { stdout } = await execPromise(cmd, { env });
                            return { content: [{ type: "text", text: stdout }] };
                        }
                        if (name === "send_email") {
                            const cmd = `${GWS_PATH} gmail +send --to "${args.to}" --subject "${args.subject}" --body "${args.body}"`;
                            const { stdout } = await execPromise(cmd, { env });
                            return { content: [{ type: "text", text: stdout }] };
                        }
                        if (name === "reply_email") {
                            const cmd = `${GWS_PATH} gmail +reply --message-id "${args.messageId}" --body "${args.body}"`;
                            const { stdout } = await execPromise(cmd, { env });
                            return { content: [{ type: "text", text: stdout }] };
                        }
                        if (name === "triage_emails") {
                            const cmd = `${GWS_PATH} gmail +triage`;
                            const { stdout } = await execPromise(cmd, { env });
                            return { content: [{ type: "text", text: stdout }] };
                        }
                        if (name === "create_presentation") {
                            const cmd = `${GWS_PATH} slides presentations create --json '{"title": "${args.title}"}'`;
                            const { stdout } = await execPromise(cmd, { env });
                            return { content: [{ type: "text", text: stdout }] };
                        }
                        if (name === "update_presentation") {
                            const cmd = `${GWS_PATH} slides presentations batchUpdate --params '{"presentationId": "${args.presentationId}"}' --json '{"requests": ${JSON.stringify(args.requests)}}'`;
                            const { stdout } = await execPromise(cmd, { env });
                            return { content: [{ type: "text", text: stdout }] };
                        }
                        if (name === "add_slide") {
                            const requests = [{
                                createSlide: {
                                    slideLayoutReference: {
                                        predefinedLayout: args.slideLayout
                                    }
                                }
                            }];
                            const cmd = `${GWS_PATH} slides presentations batchUpdate --params '{"presentationId": "${args.presentationId}"}' --json '{"requests": ${JSON.stringify(requests)}}'`;
                            const { stdout } = await execPromise(cmd, { env });
                            return { content: [{ type: "text", text: stdout }] };
                        }
                        if (name === "add_text_to_slide") {
                            const elementId = `textbox_${Date.now()}`;
                            const requests = [
                                {
                                    createShape: {
                                        objectId: elementId,
                                        shapeType: "TEXT_BOX",
                                        elementProperties: {
                                            pageObjectId: args.slideId,
                                            size: { height: { magnitude: 100, unit: "PT" }, width: { magnitude: 300, unit: "PT" } },
                                            transform: { scaleX: 1, scaleY: 1, translateX: 50, translateY: 50, unit: "PT" }
                                        }
                                    }
                                },
                                {
                                    insertText: {
                                        objectId: elementId,
                                        text: args.text
                                    }
                                }
                            ];
                            const cmd = `${GWS_PATH} slides presentations batchUpdate --params '{"presentationId": "${args.presentationId}"}' --json '{"requests": ${JSON.stringify(requests)}}'`;
                            const { stdout } = await execPromise(cmd, { env });
                            return { content: [{ type: "text", text: stdout }] };
                        }
                        throw new Error(`Tool not found: ${name}`);
                    } catch (error) {
                        return { content: [{ type: "text", text: `Error: ${error.message}` }], isError: true };
                    }
                });

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
                            return { ...target.headers, 'accept': 'application/json, text/event-stream' };
                        }
                        return Reflect.get(target, prop, receiver);
                    }
                });

                await transport.handleRequest(reqProxy, res);
            } catch (error) {
                console.error("Transport error:", error);
                if (!res.headersSent) {
                    res.statusCode = 500;
                    res.end("Internal Server Error");
                }
            }
        });
        return;
    }

    // --- Mock OAuth (Matches BQ pattern) ---
    if (url.pathname === "/auth") {
        const redirect_uri = url.searchParams.get("redirect_uri");
        const state = url.searchParams.get("state");
        res.statusCode = 302;
        res.setHeader("Location", `${redirect_uri}?code=mock_code&state=${state}`);
        res.end();
        return;
    }

    if (url.pathname === "/token") {
        res.setHeader("Content-Type", "application/json");
        res.end(JSON.stringify({
            access_token: "mock_token",
            token_type: "Bearer",
            expires_in: 3600,
            refresh_token: "mock_refresh"
        }));
        return;
    }

    // --- Health Check ---
    if (url.pathname === "/") {
        res.end("Workspace MCP Bridge is active.");
        return;
    }

    res.statusCode = 404;
    res.end("Not Found");
});

const PORT = parseInt(process.env.PORT || "3001"); // Use 3001 to avoid conflict with BQ if running
server.listen(PORT, () => {
    console.error(`Workspace MCP Bridge running on port ${PORT}`);
});
