"""
ADRION 369 - Arbitrage Flask API Server
Endpoints under /api/arbitrage/*
Run: python arbitrage_server.py
"""
import os
import sys
import threading
import logging
import time
import warnings
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS

from arbitrage.database import init_db, get_jobs, get_pending_bids, get_all_bids, approve_bid, get_totals, set_job_status
from arbitrage.config   import (
    XRP_TARGET,
    DAILY_BID_LIMIT,
    MAX_EST_COST_PER_BID_USD,
    MAX_BIDS_PER_CLIENT_PER_DAY,
    MAX_DAILY_EST_COST_USD,
    UGC_EVENTS_DAILY_CAP,
    RESALE_EVENTS_DAILY_CAP,
    get_active_llm_backend,
)
from arbitrage.scout    import run_scout
from arbitrage.analyzer import analyze_job, filter_worthy
from arbitrage.bidder   import create_bid
from arbitrage.executor import generate_content
from arbitrage.autopilot import autopilot_service
from arbitrage.database import get_recent_autopilot_runs, get_stream_kpis, record_kpi_event
from arbitrage.stream_emitters import run_aux_streams, get_stream_sources_status

logging.basicConfig(level=logging.INFO, format="%(asctime)s level=%(levelname)s logger=%(name)s %(message)s")
logger = logging.getLogger("adrion.api")

warnings.warn(
    "arbitrage_server.py is deprecated. Use arbitrage.app:create_app() instead.",
    DeprecationWarning,
    stacklevel=2,
)
logger.warning("arbitrage_server.py is deprecated. Use arbitrage.app:create_app() instead.")

STREAMS_CONNECTOR_TOKEN = os.getenv("STREAMS_CONNECTOR_TOKEN", "")

app = Flask(__name__)
CORS(app, origins=[os.getenv("CORS_ALLOWED_ORIGIN", "http://localhost:8003")])


@app.before_request
def start_request_timer():
    request.environ["adrion.request_started_at"] = time.perf_counter()


@app.after_request
def log_request(response):
    started_at = request.environ.get("adrion.request_started_at")
    duration_ms = int((time.perf_counter() - started_at) * 1000) if started_at else -1
    log_method = logger.error if response.status_code >= 500 else logger.warning if response.status_code >= 400 else logger.info
    log_method(
        "event=request method=%s path=%s status=%s duration_ms=%s remote_addr=%s",
        request.method,
        request.path,
        response.status_code,
        duration_ms,
        request.remote_addr or "unknown",
    )
    return response

# ── Health ─────────────────────────────────────────────────────────────────

@app.route("/api/arbitrage/status", methods=["GET"])
def status():
    return jsonify({
        "status":      "online",
        "llm_backend": get_active_llm_backend(),
        "xrp_target":  XRP_TARGET,
        "stream_caps": {
            "ugc_events_daily_cap": UGC_EVENTS_DAILY_CAP,
            "resale_events_daily_cap": RESALE_EVENTS_DAILY_CAP,
        },
        "stream_sources": get_stream_sources_status(),
        "timestamp":   datetime.now().isoformat(),
    })


# ── Scout ──────────────────────────────────────────────────────────────────

@app.route("/api/arbitrage/scout", methods=["POST"])
def scout():
    """Run Scout agent. Body: {"platforms":[], "keywords":[], "use_mock": bool}"""
    body = request.get_json(silent=True) or {}
    result = run_scout(
        platforms=body.get("platforms"),
        keywords=body.get("keywords"),
        use_mock=body.get("use_mock", None),
    )
    return jsonify(result)


@app.route("/api/arbitrage/jobs", methods=["GET"])
def list_jobs():
    status_filter = request.args.get("status")
    limit = int(request.args.get("limit", 50))
    jobs = get_jobs(status=status_filter, limit=limit)
    return jsonify({"jobs": jobs, "count": len(jobs)})


# ── Analyzer ────────────────────────────────────────────────────────────────

@app.route("/api/arbitrage/analyze/<job_id>", methods=["POST"])
def analyze(job_id: str):
    """Analyze a specific job and optionally auto-create a bid."""
    jobs = get_jobs()
    job = next((j for j in jobs if j["id"] == job_id), None)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    analysis = analyze_job(job)
    worthy   = filter_worthy(analysis)

    result = {
        "job_id":   job_id,
        "analysis": analysis,
        "worthy":   worthy,
        "bid":      None,
    }

    if worthy:
        bid = create_bid(job, analysis)
        result["bid"] = bid

    return jsonify(result)


