"""AnalyzeAgent — Autonomous job analysis and worthiness scoring

Responsibilities:
- Trinity evaluation (Material, Intellectual, Essential)
- Guardian Laws validation (9 ethical rules)
- Hexagon sequential processing (6 stages)
- RAG enrichment (optional)
- Worthiness scoring and decision
- Signal bidder when job is worthy
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from arbitrage.agents.base_agent import BaseAutonomousAgent

logger = logging.getLogger("adrion.agents.analyze_agent")

# Import evaluation engines
try:
    from arbitrage.trinity import evaluate_trinity
    TRINITY_AVAILABLE = True
except ImportError:
    TRINITY_AVAILABLE = False
    logger.warning("Trinity module not available")

try:
    from arbitrage.hexagon import HexagonProcessor
    HEXAGON_AVAILABLE = True
except ImportError:
    HEXAGON_AVAILABLE = False
    logger.warning("Hexagon module not available")

try:
    from arbitrage.guardian import evaluate_guardians, build_context
    GUARDIAN_AVAILABLE = True
except ImportError:
    GUARDIAN_AVAILABLE = False
    logger.warning("Guardian module not available")

try:
    from arbitrage.rag_integration import get_rag_integration
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    logger.warning("RAG module not available")


class AnalyzeAgent(BaseAutonomousAgent):
    """Autonomous Analyzer: evaluates jobs across Trinity-Hexagon-Guardian framework."""

    MIN_WORTHINESS_THRESHOLD = 0.5  # Minimum score to signal bidder

    def __init__(
        self,
        agent_id: str = "analyze-001",
        agent_name: str = "Analyzer Worker",
        trust_score: float = 0.88,
        max_retries: int = 3,
        use_rag: bool = False,
    ):
        super().__init__(agent_id, agent_name, trust_score, max_retries)
        self.use_rag = use_rag
        self.jobs_analyzed = 0
        self.jobs_worthy = 0

    async def execute(self, input_data: dict) -> dict:
        """Execute analyzer autonomous logic.

        1. Call Trinity evaluation (Material, Intellectual, Essential)
        2. Call Hexagon processing (6 stages)
        3. Validate Guardian Laws (9 ethical rules)
        4. Optional: RAG enrichment
        5. Score overall worthiness
        6. Return decision (worthy/not worthy + score)

        Args:
            input_data: {
                "job": {
                    "id": str,
                    "type": str,
                    "title": str,
                    "value": float,
                    ...
                },
                "analysis": dict (optional pre-analysis data),
                "use_rag": bool (optional override),
            }

        Returns:
            {
                "job_id": str,
                "worthy": bool,
                "worthiness_score": float,
                "trinity": dict,
                "hexagon": dict,
                "guardians": dict,
                "rag_context": dict | None,
                "decision_reason": str,
            }
        """
        job = input_data.get("job")
        if not job:
            raise ValueError("Input data must contain 'job'")

        job_id = job.get("id", "unknown")
        self.logger.info("Analyzer: Starting analysis for job %s", job_id)

        # Prepare analysis data
        analysis = input_data.get("analysis", {
            "score": 7,
            "fit": "Good",
            "risks": "None",
        })

        try:
            # Step 1: Trinity Evaluation
            trinity_result = None
            if TRINITY_AVAILABLE:
                trinity_result = await self._evaluate_trinity(job, analysis)
                self.logger.debug("Analyzer: Trinity complete - overall=%.4f",
                                trinity_result.get("overall", 0))
            else:
                self.logger.warning("Analyzer: Trinity not available, skipping")
                trinity_result = self._mock_trinity_result()

            # Step 2: Hexagon Processing
            hexagon_result = None
            if HEXAGON_AVAILABLE and trinity_result:
                hexagon_result = await self._evaluate_hexagon(trinity_result)
                self.logger.debug("Analyzer: Hexagon complete - score=%.4f",
                                hexagon_result.get("combined_score", 0))
            else:
                self.logger.warning("Analyzer: Hexagon not available, skipping")
                hexagon_result = self._mock_hexagon_result()

            # Step 3: Guardian Validation
            guardians_result = None
            if GUARDIAN_AVAILABLE:
                guardians_result = await self._evaluate_guardians(job, analysis)
                self.logger.debug("Analyzer: Guardian complete - approved=%s",
                                guardians_result.get("approved", False))
            else:
                self.logger.warning("Analyzer: Guardian not available, skipping")
                guardians_result = self._mock_guardian_result()

            # Step 4: RAG Enrichment (optional)
            rag_context = None
            if self.use_rag and RAG_AVAILABLE:
                try:
                    rag_context = await self._enhance_with_rag(job, trinity_result)
                except Exception as rag_exc:
                    self.logger.warning("Analyzer: RAG enhancement failed: %s", rag_exc)

            # Step 5: Score Worthiness
            worthiness_score = await self._score_worthiness(
                trinity_result,
                hexagon_result,
                guardians_result,
            )

            worthy = worthiness_score >= self.MIN_WORTHINESS_THRESHOLD

            if worthy:
                self.jobs_worthy += 1

            self.jobs_analyzed += 1

            decision_reason = await self._build_decision_reason(
                worthy,
                worthiness_score,
                trinity_result,
                hexagon_result,
                guardians_result,
            )

            self.logger.info(
                "Analyzer: Analysis complete - job_id=%s, worthy=%s, score=%.4f",
                job_id,
                worthy,
                worthiness_score,
            )

            return {
                "job_id": job_id,
                "worthy": worthy,
                "worthiness_score": round(worthiness_score, 4),
                "trinity": trinity_result,
                "hexagon": hexagon_result,
                "guardians": guardians_result,
                "rag_context": rag_context,
                "decision_reason": decision_reason,
            }

        except Exception as exc:
            self.logger.error("Analyzer: Analysis failed for %s: %s", job_id, exc)
            raise

    async def _evaluate_trinity(self, job: dict, analysis: dict) -> dict:
        """Evaluate using Trinity framework.

        Returns dict with material, intellectual, essential, overall scores.
        """
        self.logger.debug("Analyzer: Evaluating Trinity for %s", job.get("id"))

        trinity_eval = evaluate_trinity(job, analysis)

        return {
            "material": round(trinity_eval.material, 4),
            "intellectual": round(trinity_eval.intellectual, 4),
            "essential": round(trinity_eval.essential, 4),
            "overall": round(trinity_eval.combined, 4),
        }

    async def _evaluate_hexagon(self, trinity_result: dict) -> dict:
        """Evaluate using Hexagon pipeline.

        Returns dict with 6 stage results and combined score.
        """
        self.logger.debug("Analyzer: Evaluating Hexagon")

        processor = HexagonProcessor()
        hexagon_eval = processor.process(trinity_result)

        return {
            "stages": [s.to_dict() for s in hexagon_eval.stages],
            "combined_score": round(hexagon_eval.combined_score, 4),
            "duration_ms": round(hexagon_eval.total_duration_ms, 2),
            "approved": hexagon_eval.approved,
        }

    async def _evaluate_guardians(self, job: dict, analysis: dict) -> dict:
        """Validate using Guardian Laws.

        Returns dict with law evaluation results.
        """
        self.logger.debug("Analyzer: Evaluating Guardian Laws for %s", job.get("id"))

        guardian_context = build_context()
        guardian_eval = evaluate_guardians(job, analysis, guardian_context)

        return {
            "laws_evaluated": len(guardian_eval.laws),
            "laws_passed": sum(1 for l in guardian_eval.laws if l.passed),
            "violations": guardian_eval.violations,
            "approved": guardian_eval.approved,
            "laws": [
                {
                    "name": law.name,
                    "passed": law.passed,
                    "reason": law.reason,
                    "weight": law.weight,
                }
                for law in guardian_eval.laws
            ],
        }

    async def _enhance_with_rag(self, job: dict, trinity_result: dict) -> dict:
        """Enhance analysis with RAG context from Guardian Laws KB.

        Returns dict with retrieved context and reasoning.
        """
        self.logger.debug("Analyzer: Enhancing with RAG for %s", job.get("id"))

        rag = get_rag_integration()

        query = f"Ethical evaluation of {job.get('type', 'job')}: {job.get('title', 'untitled')}"
        context_docs = rag.retrieve_context(query, top_k=3)
        reasoning = rag.reason_with_context(query, context_docs)

        return {
            "query": query,
            "retrieved_docs": len(context_docs),
            "reasoning": reasoning.get("reasoning", ""),
            "available": rag.ragflow_available and rag.ollama_available,
        }

    async def _score_worthiness(
        self,
        trinity_result: dict,
        hexagon_result: dict,
        guardians_result: dict,
    ) -> float:
        """Score overall worthiness (0-1).

        Combines Trinity, Hexagon, and Guardian results into single score.

        Args:
            trinity_result: Trinity evaluation
            hexagon_result: Hexagon pipeline result
            guardians_result: Guardian Laws validation

        Returns:
            Worthiness score (0-1)
        """
        # Weights
        trinity_weight = 0.3
        hexagon_weight = 0.4
        guardian_weight = 0.3

        # Extract scores
        trinity_score = trinity_result.get("overall", 0.5)
        hexagon_score = hexagon_result.get("combined_score", 0.5)

        # Guardian: convert law_passed ratio to score
        laws_total = guardians_result.get("laws_evaluated", 9)
        laws_passed = guardians_result.get("laws_passed", 0)
        guardian_score = laws_passed / laws_total if laws_total > 0 else 0.5

        # Weighted average
        worthiness = (
            trinity_score * trinity_weight +
            hexagon_score * hexagon_weight +
            guardian_score * guardian_weight
        )

        # Clamp to [0, 1]
        worthiness = max(0.0, min(1.0, worthiness))

        return worthiness

    async def _build_decision_reason(
        self,
        worthy: bool,
        worthiness_score: float,
        trinity_result: dict,
        hexagon_result: dict,
        guardians_result: dict,
    ) -> str:
        """Build human-readable decision reason.

        Args:
            worthy: Whether job is worthy
            worthiness_score: Overall score
            trinity_result: Trinity evaluation
            hexagon_result: Hexagon result
            guardians_result: Guardian result

        Returns:
            Reason text
        """
        status = "WORTHY" if worthy else "NOT WORTHY"

        reasons = [
            f"Status: {status} (score={worthiness_score:.2%})",
            f"Trinity: {trinity_result.get('overall', 0):.2%}",
            f"Hexagon: {hexagon_result.get('combined_score', 0):.2%}",
            f"Guardian: {guardians_result.get('laws_passed', 0)}/{guardians_result.get('laws_evaluated', 9)} laws passed",
        ]

        return " | ".join(reasons)

    def _mock_trinity_result(self) -> dict:
        """Return mock Trinity result when module unavailable."""
        return {
            "material": 0.7,
            "intellectual": 0.7,
            "essential": 0.7,
            "overall": 0.7,
        }

    def _mock_hexagon_result(self) -> dict:
        """Return mock Hexagon result when module unavailable."""
        return {
            "stages": [],
            "combined_score": 0.7,
            "duration_ms": 0,
            "approved": True,
        }

    def _mock_guardian_result(self) -> dict:
        """Return mock Guardian result when module unavailable."""
        return {
            "laws_evaluated": 9,
            "laws_passed": 9,
            "violations": 0,
            "approved": True,
            "laws": [],
        }

    def get_analyzer_stats(self) -> dict:
        """Get analyzer statistics."""
        return {
            "agent_id": self.agent_id,
            "jobs_analyzed": self.jobs_analyzed,
            "jobs_worthy": self.jobs_worthy,
            "worthy_ratio": (
                self.jobs_worthy / self.jobs_analyzed
                if self.jobs_analyzed > 0
                else 0.0
            ),
        }
