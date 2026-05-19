"""
ADRION 369 — FeedbackLoop Orchestrator
Kamień Milowy 2+3: Obserwowalność + Pętla Dostrojenia

Orkiestrator OODA (Observe → Orient → Decide → Act).
Poszczególne komponenty wydzielone do:
  - behavior.py  → BehaviorLogger, Interaction
  - vera.py      → VERAScorer, VERAScore
  - judge.py     → Judge, JudgeVerdict
  - golden.py    → GoldenAnswerStore

Guardian Laws:
  - G4 (Causality): każda decyzja wyjaśniona
  - G5 (Transparency): pełne reasoning chain
  - G8 (Nonmaleficence): Sędzia blokuje dryf
  - G9 (Sustainability): długoterminowa optymalizacja
"""

from dataclasses import asdict
from typing import Optional

# Re-exporty dla kompatybilności wstecznej
from behavior import BehaviorLogger, Interaction
from vera import VERAScorer, VERAScore
from judge import Judge, JudgeVerdict
from golden import GoldenAnswerStore

try:
    from memory_events import (
        emit_interaction_logged, emit_feedback_received,
        emit_promoted_to_long_term, emit_judge_warned, emit_judge_blocked,
    )
    HAS_EVENT_BUS = True
except ImportError:
    HAS_EVENT_BUS = False


