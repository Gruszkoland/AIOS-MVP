"""
ADRION 369 — micro-saas Webhook Worker

Polls saas_events (webhook_sent IS NULL) and delivers payloads via HTTP POST
with HMAC-SHA256 signature. Runs as a daemon thread inside the Flask process.

Configuration (env vars):
  WEBHOOK_URL      — target URL for event delivery (required if WEBHOOK_ENABLED=true)
  WEBHOOK_SECRET   — HMAC-SHA256 signing secret (required if WEBHOOK_ENABLED=true)
  WEBHOOK_ENABLED  — "true" / "false" (default: false — opt-in)
  WEBHOOK_TIMEOUT  — HTTP request timeout seconds (default: 5)

Retry strategy: exponential backoff — 1s, 2s, 4s, 8s (max 4 attempts).
After all retries fail: webhook_sent=False, webhook_attempts=N.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from threading import Event, Thread
from typing import Optional

logger = logging.getLogger("adrion.micro_saas.webhook_worker")

# ── Runtime config ────────────────────────────────────────────────────────

_POLL_INTERVAL = int(os.getenv("WEBHOOK_POLL_INTERVAL", "10"))  # seconds
_TIMEOUT = int(os.getenv("WEBHOOK_TIMEOUT", "5"))
_MAX_ATTEMPTS = 4
_BACKOFF_BASE = 1  # seconds — doubles each retry


def _is_enabled() -> bool:
    return os.getenv("WEBHOOK_ENABLED", "false").lower() in ("1", "true", "yes")


def _get_webhook_url() -> Optional[str]:
    return os.getenv("WEBHOOK_URL")


def _get_webhook_secret() -> Optional[str]:
    return os.getenv("WEBHOOK_SECRET")


# ── HMAC signature ────────────────────────────────────────────────────────

def _sign_body(body: bytes, secret: str) -> str:
    """Return hex-encoded HMAC-SHA256 signature."""
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


# ── DB helpers (SQLite + PostgreSQL via driver detection) ─────────────────

def _get_conn():
    """
    Return a DB connection appropriate for the configured driver.
    Mirrors billing.py / billing_pg.py connection patterns.
    """
    driver = os.getenv("SAAS_DB_DRIVER", "sqlite").lower()
    if driver == "postgres":
        import psycopg2
        url = os.getenv("DATABASE_URL", "")
        return psycopg2.connect(url)
    else:
        db_path = Path(os.getenv("SAAS_DB_PATH", "micro-saas/data/subscriptions.db"))
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn


def _placeholder() -> str:
    """SQL placeholder: %s for PG, ? for SQLite."""
    return "%s" if os.getenv("SAAS_DB_DRIVER", "sqlite").lower() == "postgres" else "?"


# ── Pending event fetch ───────────────────────────────────────────────────

def _fetch_pending(conn, limit: int = 20) -> list[dict]:
    """Fetch events not yet delivered (webhook_sent IS NULL)."""
    p = _placeholder()
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT event_id, sub_id, event_type, payload, created_at,
                   COALESCE(webhook_attempts, 0) AS webhook_attempts
            FROM saas_events
            WHERE webhook_sent IS NULL
              AND COALESCE(webhook_attempts, 0) < {p}
            ORDER BY created_at ASC
            LIMIT {p}
            """,
            (_MAX_ATTEMPTS, limit),
        )
        columns = [d[0] for d in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    except Exception as exc:
        logger.warning("Failed to fetch pending events: %s", exc)
        return []


# ── Mark event result ─────────────────────────────────────────────────────

def _mark_event(conn, event_id: str, success: bool, attempts: int) -> None:
    p = _placeholder()
    try:
        conn.cursor().execute(
            f"""UPDATE saas_events
                SET webhook_sent = {p}, webhook_attempts = {p}
                WHERE event_id = {p}""",
            (success, attempts, event_id),
        )
        conn.commit()
    except Exception as exc:
        logger.warning("Failed to mark event %s: %s", event_id, exc)


def _increment_attempts(conn, event_id: str, attempts: int) -> None:
    p = _placeholder()
    try:
        conn.cursor().execute(
            f"UPDATE saas_events SET webhook_attempts = {p} WHERE event_id = {p}",
            (attempts, event_id),
        )
        conn.commit()
    except Exception as exc:
        logger.warning("Failed to increment attempts for %s: %s", event_id, exc)


# ── HTTP delivery ─────────────────────────────────────────────────────────

def _deliver(event: dict, url: str, secret: str) -> bool:
    """
    POST event payload to webhook URL with HMAC-SHA256 signature.
    Returns True on HTTP 2xx, False otherwise.
    """
    import urllib.error
    import urllib.request

    body = json.dumps(
        {
            "event_id": event["event_id"],
            "sub_id": event["sub_id"],
            "event_type": event["event_type"],
            "payload": json.loads(event["payload"] or "{}"),
            "created_at": event["created_at"],
            "sent_at": datetime.now(timezone.utc).isoformat(),
        },
        ensure_ascii=False,
    ).encode()

    signature = _sign_body(body, secret)

    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-ADRION-Signature": f"sha256={signature}",
            "X-ADRION-Event": event["event_type"],
            "User-Agent": "ADRION-WebhookWorker/1.4.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            if 200 <= resp.status < 300:
                logger.info(
                    "Webhook delivered: event=%s type=%s status=%s",
                    event["event_id"],
                    event["event_type"],
                    resp.status,
                )
                return True
            logger.warning(
                "Webhook non-2xx: event=%s status=%s",
                event["event_id"],
                resp.status,
            )
            return False
    except urllib.error.HTTPError as exc:
        logger.warning("Webhook HTTP error: event=%s code=%s", event["event_id"], exc.code)
        return False
    except Exception as exc:
        logger.warning("Webhook delivery failed: event=%s err=%s", event["event_id"], exc)
        return False


# ── Worker loop ───────────────────────────────────────────────────────────

def _process_event(event: dict, url: str, secret: str) -> None:
    """Try to deliver a single event with exponential backoff."""
    attempts = int(event.get("webhook_attempts", 0))

    conn = _get_conn()
    try:
        for attempt in range(_MAX_ATTEMPTS - attempts):
            current_attempt = attempts + attempt + 1
            wait = _BACKOFF_BASE * (2 ** attempt)

            if attempt > 0:
                logger.debug(
                    "Retry %d/%d for event %s — waiting %ds",
                    current_attempt,
                    _MAX_ATTEMPTS,
                    event["event_id"],
                    wait,
                )
                time.sleep(wait)

            if _deliver(event, url, secret):
                _mark_event(conn, event["event_id"], success=True, attempts=current_attempt)
                return

            _increment_attempts(conn, event["event_id"], current_attempt)

        # All retries exhausted
        logger.error(
            "Webhook failed after %d attempts for event=%s type=%s",
            _MAX_ATTEMPTS,
            event["event_id"],
            event["event_type"],
        )
        _mark_event(conn, event["event_id"], success=False, attempts=_MAX_ATTEMPTS)
    finally:
        conn.close()


def _worker_loop(stop_event: Event) -> None:
    logger.info("Webhook worker started (poll_interval=%ds)", _POLL_INTERVAL)
    while not stop_event.is_set():
        url = _get_webhook_url()
        secret = _get_webhook_secret()

        if not url or not secret:
            logger.debug("WEBHOOK_URL or WEBHOOK_SECRET not set — skipping poll")
        else:
            conn = _get_conn()
            try:
                pending = _fetch_pending(conn)
            finally:
                conn.close()

            for event in pending:
                if stop_event.is_set():
                    break
                _process_event(event, url, secret)

        stop_event.wait(timeout=_POLL_INTERVAL)

    logger.info("Webhook worker stopped")


# ── Public API ────────────────────────────────────────────────────────────

_worker_thread: Optional[Thread] = None
_stop_event: Optional[Event] = None


def start_webhook_worker() -> None:
    """Start the background webhook delivery thread if WEBHOOK_ENABLED=true."""
    global _worker_thread, _stop_event

    if not _is_enabled():
        logger.info("Webhook worker disabled (WEBHOOK_ENABLED != true)")
        return

    if _worker_thread is not None and _worker_thread.is_alive():
        logger.warning("Webhook worker already running")
        return

    _stop_event = Event()
    _worker_thread = Thread(
        target=_worker_loop,
        args=(_stop_event,),
        name="adrion-webhook-worker",
        daemon=True,
    )
    _worker_thread.start()
    logger.info("Webhook worker thread started")


def stop_webhook_worker() -> None:
    """Signal the worker thread to stop gracefully."""
    global _stop_event
    if _stop_event:
        _stop_event.set()
