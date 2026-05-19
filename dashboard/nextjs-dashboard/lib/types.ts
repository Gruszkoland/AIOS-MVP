/** Centralne typy danych dla ADRION 369 dashboard */

export type AgentStatus = "running" | "idle" | "error" | "unknown";

export interface Agent {
    name: string;
    status: AgentStatus;
    model: string;
    port: number;
    tasks: number;
    errors: number;
    latencyMs?: number;
}

export interface LogEntry {
    time: string;
    level: "INFO" | "WARN" | "ERROR";
    msg: string;
    agent?: string;
}

export interface MetricPoint {
    ts: string;   // ISO timestamp
    value: number;
}

export interface KpiData {
    totalTasks: number;
    runningAgents: number;
    totalAgents: number;
    errorRate: number;
    rps: number | null;
}

/** Kształt zdarzenia SSE wysyłanego przez /api/stream */
export type StreamEvent =
    | { type: "agents"; payload: Agent[] }
    | { type: "kpi"; payload: KpiData }
    | { type: "log"; payload: LogEntry }
    | { type: "ping" };
