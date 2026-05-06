"""
micro-saas Prometheus metrics module.

Exposes Counters for subscription and bid activity.
Metrics are collected by the shared Prometheus scrape target
defined in monitoring/prometheus.yml (job: adrion-micro-saas).

Usage:
  from metrics import SUBSCRIBE_COUNTER, BID_COUNTER, record_subscribe, record_bid
  record_subscribe("pro")
  record_bid("u-123", allowed=True)
"""
from __future__ import annotations

import logging
import os

logger = logging.getLogger("adrion.micro_saas.metrics")

# prometheus_client is optional — if absent, metrics are no-ops.
try:
    from prometheus_client import Counter, make_wsgi_app, REGISTRY

    _ENABLED = True
    logger.info("prometheus_client loaded — metrics active")
except ImportError:
    _ENABLED = False
    logger.warning("prometheus_client not installed — metrics disabled (pip install prometheus-client)")

# ── Counters ──────────────────────────────────────────────────────────────

if _ENABLED:
    SUBSCRIBE_COUNTER: Counter = Counter(
        "saas_subscriptions_total",
        "Total subscriptions created or upgraded",
        ["tier"],
    )
    BID_COUNTER: Counter = Counter(
        "saas_bids_total",
        "Total bid quota checks",
        ["allowed"],
    )
    BID_CONSUME_COUNTER: Counter = Counter(
        "saas_bid_consumed_total",
        "Total bids consumed (quota decremented)",
        [],
    )
else:
    # Stub objects — .labels(...).inc() is a no-op
    class _NullCounter:
        def labels(self, **_kw):
            return self
        def inc(self, _amount=1):
            pass

    SUBSCRIBE_COUNTER = _NullCounter()  # type: ignore[assignment]
    BID_COUNTER = _NullCounter()  # type: ignore[assignment]
    BID_CONSUME_COUNTER = _NullCounter()  # type: ignore[assignment]


# ── Convenience helpers ───────────────────────────────────────────────────

def record_subscribe(tier: str) -> None:
    """Increment subscription counter for the given tier."""
    SUBSCRIBE_COUNTER.labels(tier=tier).inc()


def record_bid(allowed: bool) -> None:
    """Increment bid-check counter."""
    BID_COUNTER.labels(allowed=str(allowed).lower()).inc()


def record_bid_consumed() -> None:
    """Increment bid-consumed counter."""
    BID_CONSUME_COUNTER.inc()


def prometheus_wsgi_app():
    """Return a WSGI app that serves /metrics for Prometheus scraping.

    Mount on the Flask app:
        from metrics import prometheus_wsgi_app
        from werkzeug.middleware.dispatcher import DispatcherMiddleware
        app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {"/metrics": prometheus_wsgi_app()})
    """
    if not _ENABLED:
        def _stub_app(environ, start_response):
            body = b"# prometheus_client not installed\n"
            start_response("200 OK", [("Content-Type", "text/plain")])
            return [body]
        return _stub_app
    return make_wsgi_app()
