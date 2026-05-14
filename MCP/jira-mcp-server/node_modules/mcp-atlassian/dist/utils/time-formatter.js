/**
 * Configurable time formatting system for work hour calculations
 * Supports different work hour standards and display formats
 */
/**
 * Default work hours configuration
 * Can be overridden via environment variables or configuration
 */
const DEFAULT_CONFIG = {
    hoursPerDay: 8, // Standard 8-hour work day
    minutesPerHour: 60, // Standard 60-minute hour
    displayFormat: 'mixed', // Show days, hours, and minutes
    includeSeconds: false, // Don't show seconds by default
};
/**
 * Loads work hours configuration from environment variables
 */
function loadConfigFromEnv() {
    const config = {};
    if (process.env.WORK_HOURS_PER_DAY) {
        const value = parseInt(process.env.WORK_HOURS_PER_DAY);
        if (!isNaN(value) && value > 0 && value <= 24) {
            config.hoursPerDay = value;
        }
    }
    if (process.env.TIME_DISPLAY_FORMAT) {
        const format = process.env.TIME_DISPLAY_FORMAT.toLowerCase();
        if (['short', 'long', 'mixed'].includes(format)) {
            config.displayFormat = format;
        }
    }
    if (process.env.INCLUDE_SECONDS) {
        config.includeSeconds = process.env.INCLUDE_SECONDS.toLowerCase() === 'true';
    }
    return config;
}
/**
 * Global configuration with environment overrides
 */
let globalConfig = {
    ...DEFAULT_CONFIG,
    ...loadConfigFromEnv(),
};
/**
 * Updates the global work hours configuration
 */
export function setWorkHoursConfig(config) {
    globalConfig = { ...globalConfig, ...config };
}
/**
 * Gets the current work hours configuration
 */
export function getWorkHoursConfig() {
    return { ...globalConfig };
}
/**
 * Converts seconds to a time breakdown based on work hours configuration
 */
export function breakdownTime(totalSeconds, config) {
    const activeConfig = { ...globalConfig, ...config };
    if (totalSeconds < 0) {
        totalSeconds = 0;
    }
    const secondsPerMinute = 60;
    const secondsPerHour = activeConfig.minutesPerHour * secondsPerMinute;
    const secondsPerDay = activeConfig.hoursPerDay * secondsPerHour;
    const days = Math.floor(totalSeconds / secondsPerDay);
    const remainingAfterDays = totalSeconds % secondsPerDay;
    const hours = Math.floor(remainingAfterDays / secondsPerHour);
    const remainingAfterHours = remainingAfterDays % secondsPerHour;
    const minutes = Math.floor(remainingAfterHours / secondsPerMinute);
    const seconds = remainingAfterHours % secondsPerMinute;
    return {
        totalSeconds,
        days,
        hours,
        minutes,
        seconds,
    };
}
/**
 * Formats seconds into a human-readable string
 */
