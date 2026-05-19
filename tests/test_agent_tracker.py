"""Tests for AgentPerformanceTracker — Metrics collection and reporting

Covers:
  - Agent metrics recording
  - Session metrics recording
  - Bottleneck detection
  - Prometheus metrics export
  - Report generation
"""

import pytest
from datetime import datetime
from arbitrage.agents.agent_tracker import (
    AgentPerformanceTracker,
    AgentSnapshot,
    SessionSnapshot,
)


# ─────────────────────────────────────────────────────────────────
# Initialization Tests
# ─────────────────────────────────────────────────────────────────


def test_tracker_initialization():
    """Test tracker initializes correctly."""
    tracker = AgentPerformanceTracker("session-001")

    assert tracker.session_id == "session-001"
    assert len(tracker.agent_snapshots) == 0
    assert len(tracker.session_snapshots) == 0
    assert tracker.start_time is not None


# ─────────────────────────────────────────────────────────────────
# Agent Metrics Recording Tests
# ─────────────────────────────────────────────────────────────────


def test_record_agent_metrics():
    """Test recording agent metrics snapshot."""
    tracker = AgentPerformanceTracker("session-001")

    metrics = {
        "agent_id": "scout-001",
        "agent_name": "Scout Worker",
        "trust_score": 0.92,
        "tasks_completed": 10,
        "tasks_failed": 0,
        "success_rate": 1.0,
        "avg_duration_ms": 150.5,
        "total_duration_ms": 1505.0,
    }

    tracker.record_agent_metrics("scout-001", metrics)

    assert len(tracker.agent_snapshots) == 1
    snapshot = tracker.agent_snapshots[0]
    assert snapshot.agent_id == "scout-001"
    assert snapshot.success_rate == 1.0
    assert snapshot.avg_duration_ms == 150.5


def test_record_multiple_agent_metrics():
    """Test recording metrics for multiple agents."""
    tracker = AgentPerformanceTracker("session-001")

    agents = ["scout-001", "analyze-001", "bid-001", "track-001"]
    for agent_id in agents:
        metrics = {
            "agent_id": agent_id,
            "agent_name": f"Agent {agent_id}",
            "trust_score": 0.9,
            "tasks_completed": 5,
            "tasks_failed": 0,
            "success_rate": 1.0,
            "avg_duration_ms": 100.0,
            "total_duration_ms": 500.0,
        }
        tracker.record_agent_metrics(agent_id, metrics)

    assert len(tracker.agent_snapshots) == 4


# ─────────────────────────────────────────────────────────────────
# Session Metrics Recording Tests
# ─────────────────────────────────────────────────────────────────


def test_record_session_metrics():
    """Test recording session metrics."""
    tracker = AgentPerformanceTracker("session-001")

    session_result = {
        "session_id": "session-001",
        "duration_ms": 5000.0,
        "summary": {
            "jobs_processed": 10,
            "jobs_worthy": 8,
            "bids_created": 8,
            "parallel_factor": 2.5,
            "throughput_jobs_per_sec": 2.0,
        },
        "status": "completed",
    }

    tracker.record_session_metrics(session_result)

    assert len(tracker.session_snapshots) == 1
    snapshot = tracker.session_snapshots[0]
    assert snapshot.jobs_processed == 10
    assert snapshot.jobs_worthy == 8
    assert snapshot.parallel_factor == 2.5


# ─────────────────────────────────────────────────────────────────
# Agent Statistics Tests
# ─────────────────────────────────────────────────────────────────


def test_get_agent_statistics():
    """Test aggregating agent statistics."""
    tracker = AgentPerformanceTracker("session-001")

    # Record multiple metrics for same agent
    for i in range(3):
        metrics = {
            "agent_id": "scout-001",
            "agent_name": "Scout Worker",
            "trust_score": 0.92,
            "tasks_completed": 10 + i,
            "tasks_failed": i,
            "success_rate": 0.95,
            "avg_duration_ms": 150.0 + (i * 10),
            "total_duration_ms": 1500.0 + (i * 100),
        }
        tracker.record_agent_metrics("scout-001", metrics)

    stats = tracker.get_agent_statistics("scout-001")

    assert stats["agent_id"] == "scout-001"
    assert stats["snapshots_count"] == 3
    assert "avg_success_rate" in stats
    assert "avg_duration_ms" in stats
    assert "total_tasks_completed" in stats
    assert "total_tasks_failed" in stats


def test_get_all_agents_statistics():
    """Test getting statistics for all agents."""
    tracker = AgentPerformanceTracker("session-001")

    agents = ["scout-001", "analyze-001", "bid-001"]
    for agent_id in agents:
        metrics = {
            "agent_id": agent_id,
            "agent_name": agent_id,
            "trust_score": 0.9,
            "tasks_completed": 5,
            "tasks_failed": 0,
            "success_rate": 1.0,
            "avg_duration_ms": 100.0,
            "total_duration_ms": 500.0,
        }
        tracker.record_agent_metrics(agent_id, metrics)

    # Get stats for all agents
    unique_agents = set(s.agent_id for s in tracker.agent_snapshots)
    assert len(unique_agents) == 3


