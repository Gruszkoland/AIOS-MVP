"""
ADRION 369 — Handlers: Leads & Webhook
Endpointy: /webhook/harmonia-369, /api/leads, /api/stats, /api/leads/search
"""

import urllib.parse
from datetime import datetime

from leads_db import save_lead_db, update_lead_confirmed, get_leads, get_stats, search_leads

try:
    from pipeline import genesis_log
    HAS_PIPELINE = True
except ImportError:
    HAS_PIPELINE = False


def register(router):
    """Rejestruj trasy leads/webhook w routerze."""
    router.post("/webhook/harmonia-369", handle_webhook)
    router.get("/api/leads", handle_get_leads)
    router.get("/api/stats", handle_get_stats)
    router.get("/api/leads/search", handle_search_leads)


def handle_webhook(handler, data):
    ts = datetime.now().strftime("%H:%M:%S")
    event = data.get("event", "scan")

    if event == "lead_confirmed":
        update_lead_confirmed(data)
        print(f"[{ts}] CONFIRMED: {data.get('business_name')} ({data.get('email')})")
        if HAS_PIPELINE:
            genesis_log("WEBHOOK", "LEAD_CONFIRMED", f"{data.get('business_name')} ({data.get('email')})")
        handler._json_response(200, {"status": "confirmed"})
    else:
        save_lead_db(data)
        score = data.get("score_total", "?")
        print(f"[{ts}] NEW LEAD: {data.get('business_name')} | Score: {score} | {data.get('email')}")
        if HAS_PIPELINE:
            genesis_log("WEBHOOK", "NEW_LEAD", f"{data.get('business_name')} | Score: {score}")
        handler._json_response(200, {"status": "saved", "score": score})


def handle_get_leads(handler, data):
    leads = get_leads()
    handler._json_response(200, leads)


def handle_get_stats(handler, data):
    stats = get_stats()
    handler._json_response(200, stats)


def handle_search_leads(handler, data):
    parsed = urllib.parse.urlparse(handler.path)
    qs = urllib.parse.parse_qs(parsed.query)
    query = qs.get("q", [""])[0].strip()
    results = search_leads(query)
    handler._json_response(200, results)
