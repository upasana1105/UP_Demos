import winston from 'winston';
// Define log levels
export var LogLevel;
(function (LogLevel) {
    LogLevel["ERROR"] = "error";
    LogLevel["WARN"] = "warn";
    LogLevel["INFO"] = "info";
    LogLevel["DEBUG"] = "debug";
})(LogLevel || (LogLevel = {}));
// Create winston logger instance
const logger = winston.createLogger({
    level: process.env.LOG_LEVEL || 'info',
    format: winston.format.combine(winston.format.timestamp({
        format: 'YYYY-MM-DD HH:mm:ss',
    }), winston.format.errors({ stack: true }), winston.format.json(), winston.format.prettyPrint()),
    defaultMeta: {
        service: 'mcp-atlassian',
        version: process.env.npm_package_version || '2.0.0',
        environment: process.env.NODE_ENV || 'development',
    },
    transports: [
        // Console transport for development
        new winston.transports.Console({
            format: winston.format.combine(winston.format.colorize({ all: true }), winston.format.simple()),
        }),
    ],
});
// Add file transport in production
if (process.env.NODE_ENV === 'production') {
    logger.add(new winston.transports.File({
        filename: 'logs/error.log',
        level: 'error',
        format: winston.format.combine(winston.format.timestamp(), winston.format.json()),
    }));
    logger.add(new winston.transports.File({
        filename: 'logs/combined.log',
        format: winston.format.combine(winston.format.timestamp(), winston.format.json()),
    }));
}
// Utility functions for structured logging
export class Logger {
    static sanitizeContext(context) {
        const sanitized = { ...context };
        // Remove sensitive data
        if (sanitized.metadata) {
            // eslint-disable-next-line @typescript-eslint/no-unused-vars
            const { password, token, apiKey, secret, ...safeMeta } = sanitized.metadata;
            sanitized.metadata = safeMeta;
        }
        return sanitized;
    }
    static info(message, context) {
        logger.info(message, this.sanitizeContext(context || {}));
    }
    static warn(message, context) {
        logger.warn(message, this.sanitizeContext(context || {}));
    }
    static error(message, context) {
        logger.error(message, this.sanitizeContext(context || {}));
    }
    static debug(message, context) {
        logger.debug(message, this.sanitizeContext(context || {}));
    }
    static logRequest(operation, context = {}) {
        this.info(`Starting ${operation}`, {
            ...context,
            operation,
            timestamp: new Date().toISOString(),
        });
    }
    static logResponse(operation, duration, context = {}) {
        this.info(`Completed ${operation}`, {
            ...context,
            operation,
            duration,
            timestamp: new Date().toISOString(),
        });
    }
    static logError(operation, error, context = {}) {
        this.error(`Failed ${operation}`, {
            ...context,
            operation,
            error,
            errorMessage: error.message,
            errorStack: error.stack,
            timestamp: new Date().toISOString(),
        });
    }
    static logToolCall(toolName, userId, metadata) {
        this.info(`Tool called: ${toolName}`, {
            tool: toolName,
            userId,
            metadata,
            timestamp: new Date().toISOString(),
        });
    }
    static logPerformance(operation, duration, context = {}) {
        const level = duration > 5000 ? LogLevel.WARN : LogLevel.INFO;
        const message = `Performance: ${operation} took ${duration}ms`;
        if (level === LogLevel.WARN) {
            this.warn(message, { ...context, operation, duration, performanceIssue: true });
        }
        else {
            this.info(message, { ...context, operation, duration });
        }
    }
    static logSecurity(event, context = {}) {
        this.warn(`Security event: ${event}`, {
            ...context,
            securityEvent: true,
            timestamp: new Date().toISOString(),
        });
    }
}
// Export the winston logger instance for direct use if needed
export default logger;
//# sourceMappingURL=logger.js.map