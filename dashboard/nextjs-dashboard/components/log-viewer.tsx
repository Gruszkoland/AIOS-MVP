"use client";

import type { LogEntry } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollText } from "lucide-react";

interface LogViewerProps {
    logs: LogEntry[];
    title?: string;
}

const LEVEL_CLASS = {
    INFO: "text-blue-400",
    WARN: "text-amber-400",
    ERROR: "text-red-400",
} as const;

export function LogViewer({ logs, title = "Recent Logs" }: LogViewerProps) {
    return (
        <Card>
            <CardHeader className="pb-2">
                <div className="flex items-center gap-2">
                    <ScrollText className="w-4 h-4 text-primary" />
                    <CardTitle className="text-sm">{title}</CardTitle>
                </div>
            </CardHeader>
            <CardContent>
                <div className="space-y-1 max-h-64 overflow-y-auto font-mono text-xs">
                    {logs.length === 0 && (
                        <p className="text-muted-foreground italic">Brak logów…</p>
                    )}
                    {logs.map((log, i) => (
                        <div key={i} className="flex gap-2 items-start">
                            <span className="text-muted-foreground shrink-0 w-[52px]">{log.time}</span>
                            <span className={`shrink-0 w-10 font-semibold ${LEVEL_CLASS[log.level]}`}>
                                {log.level}
                            </span>
                            {log.agent && (
                                <span className="text-purple-400 shrink-0 max-w-[100px] truncate">{log.agent}</span>
                            )}
                            <span className="text-foreground/80 break-all">{log.msg}</span>
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    );
}
