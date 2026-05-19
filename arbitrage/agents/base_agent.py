"""BaseAutonomousAgent — Abstract foundation for all autonomous agents

Provides:
- Abstract execute() method for subclasses to implement
- run_with_retry() with exponential backoff and HEALER escalation
- TSPA (Trust Score Per Agent) validation (minimum 0.6)
- Performance metrics tracking
- Graceful failure handling and recovery
"""

from __future__ import annotations

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger("adrion.agents.base_agent")


@dataclass
class AgentMetrics:
    """Performance and reliability metrics for an agent."""
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_duration_ms: float = 0.0
    success_rate: float = 1.0
    avg_duration_ms: float = 0.0
    last_error: Optional[str] = None
    last_error_time: Optional[float] = None

    def update_success(self, duration_ms: float) -> None:
        """Record successful task execution."""
        self.tasks_completed += 1
        self.total_duration_ms += duration_ms
        self.avg_duration_ms = self.total_duration_ms / self.tasks_completed
        self.success_rate = self.tasks_completed / (self.tasks_completed + self.tasks_failed)
        self.last_error = None

    def update_failure(self, error: str) -> None:
        """Record failed task execution."""
        self.tasks_failed += 1
        self.success_rate = self.tasks_completed / (self.tasks_completed + self.tasks_failed)
        self.last_error = error
        self.last_error_time = time.time()