@app.route("/api/arbitrage/analyze-batch", methods=["POST"])
def analyze_batch():
    """Analyze all 'new' jobs and create bids for worthy ones."""
    new_jobs = get_jobs(status="new", limit=20)
    results  = []

    for job in new_jobs:
        analysis = analyze_job(job)
        worthy   = filter_worthy(analysis)
        bid = create_bid(job, analysis) if worthy else None
        results.append({
            "job_id":  job["id"],
            "title":   job["title"],
            "score":   analysis.get("score", 0),
            "profit":  analysis.get("est_profit", 0),
            "worthy":  worthy,
            "bid_created": bid is not None,
        })

    return jsonify({"analyzed": len(results), "results": results})


# ── Bidder ──────────────────────────────────────────────────────────────────

@app.route("/api/arbitrage/bids/pending", methods=["GET"])
def pending_bids():
    bids = get_pending_bids()
    return jsonify({"bids": bids, "count": len(bids)})


@app.route("/api/arbitrage/bids", methods=["GET"])
def all_bids():
    limit = int(request.args.get("limit", 100))
    bids = get_all_bids(limit=limit)
    return jsonify({"bids": bids, "count": len(bids)})


@app.route("/api/arbitrage/bids/<int:bid_id>/approve", methods=["POST"])
def approve(bid_id: int):
    """Approve or reject a bid. Body: {"approved": true|false}"""
    body     = request.get_json(silent=True) or {}
    approved = bool(body.get("approved", True))
    approve_bid(bid_id, approved)
    action = "approved" if approved else "rejected"
    return jsonify({"bid_id": bid_id, "action": action})


# ── Executor ────────────────────────────────────────────────────────────────

@app.route("/api/arbitrage/execute/<job_id>", methods=["POST"])
def execute(job_id: str):
    """Generate content deliverable for a won job."""
    body       = request.get_json(silent=True) or {}
    word_count = int(body.get("word_count", 800))

    jobs = get_jobs()
    job  = next((j for j in jobs if j["id"] == job_id), None)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    content = generate_content(job, word_count=word_count)
    set_job_status(job_id, "won")

    return jsonify({
        "job_id":     job_id,
        "word_count": len(content.split()),
        "content":    content,
    })


# ── KPIs ────────────────────────────────────────────────────────────────────

@app.route("/api/arbitrage/kpis", methods=["GET"])
def kpis():
    totals = get_totals()
    stream_kpis = get_stream_kpis()
    xrp_price_usd = 2.5  # approximate; update dynamically if needed
    profit = totals.get("total_profit", 0)
    return jsonify({
        "totals":           totals,
        "stream_kpis":      stream_kpis,
        "xrp_target":       XRP_TARGET,
        "xrp_earned_est":   round(profit / xrp_price_usd, 2),
        "xrp_remaining":    round(XRP_TARGET - (profit / xrp_price_usd), 2),
        "pct_complete":     round((profit / xrp_price_usd) / XRP_TARGET * 100, 1),
        "llm_backend":      get_active_llm_backend(),
        "guardrails": {
            "daily_bid_limit": DAILY_BID_LIMIT,
            "max_est_cost_per_bid_usd": MAX_EST_COST_PER_BID_USD,
            "max_daily_est_cost_usd": MAX_DAILY_EST_COST_USD,
            "max_bids_per_client_per_day": MAX_BIDS_PER_CLIENT_PER_DAY,
        },
    })


@app.route("/api/arbitrage/kpis/streams", methods=["GET"])
def kpi_streams():
    return jsonify(get_stream_kpis())


@app.route("/api/arbitrage/kpis/events", methods=["POST"])
def kpi_event_ingest():
    body = request.get_json(silent=True) or {}
    stream = str(body.get("stream", "")).strip().lower()
    event_type = str(body.get("event_type", "")).strip().lower()

    if stream not in {"b2b", "ugc", "resale"}:
        return jsonify({"error": "Invalid stream. Expected one of: b2b, ugc, resale"}), 400
    if not event_type:
        return jsonify({"error": "event_type is required"}), 400

    amount_usd = float(body.get("amount_usd", 0) or 0)
    est_cost_usd = float(body.get("est_cost_usd", 0) or 0)
    meta = body.get("meta") if isinstance(body.get("meta"), dict) else {}

    record_kpi_event(
        stream=stream,
        event_type=event_type,
        amount_usd=amount_usd,
        est_cost_usd=est_cost_usd,
        meta=meta,
    )
    return jsonify({"status": "recorded", "stream": stream, "event_type": event_type})


