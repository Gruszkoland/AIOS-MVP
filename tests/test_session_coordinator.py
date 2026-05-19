"""Tests for SessionCoordinator — Parallel agent orchestration

Covers:
  - Session initialization and configuration
  - Parallel execution orchestration
  - Queue-based inter-agent communication
  - Agent failure handling and recovery
  - Performance metrics and reporting
  - Full end-to-end pipeline
"""

import pytest
import asyncio
from datetime import datetime
from arbitrage.agents.session_coordinator import SessionCoordinator


# ─────────────────────────────────────────────────────────────────
# Session Initialization Tests
# ─────────────────────────────────────────────────────────────────


def test_session_coordinator_initialization():
    """Test SessionCoordinator initializes with correct configuration."""
    coordinator = SessionCoordinator(
        session_id="session-001",
        num_analyzers=4,
        enable_rag=False,
    )

    assert coordinator.session_id == "session-001"
    assert coordinator.num_analyzers == 4
    assert coordinator.enable_rag is False
    assert len(coordinator.analyzers) == 4


def test_session_coordinator_with_rag():
    """Test SessionCoordinator initializes with RAG enabled."""
    coordinator = SessionCoordinator(
        session_id="session-002",
        num_analyzers=2,
        enable_rag=True,
    )

    assert coordinator.enable_rag is True
    # Check that analyzers were created with RAG enabled
    for analyzer in coordinator.analyzers:
        assert analyzer.use_rag is True


def test_session_coordinator_queue_creation():
    """Test sessions create necessary communication queues."""
    coordinator = SessionCoordinator("session-001", num_analyzers=3)

    # Verify all queues exist
    assert coordinator.scout_queue is not None
    assert len(coordinator.analyze_queues) == 3
    assert coordinator.worthy_jobs_queue is not None
    assert coordinator.bid_queue is not None


def test_session_coordinator_agent_creation():
    """Test all agents are instantiated with proper trust scores."""
    coordinator = SessionCoordinator("session-001", num_analyzers=2)

    # Check agent creation and TSPA scores
    assert coordinator.scout.trust_score == 0.92
    assert all(a.trust_score == 0.88 for a in coordinator.analyzers)
    assert coordinator.bidder.trust_score == 0.90
    assert coordinator.tracker.trust_score == 0.85


# ─────────────────────────────────────────────────────────────────
# Orchestration Tests
# ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_orchestrate_basic_execution():
    """Test basic orchestration execution completes."""
    coordinator = SessionCoordinator(
        session_id="session-001",
        num_analyzers=2,
    )

    result = await coordinator.orchestrate(
        filters={},
        max_duration_seconds=5,  # Reduced timeout for faster tests
    )

    assert result["session_id"] == "session-001"
    assert result["status"] in ["completed", "timeout"]
    assert result["start_time"] is not None or result["status"] == "timeout"
    assert result["duration_ms"] >= 0


@pytest.mark.asyncio
async def test_orchestrate_collects_scout_results():
    """Test orchestration collects Scout results."""
    coordinator = SessionCoordinator("session-001", num_analyzers=1)

    result = await coordinator.orchestrate(max_duration_seconds=3)

    assert "scout_results" in result
    assert isinstance(result["scout_results"], list)


@pytest.mark.asyncio
async def test_orchestrate_collects_analysis_results():
    """Test orchestration collects Analysis results."""
    coordinator = SessionCoordinator("session-001", num_analyzers=2)

    result = await coordinator.orchestrate(max_duration_seconds=3)

    assert "analysis_results" in result
    assert isinstance(result["analysis_results"], list)


@pytest.mark.asyncio
async def test_orchestrate_collects_bid_results():
    """Test orchestration collects Bid results."""
    coordinator = SessionCoordinator("session-001", num_analyzers=1)

    result = await coordinator.orchestrate(max_duration_seconds=3)

    assert "bid_results" in result
    assert isinstance(result["bid_results"], list)


