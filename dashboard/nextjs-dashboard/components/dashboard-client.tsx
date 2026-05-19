"use client";

import { useEffect, useRef, useState } from "react";
import type { Agent, KpiData, LogEntry, MetricPoint } from "@/lib/types";
import { AgentGrid } from "@/components/agent-grid";
import { LogViewer } from "@/components/log-viewer";
import { MetricsChart } from "@/components/metrics-chart";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Activity, Bot, RefreshCw, Zap } from "lucide-react";

interface InitialData {
    agents: Agent[];
    kpi: KpiData;
    tokens: MetricPoint[];
    logs: LogEntry[];
}

interface DashboardProps {
    initialData: InitialData;
}

export function Dashboard({ initialData }: DashboardProps) {
    const [agents, setAgents] = useState<Agent[]>(initialData.agents);
    const [kpi, setKpi] = useState<KpiData>(initialData.kpi);
    const [tokens, setTokens] = useState<MetricPoint[]>(initialData.tokens);
    const [logs, setLogs] = useState<LogEntry[]>(initialData.logs);
    const [live, setLive] = useState(false);
    const [lastSeen, setLastSeen] = useState<Date | null>(null);
    const esRef = useRef<EventSource | null>(null);

    useEffect(() => {
        const es = new EventSource("/api/stream");
        esRef.current = es;

        es.addEventListener("agents", e => {
            setAgents(JSON.parse(e.data));
            setLive(true);
            setLastSeen(new Date());
        });
        es.addEventListener("kpi", e => setKpi(JSON.parse(e.data)));
        es.addEventListener("tokens", e => setTokens(JSON.parse(e.data)));
        es.addEventListener("logs", e => {
            const fresh: LogEntry[] = JSON.parse(e.data);
            setLogs(prev => [...fresh, ...prev].slice(0, 60));
        });
        es.addEventListener("error", () => setLive(false));
        es.onerror = () => setLive(false);

        return () => es.close();
    }, []);

    return (
        <main className="p-4 md:p-6 space-y-6 max-w-[1800px] mx-auto">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <Bot className="w-6 h-6 text-primary" />
                    <div>
                        <h1 className="text-xl font-bold leading-none">ADRION 369</h1>
                        <p className="text-xs text-muted-foreground">AI Agent Monitoring Dashboard</p>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <Badge variant={live ? "running" : "unknown"} className="gap-1">
                        <span className={`w-1.5 h-1.5 rounded-full ${live ? "bg-emerald-500 animate-pulse" : "bg-slate-400"}`} />
                        {live ? "LIVE" : "OFFLINE"}
                    </Badge>
                    {lastSeen && (
                        <span className="text-xs text-muted-foreground hidden sm:block">
                            {lastSeen.toLocaleTimeString("pl-PL")}
                        </span>
                    )}
                </div>
            </div>

            {/* KPI row */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <KpiCard
                    icon={<Activity className="w-4 h-4 text-emerald-400" />}
                    label="Running Agents"
                    value={`${kpi.runningAgents} / ${kpi.totalAgents}`}
                />
                <KpiCard
                    icon={<Zap className="w-4 h-4 text-amber-400" />}
                    label="Total Tasks"
                    value={kpi.totalTasks.toLocaleString()}
                />
                <KpiCard
                    icon={<RefreshCw className="w-4 h-4 text-blue-400" />}
                    label="RPS"
                    value={kpi.rps != null ? kpi.rps.toFixed(1) : "—"}
                />
                <KpiCard
                    icon={<Activity className="w-4 h-4 text-red-400" />}
                    label="Error Rate"
                    value={`${kpi.errorRate.toFixed(1)}%`}
                />
            </div>

            {/* Agent cards */}
            <AgentGrid agents={agents} />

            {/* Charts + Logs */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <MetricsChart title="Token Usage — Vortex-MCP" data={tokens} unit=" tok" color="#6366f1" />
                <LogViewer logs={logs} title="Live Logs — Vortex-MCP" />
            </div>
        </main>
    );
}

function KpiCard({
    icon,
    label,
    value,
}: {
    icon: React.ReactNode;
    label: string;
    value: string;
}) {
    return (
        <Card>
            <CardHeader className="pb-1 pt-4">
                <div className="flex items-center gap-2">
                    {icon}
                    <CardTitle className="text-xs font-medium text-muted-foreground">{label}</CardTitle>
                </div>
            </CardHeader>
            <CardContent>
                <p className="text-2xl font-bold">{value}</p>
            </CardContent>
        </Card>
    );
}
