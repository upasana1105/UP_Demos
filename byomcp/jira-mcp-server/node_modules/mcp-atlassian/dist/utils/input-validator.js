/**
 * Input validation utilities for MCP Atlassian Server
 * Provides comprehensive validation for all user inputs to prevent security issues
 */
/**
 * Validates pagination parameters
 */
export function validatePagination(startAt, maxResults) {
    const errors = [];
    const result = { startAt: 0, maxResults: 50 };
    if (startAt !== undefined) {
        if (!Number.isInteger(startAt) || startAt < 0) {
            errors.push('startAt must be a non-negative integer');
        }
        else {
            result.startAt = startAt;
        }
    }
    if (maxResults !== undefined) {
        if (!Number.isInteger(maxResults) || maxResults < 1 || maxResults > 100) {
            errors.push('maxResults must be an integer between 1 and 100');
        }
        else {
            result.maxResults = maxResults;
        }
    }
    return {
        isValid: errors.length === 0,
        errors,
        sanitizedValue: result,
    };
}
/**
 * Validates date strings in YYYY-MM-DD format
 */
export function validateDateString(date, fieldName) {
    const errors = [];
    if (typeof date !== 'string') {
        errors.push(`${fieldName} must be a string`);
        return { isValid: false, errors };
    }
    // Check format
    const datePattern = /^\d{4}-\d{2}-\d{2}$/;
    if (!datePattern.test(date)) {
        errors.push(`${fieldName} must be in YYYY-MM-DD format`);
        return { isValid: false, errors };
    }
    // Validate actual date
    const parsedDate = new Date(date + 'T00:00:00.000Z');
    if (isNaN(parsedDate.getTime()) || parsedDate.toISOString().slice(0, 10) !== date) {
        errors.push(`${fieldName} is not a valid date: ${date}`);
        return { isValid: false, errors };
    }
    // Check reasonable date range (1900 to 100 years from now)
    const minDate = new Date('1900-01-01');
    const maxDate = new Date();
    maxDate.setFullYear(maxDate.getFullYear() + 100);
    if (parsedDate < minDate || parsedDate > maxDate) {
        errors.push(`${fieldName} must be between 1900-01-01 and ${maxDate.toISOString().slice(0, 10)}`);
        return { isValid: false, errors };
    }
    return {
        isValid: true,
        errors: [],
        sanitizedValue: date,
    };
}
/**
 * Validates date range (start date before end date)
 */
export function validateDateRange(startDate, endDate) {
    const errors = [];
    let validStartDate = startDate;
    let validEndDate = endDate;
    if (startDate) {
        const startValidation = validateDateString(startDate, 'startDate');
        if (!startValidation.isValid) {
            errors.push(...startValidation.errors);
            validStartDate = undefined;
        }
    }
    if (endDate) {
        const endValidation = validateDateString(endDate, 'endDate');
        if (!endValidation.isValid) {
            errors.push(...endValidation.errors);
            validEndDate = undefined;
        }
    }
    // Check date order if both are valid
    if (validStartDate && validEndDate) {
        const start = new Date(validStartDate);
        const end = new Date(validEndDate);
        if (start > end) {
            errors.push('startDate must be before or equal to endDate');
        }
        // Check reasonable range (not more than 5 years)
        const fiveYears = 5 * 365 * 24 * 60 * 60 * 1000;
        if (end.getTime() - start.getTime() > fiveYears) {
            errors.push('Date range cannot exceed 5 years for performance reasons');
        }
    }
    return {
        isValid: errors.length === 0,
        errors,
        sanitizedValue: {
            startDate: validStartDate,
            endDate: validEndDate,
        },
    };
}
/**
 * Validates array of strings with optional pattern matching
 */
export function validateStringArray(value, fieldName, options = {}) {
    const errors = [];
    const opts = {
        required: false,
        maxLength: 100,
        maxItems: 50,
        allowEmpty: false,
        ...options,
    };
    // Handle undefined/null
    if (value === undefined || value === null) {
        if (opts.required) {
            errors.push(`${fieldName} is required`);
        }
        return {
            isValid: errors.length === 0,
            errors,
            sanitizedValue: undefined,
        };
    }
    // Must be array
    if (!Array.isArray(value)) {
        errors.push(`${fieldName} must be an array`);
        return { isValid: false, errors };
    }
    // Check array length
    if (value.length > opts.maxItems) {
        errors.push(`${fieldName} cannot have more than ${opts.maxItems} items`);
    }
    if (value.length === 0 && !opts.allowEmpty) {
        errors.push(`${fieldName} cannot be empty`);
    }
    // Validate each item
    const sanitizedItems = [];
    for (let i = 0; i < value.length; i++) {
        const item = value[i];
        if (typeof item !== 'string') {
            errors.push(`${fieldName}[${i}] must be a string`);
            continue;
        }
        if (item.length > opts.maxLength) {
            errors.push(`${fieldName}[${i}] cannot exceed ${opts.maxLength} characters`);
            continue;
        }
        if (opts.pattern && !opts.pattern.test(item)) {
            errors.push(`${fieldName}[${i}] has invalid format: ${item}`);
            continue;
        }
        sanitizedItems.push(item);
    }
    return {
        isValid: errors.length === 0,
        errors,
        sanitizedValue: sanitizedItems,
    };
}
/**
 * Validates string with length and pattern constraints
 */
