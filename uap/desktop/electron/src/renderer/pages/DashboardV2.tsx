import { useEffect, useState } from "react";
import type { Job } from "../components/JobTable";
import { JobTable } from "../components/JobTable";
import { HealthStatus, LiveMetricsGrid } from "../components/LiveMetricsCard";
import { useBackend, useJobs } from "../hooks/useBackend";
import { initializeCache } from "../lib/db";

interface SelectedJob extends Job {
  details?: Record<string, any>;
}

export default function Dashboard() {
  const backendUrl =
    localStorage.getItem("backend_url") || "http://localhost:8001";
  const [selectedJob, setSelectedJob] = useState<SelectedJob | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  // Initialize Dexie cache on mount
  useEffect(() => {
    initializeCache();
  }, []);

  // Fetch backend status and KPIs
  const {
    status,
    kpis,
    loading: statusLoading,
    isOffline,
  } = useBackend(backendUrl, 3000);

  // Fetch jobs list
  const { jobs, loading: jobsLoading } = useJobs(backendUrl, 5000);

  // Update timestamp when data changes
  useEffect(() => {
    setLastUpdate(new Date());
  }, [kpis, jobs]);

  // Determine backend health
  const getBackendHealth = () => {
    if (isOffline) return "offline" as const;
    if (!status.running) return "degraded" as const;
    return "healthy" as const;
  };

  const metrics = [
    {
      title: "Total Jobs",
      value: kpis.total_jobs || 0,
      icon: "📊",
      color: "blue" as const,
    },
    {
      title: "Successful",
      value: kpis.successful_jobs || 0,
      icon: "✅",
      color: "green" as const,
      trend:
        (kpis.successful_jobs || 0) > 0
          ? ("up" as const)
          : ("neutral" as const),
    },
    {
      title: "Failed",
      value: kpis.failed_jobs || 0,
      icon: "❌",
      color: "red" as const,
      trend:
        (kpis.failed_jobs || 0) > 0 ? ("up" as const) : ("neutral" as const),
    },
    {
      title: "Avg Time",
      value: (kpis.avg_processing_time || 0).toFixed(2),
      unit: "s",
      icon: "⏱️",
      color: "purple" as const,
    },
    {
      title: "XRP Volume",
      value: (kpis.total_xrp_volume || 0).toFixed(0),
      unit: "XRP",
      icon: "💰",
      color: "yellow" as const,
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white">
            Dashboard
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Real-time arbitrage monitoring and job management
          </p>
        </div>

        {/* Health Status */}
        <div className="mb-6">
          <HealthStatus
            backendHealth={getBackendHealth()}
            lastUpdate={lastUpdate}
            errorMessage={
              isOffline
                ? "Backend unreachable - using cached data"
                : status.error
                  ? status.error
                  : undefined
            }
          />
        </div>

        {/* Metrics Grid */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            Key Metrics
          </h2>
          <LiveMetricsGrid
            metrics={metrics}
            isLoading={statusLoading}
            isOffline={isOffline}
          />
        </div>

        {/* Jobs Section */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              Recent Jobs
            </h2>
            <button
              className="px-4 py-2 bg-blue-500 dark:bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-600 dark:hover:bg-blue-700 transition-colors"
              onClick={() => {
                // Navigate to create job page (would need React Router integration)
                console.log("Create new job");
              }}
            >
              + New Job
            </button>
          </div>
          <div className="mt-4 bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
            <JobTable
              jobs={jobs as Job[]}
              isLoading={jobsLoading}
              isOffline={isOffline}
              onJobClick={(job) => setSelectedJob(job)}
            />
          </div>
        </div>

        {/* Job Details (if selected) */}
        {selectedJob && (
          <div className="fixed inset-0 bg-black bg-opacity-50 dark:bg-opacity-70 flex items-center justify-center p-4 z-50">
            <div className="bg-white dark:bg-gray-800 rounded-lg max-w-2xl w-full max-h-96 overflow-y-auto">
              <div className="p-6 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white">
                  Job Details: {selectedJob.name}
                </h3>
                <button
                  onClick={() => setSelectedJob(null)}
                  className="text-2xl text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                >
                  ×
                </button>
              </div>
              <div className="p-6 space-y-4">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Job ID
                  </p>
                  <p className="font-mono text-gray-900 dark:text-white">
                    {selectedJob.id}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Status
                  </p>
                  <p className="text-lg font-semibold text-gray-900 dark:text-white capitalize">
                    {selectedJob.status}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Created
                  </p>
                  <p className="text-gray-900 dark:text-white">
                    {new Date(selectedJob.created_at).toLocaleString()}
                  </p>
                </div>
                {selectedJob.error && (
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Error
                    </p>
                    <p className="text-red-600 dark:text-red-400">
                      {selectedJob.error}
                    </p>
                  </div>
                )}
                {selectedJob.results && (
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Results
                    </p>
                    <pre className="bg-gray-100 dark:bg-gray-900 p-2 rounded text-xs overflow-auto max-h-32 text-gray-900 dark:text-gray-100">
                      {JSON.stringify(selectedJob.results, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Backend Info */}
        <div className="mt-8 p-6 bg-white dark:bg-gray-800 rounded-lg shadow-md">
          <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">
            System Information
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <p className="text-gray-600 dark:text-gray-400">Backend URL</p>
              <p className="font-mono text-gray-900 dark:text-white text-xs">
                {backendUrl}
              </p>
            </div>
            <div>
              <p className="text-gray-600 dark:text-gray-400">Status</p>
              <p className="text-gray-900 dark:text-white capitalize">
                {status.status || "unknown"}
              </p>
            </div>
            <div>
              <p className="text-gray-600 dark:text-gray-400">Type</p>
              <p className="text-gray-900 dark:text-white">
                {status.backend_type || "unknown"}
              </p>
            </div>
            <div>
              <p className="text-gray-600 dark:text-gray-400">Mode</p>
              <p className="text-gray-900 dark:text-white">
                {isOffline ? "📦 Offline" : "🟢 Online"}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
