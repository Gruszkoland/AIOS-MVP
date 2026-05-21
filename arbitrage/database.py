"""
ADRION 369 - Freelance Arbitrage Database
SQLite storage for jobs, bids, KPIs, earnings and XRP snapshots.
All queries use parameterized statements to prevent SQL injection.
"""
import json
import logging
import os
import sqlite3
from datetime import datetime
from typing import Any, Optional, Protocol, cast

from .config import DB_ENGINE, DB_PATH, DB_URL


class DBConnection(Protocol):
    """Protocol for database connections (SQLite or PostgreSQL)."""

    def execute(self, query: str, params: Any = ...) -> Any: ...
    def cursor(self) -> Any: ...
    def commit(self) -> None: ...
    def close(self) -> None: ...
    def __enter__(self) -> "DBConnection": ...
    def __exit__(self, *args: Any) -> None: ...

logger = logging.getLogger("adrion.db")

# ── Connection Pool (PostgreSQL only) ────────────────────────────────────────
_pool = None  # psycopg2.pool.SimpleConnectionPool instance, None in SQLite mode


def init_pool(db_url: str = "", min_conn: int = 2, max_conn: int = 10) -> bool:
    """
    Initialize a psycopg2 connection pool for PostgreSQL production use.
    No-op (returns False) when using SQLite.

    Args:
        db_url: PostgreSQL DSN (defaults to config.DB_URL).
        min_conn: Minimum connections kept open.
        max_conn: Maximum connections allowed.

    Returns:
        True if pool was created, False if using SQLite or psycopg2 missing.
    """
    global _pool
    url = db_url or DB_URL
    if not url or DB_ENGINE != "postgres":
        logger.debug("Pool init skipped — SQLite mode or no DB_URL")
        return False
    try:
        import psycopg2.pool
        _pool = psycopg2.pool.SimpleConnectionPool(min_conn, max_conn, dsn=url)
        # Pre-warm: check out and immediately return min_conn connections
        conns = [_pool.getconn() for _ in range(min_conn)]
        for c in conns:
            _pool.putconn(c)
        logger.info("PostgreSQL connection pool ready (min=%d, max=%d)", min_conn, max_conn)
        return True
    except ImportError:
        logger.error("psycopg2 not installed — pool not available")
    except Exception as e:
        logger.error("Failed to create connection pool: %s", e)
    return False


def get_pooled_conn() -> DBConnection:
    """
    Return a connection checked out from the pool (PostgreSQL) or a fresh
    SQLite connection. Caller must call return_conn() when done.
    """
    if _pool is not None:
        return _pool.getconn()
    return get_conn()


def return_conn(conn: DBConnection) -> None:
    """Return a pooled connection back to the pool. No-op for SQLite connections."""
    if _pool is not None:
        try:
            _pool.putconn(conn)
        except Exception as e:
            logger.warning("Failed to return connection to pool: %s", e)


def graceful_drain() -> None:
    """Close all idle pool connections on app shutdown. No-op for SQLite."""
    global _pool
    if _pool is not None:
        try:
            _pool.closeall()
            logger.info("Connection pool drained.")
        except Exception as e:
            logger.warning("Error draining pool: %s", e)
        finally:
            _pool = None

def get_conn() -> DBConnection:
    """Returns a connection based on the configured engine."""
    if DB_ENGINE == "postgres" and DB_URL:
        try:
            import psycopg2
            from psycopg2.extras import RealDictConnection
            conn = psycopg2.connect(DB_URL, connection_factory=RealDictConnection)
            return conn
        except ImportError:
            logger.error("psycopg2 not installed. Falling back to SQLite.")
        except Exception as e:
            logger.error(f"Postgres connection failed: {e}")

    # Default to SQLite
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return cast(DBConnection, conn)


def init_db(db_path: Optional[str] = None) -> None:
    """Initialize database using migration files."""
    path = db_path or DB_PATH
    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA journal_mode=WAL")
    # Check if tables already exist
    tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()]
    if "jobs" in tables:
        conn.close()
        return  # Already initialized
    # Apply migrations from files
    import glob
    migration_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "db", "migrations"
    )
    for sql_file in sorted(glob.glob(os.path.join(migration_dir, "*.sql"))):
        with open(sql_file) as f:
            sql = f.read()
        try:
            conn.executescript(sql)
            logger.info("Applied migration: %s", os.path.basename(sql_file))
        except Exception as e:
            logger.warning("Migration %s skipped: %s", os.path.basename(sql_file), e)
    conn.commit()
    conn.close()


# ── Jobs ──────────────────────────────────────────────────────────────────────

def upsert_job(job: dict) -> bool:
    """Insert job, skip if already exists. Returns True if new."""
    with get_conn() as conn:
        cursor = conn.execute(
            "INSERT OR IGNORE INTO jobs "
            "(id,platform,title,description,budget_min,budget_max,client,url,keywords,status) "
            "VALUES (:id,:platform,:title,:description,:budget_min,:budget_max,:client,:url,:keywords,:status)",
            {**job, "keywords": json.dumps(job.get("keywords", [])), "status": "new"},
        )
        return cursor.rowcount > 0


