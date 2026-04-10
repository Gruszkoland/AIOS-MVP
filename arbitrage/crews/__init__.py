"""
ADRION 369 — CrewAI Agents & Crews

Multi-agent orchestration using CrewAI for Trinity, Hexagon, and Guardian decision pipelines.
"""

from .trinity_crew import trinity_crew, TrnityCrew
from .hexagon_crew import hexagon_crew, HexagonCrew
from .guardian_crew import guardian_crew, GuardianCrew
from .orchestra import run_crewai_pipeline, run_full_demonstration

__all__ = [
    "trinity_crew",
    "TrnityCrew",
    "hexagon_crew",
    "HexagonCrew",
    "guardian_crew",
    "GuardianCrew",
    "run_crewai_pipeline",
    "run_full_demonstration",
]
