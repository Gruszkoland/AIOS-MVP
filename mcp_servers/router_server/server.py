"""Router MCP Server — ADRION 369.

Central gateway: discovery, capability mapping, semantic routing.
Port: 9000 (informational — stdio transport for VS Code MCP).

Tools (5):
  discover_agents     — list all agents + capabilities
  route_task          — semantic task-to-agent matching
  get_capabilities    — capability → agent domain map
  validate_tool_schema — MCP tool spec validator
  health_check        — router + downstream status

Resources (2):
  adrion://router/agents       — agent registry JSON
  adrion://router/capabilities — capability map JSON
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

# Ensure shared utilities are importable regardless of cwd
_MCP_DIR = Path(__file__).parent.parent
if str(_MCP_DIR) not in sys.path:
    sys.path.insert(0, str(_MCP_DIR))

from shared import AGENTS_REGISTRY, MCP_PORTS, TrustScore, utc_now  # noqa: E402
from gsr import GlobalStateRegister  # noqa: E402

logger = logging.getLogger("adrion.router")

_FALLBACK_AGENT = "07"  # OCA — orchestration/clarification


# ---------------------------------------------------------------------------
# Business Logic — pure Python, fully testable without the mcp SDK
# ---------------------------------------------------------------------------
class RouterLogic:
    """Core Router logic: discovery, routing, capability mapping."""

    def __init__(self) -> None:
        self._trust: dict[str, TrustScore] = {
            name: TrustScore(agent=name)
            for name in ("vortex", "guardian", "oracle", "genesis", "healer")
        }
        self._gsr: GlobalStateRegister = GlobalStateRegister()

    # -- Tools ---------------------------------------------------------------

    def discover_agents(self) -> dict[str, Any]:
        """Return full agent registry."""
        return {
            "status": "ok",
            "total": len(AGENTS_REGISTRY),
            "agents": AGENTS_REGISTRY,
            "timestamp": utc_now(),
        }

    def route_task(self, task: str, domain: str | None = None) -> dict[str, Any]:
        """Semantically match a task to the best agent using keyword overlap."""
        best_id: str = _FALLBACK_AGENT
        best_score: float = 0.0

        task_lower = task.lower()
        for agent_id, info in AGENTS_REGISTRY.items():
            agent_domain: str = info.get("domain", "")
            capabilities: list[str] = info.get("capabilities", [])

            # Exact domain hint match → top priority
            if domain and domain.lower() in agent_domain.lower():
                best_id = agent_id
                best_score = 1.0
                break

            # Keyword overlap across capabilities
            matched = sum(1 for cap in capabilities if cap in task_lower)
            cap_score = matched / max(len(capabilities), 1)
            if cap_score > best_score:
                best_score = cap_score
                best_id = agent_id

        info = AGENTS_REGISTRY.get(best_id, AGENTS_REGISTRY[_FALLBACK_AGENT])
        return {
            "status": "ok",
            "task": task,
            "agent_id": best_id,
            "agent_name": info["name"],
            "domain": info["domain"],
            "confidence": round(best_score, 3),
            "timestamp": utc_now(),
        }

    def get_capabilities(self) -> dict[str, Any]:
        """Return a flat capability → [agents] mapping."""
        cap_map: dict[str, list[dict[str, str]]] = {}
        for agent_id, info in AGENTS_REGISTRY.items():
            for cap in info.get("capabilities", []):
                cap_map.setdefault(cap, []).append(
                    {"agent_id": agent_id, "name": info["name"], "domain": info["domain"]}
                )
        return {
            "status": "ok",
            "capabilities": cap_map,
            "total_unique": len(cap_map),
            "timestamp": utc_now(),
        }

    def validate_tool_schema(self, tool_spec: dict[str, Any]) -> dict[str, Any]:
        """Validate an MCP Tool definition against required fields and schema structure."""
        required_fields = {"name", "description", "inputSchema"}
        missing = sorted(required_fields - set(tool_spec.keys()))
        schema = tool_spec.get("inputSchema", {})
        is_valid = (not missing) and schema.get("type") == "object"
        return {
            "status": "valid" if is_valid else "invalid",
            "tool_name": tool_spec.get("name"),
            "missing_fields": missing,
            "schema_has_type_object": schema.get("type") == "object",
            "schema_has_properties": "properties" in schema,
            "timestamp": utc_now(),
        }

    def get_gsr_status(self) -> dict[str, Any]:
        """Return the current Global State Register for all 9 ADRION agents."""
        state = self._gsr.get_all_agents()
        state["status"] = "ok"
        return state

    def update_gsr(
        self,
        agent_id: str,
        status: str,
        confidence: int,
        task_description: str | None = None,
    ) -> dict[str, Any]:
        """Update a single agent's status in the Global State Register."""
        result = self._gsr.update_agent_status(agent_id, status, confidence, task_description)
        if "error" in result:
            return {**result, "status": "error"}
        return {**result, "status": "ok"}

    def health_check(self) -> dict[str, Any]:
        """Return health of Router + all downstream MCP servers."""
        downstream = {
            name: {
                "port": MCP_PORTS[name],
                "trust_score": round(self._trust[name].score, 3),
                "blocked": self._trust[name].is_blocked,
            }
            for name in ("vortex", "guardian", "oracle", "genesis", "healer")
        }
        all_healthy = all(not v["blocked"] for v in downstream.values())
        return {
            "status": "ok" if all_healthy else "degraded",
            "server": "adrion-router",
            "port": MCP_PORTS["router"],
            "agents_registered": len(AGENTS_REGISTRY),
            "downstream": downstream,
            "timestamp": utc_now(),
        }


