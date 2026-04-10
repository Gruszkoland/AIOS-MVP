interface BackendStatus {
    status: string;
    running: boolean;
    backend_type?: string;
    error?: string;
}
interface KPIMetrics {
    total_jobs: number;
    successful_jobs: number;
    failed_jobs: number;
    avg_processing_time: number;
    total_xrp_volume: number;
}
interface UseBackendReturn {
    status: BackendStatus;
    kpis: KPIMetrics;
    loading: boolean;
    isOffline: boolean;
}
/**
 * Custom hook for backend data with Dexie offline support
 * Falls back to cached data if backend is unreachable
 */
export declare function useBackend(backendUrl?: string, pollInterval?: number): UseBackendReturn;
/**
 * Custom hook for fetching jobs with Dexie offline support
 */
export declare function useJobs(backendUrl?: string, pollInterval?: number): {
    jobs: any[];
    loading: boolean;
    isOffline: boolean;
};
export {};
//# sourceMappingURL=useBackend.d.ts.map