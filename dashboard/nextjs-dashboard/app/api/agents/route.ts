import { fetchAgents, fetchKpi, fetchTokens, fetchLokiLogs } from "@/lib/data-source";
import { NextResponse } from "next/server";

// Force dynamic (no caching at route level)
export const dynamic = "force-dynamic";

export async function GET() {
    try {
        const agents = await fetchAgents();
        const kpi = await fetchKpi(agents);
        const tokens = await fetchTokens("vortex");
        const logs = await fetchLokiLogs("Vortex-MCP", 20);

        return NextResponse.json({ agents, kpi, tokens, logs });
    } catch (err) {
        return NextResponse.json({ error: String(err) }, { status: 500 });
    }
}
