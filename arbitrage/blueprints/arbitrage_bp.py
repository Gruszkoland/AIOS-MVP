"""
ADRION 369 - Arbitrage Blueprint: Core arbitrage routes.

Routes:
  GET  /api/arbitrage/status
  GET  /api/arbitrage/kpis
  GET  /api/arbitrage/stats
  GET  /api/arbitrage/jobs
  GET  /api/arbitrage/bids/pending
  POST /api/arbitrage/bids/<id>/approve
  POST /api/arbitrage/scout
  POST /api/arbitrage/analyze-batch
  POST /api/arbitrage/cycle
"""

import logging
import threading
from datetime import datetime

from flask import Blueprint, jsonify, request

arbitrage_bp = Blueprint("arbitrage", __name__)
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Lazy imports (same pattern as original api.py)
# ──────────────────────────────────────────────────────────────────────────────

def _db():
    from arbitrage.database import approve_bid, get_jobs, get_pending_bids, get_totals, init_db
    return get_jobs, get_pending_bids, approve_bid, get_totals, init_db


def _scout_fn():
    from arbitrage.scout import run_scout
    return run_scout


def _analyzer():
    from arbitrage.analyzer import analyze_job, filter_worthy
    from arbitrage.bidder import create_bid
    return analyze_job, filter_worthy, create_bid


def _config():
    from arbitrage.config import DAILY_BID_LIMIT, MIN_ANALYZER_SCORE, get_active_llm_backend
    return DAILY_BID_LIMIT, MIN_ANALYZER_SCORE, get_active_llm_backend


def _rate_limiters():
    from arbitrage.rate_limiter import cycle_limiter, mass_gen_limiter, scout_limiter
    return scout_limiter, mass_gen_limiter, cycle_limiter


# ──────────────────────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────────────────────

@arbitrage_bp.route("/api/arbitrage/status", methods=["GET"])
def handle_status():
    DAILY_BID_LIMIT, MIN_ANALYZER_SCORE, get_active_llm_backend = _config()
    get_jobs, get_pending_bids, _, get_totals, _ = _db()
    totals = get_totals()
    pending = get_pending_bids()
    return jsonify({
        "llm_backend":      get_active_llm_backend(),
        "total_jobs":       totals.get("total_jobs", 0),
        "bids_sent":        totals.get("bids_sent", 0),
        "pending_bids":     len(pending),
        "daily_bid_limit":  DAILY_BID_LIMIT,
        "timestamp":        datetime.now().isoformat(),
    })


@arbitrage_bp.route("/api/arbitrage/kpis", methods=["GET"])
def handle_kpis():
    _, _, _, get_totals, _ = _db()
    totals = get_totals()
    return jsonify({**totals, "timestamp": datetime.now().isoformat()})


@arbitrage_bp.route("/api/arbitrage/stats", methods=["GET"])
def handle_stats():
    from arbitrage.xrp import get_progress
    return jsonify(get_progress())


@arbitrage_bp.route("/api/arbitrage/jobs", methods=["GET"])
def handle_jobs():
    get_jobs, _, _, _, _ = _db()
    jobs = get_jobs(limit=20)
    return jsonify({"jobs": jobs, "count": len(jobs)})


@arbitrage_bp.route("/api/arbitrage/bids/pending", methods=["GET"])
def handle_bids_pending():
    _, get_pending_bids, _, _, _ = _db()
    bids = get_pending_bids()
    return jsonify({"bids": bids, "count": len(bids)})


@arbitrage_bp.route("/api/arbitrage/bids/<int:bid_id>/approve", methods=["POST"])
def handle_bid_approve(bid_id: int):
    body = request.get_json(silent=True) or {}
    approved = bool(body.get("approved", True))
    _, _, approve_bid, _, _ = _db()
    approve_bid(bid_id, approved)
    return jsonify({"ok": True, "bid_id": bid_id, "approved": approved})


@arbitrage_bp.route("/api/arbitrage/scout", methods=["POST"])
def handle_scout():
    scout_limiter, _, _ = _rate_limiters()
    client_ip = request.remote_addr
    if not scout_limiter.is_allowed(client_ip):
        return jsonify({"error": "Rate limit exceeded", "retry_after": 60}), 429
    run_scout = _scout_fn()
    result = run_scout()
    return jsonify(result)


@arbitrage_bp.route("/api/arbitrage/analyze-batch", methods=["POST"])
def handle_analyze_batch():
    _, mass_gen_limiter, _ = _rate_limiters()
    client_ip = request.remote_addr
    if not mass_gen_limiter.is_allowed(client_ip):
        return jsonify({"error": "Rate limit exceeded", "retry_after": 60}), 429
    get_jobs, _, _, _, _ = _db()
    analyze_job, filter_worthy, create_bid = _analyzer()
    DAILY_BID_LIMIT, MIN_ANALYZER_SCORE, _ = _config()

    new_jobs = get_jobs(status="new", limit=50)
    bids_created, analyzed = 0, 0

    for job in new_jobs:
        if bids_created >= DAILY_BID_LIMIT:
            break
        try:
            analysis = analyze_job(job)
            analyzed += 1
            if filter_worthy(analysis):
                create_bid(job, analysis)
                bids_created += 1
        except Exception as exc:
            logger.warning("Analyze failed for %s: %s", job.get("id"), exc)

    return jsonify({
        "analyzed":     analyzed,
        "bids_created": bids_created,
        "timestamp":    datetime.now().isoformat(),
    })


@arbitrage_bp.route("/api/arbitrage/cycle", methods=["POST"])
def handle_cycle():
    """Run scout + analyze in background, return immediately."""
    _, _, cycle_limiter = _rate_limiters()
    client_ip = request.remote_addr
    if not cycle_limiter.is_allowed(client_ip):
        return jsonify({"error": "Rate limit exceeded", "retry_after": 60}), 429

    def _run():
        run_scout = _scout_fn()
        get_jobs, _, _, _, _ = _db()
        analyze_job, filter_worthy, create_bid = _analyzer()
        DAILY_BID_LIMIT, _, _ = _config()
        run_scout()
        for job in get_jobs(status="new", limit=50):
            try:
                analysis = analyze_job(job)
                if filter_worthy(analysis):
                    create_bid(job, analysis)
            except Exception as exc:
                logger.warning("Cycle analyze error: %s", exc)

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return jsonify({"ok": True, "message": "Pipeline cycle started in background"})
