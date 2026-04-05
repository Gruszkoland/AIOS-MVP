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
    from arbitrage.scout import MOCK_JOBS, _mock_scout
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
    from arbitrage.config import SCOUT_MAX_BUDGET, SCOUT_MIN_BUDGET
    from arbitrage.scout import run_scout
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


# ---------------------------------------------------------------------------
# _apify_scout — with mocked ApifyClient (covers lines 65-108)
# ---------------------------------------------------------------------------

def test_apify_scout_upwork_path():
    """Mock successful Apify call for upwork platform."""
    from arbitrage.config import SCOUT_MAX_BUDGET, SCOUT_MIN_BUDGET
    from arbitrage.scout import _apify_scout
    mid_budget = (SCOUT_MIN_BUDGET + SCOUT_MAX_BUDGET) // 2
    mock_items = [
        {"title": "Write blog posts", "budget": str(mid_budget),
         "description": "SEO articles needed", "url": "https://upwork.com/job/123",
         "client": "TechCo"},
    ]
    mock_run = {"defaultDatasetId": "ds-upwork-123"}
    mock_client = MagicMock()
    mock_client.actor.return_value.call.return_value = mock_run
    mock_client.dataset.return_value.iterate_items.return_value = iter(mock_items)
    mock_apify_class = MagicMock(return_value=mock_client)
    with patch("arbitrage.scout.APIFY_AVAILABLE", True), \
         patch("arbitrage.scout.APIFY_TOKEN", "fake-token"), \
         patch("arbitrage.scout.ApifyClient", mock_apify_class, create=True):
        result = _apify_scout("upwork", "content writing")
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["platform"] == "upwork"


def test_apify_scout_fiverr_path():
    """Mock successful Apify call for fiverr platform."""
    from arbitrage.config import SCOUT_MAX_BUDGET, SCOUT_MIN_BUDGET
    from arbitrage.scout import _apify_scout
    mid_budget = (SCOUT_MIN_BUDGET + SCOUT_MAX_BUDGET) // 2
    mock_items = [
        {"name": "Product descriptions", "price": str(mid_budget),
         "details": "Write 20 product descriptions", "link": "https://fiverr.com/gig/456",
         "seller": "WriterPro"},
    ]
    mock_run = {"defaultDatasetId": "ds-fiverr-456"}
    mock_client = MagicMock()
    mock_client.actor.return_value.call.return_value = mock_run
    mock_client.dataset.return_value.iterate_items.return_value = iter(mock_items)
    mock_apify_class = MagicMock(return_value=mock_client)
    with patch("arbitrage.scout.APIFY_AVAILABLE", True), \
         patch("arbitrage.scout.APIFY_TOKEN", "fake-token"), \
         patch("arbitrage.scout.ApifyClient", mock_apify_class, create=True):
        result = _apify_scout("fiverr", "copywriting")
    assert isinstance(result, list)


def test_apify_scout_budget_out_of_range():
    """Items with budget outside range should be excluded."""
    from arbitrage.scout import _apify_scout
    mock_items = [
        {"title": "Cheap job", "budget": "0", "description": "Too cheap"},
        {"title": "Expensive job", "budget": "999999", "description": "Too expensive"},
    ]
    mock_run = {"defaultDatasetId": "ds-oob"}
    mock_client = MagicMock()
    mock_client.actor.return_value.call.return_value = mock_run
    mock_client.dataset.return_value.iterate_items.return_value = iter(mock_items)
    mock_apify_class = MagicMock(return_value=mock_client)
    with patch("arbitrage.scout.APIFY_AVAILABLE", True), \
         patch("arbitrage.scout.APIFY_TOKEN", "fake-token"), \
         patch("arbitrage.scout.ApifyClient", mock_apify_class, create=True):
        result = _apify_scout("upwork", "writing")
    assert result == []


def test_apify_scout_exception_returns_empty():
    """Exception in Apify call → return empty list."""
    from arbitrage.scout import _apify_scout
    mock_client = MagicMock()
    mock_client.actor.return_value.call.side_effect = Exception("Apify timeout")
    mock_apify_class = MagicMock(return_value=mock_client)
    with patch("arbitrage.scout.APIFY_AVAILABLE", True), \
         patch("arbitrage.scout.APIFY_TOKEN", "fake-token"), \
         patch("arbitrage.scout.ApifyClient", mock_apify_class, create=True):
        result = _apify_scout("upwork", "content writing")
    assert result == []


# ---------------------------------------------------------------------------
# run_scout — apify mode (covers lines 126-130)
# ---------------------------------------------------------------------------

def test_run_scout_apify_mode():
    """use_mock=False triggers the apify path."""
    from arbitrage.scout import run_scout
    with patch("arbitrage.scout.APIFY_TOKEN", "fake-token"), \
         patch("arbitrage.scout._apify_scout", return_value=[]), \
         patch("arbitrage.scout.upsert_job", return_value=False):
        result = run_scout(use_mock=False, platforms=["upwork"], keywords=["writing"])
    assert result["mode"] == "apify"
    assert result["new_jobs"] == 0
