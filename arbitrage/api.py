"""
"""
ADRION 369 — Arbitrage HTTP API Server (port 8001)
Serves the dashboard arbitrage endpoints via stdlib only (no Flask/FastAPI).

Endpoints:
  GET  /api/arbitrage/status
  GET  /api/arbitrage/kpis
  GET  /api/arbitrage/stats          (XRP progress)
  GET  /api/arbitrage/jobs
  GET  /api/arbitrage/bids/pending
  POST /api/arbitrage/bids/<id>/approve
  POST /api/arbitrage/scout
  POST /api/arbitrage/analyze-batch
  POST /api/arbitrage/cycle          (scout + analyze in one call)
  POST /api/arbitrage/checkout       (Stripe Checkout Session)
  POST /api/arbitrage/webhook        (Stripe webhook)
  POST /api/arbitrage/quantum/decide (Kwantowy Moduł Decyzyjny)
  GET  /api/arbitrage/quantum/status (Autopojeza status)
  POST /api/arbitrage/oracle/predict  (Vortex Oracle prediction)
  POST /api/arbitrage/oracle/scan     (Oracle batch scan)
  POST /api/arbitrage/wholesale/scout (B2B Wholesale Scout)
  POST /api/arbitrage/wholesale/cycle (Singularity Run — full pipeline)
  GET  /api/arbitrage/wholesale/deals (Query deals)
  POST /api/arbitrage/mass-generate      (Mass Generator — bulk manifest)
  GET  /api/arbitrage/mass-generate/manifest (Get current manifest)
