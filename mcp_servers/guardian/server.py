"""Guardian MCP Server — ADRION 369.

Enforces all 9 Guardian Laws; compliance validation, consent, harm risk.
Port: 9002 (informational — stdio transport for VS Code MCP).

Tools (6):
  evaluate_laws           — score all 9 laws; return ALLOW/DENY with violations
  check_critical_violations — instant ALLOW/DENY for G7+G8 veto laws
  audit_decision          — persist a decision audit entry
  get_law_details         — metadata for a specific law (G1-G9)
  validate_consent        — G7 Privacy: data scope + requester consent check
  check_harm_risk         — G8 Nonmaleficence: operation impact assessment

Resources (3):
  adrion://guardian/laws          — canonical 9 laws JSON
  adrion://guardian/audit-log     — recent decision audit entries
  adrion://guardian/violations-log — recent violation events
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

from shared import (  # noqa: E402
    GUARDIAN_LAWS_BY_ID,
    evaluate_guardian_laws,
    load_guardian_laws_json,
    sha256_hex,
    utc_now,
)

logger = logging.getLogger("adrion.guardian")

_HARM_RISK_MAP: dict[str, dict[str, Any]] = {
    "critical": {"score": 10, "allow": False, "reason": "Critical impact — DENY unconditionally"},
    "high":     {"score":  7, "allow": False, "reason": "High impact — requires backup + audit"},
    "medium":   {"score":  4, "allow": True,  "reason": "Medium impact — proceed with caution"},
    "low":      {"score":  1, "allow": True,  "reason": "Low impact — proceed normally"},
}


# ---------------------------------------------------------------------------
# Business Logic
# ---------------------------------------------------------------------------
class GuardianLogic:
    """9 Guardian Laws enforcement engine."""

    def __init__(self) -> None:
        self._audit_log:     list[dict[str, Any]] = []
        self._violations_log: list[dict[str, Any]] = []

    # -- Tools ---------------------------------------------------------------

    def evaluate_laws(self, operation: str, context: dict[str, Any]) -> dict[str, Any]:
        """Evaluate all 9 Guardian Laws and return ALLOW/DENY verdict."""
        compliant, violations, score = evaluate_guardian_laws(operation, context)
        verdict = "ALLOW" if compliant else "DENY"
        entry: dict[str, Any] = {
            "status": "ok",
            "operation": operation,
            "verdict": verdict,
            "violations": violations,
            "weighted_score": score,
            "law_details": [GUARDIAN_LAWS_BY_ID[lid] for lid in violations if lid in GUARDIAN_LAWS_BY_ID],
            "timestamp": utc_now(),
        }
        if not compliant:
            self._violations_log.append({
                "operation": operation, "violations": violations,
                "score": score, "timestamp": utc_now(),
            })
        return entry

    def check_critical_violations(self, operation: str, context: dict[str, Any]) -> dict[str, Any]:
        """Quick check: does this operation trigger any CRITICAL (veto) law?"""
        compliant, violations, _ = evaluate_guardian_laws(operation, context)
        critical_hits = [v for v in violations if v in ("G7", "G8")]
        return {
            "status": "ok",
            "operation": operation,
            "allow": compliant,
            "critical_violations": critical_hits,
            "reason": (
                f"Vetoed by {', '.join(critical_hits)}" if critical_hits
                else "No critical violations"
            ),
            "timestamp": utc_now(),
        }

    def audit_decision(
        self, decision_id: str, operation: str, context: dict[str, Any], outcome: str
    ) -> dict[str, Any]:
        """Record a decision in the immutable audit trail."""
        payload = json.dumps(
            {"decision_id": decision_id, "operation": operation, "outcome": outcome},
            sort_keys=True,
        )
        audit_id = f"AUD-{sha256_hex(payload)[:8].upper()}"
        entry = {
            "audit_id": audit_id,
            "decision_id": decision_id,
            "operation": operation,
            "outcome": outcome,
            "context_keys": list(context.keys()),
            "timestamp": utc_now(),
        }
        self._audit_log.append(entry)
        return {"status": "ok", "audit_id": audit_id, "timestamp": entry["timestamp"]}

    def get_law_details(self, law_id: str) -> dict[str, Any]:
        """Return full metadata for a specific Guardian Law."""
        law_id_upper = law_id.upper()
        law = GUARDIAN_LAWS_BY_ID.get(law_id_upper)
        if not law:
            return {
                "status": "not_found",
                "law_id": law_id,
                "available_ids": list(GUARDIAN_LAWS_BY_ID.keys()),
            }
        return {**law, "status": "ok"}

    def validate_consent(self, data_type: str, scope: str, requester: str) -> dict[str, Any]:
        """G7 Privacy: verify data access is within local scope and consented."""
        is_local = scope in ("local", "workspace", "project")
        is_sensitive = data_type in ("user_email", "credentials", "pii", "private_key", "password")
        compliant = is_local or not is_sensitive
        return {
            "status": "ok",
            "data_type": data_type,
            "scope": scope,
            "requester": requester,
            "g7_compliant": compliant,
            "is_sensitive": is_sensitive,
            "verdict": "ALLOW" if compliant else "DENY — G7 Privacy violation",
            "timestamp": utc_now(),
        }

    def check_harm_risk(self, operation: str, impact_level: str) -> dict[str, Any]:
        """G8 Nonmaleficence: assess whether an operation crosses harm thresholds."""
        level_lower = impact_level.lower()
        risk_info = _HARM_RISK_MAP.get(level_lower, _HARM_RISK_MAP["medium"])
        return {
            "status": "ok",
            "operation": operation,
            "impact_level": level_lower,
            "risk_score": risk_info["score"],
            "allow": risk_info["allow"],
            "g8_reason": risk_info["reason"],
            "timestamp": utc_now(),
        }


# ---------------------------------------------------------------------------
# MCP Server Wiring
# ---------------------------------------------------------------------------
def _build_server() -> Any:
    from mcp.server import Server  # type: ignore[import-untyped]
    from mcp.types import Resource, TextContent, Tool  # type: ignore[import-untyped]

    logic = GuardianLogic()
    server = Server("adrion-guardian")

    @server.list_tools()
    async def list_tools() -> list[Tool]:  # type: ignore[return]
        return [
            Tool(name="evaluate_laws",
                 description="Evaluate all 9 Guardian Laws for an operation + context. Returns ALLOW/DENY verdict.",
                 inputSchema={"type": "object",
                              "properties": {
                                  "operation": {"type": "string", "description": "Operation name (e.g. deploy, delete, export)"},
                                  "context":   {"type": "object", "description": "Context dict (reason, scope, audit_logged, backup_exists...)"},
                              },
                              "required": ["operation", "context"]}),
            Tool(name="check_critical_violations",
                 description="Instant check for G7 (Privacy) and G8 (Nonmaleficence) veto violations.",
                 inputSchema={"type": "object",
                              "properties": {
                                  "operation": {"type": "string"},
                                  "context":   {"type": "object"},
                              },
                              "required": ["operation", "context"]}),
            Tool(name="audit_decision",
                 description="Record a decision event in the immutable Guardian audit trail.",
                 inputSchema={"type": "object",
                              "properties": {
                                  "decision_id": {"type": "string"},
                                  "operation":   {"type": "string"},
                                  "context":     {"type": "object"},
                                  "outcome":     {"type": "string", "enum": ["ALLOW", "DENY", "ESCALATE"]},
                              },
                              "required": ["decision_id", "operation", "context", "outcome"]}),
            Tool(name="get_law_details",
                 description="Return full metadata for a specific Guardian Law by ID (G1-G9).",
                 inputSchema={"type": "object",
                              "properties": {
                                  "law_id": {"type": "string", "description": "e.g. G7"},
                              },
                              "required": ["law_id"]}),
            Tool(name="validate_consent",
                 description="G7 Privacy: verify data access consent based on data type and scope.",
                 inputSchema={"type": "object",
                              "properties": {
                                  "data_type":  {"type": "string"},
                                  "scope":      {"type": "string"},
                                  "requester":  {"type": "string"},
                              },
                              "required": ["data_type", "scope", "requester"]}),
            Tool(name="check_harm_risk",
                 description="G8 Nonmaleficence: assess operation impact level (low/medium/high/critical).",
                 inputSchema={"type": "object",
                              "properties": {
                                  "operation":    {"type": "string"},
                                  "impact_level": {"type": "string",
                                                   "enum": ["low", "medium", "high", "critical"]},
                              },
                              "required": ["operation", "impact_level"]}),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any] | None) -> list[TextContent]:  # type: ignore[return]
        args: dict[str, Any] = arguments or {}
        if name == "evaluate_laws":
            result = logic.evaluate_laws(args["operation"], args.get("context", {}))
        elif name == "check_critical_violations":
            result = logic.check_critical_violations(args["operation"], args.get("context", {}))
        elif name == "audit_decision":
            result = logic.audit_decision(args["decision_id"], args["operation"],
                                          args.get("context", {}), args["outcome"])
        elif name == "get_law_details":
            result = logic.get_law_details(args["law_id"])
        elif name == "validate_consent":
            result = logic.validate_consent(args["data_type"], args["scope"], args["requester"])
        elif name == "check_harm_risk":
            result = logic.check_harm_risk(args["operation"], args["impact_level"])
        else:
            raise ValueError(f"Unknown tool: {name}")
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    @server.list_resources()
    async def list_resources() -> list[Resource]:  # type: ignore[return]
        return [
            Resource(uri="adrion://guardian/laws",           # type: ignore[arg-type]
                     name="Guardian Laws Canonical",
                     description="All 9 Guardian Laws with severity, veto flag, and description",
                     mimeType="application/json"),
            Resource(uri="adrion://guardian/audit-log",      # type: ignore[arg-type]
                     name="Decision Audit Log",
                     description="All recorded decision audit entries (this session)",
                     mimeType="application/json"),
            Resource(uri="adrion://guardian/violations-log", # type: ignore[arg-type]
                     name="Violations Log",
                     description="All law violations detected this session",
                     mimeType="application/json"),
        ]

    @server.read_resource()
    async def read_resource(uri: Any) -> str:  # type: ignore[return]
        uri_str = str(uri)
        if uri_str == "adrion://guardian/laws":
            return load_guardian_laws_json()
        if uri_str == "adrion://guardian/audit-log":
            return json.dumps({"entries": logic._audit_log, "total": len(logic._audit_log)}, indent=2)
        if uri_str == "adrion://guardian/violations-log":
            return json.dumps({"violations": logic._violations_log, "total": len(logic._violations_log)}, indent=2)
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
    logger.info("[Guardian] MCP ready on port 9002")
    asyncio.run(main())