class BaseAutonomousAgent(ABC):
    """Abstract base class for all autonomous agents in ADRION 369 Phase 3.

    Encapsulates business logic and handles:
    - Autonomous task execution
    - Retry logic with exponential backoff
    - HEALER-MCP escalation on persistent failures
    - TSPA (Trust Score Per Agent) validation
    - Performance metrics tracking
    """

    TSPA_MINIMUM = 0.6  # Minimum trust score to execute tasks

    def __init__(
        self,
        agent_id: str,
        agent_name: str,
        trust_score: float = 0.8,
        max_retries: int = 3,
    ):
        """Initialize autonomous agent.

        Args:
            agent_id: Unique agent identifier (e.g., "scout-001")
            agent_name: Human-readable agent name (e.g., "Scout Worker")
            trust_score: TSPA score (0.0-1.0), must be >= 0.6 to execute
            max_retries: Maximum retry attempts before escalation
        """
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.trust_score = min(1.0, max(0.0, trust_score))
        self.max_retries = max(1, max_retries)
        self.logger = logging.getLogger(f"adrion.agents.{agent_id}")
        self.metrics = AgentMetrics()

        # Validate TSPA
        if self.trust_score < self.TSPA_MINIMUM:
            self.logger.error(
                "Agent blocked: trust_score %.2f < minimum %.2f",
                self.trust_score,
                self.TSPA_MINIMUM,
            )

    @abstractmethod
    async def execute(self, input_data: dict) -> dict:
        """Execute agent's business logic autonomously.

        Must be implemented by subclasses.

        Args:
            input_data: Input data for the agent's operation

        Returns:
            Result dictionary with outcome of execution

        Raises:
            Exception: Any execution errors (caught by run_with_retry)
        """
        pass

    async def run_with_retry(
        self,
        input_data: dict,
        max_retries: Optional[int] = None,
    ) -> dict:
        """Execute agent task with exponential backoff retry and escalation.

        Implements:
        1. TSPA validation (blocks if trust_score < 0.6)
        2. Task execution with exception handling
        3. Exponential backoff retry (2^attempt seconds)
        4. HEALER-MCP escalation on max retry failure
        5. Metrics tracking

        Args:
            input_data: Input data for execution
            max_retries: Override default max_retries

        Returns:
            dict with structure:
            {
                "success": bool,
                "agent_id": str,
                "attempt": int,
                "duration_ms": float,
                "result": dict | None,
                "error": str | None,
            }
        """
        # Validate TSPA
        if self.trust_score < self.TSPA_MINIMUM:
            error_msg = (
                f"Agent blocked by TSPA: score {self.trust_score:.2f} < "
                f"minimum {self.TSPA_MINIMUM}"
            )
            self.logger.error(error_msg)
            self.metrics.update_failure(error_msg)
            return {
                "success": False,
                "agent_id": self.agent_id,
                "attempt": 0,
                "duration_ms": 0.0,
                "result": None,
                "error": "TSPA_BLOCKED",
            }

        max_attempts = max_retries or self.max_retries

        for attempt in range(max_attempts):
            start_time = time.time()

            try:
                self.logger.info(
                    "Executing task (attempt %d/%d)",
                    attempt + 1,
                    max_attempts,
                )

                result = await self.execute(input_data)

                duration_ms = (time.time() - start_time) * 1000
                self.metrics.update_success(duration_ms)

                self.logger.info(
                    "Task completed: success, duration=%.1f ms",
                    duration_ms,
                )

                return {
                    "success": True,
                    "agent_id": self.agent_id,
                    "attempt": attempt + 1,
                    "duration_ms": duration_ms,
                    "result": result,
                    "error": None,
                }

            except Exception as exc:
                duration_ms = (time.time() - start_time) * 1000
                error_msg = str(exc)

                self.logger.warning(
                    "Task failed (attempt %d/%d): %s",
                    attempt + 1,
                    max_attempts,
                    error_msg,
                )

                # If last attempt, escalate to HEALER-MCP
                if attempt == max_attempts - 1:
                    self.logger.error(
                        "Max attempts exceeded. Escalating to HEALER-MCP..."
                    )
                    escalation_result = await self._escalate_to_healer(
                        error_msg,
                        input_data,
                    )
                    self.metrics.update_failure(error_msg)
                    return escalation_result

                # Exponential backoff
                backoff_seconds = 2 ** attempt
                self.logger.info(
                    "Backing off for %d seconds before retry...",
                    backoff_seconds,
                )
                await asyncio.sleep(backoff_seconds)

        # Should not reach here, but cover edge case
        self.metrics.update_failure("Unknown error")
        return {
            "success": False,
            "agent_id": self.agent_id,
            "attempt": max_attempts,
            "duration_ms": 0.0,
            "result": None,
            "error": "MAX_RETRIES_EXCEEDED",
        }

    async def _escalate_to_healer(
        self,
        error_msg: str,
        input_data: dict,
    ) -> dict:
        """Escalate failed task to HEALER-MCP for crisis recovery.

        HEALER-MCP handles:
        - System health assessment
        - Resource recovery
        - Agent reassignment recommendation
        - Crisis mode detection (Arousal > 0.7)

        Args:
            error_msg: Error message from failed task
            input_data: Input data that caused failure

        Returns:
            Recovery recommendation dict from HEALER-MCP
        """
        try:
            # TODO: Contact HEALER-MCP at mcp_servers/healer_mcp.py
            # For now, return graceful failure state
            self.logger.warning(
                "HEALER-MCP escalation called (not yet connected): %s",
                error_msg,
            )

            return {
                "success": False,
                "agent_id": self.agent_id,
                "attempt": self.max_retries,
                "duration_ms": 0.0,
                "result": None,
                "error": "HEALER_ESCALATION",
                "escalation": {
                    "original_error": error_msg,
                    "healer_status": "pending_connection",
                    "recommend_reassign": True,
                },
            }

        except Exception as healer_exc:
            self.logger.error(
                "HEALER escalation failed: %s",
                str(healer_exc),
            )
            return {
                "success": False,
                "agent_id": self.agent_id,
                "attempt": self.max_retries,
                "duration_ms": 0.0,
                "result": None,
                "error": "HEALER_ESCALATION_FAILED",
            }

    def get_metrics_dict(self) -> dict:
        """Get agent metrics as a dictionary.

        Returns:
            dict with all performance metrics
        """
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "trust_score": self.trust_score,
            "tasks_completed": self.metrics.tasks_completed,
            "tasks_failed": self.metrics.tasks_failed,
            "success_rate": round(self.metrics.success_rate, 4),
            "avg_duration_ms": round(self.metrics.avg_duration_ms, 2),
            "total_duration_ms": round(self.metrics.total_duration_ms, 2),
            "last_error": self.metrics.last_error,
        }

    def __repr__(self) -> str:
        """String representation of agent."""
        return (
            f"<{self.agent_name} "
            f"id={self.agent_id} "
            f"trust={self.trust_score:.2f} "
            f"success_rate={self.metrics.success_rate:.1%}>"
        )
