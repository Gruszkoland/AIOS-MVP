"""
ADRION 369 — Judge (Sędzia)
Wydzielony z feedback_engine.py — guardrails anty-dryf, monitoring jakości modelu.

Guardian Laws:
  - G4 (Causality): Every verdict has a reason
  - G8 (Nonmaleficence): Blocks harmful drift
  - G9 (Sustainability): Long-term quality preservation
"""

import json
import os
from datetime import datetime, timezone
from dataclasses import dataclass, asdict

from vera import VERAScorer, VERAScore
from behavior import BehaviorLogger

# ===== CONFIG =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JUDGE_LOG = os.path.join(BASE_DIR, "judge_log.json")
MAX_JUDGE_ENTRIES = 1000

DRIFT_THRESHOLD_ACCURACY = 0.4
DRIFT_THRESHOLD_ALIGNMENT = 0.3
DRIFT_WINDOW = 20


# ===== DATA MODEL =====
@dataclass
class JudgeVerdict:
    """Sędzia ruling on an interaction."""
    interaction_id: str = ""
    timestamp: str = ""
    verdict: str = "pass"           # pass | warn | block
    reason: str = ""
    drift_score: float = 0.0
    vera_score: float = 0.0
    action_taken: str = ""          # none | logged | blocked | escalated


# ===== JUDGE =====
class Judge:
    """
    Sędzia module: Guardian against Model Drift.
    Monitors V.E.R.A. trends and blocks degrading patterns.
    """

    def __init__(self, vera_scorer: VERAScorer = None, behavior_logger: BehaviorLogger = None):
        self.vera = vera_scorer
        self.logger = behavior_logger
        self._verdicts: list[dict] = []
        self._load()

    def _load(self):
        if os.path.exists(JUDGE_LOG):
            try:
                with open(JUDGE_LOG, "r", encoding="utf-8") as f:
                    self._verdicts = json.load(f)
            except (json.JSONDecodeError, OSError):
                self._verdicts = []

    def _save(self):
        if len(self._verdicts) > MAX_JUDGE_ENTRIES:
            self._verdicts = self._verdicts[-MAX_JUDGE_ENTRIES:]
        with open(JUDGE_LOG, "w", encoding="utf-8") as f:
            json.dump(self._verdicts, f, ensure_ascii=False, indent=2)

    def evaluate(self, interaction_id: str, vera_score: VERAScore) -> JudgeVerdict:
        """Evaluate an interaction and issue a verdict."""
        drift = self._detect_drift()
        verdict = JudgeVerdict(
            interaction_id=interaction_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            drift_score=drift,
            vera_score=vera_score.total,
        )

        if vera_score.total < DRIFT_THRESHOLD_ACCURACY:
            verdict.verdict = "block"
            verdict.reason = f"V.E.R.A. total ({vera_score.total:.3f}) below accuracy threshold ({DRIFT_THRESHOLD_ACCURACY})"
            verdict.action_taken = "blocked"
        elif vera_score.aligned < DRIFT_THRESHOLD_ALIGNMENT:
            verdict.verdict = "warn"
            verdict.reason = f"Alignment score ({vera_score.aligned:.3f}) below threshold ({DRIFT_THRESHOLD_ALIGNMENT}) — potential drift"
            verdict.action_taken = "logged"
        elif drift > 0.6:
            verdict.verdict = "warn"
            verdict.reason = f"Drift score elevated ({drift:.3f}) — recent quality declining"
            verdict.action_taken = "escalated"
        else:
            verdict.verdict = "pass"
            verdict.reason = "All metrics within acceptable ranges"
            verdict.action_taken = "none"

        self._verdicts.append(asdict(verdict))
        self._save()
        return verdict

    def _detect_drift(self) -> float:
        """Detect model drift by comparing recent vs historical V.E.R.A. averages."""
        if not self.vera:
            return 0.0
        trend = self.vera.get_trend(window=DRIFT_WINDOW)
        if trend["trend"] == "insufficient_data":
            return 0.0
        delta = trend.get("delta", 0)
        if delta >= 0:
            return 0.0
        return min(1.0, abs(delta) * 5)

    def get_stats(self) -> dict:
        total = len(self._verdicts)
        if total == 0:
            return {"total": 0, "pass_rate": 0, "warn_rate": 0, "block_rate": 0, "avg_drift": 0}
        passes = sum(1 for v in self._verdicts if v.get("verdict") == "pass")
        warns = sum(1 for v in self._verdicts if v.get("verdict") == "warn")
        blocks = sum(1 for v in self._verdicts if v.get("verdict") == "block")
        avg_drift = sum(v.get("drift_score", 0) for v in self._verdicts) / total
        return {
            "total": total,
            "pass_rate": round(passes / total, 3),
            "warn_rate": round(warns / total, 3),
            "block_rate": round(blocks / total, 3),
            "avg_drift": round(avg_drift, 3),
            "last_verdict": self._verdicts[-1] if self._verdicts else None,
        }

    def get_recent_verdicts(self, n: int = 20) -> list[dict]:
        return self._verdicts[-n:]
