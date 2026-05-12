/**
 * Warstwwa dostępu do danych.
 * Wszystkie funkcje działają po stronie serwera (Next.js App Router).
 * Przy błędzie połączenia zwracają dane demo.
 */

import type { Agent, KpiData, LogEntry, MetricPoint } from "./types";

const PROMETHEUS_URL = process.env.PROMETHEUS_URL ?? "http://localhost:9090";
const LOKI_URL = process.env.LOKI_URL ?? "http://localhost:3100";
const _TIMEOUT_MS = 3_000;

const MCP_REGISTRY: Record<string, { port: number; model: string }> = {
    "Vortex-MCP": { port: 9001, model: "GPT-4o" },
    "Guardian-MCP": { port: 9002, model: "Claude-3.7" },
    "Oracle-MCP": { port: 9003, model: "Mistral-L" },
    "Genesis-MCP": { port: 9004, model: "GPT-4o-mini" },
    "Healer-MCP": { port: 9005, model: "Llama-3.3" },
};

// ── Helpers ──────────────────────────────────────────────────────────────────

async function promQL(query: string): Promise<{ metric: Record<string, string>; value: [number, string] }[]> {
    try {
        const res = await fetch(
            `${PROMETHEUS_URL}/api/v1/query?query=${encodeURIComponent(query)}`,
            { signal: AbortSignal.timeout(_TIMEOUT_MS), cache: "no-store" },
        );
        const json = await res.json();
        if (json.status === "success") return json.data.result ?? [];
    } catch { /* ignore */ }
    return [];
}

async function promRange(query: string, minutes = 20): Promise<MetricPoint[]> {
    const end = new Date();
    const start = new Date(end.getTime() - minutes * 60_000);
    try {
        const res = await fetch(
            `${PROMETHEUS_URL}/api/v1/query_range` +
            `?query=${encodeURIComponent(query)}` +
            `&start=${start.toISOString()}&end=${end.toISOString()}&step=60s`,
            { signal: AbortSignal.timeout(_TIMEOUT_MS), cache: "no-store" },
        );
        const json = await res.json();
        const result = json?.data?.result ?? [];
        if (result.length > 0) {
            return (result[0].values as [number, string][]).map(([ts, val]) => ({
                ts: new Date(ts * 1000).toISOString(),
                value: parseFloat(val),
            }));
        }
    } catch { /* ignore */ }
    return _demoRange(minutes);
}

async function mcpStatus(name: string, port: number): Promise<"running" | "idle" | "error" | "unknown"> {
    try {
        const res = await fetch(`http://localhost:${port}/health`, {
            signal: AbortSignal.timeout(2_000),
            cache: "no-store",
        });
        if (res.ok) {
            const body = await res.json().catch(() => ({}));
            return (body.status as "running" | "idle") ?? "running";
        }
        return "error";
    } catch {
        return "unknown";
    }
}

// ── Public API ────────────────────────────────────────────────────────────────

export async function fetchAgents(): Promise<Agent[]> {
    return Promise.all(
        Object.entries(MCP_REGISTRY).map(async ([name, meta], idx) => {
            // Prometheus: zadania agenta
            const tasksRes = await promQL(
                `sum(increase(agent_tasks_total{agent="${name.toLowerCase().replace(/-mcp$/, "")}"}[24h]))`,
            );
            const errRes = await promQL(
                `sum(increase(agent_errors_total{agent="${name.toLowerCase().replace(/-mcp$/, "")}"}[24h]))`,
            );
            const latRes = await promQL(
                `histogram_quantile(0.95, rate(agent_request_duration_seconds_bucket{agent="${name}"}[5m]))`,
            );

            const tasks = tasksRes.length ? Math.round(parseFloat(tasksRes[0].value[1])) : _demoInt(idx, 40, 250);
            const errors = errRes.length ? Math.round(parseFloat(errRes[0].value[1])) : _demoInt(idx, 0, 8);
            const latMs = latRes.length ? Math.round(parseFloat(latRes[0].value[1]) * 1000) : undefined;
            const status = await mcpStatus(name, meta.port);

            return { name, status, model: meta.model, port: meta.port, tasks, errors, latencyMs: latMs };
        }),
    );
}

