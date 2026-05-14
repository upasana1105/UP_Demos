import express from "express";
import snowflake from "snowflake-sdk";
import axios from "axios";
import dotenv from "dotenv";

dotenv.config();

const app = express();
app.use(express.json()); // Automatically parses JSON body!
app.use(express.urlencoded({ extended: true })); // Automatically parses URL-encoded body!

// Helper to create Snowflake connection using OAuth or Fallback
const getSnowflakeConnection = (req) => {
    const authHeader = req.headers.authorization;
    
    if (authHeader && authHeader.startsWith('Bearer ') && authHeader !== 'Bearer mock_snowflake_token') {
        const token = authHeader.substring(7);
        console.error("Using provided OAuth token from Vertex AI for Snowflake connection");
        return snowflake.createConnection({
            account: process.env.SNOWFLAKE_ACCOUNT,
            authenticator: 'OAUTH',
            token: token,
            warehouse: process.env.SNOWFLAKE_WAREHOUSE || 'COMPUTE_WH',
            database: process.env.SNOWFLAKE_DATABASE || 'SNOWFLAKE_LEARNING_DB',
            schema: process.env.SNOWFLAKE_SCHEMA || 'PUBLIC'
        });
    }

    console.error("Falling back to service account credentials for Snowflake");
    return snowflake.createConnection({
        account: process.env.SNOWFLAKE_ACCOUNT,
        username: process.env.SNOWFLAKE_USER,
        password: process.env.SNOWFLAKE_PASSWORD,
        warehouse: process.env.SNOWFLAKE_WAREHOUSE || 'COMPUTE_WH',
        database: process.env.SNOWFLAKE_DATABASE || 'SNOWFLAKE_LEARNING_DB',
        schema: process.env.SNOWFLAKE_SCHEMA || 'PUBLIC'
    });
};

// Query helper
const executeQuery = (connection, sqlText) => {
    return new Promise((resolve, reject) => {
        connection.connect((err, conn) => {
            if (err) {
                return reject(new Error('Unable to connect: ' + err.message));
            }
            conn.execute({
                sqlText: sqlText,
                complete: (err, stmt, rows) => {
                    if (err) {
                        return reject(new Error('Failed to execute query: ' + err.message));
                    }
                    resolve(rows);
                }
            });
        });
    });
};

