#!/usr/bin/env python3
"""
Unified Admin Panel (UAP) -- Master Orchestrator API
Port 8002, endpoints under /mapi/v1/

Slim app factory: registers 5 blueprints, shared middleware, health endpoints.
All route handlers live in uap/backend/blueprints/.
"""
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# PRIORITY: Setup Python path FIRST before any local imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

# Load .env variables
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

load_dotenv(Path(__file__).parent.parent.parent / ".env")

# ── Structured JSON logging for Loki/Grafana ────────────────────────────────
try:
    from pythonjsonlogger import jsonlogger
    _handler = logging.StreamHandler()
    _handler.setFormatter(jsonlogger.JsonFormatter(
        "%(asctime)s %(name)s %(levelname)s %(message)s",
        rename_fields={"asctime": "timestamp", "levelname": "level"},
    ))
    logging.root.handlers = [_handler]
    logging.root.setLevel(logging.INFO)
except ImportError:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )

logger = logging.getLogger("adrion.uap.api")

# Import database integration (SQLite fallback or PostgreSQL)
from db import DatabaseEngine  # noqa: E402

# ── LLM integration (optional -- used by health check) ────────────────────
try:
    from arbitrage.llm import chat as llm_chat  # noqa: F401
    LLM_AVAILABLE = True
except Exception:
    LLM_AVAILABLE = False

# ── Kubernetes integration (optional) ──────────────────────────────────────
try:
    from kubernetes_integration import KubernetesIntegration
    K8S_INTEGRATION = KubernetesIntegration()
    K8S_ENABLED = True
except Exception as e:
    logger.warning("Kubernetes integration not available: %s", e)
    K8S_INTEGRATION = None
    K8S_ENABLED = False

try:
    from k8s_websocket import get_k8s_watcher
    K8S_WATCHER = get_k8s_watcher()
    K8S_WATCHER_ENABLED = True
except Exception as e:
    logger.warning("Kubernetes WebSocket watcher not available: %s", e)
    K8S_WATCHER = None
    K8S_WATCHER_ENABLED = False

# ── Database ───────────────────────────────────────────────────────────────
try:
    db = DatabaseEngine
    logger.info("Database initialized successfully")
    USE_DATABASE = True
except Exception as e:
    logger.warning("Database connection failed: %s. Falling back to in-memory storage.", e)
    db = None
    USE_DATABASE = False

# ── Config ─────────────────────────────────────────────────────────────────
MAPI_HOST = os.getenv("MAPI_HOST", "localhost")
MAPI_PORT = int(os.getenv("MAPI_PORT", "8002"))
API_KEY = os.getenv("UAP_API_KEY", "")

if not API_KEY:
    if os.getenv("ENVIRONMENT") == "production":
        logger.critical(
            "[SECURITY] UAP_API_KEY is not set in PRODUCTION -- refusing to start."
        )
        sys.exit(1)
    else:
        logger.warning("[SECURITY] UAP_API_KEY is not set -- using empty key.")

# ── Flask App ──────────────────────────────────────────────────────────────
app = Flask(__name__)
_CORS_ORIGIN = os.getenv("CORS_ALLOWED_ORIGIN", "http://localhost:8003")
CORS(app, origins=[_CORS_ORIGIN])
_ALLOWED_ORIGINS = {_CORS_ORIGIN, "http://localhost:8003"}

_UAP_SERVER_START = time.time()


# ── Middleware ─────────────────────────────────────────────────────────────

@app.before_request
def _check_csrf():
    if request.method in ("POST", "PUT", "DELETE"):
        origin = request.headers.get("Origin")
        if origin and origin not in _ALLOWED_ORIGINS:
            return jsonify({"error": "Origin not allowed"}), 403


@app.before_request
def _start_request_timer():
    request.environ["uap.request_started_at"] = time.perf_counter()


@app.after_request
def _log_request(response):
    started_at = request.environ.get("uap.request_started_at")
    duration_ms = int((time.perf_counter() - started_at) * 1000) if started_at else -1
    log_method = (
        logger.error if response.status_code >= 500
        else logger.warning if response.status_code >= 400
        else logger.info
    )
    log_method(
        "event=request method=%s path=%s status=%s duration_ms=%s remote_addr=%s",
        request.method, request.path, response.status_code,
        duration_ms, request.remote_addr or "unknown",
    )
    return response


