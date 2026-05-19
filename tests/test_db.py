"""
Unit tests for arbitrage/db.py — Legacy SQLite DB layer (projects/bids/earnings/xrp_snapshots).
Uses in-memory SQLite so no filesystem writes.
"""
import sqlite3
from contextlib import contextmanager
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Shared in-memory DB fixture
# ---------------------------------------------------------------------------

@pytest.fixture()
def mem_db_patch(tmp_path):
    """
    Patch arbitrage.db.get_connection to use an in-memory SQLite.
    Also patches DB_PATH to a temp file path.
    """
    db_file = tmp_path / "test.db"

    @contextmanager
    def _get_memory_conn():
        conn = sqlite3.connect(str(db_file), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    with patch("arbitrage.db.get_connection", side_effect=_get_memory_conn), \
         patch("arbitrage.db.DB_PATH", str(db_file)):
        # Initialize schema
        from arbitrage.db import init_db
        init_db()
        yield db_file


# ---------------------------------------------------------------------------
# init_db
# ---------------------------------------------------------------------------

def test_init_db_creates_projects_table(mem_db_patch):
    import sqlite3
    conn = sqlite3.connect(str(mem_db_patch))
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    table_names = [r[0] for r in rows]
    conn.close()
    assert "projects" in table_names
    assert "bids" in table_names
    assert "earnings" in table_names
    assert "xrp_snapshots" in table_names


# ---------------------------------------------------------------------------
# upsert_project
# ---------------------------------------------------------------------------

def test_upsert_project_returns_id(mem_db_patch):
    from arbitrage.db import upsert_project
    project_id = upsert_project(
        source="upwork",
        external_id="ext-001",
        title="SEO Blog Post",
        description="Write 5 articles",
        budget_min=100.0,
        budget_max=200.0,
    )
    assert isinstance(project_id, int)
    assert project_id > 0


def test_upsert_project_duplicate_returns_existing_id(mem_db_patch):
    from arbitrage.db import upsert_project
    id1 = upsert_project("upwork", "ext-002", "Title A")
    id2 = upsert_project("upwork", "ext-002", "Title A")
    assert id1 == id2


def test_upsert_project_different_external_ids(mem_db_patch):
    from arbitrage.db import upsert_project
    id1 = upsert_project("upwork", "ext-010", "Title X")
    id2 = upsert_project("upwork", "ext-011", "Title Y")
    assert id1 != id2


# ---------------------------------------------------------------------------
# update_project_score
# ---------------------------------------------------------------------------

def test_update_project_score(mem_db_patch):
    import sqlite3

    from arbitrage.db import update_project_score, upsert_project
    project_id = upsert_project("fiverr", "ext-100", "Test Project")
    update_project_score(project_id, score=8, reason="Good budget", status="analyzed")

    conn = sqlite3.connect(str(mem_db_patch))
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT score, reason, status FROM projects WHERE id=?", (project_id,)).fetchone()
    conn.close()
    assert row["score"] == 8
    assert row["reason"] == "Good budget"
    assert row["status"] == "analyzed"


# ---------------------------------------------------------------------------
# get_projects_by_status
# ---------------------------------------------------------------------------

def test_get_projects_by_status_empty(mem_db_patch):
    from arbitrage.db import get_projects_by_status
    result = get_projects_by_status("new")
    assert isinstance(result, list)
    assert len(result) == 0


def test_get_projects_by_status_returns_matching(mem_db_patch):
    from arbitrage.db import get_projects_by_status, upsert_project
    upsert_project("upwork", "ext-200", "Active Project")
    result = get_projects_by_status("new")
    assert len(result) == 1
    assert result[0]["title"] == "Active Project"


def test_get_projects_by_status_filters_correctly(mem_db_patch):
    from arbitrage.db import get_projects_by_status, update_project_score, upsert_project
    id1 = upsert_project("upwork", "ext-300", "Job A")
    upsert_project("upwork", "ext-301", "Job B")
    update_project_score(id1, 7, "good", "analyzed")

    new_jobs = get_projects_by_status("new")
    analyzed_jobs = get_projects_by_status("analyzed")
    assert len(new_jobs) == 1
    assert len(analyzed_jobs) == 1


# ---------------------------------------------------------------------------
# mark_project_bid
# ---------------------------------------------------------------------------

def test_mark_project_bid(mem_db_patch):
    import sqlite3

    from arbitrage.db import mark_project_bid, upsert_project
    project_id = upsert_project("upwork", "ext-400", "Bid Project")
    mark_project_bid(project_id)

    conn = sqlite3.connect(str(mem_db_patch))
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT status FROM projects WHERE id=?", (project_id,)).fetchone()
    conn.close()
    assert row["status"] == "bid"


# ---------------------------------------------------------------------------
# save_bid
# ---------------------------------------------------------------------------

def test_save_bid_returns_id(mem_db_patch):
    from arbitrage.db import save_bid, upsert_project
    project_id = upsert_project("upwork", "ext-500", "Bid Job")
    bid_id = save_bid(project_id, "My proposal text", 180.00)
    assert isinstance(bid_id, int)
    assert bid_id > 0


def test_save_bid_multiple_bids(mem_db_patch):
    from arbitrage.db import save_bid, upsert_project
    project_id = upsert_project("upwork", "ext-501", "Multi-bid Job")
    bid1 = save_bid(project_id, "Proposal 1", 150.0)
    bid2 = save_bid(project_id, "Proposal 2", 160.0)
    assert bid1 != bid2


# ---------------------------------------------------------------------------
# record_earning / total_earned_usd
# ---------------------------------------------------------------------------

def test_record_earning_and_total(mem_db_patch):
    from arbitrage.db import record_earning, total_earned_usd
    record_earning(100.0)
    record_earning(50.0)
    total = total_earned_usd()
    assert total == pytest.approx(150.0)


def test_total_earned_usd_zero_when_empty(mem_db_patch):
    from arbitrage.db import total_earned_usd
    total = total_earned_usd()
    assert total == pytest.approx(0.0)


def test_record_earning_with_project_id(mem_db_patch):
    from arbitrage.db import record_earning, total_earned_usd, upsert_project
    project_id = upsert_project("upwork", "ext-600", "Won Job")
    record_earning(200.0, project_id=project_id, source_note="stripe_payout")
    total = total_earned_usd()
    assert total == pytest.approx(200.0)


# ---------------------------------------------------------------------------
# save_xrp_snapshot / latest_xrp_snapshot
# ---------------------------------------------------------------------------

def test_save_and_retrieve_xrp_snapshot(mem_db_patch):
    from arbitrage.db import latest_xrp_snapshot, save_xrp_snapshot
    save_xrp_snapshot(price=2.5, earned_usd=250.0, xrp_eq=100.0, target=1000.0, pct=10.0)
    snap = latest_xrp_snapshot()
    assert snap["xrp_price_usd"] == pytest.approx(2.5)
    assert snap["total_earned_usd"] == pytest.approx(250.0)
    assert snap["pct_complete"] == pytest.approx(10.0)


def test_latest_xrp_snapshot_empty_returns_empty_dict(mem_db_patch):
    from arbitrage.db import latest_xrp_snapshot
    result = latest_xrp_snapshot()
    assert result == {}


def test_multiple_snapshots_returns_latest(mem_db_patch):
    from arbitrage.db import latest_xrp_snapshot, save_xrp_snapshot
    save_xrp_snapshot(1.0, 100.0, 100.0, 1000.0, 10.0)
    save_xrp_snapshot(3.0, 600.0, 200.0, 1000.0, 20.0)  # newer
    snap = latest_xrp_snapshot()
    assert snap["xrp_price_usd"] == pytest.approx(3.0)
    assert snap["pct_complete"] == pytest.approx(20.0)