export async function fetchKpi(agents: Agent[]): Promise<KpiData> {
    const rpsRes = await promQL("sum(rate(http_requests_total[1m]))");
    const rps = rpsRes.length ? Math.round(parseFloat(rpsRes[0].value[1]) * 100) / 100 : null;

    const totalTasks = agents.reduce((s, a) => s + a.tasks, 0);
    const totalErrors = agents.reduce((s, a) => s + a.errors, 0);
    const runningAgents = agents.filter(a => a.status === "running").length;
    const errorRate = Math.round(totalErrors / Math.max(totalTasks, 1) * 10000) / 100;

    return { totalTasks, runningAgents, totalAgents: agents.length, errorRate, rps };
}

export async function fetchTokens(agentName: string): Promise<MetricPoint[]> {
    const label = agentName.toLowerCase().replace(/-mcp$/, "").replace(/-/g, "_");
    return promRange(`sum(increase(llm_tokens_total{agent="${label}"}[1m]))`);
}

export async function fetchLokiLogs(agentName: string, limit = 20): Promise<LogEntry[]> {
    const label = agentName.toLowerCase().replace(/ /g, "_");
    const end = Date.now();
    const start = end - 10 * 60_000;
    try {
        const res = await fetch(
            `${LOKI_URL}/loki/api/v1/query_range` +
            `?query=${encodeURIComponent(`{app=~".*${label}.*"}`)}&start=${start * 1e6}&end=${end * 1e6}&limit=${limit}&direction=backward`,
            { signal: AbortSignal.timeout(_TIMEOUT_MS), cache: "no-store" },
        );
        const json = await res.json();
        const streams: { values: [string, string][] }[] = json?.data?.result ?? [];
        const entries: LogEntry[] = [];
        for (const s of streams) {
            for (const [tsNs, line] of s.values) {
                const t = new Date(parseInt(tsNs) / 1e6);
                const level = /error/i.test(line) ? "ERROR" : /warn/i.test(line) ? "WARN" : "INFO";
                entries.push({ time: t.toTimeString().slice(0, 8), level, msg: line.slice(0, 130), agent: agentName });
            }
        }
        if (entries.length) return entries;
    } catch { /* fallback */ }
    return _demoLogs(agentName, limit);
}

// ── Demo data helpers ─────────────────────────────────────────────────────────

function _demoInt(seed: number, min: number, max: number): number {
    // deterministic-ish per agent index
    return min + ((seed * 73 + 17) % (max - min));
}

function _demoRange(minutes: number): MetricPoint[] {
    let v = 1000;
    return Array.from({ length: minutes }, (_, i) => {
        v = Math.max(0, v + (Math.random() - 0.48) * 120);
        return {
            ts: new Date(Date.now() - (minutes - i) * 60_000).toISOString(),
            value: Math.round(v),
        };
    });
}

function _demoLogs(agentName: string, count: number): LogEntry[] {
    const MSGS = [
        "Task completed successfully",
        "Waiting for tool response",
        "Retrying API call (attempt 2/3)",
        "Memory context pruned",
        "Received new task from orchestrator",
        "Tool call: web_search",
        "Latency spike detected (2.4 s)",
        "Stream closed unexpectedly",
    ];
    const LEVELS = ["INFO", "INFO", "INFO", "WARN", "ERROR"] as const;
    return Array.from({ length: count }, (_, i) => {
        const t = new Date(Date.now() - i * 18_000);
        return {
            time: t.toTimeString().slice(0, 8),
            level: LEVELS[i % LEVELS.length],
            msg: MSGS[i % MSGS.length],
            agent: agentName,
        };
    });
}
