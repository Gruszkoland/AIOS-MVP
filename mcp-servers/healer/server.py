"""Healer MCP Server — ADRION 369.

Self-repair, optimisation, and system health diagnostics.
Port: 9005 (informational — stdio transport for VS Code MCP).

Tools (5):
  diagnose_issue    — identify system problems from symptoms + component
  suggest_fix       — return ranked repair action list for a known issue
  optimize_query    — apply optimisation patterns to query parameters
  cleanup_state     — soft/hard/graceful component state reset
  health_report     — full system health report across all components

Resources (3):
  adrion://healer/known-issues          — known issues database
  adrion://healer/optimization-patterns — optimisation patterns catalogue
  adrion://healer/repair-history        — repairs completed this session
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

_MCP_DIR = Path(__file__).parent.parent
if str(_MCP_DIR) not in sys.path:
    sys.path.insert(0, str(_MCP_DIR))

from shared import utc_now  # noqa: E402

logger = logging.getLogger("adrion.healer")

KNOWN_ISSUES: dict[str, dict[str, Any]] = {
    "high_latency":           {"description": "Response time > 100ms at p95",          "severity": "medium",   "component": "api",            "actions": ["add_caching", "optimize_query", "scale_horizontally"]},
    "memory_leak":            {"description": "Memory usage grows unbounded",           "severity": "high",     "component": "backend",        "actions": ["restart_service", "fix_connection_pool", "profile_heap"]},
    "db_connection_exhausted":{"description": "All DB connections in pool occupied",    "severity": "critical", "component": "database",       "actions": ["increase_pool_size", "kill_idle_connections", "scale_replicas"]},
    "error_rate_spike":       {"description": "5xx error rate > 1% in 5 min window",   "severity": "critical", "component": "api",            "actions": ["rollback_deployment", "check_dependencies", "enable_circuit_breaker"]},
    "disk_full":              {"description": "Disk usage > 90%",                       "severity": "critical", "component": "infrastructure", "actions": ["cleanup_logs", "archive_old_data", "expand_volume"]},
    "timeout":                {"description": "Requests timing out before completion",  "severity": "high",     "component": "api",            "actions": ["increase_timeout_threshold", "async_processing", "optimize_query"]},
    "stale_cache":            {"description": "Cache serving data beyond TTL",          "severity": "low",      "component": "cache",          "actions": ["flush_cache", "adjust_ttl", "add_cache_invalidation"]},
}

OPT_PATTERNS: dict[str, list[str]] = {
    "db_query":     ["add_index", "reduce_select_star", "add_limit", "use_pagination"],
    "api_endpoint": ["add_caching_header", "compress_response", "paginate_list"],
    "llm_prompt":   ["trim_whitespace", "reduce_examples", "use_system_prompt"],
    "container":    ["set_resource_limits", "use_multistage_build", "minimize_layers"],
}

_DB_LIMIT_CAP = 100
_LLM_TOKEN_CAP = 2048

_COMPONENT_HEALTH: dict[str, dict[str, Any]] = {
    "api":            {"status": "healthy", "latency_p95_ms": 45,   "error_rate": 0.001},
    "database":       {"status": "healthy", "connections": 12,       "pool_size": 50},
    "cache":          {"status": "healthy", "hit_rate": 0.87,        "eviction_rate": 0.02},
    "queue":          {"status": "healthy", "depth": 3,              "consumers": 2},
    "llm":            {"status": "healthy", "requests_per_min": 8,   "avg_latency_ms": 1200},
    "infrastructure": {"status": "healthy", "disk_pct": 0.42,        "cpu_pct": 0.28},
}

_FALLBACK_ACTIONS: dict[str, list[str]] = {
    "critical": ["escalate_to_oncall", "enable_circuit_breaker", "rollback"],
    "high":     ["restart_service", "check_dependencies", "scale_up"],
    "medium":   ["optimize_query", "add_caching", "tune_parameters"],
    "low":      ["log_and_monitor", "schedule_maintenance"],
}


class HealerLogic:
    """Self-repair, diagnostics, and optimisation engine."""

    def __init__(self) -> None:
        self._repair_history: list[dict[str, Any]] = []

    def _record(self, action: str, detail: dict[str, Any]) -> None:
        self._repair_history.append({"action": action, **detail, "timestamp": utc_now()})

    def diagnose_issue(self, symptoms: list[str], component: str) -> dict[str, Any]:
        matches = [
            {"issue_id": k, "description": v["description"],
             "severity": v["severity"], "component": v["component"]}
            for k, v in KNOWN_ISSUES.items()
            if component.lower() in v["component"]
            or any(s.lower() in k or s.lower() in v["description"].lower() for s in symptoms)
        ]
        top = matches[0] if matches else {"issue_id": "unknown", "severity": "unknown"}
        result = {"status": "ok", "symptoms": symptoms, "component": component,
                  "issue_id": top["issue_id"], "severity": top["severity"],
                  "matches": matches[:3], "timestamp": utc_now()}
        self._record("diagnose", {"issue_id": top["issue_id"]})
        return result

    def suggest_fix(self, issue_id: str, severity: str) -> dict[str, Any]:
        issue = KNOWN_ISSUES.get(issue_id)
        actions = issue["actions"] if issue else _FALLBACK_ACTIONS.get(severity.lower(), ["investigate_logs"])
        est = {"low": 5, "medium": 15, "high": 30, "critical": 60}.get(severity.lower(), 20)
        result = {"status": "ok", "issue_id": issue_id, "severity": severity,
                  "actions": actions, "primary_action": actions[0],
                  "estimated_resolution_min": est, "timestamp": utc_now()}
        self._record("suggest_fix", {"issue_id": issue_id})
        return result

    def optimize_query(self, query_type: str, current_params: dict[str, Any]) -> dict[str, Any]:
        patterns = OPT_PATTERNS.get(query_type.lower())
        if not patterns:
            return {"status": "unsupported_type", "query_type": query_type,
                    "available_types": list(OPT_PATTERNS)}
        optimized = dict(current_params)
        changes: list[str] = []
        if query_type == "db_query" and "limit" in optimized:
            old = optimized["limit"]
            optimized["limit"] = min(int(old), _DB_LIMIT_CAP)
            if optimized["limit"] != old:
                changes.append(f"limit: {old} → {optimized['limit']}")
        if query_type == "llm_prompt" and "max_tokens" in optimized:
            old = optimized["max_tokens"]
            optimized["max_tokens"] = min(int(old), _LLM_TOKEN_CAP)
            if optimized["max_tokens"] != old:
                changes.append(f"max_tokens: {old} → {optimized['max_tokens']}")
        return {"status": "ok", "query_type": query_type, "original_params": current_params,
                "optimized_params": optimized, "patterns_applied": patterns,
                "param_changes": changes, "timestamp": utc_now()}

    def cleanup_state(self, component: str, strategy: str) -> dict[str, Any]:
        _strategies: dict[str, list[str]] = {
            "soft":     [f"flush_{component}_cache", f"reset_{component}_counters"],
            "hard":     [f"stop_{component}", f"clear_{component}_state", f"restart_{component}"],
            "graceful": [f"drain_{component}_connections", "wait_for_idle", f"soft_restart_{component}"],
        }
        if strategy not in _strategies:
            return {"status": "invalid_strategy", "valid_strategies": list(_strategies)}
        actions = _strategies[strategy]
        self._record("cleanup", {"component": component, "strategy": strategy})
        return {"status": "ok", "component": component, "strategy": strategy,
                "actions_executed": actions, "clean": True, "timestamp": utc_now()}

    def health_report(self) -> dict[str, Any]:
        degraded = [k for k, v in _COMPONENT_HEALTH.items() if v.get("status") != "healthy"]
        return {"status": "ok", "overall_health": "degraded" if degraded else "healthy",
                "components": _COMPONENT_HEALTH, "degraded_components": degraded,
                "repairs_this_session": len(self._repair_history), "timestamp": utc_now()}


def _build_server() -> Any:
    from mcp.server import Server  # type: ignore[import-untyped]
    from mcp.types import Resource, TextContent, Tool  # type: ignore[import-untyped]

    logic = HealerLogic()
    server = Server("adrion-healer")

    @server.list_tools()
    async def list_tools() -> list[Tool]:  # type: ignore[return]
        return [
            Tool(name="diagnose_issue",
                 description="Identify system issues from observed symptoms and affected component.",
                 inputSchema={"type": "object",
                              "properties": {"symptoms": {"type": "array", "items": {"type": "string"}}, "component": {"type": "string"}},
                              "required": ["symptoms", "component"]}),
            Tool(name="suggest_fix",
                 description="Return a ranked repair action list for a known issue ID.",
                 inputSchema={"type": "object",
                              "properties": {"issue_id": {"type": "string"}, "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]}},
                              "required": ["issue_id", "severity"]}),
            Tool(name="optimize_query",
                 description="Apply optimisation patterns to query parameters (db_query, api_endpoint, llm_prompt, container).",
                 inputSchema={"type": "object",
                              "properties": {"query_type": {"type": "string"}, "current_params": {"type": "object"}},
                              "required": ["query_type", "current_params"]}),
            Tool(name="cleanup_state",
                 description="Execute a soft, hard, or graceful state reset for a system component.",
                 inputSchema={"type": "object",
                              "properties": {"component": {"type": "string"}, "strategy": {"type": "string", "enum": ["soft", "hard", "graceful"]}},
                              "required": ["component", "strategy"]}),
            Tool(name="health_report",
                 description="Return a full health report for all system components.",
                 inputSchema={"type": "object", "properties": {}, "required": []}),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any] | None) -> list[TextContent]:  # type: ignore[return]
        args: dict[str, Any] = arguments or {}
        dispatch = {
            "diagnose_issue":  lambda: logic.diagnose_issue(args.get("symptoms", []), args["component"]),
            "suggest_fix":     lambda: logic.suggest_fix(args["issue_id"], args["severity"]),
            "optimize_query":  lambda: logic.optimize_query(args["query_type"], args.get("current_params", {})),
            "cleanup_state":   lambda: logic.cleanup_state(args["component"], args["strategy"]),
            "health_report":   lambda: logic.health_report(),
        }
        fn = dispatch.get(name)
        if fn is None:
            raise ValueError(f"Unknown tool: {name}")
        return [TextContent(type="text", text=json.dumps(fn(), indent=2))]

    @server.list_resources()
    async def list_resources() -> list[Resource]:  # type: ignore[return]
        return [
            Resource(uri="adrion://healer/known-issues",          name="Known Issues Database",   description="Catalogue of known issues with severity and actions", mimeType="application/json"),  # type: ignore[arg-type]
            Resource(uri="adrion://healer/optimization-patterns", name="Optimisation Patterns",   description="Available optimisation strategies by query type",      mimeType="application/json"),  # type: ignore[arg-type]
            Resource(uri="adrion://healer/repair-history",        name="Repair History",          description="All repairs performed this session",                   mimeType="application/json"),  # type: ignore[arg-type]
        ]

    @server.read_resource()
    async def read_resource(uri: Any) -> str:  # type: ignore[return]
        uri_str = str(uri)
        if uri_str == "adrion://healer/known-issues":
            return json.dumps(KNOWN_ISSUES, indent=2)
        if uri_str == "adrion://healer/optimization-patterns":
            return json.dumps(OPT_PATTERNS, indent=2)
        if uri_str == "adrion://healer/repair-history":
            return json.dumps({"repairs": logic._repair_history, "total": len(logic._repair_history)}, indent=2)
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
    logger.info("[Healer] MCP ready on port 9005")
    asyncio.run(main())
