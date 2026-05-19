"""
ADRION 369 - XRP Tracker
Fetches live XRP/USD price, calculates progress toward 1000 XRP target,
persists snapshots in the DB.
NOTE: XRP wallet is NEVER stored here — enter at transfer time only.
"""
import logging
import threading
import time
from datetime import datetime

import requests

from .config import XRP_TARGET
from .database import get_conn

log = logging.getLogger(__name__)

FALLBACK_XRP_PRICE = 2.10   # Last known price if APIs are unavailable

# Public free endpoints (no API key required)
_PRICE_ENDPOINTS = [
    # CoinGecko (free, no key)
    "https://api.coingecko.com/api/v3/simple/price?ids=ripple&vs_currencies=usd",
    # Binance public (no key)
    "https://api.binance.com/api/v3/ticker/price?symbol=XRPUSDT",
]


# ─────────────────────────────────────────────────────────────────────────────
def fetch_xrp_price() -> float:
    """Try multiple public APIs to get current XRP/USD price."""
    headers = {"User-Agent": "ADRION369/1.0"}

    # CoinGecko
    try:
        resp = requests.get(_PRICE_ENDPOINTS[0], headers=headers, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        price = float(data["ripple"]["usd"])
        log.debug("XRP price from CoinGecko: $%.4f", price)
        return price
    except Exception as e:
        log.warning("CoinGecko failed: %s", e)

    # Binance
    try:
        resp = requests.get(_PRICE_ENDPOINTS[1], headers=headers, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        price = float(data["price"])
        log.debug("XRP price from Binance: $%.4f", price)
        return price
    except Exception as e:
        log.warning("Binance failed: %s", e)

    log.warning("All XRP price APIs failed — using fallback $%.2f", FALLBACK_XRP_PRICE)
    return FALLBACK_XRP_PRICE


# ─────────────────────────────────────────────────────────────────────────────
def _get_total_earned_usd() -> float:
    """Sum all recorded USD earnings from the earnings table."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(amount_usd),0) AS total FROM earnings"
        ).fetchone()
        return float(row["total"]) if row else 0.0


def record_earning(amount_usd: float, source_note: str = "", project_id: int = None):
    """Record a USD earning event (call when a job is marked won/paid)."""
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO earnings (project_id, amount_usd, source_note) VALUES (?,?,?)",
            (project_id, amount_usd, source_note),
        )
    log.info("Earning recorded: $%.2f (%s)", amount_usd, source_note or "—")
    # Immediately take a snapshot
    update_xrp_snapshot()


def update_xrp_snapshot() -> dict:
    """
    Fetch current XRP price, compute progress, persist to DB.
    Returns snapshot dict.
    """
    price = fetch_xrp_price()
    total_usd = _get_total_earned_usd()
    xrp_equivalent = total_usd / price if price > 0 else 0.0
    pct = min((xrp_equivalent / XRP_TARGET) * 100, 100.0)

    snap = {
        "xrp_price_usd":     price,
        "total_earned_usd":  total_usd,
        "xrp_equivalent":    round(xrp_equivalent, 4),
        "xrp_target":        XRP_TARGET,
        "pct_complete":      round(pct, 2),
        "snapshot_at":       datetime.now().isoformat(timespec="seconds"),
    }

    with get_conn() as conn:
        conn.execute(
            """INSERT INTO xrp_snapshots
               (xrp_price_usd, total_earned_usd, xrp_equivalent, xrp_target, pct_complete)
               VALUES (:xrp_price_usd,:total_earned_usd,:xrp_equivalent,:xrp_target,:pct_complete)""",
            snap,
        )

    return snap


def get_progress() -> dict:
    """Return latest XRP progress snapshot (from DB, no API call)."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM xrp_snapshots ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if row:
            return {
                "xrp_price_usd":    row["xrp_price_usd"],
                "total_earned_usd": row["total_earned_usd"],
                "xrp_earned":       row["xrp_equivalent"],
                "xrp_target":       row["xrp_target"],
                "pct_complete":     row["pct_complete"],
                "snapshot_at":      row["snapshot_at"],
            }
    # No snapshots yet — return zeroed state
    return {
        "xrp_price_usd":    FALLBACK_XRP_PRICE,
        "total_earned_usd": 0.0,
        "xrp_earned":       0.0,
        "xrp_target":       XRP_TARGET,
        "pct_complete":     0.0,
        "snapshot_at":      None,
    }


def start_tracking(interval_seconds: int = 300, log_every_n: int = 10) -> threading.Thread:
    """
    Start continuous XRP price tracking loop in a background daemon thread.

    Calls update_xrp_snapshot() every `interval_seconds` and logs a summary
    every `log_every_n` iterations (StartOscillation — 528Hz regeneration rhythm).

    Args:
        interval_seconds: Pause between snapshots (default 300 = 5 min).
        log_every_n:      Log progress summary every N iterations (default 10).

    Returns:
        The started daemon Thread (can be ignored — it will stop with the process).
    """
    iteration = 0

    def _worker() -> None:
        nonlocal iteration
        log.info(
            "XRP tracker started — interval=%ds, log_every_n=%d",
            interval_seconds, log_every_n,
        )
        while True:
            try:
                snap = update_xrp_snapshot()
                iteration += 1
                if iteration % log_every_n == 0:
                    log.info(
                        "XRP oscillation #%d — price=$%.4f earned=$%.2f progress=%.1f%%",
                        iteration,
                        snap["xrp_price_usd"],
                        snap["total_earned_usd"],
                        snap["pct_complete"],
                    )
            except Exception as exc:
                log.warning("XRP snapshot failed at iteration %d: %s", iteration, exc)
            time.sleep(interval_seconds)

    t = threading.Thread(target=_worker, daemon=True, name="adrion-xrp-tracker")
    t.start()
    return t


def get_kpi_summary() -> dict:
    """Aggregated KPIs for the dashboard."""
    with get_conn() as conn:
        jobs_row = conn.execute(
            "SELECT COUNT(*) AS total, "
            "SUM(CASE WHEN status='won' THEN 1 ELSE 0 END) AS won, "
            "SUM(CASE WHEN status='bid_sent' THEN 1 ELSE 0 END) AS bid_sent "
            "FROM jobs"
        ).fetchone()

        bids_row = conn.execute(
            "SELECT COUNT(*) AS total, "
            "SUM(CASE WHEN approved=1 THEN 1 ELSE 0 END) AS approved "
            "FROM bids"
        ).fetchone()

        recent_jobs = conn.execute(
            "SELECT id,platform,title,status,budget_min,budget_max,url,scouted_at "
            "FROM jobs ORDER BY scouted_at DESC LIMIT 10"
        ).fetchall()

        recent_bids = conn.execute(
            "SELECT b.id,b.our_price,b.est_profit_usd,b.analyzer_score,b.approved,b.created_at,"
            "j.title,j.platform "
            "FROM bids b JOIN jobs j ON b.job_id=j.id "
            "ORDER BY b.created_at DESC LIMIT 10"
        ).fetchall()

    progress = get_progress()

    return {
        "jobs_total":   jobs_row["total"] or 0,
        "jobs_won":     jobs_row["won"] or 0,
        "bids_total":   bids_row["total"] or 0,
        "bids_approved": bids_row["approved"] or 0,
        "xrp":          progress,
        "recent_jobs":  [dict(r) for r in recent_jobs],
        "recent_bids":  [dict(r) for r in recent_bids],
    }
