
interface MetricProps {
  title: string;
  value: string | number;
  unit?: string;
  trend?: "up" | "down" | "neutral";
  icon?: string;
  color?: "green" | "blue" | "red" | "yellow" | "purple";
}

export function MetricCard({
  title,
  value,
  unit,
  trend,
  icon,
  color = "blue",
}: MetricProps) {
  const colorClasses = {
    green: "border-green-500 bg-green-50 dark:bg-green-900",
    blue: "border-blue-500 bg-blue-50 dark:bg-blue-900",
    red: "border-red-500 bg-red-50 dark:bg-red-900",
    yellow: "border-yellow-500 bg-yellow-50 dark:bg-yellow-900",
    purple: "border-purple-500 bg-purple-50 dark:bg-purple-900",
  };

  const textColorClasses = {
    green: "text-green-600 dark:text-green-300",
    blue: "text-blue-600 dark:text-blue-300",
    red: "text-red-600 dark:text-red-300",
    yellow: "text-yellow-600 dark:text-yellow-300",
    purple: "text-purple-600 dark:text-purple-300",
  };

  const trendClass =
    trend === "up"
      ? "text-green-600"
      : trend === "down"
        ? "text-red-600"
        : "text-gray-600";

  return (
    <div className={`border-l-4 rounded-lg p-4 ${colorClasses[color]}`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
            {title}
          </p>
          <div className="mt-2 flex items-baseline gap-2">
            <p className={`text-2xl font-bold ${textColorClasses[color]}`}>
              {value}
            </p>
            {unit && (
              <p className="text-sm text-gray-600 dark:text-gray-400">{unit}</p>
            )}
          </div>
        </div>
        {icon && <span className="text-3xl">{icon}</span>}
      </div>
      {trend && (
        <p className={`mt-2 text-xs font-semibold ${trendClass}`}>
          {trend === "up" ? "↑" : trend === "down" ? "↓" : "→"}{" "}
          {trend === "up"
            ? "Increasing"
            : trend === "down"
              ? "Decreasing"
              : "Stable"}
        </p>
      )}
    </div>
  );
}

interface LiveMetricsGridProps {
  metrics: MetricProps[];
  isLoading?: boolean;
  isOffline?: boolean;
}

export function LiveMetricsGrid({
  metrics,
  isLoading,
  isOffline,
}: LiveMetricsGridProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="border-l-4 border-gray-300 rounded-lg p-4 bg-gray-50 dark:bg-gray-800 animate-pulse"
          >
            <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded w-3/4 mb-2"></div>
            <div className="h-8 bg-gray-300 dark:bg-gray-600 rounded w-1/2"></div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div>
      {isOffline && (
        <div className="mb-4 p-3 bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200 rounded-lg flex items-center gap-2">
          <span>📦</span>
          <span className="text-sm font-medium">
            Using cached data from local IndexedDB (offline mode)
          </span>
        </div>
      )}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {metrics.map((metric, idx) => (
          <MetricCard key={idx} {...metric} />
        ))}
      </div>
    </div>
  );
}

interface HealthStatusProps {
  backendHealth: "healthy" | "degraded" | "offline";
  lastUpdate: Date | null;
  errorMessage?: string;
}

export function HealthStatus({
  backendHealth,
  lastUpdate,
  errorMessage,
}: HealthStatusProps) {
  const statusColors = {
    healthy:
      "bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 border-green-300 dark:border-green-700",
    degraded:
      "bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200 border-yellow-300 dark:border-yellow-700",
    offline:
      "bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200 border-red-300 dark:border-red-700",
  };

  const statusIcon = {
    healthy: "🟢",
    degraded: "🟡",
    offline: "🔴",
  };

  const statusLabel = {
    healthy: "Healthy",
    degraded: "Degraded",
    offline: "Offline",
  };

  return (
    <div className={`border rounded-lg p-4 ${statusColors[backendHealth]}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xl">{statusIcon[backendHealth]}</span>
          <span className="font-semibold">{statusLabel[backendHealth]}</span>
        </div>
        {lastUpdate && (
          <span className="text-sm opacity-75">
            Updated {lastUpdate.toLocaleTimeString()}
          </span>
        )}
      </div>
      {errorMessage && (
        <p className="text-sm mt-2 opacity-90">{errorMessage}</p>
      )}
    </div>
  );
}
