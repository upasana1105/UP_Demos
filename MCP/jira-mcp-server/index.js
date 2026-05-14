import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import {
    CallToolRequestSchema,
    ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import axios from "axios";
import { createServer } from "http";
import dotenv from "dotenv";

dotenv.config();

const JIRA_BASE_URL = process.env.ATLASSIAN_BASE_URL;
const JIRA_EMAIL = process.env.ATLASSIAN_EMAIL;
const JIRA_TOKEN = process.env.ATLASSIAN_API_TOKEN;

const auth = Buffer.from(`${JIRA_EMAIL}:${JIRA_TOKEN}`).toString("base64");
const jiraHeaders = {
    Authorization: `Basic ${auth}`,
    Accept: "application/json",
};



const server = createServer(async (req, res) => {
    // 1. Normalize headers (Cloud Run might change casing/content)
    // The MCP Spec requires exact matches for Accept headers.
    // Cloud Run proxies sometimes mangle these. We will forcefully inject them to bypass strict checks.

    // Create a proxy request object for the transport that guarantees the required headers
    const reqProxy = new Proxy(req, {
        get(target, prop, receiver) {
            if (prop === 'headers') {
                return {
                    ...target.headers,
                    'accept': 'application/json, text/event-stream' // Force accept list
                };
            }
            return Reflect.get(target, prop, receiver);
        }
    });

    res.setHeader("Access-Control-Allow-Origin", "*");
    res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS, DELETE");
    res.setHeader("Access-Control-Allow-Headers", "Content-Type, Mcp-Session-Id, Mcp-Protocol-Version, Authorization, Accept");

    if (req.method === "OPTIONS") {
        res.statusCode = 204;
        res.end();
        return;
    }

    const host = req.headers.host || 'localhost';
    const url = new URL(req.url, `http://${host}`);

    // --- MCP Endpoint ---
    if (url.pathname === "/mcp") {
        try {
            // Instantiate a fresh transport per request to satisfy stateless requirements
            const transport = new StreamableHTTPServerTransport({
                sessionIdGenerator: undefined,
                enableJsonResponse: true
            });

            // Instantiate a fresh Server per request to avoid "Already connected" error
            const mcpServer = new Server({
                name: "jira-mcp-server-cloud",
                version: "1.1.6",
            }, {
                capabilities: { tools: {} },
            });

            // --- MCP Tool Handlers ---
            mcpServer.setRequestHandler(ListToolsRequestSchema, async () => {
                return {
                    tools: [
                        {
                            name: "get_jira_current_user",
                            description: "Get current authenticated Jira user details",
                            inputSchema: { type: "object", properties: {} },
                        },
                        {
                            name: "list_jira_projects",
                            description: "List accessible Jira projects",
                            inputSchema: { type: "object", properties: {} },
                        },
                        {
                            name: "get_jira_issue",
                            description: "Get details of a specific Jira issue",
                            inputSchema: {
                                type: "object",
                                properties: {
                                    issueIdOrKey: { type: "string", description: "The ID or key of the issue (e.g., TEAM-123)" }
                                },
                                required: ["issueIdOrKey"]
                            },
                        },
                        {
                            name: "search_jira_issues",
                            description: "Search for Jira issues using JQL",
                            inputSchema: {
                                type: "object",
                                properties: {
                                    jql: { type: "string", description: "Jira Query Language (JQL) string" }
                                },
                                required: ["jql"]
                            },
                        },
                        {
                            name: "create_jira_issue",
                            description: "Create a new Jira issue",
                            inputSchema: {
                                type: "object",
                                properties: {
                                    projectKey: { type: "string", description: "Project key (e.g., TEST)" },
                                    summary: { type: "string", description: "Issue summary" },
                                    description: { type: "string", description: "Issue description" },
                                    issueType: { type: "string", description: "Issue type (e.g., Task, Bug)" }
                                },
                                required: ["projectKey", "summary", "issueType"]
                            },
                        }
                    ],
                };
            });

            mcpServer.setRequestHandler(CallToolRequestSchema, async (request) => {
                const { name, arguments: args } = request.params;
                console.error(`Received CallToolRequest for tool: ${name}`);
                try {
                    if (name === "get_jira_current_user") {
                        const response = await axios.get(`${JIRA_BASE_URL}/rest/api/3/myself`, { headers: jiraHeaders });
                        return { content: [{ type: "text", text: JSON.stringify(response.data, null, 2) }] };
                    }
                    if (name === "list_jira_projects") {
                        console.error(`Executing axios.get to Jira API for list_jira_projects...`);
                        const response = await axios.get(`${JIRA_BASE_URL}/rest/api/3/project`, { headers: jiraHeaders });
                        console.error(`Jira API list_jira_projects success, returning response.`);
                        return { content: [{ type: "text", text: JSON.stringify(response.data, null, 2) }] };
                    }
                    if (name === "get_jira_issue") {
                        const { issueIdOrKey } = args;
                        const response = await axios.get(`${JIRA_BASE_URL}/rest/api/3/issue/${issueIdOrKey}`, { headers: jiraHeaders });
                        return { content: [{ type: "text", text: JSON.stringify(response.data, null, 2) }] };
                    }
                    if (name === "search_jira_issues") {
                        const { jql } = args;
                        const response = await axios.post(`${JIRA_BASE_URL}/rest/api/3/search/jql`, {
                            jql,
                            fields: ["*all"]
                        }, { headers: jiraHeaders });
                        return { content: [{ type: "text", text: JSON.stringify(response.data, null, 2) }] };
                    }
                    if (name === "create_jira_issue") {
                        const { projectKey, summary, description, issueType } = args;
                        const payload = {
                            fields: {
                                project: { key: projectKey },
                                summary: summary,
                                description: {
                                    type: "doc",
                                    version: 1,
                                    content: [
                                        {
                                            type: "paragraph",
                                            content: [
                                                { type: "text", text: description || "" }
                                            ]
                                        }
                                    ]
                                },
                                issuetype: { name: issueType }
                            }
                        };
                        const response = await axios.post(`${JIRA_BASE_URL}/rest/api/3/issue`, payload, { headers: jiraHeaders });
                        return { content: [{ type: "text", text: JSON.stringify(response.data, null, 2) }] };
                    }
                    throw new Error(`Tool not found: ${name}`);
                } catch (error) {
                    console.error(`Error in tool execution:`, error.message);
                    if (error.response) {
                        console.error(`Jira API error response:`, error.response.status, JSON.stringify(error.response.data));
                    }
                    return { content: [{ type: "text", text: `Error: ${error.message} \n ${error.response ? JSON.stringify(error.response.data) : ''}` }], isError: true };
                }
            });

            mcpServer.connect(transport).catch(error => console.error("MCP Connect Error:", error));

            // Using proxy request to bypass strict Accept header validation
            await transport.handleRequest(reqProxy, res);
        } catch (error) {
            console.error("Transport error:", error);
            if (!res.headersSent) {
                res.statusCode = 500;
                res.end("Internal Server Error: " + error.message);
            }
        }
        return;
    }

    // --- Mock OAuth ---
    if (url.pathname === "/auth") {
        const redirect_uri = url.searchParams.get("redirect_uri");
        const state = url.searchParams.get("state");
        res.statusCode = 302;
        res.setHeader("Location", `${redirect_uri}?code=mock&state=${state}`);
        res.end();
        return;
    }

    if (url.pathname === "/token") {
        res.setHeader("Content-Type", "application/json");
        res.end(JSON.stringify({
            access_token: "mock",
            token_type: "Bearer",
            expires_in: 3600,
            refresh_token: "mock_refresh"
        }));
        return;
    }

    // --- Health Check ---
    if (url.pathname === "/") {
        res.end("Jira MCP Server (Native Node with Header Proxy) is active.");
        return;
    }

    res.statusCode = 404;
    res.end("Not Found");
});

const PORT = parseInt(process.env.PORT || "3000");
server.listen(PORT, () => {
    console.error(`Server running on port ${PORT}`);
});
