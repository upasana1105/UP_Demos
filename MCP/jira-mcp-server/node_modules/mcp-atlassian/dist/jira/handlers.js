import { formatApiError } from '../utils/http-client.js';
import { JqlBuilder, validateAccountId, validateProjectKeys, escapeJqlString, } from '../utils/jql-sanitizer.js';
import { validatePagination, validateDateRange, validateStringArray, validateEnum, validateUserIdentification, validateString, validateNumber, } from '../utils/input-validator.js';
import { getUserCache, createCacheKey } from '../utils/user-cache.js';
import { createEnhancedError, createValidationError, createUserNotFoundError, } from '../utils/error-handler.js';
import { formatSeconds } from '../utils/time-formatter.js';
export class JiraHandlers {
    client;
    constructor(client) {
        this.client = client;
    }
    async _getCurrentUser() {
        const response = await this.client.get('/rest/api/3/myself');
        return response.data;
    }
    async readJiraIssue(args) {
        try {
            const { issueKey, expand = 'fields,transitions,changelog' } = args;
            const issueKeyValidation = validateString(issueKey, 'issueKey', {
                required: true,
                maxLength: 255,
                pattern: /^[A-Z]+-[0-9]+$/,
            });
            if (!issueKeyValidation.isValid) {
                return createValidationError(issueKeyValidation.errors, 'readJiraIssue', 'jira');
            }
            const response = await this.client.get(`/rest/api/3/issue/${issueKeyValidation.sanitizedValue}`, {
                params: { expand },
            });
            const issue = response.data;
            const result = {
                id: issue.id,
                key: issue.key,
                webUrl: `${this.client.defaults.baseURL}/browse/${issue.key}`,
                fields: {
                    summary: issue.fields.summary,
                    description: issue.fields.description,
                    status: issue.fields.status?.name,
                    priority: issue.fields.priority?.name,
                    issueType: issue.fields.issuetype?.name,
                    assignee: issue.fields.assignee?.displayName,
                    reporter: issue.fields.reporter?.displayName,
                    created: issue.fields.created,
                    updated: issue.fields.updated,
                    resolved: issue.fields.resolutiondate,
                    labels: issue.fields.labels,
                    components: issue.fields.components?.map((c) => c.name),
                },
                transitions: issue.transitions?.map((t) => ({
                    id: t.id,
                    name: t.name,
                    to: t.to.name,
                })),
            };
            return {
                content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
        }
        catch (error) {
            return {
                content: [{ type: 'text', text: formatApiError(error) }],
                isError: true,
            };
        }
    }
    async searchJiraIssues(args) {
        try {
            const { jql, maxResults = 50, startAt = 0, fields = '*all' } = args;
            const jqlValidation = validateString(jql, 'jql', { required: true, maxLength: 2000 });
            if (!jqlValidation.isValid) {
                return createValidationError(jqlValidation.errors, 'searchJiraIssues', 'jira');
            }
            const paginationValidation = validatePagination(startAt, maxResults);
            if (!paginationValidation.isValid) {
                return createValidationError(paginationValidation.errors, 'searchJiraIssues', 'jira');
            }
            const response = await this.client.get('/rest/api/3/search', {
                params: {
                    jql: jqlValidation.sanitizedValue,
                    maxResults: paginationValidation.sanitizedValue.maxResults,
                    startAt: paginationValidation.sanitizedValue.startAt,
                    fields,
                },
            });
            const issues = response.data.issues.map((issue) => ({
                id: issue.id,
                key: issue.key,
                webUrl: `${this.client.defaults.baseURL}/browse/${issue.key}`,
                fields: {
                    summary: issue.fields.summary,
                    status: issue.fields.status?.name,
                    priority: issue.fields.priority?.name,
                    issueType: issue.fields.issuetype?.name,
                    assignee: issue.fields.assignee?.displayName,
                    created: issue.fields.created,
                    updated: issue.fields.updated,
                },
            }));
            const resultData = {
                totalResults: response.data.total,
                startAt: response.data.startAt,
                maxResults: response.data.maxResults,
                issues,
            };
            return {
                content: [{ type: 'text', text: JSON.stringify(resultData, null, 2) }],
            };
        }
        catch (error) {
            return {
                content: [{ type: 'text', text: formatApiError(error) }],
                isError: true,
            };
        }
    }
    async listJiraProjects(args) {
        try {
            const { expand = 'description,lead,issueTypes' } = args;
            const response = await this.client.get('/rest/api/3/project', {
                params: { expand },
            });
            const projects = response.data.map((project) => ({
                id: project.id,
                key: project.key,
                name: project.name,
                description: project.description,
                projectType: project.projectTypeKey,
                lead: project.lead?.displayName,
                webUrl: `${this.client.defaults.baseURL}/projects/${project.key}`,
                issueTypes: project.issueTypes?.map((it) => ({
                    name: it.name,
                    description: it.description,
                })),
            }));
            const resultData = {
                totalProjects: projects.length,
                projects,
            };
            return {
                content: [{ type: 'text', text: JSON.stringify(resultData, null, 2) }],
            };
        }
        catch (error) {
            return {
                content: [{ type: 'text', text: formatApiError(error) }],
                isError: true,
            };
        }
    }
    async createJiraIssue(args) {
        try {
            const { projectKey, issueType, summary, description, priority, assignee, labels, components, customFields, } = args;
            const projectKeyValidation = validateString(projectKey, 'projectKey', {
                required: true,
                pattern: /^[A-Z][A-Z0-9_]*$/,
            });
            if (!projectKeyValidation.isValid)
                return createValidationError(projectKeyValidation.errors, 'createJiraIssue', 'jira');
            const issueTypeValidation = validateString(issueType, 'issueType', { required: true });
            if (!issueTypeValidation.isValid)
                return createValidationError(issueTypeValidation.errors, 'createJiraIssue', 'jira');
            const summaryValidation = validateString(summary, 'summary', {
                required: true,
                maxLength: 255,
            });
            if (!summaryValidation.isValid)
                return createValidationError(summaryValidation.errors, 'createJiraIssue', 'jira');
            const issueData = {
                fields: {
                    project: { key: projectKeyValidation.sanitizedValue },
                    issuetype: { name: issueTypeValidation.sanitizedValue },
                    summary: summaryValidation.sanitizedValue,
                },
            };
            if (description) {
                const descriptionValidation = validateString(description, 'description', {
                    maxLength: 32767,
                });
                if (!descriptionValidation.isValid)
                    return createValidationError(descriptionValidation.errors, 'createJiraIssue', 'jira');
                issueData.fields.description = {
                    type: 'doc',
                    version: 1,
                    content: [
                        {
                            type: 'paragraph',
                            content: [
                                {
                                    type: 'text',
                                    text: descriptionValidation.sanitizedValue,
                                },
                            ],
                        },
                    ],
                };
            }
            if (priority) {
                const priorityValidation = validateString(priority, 'priority');
                if (!priorityValidation.isValid)
                    return createValidationError(priorityValidation.errors, 'createJiraIssue', 'jira');
                issueData.fields.priority = { name: priorityValidation.sanitizedValue };
            }
            if (assignee) {
                const assigneeValidation = validateString(assignee, 'assignee');
                if (!assigneeValidation.isValid)
                    return createValidationError(assigneeValidation.errors, 'createJiraIssue', 'jira');
                issueData.fields.assignee = { accountId: assigneeValidation.sanitizedValue };
            }
            if (labels && labels.length > 0) {
                issueData.fields.labels = labels;
            }
            if (components && components.length > 0) {
                issueData.fields.components = components.map((name) => ({ name }));
            }
            if (customFields) {
                Object.assign(issueData.fields, customFields);
            }
            const response = await this.client.post('/rest/api/3/issue', issueData);
            const result = {
                id: response.data.id,
                key: response.data.key,
                self: response.data.self,
                webUrl: `${this.client.defaults.baseURL}/browse/${response.data.key}`,
            };
            return {
                content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
        }
        catch (error) {
            return {
                content: [{ type: 'text', text: formatApiError(error) }],
                isError: true,
            };
        }
    }
    async addJiraComment(args) {
        try {
            const { issueKey, body, visibility } = args;
            const issueKeyValidation = validateString(issueKey, 'issueKey', {
                required: true,
                pattern: /^[A-Z]+-[0-9]+$/,
            });
            if (!issueKeyValidation.isValid)
                return createValidationError(issueKeyValidation.errors, 'addJiraComment', 'jira');
            const bodyValidation = validateString(body, 'body', { required: true, maxLength: 32767 });
            if (!bodyValidation.isValid)
                return createValidationError(bodyValidation.errors, 'addJiraComment', 'jira');
            const commentData = {
                body: {
                    type: 'doc',
                    version: 1,
                    content: [
                        {
                            type: 'paragraph',
                            content: [
                                {
                                    type: 'text',
                                    text: bodyValidation.sanitizedValue,
                                },
                            ],
                        },
                    ],
                },
            };
            if (visibility) {
                commentData.visibility = visibility;
            }
            const response = await this.client.post(`/rest/api/3/issue/${issueKey}/comment`, commentData);
            const result = {
                id: response.data.id,
                created: response.data.created,
                author: response.data.author?.displayName,
                body,
                issueKey,
            };
            return {
                content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
        }
        catch (error) {
            return {
                content: [{ type: 'text', text: formatApiError(error) }],
                isError: true,
            };
        }
    }
    async getJiraCurrentUser() {
        try {
            const response = await this.client.get('/rest/api/3/myself');
            const user = response.data;
            const result = {
                accountId: user.accountId,
                displayName: user.displayName,
                emailAddress: user.emailAddress,
                active: user.active,
                timeZone: user.timeZone,
                accountType: user.accountType,
                avatarUrls: user.avatarUrls,
                profileUrl: `${this.client.defaults.baseURL}/people/${user.accountId}`,
            };
            return {
                content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
        }
        catch (error) {
            return {
                content: [{ type: 'text', text: formatApiError(error) }],
                isError: true,
            };
        }
    }
    async listJiraBoards(args) {
        try {
            const { projectKeyOrId, type, startAt = 0, maxResults = 50 } = args;
            const paginationValidation = validatePagination(startAt, maxResults);
            if (!paginationValidation.isValid)
                return createValidationError(paginationValidation.errors, 'listJiraBoards', 'jira');
            const params = {
                startAt: paginationValidation.sanitizedValue.startAt,
                maxResults: paginationValidation.sanitizedValue.maxResults,
            };
            if (projectKeyOrId) {
                const projectKeyValidation = validateString(projectKeyOrId, 'projectKeyOrId');
                if (!projectKeyValidation.isValid)
                    return createValidationError(projectKeyValidation.errors, 'listJiraBoards', 'jira');
                params.projectKeyOrId = projectKeyValidation.sanitizedValue;
            }
            if (type) {
                params.type = type;
            }
            const response = await this.client.get('/rest/agile/1.0/board', { params });
            const boards = response.data.values.map((board) => ({
                id: board.id,
                name: board.name,
                type: board.type,
                projectKey: board.location?.projectKey,
                projectName: board.location?.projectName,
                webUrl: `${this.client.defaults.baseURL}/secure/RapidBoard.jspa?rapidView=${board.id}`,
            }));
            const resultData = {
                totalBoards: response.data.total || boards.length,
                startAt: response.data.startAt,
                maxResults: response.data.maxResults,
                boards,
            };
            return {
                content: [{ type: 'text', text: JSON.stringify(resultData, null, 2) }],
            };
        }
        catch (error) {
            return {
                content: [{ type: 'text', text: formatApiError(error) }],
                isError: true,
            };
        }
    }
    async listJiraSprints(args) {
        try {
            const { boardId, state, startAt = 0, maxResults = 50 } = args;
            const boardIdValidation = validateNumber(boardId, 'boardId', {
                required: true,
                integer: true,
            });
            if (!boardIdValidation.isValid)
                return createValidationError(boardIdValidation.errors, 'listJiraSprints', 'jira');
            const paginationValidation = validatePagination(startAt, maxResults);
            if (!paginationValidation.isValid)
                return createValidationError(paginationValidation.errors, 'listJiraSprints', 'jira');
            const params = {
                startAt: paginationValidation.sanitizedValue.startAt,
                maxResults: paginationValidation.sanitizedValue.maxResults,
            };
            if (state) {
                const stateValidation = validateEnum(state, 'state', ['future', 'active', 'closed']);
                if (!stateValidation.isValid)
                    return createValidationError(stateValidation.errors, 'listJiraSprints', 'jira');
                params.state = stateValidation.sanitizedValue;
            }
            const response = await this.client.get(`/rest/agile/1.0/board/${boardIdValidation.sanitizedValue}/sprint`, { params });
            const sprints = response.data.values.map((sprint) => ({
                id: sprint.id,
                name: sprint.name,
                state: sprint.state,
                startDate: sprint.startDate,
                endDate: sprint.endDate,
                completeDate: sprint.completeDate,
                goal: sprint.goal,
                originBoardId: sprint.originBoardId,
            }));
            const resultData = {
                totalSprints: response.data.total || sprints.length,
                startAt: response.data.startAt,
                maxResults: response.data.maxResults,
                boardId,
                sprints,
            };
            return {
                content: [{ type: 'text', text: JSON.stringify(resultData, null, 2) }],
            };
        }
        catch (error) {
            return {
                content: [{ type: 'text', text: formatApiError(error) }],
                isError: true,
            };
        }
    }
    async getJiraSprint(args) {
        try {
            const { sprintId } = args;
            const sprintIdValidation = validateNumber(sprintId, 'sprintId', {
                required: true,
                integer: true,
            });
            if (!sprintIdValidation.isValid)
                return createValidationError(sprintIdValidation.errors, 'getJiraSprint', 'jira');
            const response = await this.client.get(`/rest/agile/1.0/sprint/${sprintIdValidation.sanitizedValue}`);
            const sprint = response.data;
            const result = {
                id: sprint.id,
                name: sprint.name,
                state: sprint.state,
                startDate: sprint.startDate,
                endDate: sprint.endDate,
                completeDate: sprint.completeDate,
                goal: sprint.goal,
                originBoardId: sprint.originBoardId,
                webUrl: sprint.originBoardId
                    ? `${this.client.defaults.baseURL}/secure/RapidBoard.jspa?rapidView=${sprint.originBoardId}&view=planning&selectedIssue=none&sprint=${sprint.id}`
                    : undefined,
            };
            try {
                const issuesResponse = await this.client.get(`/rest/agile/1.0/sprint/${sprintId}/issue`, {
                    params: { maxResults: 100 },
                });
                result.issueCount = issuesResponse.data.total;
                result.issues = issuesResponse.data.issues.map((issue) => ({
                    key: issue.key,
                    summary: issue.fields.summary,
                    status: issue.fields.status?.name,
                    assignee: issue.fields.assignee?.displayName,
                }));
            }
            catch (issuesError) {
                // If we can't get issues, continue without them
                console.error('Failed to get sprint issues:', issuesError);
            }
            return {
                content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
        }
        catch (error) {
            return {
                content: [{ type: 'text', text: formatApiError(error) }],
                isError: true,
            };
        }
    }
    async getMyTasksInCurrentSprint(args) {
        try {
            // First get the current user
            const currentUser = await this._getCurrentUser();
            let jql = `assignee = "${currentUser.accountId}" AND sprint in openSprints()`;
            if (args.projectKey) {
                const projectKeyValidation = validateString(args.projectKey, 'projectKey', {
                    pattern: /^[A-Z][A-Z0-9_]*$/,
                });
                if (!projectKeyValidation.isValid)
                    return createValidationError(projectKeyValidation.errors, 'getMyTasksInCurrentSprint', 'jira');
                jql = `project = ${projectKeyValidation.sanitizedValue} AND ${jql}`;
            }
            // If a specific board is provided, we can get more specific sprint info
            let sprintInfo = null;
            if (args.boardId) {
                const boardIdValidation = validateNumber(args.boardId, 'boardId', { integer: true });
                if (!boardIdValidation.isValid)
                    return createValidationError(boardIdValidation.errors, 'getMyTasksInCurrentSprint', 'jira');
                try {
                    const sprintResponse = await this.client.get(`/rest/agile/1.0/board/${boardIdValidation.sanitizedValue}/sprint`, {
                        params: { state: 'active' },
                    });
                    if (sprintResponse.data.values && sprintResponse.data.values.length > 0) {
                        const activeSprint = sprintResponse.data.values[0];
                        sprintInfo = {
                            id: activeSprint.id,
                            name: activeSprint.name,
                            startDate: activeSprint.startDate,
                            endDate: activeSprint.endDate,
                        };
                    }
                }
                catch (sprintError) {
                    // Continue without sprint info
                    console.error('Failed to get sprint info:', sprintError);
                }
            }
            // Search for issues
            const response = await this.client.get('/rest/api/3/search', {
                params: {
                    jql,
                    maxResults: 100,
                    fields: 'summary,status,priority,issuetype,created,updated,description,components,labels,sprint',
                },
            });
            const issues = response.data.issues.map((issue) => ({
                key: issue.key,
                summary: issue.fields.summary,
                status: issue.fields.status?.name,
                priority: issue.fields.priority?.name,
                issueType: issue.fields.issuetype?.name,
                created: issue.fields.created,
                updated: issue.fields.updated,
                webUrl: `${this.client.defaults.baseURL}/browse/${issue.key}`,
                sprint: issue.fields.sprint?.name,
            }));
            const resultData = {
                currentUser: currentUser.displayName,
                activeSprint: sprintInfo,
                totalIssues: response.data.total,
                issues,
            };
            return {
                content: [{ type: 'text', text: JSON.stringify(resultData, null, 2) }],
            };
        }
        catch (error) {
            return {
                content: [{ type: 'text', text: formatApiError(error) }],
                isError: true,
            };
        }
    }
    async getMyOpenIssues(args) {
        try {
            const { projectKeys, maxResults = 50 } = args;
            // First get the current user
            const currentUser = await this._getCurrentUser();
            let jql = `assignee = "${currentUser.accountId}" AND resolution = Unresolved`;
            if (projectKeys && projectKeys.length > 0) {
                const projectKeysValidation = validateStringArray(projectKeys, 'projectKeys', {
                    pattern: /^[A-Z][A-Z0-9_]*$/,
                });
                if (!projectKeysValidation.isValid)
                    return createValidationError(projectKeysValidation.errors, 'getMyOpenIssues', 'jira');
                const projectFilter = projectKeysValidation
                    .sanitizedValue.map((key) => `"${key}"`)
                    .join(', ');
                jql = `project in (${projectFilter}) AND ${jql}`;
            }
            jql += ' ORDER BY priority DESC, updated DESC';
            const response = await this.client.get('/rest/api/3/search', {
                params: {
                    jql,
                    maxResults: Math.min(maxResults, 100),
                    fields: 'summary,status,priority,issuetype,created,updated,project,components,labels,duedate',
                },
            });
            const issues = response.data.issues.map((issue) => ({
                key: issue.key,
                summary: issue.fields.summary,
                status: issue.fields.status?.name,
                priority: issue.fields.priority?.name,
                issueType: issue.fields.issuetype?.name,
                project: issue.fields.project?.key,
                created: issue.fields.created,
                updated: issue.fields.updated,
                dueDate: issue.fields.duedate,
                webUrl: `${this.client.defaults.baseURL}/browse/${issue.key}`,
                labels: issue.fields.labels,
                components: issue.fields.components?.map((c) => c.name),
            }));
            // Group issues by status
            const issuesByStatus = {};
            issues.forEach((issue) => {
                if (!issuesByStatus[issue.status]) {
                    issuesByStatus[issue.status] = [];
                }
                issuesByStatus[issue.status].push(issue);
            });
            const resultData = {
                currentUser: currentUser.displayName,
                totalOpenIssues: response.data.total,
                issuesByStatus,
                allIssues: issues,
            };
            return {
                content: [{ type: 'text', text: JSON.stringify(resultData, null, 2) }],
            };
        }
        catch (error) {
            return {
                content: [{ type: 'text', text: formatApiError(error) }],
                isError: true,
            };
        }
    }
    async getJiraUser(args) {
        try {
            const { username, accountId, email } = args;
            const cache = getUserCache();
            // Try cache first
            let cacheKey;
            try {
                cacheKey = createCacheKey({ username, accountId, email });
                const cachedUser = cache.get(cacheKey);
                if (cachedUser) {
                    const result = {
                        accountId: cachedUser.accountId,
                        displayName: cachedUser.displayName,
                        emailAddress: cachedUser.emailAddress,
                        active: cachedUser.active,
                        timeZone: cachedUser.timeZone,
                        accountType: cachedUser.accountType,
                        avatarUrls: cachedUser.avatarUrls,
                        profileUrl: `${this.client.defaults.baseURL}/people/${cachedUser.accountId}`,
                        source: 'cache',
                    };
                    return {
                        content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
                    };
                }
            }
            catch (e) {
                // Invalid cache key, proceed with API lookup
            }
            // Prioritize accountId lookup (most secure)
            let user = null;
            if (accountId) {
                try {
                    const validatedAccountId = validateAccountId(accountId);
                    const response = await this.client.get(`/rest/api/3/user`, {
                        params: { accountId: validatedAccountId },
                    });
                    user = response.data;
                }
                catch (e) {
                    // User not found by accountId
                }
            }
            // Fallback to username search with strict matching (deprecated - warn user)
            if (!user && username) {
                try {
                    const response = await this.client.get('/rest/api/3/user/search', {
                        params: { query: escapeJqlString(username), maxResults: 10 },
                    });
                    if (response.data && response.data.length > 0) {
                        // Strict matching: find exact match by displayName or accountId
                        user =
                            response.data.find((u) => u.displayName === username || u.accountId === username) || null;
                        // Warn about deprecated username usage
                        if (user) {
                            console.warn(`Warning: Username lookup is deprecated. Use accountId '${user.accountId}' instead.`);
                        }
                    }
                }
                catch (e) {
                    // User not found by username
                }
            }
            // Email search removed for privacy reasons - accountId should be used instead
            if (!user && email) {
                return {
                    content: [
                        {
                            type: 'text',
                            text: 'Email-based user lookup has been disabled for privacy reasons. Please use accountId instead.',
                        },
                    ],
                    isError: true,
                };
            }
            if (!user) {
                const identifier = accountId || username || email || 'unknown';
                return createUserNotFoundError(identifier, 'jira');
            }
            // Cache the user data for future lookups
            const cachedUserData = {
                accountId: user.accountId,
                displayName: user.displayName,
                emailAddress: user.emailAddress,
                active: user.active,
                timeZone: user.timeZone,
                accountType: user.accountType,
                avatarUrls: user.avatarUrls,
            };
            cache.set(cachedUserData);
            const result = {
                ...cachedUserData,
                profileUrl: `${this.client.defaults.baseURL}/people/${user.accountId}`,
                source: 'api',
            };
            return {
                content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
        }
        catch (error) {
            return createEnhancedError(error, {
                operation: 'get user profile',
                component: 'jira',
                userInput: {
                    username: args.username,
                    accountId: args.accountId,
                    email: args.email,
                },
                suggestions: [
                    'Verify the user identifier is correct',
                    'Use accountId for best performance and security',
                    'Check that the user exists in your Atlassian instance',
                ],
            });
        }
    }
    async searchJiraIssuesByUser(args) {
        try {
            const { username, accountId, searchType, projectKeys, status, issueType, maxResults = 50, startAt = 0, } = args;
            // Get user's accountId if not provided
            let userAccountId = accountId;
            if (!userAccountId && username) {
                const userResult = await this.getJiraUser({ username });
                if (userResult.isError) {
                    return userResult;
                }
                const userData = JSON.parse(userResult.content[0].text);
                userAccountId = userData.accountId;
            }
            if (!userAccountId) {
                return {
                    content: [{ type: 'text', text: 'User account ID or username is required' }],
                    isError: true,
                };
            }
            // Validate and sanitize inputs
            const validatedAccountId = validateAccountId(userAccountId);
            const jqlBuilder = new JqlBuilder();
            // Build JQL query based on search type using secure builder
            if (searchType === 'assignee') {
                jqlBuilder.equals('assignee', validatedAccountId);
            }
            else if (searchType === 'reporter') {
                jqlBuilder.equals('reporter', validatedAccountId);
            }
            else if (searchType === 'creator') {
                jqlBuilder.equals('creator', validatedAccountId);
            }
            else if (searchType === 'watcher') {
                jqlBuilder.equals('watcher', validatedAccountId);
            }
            else if (searchType === 'all') {
                jqlBuilder.orEquals(['assignee', 'reporter', 'creator', 'watcher'], validatedAccountId);
            }
            // Add project filter if specified
            if (projectKeys && projectKeys.length > 0) {
                const validatedProjectKeys = validateProjectKeys(projectKeys);
                jqlBuilder.in('project', validatedProjectKeys);
            }
            // Add status filter if specified
            if (status) {
                jqlBuilder.equals('status', status);
            }
            // Add issue type filter if specified
            if (issueType) {
                jqlBuilder.equals('issuetype', issueType);
            }
            // Build final JQL with ordering
            let jql = jqlBuilder.build();
            if (jql) {
                jql += ' ORDER BY updated DESC';
            }
            else {
                throw new Error('Invalid search criteria provided');
            }
            const response = await this.client.get('/rest/api/3/search', {
                params: {
                    jql,
                    maxResults: Math.min(maxResults, 100),
                    startAt,
                    fields: 'summary,status,priority,issuetype,assignee,reporter,created,updated,project',
                },
            });
            const issues = response.data.issues.map((issue) => ({
                key: issue.key,
                summary: issue.fields.summary,
                status: issue.fields.status?.name,
                priority: issue.fields.priority?.name,
                issueType: issue.fields.issuetype?.name,
                assignee: issue.fields.assignee?.displayName,
                reporter: issue.fields.reporter?.displayName,
                project: issue.fields.project?.key,
                created: issue.fields.created,
                updated: issue.fields.updated,
                webUrl: `${this.client.defaults.baseURL}/browse/${issue.key}`,
            }));
            const resultData = {
                searchType,
                user: userAccountId,
                totalIssues: response.data.total,
                startAt: response.data.startAt,
                maxResults: response.data.maxResults,
                issues,
            };
            return {
                content: [{ type: 'text', text: JSON.stringify(resultData, null, 2) }],
            };
        }
        catch (error) {
            return {
                content: [{ type: 'text', text: formatApiError(error) }],
                isError: true,
            };
        }
    }
    async listUserJiraIssues(args) {
        try {
            const { username, accountId, role, projectKeys, startDate, endDate, maxResults = 50, startAt = 0, } = args;
            // Validate inputs
            const userValidation = validateUserIdentification({ username, accountId });
            if (!userValidation.isValid) {
                return {
                    content: [
                        { type: 'text', text: `Input validation failed: ${userValidation.errors.join(', ')}` },
                    ],
                    isError: true,
                };
            }
            const roleValidation = validateEnum(role, 'role', ['assignee', 'reporter', 'creator'], true);
            if (!roleValidation.isValid) {
                return {
                    content: [
                        { type: 'text', text: `Role validation failed: ${roleValidation.errors.join(', ')}` },
                    ],
                    isError: true,
                };
            }
            const paginationValidation = validatePagination(startAt, maxResults);
            if (!paginationValidation.isValid) {
                return {
                    content: [
                        {
                            type: 'text',
                            text: `Pagination validation failed: ${paginationValidation.errors.join(', ')}`,
                        },
                    ],
                    isError: true,
                };
            }
            const dateValidation = validateDateRange(startDate, endDate);
            if (!dateValidation.isValid) {
                return {
                    content: [
                        { type: 'text', text: `Date validation failed: ${dateValidation.errors.join(', ')}` },
                    ],
                    isError: true,
                };
            }
            let validatedProjectKeys;
            if (projectKeys) {
                const projectValidation = validateStringArray(projectKeys, 'projectKeys', {
                    pattern: /^[A-Z0-9]{1,10}$/,
                    maxItems: 20,
                });
                if (!projectValidation.isValid) {
                    return {
                        content: [
                            {
                                type: 'text',
                                text: `Project keys validation failed: ${projectValidation.errors.join(', ')}`,
                            },
                        ],
                        isError: true,
                    };
                }
                validatedProjectKeys = projectValidation.sanitizedValue;
            }
            // Get user's accountId if not provided
            let userAccountId = userValidation.sanitizedValue?.accountId;
            if (!userAccountId && userValidation.sanitizedValue?.username) {
                const userResult = await this.getJiraUser({
                    username: userValidation.sanitizedValue.username,
                });
                if (userResult.isError) {
                    return userResult;
                }
                const userData = JSON.parse(userResult.content[0].text);
                userAccountId = userData.accountId;
            }
            if (!userAccountId) {
                return {
                    content: [{ type: 'text', text: 'Could not resolve user account ID' }],
                    isError: true,
                };
            }
            // Build secure JQL query using JQL Builder
            const jqlBuilder = new JqlBuilder();
            const validatedAccountId = validateAccountId(userAccountId);
            jqlBuilder.equals(roleValidation.sanitizedValue, validatedAccountId);
            if (validatedProjectKeys && validatedProjectKeys.length > 0) {
                jqlBuilder.in('project', validatedProjectKeys);
            }
            if (dateValidation.sanitizedValue) {
                jqlBuilder.dateRange('created', dateValidation.sanitizedValue.startDate, dateValidation.sanitizedValue.endDate);
            }
            const jql = jqlBuilder.build() + ' ORDER BY created DESC';
            const response = await this.client.get('/rest/api/3/search', {
                params: {
                    jql,
                    maxResults: paginationValidation.sanitizedValue.maxResults,
                    startAt: paginationValidation.sanitizedValue.startAt,
                    fields: 'summary,status,priority,issuetype,assignee,reporter,created,updated,project,resolution',
                },
            });
            const issues = response.data.issues.map((issue) => ({
                key: issue.key,
                summary: issue.fields.summary,
                status: issue.fields.status?.name,
                priority: issue.fields.priority?.name,
                issueType: issue.fields.issuetype?.name,
                assignee: issue.fields.assignee?.displayName,
                reporter: issue.fields.reporter?.displayName,
                project: issue.fields.project?.key,
                resolution: issue.fields.resolution?.name,
                created: issue.fields.created,
                updated: issue.fields.updated,
                webUrl: `${this.client.defaults.baseURL}/browse/${issue.key}`,
            }));
            const resultData = {
                role,
                user: userAccountId,
                dateRange: {
                    start: startDate || 'unlimited',
                    end: endDate || 'unlimited',
                },
                totalIssues: response.data.total,
                startAt: response.data.startAt,
                maxResults: response.data.maxResults,
                issues,
            };
            return {
                content: [{ type: 'text', text: JSON.stringify(resultData, null, 2) }],
            };
        }
        catch (error) {
            return {
                content: [{ type: 'text', text: formatApiError(error) }],
                isError: true,
            };
        }
    }
    async getUserJiraActivity(args) {
        try {
            const { username, accountId, activityType = 'all', projectKeys, days = 30, maxResults = 50, startAt = 0, } = args;
            const userValidation = validateUserIdentification({ username, accountId });
            if (!userValidation.isValid)
                return createValidationError(userValidation.errors, 'getUserJiraActivity', 'jira');
            const paginationValidation = validatePagination(startAt, maxResults);
            if (!paginationValidation.isValid)
                return createValidationError(paginationValidation.errors, 'getUserJiraActivity', 'jira');
            // Get user's accountId if not provided
            let userAccountId = userValidation.sanitizedValue?.accountId;
            if (!userAccountId && userValidation.sanitizedValue?.username) {
                const userResult = await this.getJiraUser({ username });
                if (userResult.isError) {
                    return userResult;
                }
                const userData = JSON.parse(userResult.content[0].text);
                userAccountId = userData.accountId;
            }
            if (!userAccountId) {
                return {
                    content: [{ type: 'text', text: 'User account ID or username is required' }],
                    isError: true,
                };
            }
            // Calculate date range for activity
            const endDate = new Date();
            const startDate = new Date();
            startDate.setDate(startDate.getDate() - days);
            // Build JQL query for recent activity
            let jql = `(assignee = "${userAccountId}" OR reporter = "${userAccountId}" OR creator = "${userAccountId}")`;
            jql += ` AND updated >= -${days}d`;
            if (projectKeys && projectKeys.length > 0) {
                const projectFilter = projectKeys.map((key) => `"${key}"`).join(', ');
                jql = `project in (${projectFilter}) AND ${jql}`;
            }
            jql += ' ORDER BY updated DESC';
            const response = await this.client.get('/rest/api/3/search', {
                params: {
                    jql,
                    maxResults: Math.min(maxResults, 100),
                    startAt,
                    fields: 'summary,status,priority,issuetype,assignee,reporter,created,updated,project,comment,worklog',
                    expand: 'changelog',
                },
            });
            // Process issues and extract activity
            const activity = [];
            for (const issue of response.data.issues) {
                // Add issue updates
                if (issue.fields.updated) {
                    const updatedDate = new Date(issue.fields.updated);
                    if (updatedDate >= startDate) {
                        activity.push({
                            type: 'issue_updated',
                            issueKey: issue.key,
                            summary: issue.fields.summary,
                            date: issue.fields.updated,
                            project: issue.fields.project?.key,
                        });
                    }
                }
                // Add comments if requested
                if ((activityType === 'comments' || activityType === 'all') &&
                    issue.fields.comment?.comments) {
                    for (const comment of issue.fields.comment.comments) {
                        if (comment.author?.accountId === userAccountId) {
                            const commentDate = new Date(comment.created);
                            if (commentDate >= startDate) {
                                activity.push({
                                    type: 'comment',
                                    issueKey: issue.key,
                                    date: comment.created,
                                    body: comment.body?.content?.[0]?.content?.[0]?.text || comment.body,
                                });
                            }
                        }
                    }
                }
                // Add transitions if requested
                if ((activityType === 'transitions' || activityType === 'all') &&
                    issue.changelog?.histories) {
                    for (const history of issue.changelog.histories) {
                        if (history.author?.accountId === userAccountId) {
                            const changeDate = new Date(history.created);
                            if (changeDate >= startDate) {
                                for (const item of history.items) {
                                    if (item.field === 'status') {
                                        activity.push({
                                            type: 'status_change',
                                            issueKey: issue.key,
                                            date: history.created,
                                            from: item.fromString,
                                            to: item.toString,
                                        });
                                    }
                                }
                            }
                        }
                    }
                }
            }
            // Sort activity by date
            activity.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
            const resultData = {
                user: userAccountId,
                activityType,
                dateRange: {
                    start: startDate.toISOString(),
                    end: endDate.toISOString(),
                    days,
                },
                totalActivities: activity.length,
                activities: activity.slice(0, maxResults),
            };
            return {
                content: [{ type: 'text', text: JSON.stringify(resultData, null, 2) }],
            };
        }
        catch (error) {
            return {
                content: [{ type: 'text', text: formatApiError(error) }],
                isError: true,
            };
        }
    }
    async getUserJiraWorklog(args) {
        try {
            const { username, accountId, startDate, endDate, projectKeys, maxResults = 50, startAt = 0, } = args;
            // Validate inputs
            const userValidation = validateUserIdentification({ username, accountId });
            if (!userValidation.isValid) {
                return {
                    content: [
                        { type: 'text', text: `Input validation failed: ${userValidation.errors.join(', ')}` },
                    ],
                    isError: true,
                };
            }
            const paginationValidation = validatePagination(startAt, maxResults);
            if (!paginationValidation.isValid) {
                return {
                    content: [
                        {
                            type: 'text',
                            text: `Pagination validation failed: ${paginationValidation.errors.join(', ')}`,
                        },
                    ],
                    isError: true,
                };
            }
            const dateValidation = validateDateRange(startDate, endDate);
            if (!dateValidation.isValid) {
                return {
                    content: [
                        { type: 'text', text: `Date validation failed: ${dateValidation.errors.join(', ')}` },
                    ],
                    isError: true,
                };
            }
            let validatedProjectKeys;
            if (projectKeys) {
                const projectValidation = validateStringArray(projectKeys, 'projectKeys', {
                    pattern: /^[A-Z0-9]{1,10}$/,
                    maxItems: 20,
                });
                if (!projectValidation.isValid) {
                    return {
                        content: [
                            {
                                type: 'text',
                                text: `Project keys validation failed: ${projectValidation.errors.join(', ')}`,
                            },
                        ],
                        isError: true,
                    };
                }
                validatedProjectKeys = projectValidation.sanitizedValue;
            }
            // Get user's accountId if not provided (with caching)
            let userAccountId = userValidation.sanitizedValue?.accountId;
            if (!userAccountId && userValidation.sanitizedValue?.username) {
                const userResult = await this.getJiraUser({
                    username: userValidation.sanitizedValue.username,
                });
                if (userResult.isError) {
                    return userResult;
                }
                const userData = JSON.parse(userResult.content[0].text);
                userAccountId = userData.accountId;
            }
            if (!userAccountId) {
                return {
                    content: [{ type: 'text', text: 'Could not resolve user account ID' }],
                    isError: true,
                };
            }
            // Build secure JQL query using JQL Builder
            const jqlBuilder = new JqlBuilder();
            const validatedAccountId = validateAccountId(userAccountId);
            jqlBuilder.equals('worklogAuthor', validatedAccountId);
            if (validatedProjectKeys && validatedProjectKeys.length > 0) {
                jqlBuilder.in('project', validatedProjectKeys);
            }
            // Add date filtering for worklog dates (optimized for performance)
            if (dateValidation.sanitizedValue) {
                if (dateValidation.sanitizedValue.startDate) {
                    jqlBuilder.raw(`worklogDate >= "${dateValidation.sanitizedValue.startDate}"`);
                }
                if (dateValidation.sanitizedValue.endDate) {
                    jqlBuilder.raw(`worklogDate <= "${dateValidation.sanitizedValue.endDate}"`);
                }
            }
            const jql = jqlBuilder.build();
            // Use batch API call with worklog expansion for optimal performance
            const response = await this.client.get('/rest/api/3/search', {
                params: {
                    jql,
                    maxResults: paginationValidation.sanitizedValue.maxResults,
                    startAt: paginationValidation.sanitizedValue.startAt,
                    fields: 'summary,project,worklog',
                    expand: 'worklog', // Efficient batch loading of worklogs
                },
            });
            const worklogs = [];
            let totalTimeSpent = 0;
            for (const issue of response.data.issues) {
                if (issue.fields.worklog?.worklogs) {
                    for (const worklog of issue.fields.worklog.worklogs) {
                        if (worklog.author?.accountId === userAccountId) {
                            const worklogEntry = {
                                issueKey: issue.key,
                                summary: issue.fields.summary || 'No summary',
                                project: issue.fields.project?.key || 'Unknown',
                                started: worklog.started,
                                timeSpent: worklog.timeSpent,
                                timeSpentSeconds: worklog.timeSpentSeconds || 0,
                                comment: worklog.comment?.content?.[0]?.content?.[0]?.text || worklog.comment || '',
                                created: worklog.created,
                                updated: worklog.updated,
                            };
                            worklogs.push(worklogEntry);
                            totalTimeSpent += worklog.timeSpentSeconds || 0;
                        }
                    }
                }
            }
            // Sort worklogs by date
            worklogs.sort((a, b) => new Date(b.started).getTime() - new Date(a.started).getTime());
            const resultData = {
                user: userAccountId,
                dateRange: {
                    start: dateValidation.sanitizedValue?.startDate || 'unlimited',
                    end: dateValidation.sanitizedValue?.endDate || 'unlimited',
                },
                totalWorklogs: worklogs.length,
                totalTimeSpentSeconds: totalTimeSpent,
                totalTimeSpentFormatted: formatSeconds(totalTimeSpent),
                worklogs: worklogs.slice(0, paginationValidation.sanitizedValue.maxResults),
            };
            return {
                content: [{ type: 'text', text: JSON.stringify(resultData, null, 2) }],
            };
        }
        catch (error) {
            return createEnhancedError(error, {
                operation: 'get user worklog',
                component: 'jira',
                userInput: { username: args.username, accountId: args.accountId },
                suggestions: [
                    'Verify the user exists and has logged work',
                    'Check date range is reasonable (not too large)',
                    'Ensure you have permission to view worklogs',
                ],
            });
        }
    }
}
//# sourceMappingURL=handlers.js.map