"""
Unit tests for arbitrage/scout.py — Scout Agent.
Mocks DB and Apify calls so no external services are needed.
"""
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# _make_job_id
# ---------------------------------------------------------------------------

def test_make_job_id_returns_16_chars():
    from arbitrage.scout import _make_job_id
    job_id = _make_job_id("upwork", "Test Job Title")
    assert isinstance(job_id, str)
    assert len(job_id) == 16


def test_make_job_id_different_for_different_inputs():
    from arbitrage.scout import _make_job_id
    id1 = _make_job_id("upwork", "Job A")
    id2 = _make_job_id("fiverr", "Job A")
    id3 = _make_job_id("upwork", "Job B")
    # Different platform or title → different (very likely) ID
    assert id1 != id2 or id1 != id3  # at least one differs


def test_make_job_id_consistent():
    """Same inputs on the same day → same ID."""
    from arbitrage.scout import _make_job_id
    id1 = _make_job_id("upwork", "Consistent Title")
    id2 = _make_job_id("upwork", "Consistent Title")
    assert id1 == id2


# ---------------------------------------------------------------------------
# _mock_scout
# ---------------------------------------------------------------------------

def test_mock_scout_returns_list():
    from arbitrage.scout import _mock_scout
    jobs = _mock_scout(count=3)
    assert isinstance(jobs, list)
    assert len(jobs) <= 3


def test_mock_scout_job_has_required_keys():
    from arbitrage.scout import _mock_scout
    jobs = _mock_scout(count=2)
    required = {"id", "platform", "title", "description", "budget_min", "budget_max", "client", "url", "keywords"}
    for job in jobs:
        assert required.issubset(job.keys()), f"Missing keys: {required - job.keys()}"


def test_mock_scout_count_respects_max():
    from arbitrage.scout import _mock_scout, MOCK_JOBS
    jobs = _mock_scout(count=100)
    assert len(jobs) <= len(MOCK_JOBS)


def test_mock_scout_count_1():
    from arbitrage.scout import _mock_scout
    jobs = _mock_scout(count=1)
    assert len(jobs) == 1


# ---------------------------------------------------------------------------
# run_scout — mock mode
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_db():
    with patch("arbitrage.scout.upsert_job") as mock_upsert:
        mock_upsert.return_value = True  # new job
        yield mock_upsert


def test_run_scout_mock_mode_returns_dict(mock_db):
    from arbitrage.scout import run_scout
    result = run_scout()
    assert "new_jobs" in result
    assert "jobs" in result
    assert "mode" in result
    assert result["mode"] == "mock"


def test_run_scout_mock_mode_has_jobs(mock_db):
    from arbitrage.scout import run_scout
    result = run_scout()
    assert isinstance(result["jobs"], list)
    assert len(result["jobs"]) > 0


def test_run_scout_explicit_mock_true(mock_db):
    from arbitrage.scout import run_scout
    result = run_scout(use_mock=True)
    assert result["mode"] == "mock"


def test_run_scout_counts_new_jobs(mock_db):
    from arbitrage.scout import run_scout
    mock_db.return_value = True  # Every job is "new"
    result = run_scout(use_mock=True)
    assert result["new_jobs"] == len(result["jobs"])


def test_run_scout_no_new_jobs_when_upsert_false(mock_db):
    from arbitrage.scout import run_scout
    mock_db.return_value = False  # No new jobs (all exist)
    result = run_scout(use_mock=True)
    assert result["new_jobs"] == 0


def test_run_scout_filters_by_budget(mock_db):
    """Jobs should be filtered to SCOUT_MIN_BUDGET..SCOUT_MAX_BUDGET range."""
    from arbitrage.scout import run_scout, MOCK_JOBS
    from arbitrage.config import SCOUT_MIN_BUDGET, SCOUT_MAX_BUDGET
    result = run_scout(use_mock=True)
    for job in result["jobs"]:
        assert SCOUT_MIN_BUDGET <= job.get("budget_max", 0) <= SCOUT_MAX_BUDGET


def test_run_scout_deduplicates_jobs(mock_db):
    """Returned jobs should have unique IDs."""
    from arbitrage.scout import run_scout
    result = run_scout(use_mock=True)
    ids = [j["id"] for j in result["jobs"]]
    assert len(ids) == len(set(ids))


# ---------------------------------------------------------------------------
# _apify_scout — no token case
# ---------------------------------------------------------------------------

def test_apify_scout_returns_empty_without_token():
    """Without APIFY_TOKEN, _apify_scout should return empty list."""
    from arbitrage.scout import _apify_scout
    with patch("arbitrage.scout.APIFY_TOKEN", ""):
        result = _apify_scout("upwork", "content writing")
    assert result == []


def test_apify_scout_returns_empty_when_not_available():
    """Without apify_client installed, _apify_scout returns empty list."""
    from arbitrage.scout import _apify_scout
    with patch("arbitrage.scout.APIFY_AVAILABLE", False):
        result = _apify_scout("fiverr", "writing")
    assert result == []
