#!/usr/bin/env node
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';
import { createAtlassianClient } from './utils/http-client.js';
import { confluenceTools } from './confluence/tools.js';
import { jiraTools } from './jira/tools.js';
import { ConfluenceHandlers } from './confluence/handlers.js';
import { JiraHandlers } from './jira/handlers.js';
import { ToolRegistry } from './utils/tool-registry.js';
import { Logger } from './utils/logger.js';
import { createValidator, validators } from './utils/argument-validator.js';
// Get package version from package.json
function getPackageVersion() {
    try {
        const __filename = fileURLToPath(import.meta.url);
        const __dirname = dirname(__filename);
        const packagePath = join(__dirname, '..', 'package.json');
        const packageJson = JSON.parse(readFileSync(packagePath, 'utf-8'));
        return packageJson.version;
    }
    catch (error) {
        Logger.warn('Could not read package.json version, using fallback', {
            error: error instanceof Error ? error : new Error(String(error)),
        });
        return '2.0.2'; // Fallback version
    }
}
// Generate a simple request ID for logging
function generateRequestId() {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}
class AtlassianMCPServer {
    server;
    confluenceHandlers;
    jiraHandlers;
    toolRegistry;
    constructor() {
        const version = getPackageVersion();
        this.server = new Server({
            name: 'mcp-atlassian',
            version,
        }, {
            capabilities: {
                tools: {},
            },
        });
        const client = createAtlassianClient();
        this.confluenceHandlers = new ConfluenceHandlers(client);
        this.jiraHandlers = new JiraHandlers(client);
        this.toolRegistry = new ToolRegistry();
        Logger.info('Initializing Atlassian MCP Server', {
            version,
            environment: process.env.NODE_ENV || 'development',
        });
        this.registerTools();
        this.setupHandlers();
        this.setupErrorHandling();
    }
    registerTools() {
        // Register all Confluence tools
        this.toolRegistry.register({
            name: 'get_confluence_current_user',
            handler: this.confluenceHandlers.getConfluenceCurrentUser.bind(this.confluenceHandlers),
            description: 'Get current Confluence user',
        });
        this.toolRegistry.register({
            name: 'get_confluence_user',
            handler: this.confluenceHandlers.getConfluenceUser.bind(this.confluenceHandlers),
            validator: this.createGetUserValidator(),
            description: 'Get specific Confluence user',
        });
        this.toolRegistry.register({
            name: 'read_confluence_page',
            handler: this.confluenceHandlers.readConfluencePage.bind(this.confluenceHandlers),
            validator: this.createReadPageValidator(),
            description: 'Read Confluence page content',
        });
        // Register other Confluence tools with basic validation
        const confluenceToolsMap = [
            { name: 'search_pages_by_user_involvement', handler: 'searchConfluencePagesByUser' },
            { name: 'list_pages_created_by_user', handler: 'listUserConfluencePages' },
            { name: 'list_attachments_uploaded_by_user', handler: 'listUserConfluenceAttachments' },
            { name: 'search_confluence_pages', handler: 'searchConfluencePages' },
            { name: 'list_confluence_spaces', handler: 'listConfluenceSpaces' },
            { name: 'get_confluence_space', handler: 'getConfluenceSpace' },
            { name: 'list_attachments_on_page', handler: 'listConfluenceAttachments' },
            { name: 'download_confluence_attachment', handler: 'downloadConfluenceAttachment' },
            { name: 'upload_confluence_attachment', handler: 'uploadConfluenceAttachment' },
            { name: 'get_page_with_attachments', handler: 'downloadConfluencePageComplete' },
            { name: 'create_confluence_page', handler: 'createConfluencePage' },
            { name: 'update_confluence_page', handler: 'updateConfluencePage' },
            { name: 'list_confluence_page_children', handler: 'listConfluencePageChildren' },
            { name: 'list_confluence_page_ancestors', handler: 'listConfluencePageAncestors' },
            { name: 'add_confluence_comment', handler: 'addConfluenceComment' },
            { name: 'find_confluence_users', handler: 'findConfluenceUsers' },
            { name: 'list_confluence_page_labels', handler: 'getConfluenceLabels' },
            { name: 'add_confluence_page_label', handler: 'addConfluenceLabels' },
            { name: 'export_confluence_page', handler: 'exportConfluencePage' },
            { name: 'get_my_recent_confluence_pages', handler: 'getMyRecentConfluencePages' },
            { name: 'get_confluence_pages_mentioning_me', handler: 'getConfluencePagesMentioningMe' },
        ];
        confluenceToolsMap.forEach((tool) => {
            this.toolRegistry.register({
                name: tool.name,
                handler: this.confluenceHandlers[tool.handler].bind(this.confluenceHandlers),
                description: `Confluence tool: ${tool.name}`,
            });
        });
        // Register Jira tools
        this.toolRegistry.register({
            name: 'get_jira_current_user',
            handler: this.jiraHandlers.getJiraCurrentUser.bind(this.jiraHandlers),
            description: 'Get current Jira user',
        });
        const jiraToolsMap = [
            { name: 'read_jira_issue', handler: 'readJiraIssue' },
            { name: 'search_jira_issues', handler: 'searchJiraIssues' },
            { name: 'list_jira_projects', handler: 'listJiraProjects' },
            { name: 'create_jira_issue', handler: 'createJiraIssue' },
            { name: 'add_jira_comment', handler: 'addJiraComment' },
            { name: 'list_agile_boards', handler: 'listJiraBoards' },
            { name: 'list_sprints_for_board', handler: 'listJiraSprints' },
            { name: 'get_sprint_details', handler: 'getJiraSprint' },
            { name: 'get_my_current_sprint_issues', handler: 'getMyTasksInCurrentSprint' },
            { name: 'get_my_unresolved_issues', handler: 'getMyOpenIssues' },
            { name: 'get_jira_user', handler: 'getJiraUser' },
            { name: 'search_issues_by_user_involvement', handler: 'searchJiraIssuesByUser' },
            { name: 'list_issues_for_user_role', handler: 'listUserJiraIssues' },
            { name: 'get_user_activity_history', handler: 'getUserJiraActivity' },
            { name: 'get_user_time_tracking', handler: 'getUserJiraWorklog' },
        ];
        jiraToolsMap.forEach((tool) => {
            this.toolRegistry.register({
                name: tool.name,
                handler: this.jiraHandlers[tool.handler].bind(this.jiraHandlers),
                description: `Jira tool: ${tool.name}`,
            });
        });
        Logger.info(`Registered ${this.toolRegistry.getRegisteredTools().length} tools`);
    }
    createGetUserValidator() {
        return createValidator({
            accountId: validators.string('accountId'),
            username: validators.string('username'),
            email: validators.string('email'),
        });
    }
    createReadPageValidator() {
        return createValidator({
            pageId: validators.string('pageId'),
            title: validators.string('title'),
            spaceKey: validators.string('spaceKey'),
            expand: validators.string('expand'),
            format: validators.enum('format', ['storage', 'markdown']),
        });
    }
    setupHandlers() {
        // List available tools
        this.server.setRequestHandler(ListToolsRequestSchema, async () => {
            Logger.debug('Listing available tools');
            return {
                tools: [...confluenceTools, ...jiraTools],
            };
        });
        // Handle tool calls using the registry
        this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
            const requestId = generateRequestId();
            const { name: toolName, arguments: args } = request.params;
            Logger.info(`Tool call received: ${toolName}`, {
                tool: toolName,
                requestId,
                hasArgs: !!args,
            });
            try {
                return await this.toolRegistry.execute(toolName, args, requestId);
            }
            catch (error) {
                Logger.logError('tool-execution-handler', error, {
                    tool: toolName,
                    requestId,
                });
                return {
                    content: [
                        {
                            type: 'text',
                            text: error instanceof Error ? error.message : 'An unknown error occurred',
                        },
                    ],
                    isError: true,
                };
            }
        });
    }
    setupErrorHandling() {
        process.on('uncaughtException', (error) => {
            Logger.error('Uncaught exception - shutting down', {
                error: error,
                errorMessage: error.message,
                errorStack: error.stack,
            });
            process.exit(1);
        });
        process.on('unhandledRejection', (reason, promise) => {
            Logger.error('Unhandled promise rejection - shutting down', {
                reason: reason instanceof Error ? reason.message : String(reason),
                promise: String(promise),
            });
            process.exit(1);
        });
        process.on('SIGINT', () => {
            Logger.info('Received SIGINT - gracefully shutting down');
            process.exit(0);
        });
        process.on('SIGTERM', () => {
            Logger.info('Received SIGTERM - gracefully shutting down');
            process.exit(0);
        });
    }
    async run() {
        try {
            const transport = new StdioServerTransport();
            await this.server.connect(transport);
            const version = getPackageVersion();
            Logger.info('Atlassian MCP server started successfully', {
                version,
                transport: 'stdio',
                toolsRegistered: this.toolRegistry.getRegisteredTools().length,
            });
            // Log to stderr so it doesn't interfere with MCP protocol
            console.error(`Atlassian MCP server v${version} running on stdio`);
        }
        catch (error) {
            Logger.error('Failed to start MCP server', {
                error: error instanceof Error ? error : new Error(String(error)),
                errorMessage: error instanceof Error ? error.message : String(error),
            });
            throw error;
        }
    }
}
const requiredEnvVars = ['ATLASSIAN_BASE_URL', 'ATLASSIAN_EMAIL', 'ATLASSIAN_API_TOKEN'];
for (const envVar of requiredEnvVars) {
    if (!process.env[envVar]) {
        console.error(`Error: Missing required environment variable: ${envVar}`);
        process.exit(1);
    }
}
const server = new AtlassianMCPServer();
server.run().catch((error) => {
    console.error('Failed to start server:', error);
    process.exit(1);
});
//# sourceMappingURL=index.js.map