# ---------------------------------------------------------------------------
# MCP Server Wiring — requires mcp SDK at runtime
# ---------------------------------------------------------------------------
def _build_server() -> Any:
    """Construct the MCP Server with all tools and resources registered."""
    from mcp.server import Server  # type: ignore[import-untyped]
    from mcp.types import Resource, TextContent, Tool  # type: ignore[import-untyped]

    logic = RouterLogic()
    server = Server("adrion-router")

    @server.list_tools()
    async def list_tools() -> list[Tool]:  # type: ignore[return]
        return [
            Tool(name="discover_agents",
                 description="Return all registered ADRION agents with capabilities and domains.",
                 inputSchema={"type": "object", "properties": {}, "required": []}),
            Tool(name="route_task",
                 description="Semantically match a task description to the best available agent.",
                 inputSchema={"type": "object",
                              "properties": {
                                  "task":   {"type": "string", "description": "Task description text"},
                                  "domain": {"type": "string", "description": "Optional domain hint"},
                              },
                              "required": ["task"]}),
            Tool(name="get_capabilities",
                 description="Return the capability-to-agent domain mapping for the full registry.",
                 inputSchema={"type": "object", "properties": {}, "required": []}),
            Tool(name="validate_tool_schema",
                 description="Validate an MCP Tool spec against required fields and JSON Schema structure.",
                 inputSchema={"type": "object",
                              "properties": {
                                  "tool_spec": {"type": "object",
                                                "description": "MCP Tool object: {name, description, inputSchema}"},
                              },
                              "required": ["tool_spec"]}),
            Tool(name="health_check",
                 description="Return health status of Router and all downstream MCP servers.",
                 inputSchema={"type": "object", "properties": {}, "required": []}),
            Tool(name="get_gsr_status",
                 description="Return the current Global State Register (PROJECT_STATE) for all 9 ADRION agent personas.",
                 inputSchema={"type": "object", "properties": {}, "required": []}),
            Tool(name="update_gsr",
                 description="Update an agent's status in the Global State Register (self-reporting).",
                 inputSchema={"type": "object",
                              "properties": {
                                  "agent_id":         {"type": "string",
                                                       "description": "Canonical agent ID, e.g. 'MPG-01'"},
                                  "status":           {"type": "string",
                                                       "enum": ["idle", "active", "error"],
                                                       "description": "Agent execution status"},
                                  "confidence":       {"type": "integer", "minimum": 0, "maximum": 100,
                                                       "description": "Agent confidence score 0-100"},
                                  "task_description": {"type": "string",
                                                       "description": "Optional: current task description"},
                              },
                              "required": ["agent_id", "status", "confidence"]}),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any] | None) -> list[TextContent]:  # type: ignore[return]
        args: dict[str, Any] = arguments or {}
        if name == "discover_agents":
            result = logic.discover_agents()
        elif name == "route_task":
            result = logic.route_task(args["task"], args.get("domain"))
        elif name == "get_capabilities":
            result = logic.get_capabilities()
        elif name == "validate_tool_schema":
            result = logic.validate_tool_schema(args["tool_spec"])
        elif name == "health_check":
            result = logic.health_check()
        elif name == "get_gsr_status":
            result = logic.get_gsr_status()
        elif name == "update_gsr":
            result = logic.update_gsr(
                args["agent_id"],
                args["status"],
                int(args["confidence"]),
                args.get("task_description"),
            )
        else:
            raise ValueError(f"Unknown tool: {name}")
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    @server.list_resources()
    async def list_resources() -> list[Resource]:  # type: ignore[return]
        return [
            Resource(uri="adrion://router/agents",       # type: ignore[arg-type]
                     name="Agents Registry",
                     description="All ADRION agents with domains and capabilities",
                     mimeType="application/json"),
            Resource(uri="adrion://router/capabilities", # type: ignore[arg-type]
                     name="Capability Map",
                     description="Capability-to-agent domain mapping",
                     mimeType="application/json"),
        ]

    @server.read_resource()
    async def read_resource(uri: Any) -> str:  # type: ignore[return]
        uri_str = str(uri)
        if uri_str == "adrion://router/agents":
            return json.dumps(logic.discover_agents(), indent=2)
        if uri_str == "adrion://router/capabilities":
            return json.dumps(logic.get_capabilities(), indent=2)
        raise ValueError(f"Unknown resource URI: {uri_str}")

    return server


async def main() -> None:
    from mcp.server.stdio import stdio_server  # type: ignore[import-untyped]

    server = _build_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO, stream=sys.stderr,
                        format="%(asctime)s [%(name)s] %(levelname)s %(message)s")
    logger.info("[Router] MCP ready on port 9000")
    asyncio.run(main())
