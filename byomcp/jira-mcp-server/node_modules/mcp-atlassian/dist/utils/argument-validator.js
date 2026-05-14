import { Logger } from './logger.js';
export function createValidator(schema) {
    return (args) => {
        if (!args || typeof args !== 'object') {
            return {
                isValid: false,
                errors: ['Arguments must be an object'],
            };
        }
        const errors = [];
        const validatedArgs = {};
        for (const [key, validator] of Object.entries(schema)) {
            const value = args[key];
            const result = validator(value);
            if (!result.valid) {
                if (result.error) {
                    errors.push(`${key}: ${result.error}`);
                }
            }
            else {
                validatedArgs[key] = result.value !== undefined ? result.value : value;
            }
        }
        if (errors.length > 0) {
            Logger.debug('Validation failed', { errors, args: sanitizeForLog(args) });
            return {
                isValid: false,
                errors,
            };
        }
        return {
            isValid: true,
            validatedArgs: validatedArgs,
        };
    };
}
// Common field validators
export const validators = {
    required: (fieldName) => (value) => ({
        valid: value !== undefined && value !== null && value !== '',
        error: value === undefined || value === null || value === ''
            ? `${fieldName} is required`
            : undefined,
    }),
    optional: () => (value) => ({ valid: true }),
    string: (fieldName, minLength = 0, maxLength = Infinity) => (value) => {
        if (value === undefined || value === null)
            return { valid: true };
        if (typeof value !== 'string') {
            return { valid: false, error: `${fieldName} must be a string` };
        }
        if (value.length < minLength) {
            return { valid: false, error: `${fieldName} must be at least ${minLength} characters` };
        }
        if (value.length > maxLength) {
            return { valid: false, error: `${fieldName} must be at most ${maxLength} characters` };
        }
        return { valid: true, value: value.trim() };
    },
    number: (fieldName, min = -Infinity, max = Infinity) => (value) => {
        if (value === undefined || value === null)
            return { valid: true };
        const num = typeof value === 'string' ? parseFloat(value) : value;
        if (typeof num !== 'number' || isNaN(num)) {
            return { valid: false, error: `${fieldName} must be a number` };
        }
        if (num < min || num > max) {
            return { valid: false, error: `${fieldName} must be between ${min} and ${max}` };
        }
        return { valid: true, value: num };
    },
    boolean: (fieldName) => (value) => {
        if (value === undefined || value === null)
            return { valid: true };
        if (typeof value === 'boolean')
            return { valid: true };
        if (typeof value === 'string') {
            const lower = value.toLowerCase();
            if (lower === 'true')
                return { valid: true, value: true };
            if (lower === 'false')
                return { valid: true, value: false };
        }
        return { valid: false, error: `${fieldName} must be a boolean` };
    },
    enum: (fieldName, allowedValues) => (value) => {
        if (value === undefined || value === null)
            return { valid: true };
        if (typeof value !== 'string') {
            return { valid: false, error: `${fieldName} must be a string` };
        }
        if (!allowedValues.includes(value)) {
            return {
                valid: false,
                error: `${fieldName} must be one of: ${allowedValues.join(', ')}`,
            };
        }
        return { valid: true };
    },
    array: (fieldName, itemValidator) => (value) => {
        if (value === undefined || value === null)
            return { valid: true };
        if (!Array.isArray(value)) {
            return { valid: false, error: `${fieldName} must be an array` };
        }
        if (itemValidator) {
            for (let i = 0; i < value.length; i++) {
                const itemResult = itemValidator(value[i]);
                if (!itemResult.valid) {
                    return {
                        valid: false,
                        error: `${fieldName}[${i}]: ${itemResult.error}`,
                    };
                }
            }
        }
        return { valid: true };
    },
    object: (fieldName) => (value) => {
        if (value === undefined || value === null)
            return { valid: true };
        if (typeof value !== 'object' || Array.isArray(value)) {
            return { valid: false, error: `${fieldName} must be an object` };
        }
        return { valid: true };
    },
    oneOfRequired: (fieldName, alternatives) => (value, args) => {
        const hasValue = value !== undefined && value !== null && value !== '';
        const hasAlternatives = alternatives.some((alt) => args[alt] !== undefined && args[alt] !== null && args[alt] !== '');
        if (!hasValue && !hasAlternatives) {
            return {
                valid: false,
                error: `Either ${fieldName} or one of [${alternatives.join(', ')}] must be provided`,
            };
        }
        return { valid: true };
    },
};
function sanitizeForLog(args) {
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
//# sourceMappingURL=argument-validator.js.map