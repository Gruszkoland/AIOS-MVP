"""
Database layer — SQLite schema + CRUD for the arbitrage system.
All queries use parameterized statements to prevent SQL injection.
"""

import sqlite3
from contextlib import contextmanager
from arbitrage.config import DB_PATH


# ──────────────────────────────────────────────────────────────────────────────
# Schema
# ──────────────────────────────────────────────────────────────────────────────

SCHEMA_SQL = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS projects (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source          TEXT NOT NULL,          -- 'upwork' | 'fiverr' | 'apify_maps'
    external_id     TEXT UNIQUE,            -- platform job ID or URL hash
    title           TEXT NOT NULL,
    description     TEXT,
    budget_min      REAL DEFAULT 0,
    budget_max      REAL DEFAULT 0,
    url             TEXT,
    skills          TEXT,                   -- comma-separated
    posted_at       TEXT,
    status          TEXT DEFAULT 'new',     -- new | analyzed | bid | won | lost | skip
    score           INTEGER DEFAULT 0,      -- 0-10 analyzer score
    reason          TEXT,                   -- analyzer reasoning
    created_at      TEXT DEFAULT (DATETIME('now'))
);

CREATE TABLE IF NOT EXISTS bids (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER NOT NULL REFERENCES projects(id),
    proposal_text   TEXT NOT NULL,
    bid_amount      REAL NOT NULL,
    status          TEXT DEFAULT 'sent',    -- sent | rejected | won | pending
    created_at      TEXT DEFAULT (DATETIME('now'))
);

CREATE TABLE IF NOT EXISTS earnings (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id      INTEGER REFERENCES projects(id),
    amount_usd      REAL NOT NULL,
    source_note     TEXT,
    earned_at       TEXT DEFAULT (DATETIME('now'))
);

CREATE TABLE IF NOT EXISTS xrp_snapshots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    xrp_price_usd   REAL NOT NULL,
    total_earned_usd REAL NOT NULL,
    xrp_equivalent  REAL NOT NULL,
    xrp_target      REAL NOT NULL DEFAULT 1000,
    pct_complete    REAL NOT NULL,
    snapshot_at     TEXT DEFAULT (DATETIME('now'))
);
"""


# ──────────────────────────────────────────────────────────────────────────────
# Connection helper
# ──────────────────────────────────────────────────────────────────────────────

@contextmanager
def get_connection():
    """Yield a thread-safe SQLite connection with row factory."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Create tables if they don't exist."""
    with get_connection() as conn:
        conn.executescript(SCHEMA_SQL)
    print(f"✅ Database initialised at {DB_PATH}")


# ──────────────────────────────────────────────────────────────────────────────
# Projects CRUD
# ──────────────────────────────────────────────────────────────────────────────

def upsert_project(source: str, external_id: str, title: str, description: str = "",
                   budget_min: float = 0, budget_max: float = 0,
                   url: str = "", skills: str = "", posted_at: str = "") -> int:
    """Insert a new project or ignore if already exists. Returns project id."""
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT OR IGNORE INTO projects
               (source, external_id, title, description, budget_min, budget_max, url, skills, posted_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (source, external_id, title, description, budget_min, budget_max, url, skills, posted_at)
        )
        if cur.lastrowid:
            return cur.lastrowid
        row = conn.execute(
            "SELECT id FROM projects WHERE external_id = ?", (external_id,)
        ).fetchone()
        return row["id"] if row else -1


def update_project_score(project_id: int, score: int, reason: str, status: str = "analyzed"):
    with get_connection() as conn:
        conn.execute(
            "UPDATE projects SET score=?, reason=?, status=? WHERE id=?",
            (score, reason, status, project_id)
        )


def get_projects_by_status(status: str) -> list:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM projects WHERE status=? ORDER BY score DESC, created_at DESC",
            (status,)
        ).fetchall()
        return [dict(r) for r in rows]


def mark_project_bid(project_id: int):
    with get_connection() as conn:
        conn.execute("UPDATE projects SET status='bid' WHERE id=?", (project_id,))


# ──────────────────────────────────────────────────────────────────────────────
# Bids CRUD
# ──────────────────────────────────────────────────────────────────────────────

def save_bid(project_id: int, proposal_text: str, bid_amount: float) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO bids (project_id, proposal_text, bid_amount) VALUES (?, ?, ?)",
            (project_id, proposal_text, bid_amount)
        )
        return cur.lastrowid


# ──────────────────────────────────────────────────────────────────────────────
# Earnings CRUD
# ──────────────────────────────────────────────────────────────────────────────

def record_earning(amount_usd: float, project_id: int = None, source_note: str = "") -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO earnings (project_id, amount_usd, source_note) VALUES (?, ?, ?)",
            (project_id, amount_usd, source_note)
        )
        return cur.lastrowid


def total_earned_usd() -> float:
    with get_connection() as conn:
        row = conn.execute("SELECT COALESCE(SUM(amount_usd), 0) AS total FROM earnings").fetchone()
        return float(row["total"])


# ──────────────────────────────────────────────────────────────────────────────
# XRP snapshots
# ──────────────────────────────────────────────────────────────────────────────

def save_xrp_snapshot(price: float, earned_usd: float, xrp_eq: float,
                      target: float, pct: float):
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO xrp_snapshots
               (xrp_price_usd, total_earned_usd, xrp_equivalent, xrp_target, pct_complete)
               VALUES (?, ?, ?, ?, ?)""",
            (price, earned_usd, xrp_eq, target, pct)
        )


def latest_xrp_snapshot() -> dict:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM xrp_snapshots ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return dict(row) if row else {}
