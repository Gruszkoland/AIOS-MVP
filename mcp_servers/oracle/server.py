"""Oracle MCP Server — ADRION 369.

Predictions, confidence scoring, risk analysis, token estimation.
Port: 9003 (informational — stdio transport for VS Code MCP).

Tools (5):
  score_task_confidence — 0-100 confidence score for task completion
  predict_outcome       — probabilistic outcome prediction
  analyze_risks         — multi-factor risk assessment
  estimate_tokens       — LLM prompt token + cost estimation
  recommend_next_step   — next natural step recommendation

Resources (2):
  adrion://oracle/scoring-rules      — scoring algorithm documentation
  adrion://oracle/prediction-history — recent prediction records
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
from verify_mode import VerifyMode  # noqa: E402

logger = logging.getLogger("adrion.oracle")

_verify_mode = VerifyMode()

_SCORING_RULES: dict[str, Any] = {
    "base_score": 50, "tool_bonus_per_tool": 5, "tool_bonus_cap": 25,
    "prior_success_bonus": 15, "similar_completed_bonus": 10,
    "complexity_penalty": 15,
    "complex_keywords": ["refactor", "migrate", "redesign", "integrate", "rewrite", "overhaul"],
    "score_clamp": [0, 100],
}

_RISK_SCOPE: dict[str, int] = {
    "production": 9, "database": 8, "external": 7, "auth": 7,
    "secrets": 10, "global": 8, "cache": 3, "log": 2, "temp": 1,
}

_NEXT_STEPS: dict[str, list[str]] = {
    "testing":     ["run_linter", "add_coverage", "deploy_to_staging"],
    "development": ["write_tests", "run_ci", "code_review"],
    "deployment":  ["smoke_test", "monitor_metrics", "document_changes"],
    "analysis":    ["create_report", "review_with_team", "implement_fixes"],
    "maintenance": ["check_dependencies", "rotate_secrets", "backup_data"],
}

_OUTCOME_MAP: dict[str, tuple[str, float]] = {
    "deploy":   ("service_updated",   0.92), "delete":  ("data_removed",    0.88),
    "export":   ("file_generated",    0.95), "refactor":("code_improved",   0.78),
    "analyze":  ("report_generated",  0.97),
}

_COST_PER_M: dict[str, float] = {
    "gpt-4": 30.0, "gpt-4o": 10.0, "gpt-4o-mini": 0.6,
    "claude": 15.0, "claude-sonnet": 3.0, "llama": 0.3,
}


class OracleLogic:
    """Predictions, scoring, and recommendations engine."""

    def __init__(self) -> None:
        self._history: list[dict[str, Any]] = []

    def _log(self, r: dict[str, Any]) -> dict[str, Any]:
        self._history.append(r)
        if len(self._history) > 200:
            self._history.pop(0)
        return r

    def score_task_confidence(self, task: str, available_tools: list[str], context: dict[str, Any]) -> dict[str, Any]:
        score = _SCORING_RULES["base_score"]
        score += min(len(available_tools) * _SCORING_RULES["tool_bonus_per_tool"], _SCORING_RULES["tool_bonus_cap"])
        if context.get("prior_success"):
            score += _SCORING_RULES["prior_success_bonus"]
        if context.get("similar_completed"):
            score += _SCORING_RULES["similar_completed_bonus"]
        if any(kw in task.lower() for kw in _SCORING_RULES["complex_keywords"]):
            score -= _SCORING_RULES["complexity_penalty"]
        confidence = max(0, min(100, score))
        band = "high" if confidence >= 75 else "medium" if confidence >= 50 else "low"
        return self._log({"status": "ok", "task": task, "confidence": confidence,
                          "confidence_band": band, "tool_count": len(available_tools), "timestamp": utc_now()})

    def predict_outcome(self, operation: str, parameters: dict[str, Any]) -> dict[str, Any]:
        base = max(0.5, 0.95 - len(parameters) * 0.03)
        outcome, prob_factor = _OUTCOME_MAP.get(operation.lower(), ("operation_completed", 0.85))
        return self._log({"status": "ok", "operation": operation, "outcome": outcome,
                          "success_probability": round(base * prob_factor, 2),
                          "note": "heuristic model", "timestamp": utc_now()})

    def analyze_risks(self, operation: str, scope: str, dependencies: list[str]) -> dict[str, Any]:
        s_risk = _RISK_SCOPE.get(scope.lower(), 4)
        d_risk = sum(_RISK_SCOPE.get(d.lower(), 2) for d in dependencies) // max(len(dependencies), 1)
        total = min(10, s_risk + d_risk)
        band = "critical" if total >= 8 else "high" if total >= 6 else "medium" if total >= 4 else "low"
        mitigations: dict[str, list[str]] = {
            "critical": ["abort_and_review", "require_backup", "escalate_to_guardian"],
            "high":     ["require_backup", "audit_log", "peer_review"],
            "medium":   ["audit_log", "test_in_staging"],
            "low":      ["standard_logging"],
        }
        return {"status": "ok", "operation": operation, "scope": scope, "dependencies": dependencies,
                "risk_score": total, "risk_band": band, "mitigations": mitigations[band], "timestamp": utc_now()}

    def estimate_tokens(self, prompt: str, model: str, max_output: int) -> dict[str, Any]:
        input_tokens = max(1, len(prompt) // 4)
        total = input_tokens + max_output
        model_lower = model.lower()
        rate = next((v for k, v in _COST_PER_M.items() if k in model_lower), 5.0)
        return {"status": "ok", "model": model, "estimated_input_tokens": input_tokens,
                "max_output_tokens": max_output, "estimated_total_tokens": total,
                "estimated_cost_usd": round(total * rate / 1_000_000, 6),
                "note": "1 token ≈ 4 chars", "timestamp": utc_now()}

    def recommend_next_step(self, current_state: str, goal: str, constraints: list[str]) -> dict[str, Any]:
        steps = _NEXT_STEPS.get(current_state.lower(), ["review_requirements", "plan_next_sprint"])
        filtered = [s for s in steps if not any(c.lower() in s for c in constraints)]
        rec = filtered[0] if filtered else steps[0]
        return {"status": "ok", "current_state": current_state, "goal": goal,
                "recommendation": rec, "alternatives": filtered[1:3],
                "constraints_applied": constraints, "timestamp": utc_now()}

    def verify_output(self, agent_id: str, output: dict[str, Any], task: str) -> dict[str, Any]:
        """Verify agent output safety via VerifyMode self-correction engine.

        Runs the full Devil's Advocate scoring pipeline: PII scan, required-field
        check, Guardian Law cross-reference, and agent-specific anti-pattern checks.

        Args:
            agent_id: ROPE agent code, e.g. "AIO-01".
            output:   Agent output dict to verify (pre-emission).
            task:     Short task description for Devil's Advocate context.

        Returns:
            dict with is_safe, risk_level, score, concerns, recommendations.
        """
        result = _verify_mode.verify_agent_output(agent_id, output)
        result["devil_advocate_prompt"] = _verify_mode.generate_devil_advocate_prompt(
            agent_id, task
        )
        result["guardian_laws_check"] = _verify_mode.check_against_guardian_laws(output)
        return result


def _build_server() -> Any:
    from mcp.server import Server  # type: ignore[import-untyped]
    from mcp.types import Resource, TextContent, Tool  # type: ignore[import-untyped]

    logic = OracleLogic()
    server = Server("adrion-oracle")

    @server.list_tools()
    async def list_tools() -> list[Tool]:  # type: ignore[return]
        return [
            Tool(name="score_task_confidence",
                 description="Score 0-100 confidence for task completion based on tools and context.",
                 inputSchema={"type": "object",
                              "properties": {"task": {"type": "string"}, "available_tools": {"type": "array", "items": {"type": "string"}}, "context": {"type": "object"}},
                              "required": ["task", "available_tools", "context"]}),
            Tool(name="predict_outcome",
                 description="Predict success probability and outcome label for an operation.",
                 inputSchema={"type": "object",
                              "properties": {"operation": {"type": "string"}, "parameters": {"type": "object"}},
                              "required": ["operation", "parameters"]}),
            Tool(name="analyze_risks",
                 description="Multi-factor risk scoring (scope × dependencies).",
                 inputSchema={"type": "object",
                              "properties": {"operation": {"type": "string"}, "scope": {"type": "string"}, "dependencies": {"type": "array", "items": {"type": "string"}}},
                              "required": ["operation", "scope", "dependencies"]}),
            Tool(name="estimate_tokens",
                 description="Estimate LLM token usage and approximate cost without an API call.",
                 inputSchema={"type": "object",
                              "properties": {"prompt": {"type": "string"}, "model": {"type": "string"}, "max_output": {"type": "integer", "minimum": 1}},
                              "required": ["prompt", "model", "max_output"]}),
            Tool(name="recommend_next_step",
                 description="Recommend the next action toward a goal from the current workflow state.",
                 inputSchema={"type": "object",
                              "properties": {"current_state": {"type": "string"}, "goal": {"type": "string"}, "constraints": {"type": "array", "items": {"type": "string"}}},
                              "required": ["current_state", "goal", "constraints"]}),
            Tool(name="verify_output",
                 description=(
                     "Verify a ROPE agent's output dict before emission. Runs Devil's Advocate "
                     "scoring: PII scan, required-field check, Guardian Law cross-reference, and "
                     "agent-specific anti-pattern detection. Returns is_safe, risk_level (LOW/"
                     "MEDIUM/HIGH/CRITICAL), concerns, recommendations, and a devil_advocate_prompt."
                 ),
                 inputSchema={"type": "object",
                              "properties": {
                                  "agent_id": {"type": "string",
                                               "description": "ROPE agent code, e.g. 'AIO-01'"},
                                  "output":   {"type": "object",
                                               "description": "Agent output dict to verify (pre-emission)"},
                                  "task":     {"type": "string",
                                               "description": "Short task description for Devil's Advocate context",
                                               "default": ""},
                              },
                              "required": ["agent_id", "output"]}),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any] | None) -> list[TextContent]:  # type: ignore[return]
        args: dict[str, Any] = arguments or {}
        dispatch = {
            "score_task_confidence": lambda: logic.score_task_confidence(args["task"], args.get("available_tools", []), args.get("context", {})),
            "predict_outcome":       lambda: logic.predict_outcome(args["operation"], args.get("parameters", {})),
            "analyze_risks":         lambda: logic.analyze_risks(args["operation"], args["scope"], args.get("dependencies", [])),
            "estimate_tokens":       lambda: logic.estimate_tokens(args["prompt"], args["model"], int(args["max_output"])),
            "recommend_next_step":   lambda: logic.recommend_next_step(args["current_state"], args["goal"], args.get("constraints", [])),
            "verify_output":         lambda: logic.verify_output(args["agent_id"], args.get("output", {}), args.get("task", "")),
        }
        fn = dispatch.get(name)
        if fn is None:
            raise ValueError(f"Unknown tool: {name}")
        return [TextContent(type="text", text=json.dumps(fn(), indent=2))]

    @server.list_resources()
    async def list_resources() -> list[Resource]:  # type: ignore[return]
        return [
            Resource(uri="adrion://oracle/scoring-rules",      name="Scoring Rules",      description="Confidence scoring algorithm parameters", mimeType="application/json"),  # type: ignore[arg-type]
            Resource(uri="adrion://oracle/prediction-history", name="Prediction History", description="Recent prediction records (this session)", mimeType="application/json"),  # type: ignore[arg-type]
        ]

    @server.read_resource()
    async def read_resource(uri: Any) -> str:  # type: ignore[return]
        uri_str = str(uri)
        if uri_str == "adrion://oracle/scoring-rules":
            return json.dumps(_SCORING_RULES, indent=2)
        if uri_str == "adrion://oracle/prediction-history":
            return json.dumps({"predictions": logic._history, "total": len(logic._history)}, indent=2)
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
    logger.info("[Oracle] MCP ready on port 9003")
    asyncio.run(main())