export function validateString(value, fieldName, options = {}) {
    const errors = [];
    const opts = {
        required: false,
        minLength: 0,
        maxLength: 1000,
        allowEmpty: false,
        ...options,
    };
    // Handle undefined/null
    if (value === undefined || value === null) {
        if (opts.required) {
            errors.push(`${fieldName} is required`);
        }
        return {
            isValid: errors.length === 0,
            errors,
            sanitizedValue: undefined,
        };
    }
    // Must be string
    if (typeof value !== 'string') {
        errors.push(`${fieldName} must be a string`);
        return { isValid: false, errors };
    }
    // Check length constraints
    if (value.length < opts.minLength) {
        errors.push(`${fieldName} must be at least ${opts.minLength} characters`);
    }
    if (value.length > opts.maxLength) {
        errors.push(`${fieldName} cannot exceed ${opts.maxLength} characters`);
    }
    if (value.length === 0 && !opts.allowEmpty) {
        errors.push(`${fieldName} cannot be empty`);
    }
    // Check pattern
    if (opts.pattern && value.length > 0 && !opts.pattern.test(value)) {
        errors.push(`${fieldName} has invalid format`);
    }
    return {
        isValid: errors.length === 0,
        errors,
        sanitizedValue: value,
    };
}
/**
 * Validates numeric values
 */
export function validateNumber(value, fieldName, options = {}) {
    const errors = [];
    const opts = {
        required: false,
        integer: false,
        min: Number.MIN_SAFE_INTEGER,
        max: Number.MAX_SAFE_INTEGER,
        ...options,
    };
    // Handle undefined/null
    if (value === undefined || value === null) {
        if (opts.required) {
            errors.push(`${fieldName} is required`);
        }
        return {
            isValid: errors.length === 0,
            errors,
            sanitizedValue: undefined,
        };
    }
    // Must be number
    if (typeof value !== 'number' || isNaN(value)) {
        errors.push(`${fieldName} must be a valid number`);
        return { isValid: false, errors };
    }
    // Check integer constraint
    if (opts.integer && !Number.isInteger(value)) {
        errors.push(`${fieldName} must be an integer`);
    }
    // Check range
    if (value < opts.min) {
        errors.push(`${fieldName} must be at least ${opts.min}`);
    }
    if (value > opts.max) {
        errors.push(`${fieldName} cannot exceed ${opts.max}`);
    }
    return {
        isValid: errors.length === 0,
        errors,
        sanitizedValue: value,
    };
}
/**
 * Validates enum values
 */
export function validateEnum(value, fieldName, allowedValues, required = false) {
    const errors = [];
    // Handle undefined/null
    if (value === undefined || value === null) {
        if (required) {
            errors.push(`${fieldName} is required`);
        }
        return {
            isValid: errors.length === 0,
            errors,
            sanitizedValue: undefined,
        };
    }
    // Must be string
    if (typeof value !== 'string') {
        errors.push(`${fieldName} must be a string`);
        return { isValid: false, errors };
    }
    // Must be one of allowed values
    if (!allowedValues.includes(value)) {
        errors.push(`${fieldName} must be one of: ${allowedValues.join(', ')}`);
        return { isValid: false, errors };
    }
    return {
        isValid: true,
        errors: [],
        sanitizedValue: value,
    };
}
/**
 * Comprehensive validation for user identification parameters
 */
export function validateUserIdentification(args) {
    const errors = [];
    const result = {};
    // At least one identifier must be provided
    if (!args.username && !args.accountId && !args.email) {
        errors.push('At least one user identifier (username, accountId, or email) is required');
        return { isValid: false, errors };
    }
    // Validate accountId if provided
    if (args.accountId) {
        try {
            const validation = validateString(args.accountId, 'accountId', {
                required: false,
                minLength: 10,
                maxLength: 128,
                pattern: /^[a-zA-Z0-9:_-]+$/,
            });
            if (!validation.isValid) {
                errors.push(...validation.errors);
            }
            else {
                result.accountId = validation.sanitizedValue;
            }
        }
        catch (e) {
            errors.push(`Invalid accountId: ${e instanceof Error ? e.message : 'Unknown error'}`);
        }
    }
    // Validate username if provided (deprecated)
    if (args.username) {
        const validation = validateString(args.username, 'username', {
            required: false,
            minLength: 1,
            maxLength: 255,
            pattern: /^[a-zA-Z0-9._@-]+$/,
        });
        if (!validation.isValid) {
            errors.push(...validation.errors);
        }
        else {
            result.username = validation.sanitizedValue;
        }
    }
    // Reject email for privacy reasons
    if (args.email) {
        errors.push('Email-based user lookup is disabled for privacy reasons. Please use accountId instead.');
    }
    return {
        isValid: errors.length === 0,
        errors,
        sanitizedValue: result,
    };
}
//# sourceMappingURL=input-validator.js.map