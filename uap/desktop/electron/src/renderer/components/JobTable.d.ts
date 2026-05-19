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
export declare function JobTable({ jobs, isLoading, isOffline, onJobClick, }: JobTableProps): import("react/jsx-runtime").JSX.Element;
export {};
//# sourceMappingURL=JobTable.d.ts.map