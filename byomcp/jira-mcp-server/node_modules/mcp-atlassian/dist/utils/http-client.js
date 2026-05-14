import axios from 'axios';
import { HttpsProxyAgent } from 'https-proxy-agent';
export function createAtlassianClient() {
    const baseURL = process.env.ATLASSIAN_BASE_URL;
    const email = process.env.ATLASSIAN_EMAIL;
    const apiToken = process.env.ATLASSIAN_API_TOKEN;
    if (!baseURL || !email || !apiToken) {
        throw new Error('Missing required environment variables');
    }
    // Create axios config
    const axiosConfig = {
        baseURL,
        auth: {
            username: email,
            password: apiToken,
        },
        headers: {
            Accept: 'application/json',
            'Content-Type': 'application/json',
        },
        timeout: 30000,
        maxRedirects: 5,
        validateStatus: (status) => status < 500, // Don't throw for 4xx errors
    };
    // Add proxy configuration using https-proxy-agent
    const httpsProxy = process.env.HTTPS_PROXY || process.env.https_proxy;
    const httpProxy = process.env.HTTP_PROXY || process.env.http_proxy;
    if (httpsProxy || httpProxy) {
        const proxyUrl = httpsProxy || httpProxy;
        axiosConfig.httpsAgent = new HttpsProxyAgent(proxyUrl);
        // Also set httpAgent for completeness
        axiosConfig.httpAgent = new HttpsProxyAgent(proxyUrl);
        // Disable axios's built-in proxy handling
        axiosConfig.proxy = false;
    }
    const client = axios.create(axiosConfig);
    // Add request interceptor to ensure proper headers for POST/PUT requests
    client.interceptors.request.use((config) => {
        if (config.method === 'post' || config.method === 'put') {
            config.headers['Content-Type'] = 'application/json';
        }
        return config;
    });
    return client;
}
export function formatApiError(error) {
    if (axios.isAxiosError(error)) {
        const axiosError = error;
        if (axiosError.response) {
            const status = axiosError.response.status;
            const data = axiosError.response.data;
            switch (status) {
                case 401:
                    return 'Authentication failed. Please check your API token and email.';
                case 403:
                    return 'Access forbidden. Your API token may not have the required permissions.';
                case 404:
                    if (data?.errorMessages && data.errorMessages.length > 0) {
                        return `Not found: ${data.errorMessages.join(', ')}`;
                    }
                    return 'Resource not found. Please check the ID or key provided.';
                case 429:
                    return 'Rate limit exceeded. Please try again later.';
                default:
                    if (data?.message) {
                        return `API Error (${status}): ${data.message}`;
                    }
                    else if (data?.errorMessages && data.errorMessages.length > 0) {
                        return `API Error (${status}): ${data.errorMessages.join(', ')}`;
                    }
                    else if (data?.errors && Object.keys(data.errors).length > 0) {
                        return `API Error (${status}): ${JSON.stringify(data.errors)}`;
                    }
                    else {
                        return `API Error (${status}): ${axiosError.message}`;
                    }
            }
        }
        else if (axiosError.request) {
            // Include more details about the network error
            const details = axiosError.code ? ` (${axiosError.code})` : '';
            return `Network error: Unable to reach Atlassian API${details}. ${axiosError.message}`;
        }
    }
    return error instanceof Error ? error.message : 'An unknown error occurred';
}
//# sourceMappingURL=http-client.js.map