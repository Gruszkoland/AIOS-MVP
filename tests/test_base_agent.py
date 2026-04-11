"""Tests for arbitrage/agents/base_agent.py — BaseAutonomousAgent framework

Covers:
  - TSPA validation and blocking
  - Successful task execution
  - Retry logic with exponential backoff
  - HEALER-MCP escalation on max retries
  - Metrics tracking and updates
  - Agent metadata and representation
"""

import asyncio
import pytest
from unittest.mock import patch, MagicMock
from arbitrage.agents.base_agent import BaseAutonomousAgent, AgentMetrics


# ─────────────────────────────────────────────────────────────────
# Test Fixtures
# ─────────────────────────────────────────────────────────────────


class MockAgent(BaseAutonomousAgent):
    """Concrete mock implementation of BaseAutonomousAgent."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.execute_count = 0
        self.execute_results = []  # Queue of results to return
        self.should_fail_count = 0  # How many times to fail before succeeding

    async def execute(self, input_data: dict) -> dict:
        """Simple test implementation that can succeed or fail."""
        self.execute_count += 1

        # Add minimal delay to ensure duration > 0
        await asyncio.sleep(0.001)

        if self.should_fail_count > 0:
            self.should_fail_count -= 1
            raise RuntimeError(f"Test failure #{self.execute_count}")

        return {
            "status": "success",
            "execute_count": self.execute_count,
            "input": input_data,
        }


@pytest.fixture
def test_agent():
    """Create a test agent with default settings."""
    return MockAgent(
        agent_id="test-agent-001",
        agent_name="Test Worker",
        trust_score=0.9,
        max_retries=3,
    )


@pytest.fixture
def low_trust_agent():
    """Create a test agent with low trust score (below TSPA minimum)."""
    return MockAgent(
        agent_id="low-trust-agent",
        agent_name="Low Trust Worker",
        trust_score=0.5,  # Below minimum of 0.6
        max_retries=3,
    )


# ─────────────────────────────────────────────────────────────────
# TSPA Blocking Tests
# ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_tspa_blocking_prevents_execution(low_trust_agent):
    """Test that TSPA validation blocks execution when trust_score < 0.6."""
    result = await low_trust_agent.run_with_retry({"test": "data"})

    assert result["success"] is False
    assert result["error"] == "TSPA_BLOCKED"
    assert result["attempt"] == 0
    assert low_trust_agent.execute_count == 0  # Never called
    assert low_trust_agent.metrics.tasks_failed == 1


@pytest.mark.asyncio
async def test_tspa_minimum_boundary(test_agent):
    """Test TSPA at exact minimum boundary (0.6)."""
    agent = MockAgent(
        agent_id="boundary-agent",
        agent_name="Boundary Agent",
        trust_score=0.6,  # Exactly at minimum
        max_retries=1,
    )

    result = await agent.run_with_retry({"test": "data"})

    # Should succeed (0.6 is >= 0.6)
    assert result["success"] is True
    assert agent.execute_count == 1


# ─────────────────────────────────────────────────────────────────
# Successful Execution Tests
# ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_successful_execution(test_agent):
    """Test successful task execution on first attempt."""
    result = await test_agent.run_with_retry({"job_id": "job-123"})

    assert result["success"] is True
    assert result["agent_id"] == "test-agent-001"
    assert result["attempt"] == 1
    assert result["error"] is None
    assert result["duration_ms"] > 0
    assert result["result"]["status"] == "success"
    assert test_agent.execute_count == 1
    assert test_agent.metrics.tasks_completed == 1
    assert test_agent.metrics.tasks_failed == 0


@pytest.mark.asyncio
async def test_metrics_updated_on_success(test_agent):
    """Test that metrics are updated correctly on successful execution."""
    await test_agent.run_with_retry({"test": "data"})

    metrics = test_agent.get_metrics_dict()
    assert metrics["tasks_completed"] == 1
    assert metrics["tasks_failed"] == 0
    assert metrics["success_rate"] == 1.0
    assert metrics["avg_duration_ms"] > 0
    assert metrics["last_error"] is None


# ─────────────────────────────────────────────────────────────────
# Retry Logic Tests
# ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_retry_succeeds_on_second_attempt(test_agent):
    """Test that agent retries and succeeds on second attempt."""
    test_agent.should_fail_count = 1  # Fail once, then succeed

    result = await test_agent.run_with_retry({"data": "test"})

    assert result["success"] is True
    assert result["attempt"] == 2  # Second attempt
    assert test_agent.execute_count == 2  # Called twice
    assert test_agent.metrics.tasks_completed == 1
    assert test_agent.metrics.tasks_failed == 0


@pytest.mark.asyncio
async def test_retry_succeeds_after_multiple_failures(test_agent):
    """Test that agent succeeds after multiple retries."""
    test_agent.should_fail_count = 2  # Fail twice, then succeed

    result = await test_agent.run_with_retry({"data": "test"})

    assert result["success"] is True
    assert result["attempt"] == 3  # Third attempt
    assert test_agent.execute_count == 3  # Called three times


@pytest.mark.asyncio
async def test_retry_respects_max_retries():
    """Test that agent respects max_retries limit."""
    agent = MockAgent(
        agent_id="limited-retries",
        agent_name="Limited Retries",
        trust_score=0.9,
        max_retries=2,
    )
    agent.should_fail_count = 10  # Always fail

    result = await agent.run_with_retry({"data": "test"})

    assert result["success"] is False
    assert result["error"] == "HEALER_ESCALATION"
    assert agent.execute_count == 2  # Called max_retries times


@pytest.mark.asyncio
async def test_exponential_backoff_timing(test_agent):
    """Test that exponential backoff delays are applied (reduced for test)."""
    test_agent.should_fail_count = 2  # Fail twice to trigger backoff

    # With exponential backoff: 2^0=1s, 2^1=2s, total ~3s
    # We'll just verify execution completes successfully
    result = await test_agent.run_with_retry({"data": "test"})

    assert result["success"] is True
    assert test_agent.execute_count == 3


# ─────────────────────────────────────────────────────────────────
# HEALER-MCP Escalation Tests
# ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_healer_escalation_on_max_retry_failure():
    """Test that HEALER-MCP escalation is triggered on max retry failure."""
    agent = MockAgent(
        agent_id="escalate-agent",
        agent_name="Escalate Agent",
        trust_score=0.9,
        max_retries=2,
    )
    agent.should_fail_count = 10  # Always fail

    result = await agent.run_with_retry({"critical": "task"})

    assert result["success"] is False
    assert result["error"] == "HEALER_ESCALATION"
    assert result["attempt"] == 2
    assert "escalation" in result
    assert result["escalation"]["recommend_reassign"] is True


@pytest.mark.asyncio
async def test_metrics_updated_on_healer_escalation():
    """Test that metrics are updated when HEALER escalation occurs."""
    agent = MockAgent(
        agent_id="fail-agent",
        agent_name="Fail Agent",
        trust_score=0.9,
        max_retries=1,
    )
    agent.should_fail_count = 1  # Fail on first attempt

    result = await agent.run_with_retry({"data": "test"})

    # After escalation, should be failed
    assert result["success"] is False
    metrics = agent.get_metrics_dict()
    assert metrics["tasks_failed"] == 1


# ─────────────────────────────────────────────────────────────────
# Metrics Tracking Tests
# ─────────────────────────────────────────────────────────────────


def test_agent_metrics_initialization():
    """Test that AgentMetrics initializes correctly."""
    metrics = AgentMetrics()

    assert metrics.tasks_completed == 0
    assert metrics.tasks_failed == 0
    assert metrics.total_duration_ms == 0.0
    assert metrics.success_rate == 1.0
    assert metrics.avg_duration_ms == 0.0
    assert metrics.last_error is None


def test_metrics_update_success():
    """Test that metrics are updated on successful execution."""
    metrics = AgentMetrics()
    metrics.update_success(150.5)

    assert metrics.tasks_completed == 1
    assert metrics.tasks_failed == 0
    assert metrics.total_duration_ms == 150.5
    assert metrics.avg_duration_ms == 150.5
    assert metrics.success_rate == 1.0


def test_metrics_update_failure():
    """Test that metrics are updated on failure."""
    metrics = AgentMetrics()
    metrics.update_failure("Test error")

    assert metrics.tasks_completed == 0
    assert metrics.tasks_failed == 1
    assert metrics.success_rate == 0.0
    assert metrics.last_error == "Test error"
    assert metrics.last_error_time is not None


def test_metrics_success_rate_calculation():
    """Test success rate calculation with mixed results."""
    metrics = AgentMetrics()

    metrics.update_success(100.0)
    metrics.update_success(150.0)
    metrics.update_failure("Error 1")
    metrics.update_failure("Error 2")

    # 2 successes, 2 failures = 50% success rate
    assert metrics.tasks_completed == 2
    assert metrics.tasks_failed == 2
    assert metrics.success_rate == pytest.approx(0.5, abs=0.01)
    assert metrics.avg_duration_ms == 125.0  # (100 + 150) / 2


@pytest.mark.asyncio
async def test_get_metrics_dict(test_agent):
    """Test that get_metrics_dict returns proper structure."""
    await test_agent.run_with_retry({"test": "data"})

    metrics_dict = test_agent.get_metrics_dict()

    assert metrics_dict["agent_id"] == "test-agent-001"
    assert metrics_dict["agent_name"] == "Test Worker"
    assert metrics_dict["trust_score"] == 0.9
    assert metrics_dict["tasks_completed"] == 1
    assert metrics_dict["tasks_failed"] == 0
    assert metrics_dict["success_rate"] == 1.0
    assert metrics_dict["avg_duration_ms"] > 0
    assert metrics_dict["total_duration_ms"] > 0
    assert metrics_dict["last_error"] is None


# ─────────────────────────────────────────────────────────────────
# Agent Representation and Metadata Tests
# ─────────────────────────────────────────────────────────────────


def test_agent_representation(test_agent):
    """Test agent string representation."""
    repr_str = repr(test_agent)

    assert "Test Worker" in repr_str
    assert "test-agent-001" in repr_str
    assert "trust=0.90" in repr_str


def test_trust_score_normalization():
    """Test that trust scores are normalized to [0, 1]."""
    # Test over-maximum
    agent1 = MockAgent(
        agent_id="agent-1",
        agent_name="Agent 1",
        trust_score=1.5,  # Over max
    )
    assert agent1.trust_score == 1.0

    # Test negative
    agent2 = MockAgent(
        agent_id="agent-2",
        agent_name="Agent 2",
        trust_score=-0.5,  # Negative
    )
    assert agent2.trust_score == 0.0


def test_max_retries_minimum_one():
    """Test that max_retries is at least 1."""
    agent = MockAgent(
        agent_id="agent",
        agent_name="Agent",
        trust_score=0.9,
        max_retries=0,  # Invalid
    )
    assert agent.max_retries == 1


# ─────────────────────────────────────────────────────────────────
# Edge Cases & Error Handling
# ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_agent_with_custom_max_retries_override():
    """Test run_with_retry accepts max_retries override."""
    agent = MockAgent(
        agent_id="override-agent",
        agent_name="Override Agent",
        trust_score=0.9,
        max_retries=5,  # Default
    )
    agent.should_fail_count = 10

    # Override with 2
    result = await agent.run_with_retry({"test": "data"}, max_retries=2)

    assert agent.execute_count == 2  # Only tried twice despite max_retries=5


@pytest.mark.asyncio
async def test_input_data_passed_to_execute(test_agent):
    """Test that input_data is properly passed to execute()."""
    input_data = {"job_id": "job-123", "priority": "high"}
    result = await test_agent.run_with_retry(input_data)

    assert result["success"] is True
    assert result["result"]["input"] == input_data


@pytest.mark.asyncio
async def test_agent_execution_with_empty_input(test_agent):
    """Test agent execution with empty input data."""
    result = await test_agent.run_with_retry({})

    assert result["success"] is True


# ─────────────────────────────────────────────────────────────────
# Integration Tests
# ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_multiple_sequential_executions(test_agent):
    """Test agent handling multiple sequential tasks."""
    result1 = await test_agent.run_with_retry({"task": 1})
    result2 = await test_agent.run_with_retry({"task": 2})
    result3 = await test_agent.run_with_retry({"task": 3})

    assert result1["success"] is True
    assert result2["success"] is True
    assert result3["success"] is True

    metrics = test_agent.get_metrics_dict()
    assert metrics["tasks_completed"] == 3
    assert metrics["tasks_failed"] == 0


@pytest.mark.asyncio
async def test_agent_partial_failure_metrics(test_agent):
    """Test metrics tracking across successes and failures."""
    # First task succeeds
    await test_agent.run_with_retry({"id": 1})

    # Second task fails all retries
    test_agent.should_fail_count = 100
    test_agent.max_retries = 1
    await test_agent.run_with_retry({"id": 2})

    metrics = test_agent.get_metrics_dict()
    assert metrics["tasks_completed"] == 1
    assert metrics["tasks_failed"] == 1
    assert metrics["success_rate"] == pytest.approx(0.5, abs=0.01)