# ─────────────────────────────────────────────────────────────────
# Bottleneck Detection Tests
# ─────────────────────────────────────────────────────────────────


def test_detect_low_success_rate():
    """Test detection of low success rate."""
    tracker = AgentPerformanceTracker("session-001")

    metrics = {
        "agent_id": "analyze-001",
        "agent_name": "Analyzer",
        "trust_score": 0.88,
        "tasks_completed": 5,
        "tasks_failed": 15,  # 25% success rate
        "success_rate": 0.25,
        "avg_duration_ms": 200.0,
        "total_duration_ms": 1000.0,
    }
    tracker.record_agent_metrics("analyze-001", metrics)

    bottlenecks = tracker.detect_bottlenecks()

    assert len(bottlenecks) > 0
    low_success = [b for b in bottlenecks if b["type"] == "low_success_rate"]
    assert len(low_success) > 0
    assert low_success[0]["severity"] == "warning"


def test_detect_high_latency():
    """Test detection of high latency."""
    tracker = AgentPerformanceTracker("session-001")

    metrics = {
        "agent_id": "bid-001",
        "agent_name": "Bidder",
        "trust_score": 0.90,
        "tasks_completed": 10,
        "tasks_failed": 0,
        "success_rate": 1.0,
        "avg_duration_ms": 2000.0,  # 2 seconds
        "total_duration_ms": 20000.0,
    }
    tracker.record_agent_metrics("bid-001", metrics)

    bottlenecks = tracker.detect_bottlenecks()

    high_latency = [b for b in bottlenecks if b["type"] == "high_latency"]
    assert len(high_latency) > 0
    assert high_latency[0]["severity"] == "warning"


def test_detect_high_failure_rate():
    """Test detection of high failure rate."""
    tracker = AgentPerformanceTracker("session-001")

    metrics = {
        "agent_id": "track-001",
        "agent_name": "Tracker",
        "trust_score": 0.85,
        "tasks_completed": 5,
        "tasks_failed": 45,  # 90% failure rate
        "success_rate": 0.1,
        "avg_duration_ms": 100.0,
        "total_duration_ms": 500.0,
    }
    tracker.record_agent_metrics("track-001", metrics)

    bottlenecks = tracker.detect_bottlenecks()

    high_failures = [b for b in bottlenecks if b["type"] == "high_failure_rate"]
    assert len(high_failures) > 0
    assert high_failures[0]["severity"] == "critical"


def test_no_bottlenecks_when_healthy():
    """Test no bottlenecks detected when all metrics are healthy."""
    tracker = AgentPerformanceTracker("session-001")

    metrics = {
        "agent_id": "scout-001",
        "agent_name": "Scout",
        "trust_score": 0.92,
        "tasks_completed": 20,
        "tasks_failed": 0,
        "success_rate": 1.0,
        "avg_duration_ms": 100.0,
        "total_duration_ms": 2000.0,
    }
    tracker.record_agent_metrics("scout-001", metrics)

    bottlenecks = tracker.detect_bottlenecks()

    assert len(bottlenecks) == 0


# ─────────────────────────────────────────────────────────────────
# Prometheus Metrics Export Tests
# ─────────────────────────────────────────────────────────────────


def test_export_prometheus_metrics():
    """Test exporting metrics in Prometheus format."""
    tracker = AgentPerformanceTracker("session-001")

    metrics = {
        "agent_id": "scout-001",
        "agent_name": "Scout",
        "trust_score": 0.92,
        "tasks_completed": 10,
        "tasks_failed": 0,
        "success_rate": 1.0,
        "avg_duration_ms": 150.0,
        "total_duration_ms": 1500.0,
    }
    tracker.record_agent_metrics("scout-001", metrics)

    prometheus_text = tracker.export_prometheus_metrics()

    assert isinstance(prometheus_text, str)
    assert 'agent_success_rate{agent_id="scout-001"}' in prometheus_text
    assert 'agent_avg_duration_ms{agent_id="scout-001"}' in prometheus_text
    assert 'agent_tasks_completed{agent_id="scout-001"}' in prometheus_text


def test_prometheus_format_valid():
    """Test Prometheus format is valid."""
    tracker = AgentPerformanceTracker("session-001")

    metrics = {
        "agent_id": "analyze-001",
        "agent_name": "Analyzer",
        "trust_score": 0.88,
        "tasks_completed": 5,
        "tasks_failed": 0,
        "success_rate": 1.0,
        "avg_duration_ms": 200.0,
        "total_duration_ms": 1000.0,
    }
    tracker.record_agent_metrics("analyze-001", metrics)

    session_result = {
        "session_id": "session-001",
        "duration_ms": 5000.0,
        "summary": {
            "jobs_processed": 10,
            "jobs_worthy": 8,
            "bids_created": 8,
            "parallel_factor": 2.5,
            "throughput_jobs_per_sec": 2.0,
        },
        "status": "completed",
    }
    tracker.record_session_metrics(session_result)

    prometheus_text = tracker.export_prometheus_metrics()

    # Check format: metric_name{labels} value
    lines = prometheus_text.split("\n")
    for line in lines:
        if line.strip():
            assert "{" in line or " " in line  # Either labels or space before value


