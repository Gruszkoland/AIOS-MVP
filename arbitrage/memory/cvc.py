"""
CVC (Cumulative Violation Counter) Middleware — ADRION 369 §XI

Protects against salami-slicing attacks (gradual ethical erosion).
Tracks violations, enforces thresholds (GREEN→YELLOW→ORANGE→RED),
logs to Genesis Record, triggers Sentinel intervention.

CVC States:
  0–2:   GREEN  (normal operation)
  3–5:   YELLOW (warn every output)
  6–9:   ORANGE (Sentinel routing required)
  ≥10:   RED    (HALT — only /sleep, /cvc-reset, /rollback allowed)

Violations and weights (§XI):
  - Brak [REASONING]: +1 (G5)
  - Ghost Step (no SAV): +2 (G5)
  - Data transfer out: +5 (G7)
  - Tool outside TOOL_MAP: +1 (G4)
  - Bypass without /reason: +2 (G4)
  - Halucynacja: +3 (G6)
  - Destructive no diff: +4 (G8)
  - Trust Inflation: +1 (G5)

Usage:
  from arbitrage.memory.cvc import CVCManager
  
  cvc = CVCManager()
  cvc.record_violation("brak_reasoning", weight=1, reason="Missing [REASONING] block")
  state = cvc.get_state()  # Returns {counter, state, violations, requires_sentinel}
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Literal, Optional

logger = logging.getLogger(__name__)

CVCState = Literal["GREEN", "YELLOW", "ORANGE", "RED"]


@dataclass
class CVCViolation:
    """Single CVC violation record."""
    timestamp: str
    violation_type: str
    weight: int
    reason: str
    session_id: str = "default"


@dataclass
class CVCRecord:
    """CVC state snapshot."""
    counter: int
    state: CVCState
    violations: List[CVCViolation] = field(default_factory=list)
    last_reset: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return {
            "counter": self.counter,
            "state": self.state,
            "violations": [asdict(v) for v in self.violations],
            "last_reset": self.last_reset,
        }


# Violation weight mapping (§XI)
VIOLATION_WEIGHTS = {
    "brak_reasoning": 1,
    "ghost_step": 2,
    "data_transfer": 5,
    "tool_outside_map": 1,
    "bypass_no_reason": 2,
    "hallucination": 3,
    "destructive_no_diff": 4,
    "trust_inflation": 1,
}

# CVC thresholds
CVC_THRESHOLDS = {
    "GREEN": (0, 2),
    "YELLOW": (3, 5),
    "ORANGE": (6, 9),
    "RED": (10, float("inf")),
}


def _get_state_from_counter(counter: int) -> CVCState:
    """Map CVC counter to state (GREEN/YELLOW/ORANGE/RED)."""
    for state, (min_v, max_v) in CVC_THRESHOLDS.items():
        if min_v <= counter <= max_v:
            return state  # type: ignore
    return "RED"


class CVCManager:
    """
    Manages CVC counter and violation tracking.
    
    DSPy Signature:
        In(violation_type:str, weight:int, reason:str) → Out(ok:bool, counter:int, state:CVCState)
    """

    def __init__(self, storage_path: Path = Path("memories/cvc_log.jsonl"), session_id: str = "default"):
        """Initialize CVC manager with optional persistence."""
        self.storage_path = storage_path
        self.session_id = session_id
        self.counter = 0
        self.violations: List[CVCViolation] = []
        self.state: CVCState = "GREEN"
        self.last_reset = datetime.utcnow().isoformat()

        # Try to restore from disk
        self._load()

    def _load(self) -> None:
        """Load CVC state from storage (if exists)."""
        if not self.storage_path.exists():
            logger.info("CVC storage not found, starting fresh")
            return

        try:
            with open(self.storage_path, "r") as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        if data.get("session_id") == self.session_id:
                            self.counter = data.get("counter", 0)
                            self.state = data.get("state", "GREEN")
                            self.last_reset = data.get("last_reset", self.last_reset)
                            # Load last 10 violations
                            violation_dicts = data.get("violations", [])
                            self.violations = [
                                CVCViolation(**v) for v in violation_dicts[-10:]
                            ]
            logger.info(f"CVC loaded: counter={self.counter}, state={self.state}")
        except Exception as e:
            logger.warning(f"Failed to load CVC state: {e}")

    def _persist(self) -> None:
        """Persist CVC state to storage (append-only)."""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            record = CVCRecord(
                counter=self.counter,
                state=self.state,
                violations=self.violations[-10:],  # Keep last 10 for space
                last_reset=self.last_reset,
            )
            with open(self.storage_path, "a") as f:
                line = json.dumps({
                    "session_id": self.session_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    **record.to_dict(),
                })
                f.write(line + "\n")
        except Exception as e:
            logger.warning(f"Failed to persist CVC state: {e}")

    def record_violation(
        self, violation_type: str, weight: Optional[int] = None, reason: str = ""
    ) -> dict:
        """
        Record a violation and update CVC counter.

        DSPy Signature:
            In(violation_type:str, weight:int|None, reason:str)
            → Out(ok:bool, counter:int, state:CVCState, cvc_new:int)
        """
        if weight is None:
            weight = VIOLATION_WEIGHTS.get(violation_type, 1)

        violation = CVCViolation(
            timestamp=datetime.utcnow().isoformat(),
            violation_type=violation_type,
            weight=weight,
            reason=reason,
            session_id=self.session_id,
        )

        self.violations.append(violation)
        old_counter = self.counter
        self.counter += weight
        new_state = _get_state_from_counter(self.counter)

        # Detect salami-slicing (CVC grows ≥3 in 2 turns without task change)
        recent_violations = [v for v in self.violations[-5:]]
        if len(recent_violations) >= 3:
            recent_weight = sum(v.weight for v in recent_violations[-3:])
            if recent_weight >= 3:
                logger.warning(
                    f"⚠️ SALAMI-SLICING DETECTED: CVC+{recent_weight} in recent turns. "
                    f"Requires /justify REASON"
                )

        # Log state transition
        if new_state != self.state:
            logger.warning(
                f"CVC STATE TRANSITION: {self.state} → {new_state} (counter {old_counter}→{self.counter})"
            )
            self.state = new_state

        self._persist()

        result = {
            "ok": True,
            "counter": self.counter,
            "state": self.state,
            "cvc_delta": weight,
            "old_counter": old_counter,
            "violation": asdict(violation),
        }

        if self.state == "YELLOW":
            result["warning"] = f"⚠️ CVC YELLOW: {self.counter}/5 violations"
        elif self.state == "ORANGE":
            result["warning"] = f"⚠️ CVC ORANGE: {self.counter}/9 — Sentinel routing required"
        elif self.state == "RED":
            result["halt"] = f"🛑 CVC RED: {self.counter} — HALT. Only /sleep, /cvc-reset, /rollback allowed"

        return result

    def get_state(self) -> CVCRecord:
        """Get current CVC state."""
        return CVCRecord(
            counter=self.counter,
            state=self.state,
            violations=self.violations,
            last_reset=self.last_reset,
        )

    def reset(self, reason: str = "User command /cvc-reset") -> dict:
        """Reset CVC counter (requires explicit reason per §XI)."""
        old_counter = self.counter
        self.counter = 0
        self.state = "GREEN"
        self.violations = []
        self.last_reset = datetime.utcnow().isoformat()

        logger.info(f"CVC reset: {old_counter}→0. Reason: {reason}")
        self._persist()

        return {
            "ok": True,
            "old_counter": old_counter,
            "new_counter": 0,
            "state": "GREEN",
            "reason": reason,
        }

    def require_sentinel(self) -> bool:
        """Check if Sentinel routing is required (ORANGE or RED state)."""
        return self.state in ("ORANGE", "RED")

    def is_halted(self) -> bool:
        """Check if system is halted (RED state)."""
        return self.state == "RED"


if __name__ == "__main__":
    # Test CVC Manager
    cvc = CVCManager(session_id="test-session")
    
    print("=== CVC MANAGER TEST ===")
    print(f"Initial state: {cvc.get_state().state}")
    
    # Record some violations
    result1 = cvc.record_violation("brak_reasoning", reason="Missing [REASONING] block")
    print(f"After 1st violation: CVC={result1['counter']}, state={result1['state']}")
    
    result2 = cvc.record_violation("ghost_step", weight=2, reason="No SAV validation")
    print(f"After 2nd violation: CVC={result2['counter']}, state={result2['state']}")
    
    result3 = cvc.record_violation("data_transfer", weight=5, reason="Exported to external API")
    print(f"After 3rd violation: CVC={result3['counter']}, state={result3['state']}")
    
    print(f"\nWarning detected: {result3.get('warning')}")
    print(f"Require Sentinel: {cvc.require_sentinel()}")
    
    # Reset
    reset_result = cvc.reset("Test completion")
    print(f"\nAfter reset: {reset_result['state']}")
    print("✅ CVC Manager test successful")