// --- MCP Hub Endpoint (Pure Express!) ---
app.post("/mcp", async (req, res) => {
    const { method, params } = req.body;
    
    console.error(`🔍 Inbound MCP Method: [${method}]`);
    console.error(`📦 Inbound MCP Body: ${JSON.stringify(req.body)}`);

    if (method === "initialize") {
        return res.json({
            jsonrpc: "2.0",
            id: req.body.id || 0,
            result: {
                protocolVersion: "2024-11-05", // Standard stable MCP protocol version
                capabilities: {
                    tools: {} // Tell Vertex we support Tools!
                },
                serverInfo: {
                    name: "snowflake-mcp-proxy",
                    version: "1.0.0"
                }
            }
        });
    }

    if (method === "tools/list") {
        return res.json({
            jsonrpc: "2.0",
            id: req.body.id || 1,
            result: {
                tools: [
                    {
                        name: "execute_sql",
                        description: "Execute a standard SQL query against Snowflake",
                        inputSchema: {
                            type: "object",
                            properties: {
                                query: { type: "string", description: "The SQL query to execute" }
                            },
                            required: ["query"]
                        }
                    },
                    {
                        name: "list_tables",
                        description: "List tables in a specific database schema",
                        inputSchema: {
                            type: "object",
                            properties: {
                                database: { type: "string", description: "The database name (optional, defaults to session database)" },
                                schema: { type: "string", description: "The schema name (optional, defaults to public)" }
                            }
                        }
                    },
                    {
                        name: "cortex_search",
                        description: "Use Snowflake Cortex Analyst to query data using natural language (requires a semantic model yaml file)",
                        inputSchema: {
                            type: "object",
                            properties: {
                                question: { type: "string", description: "The plain English question you want to ask Cortex Analyst" },
                                semantic_model_file: { type: "string", description: "Path to your uploaded YAML model file in a Snowflake stage (e.g. @MY_STAGE/sales_model.yaml)" }
                            },
                            required: ["question", "semantic_model_file"]
                        }
                    }
                ]
            }
        });
    }

    if (method === "tools/call") {
        const { name, arguments: args } = params;
        const connection = getSnowflakeConnection(req);

        try {
            if (name === "execute_sql") {
                const rows = await executeQuery(connection, args.query);
                return res.json({
                    jsonrpc: "2.0",
                    id: req.body.id || 1,
                    result: {
                        content: [{ type: "text", text: JSON.stringify(rows, null, 2) }]
                    }
                });
            }
            if (name === "list_tables") {
                const db = args.database || process.env.SNOWFLAKE_DATABASE || "SNOWFLAKE_LEARNING_DB";
                const schema = args.schema || "PUBLIC";
                const rows = await executeQuery(connection, `SHOW TABLES IN SCHEMA ${db}.${schema}`);
                const result = rows.map(r => r.name || r.NAME || r.target_name);
                return res.json({
                    jsonrpc: "2.0",
                    id: req.body.id || 1,
                    result: {
                        content: [{ type: "text", text: JSON.stringify(result, null, 2) }]
                    }
                });
            }

            if (name === "cortex_search") {
                const token = req.headers.authorization;
                if (!token) throw new Error("Missing authorization token for Cortex Analyst REST call");

                const account = process.env.SNOWFLAKE_ACCOUNT;
                const url = `https://${account}.snowflakecomputing.com/api/v2/cortex/analyst/execute`;

                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Authorization': token,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        messages: [{ role: "user", content: [{ type: "text", text: args.question }] }],
                        semantic_model_file: args.semantic_model_file
                    })
                });

                if (!response.ok) {
                    const errorText = await response.text();
                    throw new Error(`Cortex Analyst API failed with status ${response.status}: ${errorText}`);
                }

                const data = await response.json();
                return res.json({
                    jsonrpc: "2.0",
                    id: req.body.id || 1,
                    result: {
                        content: [{ type: "text", text: JSON.stringify(data, null, 2) }]
                    }
                });
            }
            throw new Error(`Tool not found: ${name}`);
        } catch (error) {
            console.error("Tool execution failed:", error.message);
            return res.json({
                jsonrpc: "2.0",
                id: req.body.id || 1,
                result: {
                    content: [{ type: "text", text: `Error: ${error.message}` }],
                    isError: true
                }
            });
        }
    }

    res.status(404).json({ 
        error: "Method not supported", 
        receivedMethod: method, 
        receivedBody: req.body 
    });
});

// --- Real OAuth Auth/Token Handlers ---
app.get("/auth", (req, res) => {
    const state = req.query.state;
    const redirect_uri = req.query.redirect_uri || 'https://vertexaisearch.cloud.google.com/oauth-redirect';

    const snowflakeAuthUrl = `https://${process.env.SNOWFLAKE_ACCOUNT}.snowflakecomputing.com/oauth/authorize` +
        `?client_id=${encodeURIComponent(process.env.SNOWFLAKE_CLIENT_ID)}` +
        `&response_type=code` +
        `&redirect_uri=${encodeURIComponent(redirect_uri)}` +
        `&state=${encodeURIComponent(state)}`;

    res.redirect(snowflakeAuthUrl);
});

app.post("/token", async (req, res) => {
    const code = req.body.code;
    const redirect_uri = req.body.redirect_uri || 'https://vertexaisearch.cloud.google.com/oauth-redirect';

    try {
        const credentials = `${process.env.SNOWFLAKE_CLIENT_ID}:${process.env.SNOWFLAKE_CLIENT_SECRET}`;
        const base64Credentials = Buffer.from(credentials).toString('base64');

        const response = await axios.post(
            `https://${process.env.SNOWFLAKE_ACCOUNT}.snowflakecomputing.com/oauth/token-request`,
            new URLSearchParams({
                grant_type: 'authorization_code',
                code: code,
                redirect_uri: redirect_uri
            }),
            {
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Authorization': `Basic ${base64Credentials}`
                }
            }
        );

        res.json({
            ...response.data,
            refresh_token: response.data.refresh_token || "mock_snowflake_refresh_token"
        });
    } catch (error) {
        console.error(`Token Exchange Failed: ${JSON.stringify(error.response ? error.response.data : error.message)}`);
        res.status(error.response ? error.response.status : 500).json({ error: error.message });
    }
});

// --- Health Check ---
app.get("/", (req, res) => {
    res.send("Bulletproof Snowflake Pure-Express Library active.");
});

const PORT = parseInt(process.env.PORT || "8080");
app.listen(PORT, '0.0.0.0', () => {
    console.error(`Pure Express Snowflake Proxy running on port ${PORT}`);
});
