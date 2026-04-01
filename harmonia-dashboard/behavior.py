"""
ADRION 369 — BehaviorLogger
Wydzielony z feedback_engine.py — logowanie interakcji prompt→response→correction→acceptance.

Guardian Laws:
  - G5 (Transparency): pełne reasoning chain preserved
"""

import json
import os
import time
import hashlib
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional

# ===== CONFIG =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BEHAVIOR_LOG = os.path.join(BASE_DIR, "behavior_log.json")
MAX_BEHAVIOR_ENTRIES = 5000


# ===== DATA MODEL =====
@dataclass
class Interaction:
    """Single user interaction record."""
    id: str = ""
    timestamp: str = ""
    prompt: str = ""
    response: str = ""
    correction: Optional[str] = None
    accepted: bool = False
    feedback_score: int = 0
    category: str = "general"
    latency_ms: float = 0.0
    model: str = ""
    rag_context_used: bool = False
    vera_score: Optional[dict] = None


# ===== BEHAVIOR LOGGER =====
class BehaviorLogger:
    """
    Logs all interactions: prompt → response → correction → acceptance.
    Guardian Law G5 (Transparency): full reasoning chain preserved.
    """

    def __init__(self):
        self._interactions: list[dict] = []
        self._load()

    def _load(self):
        if os.path.exists(BEHAVIOR_LOG):
            try:
                with open(BEHAVIOR_LOG, "r", encoding="utf-8") as f:
                    self._interactions = json.load(f)
            except (json.JSONDecodeError, OSError):
                self._interactions = []

    def _save(self):
        if len(self._interactions) > MAX_BEHAVIOR_ENTRIES:
            self._interactions = self._interactions[-MAX_BEHAVIOR_ENTRIES:]
        with open(BEHAVIOR_LOG, "w", encoding="utf-8") as f:
            json.dump(self._interactions, f, ensure_ascii=False, indent=2)

    def log_interaction(self, prompt: str, response: str, model: str = "",
                        latency_ms: float = 0.0, category: str = "general",
                        rag_context_used: bool = False) -> str:
        """Log a new interaction. Returns interaction ID."""
        interaction_id = hashlib.md5(
            f"{prompt}:{response}:{time.time()}".encode()
        ).hexdigest()[:16]

        entry = {
            "id": interaction_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "prompt": prompt,
            "response": response,
            "correction": None,
            "accepted": False,
            "feedback_score": 0,
            "category": category,
            "latency_ms": round(latency_ms, 1),
            "model": model,
            "rag_context_used": rag_context_used,
            "vera_score": None,
        }
        self._interactions.append(entry)
        self._save()
        return interaction_id

    def log_correction(self, interaction_id: str, correction: str):
        """User provided a manual correction for a response."""
        for entry in reversed(self._interactions):
            if entry["id"] == interaction_id:
                entry["correction"] = correction
                entry["accepted"] = False
                entry["feedback_score"] = min(entry.get("feedback_score", 0), -1)
                self._save()
                return True
        return False

    def log_acceptance(self, interaction_id: str, score: int = 1):
        """User accepted the response (explicit thumbs up/down)."""
        score = max(-2, min(2, score))
        for entry in reversed(self._interactions):
            if entry["id"] == interaction_id:
                entry["accepted"] = score > 0
                entry["feedback_score"] = score
                self._save()
                return True
        return False

    def get_recent(self, n: int = 50) -> list[dict]:
        return self._interactions[-n:]

    def get_by_category(self, category: str, n: int = 50) -> list[dict]:
        filtered = [e for e in self._interactions if e.get("category") == category]
        return filtered[-n:]

    def get_stats(self) -> dict:
        total = len(self._interactions)
        if total == 0:
            return {"total": 0, "accepted_rate": 0, "correction_rate": 0,
                    "avg_feedback": 0, "avg_latency_ms": 0}
        accepted = sum(1 for e in self._interactions if e.get("accepted"))
        corrected = sum(1 for e in self._interactions if e.get("correction"))
        avg_fb = sum(e.get("feedback_score", 0) for e in self._interactions) / total
        avg_lat = sum(e.get("latency_ms", 0) for e in self._interactions) / total
        return {
            "total": total,
            "accepted_rate": round(accepted / total, 3),
            "correction_rate": round(corrected / total, 3),
            "avg_feedback": round(avg_fb, 3),
            "avg_latency_ms": round(avg_lat, 1),
            "categories": list(set(e.get("category", "general") for e in self._interactions)),
        }

    @property
    def capture_rate(self) -> float:
        """KPI: What percentage of recent interactions have feedback?"""
        recent = self._interactions[-100:]
        if not recent:
            return 0.0
        scored = sum(1 for e in recent if e.get("feedback_score", 0) != 0 or e.get("accepted"))
        return round(scored / len(recent), 3)
