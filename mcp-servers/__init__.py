"""
MCP Base Classes & Utilities for ADRION 369 v4.0

Provides:
- MCPBaseServer: Abstract base for all MCP servers
- DSPy signature validator (DSV)
- Trust Score management (TSPA)
- EBDI state tracking
- Step Auto-Verification (SAV) hooks
"""

import json
from dataclasses import dataclass, asdict, field
from enum import Enum
from typing import Any, Callable, Optional, Dict, List
from datetime import datetime
import hashlib
import logging

logger = logging.getLogger(__name__)


class GuardianLaw(Enum):
    """9 Guardian Laws (G1-G9)"""
    G1_UNITY = "unity"
    G2_HARMONY = "harmony"
    G3_RHYTHM = "rhythm"
    G4_CAUSALITY = "causality"
    G5_TRANSPARENCY = "transparency"
    G6_AUTHENTICITY = "authenticity"
    G7_PRIVACY = "privacy"
    G8_NONMALEFICENCE = "nonmaleficence"
    G9_SUSTAINABILITY = "sustainability"


@dataclass
class EBDIState:
    """EBDI Vector (Pleasure, Arousal, Dominance)"""
    pleasure: float = 0.5  # [0...1]
    arousal: float = 0.3   # [0...1] — crisis if > 0.7
    dominance: float = 0.5  # [0...1]

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def is_crisis_mode(self) -> bool:
        """Trigger Crisis Mode if Arousal > 0.7"""
        return self.arousal > 0.7


@dataclass
class TrustScore:
    """Per-Agent Trust Score (TSPA)"""
    agent_name: str
    score: float = 0.8  # [0...1] — block if < 0.6
    successes: int = 0
    failures: int = 0
    last_update: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def increment_success(self):
        """Success: TS += 0.05"""
        self.score = min(1.0, self.score + 0.05)
        self.successes += 1
        self.last_update = datetime.utcnow().isoformat()

    def increment_failure(self):
        """Failure: TS -= 0.20"""
        self.score = max(0.0, self.score - 0.20)
        self.failures += 1
        self.last_update = datetime.utcnow().isoformat()

    @property
    def is_blocked(self) -> bool:
        """Block routing if TS < 0.6"""
        return self.score < 0.6

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DSPySignature:
    """Contract for Input → Output transformation"""
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    signature_name: str

    def validate_input(self, data: Dict[str, Any]) -> bool:
        """Check if input matches schema"""
        # Simplified validation — in prod, use jsonschema
        required = set(self.input_schema.keys())
        provided = set(data.keys())
        return required.issubset(provided)

    def validate_output(self, data: Dict[str, Any]) -> bool:
        """Check if output matches schema"""
        required = set(self.output_schema.keys())
        provided = set(data.keys())
        return required.issubset(provided)


@dataclass
class SAVCheckpoint:
    """Step Auto-Verification checkpoint"""
    step_id: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    definition_of_done: List[str] = field(default_factory=list)
    checks_passed: List[str] = field(default_factory=list)
    checks_failed: List[str] = field(default_factory=list)

    @property
    def is_complete(self) -> bool:
        """Step passed if all DoD checks passed"""
        return len(self.checks_failed) == 0 and len(self.checks_passed) == len(self.definition_of_done)


class MCPBaseServer:
    """Base class for all MCP servers"""

    def __init__(self, server_name: str, port: int, dspy_signature: DSPySignature):
        self.server_name = server_name
        self.port = port
        self.dspy_signature = dspy_signature
        self.ebdi_state = EBDIState()
        self.trust_score = TrustScore(agent_name=server_name)
        self.checkpoints: List[SAVCheckpoint] = []
        self.logger = logging.getLogger(f"MCP.{server_name}")

    def execute_step(self, step_name: str, operation: Callable, definition_of_done: List[str]) -> dict:
        """
        Execute single step with SAV (Step Auto-Verification)

        Returns: {success, result, checkpoint, errors}
        """
        checkpoint = SAVCheckpoint(
            step_id=step_name,
            definition_of_done=definition_of_done
        )

        try:
            # Execute operation
            result = operation()

            # Run all DoD checks
            for check_name in definition_of_done:
                if self._run_check(check_name, result):
                    checkpoint.checks_passed.append(check_name)
                else:
                    checkpoint.checks_failed.append(check_name)

            # Update state
            self.checkpoints.append(checkpoint)

            if checkpoint.is_complete:
                self.trust_score.increment_success()
                return {
                    "success": True,
                    "result": result,
                    "checkpoint": asdict(checkpoint),
                    "errors": []
                }
            else:
                self.trust_score.increment_failure()
                return {
                    "success": False,
                    "result": None,
                    "checkpoint": asdict(checkpoint),
                    "errors": checkpoint.checks_failed
                }

        except Exception as e:
            self.trust_score.increment_failure()
            checkpoint.checks_failed.append(str(e))
            return {
                "success": False,
                "result": None,
                "checkpoint": asdict(checkpoint),
                "errors": [str(e)]
            }

    def _run_check(self, check_name: str, result: Any) -> bool:
        """Override in subclasses"""
        return True

    def validate_guardian_laws(self, operation: str, context: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Check if operation violates any Guardian Laws
        Returns: (is_compliant, violated_laws)
        """
        # Simplified — in prod, use detailed rule engine
        violations = []

        # Example: G7 (Privacy) — check if data leakage
        if operation == "export_data" and context.get("local_first") is False:
            violations.append(GuardianLaw.G7_PRIVACY.value)

        return len(violations) == 0, violations

    def to_dict(self) -> dict:
        """Serialize server state"""
        return {
            "server_name": self.server_name,
            "port": self.port,
            "ebdi_state": self.ebdi_state.to_dict(),
            "trust_score": self.trust_score.to_dict(),
            "checkpoints": len(self.checkpoints),
            "signature_name": self.dspy_signature.signature_name
        }
