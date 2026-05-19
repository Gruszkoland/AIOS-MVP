import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
function getStatusBadgeColor(status) {
    switch (status) {
        case "pending":
            return "bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-100";
        case "running":
            return "bg-blue-200 dark:bg-blue-900 text-blue-800 dark:text-blue-100";
        case "completed":
            return "bg-green-200 dark:bg-green-900 text-green-800 dark:text-green-100";
        case "failed":
            return "bg-red-200 dark:bg-red-900 text-red-800 dark:text-red-100";
        default:
            return "bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-100";
    }
}
function getStatusIcon(status) {
    switch (status) {
        case "pending":
            return "⏳";
        case "running":
            return "🔄";
        case "completed":
            return "✅";
        case "failed":
            return "❌";
        default:
            return "❓";
    }
}
export function JobTable({ jobs, isLoading, isOffline, onJobClick, }) {
    if (isLoading) {
        return (_jsx("div", { className: "space-y-2", children: [1, 2, 3].map((i) => (_jsx("div", { className: "h-12 bg-gray-200 dark:bg-gray-700 rounded-lg animate-pulse" }, i))) }));
    }
    if (!jobs || jobs.length === 0) {
        return (_jsxs("div", { className: "text-center py-8 text-gray-500 dark:text-gray-400", children: [_jsx("p", { className: "text-lg font-medium", children: "No jobs found" }), _jsx("p", { className: "text-sm", children: "Create a new job to get started" })] }));
    }
    return (_jsxs("div", { className: "overflow-x-auto", children: [isOffline && (_jsxs("div", { className: "mb-3 p-2 bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200 rounded-lg text-sm flex items-center gap-2", children: [_jsx("span", { children: "\uD83D\uDCE6" }), _jsx("span", { children: "Using cached job data (offline mode)" })] })), _jsxs("table", { className: "w-full border-collapse", children: [_jsx("thead", { children: _jsxs("tr", { className: "border-b-2 border-gray-300 dark:border-gray-600", children: [_jsx("th", { className: "text-left px-4 py-2 font-semibold text-gray-700 dark:text-gray-300", children: "Job ID" }), _jsx("th", { className: "text-left px-4 py-2 font-semibold text-gray-700 dark:text-gray-300", children: "Name" }), _jsx("th", { className: "text-center px-4 py-2 font-semibold text-gray-700 dark:text-gray-300", children: "Status" }), _jsx("th", { className: "text-center px-4 py-2 font-semibold text-gray-700 dark:text-gray-300", children: "Progress" }), _jsx("th", { className: "text-left px-4 py-2 font-semibold text-gray-700 dark:text-gray-300", children: "Created" }), _jsx("th", { className: "text-right px-4 py-2 font-semibold text-gray-700 dark:text-gray-300", children: "Actions" })] }) }), _jsx("tbody", { children: jobs.map((job) => (_jsxs("tr", { className: "border-b border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors", onClick: () => onJobClick?.(job), children: [_jsxs("td", { className: "px-4 py-2 font-mono text-sm text-gray-900 dark:text-gray-100", children: [job.id.substring(0, 8), "..."] }), _jsx("td", { className: "px-4 py-2 text-gray-900 dark:text-gray-100", children: job.name }), _jsx("td", { className: "px-4 py-2 text-center", children: _jsxs("span", { className: `inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${getStatusBadgeColor(job.status)}`, children: [getStatusIcon(job.status), " ", job.status] }) }), _jsx("td", { className: "px-4 py-2 text-center", children: job.status === "running" ? (_jsxs("div", { className: "flex items-center justify-center gap-2", children: [_jsx("div", { className: "w-24 h-2 bg-gray-300 dark:bg-gray-600 rounded-full overflow-hidden", children: _jsx("div", { className: "h-full bg-blue-500 transition-all duration-300", style: {
                                                        width: `${Math.min(job.progress || 0, 100)}%`,
                                                    } }) }), _jsxs("span", { className: "text-xs text-gray-600 dark:text-gray-400 w-8", children: [Math.round(job.progress || 0), "%"] })] })) : (_jsx("span", { className: "text-xs text-gray-500 dark:text-gray-400", children: "\u2014" })) }), _jsxs("td", { className: "px-4 py-2 text-sm text-gray-600 dark:text-gray-400", children: [new Date(job.created_at).toLocaleDateString(), " ", new Date(job.created_at).toLocaleTimeString()] }), _jsx("td", { className: "px-4 py-2 text-right", children: _jsx("button", { onClick: (e) => {
                                            e.stopPropagation();
                                            onJobClick?.(job);
                                        }, className: "px-3 py-1 text-xs bg-blue-500 dark:bg-blue-600 text-white rounded hover:bg-blue-600 dark:hover:bg-blue-700 transition-colors", children: "View" }) })] }, job.id))) })] })] }));
}
//# sourceMappingURL=JobTable.js.map