# ─────────────────────────────────────────────────────────────────
# Report Generation Tests
# ─────────────────────────────────────────────────────────────────


def test_generate_report():
    """Test generating comprehensive performance report."""
    tracker = AgentPerformanceTracker("session-001")

    # Record some metrics
    metrics = {
        "agent_id": "scout-001",
        "agent_name": "Scout",
        "trust_score": 0.92,
        "tasks_completed": 10,
        "tasks_failed": 0,
        "success_rate": 1.0,
        "avg_duration_ms": 150.0,
        "total_duration_ms": 1500.0,
    }
    tracker.record_agent_metrics("scout-001", metrics)

    session_result = {
        "session_id": "session-001",
        "duration_ms": 5000.0,
        "summary": {
            "jobs_processed": 10,
            "jobs_worthy": 8,
            "bids_created": 8,
            "parallel_factor": 2.5,
            "throughput_jobs_per_sec": 2.0,
        },
        "status": "completed",
    }
    tracker.record_session_metrics(session_result)

    report = tracker.generate_report()

    assert report["session_id"] == "session-001"
    assert "uptime_seconds" in report
    assert "agents" in report
    assert "session_latest" in report
    assert "bottlenecks" in report
    assert "health_summary" in report
    assert "prometheus_metrics" in report


def test_health_summary_healthy():
    """Test health summary shows healthy when no bottlenecks."""
    tracker = AgentPerformanceTracker("session-001")

    metrics = {
        "agent_id": "scout-001",
        "agent_name": "Scout",
        "trust_score": 0.92,
        "tasks_completed": 20,
        "tasks_failed": 0,
        "success_rate": 1.0,
        "avg_duration_ms": 100.0,
        "total_duration_ms": 2000.0,
    }
    tracker.record_agent_metrics("scout-001", metrics)

    report = tracker.generate_report()

    assert report["health_summary"] == "healthy"


def test_health_summary_warning():
    """Test health summary shows warning for minor issues."""
    tracker = AgentPerformanceTracker("session-001")

    # High success rate (95%) but high latency (1200ms) - should trigger warning
    metrics = {
        "agent_id": "analyze-001",
        "agent_name": "Analyzer",
        "trust_score": 0.88,
        "tasks_completed": 100,
        "tasks_failed": 5,  # 95% success rate - above 80% threshold
        "success_rate": 0.95,
        "avg_duration_ms": 1200.0,  # Just over 1000ms latency threshold
        "total_duration_ms": 120000.0,
    }
    tracker.record_agent_metrics("analyze-001", metrics)

    report = tracker.generate_report()

    assert report["health_summary"] == "warning"


def test_health_summary_critical():
    """Test health summary shows critical for major issues."""
    tracker = AgentPerformanceTracker("session-001")

    metrics = {
        "agent_id": "track-001",
        "agent_name": "Tracker",
        "trust_score": 0.85,
        "tasks_completed": 1,
        "tasks_failed": 19,  # High failure rate
        "success_rate": 0.05,
        "avg_duration_ms": 100.0,
        "total_duration_ms": 500.0,
    }
    tracker.record_agent_metrics("track-001", metrics)

    report = tracker.generate_report()

    assert report["health_summary"] == "critical"


# ─────────────────────────────────────────────────────────────────
# Integration Tests
# ─────────────────────────────────────────────────────────────────


def test_full_tracking_workflow():
    """Test complete tracking workflow: record → analyze → report."""
    tracker = AgentPerformanceTracker("full-workflow")

    # 1. Record metrics from multiple agents
    agents_data = [
        ("scout-001", 0.92, 100, 0, 1.0, 150.0),
        ("analyze-001", 0.88, 50, 5, 0.9, 300.0),
        ("bid-001", 0.90, 80, 2, 0.97, 200.0),
        ("track-001", 0.85, 60, 10, 0.86, 100.0),
    ]

    for agent_id, trust, completed, failed, success, duration in agents_data:
        metrics = {
            "agent_id": agent_id,
            "agent_name": agent_id,
            "trust_score": trust,
            "tasks_completed": completed,
            "tasks_failed": failed,
            "success_rate": success,
            "avg_duration_ms": duration,
            "total_duration_ms": duration * max(completed, 1),
        }
        tracker.record_agent_metrics(agent_id, metrics)

    # 2. Record session metrics
    session_result = {
        "session_id": "full-workflow",
        "duration_ms": 10000.0,
        "summary": {
            "jobs_processed": 100,
            "jobs_worthy": 85,
            "bids_created": 82,
            "parallel_factor": 3.0,
            "throughput_jobs_per_sec": 10.0,
        },
        "status": "completed",
    }
    tracker.record_session_metrics(session_result)

    # 3. Generate report
    report = tracker.generate_report()

    # 4. Verify report completeness
    assert len(report["agents"]) == 4
    assert report["session_latest"]["jobs_processed"] == 100
    assert report["health_summary"] in ["healthy", "warning", "critical"]
    assert len(report["prometheus_metrics"]) > 0
