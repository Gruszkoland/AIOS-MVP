import Dexie, { Table } from "dexie";

export interface JobRecord {
  id: string;
  status: "pending" | "analyzing" | "approved" | "failed";
  created_at: string;
  xrp_amount: number;
  pair?: string;
  error?: string;
  synced_at: number; // timestamp of last sync with backend
}

export interface KPIRecord {
  id?: number;
  total_jobs: number;
  successful_jobs: number;
  failed_jobs: number;
  avg_processing_time: number;
  total_xrp_volume: number;
  timestamp: number;
}

export interface BackendStatusRecord {
  id?: number;
  status: string;
  running: boolean;
  backend_type?: string;
  error?: string;
  timestamp: number;
}

/**
 * ADRIAN 369 Offline Database
 * Stores jobs, KPIs, and backend status for offline availability
 */
class AdrianDatabase extends Dexie {
  jobs!: Table<JobRecord>;
  kpis!: Table<KPIRecord>;
  status!: Table<BackendStatusRecord>;

  constructor() {
    super("ADRIAN369");
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
export async function cacheJobs(jobs: JobRecord[]): Promise<void> {
  try {
    const now = Date.now();
    const jobsWithSync = jobs.map((j) => ({ ...j, synced_at: now }));
    await db.jobs.bulkPut(jobsWithSync);
  } catch (error) {
    console.error("Error caching jobs:", error);
  }
}

/**
 * Get cached jobs from Dexie
 */
export async function getCachedJobs(): Promise<JobRecord[]> {
  try {
    return await db.jobs.toArray();
  } catch (error) {
    console.error("Error retrieving cached jobs:", error);
    return [];
  }
}

/**
 * Cache KPI metrics
 */
export async function cacheKPIs(metrics: KPIRecord): Promise<void> {
  try {
    await db.kpis.add({ ...metrics, timestamp: Date.now() });
  } catch (error) {
    console.error("Error caching KPIs:", error);
  }
}

/**
 * Get latest KPI metrics from cache
 */
export async function getCachedKPIs(): Promise<KPIRecord | null> {
  try {
    const records = await db.kpis
      .orderBy("timestamp")
      .reverse()
      .limit(1)
      .toArray();
    return records.length > 0 ? records[0] : null;
  } catch (error) {
    console.error("Error retrieving cached KPIs:", error);
    return null;
  }
}

/**
 * Cache backend status
 */
export async function cacheBackendStatus(
  status: BackendStatusRecord,
): Promise<void> {
  try {
    await db.status.add({ ...status, timestamp: Date.now() });
  } catch (error) {
    console.error("Error caching backend status:", error);
  }
}

/**
 * Get latest backend status from cache
 */
export async function getCachedBackendStatus(): Promise<BackendStatusRecord | null> {
  try {
    const records = await db.status
      .orderBy("timestamp")
      .reverse()
      .limit(1)
      .toArray();
    return records.length > 0 ? records[0] : null;
  } catch (error) {
    console.error("Error retrieving cached backend status:", error);
    return null;
  }
}

/**
 * Clear old cached data (older than 24 hours)
 */
export async function clearOldCache(): Promise<void> {
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
  } catch (error) {
    console.error("Error clearing old cache:", error);
  }
}

/**
 * Initialize cache (run on app startup)
 */
export async function initializeCache(): Promise<void> {
  try {
    await clearOldCache();
    console.log("✅ Dexie offline database initialized");
  } catch (error) {
    console.error("Error initializing cache:", error);
  }
}
