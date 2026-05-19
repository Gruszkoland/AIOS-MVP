import { fetchAgents, fetchKpi, fetchTokens, fetchLokiLogs } from "@/lib/data-source";

export const dynamic = "force-dynamic";

const INTERVAL_MS = 15_000;

export async function GET() {
    const encoder = new TextEncoder();

    const stream = new ReadableStream({
        async start(controller) {
            const send = (event: string, data: unknown) => {
                controller.enqueue(
                    encoder.encode(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`),
                );
            };

            const tick = async () => {
                try {
                    const agents = await fetchAgents();
                    const kpi = await fetchKpi(agents);
                    const tokens = await fetchTokens("vortex");
                    const logs = await fetchLokiLogs("Vortex-MCP", 5);

                    send("agents", agents);
                    send("kpi", kpi);
                    send("tokens", tokens);
                    send("logs", logs);
                } catch {
                    send("error", { msg: "fetch_failed" });
                }
            };

            // Immediate first tick
            await tick();

            // Subsequent ticks
            const timer = setInterval(() => { void tick(); }, INTERVAL_MS);

            // Keepalive ping every 10 s to prevent proxy timeouts
            const ping = setInterval(() => {
                try { controller.enqueue(encoder.encode(": ping\n\n")); } catch { /* closed */ }
            }, 10_000);

            // Cleanup on close
            return () => {
                clearInterval(timer);
                clearInterval(ping);
            };
        },
    });

    return new Response(stream, {
        headers: {
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    });
}
