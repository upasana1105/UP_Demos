import { Logger } from './logger.js';
export class ToolRegistry {
    tools = new Map();
    register(definition) {
        if (this.tools.has(definition.name)) {
            Logger.warn(`Tool ${definition.name} is being overridden`);
        }
        this.tools.set(definition.name, definition);
        Logger.debug(`Registered tool: ${definition.name}`, { tool: definition.name });
    }
    async execute(toolName, args, requestId) {
        const startTime = Date.now();
        Logger.logToolCall(toolName, undefined, { requestId, args: this.sanitizeArgs(args) });
        const tool = this.tools.get(toolName);
        if (!tool) {
            const error = `Unknown tool: ${toolName}`;
            Logger.logError('tool-execution', new Error(error), { tool: toolName, requestId });
            return {
                content: [{ type: 'text', text: error }],
                isError: true,
            };
        }
        try {
            let validatedArgs = args;
            // Run validation if provided
            if (tool.validator) {
                const validation = tool.validator(args);
                if (!validation.isValid) {
                    const error = `Validation failed for tool ${toolName}: ${validation.errors?.join(', ')}`;
                    Logger.logError('tool-validation', new Error(error), {
                        tool: toolName,
                        requestId,
                        validationErrors: validation.errors,
                    });
                    return {
                        content: [{ type: 'text', text: error }],
                        isError: true,
                    };
                }
                validatedArgs = validation.validatedArgs || args;
            }
            const result = await tool.handler(validatedArgs);
            const duration = Date.now() - startTime;
            Logger.logResponse(`tool-${toolName}`, duration, { tool: toolName, requestId });
            Logger.logPerformance(`tool-${toolName}`, duration, { tool: toolName, requestId });
            return result;
        }
        catch (error) {
            const duration = Date.now() - startTime;
            Logger.logError(`tool-${toolName}`, error, {
                tool: toolName,
                requestId,
                duration,
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
    }
    getRegisteredTools() {
        return Array.from(this.tools.keys());
    }
    hasTool(toolName) {
        return this.tools.has(toolName);
    }
    sanitizeArgs(args) {
        if (!args || typeof args !== 'object')
            return {};
        const sanitized = { ...args };
        const sensitiveKeys = ['password', 'token', 'apiKey', 'secret', 'authorization'];
        for (const key of sensitiveKeys) {
            if (key in sanitized) {
                sanitized[key] = '[REDACTED]';
            }
        }
        return sanitized;
    }
}
//# sourceMappingURL=tool-registry.js.map