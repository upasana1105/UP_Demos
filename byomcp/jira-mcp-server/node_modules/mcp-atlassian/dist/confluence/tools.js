export const confluenceTools = [
    {
        name: 'get_confluence_current_user',
        description: 'Get details of the authenticated Confluence user. Returns information about the current user including account ID, display name, email, and profile picture.',
        inputSchema: {
            type: 'object',
            properties: {},
        },
    },
    {
        name: 'get_confluence_user',
        description: 'Get details for a specific Confluence user by a unique identifier like username, account ID, or email. Returns user profile information. **Use this tool when you are confident you can uniquely identify a user.**',
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
        name: 'search_pages_by_user_involvement',
        description: 'Search pages based on a user\'s involvement, such as being the creator or last modifier. Can filter by creator, last modifier, or both.',
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
                    enum: ['creator', 'lastModifier', 'both'],
                    description: 'Search for pages created by the user, modified by the user, or both.',
                },
                spaceKey: {
                    type: 'string',
                    description: 'Optional space key to filter results to a specific space.',
                },
                limit: {
                    type: 'number',
                    description: 'The maximum number of pages to return. Default is 25, maximum is 100.',
                    default: 25,
                    minimum: 1,
                    maximum: 100,
                },
                start: {
                    type: 'number',
                    description: 'The starting index for pagination. Default is 0.',
                    default: 0,
                },
            },
            required: ['searchType'],
        },
    },
    {
        name: 'list_pages_created_by_user',
        description: 'List all pages created by a specific user, with optional filtering by space or time range.',
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
                spaceKey: {
                    type: 'string',
                    description: 'Optional space key to filter results to a specific space.',
                },
                startDate: {
                    type: 'string',
                    description: 'Start date for filtering pages (format: YYYY-MM-DD).',
                },
                endDate: {
                    type: 'string',
                    description: 'End date for filtering pages (format: YYYY-MM-DD).',
                },
                limit: {
                    type: 'number',
                    description: 'The maximum number of pages to return. Default is 25, maximum is 100.',
                    default: 25,
                    minimum: 1,
                    maximum: 100,
                },
                start: {
                    type: 'number',
                    description: 'The starting index for pagination. Default is 0.',
                    default: 0,
                },
            },
        },
    },
    {
        name: 'list_attachments_uploaded_by_user',
        description: 'List all attachments uploaded by a specific user, with optional filtering by space.',
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
                spaceKey: {
                    type: 'string',
                    description: 'Optional space key to filter results to a specific space.',
                },
                limit: {
                    type: 'number',
                    description: 'The maximum number of attachments to return. Default is 25, maximum is 100.',
                    default: 25,
                    minimum: 1,
                    maximum: 100,
                },
                start: {
                    type: 'number',
                    description: 'The starting index for pagination. Default is 0.',
                    default: 0,
                },
            },
        },
    },
    {
        name: 'read_confluence_page',
        description: 'Retrieves the content of a Confluence page. You can specify the page by its ID or by its title and space key. The content can be returned in raw storage format (XHTML) or converted to Markdown. **Use this for quickly reading the text content of a page.**',
        inputSchema: {
            type: 'object',
            properties: {
                pageId: {
                    type: 'string',
                    description: 'The unique identifier of the Confluence page (e.g., "12345678").',
                },
                title: {
                    type: 'string',
                    description: 'The title of the page. Must be used in conjunction with `spaceKey`.',
                },
                spaceKey: {
                    type: 'string',
                    description: 'The key of the space where the page is located (e.g., "DEV"). Required when using `title`.',
                },
                expand: {
                    type: 'string',
                    description: 'A comma-separated list of properties to expand in the response (e.g., "body.storage,version,space").',
                    default: 'body.storage,version,space',
                },
                format: {
                    type: 'string',
                    description: "The desired format for the page content. `storage` returns Confluence's native XHTML format. `markdown` converts the content to Markdown.",
                    enum: ['storage', 'markdown'],
                    default: 'storage',
                },
            },
        },
    },
    {
        name: 'search_confluence_pages',
        description: 'Performs a search for Confluence pages using Confluence Query Language (CQL). This is useful for finding pages that match specific criteria.',
        inputSchema: {
            type: 'object',
            properties: {
                cql: {
                    type: 'string',
                    description: 'The CQL query string. For example, to find all pages in the "DEV" space containing the word "architecture", use: `space = DEV AND text ~ "architecture"`.',
                },
                limit: {
                    type: 'number',
                    description: 'The maximum number of pages to return. The default is 25, and the maximum is 100.',
                    default: 25,
                    minimum: 1,
                    maximum: 100,
                },
                start: {
                    type: 'number',
                    description: 'The starting index for pagination. Default is 0.',
                    default: 0,
                },
                expand: {
                    type: 'string',
                    description: 'A comma-separated list of properties to expand for each page in the results.',
                },
            },
            required: ['cql'],
        },
    },
    {
        name: 'list_confluence_spaces',
        description: 'Lists all Confluence spaces that the user has permission to view. Can be filtered by type and status.',
        inputSchema: {
            type: 'object',
            properties: {
                type: {
                    type: 'string',
                    description: 'Filter spaces by type: `global` for site-wide spaces or `personal` for user spaces.',
                    enum: ['global', 'personal'],
                },
                status: {
                    type: 'string',
                    description: 'Filter spaces by status: `current` for active spaces or `archived` for archived spaces. Default is `current`.',
                    enum: ['current', 'archived'],
                    default: 'current',
                },
                limit: {
                    type: 'number',
                    description: 'The maximum number of spaces to return. Default is 25, maximum is 100.',
                    default: 25,
                    minimum: 1,
                    maximum: 100,
                },
            },
        },
    },
    {
        name: 'get_confluence_space',
        description: 'Get details of a specific Confluence space by its key. Returns space information including name, type, status, and description.',
        inputSchema: {
            type: 'object',
            properties: {
                spaceKey: {
                    type: 'string',
                    description: 'The key of the space to retrieve (e.g., "DEV").',
                },
                expand: {
                    type: 'string',
                    description: 'Properties to expand in the response (e.g., "description.plain,homepage").',
                    default: 'description.plain,homepage',
                },
            },
            required: ['spaceKey'],
        },
    },
    {
        name: 'list_attachments_on_page',
        description: 'Lists all attachments for a specific Confluence page. Can be filtered by filename or media type.',
        inputSchema: {
            type: 'object',
            properties: {
                pageId: {
                    type: 'string',
                    description: 'The ID of the Confluence page whose attachments are to be listed.',
                },
                mediaType: {
                    type: 'string',
                    description: 'Filter attachments by their MIME type (e.g., "image/png", "application/pdf").',
                },
                filename: {
                    type: 'string',
                    description: 'Filter attachments by their filename.',
                },
                limit: {
                    type: 'number',
                    description: 'The maximum number of attachments to return. Default is 50, maximum is 100.',
                    default: 50,
                    minimum: 1,
                    maximum: 100,
                },
                start: {
                    type: 'number',
                    description: 'The starting index for pagination. Default is 0.',
                    default: 0,
                },
            },
            required: ['pageId'],
        },
    },
    {
        name: 'download_confluence_attachment',
        description: 'Downloads a specific Confluence attachment and returns its content as a base64-encoded string. This is useful for reading the content of files attached to a page.',
        inputSchema: {
            type: 'object',
            properties: {
                attachmentId: {
                    type: 'string',
                    description: 'The unique identifier of the attachment to download.',
                },
                version: {
                    type: 'number',
                    description: 'The version number of the attachment to download. If not specified, the latest version is downloaded.',
                },
            },
            required: ['attachmentId'],
        },
    },
    {
        name: 'upload_confluence_attachment',
        description: 'Upload a file attachment to a Confluence page. The file should be provided as a base64-encoded string.',
        inputSchema: {
            type: 'object',
            properties: {
                pageId: {
                    type: 'string',
                    description: 'The ID of the page to attach the file to.',
                },
                file: {
                    type: 'string',
                    description: 'The file content as a base64-encoded string.',
                },
                filename: {
                    type: 'string',
                    description: 'The name of the file including extension (e.g., "document.pdf").',
                },
                comment: {
                    type: 'string',
                    description: 'Optional comment describing the attachment.',
                },
                minorEdit: {
                    type: 'boolean',
                    description: 'Set to true if this is a minor edit that should not notify watchers. Default is false.',
                    default: false,
                },
            },
            required: ['pageId', 'file', 'filename'],
        },
    },
    {
        name: 'get_page_with_attachments',
        description: 'Performs a comprehensive download of a Confluence page, including its full content, metadata, and optionally, all of its attachments. Attachments are base64-encoded. **Use this when you need the page content, metadata, and all associated attachments.**',
        inputSchema: {
            type: 'object',
            properties: {
                pageId: {
                    type: 'string',
                    description: 'The ID of the Confluence page to download.',
                },
                includeAttachments: {
                    type: 'boolean',
                    description: 'If true, all attachments on the page will be downloaded and included in the response. Default is true.',
                    default: true,
                },
                attachmentTypes: {
                    type: 'array',
                    items: {
                        type: 'string',
                    },
                    description: 'An array of MIME types to filter attachments by (e.g., ["image/png", "application/pdf"]). If not specified, all attachment types are included.',
                },
                maxAttachmentSize: {
                    type: 'number',
                    description: 'The maximum size in bytes for an individual attachment to be downloaded. Default is 50MB.',
                    default: 52428800,
                },
            },
            required: ['pageId'],
        },
    },
    {
        name: 'create_confluence_page',
        description: 'Creates a new page or blog post in a Confluence space. Content can be provided in Markdown or Confluence storage format (XHTML).',
        inputSchema: {
            type: 'object',
            properties: {
                spaceKey: {
                    type: 'string',
                    description: 'The key of the space where the content will be created (e.g., "DEV").',
                },
                title: {
                    type: 'string',
                    description: 'The title for the new page or blog post.',
                },
                content: {
                    type: 'string',
                    description: 'The main content of the page or blog post. Can be in Markdown or Confluence storage format (XHTML).',
                },
                parentId: {
                    type: 'string',
                    description: 'The ID of a parent page, which will make the new page a child of that page. Optional.',
                },
                type: {
                    type: 'string',
                    description: 'The type of content to create. Can be `page` or `blogpost`. Default is `page`.',
                    enum: ['page', 'blogpost'],
                    default: 'page',
                },
            },
            required: ['spaceKey', 'title', 'content'],
        },
    },
    {
        name: 'update_confluence_page',
        description: 'Updates an existing Confluence page. You must provide the page ID and its current version number to prevent conflicts. You can update the title, content, or both.',
        inputSchema: {
            type: 'object',
            properties: {
                pageId: {
                    type: 'string',
                    description: 'The ID of the page to be updated.',
                },
                title: {
                    type: 'string',
                    description: 'The new title for the page. If not provided, the title remains unchanged.',
                },
                content: {
                    type: 'string',
                    description: 'The new content for the page, in Markdown or storage format. If not provided, the content remains unchanged.',
                },
                version: {
                    type: 'number',
                    description: "The current version number of the page. This is required to ensure you are not overwriting someone else's changes.",
                },
                minorEdit: {
                    type: 'boolean',
                    description: 'Set to true if this is a minor edit that should not notify watchers. Default is false.',
                    default: false,
                },
                versionComment: {
                    type: 'string',
                    description: 'A brief comment describing the changes made in this version.',
                },
            },
            required: ['pageId', 'version'],
        },
    },
    {
        name: 'list_confluence_page_children',
        description: 'List child pages under a given Confluence page. Returns a hierarchical list of direct child pages.',
        inputSchema: {
            type: 'object',
            properties: {
                pageId: {
                    type: 'string',
                    description: 'The ID of the parent page.',
                },
                limit: {
                    type: 'number',
                    description: 'The maximum number of child pages to return. Default is 25, maximum is 100.',
                    default: 25,
                    minimum: 1,
                    maximum: 100,
                },
                start: {
                    type: 'number',
                    description: 'The starting index for pagination. Default is 0.',
                    default: 0,
                },
                expand: {
                    type: 'string',
                    description: 'Properties to expand in the response.',
                    default: 'space',
                },
            },
            required: ['pageId'],
        },
    },
    {
        name: 'list_confluence_page_ancestors',
        description: 'Retrieve the parent hierarchy of a Confluence page. Returns the full ancestry path from root to the immediate parent.',
        inputSchema: {
            type: 'object',
            properties: {
                pageId: {
                    type: 'string',
                    description: 'The ID of the page to get ancestors for.',
                },
            },
            required: ['pageId'],
        },
    },
    {
        name: 'add_confluence_comment',
        description: 'Adds a comment to a Confluence page. Can also be used to reply to an existing comment.',
        inputSchema: {
            type: 'object',
            properties: {
                pageId: {
                    type: 'string',
                    description: 'The ID of the page to which the comment should be added.',
                },
                content: {
                    type: 'string',
                    description: 'The text of the comment. Can be plain text or Confluence storage format (XHTML).',
                },
                parentCommentId: {
                    type: 'string',
                    description: 'The ID of an existing comment to which this comment should be a reply. Optional.',
                },
            },
            required: ['pageId', 'content'],
        },
    },
    {
        name: 'find_confluence_users',
        description: 'Searches for Confluence users based on various criteria. This is useful for finding user details like account IDs when you have partial information or need to perform a broader search. **Use this tool when you need to find users based on a query.**',
        inputSchema: {
            type: 'object',
            properties: {
                cql: {
                    type: 'string',
                    description: 'A CQL query to search for users (e.g., `user.fullname ~ "John Doe"`).',
                },
                username: {
                    type: 'string',
                    description: 'Search for a user by their username.',
                },
                userKey: {
                    type: 'string',
                    description: 'Search for a user by their user key.',
                },
                accountId: {
                    type: 'string',
                    description: 'Search for a user by their Atlassian account ID.',
                },
                expand: {
                    type: 'string',
                    description: 'Properties to expand in the response.',
                },
                limit: {
                    type: 'number',
                    description: 'The maximum number of users to return. Default is 25, maximum is 100.',
                    default: 25,
                    minimum: 1,
                    maximum: 100,
                },
                start: {
                    type: 'number',
                    description: 'The starting index for pagination. Default is 0.',
                    default: 0,
                },
            },
        },
    },
    {
        name: 'list_confluence_page_labels',
        description: 'Retrieves all labels for a specific Confluence page.',
        inputSchema: {
            type: 'object',
            properties: {
                pageId: {
                    type: 'string',
                    description: 'The ID of the page from which to get labels.',
                },
                prefix: {
                    type: 'string',
                    description: 'Filter labels by a specific prefix (e.g., "global", "my").',
                },
                limit: {
                    type: 'number',
                    description: 'The maximum number of labels to return. Default is 25, maximum is 200.',
                    default: 25,
                    minimum: 1,
                    maximum: 200,
                },
                start: {
                    type: 'number',
                    description: 'The starting index for pagination. Default is 0.',
                    default: 0,
                },
            },
            required: ['pageId'],
        },
    },
    {
        name: 'add_confluence_page_label',
        description: 'Adds one or more labels to a Confluence page. Labels are useful for organizing and categorizing content.',
        inputSchema: {
            type: 'object',
            properties: {
                pageId: {
                    type: 'string',
                    description: 'The ID of the page to which the labels will be added.',
                },
                labels: {
                    type: 'array',
                    items: {
                        type: 'object',
                        properties: {
                            prefix: {
                                type: 'string',
                                description: 'The prefix for the label (e.g., "global", "my", "team"). "global" is the default if not provided.',
                            },
                            name: {
                                type: 'string',
                                description: 'The name of the label (e.g., "technical", "meeting-notes").',
                            },
                        },
                        required: ['name'],
                    },
                    description: 'An array of label objects to be added to the page.',
                },
            },
            required: ['pageId', 'labels'],
        },
    },
    {
        name: 'export_confluence_page',
        description: 'Exports a Confluence page to either HTML or Markdown format. All images in the page content are embedded directly into the exported file as base64 data, making it self-contained. **Use this when you want to create a portable, self-contained file of a page.**',
        inputSchema: {
            type: 'object',
            properties: {
                pageId: {
                    type: 'string',
                    description: 'The ID of the Confluence page to be exported.',
                },
                format: {
                    type: 'string',
                    description: 'The desired export format. Can be `html` or `markdown`. Both formats will have images embedded.',
                    enum: ['html', 'markdown'],
                },
            },
            required: ['pageId', 'format'],
        },
    },
    {
        name: 'get_my_recent_confluence_pages',
        description: 'List pages recently created or updated by the current user. Returns pages where you are the creator or last modifier.',
        inputSchema: {
            type: 'object',
            properties: {
                limit: {
                    type: 'number',
                    description: 'The maximum number of pages to return. Default is 25, maximum is 100.',
                    default: 25,
                    minimum: 1,
                    maximum: 100,
                },
                start: {
                    type: 'number',
                    description: 'The starting index for pagination. Default is 0.',
                    default: 0,
                },
                spaceKey: {
                    type: 'string',
                    description: 'Optional space key to filter results to a specific space.',
                },
            },
        },
    },
    {
        name: 'get_confluence_pages_mentioning_me',
        description: 'Search for pages that mention the current user. Returns pages where you have been @mentioned.',
        inputSchema: {
            type: 'object',
            properties: {
                limit: {
                    type: 'number',
                    description: 'The maximum number of pages to return. Default is 25, maximum is 100.',
                    default: 25,
                    minimum: 1,
                    maximum: 100,
                },
                start: {
                    type: 'number',
                    description: 'The starting index for pagination. Default is 0.',
                    default: 0,
                },
                spaceKey: {
                    type: 'string',
                    description: 'Optional space key to filter results to a specific space.',
                },
            },
        },
    },
];
//# sourceMappingURL=tools.js.map