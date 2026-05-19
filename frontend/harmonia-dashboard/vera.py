"""
ADRION 369 — VERAScorer
Wydzielony z feedback_engine.py — V.E.R.A. scoring: Verifiable, Efficient, Relevant, Aligned.

Guardian Laws:
  - G4 (Causality): każda decyzja wyjaśniona
  - G5 (Transparency): pełne reasoning chain
"""

import json
import os
import re
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional

from behavior import BehaviorLogger

# ===== CONFIG =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VERA_LOG = os.path.join(BASE_DIR, "vera_scores.json")
MAX_VERA_ENTRIES = 2000


# ===== DATA MODEL =====
@dataclass
class VERAScore:
    """V.E.R.A. — Verifiable, Efficient, Relevant, Aligned."""
    verifiable: float = 0.0
    efficient: float = 0.0
    relevant: float = 0.0
    aligned: float = 0.0

    @property
    def total(self) -> float:
        """Weighted total: V=0.2, E=0.15, R=0.35, A=0.3"""
        return (self.verifiable * 0.2 +
                self.efficient * 0.15 +
                self.relevant * 0.35 +
                self.aligned * 0.3)

    def to_dict(self) -> dict:
        return {
            "verifiable": round(self.verifiable, 3),
            "efficient": round(self.efficient, 3),
            "relevant": round(self.relevant, 3),
            "aligned": round(self.aligned, 3),
            "total": round(self.total, 3),
        }


# ===== V.E.R.A. SCORER =====
class VERAScorer:
    """
    V.E.R.A. scoring: Verifiable, Efficient, Relevant, Aligned.
    Combines automatic heuristics with user feedback signals.
    """

    def __init__(self, behavior_logger: BehaviorLogger = None):
        self.logger = behavior_logger
        self._scores: list[dict] = []
        self._load()

    def _load(self):
        if os.path.exists(VERA_LOG):
            try:
                with open(VERA_LOG, "r", encoding="utf-8") as f:
                    self._scores = json.load(f)
            except (json.JSONDecodeError, OSError):
                self._scores = []

    def _save(self):
        if len(self._scores) > MAX_VERA_ENTRIES:
            self._scores = self._scores[-MAX_VERA_ENTRIES:]
        with open(VERA_LOG, "w", encoding="utf-8") as f:
            json.dump(self._scores, f, ensure_ascii=False, indent=2)

    def score_interaction(self, interaction_id: str, prompt: str, response: str,
                          latency_ms: float = 0, accepted: bool = False,
                          correction: str = None, rag_used: bool = False) -> VERAScore:
        """Score an interaction using V.E.R.A. heuristics."""
        v_score = self._score_verifiable(response)
        e_score = self._score_efficient(prompt, response, latency_ms)
        r_score = self._score_relevant(prompt, response)
        a_score = self._score_aligned(accepted, correction)

        vera = VERAScore(
            verifiable=v_score,
            efficient=e_score,
            relevant=r_score,
            aligned=a_score,
        )

        score_entry = {
            "interaction_id": interaction_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **vera.to_dict(),
            "rag_used": rag_used,
        }
        self._scores.append(score_entry)
        self._save()
        return vera

    def get_average(self, last_n: int = 50) -> dict:
        """Average V.E.R.A. scores over last N interactions."""
        recent = self._scores[-last_n:]
        if not recent:
            return {"total": 0, "verifiable": 0, "efficient": 0, "relevant": 0, "aligned": 0, "count": 0}
        avg = {
            "verifiable": sum(s.get("verifiable", 0) for s in recent) / len(recent),
            "efficient": sum(s.get("efficient", 0) for s in recent) / len(recent),
            "relevant": sum(s.get("relevant", 0) for s in recent) / len(recent),
            "aligned": sum(s.get("aligned", 0) for s in recent) / len(recent),
            "total": sum(s.get("total", 0) for s in recent) / len(recent),
            "count": len(recent),
        }
        return {k: round(v, 3) for k, v in avg.items()}

    def get_trend(self, window: int = 10) -> dict:
        """Compare recent window vs previous window to detect improvement/regression."""
        if len(self._scores) < window * 2:
            return {"trend": "insufficient_data", "delta": 0}
        recent = self._scores[-window:]
        previous = self._scores[-(window * 2):-window]
        r_avg = sum(s.get("total", 0) for s in recent) / len(recent)
        p_avg = sum(s.get("total", 0) for s in previous) / len(previous)
        delta = round(r_avg - p_avg, 3)
        return {
            "trend": "improving" if delta > 0.02 else ("declining" if delta < -0.02 else "stable"),
            "delta": delta,
            "recent_avg": round(r_avg, 3),
            "previous_avg": round(p_avg, 3),
        }

    @staticmethod
    def _score_verifiable(response: str) -> float:
        """Heuristic: does the response contain verifiable content?"""
        score = 0.3
        if re.search(r'\d+[%.,]\d*|\d{2,}', response):
            score += 0.2
        if '```' in response or '/' in response or 'http' in response:
            score += 0.15
        if any(response.count(marker) >= 2 for marker in ['- ', '1.', '* ']):
            score += 0.15
        if len(response) > 200:
            score += 0.1
        biz_terms = ['lead', 'klient', 'wynik', 'score', 'mail', 'pipeline', 'harmony']
        if any(t in response.lower() for t in biz_terms):
            score += 0.1
        return min(1.0, score)

    @staticmethod
    def _score_efficient(prompt: str, response: str, latency_ms: float) -> float:
        """Heuristic: conciseness + speed."""
        score = 0.5
        if latency_ms > 0:
            if latency_ms < 2000:
                score += 0.3
            elif latency_ms < 5000:
                score += 0.15
            elif latency_ms > 10000:
                score -= 0.2
        if len(prompt) > 0:
            ratio = len(response) / max(len(prompt), 1)
            if 1.0 <= ratio <= 10.0:
                score += 0.2
            elif ratio > 20.0:
                score -= 0.1
        return max(0.0, min(1.0, score))

    @staticmethod
    def _score_relevant(prompt: str, response: str) -> float:
        """Heuristic: keyword overlap between prompt and response."""
        p_words = set(prompt.lower().split())
        r_words = set(response.lower().split())
        stopwords = {'a', 'i', 'o', 'w', 'z', 'do', 'na', 'jest', 'to', 'się', 'nie',
                     'the', 'is', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at',
                     'co', 'jak', 'czy', 'dla', 'od', 'po', 'że', 'by'}
        p_words -= stopwords
        r_words -= stopwords
        if not p_words:
            return 0.5
        overlap = len(p_words & r_words)
        coverage = overlap / len(p_words)
        return min(1.0, 0.3 + coverage * 0.7)

    @staticmethod
    def _score_aligned(accepted: bool, correction: str = None) -> float:
        """User feedback signal for alignment."""
        if correction:
            return 0.2
        if accepted:
            return 0.9
        return 0.5
