"""Tests for autonomous agents (Scout, Analyze, Bid, Track)

Covers:
  - ScoutAgent: Job fetching, filtering, ranking
  - AnalyzeAgent: Trinity/Hexagon/Guardian evaluation, reasoning
  - BidAgent: Bid calculation, creation, submission
  - TrackAgent: Health monitoring, limits tracking, alerts
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from arbitrage.agents.scout_agent import ScoutAgent
from arbitrage.agents.analyze_agent import AnalyzeAgent
from arbitrage.agents.bid_agent import BidAgent
from arbitrage.agents.track_agent import TrackAgent


# ─────────────────────────────────────────────────────────────────
# ScoutAgent Tests
# ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_scout_successful_execution():
    """Test Scout agent successful execution."""
    scout = ScoutAgent()
    result = await scout.run_with_retry({})

    assert result["success"] is True
    assert "jobs_ready" in result["result"]
    assert result["result"]["jobs_fetched"] >= 0


@pytest.mark.asyncio
async def test_scout_fetch_jobs():
    """Test Scout fetches jobs from source."""
    scout = ScoutAgent()
    jobs = await scout._fetch_jobs({"status": "open"})

    assert isinstance(jobs, list)
    assert len(jobs) > 0
    assert all("id" in job for job in jobs)
    assert all("value" in job for job in jobs)


@pytest.mark.asyncio
async def test_scout_filter_jobs():
    """Test Scout filters jobs by criteria."""
    scout = ScoutAgent()
    mock_jobs = [
        {"id": "1", "status": "open", "value": 100, "type": "bid"},
        {"id": "2", "status": "open", "value": 50, "type": "bid"},
        {"id": "3", "status": "closed", "value": 200, "type": "bid"},
    ]

    filtered = await scout._filter_jobs(mock_jobs, {
        "status": "open",
        "min_value": 75,
    })

    assert len(filtered) == 1
    assert filtered[0]["id"] == "1"


@pytest.mark.asyncio
async def test_scout_rank_jobs():
    """Test Scout ranks jobs by priority."""
    scout = ScoutAgent()
    mock_jobs = [
        {"id": "1", "priority": "low", "value": 100},
        {"id": "2", "priority": "high", "value": 50},
        {"id": "3", "priority": "high", "value": 200},
    ]

    ranked = await scout._rank_jobs(mock_jobs)

    # High priority (2, 3) should come first, sorted by value (3, 2)
    assert ranked[0]["id"] == "3"  # High priority, high value
    assert ranked[1]["id"] == "2"  # High priority, low value
    assert ranked[2]["id"] == "1"  # Low priority


@pytest.mark.asyncio
async def test_scout_stats():
    """Test Scout tracking statistics."""
    scout = ScoutAgent()
    await scout.run_with_retry({})

    stats = scout.get_scout_stats()
    assert "agent_id" in stats
    assert "jobs_fetched_total" in stats
    assert "filter_ratio" in stats


# ─────────────────────────────────────────────────────────────────
# AnalyzeAgent Tests
# ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_analyze_execution_with_mock_trinity():
    """Test Analyzer execution with mocked Trinity."""
    analyzer = AnalyzeAgent()

    job = {
        "id": "job-001",
        "type": "bid_request",
        "title": "Test job",
        "value": 150,
    }

    result = await analyzer.run_with_retry({"job": job})

    assert result["success"] is True
    analysis = result["result"]
    assert analysis["job_id"] == "job-001"
    assert "worthy" in analysis
    assert "worthiness_score" in analysis


@pytest.mark.asyncio
async def test_analyze_mock_trinity_result():
    """Test Analyzer Trinity mock when module unavailable."""
    analyzer = AnalyzeAgent()
    trinity_result = analyzer._mock_trinity_result()

    assert "material" in trinity_result
    assert "intellectual" in trinity_result
    assert "essential" in trinity_result
    assert "overall" in trinity_result
    assert all(0 <= v <= 1 for v in trinity_result.values())


@pytest.mark.asyncio
async def test_analyze_mock_hexagon_result():
    """Test Analyzer Hexagon mock when module unavailable."""
    analyzer = AnalyzeAgent()
    hexagon_result = analyzer._mock_hexagon_result()

    assert "stages" in hexagon_result
    assert "combined_score" in hexagon_result
    assert "duration_ms" in hexagon_result
    assert "approved" in hexagon_result


@pytest.mark.asyncio
async def test_analyze_mock_guardian_result():
    """Test Analyzer Guardian mock when module unavailable."""
    analyzer = AnalyzeAgent()
    guardian_result = analyzer._mock_guardian_result()

    assert "laws_evaluated" in guardian_result
    assert "laws_passed" in guardian_result
    assert "violations" in guardian_result
    assert "approved" in guardian_result
    assert guardian_result["laws_evaluated"] == 9


@pytest.mark.asyncio
async def test_analyze_score_worthiness():
    """Test Analyzer worthiness scoring."""
    analyzer = AnalyzeAgent()

    trinity_result = {
        "material": 0.8,
        "intellectual": 0.7,
        "essential": 0.6,
        "overall": 0.7,
    }
    hexagon_result = {
        "combined_score": 0.75,
        "approved": True,
    }
    guardians_result = {
        "laws_evaluated": 9,
        "laws_passed": 9,
        "violations": 0,
        "approved": True,
    }

    worthiness = await analyzer._score_worthiness(
        trinity_result,
        hexagon_result,
        guardians_result,
    )

    assert 0.0 <= worthiness <= 1.0
    # With high scores, should be notable
    assert worthiness >= 0.5


@pytest.mark.asyncio
async def test_analyze_decision_reason():
    """Test Analyzer builds decision reason."""
    analyzer = AnalyzeAgent()

    trinity_result = {"overall": 0.8}
    hexagon_result = {"combined_score": 0.75}
    guardians_result = {
        "laws_evaluated": 9,
        "laws_passed": 9,
    }

    reason = await analyzer._build_decision_reason(
        worthy=True,
        worthiness_score=0.75,
        trinity_result=trinity_result,
        hexagon_result=hexagon_result,
        guardians_result=guardians_result,
    )

    assert isinstance(reason, str)
    assert "WORTHY" in reason
    assert "75" in reason  # Should contain percentage


@pytest.mark.asyncio
async def test_analyze_stats():
    """Test Analyzer tracking statistics."""
    analyzer = AnalyzeAgent()

    # Run a job
    job = {"id": "job-001"}
    await analyzer.run_with_retry({"job": job})

    stats = analyzer.get_analyzer_stats()
    assert stats["jobs_analyzed"] > 0
    assert "worthy_ratio" in stats


@pytest.mark.asyncio
async def test_analyze_missing_job_raises_error():
    """Test Analyzer handles missing job gracefully via HEALER escalation."""
    analyzer = AnalyzeAgent()

    result = await analyzer.run_with_retry({})  # No 'job' key

    # Should fail with HEALER escalation (not raise ValueError)
    assert result["success"] is False
    assert result["error"] == "HEALER_ESCALATION"


# ─────────────────────────────────────────────────────────────────
# BidAgent Tests
# ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_bid_successful_execution():
    """Test Bidder successful bid creation and submission."""
    bidder = BidAgent()

    job = {"id": "job-001", "value": 200}
    analysis = {"worthiness_score": 0.8}

    result = await bidder.run_with_retry({
        "job": job,
        "analysis": analysis,
    })

    assert result["success"] is True
    bid = result["result"]
    assert "bid_id" in bid
    assert bid["job_id"] == "job-001"
    assert bid["amount"] > 0


@pytest.mark.asyncio
async def test_bid_calculate_amount():
    """Test Bidder bid amount calculation."""
    bidder = BidAgent()

    job = {"value": 200}
    analysis = {"worthiness_score": 0.8}

    amount = await bidder._calculate_bid_amount(job, analysis)

    # Should be less than job value but substantial
    assert 0 < amount < job["value"]
    assert amount == pytest.approx(200 * 0.85 * (0.8 + 0.8 * 0.4), rel=0.01)


@pytest.mark.asyncio
async def test_bid_create_record():
    """Test Bidder bid record creation."""
    bidder = BidAgent()

    job = {"id": "job-001"}
    analysis = {"worthiness_score": 0.75}

    bid = await bidder._create_bid_record(job, analysis, 150.0)

    assert bid["job_id"] == "job-001"
    assert bid["amount"] == 150.0
    assert "id" in bid
    assert "created_at" in bid


@pytest.mark.asyncio
async def test_bid_submit():
    """Test Bidder bid submission."""
    bidder = BidAgent()

    bid = {
        "id": "bid-001",
        "job_id": "job-001",
        "amount": 150,
    }

    result = await bidder._submit_bid(bid)

    assert result["status"] == "submitted"
    assert "message" in result


@pytest.mark.asyncio
async def test_bid_escrow_setup():
    """Test Bidder escrow account setup."""
    bidder = BidAgent()

    bid = {"id": "bid-001"}
    escrow = await bidder._setup_escrow(bid, 150.0)

    assert escrow["status"] == "active"
    assert escrow["amount"] == 150.0
    assert "account_id" in escrow


@pytest.mark.asyncio
async def test_bid_stats():
    """Test Bidder tracking statistics."""
    bidder = BidAgent()

    job = {"id": "job-001", "value": 200}
    analysis = {"worthiness_score": 0.8}

    await bidder.run_with_retry({
        "job": job,
        "analysis": analysis,
    })

    stats = bidder.get_bidder_stats()
    assert stats["bids_created"] > 0
    assert stats["bids_submitted"] > 0
    assert stats["total_bid_value"] > 0


# ─────────────────────────────────────────────────────────────────
# TrackAgent Tests
# ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_track_execution():
    """Test Tracker health check execution."""
    tracker = TrackAgent()

    result = await tracker.run_with_retry({
        "session_id": "session-001",
    })

    assert result["success"] is True
    check = result["result"]
    assert check["session_id"] == "session-001"
    assert "snapshot" in check
    assert "health_status" in check


@pytest.mark.asyncio
async def test_track_xrp_check():
    """Test Tracker XRP ledger check."""
    tracker = TrackAgent()

    xrp_status = await tracker._check_xrp_progress()

    assert "xrp_balance" in xrp_status
    assert "status" in xrp_status
    assert xrp_status["xrp_balance"] > 0


@pytest.mark.asyncio
async def test_track_daily_limits():
    """Test Tracker daily limits check."""
    tracker = TrackAgent()

    limits_status = await tracker._check_daily_limits()

    assert "bids_today" in limits_status
    assert "bids_limit" in limits_status
    assert "bids_ratio" in limits_status
    assert 0 <= limits_status["bids_ratio"] <= 1


@pytest.mark.asyncio
async def test_track_system_health():
    """Test Tracker system health check."""
    tracker = TrackAgent()

    health = await tracker._check_system_health()

    assert "cpu_percent" in health
    assert "memory_percent" in health
    assert "disk_percent" in health
    assert 0 <= health["cpu_percent"] <= 100


@pytest.mark.asyncio
async def test_track_health_status_healthy():
    """Test Tracker determines healthy status."""
    tracker = TrackAgent()

    snapshot = {}
    alerts = []

    status = tracker._determine_health_status(snapshot, alerts)

    assert status == "healthy"


@pytest.mark.asyncio
async def test_track_health_status_warning():
    """Test Tracker determines warning status."""
    tracker = TrackAgent()

    snapshot = {}
    alerts = [{"level": "warning", "message": "Test warning"}]

    status = tracker._determine_health_status(snapshot, alerts)

    assert status == "warning"


@pytest.mark.asyncio
async def test_track_health_status_critical():
    """Test Tracker determines critical status."""
    tracker = TrackAgent()

    snapshot = {}
    alerts = [{"level": "critical", "message": "Test critical"}]

    status = tracker._determine_health_status(snapshot, alerts)

    assert status == "critical"


@pytest.mark.asyncio
async def test_track_stats():
    """Test Tracker tracking statistics."""
    tracker = TrackAgent()

    await tracker.run_with_retry({"session_id": "session-001"})

    stats = tracker.get_tracker_stats()
    assert stats["checks_performed"] > 0
    assert "alert_ratio" in stats


# ─────────────────────────────────────────────────────────────────
# Integration Tests
# ─────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_scout_produce_jobs_for_analyzer():
    """Test Scout produces jobs that Analyzer can consume."""
    scout = ScoutAgent()

    scout_result = await scout.run_with_retry({})
    jobs = scout_result["result"]["jobs_ready"]

    # Verify jobs have necessary fields for analysis
    for job in jobs:
        assert "id" in job
        assert "value" in job


@pytest.mark.asyncio
async def test_analyzer_produces_decision_for_bidder():
    """Test Analyzer produces decision that Bidder can use."""
    analyzer = AnalyzeAgent()

    job = {
        "id": "job-001",
        "type": "bid_request",
        "title": "Test",
        "value": 150,
    }

    result = await analyzer.run_with_retry({"job": job})
    analysis = result["result"]

    if analysis["worthy"]:
        # Should be able to feed to bidder
        bidder = BidAgent()
        bid_result = await bidder.run_with_retry({
            "job": job,
            "analysis": analysis,
        })
        assert bid_result["success"]
