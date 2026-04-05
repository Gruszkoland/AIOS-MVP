"""
Unit tests for arbitrage/database.py — SQLite ORM (13 tables)
Uses in-memory SQLite to avoid touching the real DB.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["DB_PATH"] = ":memory:"



@pytest.fixture(autouse=True)
def fresh_db(monkeypatch, tmp_path):
    """Each test gets a fresh in-memory SQLite database."""
    db_file = str(tmp_path / "test.db")
    monkeypatch.setenv("DB_PATH", db_file)
    # Reload the module so DB_PATH is picked up
    import arbitrage.config as cfg
    import arbitrage.database as db_mod
    monkeypatch.setattr(cfg, "DB_PATH", db_file)
    monkeypatch.setattr(db_mod, "DB_PATH", db_file)
    # Patch get_conn to use new path
    import sqlite3
    def patched_conn():
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn
    monkeypatch.setattr(db_mod, "get_conn", patched_conn)
    db_mod.init_db()
    yield db_mod


# ── init_db ──────────────────────────────────────────────────────────────────

class TestInitDb:
    def test_creates_jobs_table(self, fresh_db):
        with fresh_db.get_conn() as conn:
            row = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='jobs'"
            ).fetchone()
            assert row is not None

    def test_creates_deals_table(self, fresh_db):
        with fresh_db.get_conn() as conn:
            row = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='deals'"
            ).fetchone()
            assert row is not None

    def test_creates_kpi_events_table(self, fresh_db):
        with fresh_db.get_conn() as conn:
            row = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='kpi_events'"
            ).fetchone()
            assert row is not None

    def test_creates_subscriptions_table(self, fresh_db):
        with fresh_db.get_conn() as conn:
            row = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='subscriptions'"
            ).fetchone()
            assert row is not None

    def test_idempotent_double_init(self, fresh_db):
        # Calling init_db twice should not raise
        fresh_db.init_db()
        fresh_db.init_db()


# ── upsert_job ────────────────────────────────────────────────────────────────

class TestUpsertJob:
    JOB = {
        "id": "job-001",
        "platform": "upwork",
        "title": "Python Developer Needed",
        "description": "Build a REST API",
        "budget_min": 500.0,
        "budget_max": 1000.0,
        "client": "Acme Corp",
        "url": "https://upwork.com/jobs/001",
        "keywords": ["python", "fastapi"],
        "status": "new",
    }

    def test_insert_new_job_returns_true(self, fresh_db):
        result = fresh_db.upsert_job(self.JOB)
        assert result is True

    def test_insert_duplicate_job_returns_false(self, fresh_db):
        fresh_db.upsert_job(self.JOB)
        result = fresh_db.upsert_job(self.JOB)
        assert result is False

    def test_job_appears_in_db(self, fresh_db):
        fresh_db.upsert_job(self.JOB)
        jobs = fresh_db.get_jobs()
        assert any(j["id"] == "job-001" for j in jobs)

    def test_only_one_row_after_duplicate(self, fresh_db):
        fresh_db.upsert_job(self.JOB)
        fresh_db.upsert_job(self.JOB)
        jobs = fresh_db.get_jobs()
        count = sum(1 for j in jobs if j["id"] == "job-001")
        assert count == 1


# ── get_jobs ──────────────────────────────────────────────────────────────────

class TestGetJobs:
    def _insert_jobs(self, fresh_db, n=3):
        for i in range(n):
            fresh_db.upsert_job({
                "id": f"job-{i:03d}",
                "platform": "freelancer",
                "title": f"Job {i}",
                "description": "",
                "budget_min": i * 100.0,
                "budget_max": i * 200.0,
                "client": f"Client {i}",
                "url": f"https://example.com/{i}",
                "keywords": [],
                "status": "new",
            })

    def test_returns_list(self, fresh_db):
        jobs = fresh_db.get_jobs()
        assert isinstance(jobs, list)

    def test_get_all_jobs(self, fresh_db):
        self._insert_jobs(fresh_db, 3)
        assert len(fresh_db.get_jobs()) == 3

    def test_filter_by_status(self, fresh_db):
        self._insert_jobs(fresh_db, 3)
        fresh_db.set_job_status("job-001", "won")
        won = fresh_db.get_jobs(status="won")
        assert len(won) == 1
        assert won[0]["id"] == "job-001"

    def test_limit(self, fresh_db):
        self._insert_jobs(fresh_db, 5)
        jobs = fresh_db.get_jobs(limit=2)
        assert len(jobs) <= 2


# ── upsert_deal ───────────────────────────────────────────────────────────────

class TestUpsertDeal:
    DEAL = {
        "sku": "FIIO-K9-PRO",
        "product_name": "FiiO K9 Pro",
        "channel_id": "AUDIO_PREMIUM",
        "wholesale_price": 199.0,
        "retail_price_de": 299.0,
        "retail_price_pl": 289.0,
        "margin_pct": 0.33,
        "vortex_resonance": 9,
        "vortex_pass": True,
        "source_url": "https://supplier.de/fiio-k9",
        "supplier": "AudioHaus",
        "stock_qty": 25,
    }

    def test_new_deal_returns_true(self, fresh_db):
        result = fresh_db.upsert_deal(self.DEAL)
        assert result is True

    def test_duplicate_deal_returns_false(self, fresh_db):
        fresh_db.upsert_deal(self.DEAL)
        result = fresh_db.upsert_deal(self.DEAL)
        assert result is False

    def test_deal_is_retrievable(self, fresh_db):
        fresh_db.upsert_deal(self.DEAL)
        deals = fresh_db.get_deals()
        assert any(d["sku"] == "FIIO-K9-PRO" for d in deals)

    def test_update_does_not_create_duplicate(self, fresh_db):
        fresh_db.upsert_deal(self.DEAL)
        updated = {**self.DEAL, "wholesale_price": 180.0}
        fresh_db.upsert_deal(updated)
        deals = fresh_db.get_deals()
        fiio_deals = [d for d in deals if d["sku"] == "FIIO-K9-PRO"]
        assert len(fiio_deals) == 1


# ── get_deals ─────────────────────────────────────────────────────────────────

class TestGetDeals:
    def _seed(self, fresh_db):
        fresh_db.upsert_deal({
            "sku": "A001", "product_name": "Product A", "channel_id": "AUDIO_PREMIUM",
            "wholesale_price": 100.0, "retail_price_de": 140.0, "margin_pct": 0.28,
            "supplier": "SupA", "stock_qty": 10,
        })
        fresh_db.upsert_deal({
            "sku": "B001", "product_name": "Product B", "channel_id": "SMART_ENERGY",
            "wholesale_price": 200.0, "retail_price_de": 220.0, "margin_pct": 0.09,
            "supplier": "SupB", "stock_qty": 5,
        })
        fresh_db.upsert_deal({
            "sku": "C001", "product_name": "Product C", "channel_id": "AUDIO_PREMIUM",
            "wholesale_price": 300.0, "retail_price_de": 500.0, "margin_pct": 0.40,
            "supplier": "SupC", "stock_qty": 3,
        })

    def test_get_all_deals(self, fresh_db):
        self._seed(fresh_db)
        deals = fresh_db.get_deals()
        assert len(deals) == 3

    def test_filter_by_channel(self, fresh_db):
        self._seed(fresh_db)
        deals = fresh_db.get_deals(channel_id="AUDIO_PREMIUM")
        assert all(d["channel_id"] == "AUDIO_PREMIUM" for d in deals)
        assert len(deals) == 2

    def test_filter_by_min_margin(self, fresh_db):
        self._seed(fresh_db)
        deals = fresh_db.get_deals(min_margin=0.20)
        assert all(d["margin_pct"] >= 0.20 for d in deals)

    def test_sorted_by_margin_desc(self, fresh_db):
        self._seed(fresh_db)
        deals = fresh_db.get_deals()
        margins = [d["margin_pct"] for d in deals if d["margin_pct"] is not None]
        assert margins == sorted(margins, reverse=True)

    def test_limit_parameter(self, fresh_db):
        self._seed(fresh_db)
        deals = fresh_db.get_deals(limit=1)
        assert len(deals) <= 1


# ── update_deal_status ────────────────────────────────────────────────────────

class TestUpdateDealStatus:
    def test_status_changes(self, fresh_db):
        fresh_db.upsert_deal({
            "sku": "X001", "product_name": "Test Product", "channel_id": "AUDIO_PREMIUM",
            "wholesale_price": 100.0, "margin_pct": 0.25, "supplier": "S1", "stock_qty": 5,
        })
        deal_id = fresh_db.get_deals()[0]["id"]
        fresh_db.update_deal_status(deal_id, "executed")
        deals = fresh_db.get_deals()
        updated = next(d for d in deals if d["id"] == deal_id)
        assert updated["status"] == "executed"


# ── record_kpi_event ──────────────────────────────────────────────────────────

class TestRecordKpiEvent:
    def test_basic_insert(self, fresh_db):
        fresh_db.record_kpi_event("b2b", "deal_closed", amount_usd=500.0)
        kpis = fresh_db.get_stream_kpis()
        assert kpis["streams"]["b2b"]["events"] == 1

    def test_amount_stored_correctly(self, fresh_db):
        fresh_db.record_kpi_event("resale", "sale", amount_usd=250.0, est_cost_usd=50.0)
        kpis = fresh_db.get_stream_kpis()
        assert kpis["streams"]["resale"]["revenue_usd"] == 250.0

    def test_meta_json_stored(self, fresh_db):
        fresh_db.record_kpi_event(
            "ugc", "impression", meta={"platform": "linkedin", "views": 1200}
        )
        kpis = fresh_db.get_stream_kpis()
        assert kpis["streams"]["ugc"]["events"] >= 1

    def test_multiple_events_accumulate(self, fresh_db):
        for _ in range(5):
            fresh_db.record_kpi_event("b2b", "deal", amount_usd=100.0)
        kpis = fresh_db.get_stream_kpis()
        assert kpis["streams"]["b2b"]["revenue_usd"] == 500.0

    def test_default_source_added(self, fresh_db):
        fresh_db.record_kpi_event("b2b", "test")
        kpis = fresh_db.get_stream_kpis()
        assert kpis["sources"]["other"] >= 1

    def test_total_revenue_is_sum(self, fresh_db):
        fresh_db.record_kpi_event("b2b", "e1", amount_usd=100.0)
        fresh_db.record_kpi_event("resale", "e2", amount_usd=200.0)
        kpis = fresh_db.get_stream_kpis()
        assert kpis["total_revenue_usd"] == 300.0