# ===== FEEDBACK LOOP (OODA) =====
class FeedbackLoop:
    """
    OODA Cycle: Observe → Orient → Decide → Act.
    Orchestrates all components for continuous improvement.
    """

    def __init__(self):
        self.behavior = BehaviorLogger()
        self.vera = VERAScorer(self.behavior)
        self.judge = Judge(self.vera, self.behavior)
        self.golden = GoldenAnswerStore()
        # RAG memory (lazy import to avoid circular deps)
        self._memory = None

    @property
    def memory(self):
        if self._memory is None:
            try:
                from rag_memory import get_memory
                self._memory = get_memory()
            except ImportError:
                self._memory = None
        return self._memory

    def observe(self, prompt: str, response: str, model: str = "",
                latency_ms: float = 0, category: str = "general",
                rag_context_used: bool = False) -> dict:
        """
        OBSERVE phase: Log the interaction and score it.
        Returns interaction_id + initial V.E.R.A. score.
        """
        # 1. Log interaction
        interaction_id = self.behavior.log_interaction(
            prompt=prompt, response=response, model=model,
            latency_ms=latency_ms, category=category,
            rag_context_used=rag_context_used,
        )

        # 2. Score with V.E.R.A.
        vera = self.vera.score_interaction(
            interaction_id=interaction_id,
            prompt=prompt, response=response,
            latency_ms=latency_ms,
            rag_used=rag_context_used,
        )

        # 3. Store in RAG memory
        if self.memory and self.memory.available:
            self.memory.add_interaction(
                prompt=prompt, response=response,
                metadata={"category": category, "model": model},
            )

        # 4. Emit event
        if HAS_EVENT_BUS:
            emit_interaction_logged(
                source="feedback_engine",
                interaction_id=interaction_id,
                category=category, model=model,
                vera_total=vera.total,
            )

        return {
            "interaction_id": interaction_id,
            "vera": vera.to_dict(),
        }

    def orient(self, interaction_id: str, accepted: bool = False,
               correction: str = None, score: int = 0) -> dict:
        """
        ORIENT phase: Process user feedback.
        Updates behavior log, re-scores V.E.R.A., runs Judge.
        """
        # 1. Log feedback
        if correction:
            self.behavior.log_correction(interaction_id, correction)
        if score != 0 or accepted:
            self.behavior.log_acceptance(interaction_id, score if score else (1 if accepted else -1))

        # 2. Re-score alignment with feedback
        # Find the interaction
        recent = self.behavior.get_recent(100)
        interaction = None
        for e in reversed(recent):
            if e["id"] == interaction_id:
                interaction = e
                break

        vera_update = None
        judge_verdict = None
        if interaction:
            vera = self.vera.score_interaction(
                interaction_id=f"{interaction_id}_fb",
                prompt=interaction["prompt"],
                response=interaction.get("correction") or interaction["response"],
                latency_ms=interaction.get("latency_ms", 0),
                accepted=accepted,
                correction=correction,
                rag_used=interaction.get("rag_context_used", False),
            )
            vera_update = vera.to_dict()

            # 3. Judge evaluation
            judge_verdict = self.judge.evaluate(interaction_id, vera)

            # 4. If correction provided and quality high, consider as golden answer
            if correction and accepted and vera.total > 0.7:
                self.golden.add(
                    prompt=interaction["prompt"],
                    golden_response=correction,
                    category=interaction.get("category", "general"),
                    source="user_correction",
                )

            # 5. Update RAG memory feedback
            if self.memory and self.memory.available:
                self.memory.update_feedback(
                    interaction_id,
                    score_delta=score if score else (1 if accepted else -1),
                )

            # 6. Emit events for feedback and judge verdict
            if HAS_EVENT_BUS:
                emit_feedback_received(
                    source="feedback_engine",
                    interaction_id=interaction_id,
                    score=score if score else (1 if accepted else -1),
                )
                if judge_verdict and judge_verdict.verdict == "warn":
                    emit_judge_warned(
                        source="feedback_engine",
                        interaction_id=interaction_id,
                        reason=judge_verdict.reason,
                    )
                elif judge_verdict and judge_verdict.verdict == "block":
                    emit_judge_blocked(
                        source="feedback_engine",
                        interaction_id=interaction_id,
                        reason=judge_verdict.reason,
                    )

        return {
            "interaction_id": interaction_id,
            "feedback_recorded": True,
            "vera": vera_update,
            "judge": asdict(judge_verdict) if judge_verdict else None,
        }

    def decide(self) -> dict:
        """
        DECIDE phase: Analyze trends, generate recommendations.
        """
        vera_avg = self.vera.get_average(50)
        vera_trend = self.vera.get_trend(10)
        judge_stats = self.judge.get_stats()
        behavior_stats = self.behavior.get_stats()
        capture_rate = self.behavior.capture_rate

        recommendations = []
        if vera_trend.get("trend") == "declining":
            recommendations.append("V.E.R.A. declining — review recent corrections for patterns")
        if judge_stats.get("block_rate", 0) > 0.1:
            recommendations.append("High block rate — model may need re-alignment")
        if capture_rate < 0.95:
            recommendations.append(f"Capture rate {capture_rate:.1%} < 95% target — encourage user feedback")
        if vera_avg.get("aligned", 0) < 0.5:
            recommendations.append("Low alignment — collect more golden answers for this domain")

        return {
            "vera_average": vera_avg,
            "vera_trend": vera_trend,
            "judge_stats": judge_stats,
            "behavior_stats": behavior_stats,
            "capture_rate": capture_rate,
            "recommendations": recommendations,
        }

    def act(self, prompt: str) -> dict:
        """
        ACT phase: Enrich query with RAG context + golden answers.
        Returns augmented context for better responses.
        """
        # 1. Check golden answers first
        golden = self.golden.find_match(prompt)

        # 2. Query RAG memory
        rag_results = []
        if self.memory and self.memory.available:
            rag_results = self.memory.query(prompt, n_results=3)

        # 3. Build augmented context
        context_parts = []
        if golden:
            context_parts.append(
                f"[ZŁOTA ODPOWIEDŹ] Dla podobnego pytania najlepsza odpowiedź to:\n{golden['golden_response']}"
            )
        for r in rag_results:
            if r["distance"] < 0.8:  # Only close matches
                context_parts.append(f"[PAMIĘĆ ({r['source']})] {r['document'][:300]}")

        return {
            "golden_match": golden["prompt"] if golden else None,
            "rag_matches": len(rag_results),
            "augmented_context": "\n---\n".join(context_parts) if context_parts else "",
            "context_used": bool(context_parts),
        }

    def get_full_status(self) -> dict:
        """Complete system status for dashboard."""
        memory_stats = self.memory.get_stats() if self.memory and self.memory.available else {"available": False}
        return {
            "behavior": self.behavior.get_stats(),
            "vera": self.vera.get_average(50),
            "vera_trend": self.vera.get_trend(10),
            "judge": self.judge.get_stats(),
            "golden_answers": self.golden.get_stats(),
            "memory": memory_stats,
            "capture_rate": self.behavior.capture_rate,
        }


# ===== SINGLETON =====
_loop: Optional[FeedbackLoop] = None


def get_feedback_loop() -> FeedbackLoop:
    global _loop
    if _loop is None:
        _loop = FeedbackLoop()
    return _loop
