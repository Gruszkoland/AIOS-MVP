"""Autonomous Agent Framework — ADRION 369 Phase 3

Provides BaseAutonomousAgent abstract class and specialized agent implementations
for distributed task execution with encapsulated business logic.

Agents support:
- Autonomous task execution with retry/backoff
- TSPA (Trust Score Per Agent) validation (minimum 0.6)
- HEALER-MCP escalation on persistent failures
- Performance metrics tracking (duration, success rate)
- Queue-based inter-agent communication
"""

__all__ = [
    "BaseAutonomousAgent",
    "get_logger_for_agent",
]

import logging


def get_logger_for_agent(agent_name: str) -> logging.Logger:
    """Get a logger instance for an agent."""
    return logging.getLogger(f"adrion.agents.{agent_name}")
