/**
 * JQL (Jira Query Language) sanitization utilities
 * Prevents JQL injection attacks by properly escaping user inputs
 */
/**
 * Escapes special JQL characters in string values
 * @param value - The string value to escape
 * @returns Escaped string safe for JQL queries
 */
export function escapeJqlString(value) {
    if (typeof value !== 'string') {
        throw new Error('JQL string escape requires a string input');
    }
    // Escape special JQL characters
    return value
        .replace(/\\/g, '\\\\') // Escape backslashes first
        .replace(/"/g, '\\"') // Escape double quotes
        .replace(/'/g, "\\'") // Escape single quotes
        .replace(/\n/g, '\\n') // Escape newlines
        .replace(/\r/g, '\\r') // Escape carriage returns
        .replace(/\t/g, '\\t'); // Escape tabs
}
/**
 * Validates and escapes JQL field names
 * @param fieldName - The field name to validate
 * @returns Validated field name
 */
export function validateJqlField(fieldName) {
    if (typeof fieldName !== 'string') {
        throw new Error('JQL field name must be a string');
    }
    // Allow only alphanumeric, underscore, and dot for field names
    const validFieldPattern = /^[a-zA-Z][a-zA-Z0-9_.]*$/;
    if (!validFieldPattern.test(fieldName)) {
        throw new Error(`Invalid JQL field name: ${fieldName}`);
    }
    return fieldName;
}
/**
 * Safely builds JQL conditions with proper escaping
 */
export class JqlBuilder {
    conditions = [];
    /**
     * Adds an equals condition
     * @param field - Field name
     * @param value - Field value (will be escaped)
     */
    equals(field, value) {
        const validField = validateJqlField(field);
        const escapedValue = escapeJqlString(value);
        this.conditions.push(`${validField} = "${escapedValue}"`);
        return this;
    }
    /**
     * Adds an IN condition
     * @param field - Field name
     * @param values - Array of values (will be escaped)
     */
    in(field, values) {
        const validField = validateJqlField(field);
        const escapedValues = values.map((v) => `"${escapeJqlString(v)}"`);
        this.conditions.push(`${validField} IN (${escapedValues.join(', ')})`);
        return this;
    }
    /**
     * Adds an OR condition combining multiple field-value pairs for the same value
     * @param fields - Array of field names
     * @param value - The value to match against all fields
     */
    orEquals(fields, value) {
        const validFields = fields.map((f) => validateJqlField(f));
        const escapedValue = escapeJqlString(value);
        const orConditions = validFields.map((f) => `${f} = "${escapedValue}"`);
        this.conditions.push(`(${orConditions.join(' OR ')})`);
        return this;
    }
    /**
     * Adds a date range condition
     * @param field - Field name
     * @param startDate - Start date in YYYY-MM-DD format
     * @param endDate - End date in YYYY-MM-DD format (optional)
     */
    dateRange(field, startDate, endDate) {
        const validField = validateJqlField(field);
        if (startDate) {
            this.validateDateFormat(startDate);
            this.conditions.push(`${validField} >= "${startDate}"`);
        }
        if (endDate) {
            this.validateDateFormat(endDate);
            this.conditions.push(`${validField} <= "${endDate}"`);
        }
        return this;
    }
    /**
     * Adds a custom condition (use with caution - no automatic escaping)
     * @param condition - Raw JQL condition
     */
    raw(condition) {
        this.conditions.push(condition);
        return this;
    }
    /**
     * Validates date format (YYYY-MM-DD)
     */
    validateDateFormat(date) {
        const datePattern = /^\d{4}-\d{2}-\d{2}$/;
        if (!datePattern.test(date)) {
            throw new Error(`Invalid date format: ${date}. Expected YYYY-MM-DD`);
        }
        // Validate actual date
        const parsedDate = new Date(date);
        if (isNaN(parsedDate.getTime()) || parsedDate.toISOString().slice(0, 10) !== date) {
            throw new Error(`Invalid date: ${date}`);
        }
    }
    /**
     * Builds the final JQL query string
     */
    build() {
        return this.conditions.join(' AND ');
    }
    /**
     * Clears all conditions
     */
    clear() {
        this.conditions = [];
        return this;
    }
}
/**
 * Validates project keys format
 * @param projectKeys - Array of project keys to validate
 */
export function validateProjectKeys(projectKeys) {
    if (!Array.isArray(projectKeys)) {
        throw new Error('Project keys must be an array');
    }
    return projectKeys.map((key) => {
        if (typeof key !== 'string') {
            throw new Error('Project key must be a string');
        }
        // Project keys should be uppercase letters and numbers, typically 2-10 chars
        const projectKeyPattern = /^[A-Z0-9]{1,10}$/;
        if (!projectKeyPattern.test(key)) {
            throw new Error(`Invalid project key format: ${key}. Expected uppercase letters and numbers, 1-10 characters`);
        }
        return key;
    });
}
/**
 * Validates account ID format
 * @param accountId - Atlassian account ID
 */
export function validateAccountId(accountId) {
    if (typeof accountId !== 'string') {
        throw new Error('Account ID must be a string');
    }
    // Atlassian account IDs are typically UUIDs or similar format
    const accountIdPattern = /^[a-zA-Z0-9:_-]+$/;
    if (!accountIdPattern.test(accountId) || accountId.length < 10) {
        throw new Error(`Invalid account ID format: ${accountId}`);
    }
    return accountId;
}
//# sourceMappingURL=jql-sanitizer.js.map