def get_jobs(status: Optional[str] = None, limit: int = 50) -> list[dict]:
    with get_conn() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM jobs WHERE status=? ORDER BY scouted_at DESC LIMIT ?",
                (status, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM jobs ORDER BY scouted_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]


def set_job_status(job_id: str, status: str) -> None:
    with get_conn() as conn:
        conn.execute("UPDATE jobs SET status=? WHERE id=?", (status, job_id))


# ── Bids ──────────────────────────────────────────────────────────────────────

def insert_bid(bid: dict) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO bids "
            "(job_id,cover_letter,our_price,est_profit_usd,analyzer_score,llm_backend) "
            "VALUES (:job_id,:cover_letter,:our_price,:est_profit_usd,:analyzer_score,:llm_backend)",
            bid,
        )
        return cur.lastrowid


def get_pending_bids() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT b.*, j.title, j.platform, j.url "
            "FROM bids b JOIN jobs j ON b.job_id=j.id "
            "WHERE b.approved=0 ORDER BY b.created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def approve_bid(bid_id: int, approved: bool) -> None:
    status = 1 if approved else -1
    sent_at = datetime.now().isoformat() if approved else None
    with get_conn() as conn:
        conn.execute(
            "UPDATE bids SET approved=?, sent_at=? WHERE id=?",
            (status, sent_at, bid_id),
        )


def get_all_bids(limit: int = 100) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT b.*, j.title, j.platform "
            "FROM bids b JOIN jobs j ON b.job_id=j.id "
            "ORDER BY b.created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


# ── KPIs ──────────────────────────────────────────────────────────────────────

def record_kpi(kpi: dict) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO kpis "
            "(jobs_scouted,bids_sent,bids_won,revenue_usd,profit_usd,xrp_earned) "
            "VALUES (:jobs_scouted,:bids_sent,:bids_won,:revenue_usd,:profit_usd,:xrp_earned)",
            kpi,
        )


def get_totals() -> dict:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT "
            "  (SELECT COUNT(*) FROM jobs) AS total_jobs, "
            "  (SELECT COUNT(*) FROM jobs WHERE status='won') AS jobs_won, "
            "  (SELECT COUNT(*) FROM bids WHERE approved=1) AS bids_sent, "
            "  (SELECT COALESCE(SUM(profit_usd),0) FROM kpis) AS total_profit "
        ).fetchone()
        return dict(row) if row else {}


def record_autopilot_run(run_data: dict) -> None:
    """Persist one autopilot cycle result for observability and reporting."""
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO autopilot_runs "
            "(started_at,finished_at,success,dry_run,jobs_scouted,new_jobs,analyzed,bids_created,bids_today,total_earned_usd,error_message) "
            "VALUES (:started_at,:finished_at,:success,:dry_run,:jobs_scouted,:new_jobs,:analyzed,:bids_created,:bids_today,:total_earned_usd,:error_message)",
            {
                "started_at": run_data.get("started_at"),
                "finished_at": run_data.get("finished_at"),
                "success": 1 if run_data.get("success") else 0,
                "dry_run": 1 if run_data.get("dry_run") else 0,
                "jobs_scouted": run_data.get("jobs_scouted", 0),
                "new_jobs": run_data.get("new_jobs", 0),
                "analyzed": run_data.get("analyzed", 0),
                "bids_created": run_data.get("bids_created", 0),
                "bids_today": run_data.get("bids_today", 0),
                "total_earned_usd": run_data.get("total_earned_usd", 0),
                "error_message": run_data.get("error_message"),
            },
        )


def get_recent_autopilot_runs(limit: int = 20) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM autopilot_runs ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_last_autopilot_run() -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM autopilot_runs ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return dict(row) if row else None


def record_kpi_event(
    stream: str,
    event_type: str,
    amount_usd: float = 0,
    est_cost_usd: float = 0,
    meta: dict | None = None,
):
    with get_conn() as conn:
        meta_dict = meta or {}
        # Ensure 'source' is tracked
        if "source" not in meta_dict:
            meta_dict["source"] = "manual"

        conn.execute(
            "INSERT INTO kpi_events (stream,event_type,amount_usd,est_cost_usd,meta_json) VALUES (?,?,?,?,?)",
            (
                stream,
                event_type,
                float(amount_usd or 0),
                float(est_cost_usd or 0),
                json.dumps(meta_dict, ensure_ascii=True),
            ),
        )


