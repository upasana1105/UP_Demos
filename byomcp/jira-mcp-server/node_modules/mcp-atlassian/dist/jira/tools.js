export const jiraTools = [
    {
        name: 'get_jira_current_user',
        description: 'Get details of the authenticated Jira user. Returns information about the current user including account ID, display name, email, and avatar URLs.',
        inputSchema: {
            type: 'object',
            properties: {},
        },
    },
    {
        name: 'get_jira_user',
        description: 'Get details for a specific Jira user by username, account ID, or email. Returns user profile information.',
        inputSchema: {
            type: 'object',
            properties: {
                username: {
                    type: 'string',
                    description: 'The username to search for.',
                },
                accountId: {
                    type: 'string',
                    description: 'The Atlassian account ID of the user.',
                },
                email: {
                    type: 'string',
                    description: 'The email address of the user.',
                },
            },
        },
    },
    {
        name: 'search_issues_by_user_involvement',
        description: 'Search for issues based on how a specific user is involved (assignee, reporter, creator, watcher, or any). Provides comprehensive filtering to find all issues a user is connected to.',
        inputSchema: {
            type: 'object',
            properties: {
                username: {
                    type: 'string',
                    description: 'The username of the user (alternative to accountId).',
                },
                accountId: {
                    type: 'string',
                    description: 'The Atlassian account ID of the user.',
                },
                searchType: {
                    type: 'string',
                    enum: ['assignee', 'reporter', 'creator', 'watcher', 'all'],
                    description: 'Type of user involvement to search for.',
                },
                projectKeys: {
                    type: 'array',
                    items: { type: 'string' },
                    description: 'Optional list of project keys to filter results.',
                },
                status: {
                    type: 'string',
                    description: 'Filter by issue status (e.g., "Open", "In Progress", "Done").',
                },
                issueType: {
                    type: 'string',
                    description: 'Filter by issue type (e.g., "Bug", "Task", "Story").',
                },
                maxResults: {
                    type: 'number',
                    description: 'The maximum number of issues to return. Default is 50, maximum is 100.',
                    default: 50,
                    minimum: 1,
                    maximum: 100,
                },
                startAt: {
                    type: 'number',
                    description: 'The starting index for pagination. Default is 0.',
                    default: 0,
                },
            },
            required: ['searchType'],
        },
    },
    {
        name: 'list_issues_by_user_role',
        description: 'List issues where a user has a specific role (assignee, reporter, or creator). Includes date filtering for finding issues within specific time periods.',
        inputSchema: {
            type: 'object',
            properties: {
                username: {
                    type: 'string',
                    description: 'The username of the user (alternative to accountId).',
                },
                accountId: {
                    type: 'string',
                    description: 'The Atlassian account ID of the user.',
                },
                role: {
                    type: 'string',
                    enum: ['assignee', 'reporter', 'creator'],
                    description: 'The role of the user in relation to the issues.',
                },
                projectKeys: {
                    type: 'array',
                    items: { type: 'string' },
                    description: 'Optional list of project keys to filter results.',
                },
                startDate: {
                    type: 'string',
                    description: 'Start date for filtering issues (format: YYYY-MM-DD).',
                },
                endDate: {
                    type: 'string',
                    description: 'End date for filtering issues (format: YYYY-MM-DD).',
                },
                maxResults: {
                    type: 'number',
                    description: 'The maximum number of issues to return. Default is 50, maximum is 100.',
                    default: 50,
                    minimum: 1,
                    maximum: 100,
                },
                startAt: {
                    type: 'number',
                    description: 'The starting index for pagination. Default is 0.',
                    default: 0,
                },
            },
            required: ['role'],
        },
    },
    {
        name: 'get_user_activity_history',
        description: 'Get a stream of recent user activity, such as issue comments, status changes, and field updates. Can filter by activity type and project.',
        inputSchema: {
            type: 'object',
            properties: {
                username: {
                    type: 'string',
                    description: 'The username of the user (alternative to accountId).',
                },
                accountId: {
                    type: 'string',
                    description: 'The Atlassian account ID of the user.',
                },
                activityType: {
                    type: 'string',
                    enum: ['comments', 'transitions', 'all'],
                    description: 'Type of activity to retrieve. Default is "all".',
                    default: 'all',
                },
                projectKeys: {
                    type: 'array',
                    items: { type: 'string' },
                    description: 'Optional list of project keys to filter results.',
                },
                days: {
                    type: 'number',
                    description: 'Number of days to look back for activity. Default is 30.',
                    default: 30,
                    minimum: 1,
                    maximum: 365,
                },
                maxResults: {
                    type: 'number',
                    description: 'The maximum number of activities to return. Default is 50, maximum is 100.',
                    default: 50,
                    minimum: 1,
                    maximum: 100,
                },
                startAt: {
                    type: 'number',
                    description: 'The starting index for pagination. Default is 0.',
                    default: 0,
                },
            },
        },
    },
    {
        name: 'get_user_time_tracking',
        description: 'Retrieve time tracking work logs (worklogs) for a specific user. Shows all time entries logged by the user within a date range, useful for timesheet and worklog reporting.',
        inputSchema: {
            type: 'object',
            properties: {
                username: {
                    type: 'string',
                    description: 'The username of the user (alternative to accountId).',
                },
                accountId: {
                    type: 'string',
                    description: 'The Atlassian account ID of the user.',
                },
                startDate: {
                    type: 'string',
                    description: 'Start date for filtering worklogs (format: YYYY-MM-DD).',
                },
                endDate: {
                    type: 'string',
                    description: 'End date for filtering worklogs (format: YYYY-MM-DD).',
                },
                projectKeys: {
                    type: 'array',
                    items: { type: 'string' },
                    description: 'Optional list of project keys to filter results.',
                },
                maxResults: {
                    type: 'number',
                    description: 'The maximum number of worklogs to return. Default is 50, maximum is 100.',
                    default: 50,
                    minimum: 1,
                    maximum: 100,
                },
                startAt: {
                    type: 'number',
                    description: 'The starting index for pagination. Default is 0.',
                    default: 0,
                },
            },
        },
    },
    {
        name: 'read_jira_issue',
        description: 'Retrieves detailed information about a specific Jira issue, including its fields, status, and transitions. Use this to get the full picture of a single issue.',
        inputSchema: {
            type: 'object',
            properties: {
                issueKey: {
                    type: 'string',
                    description: 'The unique identifier for the Jira issue (e.g., "PROJ-123").',
                },
                expand: {
                    type: 'string',
                    description: 'A comma-separated list of additional properties to expand. Common options include `fields`, `transitions`, and `changelog`.',
                    default: 'fields,transitions,changelog',
                },
            },
            required: ['issueKey'],
        },
    },
    {
        name: 'search_jira_issues',
        description: 'Searches for Jira issues using Jira Query Language (JQL). This is the primary way to find issues that match specific criteria.',
        inputSchema: {
            type: 'object',
            properties: {
                jql: {
                    type: 'string',
                    description: 'A JQL query string. For example, to find all open issues in project "PROJ", use: `project = PROJ AND status = Open`.',
                },
                maxResults: {
                    type: 'number',
                    description: 'The maximum number of issues to return. Default is 50, maximum is 100.',
                    default: 50,
                    minimum: 1,
                    maximum: 100,
                },
                startAt: {
                    type: 'number',
                    description: 'The starting index for pagination. Default is 0.',
                    default: 0,
                },
                fields: {
                    type: 'string',
                    description: 'A comma-separated list of fields to include for each issue in the response. By default, it returns all fields (`*all`).',
                    default: '*all',
                },
            },
            required: ['jql'],
        },
    },
    {
        name: 'list_jira_projects',
        description: 'Lists all Jira projects that the user has permission to view. This is useful for discovering available projects to work with.',
        inputSchema: {
            type: 'object',
            properties: {
                expand: {
                    type: 'string',
                    description: 'A comma-separated list of properties to expand for each project. Common options are `description`, `lead`, and `issueTypes`.',
                    default: 'description,lead,issueTypes',
                },
            },
        },
    },
    {
        name: 'create_jira_issue',
        description: 'Creates a new issue in a Jira project. You must specify the project, issue type, and a summary. Other fields like description, priority, and assignee are optional.',
        inputSchema: {
            type: 'object',
            properties: {
                projectKey: {
                    type: 'string',
                    description: 'The key of the project in which the issue will be created (e.g., "PROJ").',
                },
                issueType: {
                    type: 'string',
                    description: 'The name of the issue type (e.g., "Bug", "Task", "Story"). This must be a valid issue type in the specified project.',
                },
                summary: {
                    type: 'string',
                    description: 'A concise summary or title for the issue.',
                },
                description: {
                    type: 'string',
                    description: 'A detailed description of the issue. Optional.',
                },
                priority: {
                    type: 'string',
                    description: 'The priority level for the issue (e.g., "High", "Medium", "Low"). Must be a valid priority in the project.',
                },
                assignee: {
                    type: 'string',
                    description: 'The Atlassian account ID of the user to whom the issue should be assigned.',
                },
                labels: {
                    type: 'array',
                    items: { type: 'string' },
                    description: 'A list of labels to add to the new issue.',
                },
                components: {
                    type: 'array',
                    items: { type: 'string' },
                    description: 'A list of component names to associate with the new issue.',
                },
                customFields: {
                    type: 'object',
                    description: 'A JSON object for setting custom fields. The keys are the custom field IDs (e.g., "customfield_10010") and the values are the data to be set. **For example: `{"customfield_10010": "Value for custom field"}`**.',
                },
            },
            required: ['projectKey', 'issueType', 'summary'],
        },
    },
    {
        name: 'add_jira_comment',
        description: 'Adds a comment to an existing Jira issue. You can also control the visibility of the comment.',
        inputSchema: {
            type: 'object',
            properties: {
                issueKey: {
                    type: 'string',
                    description: 'The key of the issue to which the comment will be added (e.g., "PROJ-123").',
                },
                body: {
                    type: 'string',
                    description: 'The text content of the comment.',
                },
                visibility: {
                    type: 'object',
                    description: 'An object that sets the visibility of the comment to a specific project role or group. Optional.',
                    properties: {
                        type: {
                            type: 'string',
                            enum: ['group', 'role'],
                            description: 'The type of visibility restriction.',
                        },
                        value: {
                            type: 'string',
                            description: 'The name of the group or project role.',
                        },
                    },
                },
            },
            required: ['issueKey', 'body'],
        },
    },
    {
        name: 'list_agile_boards',
        description: 'List all accessible Agile boards (both Scrum and Kanban types). Can be filtered by project or board type to find specific boards.',
        inputSchema: {
            type: 'object',
            properties: {
                projectKeyOrId: {
                    type: 'string',
                    description: 'Filter boards by a specific project key or ID (e.g., "PROJ" or "10000").',
                },
                type: {
                    type: 'string',
                    enum: ['scrum', 'kanban'],
                    description: 'Filter by board type: scrum or kanban.',
                },
                startAt: {
                    type: 'number',
                    description: 'The starting index for pagination. Default is 0.',
                    default: 0,
                },
                maxResults: {
                    type: 'number',
                    description: 'The maximum number of boards to return. Default is 50, maximum is 50.',
                    default: 50,
                    minimum: 1,
                    maximum: 50,
                },
            },
        },
    },
    {
        name: 'list_sprints_for_board',
        description: 'List all sprints for a specific Agile board. Can filter by sprint state (active, closed, or future) to find current or historical sprints.',
        inputSchema: {
            type: 'object',
            properties: {
                boardId: {
                    type: 'number',
                    description: 'The ID of the board to get sprints from.',
                },
                state: {
                    type: 'string',
                    enum: ['active', 'closed', 'future'],
                    description: 'Filter sprints by state. If not provided, returns all sprints.',
                },
                startAt: {
                    type: 'number',
                    description: 'The starting index for pagination. Default is 0.',
                    default: 0,
                },
                maxResults: {
                    type: 'number',
                    description: 'The maximum number of sprints to return. Default is 50, maximum is 50.',
                    default: 50,
                    minimum: 1,
                    maximum: 50,
                },
            },
            required: ['boardId'],
        },
    },
    {
        name: 'get_sprint_details',
        description: 'Get comprehensive details about a specific sprint including its name, start/end dates, goals, and all issues included in the sprint.',
        inputSchema: {
            type: 'object',
            properties: {
                sprintId: {
                    type: 'number',
                    description: 'The ID of the sprint to retrieve.',
                },
            },
            required: ['sprintId'],
        },
    },
    {
        name: 'get_my_current_sprint_issues',
        description: 'Get all issues assigned to you in the currently active sprint(s). Useful for daily standups or checking your current sprint workload. Can filter by specific board or project.',
        inputSchema: {
            type: 'object',
            properties: {
                boardId: {
                    type: 'number',
                    description: 'Optional board ID to get sprint-specific information.',
                },
                projectKey: {
                    type: 'string',
                    description: 'Optional project key to filter issues (e.g., "PROJ").',
                },
            },
        },
    },
    {
        name: 'get_my_unresolved_issues',
        description: 'Get all unresolved issues currently assigned to you, organized by status and priority. Perfect for checking your backlog or identifying what needs attention.',
        inputSchema: {
            type: 'object',
            properties: {
                projectKeys: {
                    type: 'array',
                    items: { type: 'string' },
                    description: 'Optional list of project keys to filter issues (e.g., ["PROJ1", "PROJ2"]).',
                },
                maxResults: {
                    type: 'number',
                    description: 'The maximum number of issues to return. Default is 50, maximum is 100.',
                    default: 50,
                    minimum: 1,
                    maximum: 100,
                },
            },
        },
    },
];
//# sourceMappingURL=tools.js.map