"""
micro-saas billing_pg — PostgreSQL backend (drop-in for billing.py).

Activation:
  Set env vars:
    SAAS_DB_DRIVER=postgres
    DATABASE_URL=postgresql://user:pass@host:5432/adrion

  In api.py / init code, call:
    from billing_pg import init_saas_db, get_subscription, create_subscription, \
                           check_bid_quota, consume_bid

  The public API is identical to billing.py — zero changes needed in api.py.

Requires: psycopg2-binary (added to requirements-mcp.txt by this module).

Schema: same column names as SQLite version → shared test_saas_billing.py works
        with both backends (isolation via SAAS_DB_DRIVER env var).
"""
from __future__ import annotations

import logging
import os
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Generator, Optional

from billing import TIERS, Subscription  # re-export shared definitions

logger = logging.getLogger("adrion.micro_saas.billing_pg")

_DATABASE_URL = os.getenv("DATABASE_URL", "")


def _get_psycopg2():
    """Lazy import — raises ImportError with actionable message if missing."""
    try:
        import psycopg2
        import psycopg2.extras
        return psycopg2
    except ImportError as exc:
        raise ImportError(
            "psycopg2 is required for PostgreSQL billing backend. "
            "Install: pip install psycopg2-binary"
        ) from exc


@contextmanager
def _get_conn() -> Generator:
    """Context manager returning a psycopg2 connection with RealDictCursor."""
    psycopg2 = _get_psycopg2()
    if not _DATABASE_URL:
        raise RuntimeError("DATABASE_URL env var is not set. Required for SAAS_DB_DRIVER=postgres.")
    conn = psycopg2.connect(_DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── Schema ────────────────────────────────────────────────────────────────

def init_saas_db() -> None:
    """Create tables if they don't exist (idempotent, safe to call on startup)."""
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS subscriptions (
                    sub_id          TEXT PRIMARY KEY,
                    user_id         TEXT NOT NULL,
                    tier            TEXT NOT NULL DEFAULT 'free',
                    status          TEXT NOT NULL DEFAULT 'active',
                    created_at      TEXT NOT NULL,
                    expires_at      TEXT,
                    bids_used_today INTEGER NOT NULL DEFAULT 0,
                    last_bid_date   TEXT
                )
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_subscriptions_user_status
                    ON subscriptions (user_id, status)
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS saas_events (
                    event_id   TEXT PRIMARY KEY,
                    sub_id     TEXT NOT NULL REFERENCES subscriptions(sub_id),
                    event_type TEXT NOT NULL,
                    payload    TEXT,
                    created_at TEXT NOT NULL
                )
            """)
    logger.info("SaaS PostgreSQL schema initialized (DATABASE_URL=%s...)", _DATABASE_URL[:20])


# ── CRUD ──────────────────────────────────────────────────────────────────

def get_subscription(user_id: str) -> Optional[Subscription]:
    """Fetch active subscription for a user; returns None if not subscribed."""
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM subscriptions WHERE user_id=%s AND status='active' LIMIT 1",
                (user_id,),
            )
            row = cur.fetchone()
    if not row:
        return None
    return Subscription(**dict(row))


def create_subscription(user_id: str, tier: str) -> Subscription:
    """Create or upgrade a subscription for a user (cancels existing active sub)."""
    if tier not in TIERS:
        raise ValueError(f"Unknown tier: {tier!r}. Valid: {list(TIERS)}")

    now = datetime.now(timezone.utc).isoformat()
    sub_id = str(uuid.uuid4())

    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE subscriptions SET status='cancelled' WHERE user_id=%s AND status='active'",
                (user_id,),
            )
            cur.execute(
                """INSERT INTO subscriptions
                   (sub_id, user_id, tier, status, created_at, expires_at, bids_used_today)
                   VALUES (%s, %s, %s, 'active', %s, NULL, 0)""",
                (sub_id, user_id, tier, now),
            )

    logger.info("Subscription created: user=%s tier=%s sub_id=%s", user_id, tier, sub_id)
    return Subscription(
        sub_id=sub_id,
        user_id=user_id,
        tier=tier,
        status="active",
        created_at=now,
        expires_at=None,
    )


def check_bid_quota(user_id: str) -> tuple[bool, str]:
    """Check if user has bid quota remaining today. Returns (allowed, reason)."""
    sub = get_subscription(user_id)
    if not sub:
        return False, "No active subscription. Register at /saas/subscribe"

    tier_cfg = TIERS.get(sub.tier, TIERS["free"])
    limit = tier_cfg["bids_per_day"]
    if limit == -1:
        return True, "unlimited"

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT bids_used_today, last_bid_date FROM subscriptions WHERE sub_id=%s",
                (sub.sub_id,),
            )
            row = cur.fetchone()
            used: int = row["bids_used_today"] if row else 0
            last_date: str | None = row["last_bid_date"] if row else None

            if last_date != today:
                cur.execute(
                    "UPDATE subscriptions SET bids_used_today=0, last_bid_date=%s WHERE sub_id=%s",
                    (today, sub.sub_id),
                )
                used = 0

    if used >= limit:
        return False, f"Daily limit reached ({limit} bids). Upgrade to Pro or Elite."

    return True, f"{limit - used} bids remaining today"


def consume_bid(user_id: str) -> None:
    """Increment bid counter for today."""
    sub = get_subscription(user_id)
    if not sub:
        return
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE subscriptions
                   SET bids_used_today = bids_used_today + 1,
                       last_bid_date = %s
                   WHERE sub_id=%s""",
                (today, sub.sub_id),
            )