def get_stream_kpis() -> dict:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT stream, "
            "COUNT(*) AS events, "
            "COALESCE(SUM(amount_usd),0) AS revenue_usd, "
            "COALESCE(SUM(est_cost_usd),0) AS est_cost_usd "
            "FROM kpi_events "
            "GROUP BY stream"
        ).fetchall()

        # Phase 2: Source Metrics
        source_rows = conn.execute(
            "SELECT COUNT(*) AS c, "
            "CASE WHEN json_extract(meta_json, '$.source') = 'external' THEN 'external' "
            "     WHEN json_extract(meta_json, '$.source') = 'seed' THEN 'seed' "
            "     ELSE 'other' END AS src_group "
            "FROM kpi_events "
            "GROUP BY src_group"
        ).fetchall()

        daily_cost_row = conn.execute(
            "SELECT COALESCE(SUM(est_cost_usd),0) AS daily_est_cost "
            "FROM kpi_events WHERE DATE(created_at)=DATE('now')"
        ).fetchone()

    streams = {
        "b2b": {"events": 0, "revenue_usd": 0.0, "est_cost_usd": 0.0},
        "ugc": {"events": 0, "revenue_usd": 0.0, "est_cost_usd": 0.0},
        "resale": {"events": 0, "revenue_usd": 0.0, "est_cost_usd": 0.0},
    }

    for r in rows:
        stream = r["stream"]
        if stream not in streams:
            streams[stream] = {"events": 0, "revenue_usd": 0.0, "est_cost_usd": 0.0}
        streams[stream] = {
            "events": int(r["events"] or 0),
            "revenue_usd": float(r["revenue_usd"] or 0),
            "est_cost_usd": float(r["est_cost_usd"] or 0),
        }

    total_revenue = sum(v["revenue_usd"] for v in streams.values())
    total_cost = sum(v["est_cost_usd"] for v in streams.values())

    sources = {"external": 0, "seed": 0, "other": 0}
    for sr in source_rows:
        sources[sr["src_group"]] = int(sr["c"] or 0)

    return {
        "streams": streams,
        "total_revenue_usd": round(total_revenue, 2),
        "total_est_cost_usd": round(total_cost, 2),
        "daily_est_cost_usd": round(float(daily_cost_row["daily_est_cost"] or 0), 2),
        "total_margin_usd": round(total_revenue - total_cost, 2),
        "sources": sources,
    }


def get_client_bid_count_today(client_name: str) -> int:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS c "
            "FROM bids b JOIN jobs j ON b.job_id=j.id "
            "WHERE DATE(b.created_at)=DATE('now') AND LOWER(COALESCE(j.client,''))=LOWER(?)",
            (client_name or "",),
        ).fetchone()
        return int(row["c"] or 0) if row else 0


# ── Deals (Wholesale) ────────────────────────────────────────────────────────

def upsert_deal(deal: dict) -> bool:
    """Insert or update a wholesale deal. Returns True if new."""
    with get_conn() as conn:
        cursor = conn.execute(
            "INSERT OR IGNORE INTO deals "
            "(sku,product_name,channel_id,wholesale_price,retail_price_de,retail_price_pl,"
            "margin_pct,vortex_resonance,vortex_pass,source_url,supplier,stock_qty,status) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                deal["sku"], deal.get("product_name", deal["sku"]),
                deal.get("channel_id", "AUDIO_PREMIUM"),
                deal.get("wholesale_price", 0), deal.get("retail_price_de"),
                deal.get("retail_price_pl"), deal.get("margin_pct"),
                deal.get("vortex_resonance"), int(deal.get("vortex_pass", False)),
                deal.get("source_url"), deal.get("supplier", ""),
                deal.get("stock_qty", 0), "new",
            ),
        )
        if cursor.rowcount > 0:
            return True
        conn.execute(
            "UPDATE deals SET wholesale_price=?, retail_price_de=?, retail_price_pl=?, "
            "margin_pct=?, vortex_resonance=?, vortex_pass=?, stock_qty=?, "
            "source_url=?, status=? WHERE sku=? AND supplier=?",
            (
                deal.get("wholesale_price"), deal.get("retail_price_de"),
                deal.get("retail_price_pl"), deal.get("margin_pct"),
                deal.get("vortex_resonance"), int(deal.get("vortex_pass", False)),
                deal.get("stock_qty", 0), deal.get("source_url"), "updated",
                deal["sku"], deal.get("supplier", ""),
            ),
        )
        return False


def get_deals(channel_id: Optional[str] = None, status: Optional[str] = None, min_margin: Optional[float] = None,
              limit: int = 50) -> list[dict]:
    """Query deals with optional filters."""
    clauses: list[str] = []
    params: list[Any] = []
    if channel_id:
        clauses.append("channel_id=?")
        params.append(channel_id)
    if status:
        clauses.append("status=?")
        params.append(status)
    if min_margin is not None:
        clauses.append("margin_pct>=?")
        params.append(min_margin)
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    params.append(limit)
    with get_conn() as conn:
        rows = conn.execute(
            f"SELECT * FROM deals{where} ORDER BY margin_pct DESC LIMIT ?", params
        ).fetchall()
        return [dict(r) for r in rows]


def update_deal_status(deal_id: int, status: str) -> None:
    with get_conn() as conn:
        conn.execute("UPDATE deals SET status=?, executed_at=datetime('now') WHERE id=?",
                      (status, deal_id))
