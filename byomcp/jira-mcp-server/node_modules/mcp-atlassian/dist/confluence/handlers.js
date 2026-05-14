import { formatApiError } from '../utils/http-client.js';
import { ContentConverter } from '../utils/content-converter.js';
import { ExportConverter } from '../utils/export-converter.js';
import { sanitizeHtml } from '../utils/html-sanitizer.js';
import { validateString, validatePagination, validateUserIdentification, validateNumber, validateStringArray, } from '../utils/input-validator.js';
import { createValidationError } from '../utils/error-handler.js';
export class ConfluenceHandlers {
    client;
    constructor(client) {
        this.client = client;
    }
    async _getCurrentUser() {
        const response = await this.client.get('/api/user/current');
        return response.data;
    }
    async readConfluencePage(args) {
        try {
            const { pageId, title, spaceKey, expand = 'body.storage,version,space', format = 'storage', } = args;
            if (!pageId && !title) {
                return createValidationError(['Either pageId or title must be provided'], 'readConfluencePage', 'confluence');
            }
            if (title && !spaceKey) {
                return createValidationError(['spaceKey is required when using title'], 'readConfluencePage', 'confluence');
            }
            if (pageId) {
                const pageIdValidation = validateString(pageId, 'pageId');
                if (!pageIdValidation.isValid)
                    return createValidationError(pageIdValidation.errors, 'readConfluencePage', 'confluence');
            }
            if (title) {
                const titleValidation = validateString(title, 'title');
                if (!titleValidation.isValid)
                    return createValidationError(titleValidation.errors, 'readConfluencePage', 'confluence');
            }
            if (spaceKey) {
                const spaceKeyValidation = validateString(spaceKey, 'spaceKey');
                if (!spaceKeyValidation.isValid)
                    return createValidationError(spaceKeyValidation.errors, 'readConfluencePage', 'confluence');
            }
            let page;
            if (pageId) {
                const response = await this.client.get(`/wiki/rest/api/content/${pageId}`, {
                    params: { expand },
                });
                page = response.data;
            }
            else {
                const searchResponse = await this.client.get('/wiki/rest/api/content', {
                    params: {
                        spaceKey,
                        title,
                        expand,
                    },
                });
                if (searchResponse.data.results.length === 0) {
                    return {
                        content: [
                            { type: 'text', text: `No page found with title "${title}" in space ${spaceKey}` },
                        ],
                    };
                }
                page = searchResponse.data.results[0];
            }
            const storageContent = page.body?.storage?.value || '';
            const content = format === 'markdown' ? ContentConverter.storageToMarkdown(storageContent) : storageContent;
            const result = {
                id: page.id,
                title: page.title,
                space: page.space,
                version: page.version?.number,
                webUrl: `${this.client.defaults.baseURL}/wiki${page._links?.webui}`,
                content,
                format,
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
    async searchConfluencePages(args) {
        try {
            const { cql, limit = 25, start = 0, expand } = args;
            const cqlValidation = validateString(cql, 'cql', { required: true, maxLength: 2000 });
            if (!cqlValidation.isValid)
                return createValidationError(cqlValidation.errors, 'searchConfluencePages', 'confluence');
            const paginationValidation = validatePagination(start, limit);
            if (!paginationValidation.isValid)
                return createValidationError(paginationValidation.errors, 'searchConfluencePages', 'confluence');
            const response = await this.client.get('/wiki/rest/api/content/search', {
                params: {
                    cql: cqlValidation.sanitizedValue,
                    limit: paginationValidation.sanitizedValue.maxResults,
                    start: paginationValidation.sanitizedValue.startAt,
                    expand,
                },
            });
            const results = response.data.results.map((page) => ({
                id: page.id,
                title: page.title,
                type: page.type,
                space: page.space,
                webUrl: `${this.client.defaults.baseURL}/wiki${page._links?.webui}`,
            }));
            const resultData = {
                totalResults: response.data.totalSize,
                startAt: response.data.start,
                limit: response.data.limit,
                results,
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
    async listConfluenceSpaces(args) {
        try {
            const { type, status = 'current', limit = 25, start = 0 } = args;
            const paginationValidation = validatePagination(start, limit);
            if (!paginationValidation.isValid)
                return createValidationError(paginationValidation.errors, 'listConfluenceSpaces', 'confluence');
            const params = {
                limit: paginationValidation.sanitizedValue.maxResults,
                start: paginationValidation.sanitizedValue.startAt,
                status,
            };
            if (type) {
                const typeValidation = validateString(type, 'type');
                if (!typeValidation.isValid)
                    return createValidationError(typeValidation.errors, 'listConfluenceSpaces', 'confluence');
                params.type = typeValidation.sanitizedValue;
            }
            const response = await this.client.get('/wiki/rest/api/space', { params });
            const results = response.data.results.map((space) => ({
                id: space.id,
                key: space.key,
                name: space.name,
                type: space.type,
                status: space.status,
                webUrl: `${this.client.defaults.baseURL}/wiki${space._links?.webui}`,
            }));
            const resultData = {
                totalResults: response.data.size,
                startAt: response.data.start,
                limit: response.data.limit,
                results,
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
    async listConfluenceAttachments(args) {
        try {
            const { pageId, mediaType, filename, limit = 50, start = 0 } = args;
            const pageIdValidation = validateString(pageId, 'pageId', { required: true });
            if (!pageIdValidation.isValid)
                return createValidationError(pageIdValidation.errors, 'listConfluenceAttachments', 'confluence');
            const paginationValidation = validatePagination(start, limit);
            if (!paginationValidation.isValid)
                return createValidationError(paginationValidation.errors, 'listConfluenceAttachments', 'confluence');
            const params = {
                limit: paginationValidation.sanitizedValue.maxResults,
                start: paginationValidation.sanitizedValue.startAt,
            };
            if (mediaType) {
                const mediaTypeValidation = validateString(mediaType, 'mediaType');
                if (!mediaTypeValidation.isValid)
                    return createValidationError(mediaTypeValidation.errors, 'listConfluenceAttachments', 'confluence');
                params.mediaType = mediaTypeValidation.sanitizedValue;
            }
            if (filename) {
                const filenameValidation = validateString(filename, 'filename');
                if (!filenameValidation.isValid)
                    return createValidationError(filenameValidation.errors, 'listConfluenceAttachments', 'confluence');
                params.filename = filenameValidation.sanitizedValue;
            }
            const response = await this.client.get(`/wiki/rest/api/content/${pageIdValidation.sanitizedValue}/child/attachment`, {
                params,
            });
            const attachments = response.data.results.map((attachment) => ({
                id: attachment.id,
                title: attachment.title,
                mediaType: attachment.extensions.mediaType,
                fileSize: attachment.extensions.fileSize,
                version: attachment.version.number,
                downloadUrl: `${this.client.defaults.baseURL}/wiki${attachment._links?.download}`,
                webUrl: `${this.client.defaults.baseURL}/wiki${attachment._links?.webui}`,
            }));
            const resultData = {
                totalResults: response.data.size,
                startAt: response.data.start,
                limit: response.data.limit,
                pageId,
                attachments,
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
    async downloadConfluenceAttachment(args) {
        try {
            const { attachmentId, version } = args;
            const attachmentIdValidation = validateString(attachmentId, 'attachmentId', {
                required: true,
            });
            if (!attachmentIdValidation.isValid)
                return createValidationError(attachmentIdValidation.errors, 'downloadConfluenceAttachment', 'confluence');
            if (version) {
                const versionValidation = validateNumber(version, 'version', { integer: true });
                if (!versionValidation.isValid)
                    return createValidationError(versionValidation.errors, 'downloadConfluenceAttachment', 'confluence');
            }
            // First get attachment metadata
            const metadataResponse = await this.client.get(`/wiki/rest/api/content/${attachmentIdValidation.sanitizedValue}`, {
                params: {
                    expand: 'version,metadata',
                },
            });
            const attachment = metadataResponse.data;
            // Use the download link from the attachment metadata
            if (!attachment._links?.download) {
                return {
                    content: [{ type: 'text', text: 'No download link available for this attachment' }],
                    isError: true,
                };
            }
            // Build the download URL
            let downloadPath = `/wiki${attachment._links.download}`;
            // If a specific version is requested, update the URL
            if (version && version !== attachment.version.number) {
                // Parse existing URL and update version parameter
                const url = new URL(downloadPath, this.client.defaults.baseURL);
                url.searchParams.set('version', version.toString());
                downloadPath = url.pathname + url.search;
            }
            // Download the attachment
            const downloadResponse = await this.client.get(downloadPath, {
                responseType: 'arraybuffer',
            });
            // Convert to base64
            const base64Data = Buffer.from(downloadResponse.data).toString('base64');
            const result = {
                id: attachment.id,
                title: attachment.title,
                mediaType: attachment.metadata?.mediaType ||
                    attachment.extensions?.mediaType ||
                    'application/octet-stream',
                fileSize: downloadResponse.data.byteLength,
                version: attachment.version.number,
                base64Data,
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
    async downloadConfluencePageComplete(args) {
        try {
            const { pageId, includeAttachments = true, attachmentTypes, maxAttachmentSize = 52428800, // 50MB default
             } = args;
            const pageIdValidation = validateString(pageId, 'pageId', { required: true });
            if (!pageIdValidation.isValid)
                return createValidationError(pageIdValidation.errors, 'downloadConfluencePageComplete', 'confluence');
            if (attachmentTypes) {
                const attachmentTypesValidation = validateStringArray(attachmentTypes, 'attachmentTypes');
                if (!attachmentTypesValidation.isValid)
                    return createValidationError(attachmentTypesValidation.errors, 'downloadConfluencePageComplete', 'confluence');
            }
            const maxAttachmentSizeValidation = validateNumber(maxAttachmentSize, 'maxAttachmentSize', {
                integer: true,
                min: 0,
            });
            if (!maxAttachmentSizeValidation.isValid)
                return createValidationError(maxAttachmentSizeValidation.errors, 'downloadConfluencePageComplete', 'confluence');
            // Get page content with all expansions
            const pageResponse = await this.client.get(`/wiki/rest/api/content/${pageIdValidation.sanitizedValue}`, {
                params: {
                    expand: 'body.storage,body.view,version,space,ancestors,descendants,metadata.labels',
                },
            });
            const page = pageResponse.data;
            const result = {
                page: {
                    id: page.id,
                    title: page.title,
                    version: page.version?.number,
                    space: page.space,
                    webUrl: `${this.client.defaults.baseURL}/wiki${page._links?.webui}`,
                    content: {
                        storage: page.body?.storage?.value,
                        view: page.body?.view?.value,
                    },
                    metadata: {
                        labels: page.metadata?.labels?.results || [],
                        created: page.version?.when,
                        createdBy: page.version?.by?.displayName,
                    },
                    ancestors: page.ancestors || [],
                },
                attachments: [],
            };
            if (includeAttachments) {
                // Get all attachments for the page
                const attachmentsResponse = await this.client.get(`/wiki/rest/api/content/${pageId}/child/attachment`, {
                    params: {
                        limit: 100,
                        expand: 'version,metadata',
                    },
                });
                const attachments = attachmentsResponse.data.results;
                const downloadPromises = [];
                for (const attachment of attachments) {
                    // Filter by type if specified
                    if (attachmentTypes && attachmentTypes.length > 0) {
                        if (!attachmentTypes.includes(attachment.extensions.mediaType)) {
                            continue;
                        }
                    }
                    // Skip if too large
                    if (attachment.extensions.fileSize > maxAttachmentSize) {
                        result.attachments.push({
                            id: attachment.id,
                            title: attachment.title,
                            mediaType: attachment.extensions.mediaType,
                            fileSize: attachment.extensions.fileSize,
                            skipped: true,
                            reason: `File size (${attachment.extensions.fileSize} bytes) exceeds maximum (${maxAttachmentSize} bytes)`,
                        });
                        continue;
                    }
                    // Download attachment
                    const downloadPromise = (async () => {
                        try {
                            if (!attachment._links?.download) {
                                return {
                                    id: attachment.id,
                                    title: attachment.title,
                                    mediaType: attachment.extensions.mediaType,
                                    fileSize: attachment.extensions.fileSize,
                                    error: 'No download link available',
                                };
                            }
                            const downloadPath = `/wiki${attachment._links.download}`;
                            const downloadResponse = await this.client.get(downloadPath, {
                                responseType: 'arraybuffer',
                            });
                            const base64Data = Buffer.from(downloadResponse.data).toString('base64');
                            return {
                                id: attachment.id,
                                title: attachment.title,
                                mediaType: attachment.extensions.mediaType,
                                fileSize: downloadResponse.data.byteLength,
                                version: attachment.version.number,
                                base64Data,
                            };
                        }
                        catch (error) {
                            return {
                                id: attachment.id,
                                title: attachment.title,
                                mediaType: attachment.extensions.mediaType,
                                fileSize: attachment.extensions.fileSize,
                                error: formatApiError(error),
                            };
                        }
                    })();
                    downloadPromises.push(downloadPromise);
                }
                // Wait for all downloads to complete
                const downloadedAttachments = await Promise.all(downloadPromises);
                result.attachments.push(...downloadedAttachments);
                // Add summary
                result.summary = {
                    totalAttachments: attachments.length,
                    downloadedAttachments: downloadedAttachments.filter((a) => a.base64Data).length,
                    skippedAttachments: result.attachments.filter((a) => a.skipped).length,
                    failedAttachments: downloadedAttachments.filter((a) => a.error && !a.skipped).length,
                };
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
    async createConfluencePage(args) {
        try {
            const { spaceKey, title, content, parentId, type = 'page' } = args;
            const spaceKeyValidation = validateString(spaceKey, 'spaceKey', { required: true });
            if (!spaceKeyValidation.isValid)
                return createValidationError(spaceKeyValidation.errors, 'createConfluencePage', 'confluence');
            const titleValidation = validateString(title, 'title', { required: true });
            if (!titleValidation.isValid)
                return createValidationError(titleValidation.errors, 'createConfluencePage', 'confluence');
            const contentValidation = validateString(content, 'content', { required: true });
            if (!contentValidation.isValid)
                return createValidationError(contentValidation.errors, 'createConfluencePage', 'confluence');
            if (parentId) {
                const parentIdValidation = validateString(parentId, 'parentId');
                if (!parentIdValidation.isValid)
                    return createValidationError(parentIdValidation.errors, 'createConfluencePage', 'confluence');
            }
            // Convert to storage format if needed
            const storageContent = ContentConverter.ensureStorageFormat(contentValidation.sanitizedValue);
            const requestBody = {
                type,
                title: titleValidation.sanitizedValue,
                space: {
                    key: spaceKeyValidation.sanitizedValue,
                },
                body: {
                    storage: {
                        value: storageContent,
                        representation: 'storage',
                    },
                },
            };
            // Add parent relationship if specified
            if (parentId) {
                requestBody.ancestors = [{ id: parentId }];
            }
            const response = await this.client.post('/wiki/rest/api/content', requestBody);
            const result = {
                id: response.data.id,
                title: response.data.title,
                type: response.data.type,
                space: response.data.space,
                version: response.data.version?.number,
                webUrl: `${this.client.defaults.baseURL}/wiki${response.data._links?.webui}`,
                message: 'Page created successfully',
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
    async updateConfluencePage(args) {
        try {
            const { pageId, title, content, version, minorEdit = false, versionComment } = args;
            const pageIdValidation = validateString(pageId, 'pageId', { required: true });
            if (!pageIdValidation.isValid)
                return createValidationError(pageIdValidation.errors, 'updateConfluencePage', 'confluence');
            const versionValidation = validateNumber(version, 'version', {
                required: true,
                integer: true,
            });
            if (!versionValidation.isValid)
                return createValidationError(versionValidation.errors, 'updateConfluencePage', 'confluence');
            // First, get the current page to maintain existing properties
            const currentPageResponse = await this.client.get(`/wiki/rest/api/content/${pageIdValidation.sanitizedValue}`, {
                params: { expand: 'body.storage,version,space' },
            });
            const currentPage = currentPageResponse.data;
            // Prepare update request
            const requestBody = {
                id: pageIdValidation.sanitizedValue,
                type: currentPage.type,
                title: title || currentPage.title,
                space: currentPage.space,
                version: {
                    number: versionValidation.sanitizedValue,
                    minorEdit,
                },
                body: currentPage.body,
            };
            if (title) {
                const titleValidation = validateString(title, 'title');
                if (!titleValidation.isValid)
                    return createValidationError(titleValidation.errors, 'updateConfluencePage', 'confluence');
                requestBody.title = titleValidation.sanitizedValue;
            }
            // Add version comment if provided
            if (versionComment) {
                const versionCommentValidation = validateString(versionComment, 'versionComment');
                if (!versionCommentValidation.isValid)
                    return createValidationError(versionCommentValidation.errors, 'updateConfluencePage', 'confluence');
                requestBody.version.message = versionCommentValidation.sanitizedValue;
            }
            // Update content if provided
            if (content) {
                const contentValidation = validateString(content, 'content');
                if (!contentValidation.isValid)
                    return createValidationError(contentValidation.errors, 'updateConfluencePage', 'confluence');
                const storageContent = ContentConverter.ensureStorageFormat(contentValidation.sanitizedValue);
                requestBody.body = {
                    storage: {
                        value: storageContent,
                        representation: 'storage',
                    },
                };
            }
            else {
                requestBody.body = currentPage.body;
            }
            const response = await this.client.put(`/wiki/rest/api/content/${pageIdValidation.sanitizedValue}`, requestBody);
            const result = {
                id: response.data.id,
                title: response.data.title,
                version: response.data.version?.number,
                previousVersion: version,
                webUrl: `${this.client.defaults.baseURL}/wiki${response.data._links?.webui}`,
                message: 'Page updated successfully',
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
    async addConfluenceComment(args) {
        try {
            const { pageId, content, parentCommentId } = args;
            const pageIdValidation = validateString(pageId, 'pageId', { required: true });
            if (!pageIdValidation.isValid)
                return createValidationError(pageIdValidation.errors, 'addConfluenceComment', 'confluence');
            const contentValidation = validateString(content, 'content', { required: true });
            if (!contentValidation.isValid)
                return createValidationError(contentValidation.errors, 'addConfluenceComment', 'confluence');
            if (parentCommentId) {
                const parentCommentIdValidation = validateString(parentCommentId, 'parentCommentId');
                if (!parentCommentIdValidation.isValid)
                    return createValidationError(parentCommentIdValidation.errors, 'addConfluenceComment', 'confluence');
            }
            // Convert to storage format if needed
            const storageContent = ContentConverter.ensureStorageFormat(contentValidation.sanitizedValue);
            const requestBody = {
                type: 'comment',
                container: {
                    id: pageIdValidation.sanitizedValue,
                    type: 'page',
                },
                body: {
                    storage: {
                        value: storageContent,
                        representation: 'storage',
                    },
                },
            };
            // Add parent comment relationship if specified
            if (parentCommentId) {
                requestBody.ancestors = [{ id: parentCommentId }];
            }
            const response = await this.client.post('/wiki/rest/api/content', requestBody);
            const result = {
                id: response.data.id,
                type: response.data.type,
                pageId,
                parentCommentId,
                version: response.data.version?.number,
                createdBy: response.data.version?.by?.displayName,
                createdAt: response.data.version?.when,
                webUrl: `${this.client.defaults.baseURL}/wiki${response.data._links?.webui}`,
                message: 'Comment added successfully',
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
    async findConfluenceUsers(args) {
        try {
            const { cql, username, userKey, accountId, expand, limit = 25, start = 0 } = args;
            const paginationValidation = validatePagination(start, limit);
            if (!paginationValidation.isValid)
                return createValidationError(paginationValidation.errors, 'findConfluenceUsers', 'confluence');
            // Build query parameters
            const params = {
                limit: paginationValidation.sanitizedValue.maxResults,
                start: paginationValidation.sanitizedValue.startAt,
            };
            if (cql) {
                const cqlValidation = validateString(cql, 'cql');
                if (!cqlValidation.isValid)
                    return createValidationError(cqlValidation.errors, 'findConfluenceUsers', 'confluence');
                params.cql = cqlValidation.sanitizedValue;
            }
            if (username) {
                const usernameValidation = validateString(username, 'username');
                if (!usernameValidation.isValid)
                    return createValidationError(usernameValidation.errors, 'findConfluenceUsers', 'confluence');
                params.username = usernameValidation.sanitizedValue;
            }
            if (userKey) {
                const userKeyValidation = validateString(userKey, 'userKey');
                if (!userKeyValidation.isValid)
                    return createValidationError(userKeyValidation.errors, 'findConfluenceUsers', 'confluence');
                params.key = userKeyValidation.sanitizedValue;
            }
            if (accountId) {
                const accountIdValidation = validateString(accountId, 'accountId');
                if (!accountIdValidation.isValid)
                    return createValidationError(accountIdValidation.errors, 'findConfluenceUsers', 'confluence');
                params.accountId = accountIdValidation.sanitizedValue;
            }
            if (expand) {
                const expandValidation = validateString(expand, 'expand');
                if (!expandValidation.isValid)
                    return createValidationError(expandValidation.errors, 'findConfluenceUsers', 'confluence');
                params.expand = expandValidation.sanitizedValue;
            }
            // Try different endpoints based on Confluence version
            let response;
            try {
                // Try the standard user search endpoint first
                response = await this.client.get('/wiki/rest/api/user/search', { params });
            }
            catch (error) {
                // If that fails, try the alternative search/user endpoint
                try {
                    response = await this.client.get('/wiki/rest/api/search/user', { params });
                }
                catch (searchError) {
                    // If both fail, return a helpful message
                    return {
                        content: [
                            {
                                type: 'text',
                                text: JSON.stringify({
                                    message: 'User search endpoint not available. This might be due to Confluence version or permissions.',
                                    suggestion: 'Try using the Confluence web interface to search for users.',
                                    error: formatApiError(error),
                                }, null, 2),
                            },
                        ],
                        isError: false, // Not marking as error since it's a known limitation
                    };
                }
            }
            const users = response.data.results?.map((user) => ({
                userKey: user.userKey,
                username: user.username,
                accountId: user.accountId,
                displayName: user.displayName,
                email: user.email,
                profilePicture: user.profilePicture,
                active: user.active,
            })) || [];
            const result = {
                totalResults: response.data.size || users.length,
                startAt: response.data.start || start,
                limit: response.data.limit || limit,
                users,
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
    async getConfluenceLabels(args) {
        try {
            const { pageId, prefix, limit = 25, start = 0 } = args;
            const pageIdValidation = validateString(pageId, 'pageId', { required: true });
            if (!pageIdValidation.isValid)
                return createValidationError(pageIdValidation.errors, 'getConfluenceLabels', 'confluence');
            const paginationValidation = validatePagination(start, limit);
            if (!paginationValidation.isValid)
                return createValidationError(paginationValidation.errors, 'getConfluenceLabels', 'confluence');
            const params = {
                limit: paginationValidation.sanitizedValue.maxResults,
                start: paginationValidation.sanitizedValue.startAt,
            };
            if (prefix) {
                const prefixValidation = validateString(prefix, 'prefix');
                if (!prefixValidation.isValid)
                    return createValidationError(prefixValidation.errors, 'getConfluenceLabels', 'confluence');
                params.prefix = prefixValidation.sanitizedValue;
            }
            const response = await this.client.get(`/wiki/rest/api/content/${pageIdValidation.sanitizedValue}/label`, { params });
            const labels = response.data.results?.map((label) => ({
                prefix: label.prefix,
                name: label.name,
                id: label.id,
                label: label.label,
            })) || [];
            const result = {
                pageId,
                totalResults: response.data.size || labels.length,
                startAt: response.data.start || start,
                limit: response.data.limit || limit,
                labels,
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
    async addConfluenceLabels(args) {
        try {
            const { pageId, labels } = args;
            const pageIdValidation = validateString(pageId, 'pageId', { required: true });
            if (!pageIdValidation.isValid)
                return createValidationError(pageIdValidation.errors, 'addConfluenceLabels', 'confluence');
            // Basic validation for labels array
            if (!Array.isArray(labels) || labels.length === 0) {
                return createValidationError(['labels must be a non-empty array'], 'addConfluenceLabels', 'confluence');
            }
            // Format labels for the API
            const formattedLabels = labels.map((label) => ({
                prefix: label.prefix || 'global',
                name: label.name,
            }));
            const response = await this.client.post(`/wiki/rest/api/content/${pageIdValidation.sanitizedValue}/label`, formattedLabels);
            const addedLabels = response.data.results?.map((label) => ({
                prefix: label.prefix,
                name: label.name,
                id: label.id,
                label: label.label,
            })) || [];
            const result = {
                pageId,
                addedLabels,
                totalLabels: addedLabels.length,
                message: `Successfully added ${addedLabels.length} label(s) to page`,
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
    async exportConfluencePage(args) {
        try {
            const { pageId, format } = args;
            console.error(`Exporting page ${pageId} to ${format.toUpperCase()} format...`);
            // Step 1: Get the page content with export view
            const pageResponse = await this.client.get(`/wiki/rest/api/content/${pageId}`, {
                params: {
                    expand: 'body.export_view,space,version',
                },
            });
            if (!pageResponse.data?.body?.export_view) {
                return {
                    content: [
                        {
                            type: 'text',
                            text: JSON.stringify({
                                error: 'Could not retrieve page export view',
                                message: 'The page may not have export view available',
                                pageId,
                            }, null, 2),
                        },
                    ],
                    isError: true,
                };
            }
            const page = pageResponse.data;
            let htmlContent = page.body.export_view.value;
            // Sanitize the HTML content immediately after retrieving it to prevent XSS.
            htmlContent = sanitizeHtml(htmlContent);
            const title = page.title;
            const baseUrl = this.client.defaults.baseURL || '';
            console.error(`Page retrieved: "${title}", processing content...`);
            // Step 2: Process and embed all images
            const imageResult = await ExportConverter.processImages(htmlContent, this.client, true // Always embed images
            );
            htmlContent = imageResult.html;
            const processedImages = imageResult.images;
            console.error(`Processed and embedded ${processedImages.length} images`);
            let exportContent;
            let mimeType;
            let fileExtension;
            if (format === 'html') {
                // Step 3a: Return just the HTML content without wrapper
                exportContent = htmlContent;
                mimeType = 'text/html';
                fileExtension = 'html';
            }
            else {
                // Step 3b: Convert to Markdown
                const markdownContent = ExportConverter.htmlToMarkdown(htmlContent);
                // Create markdown document with metadata
                exportContent = ExportConverter.createMarkdownDocument(markdownContent, {
                    title,
                    space: page.space?.name,
                    spaceKey: page.space?.key,
                    version: page.version?.number,
                    modified: page.version?.when ? new Date(page.version.when) : undefined,
                    pageId,
                    sourceUrl: `${baseUrl}/wiki${page._links?.webui || ''}`,
                });
                mimeType = 'text/markdown';
                fileExtension = 'md';
            }
            // Step 4: Return as base64
            const contentBuffer = Buffer.from(exportContent, 'utf-8');
            const base64Data = contentBuffer.toString('base64');
            const result = {
                pageId,
                title,
                format,
                spaceKey: page.space?.key,
                spaceName: page.space?.name,
                filename: `${title.replace(/[^a-z0-9]/gi, '_')}.${fileExtension}`,
                fileSize: contentBuffer.length,
                mimeType,
                base64Data,
                imagesEmbedded: processedImages.length,
                webUrl: `${baseUrl}/wiki${page._links?.webui || ''}`,
                message: `Page exported successfully to ${format.toUpperCase()} format with ${processedImages.length} embedded images`,
                exportMethod: format === 'html' ? 'html-export' : 'markdown-conversion',
                timestamp: new Date().toISOString(),
            };
            return {
                content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
            };
        }
        catch (error) {
            console.error('Export error:', error);
            return {
                content: [
                    {
                        type: 'text',
                        text: JSON.stringify({
                            error: 'Export failed',
                            message: error instanceof Error ? error.message : String(error),
                            pageId: args.pageId,
                            format: args.format,
                            suggestion: 'Ensure the page exists and has proper permissions',
                        }, null, 2),
                    },
                ],
                isError: true,
            };
        }
    }
    async getConfluenceCurrentUser() {
        try {
            const response = await this.client.get('/api/user/current');
            const user = response.data;
            const result = {
                accountId: user.accountId,
                displayName: user.displayName,
                publicName: user.publicName,
                email: user.email,
                profilePicture: user.profilePicture,
                type: user.type,
                profileUrl: `${this.client.defaults.baseURL}/wiki/people/${user.accountId}`,
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
    async getConfluenceSpace(args) {
        try {
            const { spaceKey, expand = 'description.plain,homepage' } = args;
            const spaceKeyValidation = validateString(spaceKey, 'spaceKey', { required: true });
            if (!spaceKeyValidation.isValid)
                return createValidationError(spaceKeyValidation.errors, 'getConfluenceSpace', 'confluence');
            const response = await this.client.get(`/api/space/${spaceKeyValidation.sanitizedValue}`, {
                params: { expand },
            });
            const space = response.data;
            const result = {
                id: space.id,
                key: space.key,
                name: space.name,
                type: space.type,
                status: space.status,
                description: space.description?.plain?.value,
                webUrl: `${this.client.defaults.baseURL}/wiki/spaces/${space.key}`,
                _links: space._links,
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
    async listConfluencePageChildren(args) {
        try {
            const { pageId, limit = 25, start = 0, expand = 'space' } = args;
            const pageIdValidation = validateString(pageId, 'pageId', { required: true });
            if (!pageIdValidation.isValid)
                return createValidationError(pageIdValidation.errors, 'listConfluencePageChildren', 'confluence');
            const paginationValidation = validatePagination(start, limit);
            if (!paginationValidation.isValid)
                return createValidationError(paginationValidation.errors, 'listConfluencePageChildren', 'confluence');
            const response = await this.client.get(`/api/content/${pageIdValidation.sanitizedValue}/child/page`, {
                params: {
                    limit: paginationValidation.sanitizedValue.maxResults,
                    start: paginationValidation.sanitizedValue.startAt,
                    expand,
                },
            });
            const children = response.data.results.map((page) => ({
                id: page.id,
                title: page.title,
                type: page.type,
                status: page.status,
                spaceKey: page.space?.key,
                webUrl: `${this.client.defaults.baseURL}/wiki${page._links?.webui || ''}`,
            }));
            const resultData = {
                parentPageId: pageId,
                totalChildren: response.data.size,
                start: response.data.start,
                limit: response.data.limit,
                children,
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
    async listConfluencePageAncestors(args) {
        try {
            const { pageId } = args;
            const pageIdValidation = validateString(pageId, 'pageId', { required: true });
            if (!pageIdValidation.isValid)
                return createValidationError(pageIdValidation.errors, 'listConfluencePageAncestors', 'confluence');
            // First get the page with ancestors expanded
            const response = await this.client.get(`/api/content/${pageIdValidation.sanitizedValue}`, {
                params: {
                    expand: 'ancestors',
                },
            });
            const page = response.data;
            const ancestors = page.ancestors?.map((ancestor) => ({
                id: ancestor.id,
                title: ancestor.title,
                type: ancestor.type,
                status: ancestor.status,
                webUrl: `${this.client.defaults.baseURL}/wiki${ancestor._links?.webui || ''}`,
            })) || [];
            const resultData = {
                pageId,
                pageTitle: page.title,
                ancestors: ancestors.reverse(), // Root first, immediate parent last
                depth: ancestors.length,
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
    async uploadConfluenceAttachment(args) {
        try {
            const { pageId, file, filename, comment, minorEdit = false } = args;
            const pageIdValidation = validateString(pageId, 'pageId', { required: true });
            if (!pageIdValidation.isValid)
                return createValidationError(pageIdValidation.errors, 'uploadConfluenceAttachment', 'confluence');
            const fileValidation = validateString(file, 'file', { required: true });
            if (!fileValidation.isValid)
                return createValidationError(fileValidation.errors, 'uploadConfluenceAttachment', 'confluence');
            const filenameValidation = validateString(filename, 'filename', { required: true });
            if (!filenameValidation.isValid)
                return createValidationError(filenameValidation.errors, 'uploadConfluenceAttachment', 'confluence');
            // Convert base64 file to buffer
            const fileBuffer = Buffer.from(fileValidation.sanitizedValue, 'base64');
            // Create form data
            const { default: FormData } = await import('form-data');
            const form = new FormData();
            form.append('file', fileBuffer, filename);
            if (comment) {
                form.append('comment', comment);
            }
            form.append('minorEdit', String(minorEdit));
            const response = await this.client.post(`/api/content/${pageId}/child/attachment`, form, {
                headers: {
                    ...form.getHeaders(),
                    'X-Atlassian-Token': 'no-check', // Required for file uploads
                },
            });
            const attachment = response.data.results[0];
            const result = {
                id: attachment.id,
                title: attachment.title,
                filename: attachment.title,
                fileSize: attachment.extensions?.fileSize,
                mediaType: attachment.metadata?.mediaType,
                comment: attachment.extensions?.comment,
                version: attachment.version?.number,
                downloadUrl: `${this.client.defaults.baseURL}/wiki${attachment._links?.download}`,
                webUrl: `${this.client.defaults.baseURL}/wiki${attachment._links?.webui}`,
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
    async getMyRecentConfluencePages(args) {
        try {
            const { limit = 25, start = 0, spaceKey } = args;
            const paginationValidation = validatePagination(start, limit);
            if (!paginationValidation.isValid)
                return createValidationError(paginationValidation.errors, 'getMyRecentConfluencePages', 'confluence');
            if (spaceKey) {
                const spaceKeyValidation = validateString(spaceKey, 'spaceKey');
                if (!spaceKeyValidation.isValid)
                    return createValidationError(spaceKeyValidation.errors, 'getMyRecentConfluencePages', 'confluence');
            }
            // Get current user
            const currentUser = await this._getCurrentUser();
            // Build CQL query
            let cql = `creator = "${currentUser.accountId}" OR lastModifier = "${currentUser.accountId}"`;
            if (spaceKey) {
                cql = `space = ${spaceKey} AND (${cql})`;
            }
            cql += ' ORDER BY lastmodified DESC';
            const response = await this.client.get('/api/content/search', {
                params: {
                    cql,
                    limit: Math.min(limit, 100),
                    start,
                    expand: 'space,version',
                },
            });
            const pages = response.data.results.map((page) => ({
                id: page.id,
                title: page.title,
                type: page.type,
                spaceKey: page.space?.key,
                spaceName: page.space?.name,
                version: page.version?.number,
                lastModified: page.version?.when,
                webUrl: `${this.client.defaults.baseURL}/wiki${page._links?.webui || ''}`,
            }));
            const resultData = {
                currentUser: currentUser.displayName,
                totalPages: response.data.totalSize,
                start: response.data.start,
                limit: response.data.limit,
                pages,
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
    async getConfluencePagesMentioningMe(args) {
        try {
            const { limit = 25, start = 0, spaceKey } = args;
            const paginationValidation = validatePagination(start, limit);
            if (!paginationValidation.isValid)
                return createValidationError(paginationValidation.errors, 'getConfluencePagesMentioningMe', 'confluence');
            if (spaceKey) {
                const spaceKeyValidation = validateString(spaceKey, 'spaceKey');
                if (!spaceKeyValidation.isValid)
                    return createValidationError(spaceKeyValidation.errors, 'getConfluencePagesMentioningMe', 'confluence');
            }
            // Get current user
            const currentUser = await this._getCurrentUser();
            // Build CQL query to find mentions
            let cql = `mention = "${currentUser.accountId}"`;
            if (spaceKey) {
                cql = `space = ${spaceKey} AND ${cql}`;
            }
            cql += ' ORDER BY lastmodified DESC';
            const response = await this.client.get('/api/content/search', {
                params: {
                    cql,
                    limit: Math.min(limit, 100),
                    start,
                    expand: 'space,version',
                },
            });
            const pages = response.data.results.map((page) => ({
                id: page.id,
                title: page.title,
                type: page.type,
                spaceKey: page.space?.key,
                spaceName: page.space?.name,
                version: page.version?.number,
                lastModified: page.version?.when,
                lastModifier: page.version?.by?.displayName,
                webUrl: `${this.client.defaults.baseURL}/wiki${page._links?.webui || ''}`,
            }));
            const resultData = {
                currentUser: currentUser.displayName,
                totalPages: response.data.totalSize,
                start: response.data.start,
                limit: response.data.limit,
                pages,
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
    async getConfluenceUser(args) {
        try {
            const { username, accountId, email } = args;
            const userValidation = validateUserIdentification({ username, accountId, email });
            if (!userValidation.isValid)
                return createValidationError(userValidation.errors, 'getConfluenceUser', 'confluence');
            // Build search parameters
            const params = {};
            if (userValidation.sanitizedValue?.username)
                params.username = userValidation.sanitizedValue.username;
            if (userValidation.sanitizedValue?.accountId)
                params.accountId = userValidation.sanitizedValue.accountId;
            if (userValidation.sanitizedValue?.email)
                params.email = userValidation.sanitizedValue.email;
            // First try to get user by accountId if provided
            let userResponse;
            if (accountId) {
                try {
                    userResponse = await this.client.get(`/api/user`, {
                        params: { accountId },
                    });
                }
                catch (e) {
                    // Fall back to search
                }
            }
            // If not found by accountId, search for user
            if (!userResponse && (username || email)) {
                const searchResponse = await this.client.get('/api/search/user', {
                    params: {
                        cql: username ? `user.fullname ~ "${username}"` : `user.email = "${email}"`,
                        limit: 1,
                    },
                });
                if (searchResponse.data.results && searchResponse.data.results.length > 0) {
                    const user = searchResponse.data.results[0].user;
                    userResponse = { data: user };
                }
            }
            if (!userResponse?.data) {
                return {
                    content: [{ type: 'text', text: 'User not found' }],
                    isError: true,
                };
            }
            const user = userResponse.data;
            const result = {
                accountId: user.accountId,
                displayName: user.displayName,
                publicName: user.publicName,
                email: user.email,
                profilePicture: user.profilePicture,
                type: user.type,
                profileUrl: `${this.client.defaults.baseURL}/wiki/people/${user.accountId}`,
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
    async searchConfluencePagesByUser(args) {
        try {
            const { username, accountId, searchType, spaceKey, limit = 25, start = 0 } = args;
            const userValidation = validateUserIdentification({ username, accountId });
            if (!userValidation.isValid)
                return createValidationError(userValidation.errors, 'searchConfluencePagesByUser', 'confluence');
            const paginationValidation = validatePagination(start, limit);
            if (!paginationValidation.isValid)
                return createValidationError(paginationValidation.errors, 'searchConfluencePagesByUser', 'confluence');
            // Get user's accountId if not provided
            let userAccountId = userValidation.sanitizedValue?.accountId;
            if (!userAccountId && userValidation.sanitizedValue?.username) {
                const userResult = await this.getConfluenceUser({
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
                    content: [{ type: 'text', text: 'User account ID or username is required' }],
                    isError: true,
                };
            }
            // Build CQL query based on search type
            let cql = '';
            if (searchType === 'creator') {
                cql = `creator = "${userAccountId}"`;
            }
            else if (searchType === 'lastModifier') {
                cql = `lastModifier = "${userAccountId}"`;
            }
            else {
                cql = `(creator = "${userAccountId}" OR lastModifier = "${userAccountId}")`;
            }
            if (spaceKey) {
                cql = `space = ${spaceKey} AND ${cql}`;
            }
            cql += ' ORDER BY lastmodified DESC';
            const response = await this.client.get('/api/content/search', {
                params: {
                    cql,
                    limit: Math.min(limit, 100),
                    start,
                    expand: 'space,version,history.lastUpdated',
                },
            });
            const pages = response.data.results.map((page) => ({
                id: page.id,
                title: page.title,
                type: page.type,
                spaceKey: page.space?.key,
                spaceName: page.space?.name,
                version: page.version?.number,
                created: page.history?.createdDate,
                lastModified: page.history?.lastUpdated?.when,
                createdBy: page.history?.createdBy?.displayName,
                lastModifiedBy: page.history?.lastUpdated?.by?.displayName,
                webUrl: `${this.client.defaults.baseURL}/wiki${page._links?.webui || ''}`,
            }));
            const resultData = {
                searchType,
                user: userAccountId,
                totalPages: response.data.totalSize,
                start: response.data.start,
                limit: response.data.limit,
                pages,
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
    async listUserConfluencePages(args) {
        try {
            const { username, accountId, spaceKey, startDate, endDate, limit = 25, start = 0 } = args;
            const userValidation = validateUserIdentification({ username, accountId });
            if (!userValidation.isValid)
                return createValidationError(userValidation.errors, 'listUserConfluencePages', 'confluence');
            const paginationValidation = validatePagination(start, limit);
            if (!paginationValidation.isValid)
                return createValidationError(paginationValidation.errors, 'listUserConfluencePages', 'confluence');
            // Get user's accountId if not provided
            let userAccountId = userValidation.sanitizedValue?.accountId;
            if (!userAccountId && userValidation.sanitizedValue?.username) {
                const userResult = await this.getConfluenceUser({
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
                    content: [{ type: 'text', text: 'User account ID or username is required' }],
                    isError: true,
                };
            }
            // Build CQL query
            let cql = `creator = "${userAccountId}"`;
            if (spaceKey) {
                cql = `space = ${spaceKey} AND ${cql}`;
            }
            if (startDate && endDate) {
                cql += ` AND created >= ${startDate} AND created <= ${endDate}`;
            }
            else if (startDate) {
                cql += ` AND created >= ${startDate}`;
            }
            else if (endDate) {
                cql += ` AND created <= ${endDate}`;
            }
            cql += ' ORDER BY created DESC';
            const response = await this.client.get('/api/content/search', {
                params: {
                    cql,
                    limit: Math.min(limit, 100),
                    start,
                    expand: 'space,version,history.createdDate',
                },
            });
            const pages = response.data.results.map((page) => ({
                id: page.id,
                title: page.title,
                type: page.type,
                spaceKey: page.space?.key,
                spaceName: page.space?.name,
                version: page.version?.number,
                created: page.history?.createdDate,
                webUrl: `${this.client.defaults.baseURL}/wiki${page._links?.webui || ''}`,
            }));
            const resultData = {
                author: userAccountId,
                spaceKey: spaceKey || 'all',
                dateRange: {
                    start: startDate || 'unlimited',
                    end: endDate || 'unlimited',
                },
                totalPages: response.data.totalSize,
                start: response.data.start,
                limit: response.data.limit,
                pages,
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
    async listUserConfluenceAttachments(args) {
        try {
            const { username, accountId, spaceKey, limit = 25, start = 0 } = args;
            const userValidation = validateUserIdentification({ username, accountId });
            if (!userValidation.isValid)
                return createValidationError(userValidation.errors, 'listUserConfluenceAttachments', 'confluence');
            const paginationValidation = validatePagination(start, limit);
            if (!paginationValidation.isValid)
                return createValidationError(paginationValidation.errors, 'listUserConfluenceAttachments', 'confluence');
            // Get user's accountId if not provided
            let userAccountId = userValidation.sanitizedValue?.accountId;
            if (!userAccountId && userValidation.sanitizedValue?.username) {
                const userResult = await this.getConfluenceUser({
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
                    content: [{ type: 'text', text: 'User account ID or username is required' }],
                    isError: true,
                };
            }
            // Build CQL query for attachments
            let cql = `type = attachment AND creator = "${userAccountId}"`;
            if (spaceKey) {
                cql = `space = ${spaceKey} AND ${cql}`;
            }
            cql += ' ORDER BY created DESC';
            const response = await this.client.get('/api/content/search', {
                params: {
                    cql,
                    limit: Math.min(limit, 100),
                    start,
                    expand: 'container,space,version,metadata.mediaType,extensions.fileSize',
                },
            });
            const attachments = response.data.results.map((attachment) => ({
                id: attachment.id,
                title: attachment.title,
                filename: attachment.title,
                mediaType: attachment.metadata?.mediaType,
                fileSize: attachment.extensions?.fileSize,
                created: attachment.history?.createdDate,
                version: attachment.version?.number,
                parentPageId: attachment.container?.id,
                parentPageTitle: attachment.container?.title,
                spaceKey: attachment.space?.key,
                spaceName: attachment.space?.name,
                downloadUrl: `${this.client.defaults.baseURL}/wiki${attachment._links?.download}`,
                webUrl: `${this.client.defaults.baseURL}/wiki${attachment._links?.webui}`,
            }));
            const resultData = {
                uploader: userAccountId,
                spaceKey: spaceKey || 'all',
                totalAttachments: response.data.totalSize,
                start: response.data.start,
                limit: response.data.limit,
                attachments,
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
}
//# sourceMappingURL=handlers.js.map