@app.route("/api/arbitrage/streams/ingest", methods=["POST"])
def stream_ingest_webhook():
    """
    Model Webhookowy (Phase 2): Pozwala systemom zewnętrznym (n8n)
    na wypychanie (PUSH) danych bezpośrednio do strumieni ADRION.
    """
    # Authorization check
    auth_header = request.headers.get("Authorization")
    if STREAMS_CONNECTOR_TOKEN:
        expected = f"Bearer {STREAMS_CONNECTOR_TOKEN}"
        if auth_header != expected:
            return jsonify({"error": "Unauthorized"}), 401

    body = request.get_json(silent=True) or {}
    stream = str(body.get("stream", "")).strip().lower()

    if stream not in {"ugc", "resale"}:
        return jsonify({"error": "Invalid stream. Expected 'ugc' or 'resale'"}), 400

    from arbitrage.stream_emitters import _normalize_external_events, _emit_events

    # Normalize potential single event or list of events
    payload = body.get("data") or body.get("events") or [body]
    events = _normalize_external_events(stream, payload)

    if not events:
        return jsonify({"status": "ignored", "reason": "no_valid_events_found"}), 200

    emitted = _emit_events(stream, events, dry_run=False)

    return jsonify({
        "status": "received",
        "stream": stream,
        "emitted_count": emitted,
        "timestamp": datetime.utcnow().isoformat()
    })


@app.route("/api/arbitrage/streams/run", methods=["POST"])
def run_stream_emitters():
    body = request.get_json(silent=True) or {}
    dry_run = bool(body.get("dry_run", False))
    result = run_aux_streams(
        ugc_daily_cap=int(body.get("ugc_daily_cap", UGC_EVENTS_DAILY_CAP)),
        resale_daily_cap=int(body.get("resale_daily_cap", RESALE_EVENTS_DAILY_CAP)),
        dry_run=dry_run,
    )
    return jsonify({"status": "ok", "result": result, "sources": get_stream_sources_status()})


# ── Autopilot control ───────────────────────────────────────────────────────

@app.route("/api/arbitrage/autopilot/status", methods=["GET"])
def autopilot_status():
    return jsonify(autopilot_service.get_status())


@app.route("/api/arbitrage/autopilot/start", methods=["POST"])
def autopilot_start():
    body = request.get_json(silent=True) or {}
    interval_minutes = int(body.get("interval_minutes", 30))
    dry_run = bool(body.get("dry_run", False))
    status_payload = autopilot_service.start(interval_minutes=interval_minutes, dry_run=dry_run)
    return jsonify({"status": "started", "autopilot": status_payload})


@app.route("/api/arbitrage/autopilot/stop", methods=["POST"])
def autopilot_stop():
    status_payload = autopilot_service.stop()
    return jsonify({"status": "stopped", "autopilot": status_payload})


@app.route("/api/arbitrage/autopilot/runs", methods=["GET"])
def autopilot_runs():
    limit = int(request.args.get("limit", 20))
    runs = get_recent_autopilot_runs(limit=limit)
    return jsonify({"runs": runs, "count": len(runs)})


# ── Full pipeline ────────────────────────────────────────────────────────────

@app.route("/api/arbitrage/run-pipeline", methods=["POST"])
def run_pipeline():
    """Run Scout + Analyze batch in sequence. Non-blocking via thread."""
    def _pipeline():
        scout_result = run_scout()
        new_jobs = get_jobs(status="new", limit=20)
        for job in new_jobs:
            analysis = analyze_job(job)
            if filter_worthy(analysis):
                create_bid(job, analysis)

    thread = threading.Thread(target=_pipeline, daemon=True)
    thread.start()

    return jsonify({"status": "pipeline_started", "message": "Scout + Analyze running in background. Check /api/arbitrage/bids/pending for results."})


if __name__ == "__main__":
    init_db()
    print("=" * 60)
    print("ADRION 369 - Arbitrage Server")
    print(f"LLM Backend : {get_active_llm_backend()}")
    print(f"XRP Target  : {XRP_TARGET}")
    print(f"Database    : arbitrage.db")
    print("=" * 60)
    print("Endpoints:")
    print("  POST /api/arbitrage/scout")
    print("  GET  /api/arbitrage/jobs")
    print("  POST /api/arbitrage/analyze/<job_id>")
    print("  POST /api/arbitrage/analyze-batch")
    print("  GET  /api/arbitrage/bids/pending")
    print("  POST /api/arbitrage/bids/<id>/approve")
    print("  POST /api/arbitrage/execute/<job_id>")
    print("  GET  /api/arbitrage/kpis")
    print("  POST /api/arbitrage/run-pipeline")
    print("=" * 60)
    app.run(port=8001, debug=False)
