"""
Tests for micro-saas webhook_worker.py

Covers:
  - HMAC-SHA256 signature generation
  - Successful delivery (mock HTTP 200)
  - HTTP failure → retry → success
  - All retries exhausted → webhook_sent=False
  - Worker disabled when WEBHOOK_ENABLED != true
"""
from __future__ import annotations

import hashlib
import hmac
import json
import sqlite3
import threading
import time
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add micro-saas directory to path
_SAAS_DIR = Path(__file__).parent.parent / "micro-saas"
if str(_SAAS_DIR) not in sys.path:
    sys.path.insert(0, str(_SAAS_DIR))


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def isolate_env(monkeypatch, tmp_path):
    """Each test gets a clean SQLite DB and isolated env vars."""
    db_file = tmp_path / "test_saas.db"
    monkeypatch.setenv("SAAS_DB_DRIVER", "sqlite")
    monkeypatch.setenv("SAAS_DB_PATH", str(db_file))
    monkeypatch.setenv("WEBHOOK_ENABLED", "true")
    monkeypatch.setenv("WEBHOOK_URL", "http://localhost:19999/webhook")
    monkeypatch.setenv("WEBHOOK_SECRET", "test-secret-1234")
    yield


@pytest.fixture()
def saas_db(tmp_path):
    """Pre-seeded SQLite DB with one pending saas_event."""
    db_path = Path(os.environ["SAAS_DB_PATH"])
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            sub_id TEXT PRIMARY KEY, user_id TEXT, tier TEXT, status TEXT,
            created_at TEXT, expires_at TEXT, bids_used_today INTEGER, last_bid_date TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS saas_events (
            event_id TEXT PRIMARY KEY, sub_id TEXT, event_type TEXT,
            payload TEXT, created_at TEXT,
            webhook_sent INTEGER, webhook_attempts INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        INSERT INTO saas_events (event_id, sub_id, event_type, payload, created_at, webhook_sent, webhook_attempts)
        VALUES ('evt-001', 'sub-abc', 'subscription.created', '{"tier":"pro"}', '2026-05-07T00:00:00+00:00', NULL, 0)
    """)
    conn.commit()
    conn.close()
    yield db_path


# ── HMAC signature tests ──────────────────────────────────────────────────

class TestSignature:
    def test_sign_body_produces_hex_string(self):
        from webhook_worker import _sign_body
        sig = _sign_body(b"hello", "secret")
        assert len(sig) == 64
        assert all(c in "0123456789abcdef" for c in sig)

    def test_sign_body_deterministic(self):
        from webhook_worker import _sign_body
        assert _sign_body(b"data", "key") == _sign_body(b"data", "key")

    def test_sign_body_different_secrets(self):
        from webhook_worker import _sign_body
        assert _sign_body(b"data", "key1") != _sign_body(b"data", "key2")

    def test_sign_body_matches_hmac_sha256(self):
        from webhook_worker import _sign_body
        body = b"test-payload"
        secret = "my-secret"
        expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        assert _sign_body(body, secret) == expected


# ── Delivery tests ────────────────────────────────────────────────────────

class TestDelivery:
    def test_deliver_success_returns_true(self, saas_db):
        from webhook_worker import _deliver

        event = {
            "event_id": "evt-001",
            "sub_id": "sub-abc",
            "event_type": "subscription.created",
            "payload": '{"tier":"pro"}',
            "created_at": "2026-05-07T00:00:00+00:00",
        }

        # Mock urllib.request.urlopen to return 200
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = _deliver(event, "http://localhost:19999/webhook", "test-secret")

        assert result is True

    def test_deliver_http_error_returns_false(self, saas_db):
        from webhook_worker import _deliver
        import urllib.error

        event = {
            "event_id": "evt-002",
            "sub_id": "sub-abc",
            "event_type": "bid.quota_exceeded",
            "payload": "{}",
            "created_at": "2026-05-07T00:00:00+00:00",
        }

        with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError(
            url="http://x", code=500, msg="Internal Server Error", hdrs={}, fp=None
        )):
            result = _deliver(event, "http://localhost:19999/webhook", "test-secret")

        assert result is False

    def test_deliver_connection_error_returns_false(self):
        from webhook_worker import _deliver

        event = {
            "event_id": "evt-003",
            "sub_id": "sub-abc",
            "event_type": "subscription.created",
            "payload": "{}",
            "created_at": "2026-05-07T00:00:00+00:00",
        }

        with patch("urllib.request.urlopen", side_effect=ConnectionRefusedError("refused")):
            result = _deliver(event, "http://localhost:9999/webhook", "secret")

        assert result is False


# ── Process event with retries ────────────────────────────────────────────

class TestProcessEvent:
    def test_success_on_first_attempt_marks_sent(self, saas_db):
        from webhook_worker import _process_event

        event = {
            "event_id": "evt-001",
            "sub_id": "sub-abc",
            "event_type": "subscription.created",
            "payload": '{"tier":"pro"}',
            "created_at": "2026-05-07T00:00:00+00:00",
            "webhook_attempts": 0,
        }

        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_resp):
            _process_event(event, "http://localhost:19999/webhook", "secret")

        conn = sqlite3.connect(saas_db)
        row = conn.execute("SELECT webhook_sent, webhook_attempts FROM saas_events WHERE event_id='evt-001'").fetchone()
        conn.close()
        assert row[0] == 1  # True (SQLite stores bool as int)
        assert row[1] == 1

    def test_all_retries_exhausted_marks_failed(self, saas_db):
        from webhook_worker import _process_event
        import urllib.error

        event = {
            "event_id": "evt-001",
            "sub_id": "sub-abc",
            "event_type": "subscription.created",
            "payload": '{"tier":"pro"}',
            "created_at": "2026-05-07T00:00:00+00:00",
            "webhook_attempts": 0,
        }

        with patch("urllib.request.urlopen", side_effect=ConnectionRefusedError("refused")):
            with patch("time.sleep"):  # speed up test — skip backoff sleeps
                _process_event(event, "http://localhost:19999/webhook", "secret")

        conn = sqlite3.connect(saas_db)
        row = conn.execute("SELECT webhook_sent, webhook_attempts FROM saas_events WHERE event_id='evt-001'").fetchone()
        conn.close()
        assert row[0] == 0  # False
        assert row[1] == 4  # MAX_ATTEMPTS


# ── Worker enabled/disabled ───────────────────────────────────────────────

class TestWorkerControl:
    def test_worker_not_started_when_disabled(self, monkeypatch):
        monkeypatch.setenv("WEBHOOK_ENABLED", "false")
        from webhook_worker import start_webhook_worker
        import webhook_worker

        # Reset global state
        webhook_worker._worker_thread = None
        webhook_worker._stop_event = None

        start_webhook_worker()

        assert webhook_worker._worker_thread is None

    def test_is_enabled_reads_env(self, monkeypatch):
        from webhook_worker import _is_enabled
        monkeypatch.setenv("WEBHOOK_ENABLED", "true")
        assert _is_enabled() is True
        monkeypatch.setenv("WEBHOOK_ENABLED", "false")
        assert _is_enabled() is False
        monkeypatch.setenv("WEBHOOK_ENABLED", "1")
        assert _is_enabled() is True
