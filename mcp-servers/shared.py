"""Shared utilities for ADRION 369 MCP Servers.

Provides:
- GUARDIAN_LAWS: Canonical 9 laws (mirrors docs/GUARDIAN_LAWS_CANONICAL.json)
- EBDIState: Pleasure/Arousal/Dominance state vector
- TrustScore: Per-agent trust tracking (TSPA)
- digital_root(): Tesla 3-6-9 reduction
- evaluate_guardian_laws(): Full 9-law compliance check
- sha256_hex(), utc_now(): Utility helpers

This module must never import from mcp.* to remain testable without the SDK.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

# ---------------------------------------------------------------------------
# Guardian Laws — canonical source (mirrors docs/GUARDIAN_LAWS_CANONICAL.json)
# ---------------------------------------------------------------------------
GUARDIAN_LAWS: list[dict[str, str]] = [
    {"id": "G1", "name": "Unity",          "severity": "MEDIUM",   "veto": "false",
     "description": "All actions must serve system coherence"},
    {"id": "G2", "name": "Harmony",        "severity": "HIGH",     "veto": "false",
     "description": "Balance between competing objectives; analysis must be genuine"},
    {"id": "G3", "name": "Rhythm",         "severity": "MEDIUM",   "veto": "false",
     "description": "Maintain consistent cadence and timing of operations"},
    {"id": "G4", "name": "Causality",      "severity": "HIGH",     "veto": "false",
     "description": "Every action must have a traceable, justified cause"},
    {"id": "G5", "name": "Transparency",   "severity": "MEDIUM",   "veto": "false",
     "description": "All decisions and reasoning must be visible and auditable"},
    {"id": "G6", "name": "Authenticity",   "severity": "HIGH",     "veto": "false",
     "description": "Outputs must be genuine and free from deception"},
    {"id": "G7", "name": "Privacy",        "severity": "CRITICAL", "veto": "true",
     "description": "All data remains local; no repeated unsolicited contact without consent"},
    {"id": "G8", "name": "Nonmaleficence", "severity": "CRITICAL", "veto": "true",
     "description": "Never cause harm: do not bid on jobs outside fair budget range"},
    {"id": "G9", "name": "Sustainability", "severity": "HIGH",     "veto": "false",
     "description": "Operate within resource limits and preserve long-term system health"},
]

GUARDIAN_LAWS_BY_ID: dict[str, dict[str, str]] = {
    law["id"]: law for law in GUARDIAN_LAWS
}

SEVERITY_WEIGHTS: dict[str, int] = {"CRITICAL": 10, "HIGH": 2, "MEDIUM": 1}
DENY_WEIGHTED_THRESHOLD: int = 4  # cumulative weight that triggers DENY

MCP_PORTS: dict[str, int] = {
    "router":   9000,
    "vortex":   9001,
    "guardian": 9002,
    "oracle":   9003,
    "genesis":  9004,
    "healer":   9005,
}

# ---------------------------------------------------------------------------
# Agent Registry — ADRION 369 canonical 9 personas (expandable to 33)
# Canonical agent ID format for GSR: "{NAME}-{zero-padded-id}", e.g. "MPG-01"
# ---------------------------------------------------------------------------
AGENTS_REGISTRY: dict[str, dict[str, Any]] = {
    "01": {"name": "MPG", "domain": "prompt_generation",    "capabilities": ["generation", "analysis"]},
    "02": {"name": "PAA", "domain": "process_architecture", "capabilities": ["architecture", "workflow"]},
    "03": {"name": "TDO", "domain": "tooling_discovery",    "capabilities": ["tools", "integration"]},
    "04": {"name": "AUA", "domain": "automation_upgrade",   "capabilities": ["automation", "optimization"]},
    "05": {"name": "VTA", "domain": "verification_testing", "capabilities": ["testing", "validation"]},
    "06": {"name": "GRA", "domain": "governance_risk",      "capabilities": ["compliance", "security"]},
    "07": {"name": "OCA", "domain": "orchestration",        "capabilities": ["routing", "clarification"]},
    "08": {"name": "KSA", "domain": "knowledge",            "capabilities": ["documentation", "standards"]},
    "09": {"name": "RIA", "domain": "rollout_iteration",    "capabilities": ["deployment", "iteration"]},
}


# ---------------------------------------------------------------------------
# EBDI State Vector
# ---------------------------------------------------------------------------
@dataclass
class EBDIState:
    """Pleasure / Arousal / Dominance decision-space vector.

    Crisis mode activates when arousal > 0.7 — routes to HEALER.
    All values are clamped to [0.0, 1.0].
    """

    pleasure: float = 0.5
    arousal: float = 0.3
    dominance: float = 0.5
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def is_crisis(self) -> bool:
        return self.arousal > 0.7

    def update(
        self,
        pleasure: float | None = None,
        arousal: float | None = None,
        dominance: float | None = None,
    ) -> None:
        if pleasure is not None:
            self.pleasure = max(0.0, min(1.0, pleasure))
        if arousal is not None:
            self.arousal = max(0.0, min(1.0, arousal))
        if dominance is not None:
            self.dominance = max(0.0, min(1.0, dominance))
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Trust Score (TSPA)
# ---------------------------------------------------------------------------
@dataclass
class TrustScore:
    """Per-agent Trust Score.

    success  → TS += 0.05 (capped at 1.0)
    failure  → TS -= 0.20 (floored at 0.0)
    blocked  → TS < 0.60
    """

    agent: str
    score: float = 0.85
    successes: int = 0
    failures: int = 0

    def update(self, success: bool) -> None:
        if success:
            self.score = min(1.0, self.score + 0.05)
            self.successes += 1
        else:
            self.score = max(0.0, self.score - 0.20)
            self.failures += 1

    @property
    def is_blocked(self) -> bool:
        return self.score < 0.6

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# 3-6-9 Digital Root
# ---------------------------------------------------------------------------
def digital_root(n: int) -> int:
    """Tesla 3-6-9 digital root: reduces any integer to 1-9 (0 → 0).

    Uses the formula: 1 + (|n| - 1) % 9  for n != 0.
    """
    n = abs(n)
    if n == 0:
        return 0
    remainder = n % 9
    return remainder if remainder != 0 else 9


# ---------------------------------------------------------------------------
# Guardian Law Evaluator
# ---------------------------------------------------------------------------
def evaluate_guardian_laws(
    operation: str,
    context: dict[str, Any],
) -> tuple[bool, list[str], int]:
    """Evaluate all 9 Guardian Laws for a given operation + context.

    Returns:
        is_compliant  — False if any CRITICAL (veto) law fires OR score >= threshold
        violations    — list of violated law IDs (e.g. ["G7", "G5"])
        weighted_score — cumulative severity weight of violations
    """
    violations: list[str] = []
    score: int = 0

    # G7 Privacy: no unsolicited global data export
    if operation in {"export", "export_data"} and context.get("scope") == "global":
        violations.append("G7")
        score += SEVERITY_WEIGHTS["CRITICAL"]

    # G8 Nonmaleficence: destructive ops require confirmed backup
    if operation in {"delete", "destroy"} and not context.get("backup_exists", False):
        violations.append("G8")
        score += SEVERITY_WEIGHTS["CRITICAL"]

    # G5 Transparency: critical ops must be audit-logged
    _critical_ops = {"deploy", "delete", "destroy", "export", "export_data"}
    if operation in _critical_ops and not context.get("audit_logged", False):
        violations.append("G5")
        score += SEVERITY_WEIGHTS["MEDIUM"]

    # G4 Causality: every action must carry a stated reason
    if not context.get("reason"):
        violations.append("G4")
        score += SEVERITY_WEIGHTS["HIGH"]

    # G9 Sustainability: resource cost must be within limits
    if int(context.get("resource_cost", 0)) > 1000:
        violations.append("G9")
        score += SEVERITY_WEIGHTS["HIGH"]

    # Veto: any CRITICAL-veto law fires → instant DENY
    has_veto = bool({"G7", "G8"} & set(violations))
    is_compliant = (not has_veto) and (score < DENY_WEIGHTED_THRESHOLD)
    return is_compliant, violations, score


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------
def sha256_hex(data: str) -> str:
    """Return SHA-256 hex digest of UTF-8 encoded string."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def utc_now() -> str:
    """Current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()


def load_guardian_laws_json() -> str:
    """Return the canonical Guardian Laws as a JSON string."""
    return json.dumps(
        {
            "version": "2.0",
            "deny_weighted_threshold": DENY_WEIGHTED_THRESHOLD,
            "severity_weights": SEVERITY_WEIGHTS,
            "laws": GUARDIAN_LAWS,
        },
        indent=2,
    )
