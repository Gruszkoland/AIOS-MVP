import { useEffect, useState } from "react";
import { cacheBackendStatus, cacheJobs, cacheKPIs, getCachedBackendStatus, getCachedJobs, getCachedKPIs, } from "../lib/db";
/**
 * Custom hook for backend data with Dexie offline support
 * Falls back to cached data if backend is unreachable
 */
export function useBackend(backendUrl = "http://localhost:8001", pollInterval = 3000) {
    const [status, setStatus] = useState({
        status: "checking...",
        running: false,
    });
    const [kpis, setKpis] = useState({
        total_jobs: 0,
        successful_jobs: 0,
        failed_jobs: 0,
        avg_processing_time: 0,
        total_xrp_volume: 0,
    });
    const [loading, setLoading] = useState(true);
    const [isOffline, setIsOffline] = useState(false);
    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                // Try to fetch status
                const statusResponse = await fetch(`${backendUrl}/api/arbitrage/status`, { signal: AbortSignal.timeout(3000) });
                const statusData = await statusResponse.json();
                setStatus({
                    ...statusData,
                    running: statusResponse.ok,
                });
                setIsOffline(false);
                // Cache the status
                await cacheBackendStatus(statusData);
                // Try to fetch KPIs
                try {
                    const kpiResponse = await fetch(`${backendUrl}/api/arbitrage/kpis`, {
                        signal: AbortSignal.timeout(3000),
                    });
                    if (kpiResponse.ok) {
                        const kpiData = await kpiResponse.json();
                        setKpis(kpiData);
                        await cacheKPIs(kpiData);
                    }
                }
                catch (e) {
                    console.log("KPI endpoint not available");
                }
            }
            catch (error) {
                console.warn("Backend unreachable, using cached data:", error);
                setIsOffline(true);
                // Fall back to cached data
                const cachedStatus = await getCachedBackendStatus();
                if (cachedStatus) {
                    setStatus({
                        status: "offline (cached)",
                        running: false,
                        backend_type: cachedStatus.backend_type,
                    });
                }
                else {
                    setStatus({
                        status: "error",
                        running: false,
                        error: "Backend unreachable and no cached data available",
                    });
                }
                // Try to get cached KPIs
                const cachedKpis = await getCachedKPIs();
                if (cachedKpis) {
                    setKpis(cachedKpis);
                }
            }
            finally {
                setLoading(false);
            }
        };
        fetchData();
        const interval = setInterval(fetchData, pollInterval);
        return () => clearInterval(interval);
    }, [backendUrl, pollInterval]);
    return { status, kpis, loading, isOffline };
}
/**
 * Custom hook for fetching jobs with Dexie offline support
 */
export function useJobs(backendUrl = "http://localhost:8001", pollInterval = 5000) {
    const [jobs, setJobs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [isOffline, setIsOffline] = useState(false);
    useEffect(() => {
        const fetchJobs = async () => {
            try {
                setLoading(true);
                const response = await fetch(`${backendUrl}/api/arbitrage/jobs`, {
                    signal: AbortSignal.timeout(3000),
                });
                if (response.ok) {
                    const data = await response.json();
                    const jobsArray = Array.isArray(data) ? data : [];
                    setJobs(jobsArray);
                    setIsOffline(false);
                    // Cache the jobs
                    await cacheJobs(jobsArray);
                }
                else {
                    throw new Error(`HTTP ${response.status}`);
                }
            }
            catch (error) {
                console.warn("Failed to fetch jobs, using cached:", error);
                setIsOffline(true);
                // Fall back to cached jobs
                const cachedJobs = await getCachedJobs();
                setJobs(cachedJobs);
            }
            finally {
                setLoading(false);
            }
        };
        fetchJobs();
        const interval = setInterval(fetchJobs, pollInterval);
        return () => clearInterval(interval);
    }, [backendUrl, pollInterval]);
    return { jobs, loading, isOffline };
}
//# sourceMappingURL=useBackend.js.map