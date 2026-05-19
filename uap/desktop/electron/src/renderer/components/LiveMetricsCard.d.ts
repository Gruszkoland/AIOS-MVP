interface MetricProps {
    title: string;
    value: string | number;
    unit?: string;
    trend?: "up" | "down" | "neutral";
    icon?: string;
    color?: "green" | "blue" | "red" | "yellow" | "purple";
}
export declare function MetricCard({ title, value, unit, trend, icon, color, }: MetricProps): import("react/jsx-runtime").JSX.Element;
interface LiveMetricsGridProps {
    metrics: MetricProps[];
    isLoading?: boolean;
    isOffline?: boolean;
}
export declare function LiveMetricsGrid({ metrics, isLoading, isOffline, }: LiveMetricsGridProps): import("react/jsx-runtime").JSX.Element;
interface HealthStatusProps {
    backendHealth: "healthy" | "degraded" | "offline";
    lastUpdate: Date | null;
    errorMessage?: string;
}
export declare function HealthStatus({ backendHealth, lastUpdate, errorMessage, }: HealthStatusProps): import("react/jsx-runtime").JSX.Element;
export {};
//# sourceMappingURL=LiveMetricsCard.d.ts.map