"""
ADRION 369 — Handlers: Pipeline, AI, Genesis, Swarm, Blacklist
Endpointy: /api/pipeline/*, /api/ai/*, /api/genesis, /api/swarm/*, /api/blacklist
"""

import threading

try:
    from pipeline import (
        run_pipeline_sync, get_pipeline_state, get_swarm_status,
        get_genesis_logs, genesis_log, generate_weekly_report,
        add_to_blacklist, load_blacklist,
    )
    HAS_PIPELINE = True
except ImportError:
    HAS_PIPELINE = False


def register(router):
    """Rejestruj trasy pipeline w routerze."""
    router.post("/api/pipeline/run", handle_pipeline_run)
    router.post("/api/ai/report", handle_ai_report)
    router.post("/api/blacklist", handle_blacklist_add)
    router.get("/api/genesis", handle_get_genesis)
    router.get("/api/swarm/status", handle_get_swarm)
    router.get("/api/pipeline/status", handle_get_pipeline_status)
    router.get("/api/blacklist", handle_get_blacklist)


def _require_pipeline(handler):
    if not HAS_PIPELINE:
        handler._json_response(503, {"error": "Pipeline module unavailable"})
        return False
    return True


def handle_pipeline_run(handler, data):
    if not _require_pipeline(handler):
        return
    niche = data.get("niche", "restauracje")
    city = data.get("city", "Kraków")
    radius = data.get("radius_km", 5)
    gen_mails = data.get("generate_mails", True)

    def _run():
        run_pipeline_sync(niche, city, radius, gen_mails)
    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    handler._json_response(200, {"status": "started", "niche": niche, "city": city})


def handle_ai_report(handler, data):
    if not _require_pipeline(handler):
        return
    client = data.get("client_name", "")
    period = data.get("period", "ostatni tydzień")
    context = data.get("context", "")
    if not client:
        handler._json_response(400, {"error": "client_name required"})
        return
    result = generate_weekly_report(client, period, context)
    handler._json_response(200, result)


def handle_blacklist_add(handler, data):
    if not _require_pipeline(handler):
        return
    email = data.get("email", "").strip()
    if not email:
        handler._json_response(400, {"error": "email required"})
        return
    add_to_blacklist(email)
    genesis_log("AUDYTOR", "BLACKLIST_ADD", f"Added: {email}")
    handler._json_response(200, {"status": "added", "email": email, "total": len(list(load_blacklist()))})


def handle_get_genesis(handler, data):
    if HAS_PIPELINE:
        logs = get_genesis_logs(200)
        handler._json_response(200, logs)
    else:
        handler._json_response(200, [])


def handle_get_swarm(handler, data):
    if HAS_PIPELINE:
        swarm = get_swarm_status()
        handler._json_response(200, swarm)
    else:
        handler._json_response(200, [])


def handle_get_pipeline_status(handler, data):
    if HAS_PIPELINE:
        state = get_pipeline_state()
        handler._json_response(200, state)
    else:
        handler._json_response(200, {"status": "unavailable"})


def handle_get_blacklist(handler, data):
    if HAS_PIPELINE:
        bl = sorted(load_blacklist())
        handler._json_response(200, {"blacklist": bl, "total": len(bl)})
    else:
        handler._json_response(200, {"blacklist": [], "total": 0})
