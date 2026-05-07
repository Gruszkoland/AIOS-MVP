"""
ADRION 369 — micro-saas Billing & Pricing Tiers

Defines subscription tiers for the ADRION SaaS product:
  FREE  — 5 bids/day,  no RAG,   no Oracle
  PRO   — 100 bids/day, RAG,     Oracle access
  ELITE — unlimited,   full MCP, priority LLM queue

Subscriptions are stored in SQLite (dev) or PostgreSQL (prod) via
the same DatabaseEngine used by the UAP backend.
"""
from __future__ import annotations

import logging
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger("adrion.micro_saas.billing")

# ── Tier definitions ──────────────────────────────────────────────────────

TIERS: dict[str, dict] = {
    "free": {
        "name": "Free",
        "price_eur_monthly": 0.0,
        "bids_per_day": 5,
        "rag_enabled": False,
        "oracle_enabled": False,
        "mcp_access": False,
        "priority_llm": False,
        "description": "Start for free — 5 arbitrage scans per day, no RAG.",
    },
    "pro": {
        "name": "Pro",
        "price_eur_monthly": 29.0,
        "bids_per_day": 100,
        "rag_enabled": True,
        "oracle_enabled": True,
        "mcp_access": False,
        "priority_llm": False,
        "description": "RAG enrichment + Oracle predictions. For active traders.",
    },
    "elite": {
        "name": "Elite",
        "price_eur_monthly": 99.0,
        "bids_per_day": -1,  # unlimited
        "rag_enabled": True,
        "oracle_enabled": True,
        "mcp_access": True,
        "priority_llm": True,
        "description": "Unlimited bids, full MCP tier access, priority LLM queue.",
    },
}


@dataclass
class Subscription:
    """Active subscription record."""
    sub_id: str
    user_id: str
    tier: str
    status: str  # active | cancelled | expired
    created_at: str
    expires_at: Optional[str]
    bids_used_today: int = 0


# ── SQLite-backed subscription store (dev / single-node prod) ─────────────

_DB_PATH = Path(os.getenv("SAAS_DB_PATH", "micro-saas/data/subscriptions.db"))


def _get_conn() -> sqlite3.Connection:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_saas_db() -> None:
    """Create tables if they don't exist."""
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                sub_id       TEXT PRIMARY KEY,
                user_id      TEXT NOT NULL,
                tier         TEXT NOT NULL DEFAULT 'free',
                status       TEXT NOT NULL DEFAULT 'active',
                created_at   TEXT NOT NULL,
                expires_at   TEXT,
                bids_used_today INTEGER NOT NULL DEFAULT 0,
                last_bid_date   TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS saas_events (
                event_id   TEXT PRIMARY KEY,
                sub_id     TEXT NOT NULL,
                event_type TEXT NOT NULL,
                payload    TEXT,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()
    logger.info("SaaS DB initialized at %s", _DB_PATH)


def get_subscription(user_id: str) -> Optional[Subscription]:
    """Fetch active subscription for a user; returns None if not subscribed."""
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM subscriptions WHERE user_id=? AND status='active' LIMIT 1",
            (user_id,),
        ).fetchone()
    if not row:
        return None
    return Subscription(**dict(row))


def create_subscription(user_id: str, tier: str) -> Subscription:
    """Create or upgrade a subscription for a user."""
    import uuid

    if tier not in TIERS:
        raise ValueError(f"Unknown tier: {tier!r}. Valid: {list(TIERS)}")

    now = datetime.now(timezone.utc).isoformat()
    sub_id = str(uuid.uuid4())

    with _get_conn() as conn:
        # Cancel any existing active sub
        conn.execute(
            "UPDATE subscriptions SET status='cancelled' WHERE user_id=? AND status='active'",
            (user_id,),
        )
        conn.execute(
            """INSERT INTO subscriptions
               (sub_id, user_id, tier, status, created_at, expires_at, bids_used_today)
               VALUES (?, ?, ?, 'active', ?, NULL, 0)""",
            (sub_id, user_id, tier, now),
        )
        conn.commit()

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
    """
    Check if user has bid quota remaining today.
    Returns (allowed: bool, reason: str).
    Resets counter at midnight UTC.
    """
    sub = get_subscription(user_id)
    if not sub:
        # Default to free tier limits for unregistered users
        tier_cfg = TIERS["free"]
        return False, "No active subscription. Register at /saas/subscribe"

    tier_cfg = TIERS.get(sub.tier, TIERS["free"])
    limit = tier_cfg["bids_per_day"]

    if limit == -1:
        return True, "unlimited"

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT bids_used_today, last_bid_date FROM subscriptions WHERE sub_id=?",
            (sub.sub_id,),
        ).fetchone()
        used = row["bids_used_today"] if row else 0
        last_date = row["last_bid_date"] if row else None

        if last_date != today:
            # Reset counter for new day
            conn.execute(
                "UPDATE subscriptions SET bids_used_today=0, last_bid_date=? WHERE sub_id=?",
                (today, sub.sub_id),
            )
            conn.commit()
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
        conn.execute(
            """UPDATE subscriptions
               SET bids_used_today = bids_used_today + 1,
                   last_bid_date = ?
               WHERE sub_id=?""",
            (today, sub.sub_id),
        )
        conn.commit()


def emit_event(sub_id: str, event_type: str, payload: Optional[dict] = None) -> None:
    """
    Persist an event to saas_events for webhook delivery.

    event_type examples:
      - subscription.created
      - bid.quota_exceeded
      - subscription.expired
    """
    import json as _json
    import uuid

    event_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    payload_str = _json.dumps(payload or {})

    with _get_conn() as conn:
        conn.execute(
            """
            INSERT INTO saas_events
                (event_id, sub_id, event_type, payload, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (event_id, sub_id, event_type, payload_str, now),
        )
        conn.commit()
    logger.debug("Event emitted: %s type=%s sub=%s", event_id, event_type, sub_id)
