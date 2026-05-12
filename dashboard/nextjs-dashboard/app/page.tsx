import { fetchAgents, fetchKpi, fetchTokens, fetchLokiLogs } from "@/lib/data-source";
import { Dashboard } from "@/components/dashboard-client";

// This is a Server Component — it fetches data at request time and passes
// it as initial props to the Client Component which then subscribes to SSE.
export default async function Page() {
    const agents = await fetchAgents();
    const kpi = await fetchKpi(agents);
    const tokens = await fetchTokens("vortex");
    const logs = await fetchLokiLogs("Vortex-MCP", 20);

    return (
        <Dashboard
            initialData={{ agents, kpi, tokens, logs }}
        />
    );
}
