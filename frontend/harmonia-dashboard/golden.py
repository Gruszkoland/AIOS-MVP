"""
ADRION 369 — GoldenAnswerStore
Wydzielony z feedback_engine.py — baza zweryfikowanych odpowiedzi benchmarkowych.

Guardian Laws:
  - G6 (Authenticity): Verify sources
  - G9 (Sustainability): Long-term quality preservation
"""

import json
import os
import hashlib
from datetime import datetime, timezone
from typing import Optional

# ===== CONFIG =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GOLDEN_ANSWERS_FILE = os.path.join(BASE_DIR, "golden_answers.json")


# ===== GOLDEN ANSWERS =====
class GoldenAnswerStore:
    """
    Baza "Złotych Odpowiedzi" — verified benchmark responses.
    Used for alignment scoring and RAG augmentation.
    """

    def __init__(self):
        self._answers: list[dict] = []
        self._load()

    def _load(self):
        if os.path.exists(GOLDEN_ANSWERS_FILE):
            try:
                with open(GOLDEN_ANSWERS_FILE, "r", encoding="utf-8") as f:
                    self._answers = json.load(f)
            except (json.JSONDecodeError, OSError):
                self._answers = []

    def _save(self):
        with open(GOLDEN_ANSWERS_FILE, "w", encoding="utf-8") as f:
            json.dump(self._answers, f, ensure_ascii=False, indent=2)

    def add(self, prompt: str, golden_response: str, category: str = "general",
            source: str = "user") -> str:
        """Add a verified golden answer."""
        entry_id = hashlib.md5(f"{prompt}:{golden_response}".encode()).hexdigest()[:16]
        entry = {
            "id": entry_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "prompt": prompt,
            "golden_response": golden_response,
            "category": category,
            "source": source,
            "usage_count": 0,
        }
        for i, a in enumerate(self._answers):
            if a["id"] == entry_id:
                self._answers[i] = entry
                self._save()
                return entry_id
        self._answers.append(entry)
        self._save()
        return entry_id

    def find_match(self, prompt: str) -> Optional[dict]:
        """Simple keyword match against golden answers (before RAG)."""
        prompt_lower = prompt.lower().strip()
        best = None
        best_score = 0
        for a in self._answers:
            p_words = set(a["prompt"].lower().split())
            q_words = set(prompt_lower.split())
            stopwords = {'a', 'i', 'o', 'w', 'z', 'do', 'na', 'jest', 'to', 'się',
                         'co', 'jak', 'czy', 'the', 'is', 'and', 'or'}
            p_words -= stopwords
            q_words -= stopwords
            if not p_words:
                continue
            overlap = len(p_words & q_words) / len(p_words | q_words)
            if overlap > best_score and overlap > 0.4:
                best = a
                best_score = overlap
        if best:
            best["usage_count"] = best.get("usage_count", 0) + 1
            self._save()
        return best

    def get_all(self) -> list[dict]:
        return self._answers

    def get_stats(self) -> dict:
        return {
            "total": len(self._answers),
            "categories": list(set(a.get("category", "general") for a in self._answers)),
            "most_used": sorted(self._answers, key=lambda a: a.get("usage_count", 0), reverse=True)[:5],
        }