export function formatSeconds(totalSeconds, config) {
    const activeConfig = { ...globalConfig, ...config };
    const breakdown = breakdownTime(totalSeconds, activeConfig);
    if (totalSeconds === 0) {
        return activeConfig.displayFormat === 'long' ? '0 minutes' : '0m';
    }
    const parts = [];
    // Add days
    if (breakdown.days > 0) {
        if (activeConfig.displayFormat === 'long') {
            parts.push(`${breakdown.days} day${breakdown.days !== 1 ? 's' : ''}`);
        }
        else {
            parts.push(`${breakdown.days}d`);
        }
    }
    // Add hours
    if (breakdown.hours > 0) {
        if (activeConfig.displayFormat === 'long') {
            parts.push(`${breakdown.hours} hour${breakdown.hours !== 1 ? 's' : ''}`);
        }
        else {
            parts.push(`${breakdown.hours}h`);
        }
    }
    // Add minutes
    if (breakdown.minutes > 0) {
        if (activeConfig.displayFormat === 'long') {
            parts.push(`${breakdown.minutes} minute${breakdown.minutes !== 1 ? 's' : ''}`);
        }
        else {
            parts.push(`${breakdown.minutes}m`);
        }
    }
    // Add seconds if enabled
    if (activeConfig.includeSeconds && breakdown.seconds > 0) {
        if (activeConfig.displayFormat === 'long') {
            parts.push(`${breakdown.seconds} second${breakdown.seconds !== 1 ? 's' : ''}`);
        }
        else {
            parts.push(`${breakdown.seconds}s`);
        }
    }
    // Handle display format
    if (activeConfig.displayFormat === 'short' || parts.length === 0) {
        // Show only the largest unit
        if (breakdown.days > 0)
            return `${breakdown.days}d`;
        if (breakdown.hours > 0)
            return `${breakdown.hours}h`;
        if (breakdown.minutes > 0)
            return `${breakdown.minutes}m`;
        if (activeConfig.includeSeconds && breakdown.seconds > 0)
            return `${breakdown.seconds}s`;
        return '0m';
    }
    if (activeConfig.displayFormat === 'long') {
        if (parts.length === 1)
            return parts[0];
        if (parts.length === 2)
            return parts.join(' and ');
        return parts.slice(0, -1).join(', ') + ', and ' + parts[parts.length - 1];
    }
    // Mixed format (default)
    return parts.join(' ');
}
/**
 * Formats time breakdown with additional metadata
 */
export function formatTimeWithMetadata(totalSeconds, config) {
    const activeConfig = { ...globalConfig, ...config };
    const breakdown = breakdownTime(totalSeconds, activeConfig);
    const formatted = formatSeconds(totalSeconds, activeConfig);
    return {
        formatted,
        breakdown,
        config: activeConfig,
        equivalents: {
            totalHours: totalSeconds / 3600,
            totalMinutes: totalSeconds / 60,
            workDays: totalSeconds / (activeConfig.hoursPerDay * 3600),
        },
    };
}
/**
 * Parses time strings back to seconds (for testing/validation)
 */
export function parseTimeString(timeString) {
    const patterns = [
        { pattern: /(\d+)d/, multiplier: globalConfig.hoursPerDay * 3600 },
        { pattern: /(\d+)h/, multiplier: 3600 },
        { pattern: /(\d+)m/, multiplier: 60 },
        { pattern: /(\d+)s/, multiplier: 1 },
    ];
    let totalSeconds = 0;
    let hasMatch = false;
    for (const { pattern, multiplier } of patterns) {
        const match = timeString.match(pattern);
        if (match) {
            totalSeconds += parseInt(match[1]) * multiplier;
            hasMatch = true;
        }
    }
    return hasMatch ? totalSeconds : null;
}
/**
 * Validates work hours configuration
 */
export function validateWorkHoursConfig(config) {
    const errors = [];
    if (config.hoursPerDay !== undefined) {
        if (!Number.isInteger(config.hoursPerDay) ||
            config.hoursPerDay < 1 ||
            config.hoursPerDay > 24) {
            errors.push('hoursPerDay must be an integer between 1 and 24');
        }
    }
    if (config.minutesPerHour !== undefined) {
        if (!Number.isInteger(config.minutesPerHour) ||
            config.minutesPerHour < 1 ||
            config.minutesPerHour > 120) {
            errors.push('minutesPerHour must be an integer between 1 and 120');
        }
    }
    if (config.displayFormat !== undefined) {
        if (!['short', 'long', 'mixed'].includes(config.displayFormat)) {
            errors.push('displayFormat must be "short", "long", or "mixed"');
        }
    }
    return errors;
}
/**
 * Gets configuration information as a formatted string
 */
export function getConfigInfo() {
    const config = getWorkHoursConfig();
    return `
Work Hours Configuration:
• Hours per day: ${config.hoursPerDay}
• Minutes per hour: ${config.minutesPerHour}
• Display format: ${config.displayFormat}
• Include seconds: ${config.includeSeconds}

Environment Variables (optional):
• WORK_HOURS_PER_DAY: Override hours per work day (1-24)
• TIME_DISPLAY_FORMAT: Set display format (short|long|mixed)  
• INCLUDE_SECONDS: Show seconds in output (true|false)
  `.trim();
}
//# sourceMappingURL=time-formatter.js.map