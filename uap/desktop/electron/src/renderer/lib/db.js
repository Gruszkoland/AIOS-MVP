import Dexie from "dexie";
/**
 * ADRIAN 369 Offline Database
 * Stores jobs, KPIs, and backend status for offline availability
 */
class AdrianDatabase extends Dexie {
    constructor() {
        super("ADRIAN369");
        Object.defineProperty(this, "jobs", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "kpis", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "status", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        this.version(1).stores({
            jobs: "++id, status, created_at", // Primary key ++id, indexes on status and created_at
            kpis: "++id, timestamp", // Numeric key, indexed by timestamp
            status: "++id, timestamp", // Latest status records
        });
    }
}
export const db = new AdrianDatabase();
/**
 * Cache jobs in Dexie
 */
export async function cacheJobs(jobs) {
    try {
        const now = Date.now();
        const jobsWithSync = jobs.map((j) => ({ ...j, synced_at: now }));
        await db.jobs.bulkPut(jobsWithSync);
    }
    catch (error) {
        console.error("Error caching jobs:", error);
    }
}
/**
 * Get cached jobs from Dexie
 */
export async function getCachedJobs() {
    try {
        return await db.jobs.toArray();
    }
    catch (error) {
        console.error("Error retrieving cached jobs:", error);
        return [];
    }
}
/**
 * Cache KPI metrics
 */
export async function cacheKPIs(metrics) {
    try {
        await db.kpis.add({ ...metrics, timestamp: Date.now() });
    }
    catch (error) {
        console.error("Error caching KPIs:", error);
    }
}
/**
 * Get latest KPI metrics from cache
 */
export async function getCachedKPIs() {
    try {
        const records = await db.kpis
            .orderBy("timestamp")
            .reverse()
            .limit(1)
            .toArray();
        return records.length > 0 ? records[0] : null;
    }
    catch (error) {
        console.error("Error retrieving cached KPIs:", error);
        return null;
    }
}
/**
 * Cache backend status
 */
export async function cacheBackendStatus(status) {
    try {
        await db.status.add({ ...status, timestamp: Date.now() });
    }
    catch (error) {
        console.error("Error caching backend status:", error);
    }
}
/**
 * Get latest backend status from cache
 */
export async function getCachedBackendStatus() {
    try {
        const records = await db.status
            .orderBy("timestamp")
            .reverse()
            .limit(1)
            .toArray();
        return records.length > 0 ? records[0] : null;
    }
    catch (error) {
        console.error("Error retrieving cached backend status:", error);
        return null;
    }
}
/**
 * Clear old cached data (older than 24 hours)
 */
export async function clearOldCache() {
    try {
        const oneDayAgo = Date.now() - 24 * 60 * 60 * 1000;
        // Clear old jobs (synced more than 24h ago)
        const oldJobs = await db.jobs.where("synced_at").below(oneDayAgo).toArray();
        if (oldJobs.length > 0) {
            await db.jobs.bulkDelete(oldJobs.map((j) => j.id));
            console.log(`Cleared ${oldJobs.length} old cached jobs`);
        }
        // Clear old KPIs
        await db.kpis.where("timestamp").below(oneDayAgo).delete();
        // Clear old status records
        await db.status.where("timestamp").below(oneDayAgo).delete();
        console.log("Cache cleanup completed");
    }
    catch (error) {
        console.error("Error clearing old cache:", error);
    }
}
/**
 * Initialize cache (run on app startup)
 */
export async function initializeCache() {
    try {
        await clearOldCache();
        console.log("✅ Dexie offline database initialized");
    }
    catch (error) {
        console.error("Error initializing cache:", error);
    }
}
//# sourceMappingURL=db.js.map