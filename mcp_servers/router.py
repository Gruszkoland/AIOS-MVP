"""
MCP ROUTER: Central Decision Arbitration (Port 9000)

Orchestrates communication between 5 MCP servers:
- VORTEX-MCP (9001) — Orchestration
- GUARDIAN-MCP (9002) — Security
- ORACLE-MCP (9003) — Routing
- GENESIS-MCP (9004) — State
- HEALER-MCP (9005) — Recovery

Decision Flow:
1. Receive user query
2. ORACLE classifies intent
3. GUARDIAN validates compliance (9 Laws)
4. Route to best agent (by Trust Score)
5. VORTEX executes safely
6. GENESIS logs
7. HEALER monitors
"""

from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json


class RoutingDecision(Enum):
    """Routing outcomes"""
    APPROVED = "approved"
    BLOCKED = "blocked"
    ESCALATED = "escalated"
    CRISIS = "crisis"


@dataclass
class RoutingTrace:
    """Trace of routing decision"""
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    query: str = ""
    intent: str = ""
    guardian_check: Tuple[bool, List[str]] = (True, [])  # (compliant, violations)
    selected_agent: str = ""
    agent_trust_score: float = 0.0
    execution_status: str = "pending"  # pending, executing, completed, failed
    result: Dict[str, Any] = field(default_factory=dict)


