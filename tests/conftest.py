"""
ADRION 369 — Shared pytest fixtures.
Import these in test files with:   from conftest import ...   (or they are auto-loaded by pytest)
"""
import json
import sqlite3
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# ── Path setup ───────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# ── Database fixtures ────────────────────────────────────────────────────────

@pytest.fixture
def in_memory_db():
    """Lightweight in-memory SQLite connection, schema pre-applied."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")

    schema_sql = """
    CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY,
        platform TEXT,
        title TEXT,
        budget_min REAL,
        budget_max REAL,
        description TEXT,
        keywords TEXT,
        status TEXT DEFAULT 'new',
        score INTEGER,
        scouted_at TEXT
    );
    CREATE TABLE IF NOT EXISTS bids (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT,
        cover_letter TEXT,
        bid_price REAL,
        status TEXT DEFAULT 'pending',
        bid_at TEXT
    );
    """
    conn.executescript(schema_sql)
    yield conn
    conn.close()


# ── Environment fixtures ──────────────────────────────────────────────────────

@pytest.fixture
def clean_env(monkeypatch):
    """Remove all ADRION-related env vars so defaults are used.

    Also patches load_dotenv to be a no-op so .env file doesn't override
    the cleared environment during module reloads in tests.
    """
    import dotenv
    monkeypatch.setattr(dotenv, "load_dotenv", lambda *a, **kw: None)

    keys = [
        "LLM_BACKEND", "OPENROUTER_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY",
        "LLM_MODEL", "APIFY_API_TOKEN", "DATABASE_URL", "DB_ENGINE", "DB_PATH",
        "DAILY_BID_LIMIT", "MIN_PROFIT_USD", "MIN_ANALYZER_SCORE",
        "LINKEDIN_ACCESS_TOKEN", "LINKEDIN_ACCOUNT_ID",
    ]
    for key in keys:
        monkeypatch.delenv(key, raising=False)
    return monkeypatch


# ── LLM mock fixtures ─────────────────────────────────────────────────────────

@pytest.fixture
def mock_llm_response():
    """Canonical mock LLM JSON response string for job analysis."""
    return json.dumps({
        "score": 8,
        "fit": "Perfect match for content writer",
        "risks": "Short deadline",
        "est_hours": 4,
        "our_price": 150,
        "est_cost": 1.5,
        "est_profit": 148.5,
    })


@pytest.fixture
def mock_openai_client(mock_llm_response):
    """MagicMock configured to mimic openai.OpenAI chat completions."""
    client = MagicMock()
    choice = MagicMock()
    choice.message.content = mock_llm_response
    client.chat.completions.create.return_value = MagicMock(choices=[choice])
    return client


# ── Job / arbitrage data fixtures ─────────────────────────────────────────────

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def mock_jobs():
    """Load sample job postings from fixtures/mock_jobs.json."""
    with open(FIXTURES_DIR / "mock_jobs.json", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def sample_job():
    """Single job dict matching the DB schema."""
    return {
        "id": "test-job-001",
        "platform": "upwork",
        "title": "SEO Content Writer Needed",
        "budget_min": 100.0,
        "budget_max": 300.0,
        "description": "Write 5 SEO-optimized blog posts about digital marketing.",
        "keywords": ["content writing", "SEO", "blog post"],
        "status": "new",
        "score": None,
        "scouted_at": "2026-04-04T10:00:00",
    }


# ── Network mock fixtures ─────────────────────────────────────────────────────

@pytest.fixture
def mock_requests_get_xrp():
    """Fake requests.get that returns a CoinGecko-formatted XRP price response."""
    def _fake_get(url, **kwargs):
        resp = MagicMock()
        resp.raise_for_status = lambda: None
        if "coingecko" in url:
            resp.json.return_value = {"ripple": {"usd": 2.35}}
        else:
            resp.json.return_value = {"price": "2.35"}
        return resp
    return _fake_get


# ── TIER 0 Critical fixtures ─────────────────────────────────────────────────

@pytest.fixture
def tier0_ebdi_baseline():
    """TIER 0: EBDI baseline state (Pleasure, Arousal, Dominance) per agent."""
    return {
        "librarian": {"P": 0.5, "A": 0.3, "D": 0.6},
        "sap": {"P": 0.6, "A": 0.4, "D": 0.8},
        "auditor": {"P": 0.3, "A": 0.1, "D": 0.5},
        "sentinel": {"P": 0.4, "A": 0.7, "D": 0.9},
        "architect": {"P": 0.6, "A": 0.5, "D": 0.7},
        "healer": {"P": 0.7, "A": 0.3, "D": 0.6},
    }


@pytest.fixture
def tier0_guardian_laws():
    """TIER 0: 9 Guardian Laws for compliance checks."""
    return {
        "G1": "Unity",
        "G2": "Harmony",
        "G3": "Rhythm",
        "G4": "Causality",
        "G5": "Transparency",
        "G6": "Authenticity",
        "G7": "Privacy",
        "G8": "Nonmaleficence",
        "G9": "Sustainability",
    }


@pytest.fixture
def tier0_crisis_mode_trigger():
    """TIER 0: Crisis mode activates when Arousal > 0.7 (Sentinel only)."""
    return 0.7


# ── Helper pytest markers and utilities ──────────────────────────────────────

def pytest_configure(config):
    """Register TIER 0 marker for critical tests."""
    config.addinivalue_line(
        "markers", "tier0: TIER 0 critical system tests (must pass)"
    )


@pytest.fixture
def assert_guardian_law_compliance():
    """TIER 0: Helper to verify Guardian Law compliance in assertions."""
    def _check(operation, law_ids: list, description: str):
        """Verify operation message mentions Guardian Laws."""
        msg = str(operation)
        for law_id in law_ids:
            assert law_id in msg, f"Operation {description} missing {law_id} compliance info"
    return _check