"""

import json
import logging
import re
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime

logger = logging.getLogger(__name__)
ARB_PORT = 8001


# ──────────────────────────────────────────────────────────────────────────────
# Lazy imports to avoid startup failures when optional deps are absent
# ──────────────────────────────────────────────────────────────────────────────

def _db():
    from arbitrage.database import get_jobs, get_pending_bids, approve_bid, get_totals, init_db
    return get_jobs, get_pending_bids, approve_bid, get_totals, init_db


def _xrp():
    from arbitrage.xrp import get_progress
    return get_progress


def _scout():
    from arbitrage.scout import run_scout
    return run_scout


def _analyzer():
    from arbitrage.analyzer import analyze_job, filter_worthy
    from arbitrage.bidder import create_bid
    return analyze_job, filter_worthy, create_bid


def _config():
    from arbitrage.config import DAILY_BID_LIMIT, MIN_ANALYZER_SCORE, get_active_llm_backend
    return DAILY_BID_LIMIT, MIN_ANALYZER_SCORE, get_active_llm_backend


def _payments():
    from arbitrage.payments import create_checkout_session, verify_webhook_signature, handle_webhook_event
    return create_checkout_session, verify_webhook_signature, handle_webhook_event


def _quantum():
    from arbitrage.quantum import quantum_decide, entangle_markets, get_autopojeza_status, run_quantum_scan
    return quantum_decide, entangle_markets, get_autopojeza_status, run_quantum_scan


def _oracle():
    from arbitrage.oracle import oracle_predict, oracle_scan_products
    return oracle_predict, oracle_scan_products


def _wholesale():
    from arbitrage.wholesale_scout import scout_wholesale
    from arbitrage.database import get_deals
    return scout_wholesale, get_deals


def _wholesale_cycle():
    from arbitrage.wholesale_orchestrator import run_wholesale_cycle
    return run_wholesale_cycle


def _mass_generator():
    from arbitrage.mass_generator import run_mass_generation, generate_manifest, MANIFEST_FILE
    return run_mass_generation, generate_manifest, MANIFEST_FILE


# ──────────────────────────────────────────────────────────────────────────────
# Request handler
# ──────────────────────────────────────────────────────────────────────────────

class ArbitrageHandler(BaseHTTPRequestHandler):

    def _send(self, data: dict, code: int = 200):
        body = json.dumps(data, default=str).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        try:
            path = self.path.split("?")[0]

            if path == "/api/arbitrage/status":
                return self._handle_status()
            elif path == "/api/arbitrage/kpis":
                return self._handle_kpis()
            elif path == "/api/arbitrage/stats":
                return self._handle_stats()
            elif path == "/api/arbitrage/jobs":
                return self._handle_jobs()
            elif path == "/api/arbitrage/bids/pending":
                return self._handle_bids_pending()
            elif path == "/api/arbitrage/quantum/status":
                return self._handle_quantum_status()
            elif path == "/api/arbitrage/wholesale/deals":
                return self._handle_wholesale_deals()
            elif path == "/api/arbitrage/mass-generate/manifest":
                return self._handle_get_manifest()
            else:
                self._send({"error": "Not found"}, 404)
        except Exception as exc:
            logger.exception("GET error: %s", exc)
            self._send({"error": str(exc)}, 500)

    def do_POST(self):
        try:
            path = self.path.split("?")[0]

            # Approve/Reject bid: POST /api/arbitrage/bids/<id>/approve
            m = re.match(r"^/api/arbitrage/bids/(\d+)/approve$", path)
            if m:
                return self._handle_bid_approve(int(m.group(1)))

            if path == "/api/arbitrage/scout":
                return self._handle_scout()
            elif path == "/api/arbitrage/analyze-batch":
                return self._handle_analyze_batch()
            elif path == "/api/arbitrage/cycle":
                return self._handle_cycle()
            elif path == "/api/arbitrage/checkout":
                return self._handle_checkout()
            elif path == "/api/arbitrage/webhook":
                return self._handle_webhook()
            elif path == "/api/arbitrage/quantum/decide":
                return self._handle_quantum_decide()
            elif path == "/api/arbitrage/quantum/scan":
                return self._handle_quantum_scan()
            elif path == "/api/arbitrage/oracle/predict":
                return self._handle_oracle_predict()
            elif path == "/api/arbitrage/oracle/scan":
                return self._handle_oracle_scan()
            elif path == "/api/arbitrage/wholesale/scout":
                return self._handle_wholesale_scout()
            elif path == "/api/arbitrage/wholesale/cycle":
                return self._handle_wholesale_cycle()
            elif path == "/api/arbitrage/mass-generate":
                return self._handle_mass_generate()
            else:
                self._send({"error": "Not found"}, 404)
        except Exception as exc:
            logger.exception("POST error: %s", exc)
            self._send({"error": str(exc)}, 500)

    # ── Handlers ──────────────────────────────────────────────────────────────

    def _handle_status(self):
        DAILY_BID_LIMIT, MIN_ANALYZER_SCORE, get_active_llm_backend = _config()
        get_jobs, get_pending_bids, _, get_totals, _ = _db()
        totals = get_totals()
        pending = get_pending_bids()
        self._send({
            "llm_backend":      get_active_llm_backend(),
            "total_jobs":       totals.get("total_jobs", 0),
            "bids_sent":        totals.get("bids_sent", 0),
            "pending_bids":     len(pending),
            "daily_bid_limit":  DAILY_BID_LIMIT,
            "timestamp":        datetime.now().isoformat(),
        })

    def _handle_kpis(self):
        _, _, _, get_totals, _ = _db()
        totals = get_totals()
        self._send({**totals, "timestamp": datetime.now().isoformat()})

    def _handle_stats(self):
        get_progress = _xrp()
        self._send(get_progress())

    def _handle_jobs(self):
        get_jobs, _, _, _, _ = _db()
        jobs = get_jobs(limit=20)
        self._send({"jobs": jobs, "count": len(jobs)})

    def _handle_bids_pending(self):
        _, get_pending_bids, _, _, _ = _db()
        bids = get_pending_bids()
        self._send({"bids": bids, "count": len(bids)})

    def _handle_bid_approve(self, bid_id: int):
        length = int(self.headers.get("Content-Length", 0))
        body   = json.loads(self.rfile.read(length) or b"{}") if length else {}
        approved = bool(body.get("approved", True))
        _, _, approve_bid, _, _ = _db()
        approve_bid(bid_id, approved)
        self._send({"ok": True, "bid_id": bid_id, "approved": approved})

    def _handle_scout(self):
        run_scout = _scout()
        result = run_scout()
        self._send(result)

    def _handle_analyze_batch(self):
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

        self._send({
            "analyzed":     analyzed,
            "bids_created": bids_created,
            "timestamp":    datetime.now().isoformat(),
        })

    def _handle_cycle(self):
        """Run scout + analyze in background, return immediately."""
        def _run():
            run_scout = _scout()
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
        self._send({"ok": True, "message": "Pipeline cycle started in background"})

    def _handle_checkout(self):
        """POST /api/arbitrage/checkout — Create Stripe Checkout Session."""
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}") if length else {}
        tier = body.get("tier", "pilot")
        success_url = body.get("success_url", "http://localhost:9000")
        cancel_url = body.get("cancel_url", "http://localhost:9000")
        create_checkout_session, _, _ = _payments()
        result = create_checkout_session(tier, success_url, cancel_url)
        code = 200 if "url" in result else 400
        self._send(result, code)

    def _handle_webhook(self):
        """POST /api/arbitrage/webhook — Stripe webhook receiver."""
        import os
        length = int(self.headers.get("Content-Length", 0))
        payload = self.rfile.read(length) if length else b""
        sig = self.headers.get("Stripe-Signature", "")
        secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")

        _, verify_webhook_signature, handle_webhook_event = _payments()
        if secret and not verify_webhook_signature(payload, sig, secret):
            self._send({"error": "Invalid signature"}, 401)
            return

        try:
            event_data = json.loads(payload)
        except json.JSONDecodeError:
            self._send({"error": "Invalid JSON"}, 400)
            return

        result = handle_webhook_event(event_data)
        self._send(result)

    def _handle_quantum_decide(self):
        """POST /api/arbitrage/quantum/decide — Kwantowy Moduł Decyzyjny."""
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}") if length else {}
        price_source = float(body.get("price_source", 0))
        price_target = float(body.get("price_target", 0))
        channel_id = body.get("channel_id", "AUDIO_PREMIUM")

        if price_source <= 0 or price_target <= 0:
            self._send({"error": "price_source and price_target must be > 0"}, 400)
            return

        quantum_decide, _, _, _ = _quantum()
        decision = quantum_decide(price_source, price_target, channel_id)
        self._send(decision.to_dict())

    def _handle_quantum_status(self):
        """GET /api/arbitrage/quantum/status — Autopojeza status."""
        _, _, get_autopojeza_status, _ = _quantum()
        self._send(get_autopojeza_status())

    def _handle_quantum_scan(self):
        """POST /api/arbitrage/quantum/scan — Skan wszystkich kanałów."""
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}") if length else {}
        all_deals = body.get("deals", {})
        _, _, _, run_quantum_scan = _quantum()
        result = run_quantum_scan(all_deals)
        self._send(result)

    def _handle_oracle_predict(self):
        """POST /api/arbitrage/oracle/predict — Vortex Oracle single prediction."""
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}") if length else {}
        wholesale_price = float(body.get("wholesale_price", 0))
        retail_price = float(body.get("retail_price", 0))
        price_history = body.get("price_history", [])
        channel_id = body.get("channel_id", "AUDIO_PREMIUM")
        oracle_predict, _ = _oracle()
        prediction = oracle_predict(wholesale_price, retail_price, price_history, channel_id)
        self._send(prediction.to_dict())

    def _handle_oracle_scan(self):
        """POST /api/arbitrage/oracle/scan — Oracle batch product scan."""
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}") if length else {}
        products = body.get("products", [])
        channel_id = body.get("channel_id", "AUDIO_PREMIUM")
        _, oracle_scan_products = _oracle()
        result = oracle_scan_products(products, channel_id)
        self._send(result)

    def _handle_wholesale_scout(self):
        """POST /api/arbitrage/wholesale/scout — B2B Wholesale Scout Bridge."""
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}") if length else {}
        feed_data = body.get("feed_data")
        feed_format = body.get("feed_format", "json")
        channel_filter = body.get("channel_filter")
        min_margin = float(body.get("min_margin", 0.15))
        min_stock = int(body.get("min_stock", 1))
        use_mock = body.get("use_mock", feed_data is None)
        scout_wholesale, _ = _wholesale()
        result = scout_wholesale(feed_data, feed_format, channel_filter,
                                 min_margin, min_stock, use_mock)
        self._send(result)

    def _handle_wholesale_cycle(self):
        """POST /api/arbitrage/wholesale/cycle — Full Singularity Run pipeline."""
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}") if length else {}
        channel_filter = body.get("channel_filter")
        min_margin = float(body.get("min_margin", 0.15))
        auto_execute = body.get("auto_execute", False)
        use_mock = body.get("use_mock", True)
        cycle_fn = _wholesale_cycle()
        result = cycle_fn(
            channel_filter=channel_filter,
            min_margin=min_margin,
            auto_execute=auto_execute,
            use_mock=use_mock,
        )
        self._send(result)

    def _handle_wholesale_deals(self):
        """GET /api/arbitrage/wholesale/deals — Query stored deals."""
        from urllib.parse import urlparse, parse_qs
        qs = parse_qs(urlparse(self.path).query)
        channel_id = qs.get("channel_id", [None])[0]
        status = qs.get("status", [None])[0]
        min_margin = float(qs["min_margin"][0]) if "min_margin" in qs else None
        limit = int(qs.get("limit", ["50"])[0])
        _, get_deals = _wholesale()
        deals = get_deals(channel_id, status, min_margin, limit)
        self._send({"deals": deals, "count": len(deals)})

    def _handle_mass_generate(self):
        """POST /api/arbitrage/mass-generate — Run Mass Generator pipeline."""
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}") if length else {}
        channel_filter = body.get("channel_filter")
        min_margin = float(body.get("min_margin", 0.15))
        min_stock = int(body.get("min_stock", 5))
        revalidate = body.get("revalidate", False)
        run_mass, _, _ = _mass_generator()
        result = run_mass(
            channel_filter=channel_filter,
            min_margin=min_margin,
            min_stock=min_stock,
            revalidate=revalidate,
        )
        self._send(result)

    def _handle_get_manifest(self):
        """GET /api/arbitrage/mass-generate/manifest — Return current product manifest."""
        _, _, manifest_file = _mass_generator()
        if manifest_file.exists():
            with open(manifest_file, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            self._send(manifest)
        else:
            self._send({"error": "No manifest generated yet. POST /api/arbitrage/mass-generate first."}, 404)

    def log_message(self, fmt, *args):
        logger.debug(fmt, *args)


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────

def run_api_server():
    """Initialise DB and start the arbitrage API server (blocking)."""
    from arbitrage.database import init_db
    init_db()
    server = HTTPServer(("0.0.0.0", ARB_PORT), ArbitrageHandler)
    print(f"✅ Arbitrage API running on http://localhost:{ARB_PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n✋ Arbitrage API stopped")
        server.shutdown()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    run_api_server()
