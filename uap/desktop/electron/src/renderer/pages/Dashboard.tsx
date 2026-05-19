import React, { useEffect } from "react";
import { useBackend } from "../hooks/useBackend";
import { initializeCache } from "../lib/db";

const Dashboard: React.FC = () => {
  // Initialize offline database on mount
  useEffect(() => {
    initializeCache();
  }, []);

  // Use custom hooks with Dexie fallback
  const backendUrl =
    localStorage.getItem("backend_url") || "http://localhost:8001";
  const {
    status: backendStatus,
    kpis: kpiMetrics,
    loading,
    isOffline,
  } = useBackend(backendUrl, 3000);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold mb-2">Dashboard</h2>
        <p className="text-slate-400">
          Real-time monitoring of ADRIAN 369 arbitrage system
        </p>
      </div>

      {/* Backend Status Card - with Offline Indicator */}
      <div className="bg-slate-900 rounded-lg p-6 border border-slate-700">
        <h3 className="text-xl font-semibold mb-4">Backend Status</h3>
        <div className="flex items-center gap-4">
          <div
            className={`text-4xl ${backendStatus.running ? "text-green-400" : "text-red-400"}`}
          >
            {backendStatus.running ? "✅" : "❌"}
          </div>
          <div className="flex-1">
            <p className="text-slate-300">
              Status:{" "}
              <span
                className={`font-bold ${backendStatus.running ? "text-green-400" : "text-red-400"}`}
              >
                {backendStatus.status} {isOffline && "(offline mode)"}
              </span>
            </p>
            {backendStatus.backend_type && (
              <p className="text-sm text-slate-400 mt-1">
                Backend:{" "}
                <span className="font-mono">{backendStatus.backend_type}</span>
              </p>
            )}
            {backendStatus.error && (
              <p className="text-sm text-red-400 mt-2">{backendStatus.error}</p>
            )}
            {isOffline && (
              <p className="text-xs text-yellow-400 mt-2">
                📦 Using cached data from local IndexedDB (Dexie)
              </p>
            )}
          </div>
          <div className="text-right text-xs text-slate-500">
            {loading ? "updating..." : "live"}
          </div>
        </div>
      </div>

      {/* KPI Metrics Grid */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
        {/* Total Jobs */}
        <div className="bg-slate-900 rounded-lg p-4 border border-slate-700">
          <p className="text-xs text-slate-400 mb-1">Total Jobs</p>
          <p className="text-2xl font-bold text-blue-400">
            {kpiMetrics.total_jobs}
          </p>
        </div>

        {/* Successful Jobs */}
        <div className="bg-slate-900 rounded-lg p-4 border border-slate-700">
          <p className="text-xs text-slate-400 mb-1">Successful</p>
          <p className="text-2xl font-bold text-green-400">
            {kpiMetrics.successful_jobs}
          </p>
        </div>

        {/* Failed Jobs */}
        <div className="bg-slate-900 rounded-lg p-4 border border-slate-700">
          <p className="text-xs text-slate-400 mb-1">Failed</p>
          <p className="text-2xl font-bold text-red-400">
            {kpiMetrics.failed_jobs}
          </p>
        </div>

        {/* Avg Processing Time */}
        <div className="bg-slate-900 rounded-lg p-4 border border-slate-700">
          <p className="text-xs text-slate-400 mb-1">Avg Time</p>
          <p className="text-2xl font-bold text-yellow-400">
            {kpiMetrics.avg_processing_time.toFixed(2)}s
          </p>
        </div>

        {/* Total XRP Volume */}
        <div className="bg-slate-900 rounded-lg p-4 border border-slate-700">
          <p className="text-xs text-slate-400 mb-1">XRP Volume</p>
          <p className="text-2xl font-bold text-purple-400">
            {kpiMetrics.total_xrp_volume.toFixed(0)}
          </p>
        </div>
      </div>

      {/* System Info Card */}
      <div className="bg-slate-900 rounded-lg p-6 border border-slate-700">
        <h3 className="text-lg font-semibold mb-4">System Information</h3>
        <dl className="grid grid-cols-2 gap-4 text-sm text-slate-400">
          <div>
            <dt className="text-slate-500">Platform</dt>
            <dd className="font-mono text-slate-300">{process.platform}</dd>
          </div>
          <div>
            <dt className="text-slate-500">Cache Status</dt>
            <dd className="font-mono text-slate-300">
              {isOffline ? "Offline Mode" : "Online"}
            </dd>
          </div>
          <div>
            <dt className="text-slate-500">Database</dt>
            <dd className="font-mono text-slate-300">Dexie (IndexedDB)</dd>
          </div>
          <div>
            <dt className="text-slate-500">Session</dt>
            <dd className="font-mono text-slate-300">Session 11</dd>
          </div>
        </dl>
      </div>

      {/* Session Info Card */}
      <div className="bg-blue-950 rounded-lg p-6 border border-blue-700">
        <h3 className="text-lg font-semibold mb-3 text-blue-300">
          Session 11: Dashboard Migration
        </h3>
        <ul className="space-y-2 text-sm text-slate-300">
          <li>✅ React Router navigation</li>
          <li>✅ Dashboard with KPI metrics</li>
          <li>✅ Dexie offline database</li>
          <li>→ Real-time WebSocket updates (Socket.io)</li>
          <li>→ MSI installer packaging</li>
        </ul>
      </div>
    </div>
  );
};

export default Dashboard;
