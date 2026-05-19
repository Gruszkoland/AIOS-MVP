"""
ADRION 369 — Orchestra: Unified CrewAI Pipeline Orchestration

Orchestrates the complete decision pipeline:
  Trinity Crew (parallel) → Hexagon Crew (sequential) → Guardian Crew (parallel)

Produces full decision output with all reasoning and audit trail.
"""
from __future__ import annotations

import logging
from datetime import datetime

logger = logging.getLogger("adrion.crews.orchestra")


async def run_crewai_pipeline(job_data: dict) -> dict:
    """
    Execute full CrewAI pipeline: Trinity → Hexagon → Guardian.

    Args:
        job_data: dict containing job details

    Returns:
        dict with complete decision (trinity, hexagon, guardians, final decision)
    """
    from arbitrage.crews.trinity_crew import trinity_crew
    from arbitrage.crews.hexagon_crew import hexagon_crew
    from arbitrage.crews.guardian_crew import guardian_crew

    logger.info("🎼 Orchestra starting: Trinity → Hexagon → Guardian pipeline")

    # Step 1: Trinity Crew (parallel perspective evaluation)
    logger.debug("Step 1/3: Trinity crew evaluation...")
    trinity_result = trinity_crew.kickoff(
        inputs={
            "job": job_data,
            "analysis": job_data.get("analysis", {}),
            "resources": job_data.get("resources"),
        }
    )
    logger.info("✓ Trinity complete (combined=%.3f)", trinity_result["combined_score"])

    # Step 2: Hexagon Crew (sequential pipeline processing)
    logger.debug("Step 2/3: Hexagon crew pipeline...")
    hexagon_result = hexagon_crew.kickoff(
        inputs={
            "trinity_scores": {
                "material": trinity_result["material"]["score"],
                "intellectual": trinity_result["intellectual"]["score"],
                "essential": trinity_result["essential"]["score"],
                "combined": trinity_result["combined_score"],
            }
        }
    )
    logger.info("✓ Hexagon complete (combined=%.3f)", hexagon_result["combined_score"])

    # Step 3: Guardian Crew (parallel law validation)
    logger.debug("Step 3/3: Guardian crew validation...")
    guardian_result = guardian_crew.kickoff(inputs={"context": hexagon_result})
    logger.info("✓ Guardian complete (violations=%d)", guardian_result["violations"])

    # Final decision
    final_approved = (
        trinity_result["approved"]
        and hexagon_result["approved"]
        and guardian_result["status"] == "APPROVED"
    )

    decision_summary = {
        "APPROVED": "✓✓✓",
        "DENIED": "✗✗✗",
        "CONDITIONAL": "~",
    }

    if not final_approved:
        final_decision = "DENIED"
    elif guardian_result["violations"] > 0:
        final_decision = "CONDITIONAL"
    else:
        final_decision = "APPROVED"

    logger.info("🎼 Orchestra complete: %s %s", final_decision, decision_summary[final_decision])

    return {
        "job_id": job_data.get("id", "unknown"),
        "timestamp": datetime.utcnow().isoformat(),
        "trinity": trinity_result,
        "hexagon": hexagon_result,
        "guardians": guardian_result,
        "final_decision": final_decision,
        "approved": final_approved,
    }


def run_full_demonstration(job: dict) -> dict:
    """
    Synchronous wrapper for full demonstration (non-async version).

    Args:
        job: job data dict

    Returns:
        dict with complete decision output
    """
    import asyncio

    # For Python 3.7+ with event loop policy issues
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    result = loop.run_until_complete(run_crewai_pipeline(job))
    return result


# ─────────────────────────────────────────────────────────────────────
# Orchestra Orchestrator Class (Alternative Interface)
# ─────────────────────────────────────────────────────────────────────

class OrchestraOrchestrator:
    """
    Unified orchestrator for Trinity → Hexagon → Guardian pipeline.

    Provides synchronized and asynchronous execution modes.
    """

    def __init__(self):
        self.logger = logging.getLogger("adrion.orchestra")

    def execute_sync(self, job_data: dict) -> dict:
        """Execute pipeline synchronously."""
        return run_full_demonstration(job_data)

    async def execute_async(self, job_data: dict) -> dict:
        """Execute pipeline asynchronously."""
        return await run_crewai_pipeline(job_data)

    def execute(self, job_data: dict, async_mode: bool = False) -> dict:
        """
        Execute pipeline (mode-agnostic).

        Args:
            job_data: input job
            async_mode: if True, use async; if False, use sync

        Returns:
            dict with complete decision
        """
        if async_mode:
            import asyncio

            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            return loop.run_until_complete(self.execute_async(job_data))
        else:
            return self.execute_sync(job_data)


# Default orchestrator instance
orchestra = OrchestraOrchestrator()
