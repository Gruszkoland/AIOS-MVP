
export interface Job {
  id: string;
  name: string;
  status: "pending" | "running" | "completed" | "failed";
  created_at: string;
  updated_at: string;
  progress?: number;
  error?: string;
  results?: Record<string, any>;
}

interface JobTableProps {
  jobs: Job[];
  isLoading?: boolean;
  isOffline?: boolean;
  onJobClick?: (job: Job) => void;
}

function getStatusBadgeColor(status: Job["status"]) {
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

function getStatusIcon(status: Job["status"]) {
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

export function JobTable({
  jobs,
  isLoading,
  isOffline,
  onJobClick,
}: JobTableProps) {
  if (isLoading) {
    return (
      <div className="space-y-2">
        {[1, 2, 3].map((i) => (
          <div
            key={i}
            className="h-12 bg-gray-200 dark:bg-gray-700 rounded-lg animate-pulse"
          />
        ))}
      </div>
    );
  }

  if (!jobs || jobs.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500 dark:text-gray-400">
        <p className="text-lg font-medium">No jobs found</p>
        <p className="text-sm">Create a new job to get started</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      {isOffline && (
        <div className="mb-3 p-2 bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200 rounded-lg text-sm flex items-center gap-2">
          <span>📦</span>
          <span>Using cached job data (offline mode)</span>
        </div>
      )}
      <table className="w-full border-collapse">
        <thead>
          <tr className="border-b-2 border-gray-300 dark:border-gray-600">
            <th className="text-left px-4 py-2 font-semibold text-gray-700 dark:text-gray-300">
              Job ID
            </th>
            <th className="text-left px-4 py-2 font-semibold text-gray-700 dark:text-gray-300">
              Name
            </th>
            <th className="text-center px-4 py-2 font-semibold text-gray-700 dark:text-gray-300">
              Status
            </th>
            <th className="text-center px-4 py-2 font-semibold text-gray-700 dark:text-gray-300">
              Progress
            </th>
            <th className="text-left px-4 py-2 font-semibold text-gray-700 dark:text-gray-300">
              Created
            </th>
            <th className="text-right px-4 py-2 font-semibold text-gray-700 dark:text-gray-300">
              Actions
            </th>
          </tr>
        </thead>
        <tbody>
          {jobs.map((job) => (
            <tr
              key={job.id}
              className="border-b border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
              onClick={() => onJobClick?.(job)}
            >
              <td className="px-4 py-2 font-mono text-sm text-gray-900 dark:text-gray-100">
                {job.id.substring(0, 8)}...
              </td>
              <td className="px-4 py-2 text-gray-900 dark:text-gray-100">
                {job.name}
              </td>
              <td className="px-4 py-2 text-center">
                <span
                  className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${getStatusBadgeColor(job.status)}`}
                >
                  {getStatusIcon(job.status)} {job.status}
                </span>
              </td>
              <td className="px-4 py-2 text-center">
                {job.status === "running" ? (
                  <div className="flex items-center justify-center gap-2">
                    <div className="w-24 h-2 bg-gray-300 dark:bg-gray-600 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-500 transition-all duration-300"
                        style={{
                          width: `${Math.min(job.progress || 0, 100)}%`,
                        }}
                      />
                    </div>
                    <span className="text-xs text-gray-600 dark:text-gray-400 w-8">
                      {Math.round(job.progress || 0)}%
                    </span>
                  </div>
                ) : (
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    —
                  </span>
                )}
              </td>
              <td className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400">
                {new Date(job.created_at).toLocaleDateString()}{" "}
                {new Date(job.created_at).toLocaleTimeString()}
              </td>
              <td className="px-4 py-2 text-right">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onJobClick?.(job);
                  }}
                  className="px-3 py-1 text-xs bg-blue-500 dark:bg-blue-600 text-white rounded hover:bg-blue-600 dark:hover:bg-blue-700 transition-colors"
                >
                  View
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
