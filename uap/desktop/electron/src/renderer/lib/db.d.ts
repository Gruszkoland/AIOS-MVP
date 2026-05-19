import Dexie, { Table } from "dexie";
export interface JobRecord {
    id: string;
    status: "pending" | "analyzing" | "approved" | "failed";
    created_at: string;
    xrp_amount: number;
    pair?: string;
    error?: string;
    synced_at: number;
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
declare class AdrianDatabase extends Dexie {
    jobs: Table<JobRecord>;
    kpis: Table<KPIRecord>;
    status: Table<BackendStatusRecord>;
    constructor();
}
export declare const db: AdrianDatabase;
/**
 * Cache jobs in Dexie
 */
export declare function cacheJobs(jobs: JobRecord[]): Promise<void>;
/**
 * Get cached jobs from Dexie
 */
export declare function getCachedJobs(): Promise<JobRecord[]>;
/**
 * Cache KPI metrics
 */
export declare function cacheKPIs(metrics: KPIRecord): Promise<void>;
/**
 * Get latest KPI metrics from cache
 */
export declare function getCachedKPIs(): Promise<KPIRecord | null>;
/**
 * Cache backend status
 */
export declare function cacheBackendStatus(status: BackendStatusRecord): Promise<void>;
/**
 * Get latest backend status from cache
 */
export declare function getCachedBackendStatus(): Promise<BackendStatusRecord | null>;
/**
 * Clear old cached data (older than 24 hours)
 */
export declare function clearOldCache(): Promise<void>;
/**
 * Initialize cache (run on app startup)
 */
export declare function initializeCache(): Promise<void>;
export {};
//# sourceMappingURL=db.d.ts.map