/**
 * Enhanced error handling with contextual error messages
 * Provides better user experience with specific, actionable error information
 */
/**
 * Creates enhanced error response with context and suggestions
 */
export function createEnhancedError(error, context) {
    const enhancedError = analyzeError(error, context);
    const errorMessage = `
**Error in ${enhancedError.context.component.toUpperCase()}**: ${enhancedError.message}

**Operation**: ${enhancedError.context.operation}

**Details**: ${enhancedError.details}

**Suggestions**:
${enhancedError.suggestions.map((s) => `• ${s}`).join('\n')}

**Type**: ${enhancedError.type}${enhancedError.statusCode ? ` (HTTP ${enhancedError.statusCode})` : ''}
**Retryable**: ${enhancedError.retryable ? 'Yes' : 'No'}
`.trim();
    return {
        content: [{ type: 'text', text: errorMessage }],
        isError: true,
    };
}
/**
 * Analyzes error and creates enhanced error information
 */
function analyzeError(error, context) {
    // Handle Axios errors (API calls)
    if (error && typeof error === 'object' && 'isAxiosError' in error) {
        return analyzeAxiosError(error, context);
    }
    // Handle validation errors
    if (error instanceof Error && error.message.includes('validation')) {
        return {
            type: 'validation',
            message: 'Input validation failed',
            details: error.message,
            suggestions: [
                'Check that all required parameters are provided',
                'Verify parameter formats match expected patterns',
                'Review the tool documentation for parameter requirements',
            ],
            retryable: true,
            context,
        };
    }
    // Handle generic errors
    const errorMessage = error instanceof Error ? error.message : String(error);
    return {
        type: 'unknown',
        message: 'An unexpected error occurred',
        details: errorMessage,
        suggestions: [
            'Check your network connection',
            'Verify your Atlassian credentials are valid',
            'Try the request again in a few moments',
            'Contact support if the issue persists',
        ],
        retryable: true,
        context,
    };
}
/**
 * Analyzes Axios errors and provides specific guidance
 */
function analyzeAxiosError(error, context) {
    const status = error.response?.status;
    const responseData = error.response?.data;
    switch (status) {
        case 400:
            return {
                type: 'validation',
                message: 'Bad request - Invalid parameters',
                details: getApiErrorDetails(responseData) || error.message,
                suggestions: [
                    'Verify all parameters are correctly formatted',
                    'Check that project keys exist and are accessible',
                    'Ensure date formats use YYYY-MM-DD pattern',
                    'Review JQL syntax if using custom queries',
                ],
                retryable: true,
                statusCode: 400,
                context,
            };
        case 401:
            return {
                type: 'authentication',
                message: 'Authentication failed',
                details: 'Your API credentials are invalid or have expired',
                suggestions: [
                    'Check that ATLASSIAN_API_TOKEN is set correctly',
                    'Verify ATLASSIAN_EMAIL matches your Atlassian account',
                    'Generate a new API token from https://id.atlassian.com/manage-profile/security/api-tokens',
                    'Ensure your API token has not expired',
                ],
                retryable: false,
                statusCode: 401,
                context,
            };
        case 403:
            return {
                type: 'permission',
                message: 'Permission denied',
                details: getApiErrorDetails(responseData) || 'You do not have permission to access this resource',
                suggestions: [
                    'Check that your user has the necessary permissions in Jira/Confluence',
                    'Verify the project or space is accessible to your account',
                    'Contact your Atlassian administrator for access',
                    'Ensure you are using the correct site URL (ATLASSIAN_BASE_URL)',
                ],
                retryable: false,
                statusCode: 403,
                context,
            };
        case 404:
            return {
                type: 'notFound',
                message: 'Resource not found',
                details: getApiErrorDetails(responseData) || 'The requested resource could not be found',
                suggestions: getNotFoundSuggestions(context),
                retryable: false,
                statusCode: 404,
                context,
            };
        case 429:
            return {
                type: 'rateLimit',
                message: 'Rate limit exceeded',
                details: 'Too many requests have been made in a short period',
                suggestions: [
                    'Wait a few minutes before retrying',
                    'Reduce the frequency of requests',
                    'Consider implementing request batching',
                    'Use pagination to make smaller requests',
                ],
                retryable: true,
                statusCode: 429,
                context,
            };
        case 500:
        case 502:
        case 503:
            return {
                type: 'server',
                message: 'Server error',
                details: 'Atlassian service is temporarily unavailable',
                suggestions: [
                    'Wait a few minutes and try again',
                    'Check Atlassian Status page for service outages',
                    'Reduce request complexity if possible',
                    'Contact Atlassian support if the issue persists',
                ],
                retryable: true,
                statusCode: status,
                context,
            };
        default:
            return {
                type: 'network',
                message: 'Network or API error',
                details: error.message || 'An unknown network error occurred',
                suggestions: [
                    'Check your internet connection',
                    'Verify ATLASSIAN_BASE_URL is correct',
                    'Try the request again',
                    'Check if the Atlassian service is available',
                ],
                retryable: true,
                statusCode: status,
                context,
            };
    }
}
/**
 * Extracts detailed error information from Atlassian API responses
 */
