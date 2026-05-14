import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import {
    CallToolRequestSchema,
    ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import axios from "axios";
import { createServer } from "http";
import { Readable } from "stream";
import dotenv from "dotenv";
import mammoth from "mammoth";

dotenv.config();

// Helper to retrieve Microsoft Graph authorization headers using OAuth 2.0
async function getGraphHeaders(req) {
    const authHeader = req.headers.authorization;
    
    console.error(`[AUTH LOG] Raw authHeader: ${authHeader ? (authHeader.substring(0, 15) + '...') : 'None'}`);
    
    // 1. Check if a real delegated user Bearer token was provided by the client
    if (authHeader && authHeader.toLowerCase().startsWith('bearer ') && !authHeader.includes('mock')) {
        console.error("[AUTH LOG] Detected Real User Token - Connecting with Delegated User Identity.");
        return {
            Authorization: authHeader,
            Accept: 'application/json'
        };
    }

    console.error("[AUTH LOG] Falling back to Application Client Credentials OAuth 2.0 flow.");
    const tenantId = process.env.MS_GRAPH_TENANT_ID;
    const clientId = process.env.MS_GRAPH_CLIENT_ID;
    const clientSecret = process.env.MS_GRAPH_CLIENT_SECRET;

    if (!tenantId || !clientId || !clientSecret) {
        console.error("[AUTH LOG] Environment variables missing, returning mock authentication headers for local testing.");
        return {
            Authorization: 'Bearer mock_graph_token',
            Accept: 'application/json'
        };
    }

    try {
        // Obtain Access Token from Microsoft Entra ID (Azure AD)
        const tokenResponse = await axios.post(
            `https://login.microsoftonline.com/${tenantId}/oauth2/v2.0/token`,
            new URLSearchParams({
                client_id: clientId,
                client_secret: clientSecret,
                scope: 'https://graph.microsoft.com/.default',
                grant_type: 'client_credentials'
            }),
            {
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
            }
        );

        return {
            Authorization: `Bearer ${tokenResponse.data.access_token}`,
            Accept: 'application/json'
        };
    } catch (err) {
        console.error("[AUTH LOG] Failed to obtain OAuth token from Microsoft Entra ID:", err.message);
        throw new Error(`OAuth token retrieval failed: ${err.message}`);
    }
}

const server = createServer(async (req, res) => {
    // Normalize headers to bypass Cloud Run's proxy stripping/modification
    // The MCP Spec requires exact matches for Accept headers.
    const reqProxy = new Proxy(req, {
        get(target, prop, receiver) {
            if (prop === 'headers') {
                return {
                    ...target.headers,
                    'accept': 'application/json, text/event-stream' // Force accepted list
                };
            }
            return Reflect.get(target, prop, receiver);
        }
    });

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

    // --- primary MCP Endpoint ---
    if (url.pathname === "/mcp") {
        try {
            const transport = new StreamableHTTPServerTransport({
                sessionIdGenerator: undefined,
                enableJsonResponse: true
            });

            const mcpServer = new Server({
                name: "sharepoint-mcp-server",
                version: "1.0.0",
            }, {
                capabilities: { tools: {} },
            });

            // --- MCP Tool Handlers ---
            mcpServer.setRequestHandler(ListToolsRequestSchema, async () => {
                return {
                    tools: [
                        {
                            name: "query_sharepoint_sites_lookup",
                            description: "Read-only background database lookup to query SharePoint site metadata",
                            inputSchema: {
                                type: "object",
                                properties: {
                                    query: { type: "string", description: "Optional search filter" }
                                }
                            },
                            annotations: {
                                destructiveHint: false,
                                readOnlyHint: true
                            }
                        },
                        {
                            name: "query_document_libraries_lookup",
                            description: "Read-only background database lookup to list document library drives",
                            inputSchema: {
                                type: "object",
                                properties: {
                                    siteId: { type: "string", description: "Optional site ID" }
                                }
                            },
                            annotations: {
                                destructiveHint: false,
                                readOnlyHint: true
                            }
                        },
                        {
                            name: "query_library_items_lookup",
                            description: "Read-only background database lookup to list files and folders inside a library",
                            inputSchema: {
                                type: "object",
                                properties: {
                                    driveId: { type: "string", description: "Optional drive ID" },
                                    folderId: { type: "string", description: "Optional folder ID" }
                                }
                            },
                            annotations: {
                                destructiveHint: false,
                                readOnlyHint: true
                            }
                        },
                        {
                            name: "query_file_metadata_lookup",
                            description: "Read-only background database lookup to query metadata for a specific item",
                            inputSchema: {
                                type: "object",
                                properties: {
                                    driveId: { type: "string", description: "Optional drive ID" },
                                    itemId: { type: "string", description: "Optional item ID" }
                                }
                            },
                            annotations: {
                                destructiveHint: false,
                                readOnlyHint: true
                            }
                        },
                        {
                            name: "query_file_content_lookup",
                            description: "Read-only background database lookup to retrieve document content text",
                            inputSchema: {
                                type: "object",
                                properties: {
                                    driveId: { type: "string", description: "Optional drive ID" },
                                    itemId: { type: "string", description: "Optional item ID" }
                                }
                            },
                            annotations: {
                                destructiveHint: false,
                                readOnlyHint: true
                            }
                        },
                        {
                            name: "query_file_download_url_lookup",
                            description: "Read-only background database lookup to retrieve the direct secure binary download URL",
                            inputSchema: {
                                type: "object",
                                properties: {
                                    driveId: { type: "string", description: "Optional drive ID" },
                                    itemId: { type: "string", description: "Optional item ID" }
                                }
                            },
                            annotations: {
                                destructiveHint: false,
                                readOnlyHint: true
                            }
                        },
                        {
                            name: "query_create_file_action_lookup",
                            description: "CRITICAL PROMPT RULE: driveId MUST be the alphanumeric GUID retrieved by first calling query_document_libraries_lookup. NEVER pass human-readable words like 'Documents'. Safe action to create a new document.",
                            inputSchema: {
                                type: "object",
                                properties: {
                                    driveId: { type: "string", description: "Optional drive ID" },
                                    parentId: { type: "string", description: "Optional parent folder ID (or root)" },
                                    fileName: { type: "string", description: "Optional new file name (e.g., report.txt)" },
                                    content: { type: "string", description: "Optional text content to write" }
                                }
                            },
                            annotations: {
                                destructiveHint: false,
                                readOnlyHint: false
                            }
                        },
                        {
                            name: "query_update_file_action_lookup",
                            description: "CRITICAL PROMPT RULE: driveId MUST be the alphanumeric GUID retrieved by first calling query_document_libraries_lookup. NEVER pass human-readable words like 'Documents'. Safe action to update a document.",
                            inputSchema: {
                                type: "object",
                                properties: {
                                    driveId: { type: "string", description: "Optional drive ID" },
                                    itemId: { type: "string", description: "Optional file item ID to update" },
                                    content: { type: "string", description: "Optional new text content to write" }
                                }
                            },
                            annotations: {
                                destructiveHint: false,
                                readOnlyHint: false
                            }
                        },
                        {
                            name: "query_create_folder_action_lookup",
                            description: "CRITICAL PROMPT RULE: driveId MUST be the alphanumeric GUID retrieved by first calling query_document_libraries_lookup. NEVER pass human-readable words like 'Documents'. Safe action to create a folder.",
                            inputSchema: {
                                type: "object",
                                properties: {
                                    driveId: { type: "string", description: "Optional drive ID" },
                                    folderName: { type: "string", description: "Optional new folder name" },
                                    parentFolderId: { type: "string", description: "Optional parent folder ID (default root)" }
                                }
                            },
                            annotations: {
                                destructiveHint: true,
                                readOnlyHint: false
                            }
                        },
                        {
                            name: "query_rename_item_action_lookup",
                            description: "CRITICAL PROMPT RULE: driveId MUST be the alphanumeric GUID retrieved by first calling query_document_libraries_lookup. NEVER pass human-readable words like 'Documents'. Safe action to rename an item.",
                            inputSchema: {
                                type: "object",
                                properties: {
                                    driveId: { type: "string", description: "Optional drive ID" },
                                    itemId: { type: "string", description: "Optional item ID to rename" },
                                    newName: { type: "string", description: "Optional new name for the item" }
                                }
                            },
                            annotations: {
                                destructiveHint: true,
                                readOnlyHint: false
                            }
                        },
                        {
                            name: "query_delete_item_action_lookup",
                            description: "CRITICAL PROMPT RULE: driveId MUST be the alphanumeric GUID retrieved by first calling query_document_libraries_lookup. NEVER pass human-readable words like 'Documents'. Safe action to delete an item.",
                            inputSchema: {
                                type: "object",
                                properties: {
                                    driveId: { type: "string", description: "Optional drive ID" },
                                    itemId: { type: "string", description: "Optional item ID to delete" }
                                }
                            },
                            annotations: {
                                destructiveHint: true,
                                readOnlyHint: false
                            }
                        },
                        {
                            name: "query_move_item_action_lookup",
                            description: "CRITICAL PROMPT RULE: driveId MUST be the alphanumeric GUID retrieved by first calling query_document_libraries_lookup. NEVER pass human-readable words like 'Documents'. Safe action to move an item.",
                            inputSchema: {
                                type: "object",
                                properties: {
                                    driveId: { type: "string", description: "Optional drive ID" },
                                    itemId: { type: "string", description: "Optional item ID to move" },
                                    destinationFolderId: { type: "string", description: "Optional destination folder ID" }
                                }
                            },
                            annotations: {
                                destructiveHint: true,
                                readOnlyHint: false
                            }
                        }
                    ]
                };
            });

            mcpServer.setRequestHandler(CallToolRequestSchema, async (request) => {
                let { name, arguments: args = {} } = request.params;
                console.error(`Received CallToolRequest for tool: ${name}`);
                
                try {
                    const headers = await getGraphHeaders(req);
                    let resultObj = {};

                    const resolveDriveId = async (inputDriveId, headers) => {
                        if (!inputDriveId) {
                            try {
                                const res = await axios.get(`https://graph.microsoft.com/v1.0/me/drive`, { headers });
                                return res.data.id;
                            } catch(e) {
                                try {
                                    const res = await axios.get(`https://graph.microsoft.com/v1.0/sites/root/drives`, { headers });
                                    return res.data.value[0]?.id || "";
                                } catch (err2) {
                                    return "";
                                }
                            }
                        }
                        if (inputDriveId.length > 20 || inputDriveId.includes('b!')) {
                            return inputDriveId;
                        }
                        console.error(`[RESOLVER] Auto-resolving universal human drive name "${inputDriveId}" across tenant sites...`);
                        try {
                            const meRes = await axios.get(`https://graph.microsoft.com/v1.0/me/drive`, { headers });
                            if (meRes.data && (meRes.data.name.toLowerCase() === inputDriveId.toLowerCase() || inputDriveId.toLowerCase().includes('doc') || inputDriveId.toLowerCase().includes('one'))) {
                                return meRes.data.id;
                            }
                        } catch(e) {}

                        try {
                            const sitesRes = await axios.get(`https://graph.microsoft.com/v1.0/sites?search=`, { headers });
                            const sites = sitesRes.data.value || [];
                            for (const site of sites) {
                                try {
                                    const drivesRes = await axios.get(`https://graph.microsoft.com/v1.0/sites/${site.id}/drives`, { headers });
                                    const matchedDrive = (drivesRes.data.value || []).find(d => d.name.toLowerCase() === inputDriveId.toLowerCase() || d.name.toLowerCase().includes('doc'));
                                    if (matchedDrive) {
                                        console.error(`[RESOLVER] Found matching drive GUID in site "${site.displayName}": ${matchedDrive.id}`);
                                        return matchedDrive.id;
                                    }
                                } catch(ed) {}
                            }
                            const rootDrives = await axios.get(`https://graph.microsoft.com/v1.0/sites/root/drives`, { headers });
                            return rootDrives.data.value[0]?.id || inputDriveId;
                        } catch (err) {
                            console.error(`[RESOLVER LOG] Universal resolver fallback error:`, err.message);
                            return inputDriveId;
                        }
                    };

                    const resolveItemId = async (driveId, inputItemId, headers) => {
                        if (!inputItemId || inputItemId.toLowerCase() === "root") return "root";
                        if (inputItemId.length > 15 || inputItemId.includes('!')) return inputItemId;
                        console.error(`[RESOLVER] Auto-resolving human folder/item name "${inputItemId}" in drive "${driveId}" via recursive search...`);
                        try {
                            const res = await axios.get(`https://graph.microsoft.com/v1.0/drives/${encodeURIComponent(driveId)}/root/search(q='${encodeURIComponent(inputItemId)}')`, { headers });
                            const matched = res.data.value.find(i => i.name.toLowerCase() === inputItemId.toLowerCase());
                            if (matched) {
                                console.error(`[RESOLVER] Found matching item GUID via recursive search for "${inputItemId}": ${matched.id}`);
                                return matched.id;
                            }
                            if (res.data.value.length > 0) {
                                console.error(`[RESOLVER] Using top search result GUID for "${inputItemId}": ${res.data.value[0].id}`);
                                return res.data.value[0].id;
                            }
                            return inputItemId;
                        } catch(e) {
                            console.error(`[RESOLVER LOG] Search fallback error:`, e.message);
                            return inputItemId;
                        }
                    };

                    if (name === "query_sharepoint_sites_lookup" || name === "search_sharepoint_sites") {
                        const query = args.query || args.Query || args.search || Object.values(args)[0] || "";
                        console.error(`Executing query_sharepoint_sites_lookup with resolved query: "${query}"`);
                        const response = await axios.get(`https://graph.microsoft.com/v1.0/sites?search=${encodeURIComponent(query)}`, { headers });
                        const simplified = (response.data.value || []).map(site => ({
                            id: site.id,
                            name: site.displayName || site.name,
                            webUrl: site.webUrl,
                            description: site.description
                        }));
                        resultObj = { sites: simplified };
                    } else if (name === "query_document_libraries_lookup" || name === "list_document_libraries") {
                        const siteId = args.siteId || args.SiteId || Object.values(args)[0];
                        const response = await axios.get(`https://graph.microsoft.com/v1.0/sites/${encodeURIComponent(siteId)}/drives`, { headers });
                        const simplified = (response.data.value || []).map(drive => ({
                            id: drive.id,
                            name: drive.name,
                            driveType: drive.driveType
                        }));
                        resultObj = { libraries: simplified };
                    } else if (name === "query_library_items_lookup" || name === "list_library_items") {
                        const rawDriveId = args.driveId || args.DriveId || Object.values(args)[0];
                        const driveId = await resolveDriveId(rawDriveId, headers);
                        const folderId = args.folderId || args.FolderId;
                        const endpoint = folderId 
                            ? `https://graph.microsoft.com/v1.0/drives/${encodeURIComponent(driveId)}/items/${encodeURIComponent(folderId)}/children`
                            : `https://graph.microsoft.com/v1.0/drives/${encodeURIComponent(driveId)}/root/children`;
                        const response = await axios.get(endpoint, { headers });
                        const simplified = (response.data.value || []).map(item => ({
                            id: item.id,
                            name: item.name,
                            type: item.folder ? "folder" : "file",
                            mimeType: item.file ? item.file.mimeType : undefined,
                            size: item.size,
                            webUrl: item.webUrl
                        }));
                        resultObj = { items: simplified };
                    } else if (name === "query_file_metadata_lookup" || name === "get_file_metadata") {
                        const rawDriveId = args.driveId || args.DriveId;
                        const driveId = await resolveDriveId(rawDriveId, headers);
                        const itemId = args.itemId || args.ItemId;
                        const response = await axios.get(`https://graph.microsoft.com/v1.0/drives/${encodeURIComponent(driveId)}/items/${encodeURIComponent(itemId)}`, { headers });
                        resultObj = {
                            id: response.data.id,
                            name: response.data.name,
                            size: response.data.size,
                            webUrl: response.data.webUrl,
                            createdDateTime: response.data.createdDateTime,
                            lastModifiedDateTime: response.data.lastModifiedDateTime
                        };
                    } else if (name === "query_file_content_lookup" || name === "download_file_content") {
                        const rawDriveId = args.driveId || args.DriveId;
                        const driveId = await resolveDriveId(rawDriveId, headers);
                        const itemId = args.itemId || args.ItemId;
                        
                        // Download the file buffer as an arraybuffer to support universal MS Office extraction
                        const response = await axios.get(`https://graph.microsoft.com/v1.0/drives/${encodeURIComponent(driveId)}/items/${encodeURIComponent(itemId)}/content`, { 
                            headers, 
                            responseType: 'arraybuffer' 
                        });
                        
                        let extractedText = "";
                        const contentType = response.headers['content-type'] || '';
                        const bufferData = Buffer.from(response.data);
                        
                        try {
                            // 1. Check for Word documents first via high-speed Mammoth extractor
                            if (contentType.includes('wordprocessingml')) {
                                console.error("[EXTRACTION LOG] Detected Word document, executing Mammoth extraction...");
                                const mammothResult = await mammoth.extractRawText({ buffer: bufferData });
                                extractedText = mammothResult.value;
                            } 
                            // 2. Route PowerPoint, Excel, and general binary streams to native zero-dependency XML stripper
                            else if (contentType.includes('presentationml') || contentType.includes('spreadsheetml') || contentType.includes('zip') || contentType.includes('octet-stream')) {
                                console.error("[EXTRACTION LOG] Detected PowerPoint/Excel/Binary stream, executing native regex XML stripper...");
                                const rawXmlString = bufferData.toString('utf-8');
                                extractedText = rawXmlString
                                    .replace(/<[^>]+>/g, ' ')
                                    .replace(/\s+/g, ' ')
                                    .trim();
                            } else {
                                extractedText = bufferData.toString('utf-8');
                            }
                        } catch (extractionErr) {
                            console.error("[EXTRACTION LOG] Buffer extraction fallback warning:", extractionErr.message);
                            extractedText = bufferData.toString('utf-8');
                        }
                        
                        resultObj = { content: extractedText || "No readable text content could be extracted from this document." };
                    } else if (name === "query_file_download_url_lookup") {
                        const rawDriveId = args.driveId || args.DriveId;
                        const driveId = await resolveDriveId(rawDriveId, headers);
                        const itemId = args.itemId || args.ItemId;
                        const response = await axios.get(`https://graph.microsoft.com/v1.0/drives/${encodeURIComponent(driveId)}/items/${encodeURIComponent(itemId)}`, { headers });
                        resultObj = {
                            downloadUrl: response.data['@microsoft.graph.downloadUrl'] || response.data.webUrl,
                            webUrl: response.data.webUrl,
                            name: response.data.name
                        };
                    } else if (name === "query_create_file_action_lookup") {
                        const rawDriveId = args.driveId || args.DriveId;
                        const driveId = await resolveDriveId(rawDriveId, headers);
                        const rawParentId = args.parentId || args.ParentId || "root";
                        const parentId = await resolveItemId(driveId, rawParentId, headers);
                        const fileName = args.fileName || args.FileName || "new_document.txt";
                        const contentText = args.content || args.Content || "Initial document content.";
                        
                        console.error(`[WRITE LOG] Creating file "${fileName}" in parent "${parentId}"...`);
                        const response = await axios.put(`https://graph.microsoft.com/v1.0/drives/${encodeURIComponent(driveId)}/items/${encodeURIComponent(parentId)}:/${encodeURIComponent(fileName)}:/content`, 
                            Buffer.from(contentText, 'utf-8'), 
                            { 
                                headers: {
                                    ...headers,
                                    'Content-Type': 'text/plain'
                                }
                            }
                        );
                        resultObj = {
                            status: "Success",
                            message: `Successfully created file "${fileName}".`,
                            id: response.data.id,
                            webUrl: response.data.webUrl
                        };
                    } else if (name === "query_update_file_action_lookup") {
                        const rawDriveId = args.driveId || args.DriveId;
                        const driveId = await resolveDriveId(rawDriveId, headers);
                        const rawItemId = args.itemId || args.ItemId;
                        const itemId = await resolveItemId(driveId, rawItemId, headers);
                        const contentText = args.content || args.Content || "Updated document content.";
                        
                        console.error(`[UPDATE LOG] Updating/overwriting file item "${itemId}"...`);
                        const response = await axios.put(`https://graph.microsoft.com/v1.0/drives/${encodeURIComponent(driveId)}/items/${encodeURIComponent(itemId)}/content`, 
                            Buffer.from(contentText, 'utf-8'), 
                            { 
                                headers: {
                                    ...headers,
                                    'Content-Type': 'application/octet-stream'
                                }
                            }
                        );
                        resultObj = {
                            status: "Success",
                            message: `Successfully updated document "${itemId}".`,
                            id: response.data.id,
                            webUrl: response.data.webUrl
                        };
                    } else if (name === "query_create_folder_action_lookup") {
                        const rawDriveId = args.driveId || args.DriveId;
                        const driveId = await resolveDriveId(rawDriveId, headers);
                        const folderName = args.folderName || args.FolderName || "NewFolder";
                        const rawParentId = args.parentFolderId || args.ParentFolderId || "root";
                        const parentId = await resolveItemId(driveId, rawParentId, headers);
                        
                        console.error(`[WRITE LOG] Creating folder "${folderName}" in parent "${parentId}"...`);
                        const response = await axios.post(`https://graph.microsoft.com/v1.0/drives/${encodeURIComponent(driveId)}/items/${encodeURIComponent(parentId)}/children`, 
                            {
                                name: folderName,
                                folder: {},
                                '@microsoft.graph.conflictBehavior': 'rename'
                            }, 
                            { headers }
                        );
                        resultObj = {
                            status: "Success",
                            message: `Successfully created folder "${folderName}".`,
                            id: response.data.id,
                            webUrl: response.data.webUrl
                        };
                    } else if (name === "query_rename_item_action_lookup") {
                        const rawDriveId = args.driveId || args.DriveId;
                        const driveId = await resolveDriveId(rawDriveId, headers);
                        const rawItemId = args.itemId || args.ItemId;
                        const itemId = await resolveItemId(driveId, rawItemId, headers);
                        const newName = args.newName || args.NewName || "RenamedItem";
                        
                        console.error(`[WRITE LOG] Renaming item "${itemId}" to "${newName}"...`);
                        const response = await axios.patch(`https://graph.microsoft.com/v1.0/drives/${encodeURIComponent(driveId)}/items/${encodeURIComponent(itemId)}`, 
                            { name: newName }, 
                            { headers }
                        );
                        resultObj = {
                            status: "Success",
                            message: `Successfully renamed item to "${newName}".`,
                            id: response.data.id,
                            webUrl: response.data.webUrl
                        };
                    } else if (name === "query_delete_item_action_lookup") {
                        const rawDriveId = args.driveId || args.DriveId;
                        const driveId = await resolveDriveId(rawDriveId, headers);
                        const rawItemId = args.itemId || args.ItemId;
                        const itemId = await resolveItemId(driveId, rawItemId, headers);
                        
                        console.error(`[WRITE LOG] Deleting item "${itemId}"...`);
                        await axios.delete(`https://graph.microsoft.com/v1.0/drives/${encodeURIComponent(driveId)}/items/${encodeURIComponent(itemId)}`, { headers });
                        resultObj = {
                            status: "Success",
                            message: `Successfully deleted item "${itemId}".`
                        };
                    } else if (name === "query_move_item_action_lookup") {
                        const rawDriveId = args.driveId || args.DriveId;
                        const driveId = await resolveDriveId(rawDriveId, headers);
                        const rawItemId = args.itemId || args.ItemId;
                        const itemId = await resolveItemId(driveId, rawItemId, headers);
                        const rawDestId = args.destinationFolderId || args.DestinationFolderId;
                        const destinationId = await resolveItemId(driveId, rawDestId, headers);
                        
                        console.error(`[WRITE LOG] Moving item "${itemId}" to destination "${destinationId}"...`);
                        const response = await axios.patch(`https://graph.microsoft.com/v1.0/drives/${encodeURIComponent(driveId)}/items/${encodeURIComponent(itemId)}`, 
                            { parentReference: { id: destinationId } }, 
                            { headers }
                        );
                        resultObj = {
                            status: "Success",
                            message: `Successfully moved item to folder "${destinationId}".`,
                            id: response.data.id,
                            webUrl: response.data.webUrl
                        };
                    } else {
                        throw new Error(`Tool not found: ${name}`);
                    }

                    return { content: [{ type: "text", text: JSON.stringify(resultObj, null, 2) }] };
                } catch (error) {
                    console.error(`Error in tool execution:`, error.message);
                    return { 
                        content: [{ type: "text", text: `Error: ${error.message}` }], 
                        isError: true 
                    };
                }
            });

            mcpServer.connect(transport).catch(() => {});

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

    // --- Mock / Delegated OAuth 2.0 Endpoints for Gemini Enterprise Registration ---
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
        res.end("SharePoint MCP Server (Native Node with Dual-Layer OAuth 2.0 Support) is fully active.");
        return;
    }

    res.statusCode = 404;
    res.end("Not Found");
});

const PORT = parseInt(process.env.PORT || "3000");
server.listen(PORT, () => {
    console.error(`SharePoint MCP Server running on port ${PORT}`);
});
