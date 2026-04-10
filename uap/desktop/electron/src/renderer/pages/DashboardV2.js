import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from "react";
import { JobTable } from "../components/JobTable";
import { HealthStatus, LiveMetricsGrid } from "../components/LiveMetricsCard";
import { useBackend, useJobs } from "../hooks/useBackend";
import { initializeCache } from "../lib/db";
export default function Dashboard() {
    const backendUrl = localStorage.getItem("backend_url") || "http://localhost:8001";
    const [selectedJob, setSelectedJob] = useState(null);
    const [lastUpdate, setLastUpdate] = useState(null);
    // Initialize Dexie cache on mount
    useEffect(() => {
        initializeCache();
    }, []);
    // Fetch backend status and KPIs
    const { status, kpis, loading: statusLoading, isOffline, } = useBackend(backendUrl, 3000);
    // Fetch jobs list
    const { jobs, loading: jobsLoading } = useJobs(backendUrl, 5000);
    // Update timestamp when data changes
    useEffect(() => {
        setLastUpdate(new Date());
    }, [kpis, jobs]);
    // Determine backend health
    const getBackendHealth = () => {
        if (isOffline)
            return "offline";
        if (!status.running)
            return "degraded";
        return "healthy";
    };
    const metrics = [
        {
            title: "Total Jobs",
            value: kpis.total_jobs || 0,
            icon: "📊",
            color: "blue",
        },
        {
            title: "Successful",
            value: kpis.successful_jobs || 0,
            icon: "✅",
            color: "green",
            trend: (kpis.successful_jobs || 0) > 0
                ? "up"
                : "neutral",
        },
        {
            title: "Failed",
            value: kpis.failed_jobs || 0,
            icon: "❌",
            color: "red",
            trend: (kpis.failed_jobs || 0) > 0 ? "up" : "neutral",
        },
        {
            title: "Avg Time",
            value: (kpis.avg_processing_time || 0).toFixed(2),
            unit: "s",
            icon: "⏱️",
            color: "purple",
        },
        {
            title: "XRP Volume",
            value: (kpis.total_xrp_volume || 0).toFixed(0),
            unit: "XRP",
            icon: "💰",
            color: "yellow",
        },
    ];
    return (_jsx("div", { className: "min-h-screen bg-gray-50 dark:bg-gray-900 p-6", children: _jsxs("div", { className: "max-w-7xl mx-auto", children: [_jsxs("div", { className: "mb-8", children: [_jsx("h1", { className: "text-4xl font-bold text-gray-900 dark:text-white", children: "Dashboard" }), _jsx("p", { className: "text-gray-600 dark:text-gray-400 mt-2", children: "Real-time arbitrage monitoring and job management" })] }), _jsx("div", { className: "mb-6", children: _jsx(HealthStatus, { backendHealth: getBackendHealth(), lastUpdate: lastUpdate, errorMessage: isOffline
                            ? "Backend unreachable - using cached data"
                            : status.error
                                ? status.error
                                : undefined }) }), _jsxs("div", { className: "mb-8", children: [_jsx("h2", { className: "text-2xl font-bold text-gray-900 dark:text-white mb-4", children: "Key Metrics" }), _jsx(LiveMetricsGrid, { metrics: metrics, isLoading: statusLoading, isOffline: isOffline })] }), _jsxs("div", { className: "mb-8", children: [_jsxs("div", { className: "flex items-center justify-between", children: [_jsx("h2", { className: "text-2xl font-bold text-gray-900 dark:text-white", children: "Recent Jobs" }), _jsx("button", { className: "px-4 py-2 bg-blue-500 dark:bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-600 dark:hover:bg-blue-700 transition-colors", onClick: () => {
                                        // Navigate to create job page (would need React Router integration)
                                        console.log("Create new job");
                                    }, children: "+ New Job" })] }), _jsx("div", { className: "mt-4 bg-white dark:bg-gray-800 rounded-lg shadow-md p-6", children: _jsx(JobTable, { jobs: jobs, isLoading: jobsLoading, isOffline: isOffline, onJobClick: (job) => setSelectedJob(job) }) })] }), selectedJob && (_jsx("div", { className: "fixed inset-0 bg-black bg-opacity-50 dark:bg-opacity-70 flex items-center justify-center p-4 z-50", children: _jsxs("div", { className: "bg-white dark:bg-gray-800 rounded-lg max-w-2xl w-full max-h-96 overflow-y-auto", children: [_jsxs("div", { className: "p-6 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between", children: [_jsxs("h3", { className: "text-xl font-bold text-gray-900 dark:text-white", children: ["Job Details: ", selectedJob.name] }), _jsx("button", { onClick: () => setSelectedJob(null), className: "text-2xl text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200", children: "\u00D7" })] }), _jsxs("div", { className: "p-6 space-y-4", children: [_jsxs("div", { children: [_jsx("p", { className: "text-sm text-gray-600 dark:text-gray-400", children: "Job ID" }), _jsx("p", { className: "font-mono text-gray-900 dark:text-white", children: selectedJob.id })] }), _jsxs("div", { children: [_jsx("p", { className: "text-sm text-gray-600 dark:text-gray-400", children: "Status" }), _jsx("p", { className: "text-lg font-semibold text-gray-900 dark:text-white capitalize", children: selectedJob.status })] }), _jsxs("div", { children: [_jsx("p", { className: "text-sm text-gray-600 dark:text-gray-400", children: "Created" }), _jsx("p", { className: "text-gray-900 dark:text-white", children: new Date(selectedJob.created_at).toLocaleString() })] }), selectedJob.error && (_jsxs("div", { children: [_jsx("p", { className: "text-sm text-gray-600 dark:text-gray-400", children: "Error" }), _jsx("p", { className: "text-red-600 dark:text-red-400", children: selectedJob.error })] })), selectedJob.results && (_jsxs("div", { children: [_jsx("p", { className: "text-sm text-gray-600 dark:text-gray-400", children: "Results" }), _jsx("pre", { className: "bg-gray-100 dark:bg-gray-900 p-2 rounded text-xs overflow-auto max-h-32 text-gray-900 dark:text-gray-100", children: JSON.stringify(selectedJob.results, null, 2) })] }))] })] }) })), _jsxs("div", { className: "mt-8 p-6 bg-white dark:bg-gray-800 rounded-lg shadow-md", children: [_jsx("h3", { className: "text-lg font-bold text-gray-900 dark:text-white mb-4", children: "System Information" }), _jsxs("div", { className: "grid grid-cols-2 md:grid-cols-4 gap-4 text-sm", children: [_jsxs("div", { children: [_jsx("p", { className: "text-gray-600 dark:text-gray-400", children: "Backend URL" }), _jsx("p", { className: "font-mono text-gray-900 dark:text-white text-xs", children: backendUrl })] }), _jsxs("div", { children: [_jsx("p", { className: "text-gray-600 dark:text-gray-400", children: "Status" }), _jsx("p", { className: "text-gray-900 dark:text-white capitalize", children: status.status || "unknown" })] }), _jsxs("div", { children: [_jsx("p", { className: "text-gray-600 dark:text-gray-400", children: "Type" }), _jsx("p", { className: "text-gray-900 dark:text-white", children: status.backend_type || "unknown" })] }), _jsxs("div", { children: [_jsx("p", { className: "text-gray-600 dark:text-gray-400", children: "Mode" }), _jsx("p", { className: "text-gray-900 dark:text-white", children: isOffline ? "📦 Offline" : "🟢 Online" })] })] })] })] }) }));
}
//# sourceMappingURL=DashboardV2.js.map