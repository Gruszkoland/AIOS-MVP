import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect } from "react";
import { useJobs } from "../hooks/useBackend";
import { initializeCache } from "../lib/db";
const JobsPage = () => {
    // Initialize offline database on mount
    useEffect(() => {
        initializeCache();
    }, []);
    // Use custom hooks with Dexie offline support
    const backendUrl = localStorage.getItem("backend_url") || "http://localhost:8001";
    const { jobs, loading, isOffline } = useJobs(backendUrl, 5000);
    const getStatusBadgeColor = (status) => {
        switch (status) {
            case "pending":
                return "bg-yellow-900 text-yellow-300";
            case "analyzing":
                return "bg-blue-900 text-blue-300";
            case "approved":
                return "bg-green-900 text-green-300";
            case "failed":
                return "bg-red-900 text-red-300";
            default:
                return "bg-slate-900 text-slate-300";
        }
    };
    const getStatusIcon = (status) => {
        switch (status) {
            case "pending":
                return "⏳";
            case "analyzing":
                return "🔄";
            case "approved":
                return "✅";
            case "failed":
                return "❌";
            default:
                return "❓";
        }
    };
    return (_jsxs("div", { className: "space-y-6", children: [_jsxs("div", { children: [_jsx("h2", { className: "text-3xl font-bold mb-2", children: "Jobs Monitor" }), _jsxs("p", { className: "text-slate-400", children: ["Track all arbitrage jobs ", isOffline && "- Offline Mode 📦"] })] }), loading && (_jsx("div", { className: "bg-slate-900 rounded-lg p-6 border border-slate-700 text-center", children: _jsx("p", { className: "text-slate-400", children: "Loading jobs..." }) })), !loading && jobs.length === 0 && (_jsxs("div", { className: "bg-slate-900 rounded-lg p-6 border border-slate-700 text-center", children: [_jsx("p", { className: "text-slate-400", children: "No jobs yet" }), _jsx("p", { className: "text-xs text-slate-500 mt-2", children: "Start a job from the Settings page" })] })), jobs.length > 0 && (_jsx("div", { className: "bg-slate-900 rounded-lg border border-slate-700 overflow-hidden", children: _jsx("div", { className: "overflow-x-auto", children: _jsxs("table", { className: "w-full text-sm", children: [_jsx("thead", { className: "bg-slate-950 border-b border-slate-700", children: _jsxs("tr", { children: [_jsx("th", { className: "px-6 py-3 text-left font-semibold text-slate-300", children: "Job ID" }), _jsx("th", { className: "px-6 py-3 text-left font-semibold text-slate-300", children: "Status" }), _jsx("th", { className: "px-6 py-3 text-left font-semibold text-slate-300", children: "Pair" }), _jsx("th", { className: "px-6 py-3 text-right font-semibold text-slate-300", children: "XRP Amount" }), _jsx("th", { className: "px-6 py-3 text-left font-semibold text-slate-300", children: "Created At" })] }) }), _jsx("tbody", { className: "divide-y divide-slate-700", children: jobs.map((job) => (_jsxs("tr", { className: "hover:bg-slate-800 transition-colors", children: [_jsxs("td", { className: "px-6 py-4 font-mono text-slate-300", children: [job.id.substring(0, 8), "..."] }), _jsx("td", { className: "px-6 py-4", children: _jsxs("span", { className: `inline-flex items-center gap-2 px-3 py-1 rounded-full ${getStatusBadgeColor(job.status)}`, children: [getStatusIcon(job.status), " ", job.status] }) }), _jsx("td", { className: "px-6 py-4 text-slate-400", children: job.pair || "N/A" }), _jsxs("td", { className: "px-6 py-4 text-right font-mono", children: [_jsx("span", { className: "text-blue-400", children: job.xrp_amount }), " ", "XRP"] }), _jsx("td", { className: "px-6 py-4 text-slate-400", children: new Date(job.created_at).toLocaleString() })] }, job.id))) })] }) }) })), jobs.length > 0 && (_jsxs("div", { className: "grid grid-cols-4 gap-4", children: [_jsxs("div", { className: "bg-slate-900 rounded-lg p-4 border border-slate-700", children: [_jsx("p", { className: "text-xs text-slate-400", children: "Total" }), _jsx("p", { className: "text-2xl font-bold text-blue-400", children: jobs.length })] }), _jsxs("div", { className: "bg-slate-900 rounded-lg p-4 border border-slate-700", children: [_jsx("p", { className: "text-xs text-slate-400", children: "Approved" }), _jsx("p", { className: "text-2xl font-bold text-green-400", children: jobs.filter((j) => j.status === "approved").length })] }), _jsxs("div", { className: "bg-slate-900 rounded-lg p-4 border border-slate-700", children: [_jsx("p", { className: "text-xs text-slate-400", children: "Processing" }), _jsx("p", { className: "text-2xl font-bold text-yellow-400", children: jobs.filter((j) => j.status === "analyzing").length })] }), _jsxs("div", { className: "bg-slate-900 rounded-lg p-4 border border-slate-700", children: [_jsx("p", { className: "text-xs text-slate-400", children: "Failed" }), _jsx("p", { className: "text-2xl font-bold text-red-400", children: jobs.filter((j) => j.status === "failed").length })] })] }))] }));
};
export default JobsPage;
//# sourceMappingURL=JobsPage.js.map