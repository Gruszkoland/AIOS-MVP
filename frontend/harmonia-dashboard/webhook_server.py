"""
Harmonia 369 — Webhook Backend Server v4 (Slim Bootstrapper)
ADRION 369 | Centrum Dowodzenia

Routing delegowany do router.py + handlers_*.py
Warstwa DB w leads_db.py

Port: 3691
"""
import json
import sys
import http.server
import socketserver

from router import Router
import handlers_leads
import handlers_feedback
import handlers_outreach
import handlers_pipeline

PORT = 3691

# ===== BUILD ROUTER =====
_router = Router()
handlers_leads.register(_router)
handlers_feedback.register(_router)
handlers_outreach.register(_router)
handlers_pipeline.register(_router)


# ===== HEALTH CHECK =====
def handle_health(handler, data):
    from handlers_feedback import HAS_FEEDBACK, HAS_RAG, HAS_EVENT_BUS
    from handlers_pipeline import HAS_PIPELINE
    from leads_db import HAS_PG
    handler._json_response(200, {
        "status": "ok",
        "system": "Harmonia 369 Webhook v4",
        "pipeline": HAS_PIPELINE,
        "postgres": HAS_PG,
        "feedback_engine": HAS_FEEDBACK,
        "rag_memory": HAS_RAG,
        "event_bus": HAS_EVENT_BUS,
    })

_router.get("/health", handle_health)


class WebhookHandler(http.server.BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json_response(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self._cors()
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str, ensure_ascii=False).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(content_length) if content_length > 0 else b"{}"
        try:
            data = json.loads(raw) if raw else {}
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._json_response(400, {"error": "Invalid JSON"})
            return

        handler_fn = _router.resolve("POST", self.path)
        if handler_fn:
            handler_fn(self, data)
        else:
            self._json_response(404, {"error": "Not found"})

    def do_GET(self):
        handler_fn = _router.resolve("GET", self.path)
        if handler_fn:
            handler_fn(self, {})
        else:
            self._json_response(404, {"error": "Not found"})

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
        daemon_threads = True

    with ThreadedHTTPServer(("", PORT), WebhookHandler) as httpd:
        print(f"[Harmonia 369] Webhook Backend v4 aktywny: http://localhost:{PORT}")
        print(f"[Harmonia 369] Registered routes:")
        for r in _router.list_routes():
            print(f"  {r['method']:6s} {r['pattern']}")
        print(f"[Harmonia 369] Listening...")
        httpd.serve_forever()
