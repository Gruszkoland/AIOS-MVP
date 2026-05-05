"""
ADRION 369 — Handlers: Feedback Engine (OODA + V.E.R.A.), Golden, Memory, Events
Endpointy: /api/feedback/*, /api/golden, /api/memory/*, /api/events/*
"""

try:
    from feedback_engine import get_feedback_loop
    HAS_FEEDBACK = True
except ImportError:
    HAS_FEEDBACK = False

try:
    from rag_memory import get_memory
    HAS_RAG = True
except ImportError:
    HAS_RAG = False

try:
    from memory_events import get_event_bus
    HAS_EVENT_BUS = True
except ImportError:
    HAS_EVENT_BUS = False


def register(router):
    """Rejestruj trasy feedback/memory w routerze."""
    router.post("/api/feedback/observe", handle_observe)
    router.post("/api/feedback/orient", handle_orient)
    router.post("/api/feedback/act", handle_act)
    router.post("/api/golden", handle_golden_add)
    router.get("/api/feedback/decide", handle_decide)
    router.get("/api/feedback/status", handle_status)
    router.get("/api/golden", handle_golden_list)
    router.get("/api/memory/stats", handle_memory_stats)
    router.get("/api/events/metrics", handle_events_metrics)


def _require_feedback(handler):
    if not HAS_FEEDBACK:
        handler._json_response(503, {"error": "Feedback engine unavailable"})
        return False
    return True


def handle_observe(handler, data):
    if not _require_feedback(handler):
        return
    prompt = data.get("prompt", "")
    response = data.get("response", "")
    if not prompt or not response:
        handler._json_response(400, {"error": "prompt and response required"})
        return
    loop = get_feedback_loop()
    result = loop.observe(
        prompt=prompt, response=response,
        model=data.get("model", ""),
        latency_ms=data.get("latency_ms", 0),
        category=data.get("category", "general"),
        rag_context_used=data.get("rag_context_used", False),
    )
    handler._json_response(200, result)


def handle_orient(handler, data):
    if not _require_feedback(handler):
        return
    iid = data.get("interaction_id", "")
    if not iid:
        handler._json_response(400, {"error": "interaction_id required"})
        return
    loop = get_feedback_loop()
    result = loop.orient(
        interaction_id=iid,
        accepted=data.get("accepted", False),
        correction=data.get("correction"),
        score=data.get("score", 0),
    )
    handler._json_response(200, result)


def handle_act(handler, data):
    if not _require_feedback(handler):
        return
    prompt = data.get("prompt", "")
    if not prompt:
        handler._json_response(400, {"error": "prompt required"})
        return
    loop = get_feedback_loop()
    result = loop.act(prompt)
    handler._json_response(200, result)


def handle_golden_add(handler, data):
    if not _require_feedback(handler):
        return
    prompt = data.get("prompt", "")
    golden_response = data.get("golden_response", "")
    if not prompt or not golden_response:
        handler._json_response(400, {"error": "prompt and golden_response required"})
        return
    loop = get_feedback_loop()
    gid = loop.golden.add(
        prompt=prompt, golden_response=golden_response,
        category=data.get("category", "general"),
        source=data.get("source", "user"),
    )
    if loop.memory and loop.memory.available:
        loop.memory.add_golden_answer(prompt, golden_response, data.get("category", "general"))
    handler._json_response(200, {"status": "added", "id": gid})


def handle_decide(handler, data):
    if not HAS_FEEDBACK:
        handler._json_response(200, {"error": "Feedback engine unavailable"})
        return
    loop = get_feedback_loop()
    result = loop.decide()
    handler._json_response(200, result)


def handle_status(handler, data):
    if not HAS_FEEDBACK:
        handler._json_response(200, {"available": False})
        return
    loop = get_feedback_loop()
    result = loop.get_full_status()
    handler._json_response(200, result)


def handle_golden_list(handler, data):
    if not HAS_FEEDBACK:
        handler._json_response(200, [])
        return
    loop = get_feedback_loop()
    handler._json_response(200, loop.golden.get_all())


def handle_memory_stats(handler, data):
    if HAS_RAG:
        mem = get_memory()
        handler._json_response(200, mem.get_stats())
    else:
        handler._json_response(200, {"available": False})


def handle_events_metrics(handler, data):
    if HAS_EVENT_BUS:
        bus = get_event_bus()
        handler._json_response(200, bus.get_metrics())
    else:
        handler._json_response(200, {"available": False})
