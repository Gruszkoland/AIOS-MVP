"""
ADRION 369 — Hexagon CrewAI Agents & Crew

6 sequential agents (Inventory → Empathy → Process → Debate → Healing → Action).
Wraps hexagon.py logic into CrewAI agent structure.
"""
from __future__ import annotations

import logging

logger = logging.getLogger("adrion.crews.hexagon")


class HexagonCrew:
    """
    Hexagon Crew — 6 sequential agents for pipeline processing.

    Stages: Inventory → Empathy → Process → Debate → Healing → Action

    This is a mock implementation wrapping hexagon.py.
    Future: Replace with actual CrewAI Agent/Crew classes.
    """

    def __init__(self):
        self.logger = logging.getLogger("adrion.crews.hexagon.crew")

    def kickoff(self, inputs: dict) -> dict:
        """
        Run Hexagon crew pipeline (sequential execution).

        Args:
            inputs: dict with key 'trinity_scores' from Trinity crew

        Returns:
            dict with all 6 stage results
        """
        from arbitrage.hexagon import HexagonProcessor

        trinity_scores = inputs.get("trinity_scores", {})

        self.logger.debug("Hexagon crew starting pipeline")

        processor = HexagonProcessor()
        hexagon_result = processor.process(trinity_scores)

        # Convert to crew-compatible format
        stages_output = {
            stage.stage_name: stage.to_dict()
            for stage in hexagon_result.stages
        }

        result = {
            "stages": stages_output,
            "combined_score": hexagon_result.combined_score,
            "total_duration_ms": hexagon_result.total_duration_ms,
            "approved": hexagon_result.approved,
            "stage_count": 6,
        }

        status = "✓ APPROVED" if hexagon_result.approved else "✗ DENIED"
        self.logger.info(
            "Hexagon crew complete: %s (combined=%.3f duration=%.1fms)",
            status,
            hexagon_result.combined_score,
            hexagon_result.total_duration_ms,
        )

        return result


# Default Hexagon crew instance
hexagon_crew = HexagonCrew()


def create_hexagon_agents():
    """Create Hexagon stage agents (requires crewai package)."""
    try:
        from crewai import Agent

        agents = {}

        stages = [
            ("inventory", "Resource and asset analysis"),
            ("empathy", "Stakeholder impact evaluation"),
            ("process", "Workflow optimization"),
            ("debate", "Multi-perspective deliberation"),
            ("healing", "Risk mitigation planning"),
            ("action", "Final recommendation"),
        ]

        for stage_name, description in stages:
            agents[stage_name] = Agent(
                role=f"{stage_name.capitalize()} Agent",
                goal=f"Execute {stage_name} stage: {description}",
                description=f"Processes {stage_name} stage of hexagon pipeline",
                allow_delegation=False,
            )

        return agents

    except ImportError:
        logger.warning("CrewAI not installed - using mock agents")
        return {}
