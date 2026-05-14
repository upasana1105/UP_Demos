/**
 * User lookup caching system to reduce redundant API calls
 * Implements in-memory LRU cache with TTL for user data
 */
export class UserCache {
    cache = new Map();
    accessOrder = new Map();
    accessCounter = 0;
    config;
    constructor(config = {}) {
        this.config = {
            maxSize: 1000, // Max 1000 users in cache
            ttlMs: 15 * 60 * 1000, // 15 minutes TTL
            ...config,
        };
    }
    /**
     * Gets user from cache by any identifier
     */
    get(identifier) {
        const key = this.normalizeKey(identifier);
        const cached = this.cache.get(key);
        if (!cached) {
            return null;
        }
        // Check TTL
        if (Date.now() - cached.cachedAt > this.config.ttlMs) {
            this.cache.delete(key);
            this.accessOrder.delete(key);
            return null;
        }
        // Update access order for LRU
        this.accessOrder.set(key, ++this.accessCounter);
        return cached;
    }
    /**
     * Stores user in cache with all possible identifiers as keys
     */
    set(user) {
        const cachedUser = {
            ...user,
            cachedAt: Date.now(),
        };
        // Store under multiple keys for different lookup methods
        const keys = this.generateKeys(user);
        keys.forEach((key) => {
            this.cache.set(key, cachedUser);
            this.accessOrder.set(key, ++this.accessCounter);
        });
        // Enforce size limit with LRU eviction
        this.evictIfNeeded();
    }
    /**
     * Removes user from cache
     */
    delete(identifier) {
        const keys = this.findRelatedKeys(identifier);
        keys.forEach((key) => {
            this.cache.delete(key);
            this.accessOrder.delete(key);
        });
    }
    /**
     * Clears all cached data
     */
    clear() {
        this.cache.clear();
        this.accessOrder.clear();
        this.accessCounter = 0;
    }
    /**
     * Gets cache statistics
     */
    getStats() {
        const oldestTimestamp = Array.from(this.cache.values()).reduce((oldest, user) => (oldest === null || user.cachedAt < oldest ? user.cachedAt : oldest), null);
        // Rough memory usage calculation
        const avgEntrySize = 200; // bytes per cache entry
        const memoryUsageKB = Math.round((this.cache.size * avgEntrySize) / 1024);
        return {
            size: this.cache.size,
            hitRate: 0, // Would need to track hits/misses for this
            oldestEntry: oldestTimestamp,
            memoryUsageKB,
        };
    }
    /**
     * Normalizes cache keys for consistent lookup
     */
    normalizeKey(identifier) {
        return identifier.toLowerCase().trim();
    }
    /**
     * Generates all possible cache keys for a user
     */
    generateKeys(user) {
        const keys = [];
        // Always include accountId
        if (user.accountId) {
            keys.push(this.normalizeKey(user.accountId));
        }
        // Include displayName if available
        if (user.displayName) {
            keys.push(this.normalizeKey(user.displayName));
        }
        // Include email if available (though we're deprecating email lookup)
        if (user.emailAddress) {
            keys.push(this.normalizeKey(user.emailAddress));
        }
        return keys;
    }
    /**
     * Finds all cache keys related to an identifier
     */
    findRelatedKeys(identifier) {
        const normalizedId = this.normalizeKey(identifier);
        const relatedKeys = [];
        // Find the cached user first
        const cachedUser = this.cache.get(normalizedId);
        if (cachedUser) {
            // Generate all keys for this user
            relatedKeys.push(...this.generateKeys(cachedUser));
        }
        else {
            // Just the provided identifier
            relatedKeys.push(normalizedId);
        }
        return relatedKeys;
    }
    /**
     * Evicts least recently used entries to maintain size limit
     */
    evictIfNeeded() {
        while (this.cache.size > this.config.maxSize) {
            // Find LRU entry
            let lruKey = null;
            let lruAccessTime = Infinity;
            for (const [key, accessTime] of this.accessOrder) {
                if (accessTime < lruAccessTime) {
                    lruAccessTime = accessTime;
                    lruKey = key;
                }
            }
            if (lruKey) {
                const user = this.cache.get(lruKey);
                if (user) {
                    // Remove all keys for this user
                    const keysToRemove = this.generateKeys(user);
                    keysToRemove.forEach((key) => {
                        this.cache.delete(key);
                        this.accessOrder.delete(key);
                    });
                }
            }
        }
    }
    /**
     * Performs cache maintenance (remove expired entries)
     */
    maintenance() {
        const now = Date.now();
        const expiredKeys = [];
        for (const [key, user] of this.cache) {
            if (now - user.cachedAt > this.config.ttlMs) {
                expiredKeys.push(key);
            }
        }
        expiredKeys.forEach((key) => {
            this.cache.delete(key);
            this.accessOrder.delete(key);
        });
    }
}
// Global cache instance
let globalUserCache = null;
/**
 * Gets the global user cache instance
 */
export function getUserCache(config) {
    if (!globalUserCache || config) {
        globalUserCache = new UserCache(config);
    }
    return globalUserCache;
}
/**
 * Helper function to create cache key from user identification args
 */
export function createCacheKey(args) {
    // Prefer accountId, then username, then email
    if (args.accountId)
        return args.accountId.toLowerCase().trim();
    if (args.username)
        return args.username.toLowerCase().trim();
    if (args.email)
        return args.email.toLowerCase().trim();
    throw new Error('At least one identifier required for cache key');
}
//# sourceMappingURL=user-cache.js.map