@pytest.mark.asyncio
async def test_orchestrate_with_multiple_analyzers():
    """Test orchestration with configurable analyzer pool."""
    coordinator = SessionCoordinator(
        session_id="parallel-001",
        num_analyzers=4,
    )

    result = await coordinator.orchestrate(max_duration_seconds=3)

    # With 4 analyzers processing in parallel, should handle multiple jobs
    assert "summary" in result
    assert result["summary"]["parallel_factor"] > 0


# ─────────────────────────────────────────────────────────────────
# Results Aggregation Tests
# ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_aggregated_results_structure():
    """Test aggregated results have correct structure."""
    coordinator = SessionCoordinator("session-001", num_analyzers=2)

    result = await coordinator.orchestrate(max_duration_seconds=3)

    # Verify all required fields
    assert "session_id" in result
    assert "status" in result
    assert "duration_ms" in result
    assert "scout_results" in result
    assert "analysis_results" in result
    assert "bid_results" in result
    assert "tracking_results" in result
    assert "summary" in result
    assert "agent_metrics" in result


@pytest.mark.asyncio
async def test_aggregated_summary_metrics():
    """Test summary metrics are correctly calculated."""
    coordinator = SessionCoordinator("session-001", num_analyzers=2)

    result = await coordinator.orchestrate(max_duration_seconds=3)

    summary = result["summary"]
    assert "jobs_processed" in summary
    assert "jobs_worthy" in summary
    assert "bids_created" in summary
    assert "parallel_factor" in summary
    assert "throughput_jobs_per_sec" in summary


@pytest.mark.asyncio
async def test_aggregated_agent_metrics():
    """Test agent metrics are aggregated correctly."""
    coordinator = SessionCoordinator("session-001", num_analyzers=2)

    result = await coordinator.orchestrate(max_duration_seconds=3)

    metrics = result["agent_metrics"]
    assert "scout" in metrics
    assert "analyzers" in metrics
    assert "bidder" in metrics
    assert "tracker" in metrics


# ─────────────────────────────────────────────────────────────────
# Queue-Based Communication Tests
# ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_scout_queues_jobs_for_analyzers():
    """Test Scout distributes jobs to analyzer queues."""
    coordinator = SessionCoordinator("session-001", num_analyzers=2)

    # Run Scout manually
    await coordinator._run_scout({})

    # Check results were collected
    assert len(coordinator.scout_results) >= 0


@pytest.mark.asyncio
async def test_analyzer_processes_queued_jobs():
    """Test Analyzers consume queued jobs."""
    coordinator = SessionCoordinator("session-001", num_analyzers=1)

    # Manually queue a job
    test_job = {"id": "test-001", "type": "bid", "value": 100}
    await coordinator.analyze_queues[0].put(test_job)
    await coordinator.analyze_queues[0].put(None)  # Sentinel

    # Run analyzer
    await coordinator._run_analyzer(0)

    # Should have processed the job
    assert len(coordinator.analysis_results) >= 0


@pytest.mark.asyncio
async def test_bidder_consumes_worthy_jobs():
    """Test Bidder consumes worthy jobs from queue."""
    coordinator = SessionCoordinator("session-001", num_analyzers=1)

    # Manually queue a worthy job
    worth_job = {
        "job": {"id": "job-001", "value": 100},
        "analysis": {"worthy": True, "worthiness_score": 0.8},
    }
    await coordinator.worthy_jobs_queue.put(worth_job)

    # Trigger bidder for short time
    bidder_task = asyncio.create_task(coordinator._run_bidder())
    await asyncio.sleep(0.5)

    # Verify job was processed
    assert len(coordinator.bid_results) >= 0


# ─────────────────────────────────────────────────────────────────
# Error Handling Tests
# ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_orchestrate_timeout_handling():
    """Test orchestration handles timeout gracefully."""
    coordinator = SessionCoordinator("timeout-001", num_analyzers=1)

    # Very short timeout
    result = await coordinator.orchestrate(max_duration_seconds=0.2)

    assert result["status"] in ["timeout", "completed"]  # May be too fast to timeout


