import React, { useEffect } from "react";
import { useJobs } from "../hooks/useBackend";
import { initializeCache } from "../lib/db";

interface Job {
  id: string;
  status: "pending" | "analyzing" | "approved" | "failed";
  created_at: string;
  xrp_amount: number;
  pair?: string;
  error?: string;
}

const JobsPage: React.FC = () => {
  // Initialize offline database on mount
  useEffect(() => {
    initializeCache();
  }, []);

  // Use custom hooks with Dexie offline support
  const backendUrl =
    localStorage.getItem("backend_url") || "http://localhost:8001";
  const { jobs, loading, isOffline } = useJobs(backendUrl, 5000);

  const getStatusBadgeColor = (status: Job["status"]) => {
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

  const getStatusIcon = (status: Job["status"]) => {
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold mb-2">Jobs Monitor</h2>
        <p className="text-slate-400">
          Track all arbitrage jobs {isOffline && "- Offline Mode 📦"}
        </p>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="bg-slate-900 rounded-lg p-6 border border-slate-700 text-center">
          <p className="text-slate-400">Loading jobs...</p>
        </div>
      )}

      {/* Empty State */}
      {!loading && jobs.length === 0 && (
        <div className="bg-slate-900 rounded-lg p-6 border border-slate-700 text-center">
          <p className="text-slate-400">No jobs yet</p>
          <p className="text-xs text-slate-500 mt-2">
            Start a job from the Settings page
          </p>
        </div>
      )}

      {/* Jobs Table */}
      {jobs.length > 0 && (
        <div className="bg-slate-900 rounded-lg border border-slate-700 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              {/* Table Header */}
              <thead className="bg-slate-950 border-b border-slate-700">
                <tr>
                  <th className="px-6 py-3 text-left font-semibold text-slate-300">
                    Job ID
                  </th>
                  <th className="px-6 py-3 text-left font-semibold text-slate-300">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left font-semibold text-slate-300">
                    Pair
                  </th>
                  <th className="px-6 py-3 text-right font-semibold text-slate-300">
                    XRP Amount
                  </th>
                  <th className="px-6 py-3 text-left font-semibold text-slate-300">
                    Created At
                  </th>
                </tr>
              </thead>

              {/* Table Body */}
              <tbody className="divide-y divide-slate-700">
                {jobs.map((job) => (
                  <tr
                    key={job.id}
                    className="hover:bg-slate-800 transition-colors"
                  >
                    <td className="px-6 py-4 font-mono text-slate-300">
                      {job.id.substring(0, 8)}...
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`inline-flex items-center gap-2 px-3 py-1 rounded-full ${getStatusBadgeColor(
                          job.status,
                        )}`}
                      >
                        {getStatusIcon(job.status)} {job.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-slate-400">
                      {job.pair || "N/A"}
                    </td>
                    <td className="px-6 py-4 text-right font-mono">
                      <span className="text-blue-400">{job.xrp_amount}</span>{" "}
                      XRP
                    </td>
                    <td className="px-6 py-4 text-slate-400">
                      {new Date(job.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Stats Footer */}
      {jobs.length > 0 && (
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-slate-900 rounded-lg p-4 border border-slate-700">
            <p className="text-xs text-slate-400">Total</p>
            <p className="text-2xl font-bold text-blue-400">{jobs.length}</p>
          </div>
          <div className="bg-slate-900 rounded-lg p-4 border border-slate-700">
            <p className="text-xs text-slate-400">Approved</p>
            <p className="text-2xl font-bold text-green-400">
              {jobs.filter((j) => j.status === "approved").length}
            </p>
          </div>
          <div className="bg-slate-900 rounded-lg p-4 border border-slate-700">
            <p className="text-xs text-slate-400">Processing</p>
            <p className="text-2xl font-bold text-yellow-400">
              {jobs.filter((j) => j.status === "analyzing").length}
            </p>
          </div>
          <div className="bg-slate-900 rounded-lg p-4 border border-slate-700">
            <p className="text-xs text-slate-400">Failed</p>
            <p className="text-2xl font-bold text-red-400">
              {jobs.filter((j) => j.status === "failed").length}
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default JobsPage;