# ── Health & Status ────────────────────────────────────────────────────────

def _run_uap_health_checks() -> dict:
    """Run cascade health checks against downstream dependencies."""
    checks: dict = {"uptime": round(time.time() - _UAP_SERVER_START, 2)}
    overall = True

    if USE_DATABASE and db:
        try:
            db.query("SELECT 1", [])
            checks["db"] = "ok"
        except Exception as e:
            checks["db"] = f"error: {e}"
            overall = False
    else:
        checks["db"] = "in-memory-fallback"

    try:
        import requests as _req
        resp = _req.get("http://localhost:11434/api/tags", timeout=2)
        checks["ollama"] = "ok" if resp.status_code == 200 else "degraded"
    except Exception:
        checks["ollama"] = "unreachable"

    checks["llm_available"] = LLM_AVAILABLE
    checks["status"] = "healthy" if overall else "degraded"
    return checks


@app.route("/mapi/v1/health", methods=["GET"])
def health():
    """Deep health check endpoint with cascade dependency checks."""
    checks = _run_uap_health_checks()
    checks["version"] = "1.0.0"
    checks["timestamp"] = datetime.now().isoformat()
    status_code = 200 if checks["status"] == "healthy" else 503
    return jsonify(checks), status_code


@app.route("/mapi/v1/health/live", methods=["GET"])
def liveness():
    """Liveness probe -- returns 200 if the process is running."""
    return jsonify({"status": "alive"}), 200


@app.route("/mapi/v1/health/ready", methods=["GET"])
def readiness():
    """Readiness probe -- returns 503 if any critical dependency is down."""
    checks = _run_uap_health_checks()
    status_code = 200 if checks["status"] == "healthy" else 503
    return jsonify(checks), status_code


@app.route("/mapi/v1/status", methods=["GET"])
def status():
    """System status overview."""
    from uap.backend.blueprints import TASKS_STORE, GENESIS_LOGS, AGENT_TRUST_SCORES

    try:
        if USE_DATABASE and db:
            active_tasks = db.list_tasks(status="executing", limit=1000)
            active_count = len(active_tasks)
            all_logs = db.export_genesis_logs()
            logs_count = len(all_logs)
        else:
            active_count = len([t for t in TASKS_STORE.values() if t["status"] == "executing"])
            logs_count = len(GENESIS_LOGS)
    except Exception as e:
        logger.error("Error getting status from DB: %s", e)
        active_count = len([t for t in TASKS_STORE.values() if t["status"] == "executing"])
        logs_count = len(GENESIS_LOGS)

    return jsonify({
        "status": "online",
        "agents_online": len(AGENT_TRUST_SCORES),
        "tasks_active": active_count,
        "genesis_logs_total": logs_count,
        "database_backend": USE_DATABASE,
        "timestamp": datetime.now().isoformat(),
    })


# ── Error Handlers ─────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(e):
    logger.error("event=internal_error error=%s", str(e))
    return jsonify({"error": "Internal server error"}), 500


# ── Register Blueprints ───────────────────────────────────────────────────

def _register_blueprints():
    """Import and register all UAP blueprints, injecting shared dependencies."""
    import uap.backend.blueprints.tasks_bp as _tasks_mod
    import uap.backend.blueprints.agents_bp as _agents_mod
    import uap.backend.blueprints.genesis_bp as _genesis_mod
    import uap.backend.blueprints.ebdi_bp as _ebdi_mod
    import uap.backend.blueprints.admin_bp as _admin_mod

    # Inject shared dependencies into each blueprint module
    for mod in (_tasks_mod, _agents_mod, _genesis_mod, _ebdi_mod, _admin_mod):
        mod.USE_DATABASE = USE_DATABASE
        mod.db = db

    # Inject K8s dependencies into admin blueprint
    _admin_mod.K8S_INTEGRATION = K8S_INTEGRATION
    _admin_mod.K8S_ENABLED = K8S_ENABLED
    _admin_mod.K8S_WATCHER = K8S_WATCHER
    _admin_mod.K8S_WATCHER_ENABLED = K8S_WATCHER_ENABLED

    # Register all blueprints
    app.register_blueprint(_tasks_mod.tasks_bp)
    app.register_blueprint(_agents_mod.agents_bp)
    app.register_blueprint(_genesis_mod.genesis_bp)
    app.register_blueprint(_ebdi_mod.ebdi_bp)
    app.register_blueprint(_admin_mod.admin_bp)

    logger.info("All 5 UAP blueprints registered (tasks, agents, genesis, ebdi, admin)")