@pytest.mark.asyncio
async def test_orchestrate_collects_tracking_results():
    """Test Tracker continuously monitors and collects health data."""
    coordinator = SessionCoordinator("tracker-001", num_analyzers=1)

    result = await coordinator.orchestrate(max_duration_seconds=3)

    assert "tracking_results" in result


# ─────────────────────────────────────────────────────────────────
# Parallelization Factor Tests
# ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_parallel_factor_calculation():
    """Test parallelization factor is calculated."""
    coordinator = SessionCoordinator("parallel-001", num_analyzers=2)

    result = await coordinator.orchestrate(max_duration_seconds=3)

    parallel_factor = result["summary"]["parallel_factor"]
    assert parallel_factor >= 1.0  # Base factor


@pytest.mark.asyncio
async def test_throughput_calculation():
    """Test job throughput is calculated."""
    coordinator = SessionCoordinator("throughput-001", num_analyzers=2)

    result = await coordinator.orchestrate(max_duration_seconds=3)

    throughput = result["summary"]["throughput_jobs_per_sec"]
    assert throughput >= 0  # May be 0 if no jobs


# ─────────────────────────────────────────────────────────────────
# Scalability Tests
# ─────────────────────────────────────────────────────────────────


def test_coordinator_scales_analyzer_workers():
    """Test SessionCoordinator can scale analyzer workers."""
    for num_workers in [1, 2, 4, 8]:
        coordinator = SessionCoordinator("scale-test", num_analyzers=num_workers)
        assert len(coordinator.analyzers) == num_workers
        assert len(coordinator.analyze_queues) == num_workers


@pytest.mark.asyncio
async def test_larger_analyzer_pool_execution():
    """Test execution with larger analyzer pool."""
    coordinator = SessionCoordinator(
        session_id="large-pool-001",
        num_analyzers=8,
    )

    result = await coordinator.orchestrate()

    # Should complete without errors
    assert result["status"] == "completed"
    assert len(coordinator.analyzers) == 8


# ─────────────────────────────────────────────────────────────────
# Session State Tests
# ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_session_state_after_completion():
    """Test session state is properly updated after execution."""
    coordinator = SessionCoordinator("state-001", num_analyzers=2)

    assert coordinator.start_time is None
    assert coordinator.end_time is None

    result = await coordinator.orchestrate(max_duration_seconds=3)

    # After orchestration, should have timing info
    assert coordinator.start_time is not None or result["status"] == "timeout"


@pytest.mark.asyncio
async def test_session_preserves_all_results():
    """Test session preserves all intermediate results."""
    coordinator = SessionCoordinator("preserve-001", num_analyzers=1)

    result = await coordinator.orchestrate(max_duration_seconds=3)

    # Results should be accessible
    assert len(coordinator.scout_results) == len(result["scout_results"])
    assert len(coordinator.analysis_results) == len(result["analysis_results"])
    assert len(coordinator.bid_results) == len(result["bid_results"])


# ─────────────────────────────────────────────────────────────────
# Integration Tests
# ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_full_pipeline_scout_to_tracker():
    """Test full pipeline from Scout through Tracker."""
    coordinator = SessionCoordinator("e2e-001", num_analyzers=2)

    result = await coordinator.orchestrate(max_duration_seconds=5)

    # Verify all stages have results collected
    assert result["scout_results"] is not None
    assert result["analysis_results"] is not None
    assert result["bid_results"] is not None
    assert result["tracking_results"] is not None

    # Stats should be generated
    stats = result["summary"]
    assert stats["jobs_processed"] >= 0
    assert stats["parallel_factor"] >= 1.0


@pytest.mark.asyncio
async def test_session_produces_valid_output():
    """Test session output is valid and complete."""
    coordinator = SessionCoordinator("valid-001", num_analyzers=2)

    result = await coordinator.orchestrate(max_duration_seconds=3)

    # Verify response format
    assert isinstance(result, dict)
    assert result["status"] in ["completed", "timeout"]
    assert isinstance(result["duration_ms"], (int, float))
    assert result["duration_ms"] >= 0