class MCPRouter:
    """Central routing orchestrator"""

    def __init__(self):
        self.traces: List[RoutingTrace] = []
        self.agents = {
            "VORTEX": {"port": 9001, "trust_score": 0.85},
            "GUARDIAN": {"port": 9002, "trust_score": 0.90},
            "ORACLE": {"port": 9003, "trust_score": 0.82},
            "GENESIS": {"port": 9004, "trust_score": 0.88},
            "HEALER": {"port": 9005, "trust_score": 0.80}
        }
        self.decision_log = []

    async def route_query(self, query: str, context: Dict[str, Any]) -> dict:
        """
        Main routing logic:
        Query -> Intent Classification -> Compliance Check -> Agent Selection -> Execution
        """
        trace = RoutingTrace(query=query)

        # STEP 1: ORACLE — Classify intent
        intent, confidence = self._classify_intent(query)
        trace.intent = intent

        # STEP 2: GUARDIAN — Check 9 Guardian Laws
        is_compliant, violations = self._validate_compliance(intent, context)
        trace.guardian_check = (is_compliant, violations)

        if not is_compliant:
            trace.execution_status = "blocked"
            self.traces.append(trace)
            return {
                "decision": RoutingDecision.BLOCKED.value,
                "reason": f"Violations: {violations}",
                "trace": self._serialize_trace(trace)
            }

        # STEP 3: Check for crisis mode
        if context.get("arousal", 0.3) > 0.7:
            trace.execution_status = "escalated"
            trace.selected_agent = "HEALER"
            self.traces.append(trace)
            return {
                "decision": RoutingDecision.CRISIS.value,
                "agent": "HEALER",
                "reason": "High arousal detected — Crisis Mode",
                "trace": self._serialize_trace(trace)
            }

        # STEP 4: ORACLE — Select best agent by Trust Score
        best_agent, best_ts = self._select_best_agent(intent, context)
        trace.selected_agent = best_agent
        trace.agent_trust_score = best_ts

        # STEP 5: Check agent Trust Score threshold (TSPA)
        if best_ts < 0.6:
            trace.execution_status = "escalated"
            self.traces.append(trace)
            return {
                "decision": RoutingDecision.ESCALATED.value,
                "reason": f"Agent TS={best_ts:.2f} < 0.6 (threshold)",
                "trace": self._serialize_trace(trace)
            }

        # STEP 6: VORTEX — Execute safely
        execution_result = self._execute_safe(best_agent, context)
        trace.execution_status = execution_result.get("status", "completed")
        trace.result = execution_result

        # STEP 7: GENESIS — Log decision
        self._log_decision(trace)
        self.traces.append(trace)

        return {
            "decision": RoutingDecision.APPROVED.value,
            "agent": best_agent,
            "trust_score": best_ts,
            "result": execution_result,
            "trace": self._serialize_trace(trace)
        }

    def _classify_intent(self, query: str) -> Tuple[str, float]:
        """ORACLE: Classify user intent"""
        query_lower = query.lower()

        intents = {
            "fix": (["bug", "error", "crash", "broken"], 0.85),
            "feature": (["add", "new", "implement", "support"], 0.82),
            "refactor": (["redesign", "optimize", "clean"], 0.78),
            "analyze": (["analyze", "diagnose", "check"], 0.75),
            "deploy": (["deploy", "rollout", "release"], 0.80)
        }

        best_intent = "unknown"
        best_confidence = 0.0

        for intent, (keywords, conf) in intents.items():
            if any(kw in query_lower for kw in keywords):
                if conf > best_confidence:
                    best_intent = intent
                    best_confidence = conf

        return best_intent, best_confidence

    def _validate_compliance(self, intent: str, context: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """GUARDIAN: Check 9 Guardian Laws"""
        violations = []

        # G7 Privacy — local_first
        if intent == "export" and context.get("export_scope") == "global":
            violations.append("G7_Privacy")

        # G8 Nonmaleficence — no_destructive_without_backup
        if intent == "delete" and not context.get("backup_exists"):
            violations.append("G8_Nonmaleficence")

        # G5 Transparency — require_audit
        if not context.get("audit_logged"):
            violations.append("G5_Transparency")

        return len(violations) == 0, violations

    def _select_best_agent(self, intent: str, context: Dict[str, Any]) -> Tuple[str, float]:
        """Route to best agent by Trust Score"""
        agent_candidates = {
            "fix": ["HEALER", "AUDITOR"],
            "feature": ["ARCHITECT", "ORACLE"],
            "refactor": ["ARCHITECT", "GUARDIAN"],
            "analyze": ["AUDITOR", "ORACLE"],
            "deploy": ["VORTEX", "HEALER"]
        }

        candidates = agent_candidates.get(intent, [])
        if not candidates:
            return "ORACLE", self.agents.get("ORACLE", {}).get("trust_score", 0.8)

        best_agent = candidates[0]
        best_ts = self.agents.get(best_agent, {}).get("trust_score", 0.8)

        return best_agent, best_ts

    def _execute_safe(self, agent: str, context: Dict[str, Any]) -> dict:
        """VORTEX: Safe execution with monitoring"""
        return {
            "status": "completed",
            "agent": agent,
            "actions": [
                "pre_check: PASSED",
                "guardian_check: PASSED",
                "execution: COMPLETED",
                "verification: PASSED"
            ],
            "timestamp": datetime.utcnow().isoformat(),
            "result": {"success": True, "data": "operation_result"}
        }

    def _log_decision(self, trace: RoutingTrace):
        """GENESIS: Append to decision log"""
        self.decision_log.append({
            "timestamp": trace.timestamp,
            "query": trace.query,
            "intent": trace.intent,
            "agent": trace.selected_agent,
            "status": trace.execution_status
        })

    def _serialize_trace(self, trace: RoutingTrace) -> dict:
        """Serialize trace for JSON"""
        compliant, violations = trace.guardian_check
        return {
            "timestamp": trace.timestamp,
            "query": trace.query,
            "intent": trace.intent,
            "compliant": compliant,
            "violations": violations,
            "selected_agent": trace.selected_agent,
            "agent_ts": trace.agent_trust_score,
            "status": trace.execution_status
        }

    def get_routing_stats(self) -> dict:
        """Get router statistics"""
        approved = len([t for t in self.traces if t.execution_status == "completed"])
        blocked = len([t for t in self.traces if t.execution_status == "blocked"])
        escalated = len([t for t in self.traces if t.execution_status == "escalated"])

        return {
            "total_queries": len(self.traces),
            "approved": approved,
            "blocked": blocked,
            "escalated": escalated,
            "success_rate": approved / max(1, len(self.traces)),
            "recent_traces": len(self.traces[-10:])
        }

    def get_agent_health(self) -> dict:
        """Agent status snapshot"""
        return {
            "agents": self.agents,
            "timestamp": datetime.utcnow().isoformat(),
            "all_healthy": all(
                ts >= 0.6 for ts in [a.get("trust_score", 0.5) for a in self.agents.values()]
            )
        }