_register_blueprints()

# Register Phase 2 endpoints (PRIORITY 1-10)
try:
    from api_v2_extensions import register_phase2_endpoints
    register_phase2_endpoints(app)
    logger.info("Phase 2 endpoints registered (PRIORITY 1-10)")
except Exception as e:
    logger.warning("Phase 2 endpoints not registered: %s", e)

# Register Phase 3 auth endpoints (JWT + RBAC)
try:
    from auth_endpoints import register_auth_endpoints
    register_auth_endpoints(app)
    logger.info("Phase 3 auth endpoints registered (JWT + RBAC)")
except Exception as e:
    logger.warning("Phase 3 auth endpoints not registered: %s", e)


# ── U6: Background Services Startup ──────────────────────────────────────

def _start_background_services():
    """Start optional background services: EBDI homeostasis + DB sync worker."""
    # U2/U8: EBDI Homeostatic Decay Service
    try:
        from uap.backend.ebdi_homeostasis import EBDIHomeostaticService
        from uap.backend.blueprints import EBDI_TELEMETRY
        _ebdi_svc = EBDIHomeostaticService(EBDI_TELEMETRY)

        # U8: Wire WebSocket broadcast callback
        try:
            from uap.backend.websocket_server import push_ebdi_event
            _ebdi_svc.on_event(push_ebdi_event)
            logger.info("EBDI events wired to WebSocket broadcast")
        except ImportError:
            logger.info("WebSocket server not available — EBDI events local only")

        _ebdi_svc.start()
        app.config["_ebdi_homeostasis"] = _ebdi_svc
        logger.info("EBDI homeostatic decay service started as background thread")
    except Exception as exc:
        logger.warning("EBDI homeostasis service not started: %s", exc)

    # U6: DB Sync Worker (requires DATABASE_URL env var for PostgreSQL)
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        try:
            import asyncio
            import threading
            from scripts.db.db_sync_worker import SyncWorker
            from uap.backend.blueprints import TASKS_STORE

            def _task_store_getter():
                return TASKS_STORE

            worker = SyncWorker(
                db_url=db_url,
                interval_seconds=int(os.getenv("SYNC_INTERVAL", "5")),
                batch_size=int(os.getenv("SYNC_BATCH_SIZE", "100")),
                task_store_getter=_task_store_getter,
            )

            def _run_sync_loop():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(worker.start())
                except Exception as e:
                    logger.error("DB Sync Worker stopped: %s", e)
                finally:
                    loop.close()

            sync_thread = threading.Thread(target=_run_sync_loop, daemon=True, name="db-sync-worker")
            sync_thread.start()
            app.config["_sync_worker"] = worker
            logger.info("DB Sync Worker started as background thread (interval=%ss)", os.getenv("SYNC_INTERVAL", "5"))
        except Exception as exc:
            logger.warning("DB Sync Worker not started: %s", exc)
    else:
        logger.info("DATABASE_URL not set — DB Sync Worker disabled")


_start_background_services()


# ── Startup ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 45)
    print("  Unified Admin Panel (UAP) API Server")
    print("  Master Orchestrator Integration")
    print("=" * 45 + "\n")

    logger.info(
        "event=uap_startup host=%s port=%s api_key=%s",
        MAPI_HOST, MAPI_PORT, "***" if API_KEY else "none",
    )

    app.run(
        host=MAPI_HOST,
        port=MAPI_PORT,
        debug=os.getenv("FLASK_ENV") == "development",
        use_reloader=False,
    )
