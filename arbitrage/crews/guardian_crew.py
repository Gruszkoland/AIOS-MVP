"""
ADRION 369 — Guardian CrewAI Agents & Crew

9 parallel agents for Guardian Laws validation (Unity, Harmony, Rhythm, Causality,
Transparency, Authenticity, Privacy, Nonmaleficence, Sustainability).

Wraps guardian.py logic into CrewAI agent structure.
"""
from __future__ import annotations

import logging

logger = logging.getLogger("adrion.crews.guardian")


class GuardianCrew:
    """
    Guardian Crew — 9 parallel agents for ethical law validation.

    Laws (can validate in parallel):
      1. Unity (MEDIUM)
      2. Harmony (HIGH)
      3. Rhythm (MEDIUM)
      4. Causality (HIGH)
      5. Transparency (MEDIUM)
      6. Authenticity (HIGH)
      7. Privacy (CRITICAL)
      8. Nonmaleficence (CRITICAL)
      9. Sustainability (HIGH)

    This is a mock implementation wrapping guardian.py.
    Future: Replace with actual CrewAI Agent/Crew classes.
    """

    def __init__(self):
        self.logger = logging.getLogger("adrion.crews.guardian.crew")

    def kickoff(self, inputs: dict) -> dict:
        """
        Run Guardian crew validation (parallel execution).

        Args:
            inputs: dict with key 'context' from Hexagon crew

        Returns:
            dict with all 9 law evaluations
        """
        from arbitrage.guardian import evaluate_guardians

        decision_context = inputs.get("context", {})

        self.logger.debug("Guardian crew starting validation")

        # Call existing guardian evaluation
        guardian_eval = evaluate_guardians(
            job={},
            analysis={},
            context=decision_context,
        )

        # Convert to crew-compatible format
        laws_output = {}
        if hasattr(guardian_eval, "evaluations") and guardian_eval.evaluations:
            for law_result in guardian_eval.evaluations:
                laws_output[law_result.name] = {
                    "name": law_result.name,
                    "passed": law_result.passed,
                    "reason": law_result.reason,
                    "weight": str(law_result.weight) if law_result.weight else "MEDIUM",
                }

        result = {
            "laws": laws_output,
            "violations": guardian_eval.violations if hasattr(guardian_eval, "violations") else 0,
            "status": "APPROVED" if guardian_eval.approved else "DENIED",
            "law_count": 9,
        }

        status = "✓ APPROVED" if guardian_eval.approved else "✗ DENIED"
        self.logger.info(
            "Guardian crew complete: %s (violations=%d)",
            status,
            result["violations"],
        )

        return result


# Default Guardian crew instance
guardian_crew = GuardianCrew()


def create_guardian_agents():
    """Create Guardian law evaluation agents (requires crewai package)."""
    try:
        from crewai import Agent

        agents = {}

        laws = [
            ("unity", "Ensure job aligns with system purpose", "MEDIUM"),
            ("truth", "Verify analysis is genuine and reasoned", "HIGH"),
            ("rhythm", "Check bid pace sustainability", "MEDIUM"),
            ("causality", "Trace price chain and validate causality", "HIGH"),
            ("transparency", "Ensure all required fields present", "MEDIUM"),
            ("nonmaleficence", "Prevent financial harm", "CRITICAL"),
            ("autonomy", "Avoid client spam (daily cap)", "HIGH"),
            ("justice", "Validate budget within fair range", "MEDIUM"),
            ("sustainability", "Keep daily costs within limits", "HIGH"),
        ]

        for law_name, description, criticality in laws:
            agents[law_name] = Agent(
                role=f"{law_name.capitalize()} Guardian",
                goal=f"Validate {law_name} law: {description}",
                description=f"Evaluates {law_name} ({criticality}) Guardian Law",
                allow_delegation=False,
            )

        return agents

    except ImportError:
        logger.warning("CrewAI not installed - using mock agents")
        return {}