function getApiErrorDetails(responseData) {
    if (!responseData)
        return null;
    // Jira error format
    if (responseData.errorMessages && Array.isArray(responseData.errorMessages)) {
        return responseData.errorMessages.join('; ');
    }
    // Confluence error format
    if (responseData.message) {
        return responseData.message;
    }
    // Generic error details
    if (typeof responseData === 'string') {
        return responseData;
    }
    return null;
}
/**
 * Provides context-specific suggestions for 404 errors
 */
function getNotFoundSuggestions(context) {
    const baseSuggestions = [
        'Verify the resource identifier is correct',
        'Check that the resource exists and is accessible',
    ];
    if (context.operation.includes('user')) {
        return [
            ...baseSuggestions,
            'Ensure the username or accountId is valid',
            'Check that the user exists in your Atlassian instance',
            'Try using accountId instead of username',
        ];
    }
    if (context.operation.includes('issue')) {
        return [
            ...baseSuggestions,
            'Verify the issue key format (e.g., PROJ-123)',
            'Check that the issue exists and you have access to view it',
            'Ensure the project key is correct',
        ];
    }
    if (context.operation.includes('project')) {
        return [
            ...baseSuggestions,
            'Verify the project key is correct',
            'Check that the project exists and is accessible',
            'Ensure you have permission to view the project',
        ];
    }
    return baseSuggestions;
}
/**
 * Creates a validation error response
 */
export function createValidationError(errors, operation, component = 'jira') {
    const context = {
        operation,
        component,
        suggestions: [
            'Review the input parameters and their formats',
            'Check the tool documentation for requirements',
            'Ensure all required fields are provided',
        ],
    };
    const validationError = new Error(`Validation failed: ${errors.join(', ')}`);
    return createEnhancedError(validationError, context);
}
/**
 * Creates a user not found error with specific guidance
 */
export function createUserNotFoundError(identifier, component = 'jira') {
    const context = {
        operation: 'user lookup',
        component,
        userInput: { identifier },
        suggestions: [
            "Use the user's accountId instead of username or email",
            'Verify the user exists in your Atlassian instance',
            'Check that the user has not been deactivated',
            'Ensure you have permission to view user information',
        ],
    };
    return {
        content: [
            {
                type: 'text',
                text: `
**User Not Found**: Could not locate user "${identifier}"

**Operation**: ${context.operation}

**Recommendations**:
• **Security Best Practice**: Use accountId instead of username/email
• **Verification**: Confirm the user exists and is active
• **Permissions**: Ensure you can view user information
• **Alternative**: Try searching by a different identifier

**Why This Matters**:
For privacy and security, email-based lookups are disabled. Username lookups are deprecated and may not work reliably. AccountId is the recommended approach.
      `.trim(),
            },
        ],
        isError: true,
    };
}
//# sourceMappingURL=error-handler.js.map