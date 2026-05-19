"use client";

import type { Agent } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, AlertCircle, Bot, Clock } from "lucide-react";

interface AgentCardProps {
    agent: Agent;
}

function AgentCard({ agent }: AgentCardProps) {
    const variant = (
        agent.status === "running" ? "running" :
            agent.status === "idle" ? "idle" :
                agent.status === "error" ? "error" : "unknown"
    ) as "running" | "idle" | "error" | "unknown";

    return (
        <Card className="relative overflow-hidden transition-all hover:shadow-md hover:-translate-y-0.5">
            {/* Accent bar */}
            <div className={`absolute inset-x-0 top-0 h-1 ${agent.status === "running" ? "bg-emerald-500" :
                    agent.status === "idle" ? "bg-amber-400" :
                        agent.status === "error" ? "bg-red-500" : "bg-slate-400"
                }`} />
            <CardHeader className="pb-2 pt-4">
                <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-medium">{agent.name}</CardTitle>
                    <Badge variant={variant} className="capitalize">{agent.status}</Badge>
                </div>
                <p className="text-xs text-muted-foreground">{agent.model}</p>
            </CardHeader>
            <CardContent>
                <div className="grid grid-cols-3 gap-2 text-center">
                    <Stat icon={<Activity className="w-3.5 h-3.5 text-emerald-500" />} value={agent.tasks} label="Tasks" />
                    <Stat icon={<AlertCircle className="w-3.5 h-3.5 text-red-400" />} value={agent.errors} label="Errors" />
                    <Stat
                        icon={<Clock className="w-3.5 h-3.5 text-blue-400" />}
                        value={agent.latencyMs != null ? `${agent.latencyMs}ms` : "—"}
                        label="p95"
                    />
                </div>
            </CardContent>
        </Card>
    );
}

function Stat({ icon, value, label }: { icon: React.ReactNode; value: string | number; label: string }) {
    return (
        <div className="flex flex-col items-center gap-0.5">
            {icon}
            <span className="text-base font-semibold">{value}</span>
            <span className="text-[10px] text-muted-foreground">{label}</span>
        </div>
    );
}

interface AgentGridProps {
    agents: Agent[];
}

export function AgentGrid({ agents }: AgentGridProps) {
    return (
        <section>
            <div className="flex items-center gap-2 mb-3">
                <Bot className="w-4 h-4 text-primary" />
                <h2 className="font-semibold text-sm">Agent Status</h2>
                <span className="text-xs text-muted-foreground ml-auto">{agents.length} agents</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-5 gap-4">
                {agents.map(a => <AgentCard key={a.name} agent={a} />)}
            </div>
        </section>
    );
}
