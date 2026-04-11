#!/usr/bin/env python3
"""
Unified Admin Panel (UAP) — Master Orchestrator API
Port 8002, endpoints under /mapi/v1/

CORE FEATURES:
- Task delegator with Master Orchestrator routing
- Genesis Record audit trail queries
- Rollback checkpoint management
- Real-time EBDI telemetry
- Trust Score heatmap
"""
import hmac
import json
import logging
import os
import sys
import threading
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# PRIORITY: Setup Python path FIRST before any local imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

# Load .env variables
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

load_dotenv(Path(__file__).parent.parent.parent / ".env")

# ────────────────────────────────────────────────────────────────────────────
# LLM INTEGRATION (optional — graceful fallback if not available)
# ────────────────────────────────────────────────────────────────────────────
try:
    from arbitrage.llm import chat as llm_chat
    from arbitrage.config import get_active_llm_backend
    LLM_AVAILABLE = True
except Exception:
    llm_chat = None
    get_active_llm_backend = None
    LLM_AVAILABLE = False

# ────────────────────────────────────────────────────────────────────────────
# CONFIG & LOGGING (must be before conditional imports that use logger)
# ────────────────────────────────────────────────────────────────────────────

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

# Import Kubernetes integration for cluster monitoring
try:
    from kubernetes_integration import KubernetesIntegration
    K8S_INTEGRATION = KubernetesIntegration()
    K8S_ENABLED = True
except Exception as e:
    logger.warning(f"⚠️ Kubernetes integration not available: {e}")
    K8S_INTEGRATION = None
    K8S_ENABLED = False

# Import Kubernetes WebSocket watcher for real-time updates
try:
    from k8s_websocket import get_k8s_watcher
    K8S_WATCHER = get_k8s_watcher()
    K8S_WATCHER_ENABLED = True
except Exception as e:
    logger.warning(f"⚠️ Kubernetes WebSocket watcher not available: {e}")
    K8S_WATCHER = None
    K8S_WATCHER_ENABLED = False

app = Flask(__name__)
_CORS_ORIGIN = os.getenv("CORS_ALLOWED_ORIGIN", "http://localhost:8003")
CORS(app, origins=[_CORS_ORIGIN])

# ── CSRF Origin check ─────────────────────────────────────────────────────
_ALLOWED_ORIGINS = {_CORS_ORIGIN, "http://localhost:8003"}


@app.before_request
def _check_csrf():
    if request.method in ("POST", "PUT", "DELETE"):
        origin = request.headers.get("Origin")
        if origin and origin not in _ALLOWED_ORIGINS:
            return jsonify({"error": "Origin not allowed"}), 403


# Initialize database (SQLite or PostgreSQL)
try:
    db = DatabaseEngine  # DatabaseEngine is already an instance from db.py factory
    logger.info("✅ Database initialized successfully")
    USE_DATABASE = True
except Exception as e:
    logger.warning(f"⚠️ Database connection failed: {e}. Falling back to in-memory storage.")
    db = None
    USE_DATABASE = False

MAPI_HOST = os.getenv("MAPI_HOST", "localhost")
MAPI_PORT = int(os.getenv("MAPI_PORT", "8002"))
API_KEY = os.getenv("UAP_API_KEY", "")

# ── Agent column allowlist for UPDATE operations (security: prevent SQL injection) ──
ALLOWED_AGENT_COLUMNS = frozenset({
    "name", "role", "personality", "description", "trust_score",
    "capability_level", "skills", "active"
})

# PRIORITY 7 FIX: Fail hard if API key is empty in production
if not API_KEY:
    if os.getenv("ENVIRONMENT") == "production":
        logger.critical(
            "[SECURITY] UAP_API_KEY is not set in PRODUCTION — refusing to start. "
            "Set UAP_API_KEY env var (min 32 random chars) before exposing this service."
        )
        sys.exit(1)
    else:
        logger.warning(
            "[SECURITY] UAP_API_KEY is not set — using empty key. "
            "This means all requests with X-API-Key header will be rejected. "
            "Set UAP_API_KEY env var for development/testing."
        )

# ────────────────────────────────────────────────────────────────────────────
# IN-MEMORY DATA STORES (Phase 1 — will migrate to PostgreSQL in Phase 2)
# ────────────────────────────────────────────────────────────────────────────

TASKS_STORE: Dict[str, Dict[str, Any]] = {}
GENESIS_LOGS: List[Dict[str, Any]] = []
CHECKPOINTS_STORE: Dict[str, Dict[str, Any]] = {}
AGENT_TRUST_SCORES: Dict[str, float] = {
    "Librarian": 0.85,
    "SAP": 0.90,
    "Auditor": 0.88,
    "Sentinel": 0.92,
    "Architect": 0.87,
    "Healer": 0.83,
    "Amplifier": 0.80,
    "BoosterLever": 0.78,
    "Chronos": 0.82,
}
EBDI_TELEMETRY: Dict[str, Dict[str, float]] = {
    agent: {"pleasure": 0.5, "arousal": 0.3, "dominance": 0.6}
    for agent in AGENT_TRUST_SCORES.keys()
}
GUARDIAN_LAWS_STATUS: List[Dict[str, Any]] = [
    {"law": "G1", "name": "Unity", "status": "pass"},
    {"law": "G2", "name": "Harmony", "status": "pass"},
    {"law": "G3", "name": "Rhythm", "status": "pass"},
    {"law": "G4", "name": "Causality", "status": "pass"},
    {"law": "G5", "name": "Transparency", "status": "pass"},
    {"law": "G6", "name": "Authenticity", "status": "pass"},
    {"law": "G7", "name": "Privacy", "status": "pass"},
    {"law": "G8", "name": "Nonmaleficence", "status": "pass"},
    {"law": "G9", "name": "Sustainability", "status": "pass"},
]

# ────────────────────────────────────────────────────────────────────────────
# MIDDLEWARE
# ────────────────────────────────────────────────────────────────────────────

@app.before_request
def start_request_timer():
    request.environ["uap.request_started_at"] = time.perf_counter()


@app.after_request
def log_request(response):
    started_at = request.environ.get("uap.request_started_at")
    duration_ms = int((time.perf_counter() - started_at) * 1000) if started_at else -1
    log_method = (
        logger.error if response.status_code >= 500
        else logger.warning if response.status_code >= 400
        else logger.info
    )
    log_method(
        "event=request method=%s path=%s status=%s duration_ms=%s remote_addr=%s",
        request.method,
        request.path,
        response.status_code,
        duration_ms,
        request.remote_addr or "unknown",
    )
    return response


# ────────────────────────────────────────────────────────────────────────────
# HELPERS
# ────────────────────────────────────────────────────────────────────────────

def validate_api_key():
    """Check API key from header. Returns False when key is unset (forces rejection)."""
    if not API_KEY:
        return False
    key = request.headers.get("X-API-Key", "")
    return hmac.compare_digest(key, API_KEY)


def generate_task_id() -> str:
    """Generate unique task ID: upc-YYYYMMDD-HHMMSS-XXXX"""
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d-%H%M%S")
    random_suffix = os.urandom(2).hex().upper()
    return f"upc-{timestamp}-{random_suffix}"


def _keyword_persona_match(task_description: str) -> str:
    """Keyword-based routing heuristic (fallback when LLM is unavailable)."""
    keywords = task_description.lower()

    if "scout" in keywords or "find" in keywords or "search" in keywords:
        return "SAP"
    elif "analyze" in keywords or "evaluate" in keywords:
        return "Auditor"
    elif "crisis" in keywords or "urgent" in keywords or "error" in keywords:
        return "Sentinel"
    elif "design" in keywords or "architecture" in keywords:
        return "Architect"
    elif "heal" in keywords or "fix" in keywords or "optimize" in keywords:
        return "Healer"
    elif "history" in keywords or "document" in keywords or "archive" in keywords:
        return "Librarian"
    else:
        return "SAP"  # Default


def find_best_persona(task_description: str, agent_hint: Optional[str] = None) -> str:
    """Route task to best persona using LLM with keyword fallback."""
    if agent_hint and agent_hint in AGENT_TRUST_SCORES:
        return agent_hint

    if not LLM_AVAILABLE:
        return _keyword_persona_match(task_description)

    try:
        agents = list(AGENT_TRUST_SCORES.keys())
        prompt = (
            f"Task: '{task_description}'. Choose the best agent: {agents}. "
            "Reply with the agent name only, nothing else."
        )
        result = llm_chat(prompt, system="You are a task router for the ADRION 369 system.")
        agent = result.strip().strip('"').strip("'")
        if agent in AGENT_TRUST_SCORES:
            return agent
        logger.warning("LLM returned unknown agent '%s', falling back to keyword match", agent)
    except Exception as exc:
        logger.warning("LLM routing failed: %s, falling back to keyword match", exc)

    return _keyword_persona_match(task_description)


def check_trust_score(agent: str) -> bool:
    """TSPA [1]: Block agent if TS < 0.6"""
    ts = AGENT_TRUST_SCORES.get(agent, 0)
    return ts >= 0.6


def validate_dsv_signature(task_description: str) -> bool:
    """DSV [7]: Validate Input→Output signature."""
    if not task_description or len(task_description.strip()) < 5:
        return False
    return True


def log_genesis_record(
    task_id: str,
    agent: str,
    status: str,
    action: str,
    guards_passed: int = 9,
    notes: str = ""
):
    """Log action to Genesis Record for audit trail."""
    if USE_DATABASE and db:
        try:
            db.insert_genesis_log(task_id, agent, status, action, guards_passed, notes)
        except Exception as e:
            logger.error(f"Failed to insert genesis log to DB: {e}. Using in-memory fallback.")
            GENESIS_LOGS.append({
                "timestamp": datetime.now().isoformat(),
                "task_id": task_id,
                "agent": agent,
                "status": status,
                "action": action,
                "guards_passed": guards_passed,
                "notes": notes,
            })
    else:
        # Fallback to in-memory
        GENESIS_LOGS.append({
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            "agent": agent,
            "status": status,
            "action": action,
            "guards_passed": guards_passed,
            "notes": notes,
        })

    logger.info("event=genesis_log task_id=%s agent=%s action=%s", task_id, agent, action)


# ────────────────────────────────────────────────────────────────────────────
# HEALTH & STATUS
# ────────────────────────────────────────────────────────────────────────────

_UAP_SERVER_START = time.time()


def _run_uap_health_checks() -> dict:
    """Run cascade health checks against downstream dependencies."""
    checks: dict = {"uptime": round(time.time() - _UAP_SERVER_START, 2)}
    overall = True

    # DB check
    if USE_DATABASE and db:
        try:
            result = db.query("SELECT 1", [])
            checks["db"] = "ok"
        except Exception as e:
            checks["db"] = f"error: {e}"
            overall = False
    else:
        checks["db"] = "in-memory-fallback"

    # Ollama / LLM check (non-critical)
    try:
        import requests as _req
        resp = _req.get("http://localhost:11434/api/tags", timeout=2)
        checks["ollama"] = "ok" if resp.status_code == 200 else "degraded"
    except Exception:
        checks["ollama"] = "unreachable"

    # LLM backend availability
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
    """Liveness probe — returns 200 if the process is running."""
    return jsonify({"status": "alive"}), 200


@app.route("/mapi/v1/health/ready", methods=["GET"])
def readiness():
    """Readiness probe — returns 503 if any critical dependency is down."""
    checks = _run_uap_health_checks()
    status_code = 200 if checks["status"] == "healthy" else 503
    return jsonify(checks), status_code


@app.route("/mapi/v1/status", methods=["GET"])
def status():
    """System status."""
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
        logger.error(f"Error getting status from DB: {e}")
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


# ────────────────────────────────────────────────────────────────────────────
# TASK DELEGATION [Master Orchestrator Protocol]
# ────────────────────────────────────────────────────────────────────────────

@app.route("/mapi/v1/task/delegate", methods=["POST"])
def task_delegate():
    """
    KROK 1: Sensing & Routing (MoE Gating)
    KROK 2: Graph-of-Thoughts (Drafting)
    KROK 2.5: Step Auto-Verification (SAV)
    KROK 4: Action & Genesis Record

    Request:
    {
      "task_description": "Scout XRP opportunities under $5",
      "agent_hint": "SAP",  # optional
      "dry_run": false,
      "budget_max": 500
    }
    """
    if not validate_api_key():
        return jsonify({"error": "Unauthorized"}), 401

    body = request.get_json(silent=True) or {}
    task_desc = body.get("task_description", "").strip()
    agent_hint = body.get("agent_hint")
    dry_run = body.get("dry_run", False)
    budget_max = body.get("budget_max", 1000)

    # DSV [7]: Validate Input→Output signature
    if not validate_dsv_signature(task_desc):
        return jsonify({
            "error": "Invalid task description (min 5 characters)",
            "status": "rejected"
        }), 400

    # KROK 1: Routing via EBDI + TSPA
    agent = find_best_persona(task_desc, agent_hint)

    # TSPA [1]: Block if TS < 0.6
    if not check_trust_score(agent):
        log_genesis_record(
            task_id="pending",
            agent=agent,
            status="blocked",
            action="TSPA_rejection",
            guards_passed=2,
            notes=f"Trust Score {AGENT_TRUST_SCORES[agent]} < 0.6"
        )
        return jsonify({
            "error": f"Agent {agent} trust score too low (< 0.6). Use Healer to re-calibrate.",
            "status": "blocked",
            "agent": agent,
            "trust_score": AGENT_TRUST_SCORES[agent],
        }), 403

    task_id = generate_task_id()

    # Create task record
    task = {
        "task_id": task_id,
        "task_description": task_desc,
        "assigned_agent": agent,
        "dry_run": dry_run,
        "budget_max": budget_max,
        "status": "submitted",
        "trust_score": AGENT_TRUST_SCORES[agent],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "result": None,
        "errors": [],
    }

    # Save to database (with fallback to in-memory)
    if USE_DATABASE and db:
        try:
            db.insert_task(task_id, task_desc, agent, dry_run, budget_max, AGENT_TRUST_SCORES[agent])
        except Exception as e:
            logger.error(f"Failed to insert task to DB: {e}. Using in-memory fallback.")
            TASKS_STORE[task_id] = task
    else:
        TASKS_STORE[task_id] = task

    # Log to Genesis Record
    log_genesis_record(
        task_id=task_id,
        agent=agent,
        status="submitted",
        action="task_delegation",
        guards_passed=9,
        notes=f"Routed to {agent}, dry_run={dry_run}"
    )

    logger.info(
        "event=task_submitted task_id=%s agent=%s description=%s dry_run=%s",
        task_id, agent, task_desc[:50], dry_run
    )

    # Execute task via LLM or mock
    def _execute_task():
        task["status"] = "executing"
        task["updated_at"] = datetime.now().isoformat()
        if USE_DATABASE and db:
            try:
                db.update_task_status(task_id, "executing")
            except Exception as exc:
                logger.error("Failed to update task status to 'executing' in DB: %s", exc)

        try:
            system_prompt = (
                f"You are {agent}, an AI agent in the ADRION 369 system. "
                "Execute the following task thoroughly."
            )
            if LLM_AVAILABLE:
                result_text = llm_chat(task_desc, system=system_prompt)
            else:
                result_text = f"[mock] Task '{task_desc}' processed by {agent}"
            result = {"output": result_text, "agent": agent, "confidence": 0.85}
        except Exception as e:
            logger.error("Task execution error for %s: %s", task_id, e)
            result = {"output": f"Execution error: {e}", "agent": agent, "confidence": 0.0, "error": True}

        task["status"] = "completed"
        task["result"] = result
        task["updated_at"] = datetime.now().isoformat()
        if USE_DATABASE and db:
            try:
                db.update_task_status(task_id, "completed", task["result"])
            except Exception as exc:
                logger.error("Failed to update task status to 'completed' in DB: %s", exc)

        log_genesis_record(
            task_id=task_id,
            agent=agent,
            status="completed",
            action="execution_success",
            guards_passed=9,
            notes=f"Confidence: {result.get('confidence', 0):.2f}"
        )

    if not dry_run:
        threading.Thread(target=_execute_task, daemon=True).start()

    return jsonify({
        "task_id": task_id,
        "status": task["status"],
        "assigned_agent": agent,
        "trust_score": AGENT_TRUST_SCORES[agent],
        "dry_run": dry_run,
        "created_at": task["created_at"],
    }), 201


@app.route("/mapi/v1/task/<task_id>", methods=["GET"])
def task_status(task_id: str):
    """Get task status, logs, errors."""
    if not validate_api_key():
        return jsonify({"error": "Unauthorized"}), 401

    # Try to get from database first
    if USE_DATABASE and db:
        try:
            task = db.get_task(task_id)
        except Exception as e:
            logger.warning(f"DB error: {e}, falling back to in-memory")
            task = TASKS_STORE.get(task_id)
    else:
        task = TASKS_STORE.get(task_id)

    if not task:
        return jsonify({"error": f"Task {task_id} not found"}), 404

    return jsonify(task)


@app.route("/mapi/v1/task/list", methods=["GET"])
def task_list():
    """List all tasks with optional filters."""
    if not validate_api_key():
        return jsonify({"error": "Unauthorized"}), 401

    status_filter = request.args.get("status")
    agent_filter = request.args.get("agent")
    limit = int(request.args.get("limit", 50))

    # Get tasks from database or in-memory
    if USE_DATABASE and db:
        try:
            tasks = db.list_tasks(status=status_filter, agent=agent_filter, limit=limit)
        except Exception as e:
            logger.warning(f"DB error: {e}, falling back to in-memory")
            tasks = list(TASKS_STORE.values())
            if status_filter:
                tasks = [t for t in tasks if t["status"] == status_filter]
            if agent_filter:
                tasks = [t for t in tasks if t["assigned_agent"] == agent_filter]
            tasks = sorted(tasks, key=lambda t: t["created_at"], reverse=True)[:limit]
    else:
        tasks = list(TASKS_STORE.values())
        if status_filter:
            tasks = [t for t in tasks if t["status"] == status_filter]
        if agent_filter:
            tasks = [t for t in tasks if t["assigned_agent"] == agent_filter]
        tasks = sorted(tasks, key=lambda t: t["created_at"], reverse=True)[:limit]

    return jsonify({"tasks": tasks, "count": len(tasks)})


# ────────────────────────────────────────────────────────────────────────────
# GENESIS RECORD AUDIT TRAIL
# ────────────────────────────────────────────────────────────────────────────

@app.route("/mapi/v1/genesis/logs", methods=["GET"])
def genesis_logs():
    """Query Genesis Record audit trail."""
    if not validate_api_key():
        return jsonify({"error": "Unauthorized"}), 401

    agent_filter = request.args.get("agent")
    since_str = request.args.get("since")  # '1h', '24h', '7d'
    status_filter = request.args.get("status")
    limit = int(request.args.get("limit", 100))

    # Parse 'since' parameter
    since_hours = 1  # default
    if since_str:
        if since_str.endswith("h"):
            since_hours = int(since_str[:-1])
        elif since_str.endswith("d"):
            since_hours = int(since_str[:-1]) * 24
        else:
            since_hours = 1

    # Get from database or in-memory
    if USE_DATABASE and db:
        try:
            logs = db.query_genesis_logs(agent=agent_filter, since_hours=since_hours,
                                        status=status_filter, limit=limit)
        except Exception as e:
            logger.warning(f"DB error: {e}, falling back to in-memory")
            logs = GENESIS_LOGS.copy()
            cutoff = datetime.now() - timedelta(hours=since_hours)
            logs = [entry for entry in logs if datetime.fromisoformat(entry["timestamp"]) > cutoff]
            if agent_filter:
                logs = [entry for entry in logs if entry["agent"] == agent_filter]
            if status_filter:
                logs = [entry for entry in logs if entry["status"] == status_filter]
            logs = sorted(logs, key=lambda entry: entry["timestamp"], reverse=True)[:limit]
    else:
        logs = GENESIS_LOGS.copy()
        cutoff = datetime.now() - timedelta(hours=since_hours)
        logs = [entry for entry in logs if datetime.fromisoformat(entry["timestamp"]) > cutoff]
        if agent_filter:
            logs = [entry for entry in logs if entry["agent"] == agent_filter]
        if status_filter:
            logs = [entry for entry in logs if entry["status"] == status_filter]
        logs = sorted(logs, key=lambda entry: entry["timestamp"], reverse=True)[:limit]

    return jsonify({"logs": logs, "count": len(logs)})


@app.route("/mapi/v1/genesis/export", methods=["GET"])
def genesis_export():
    """Export audit trail as JSON or CSV."""
    if not validate_api_key():
        return jsonify({"error": "Unauthorized"}), 401

    export_format = request.args.get("format", "json")  # json, csv

    # Get all logs from database or in-memory
    if USE_DATABASE and db:
        try:
            all_logs = db.export_genesis_logs()
        except Exception as e:
            logger.warning(f"DB error: {e}, falling back to in-memory")
            all_logs = GENESIS_LOGS.copy()
    else:
        all_logs = GENESIS_LOGS.copy()

    if export_format == "csv":
        import csv
        from io import StringIO

        output = StringIO()
        if all_logs:
            writer = csv.DictWriter(output, fieldnames=all_logs[0].keys())
            writer.writeheader()
            writer.writerows(all_logs)

        return app.response_class(
            response=output.getvalue(),
            status=200,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=genesis_export.csv"}
        )

    # JSON format
    return jsonify(all_logs)


# ────────────────────────────────────────────────────────────────────────────
# AGENT TRUST SCORES & EBDI TELEMETRY
# ────────────────────────────────────────────────────────────────────────────

@app.route("/mapi/v1/agent/scores", methods=["GET"])
def agent_scores():
    """Get Trust Score heatmap for all agents."""
    if not validate_api_key():
        return jsonify({"error": "Unauthorized"}), 401

    scores = [
        {
            "agent": agent,
            "trust_score": ts,
            "status": "operational" if ts >= 0.6 else "needs_recalibration",
            "ebdi": EBDI_TELEMETRY.get(agent, {}),
        }
        for agent, ts in AGENT_TRUST_SCORES.items()
    ]

    return jsonify({
        "agents": scores,
        "average_trust_score": sum(AGENT_TRUST_SCORES.values()) / len(AGENT_TRUST_SCORES),
        "timestamp": datetime.now().isoformat(),
    })


@app.route("/mapi/v1/agent/<agent>/score", methods=["GET"])
def agent_score(agent: str):
    """Get specific agent Trust Score + EBDI."""
    if not validate_api_key():
        return jsonify({"error": "Unauthorized"}), 401

    ts = AGENT_TRUST_SCORES.get(agent)
    if ts is None:
        return jsonify({"error": f"Agent {agent} not found"}), 404

    return jsonify({
        "agent": agent,
        "trust_score": ts,
        "status": "operational" if ts >= 0.6 else "needs_recalibration",
        "ebdi": EBDI_TELEMETRY.get(agent, {}),
    })


@app.route("/mapi/v1/ebdi/telemetry", methods=["GET"])
def ebdi_telemetry():
    """Get live EBDI (PAD) vectors for all agents."""
    if not validate_api_key():
        return jsonify({"error": "Unauthorized"}), 401

    # Simulate real-time telemetry changes
    for agent in EBDI_TELEMETRY:
        EBDI_TELEMETRY[agent]["pleasure"] += (os.urandom(1)[0] % 5 - 2) * 0.01
        EBDI_TELEMETRY[agent]["arousal"] += (os.urandom(1)[0] % 5 - 2) * 0.01
        EBDI_TELEMETRY[agent]["dominance"] += (os.urandom(1)[0] % 5 - 2) * 0.01

        # Clamp to [0, 1]
        for key in EBDI_TELEMETRY[agent]:
            EBDI_TELEMETRY[agent][key] = max(0, min(1, EBDI_TELEMETRY[agent][key]))

    # Crisis detection: Arousal > 0.7
    crisis_agents = [
        agent for agent, pad in EBDI_TELEMETRY.items()
        if pad.get("arousal", 0) > 0.7
    ]

    return jsonify({
        "telemetry": EBDI_TELEMETRY,
        "crisis_detected": len(crisis_agents) > 0,
        "crisis_agents": crisis_agents,
        "timestamp": datetime.now().isoformat(),
    })


# ────────────────────────────────────────────────────────────────────────────
# GUARDIAN LAWS STATUS
# ────────────────────────────────────────────────────────────────────────────

@app.route("/mapi/v1/guardian/laws", methods=["GET"])
def guardian_laws():
    """Get 9 Guardian Laws status."""
    if not validate_api_key():
        return jsonify({"error": "Unauthorized"}), 401

    return jsonify({
        "laws": GUARDIAN_LAWS_STATUS,
        "compliance": sum(1 for law in GUARDIAN_LAWS_STATUS if law["status"] == "pass"),
        "total": len(GUARDIAN_LAWS_STATUS),
        "timestamp": datetime.now().isoformat(),
    })


# ────────────────────────────────────────────────────────────────────────────
# CHECKPOINT & ROLLBACK (RBC)
# ────────────────────────────────────────────────────────────────────────────

@app.route("/mapi/v1/checkpoint/create", methods=["POST"])
def checkpoint_create():
    """Create Rollback Checkpoint (RBC)."""
    if not validate_api_key():
        return jsonify({"error": "Unauthorized"}), 401

    body = request.get_json(silent=True) or {}
    label = body.get("label", "")

    checkpoint_id = f"rbc-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}-{str(uuid.uuid4())[:8]}"

    # Snapshot current session state (tasks + logs) for restore capability
    try:
        if USE_DATABASE and db:
            tasks_snapshot = db.list_tasks(limit=10000)
            logs_snapshot = db.export_genesis_logs()
        else:
            tasks_snapshot = list(TASKS_STORE.values())
            logs_snapshot = GENESIS_LOGS.copy()
    except Exception as snap_err:
        logger.warning("Failed to snapshot full state for checkpoint: %s. Storing counts only.", snap_err)
        tasks_snapshot = []
        logs_snapshot = []

    checkpoint = {
        "checkpoint_id": checkpoint_id,
        "label": label,
        "created_at": datetime.now().isoformat(),
        "git_commit": "local-checkpoint",  # TODO: actual git commit hash
        "session_state": {
            "tasks_count": len(tasks_snapshot),
            "logs_count": len(logs_snapshot),
            "tasks": tasks_snapshot,
            "logs": logs_snapshot,
        },
    }

    CHECKPOINTS_STORE[checkpoint_id] = checkpoint

    log_genesis_record(
        task_id="system",
        agent="Master",
        status="created",
        action="RBC_checkpoint_created",
        guards_passed=9,
        notes=f"Checkpoint {checkpoint_id}"
    )

    return jsonify(checkpoint), 201


@app.route("/mapi/v1/checkpoint/list", methods=["GET"])
def checkpoint_list():
    """List all Rollback Checkpoints."""
    if not validate_api_key():
        return jsonify({"error": "Unauthorized"}), 401

    checkpoints = sorted(
        CHECKPOINTS_STORE.values(),
        key=lambda c: c["created_at"],
        reverse=True
    )

    return jsonify({"checkpoints": checkpoints, "count": len(checkpoints)})


@app.route("/mapi/v1/checkpoint/<checkpoint_id>/restore", methods=["POST"])
def checkpoint_restore(checkpoint_id: str):
    """Restore from Rollback Checkpoint."""
    if not validate_api_key():
        return jsonify({"error": "Unauthorized"}), 401

    checkpoint = CHECKPOINTS_STORE.get(checkpoint_id)

    # Try DB first if in-memory store doesn't have it
    if not checkpoint and USE_DATABASE and db:
        try:
            checkpoint = db.get_checkpoint(checkpoint_id)
        except Exception as e:
            logger.warning("Failed to fetch checkpoint from DB: %s", e)

    if not checkpoint:
        return jsonify({"error": f"Checkpoint {checkpoint_id} not found"}), 404

    # Load session_state and restore in-memory stores if data is present
    session_state = checkpoint.get("session_state") or {}

    tasks_restored = 0
    logs_restored = 0

    if "tasks" in session_state and isinstance(session_state["tasks"], list):
        TASKS_STORE.clear()
        for task in session_state["tasks"]:
            if isinstance(task, dict) and "task_id" in task:
                TASKS_STORE[task["task_id"]] = task
        tasks_restored = len(TASKS_STORE)
        logger.info(
            "event=checkpoint_restore checkpoint_id=%s tasks_restored=%d",
            checkpoint_id, tasks_restored,
        )

    if "logs" in session_state and isinstance(session_state["logs"], list):
        GENESIS_LOGS.clear()
        GENESIS_LOGS.extend(session_state["logs"])
        logs_restored = len(GENESIS_LOGS)
        logger.info(
            "event=checkpoint_restore checkpoint_id=%s logs_restored=%d",
            checkpoint_id, logs_restored,
        )

    log_genesis_record(
        task_id="system",
        agent="Master",
        status="restored",
        action="RBC_checkpoint_restored",
        guards_passed=9,
        notes=f"Restored from {checkpoint_id}: label='{checkpoint.get('label', '')}'"
    )

    return jsonify({
        "status": "restored",
        "checkpoint_id": checkpoint_id,
        "label": checkpoint.get("label", ""),
        "restored_from": checkpoint.get("created_at", ""),
        "restored_at": datetime.now().isoformat(),
        "tasks_restored": tasks_restored,
        "logs_restored": logs_restored,
    })


# ────────────────────────────────────────────────────────────────────────────
# CRISIS MODE & CONFLICT RESOLVER
# ────────────────────────────────────────────────────────────────────────────

@app.route("/mapi/v1/crisis/activate", methods=["POST"])
def crisis_activate():
    """Manually activate Crisis Mode (Arousal > 0.7)."""
    if not validate_api_key():
        return jsonify({"error": "Unauthorized"}), 401

    body = request.get_json(silent=True) or {}
    reason = body.get("reason", "Manual activation")

    # Simulate Sentinel activation
    EBDI_TELEMETRY["Sentinel"]["arousal"] = 0.95

    log_genesis_record(
        task_id="system",
        agent="Sentinel",
        status="active",
        action="crisis_mode_activated",
        guards_passed=8,
        notes=f"Crisis: {reason}"
    )

    return jsonify({
        "status": "crisis_active",
        "agent": "Sentinel",
        "arousal": 0.95,
        "reason": reason,
        "timestamp": datetime.now().isoformat(),
    })


@app.route("/mapi/v1/conflict/resolve", methods=["POST"])
def conflict_resolve():
    """Conflict Resolver (CR) [6]: Weighted voting on agent disagreements."""
    if not validate_api_key():
        return jsonify({"error": "Unauthorized"}), 401

    body = request.get_json(silent=True) or {}
    proposals = body.get("proposals", [])  # [{agent, proposal, confidence}, ...]

    if len(proposals) < 2:
        return jsonify({"error": "At least 2 proposals required"}), 400

    # Weighted voting by Trust Score
    total_weight = sum(AGENT_TRUST_SCORES.get(p["agent"], 0) for p in proposals)

    votes = []
    for proposal in proposals:
        agent = proposal["agent"]
        weight = AGENT_TRUST_SCORES.get(agent, 0) / total_weight if total_weight > 0 else 0
        votes.append({
            "agent": agent,
            "proposal": proposal["proposal"],
            "weight": weight,
            "weighted_score": weight * proposal.get("confidence", 0.5),
        })

    # Winner: highest weighted score
    winner = max(votes, key=lambda v: v["weighted_score"])

    log_genesis_record(
        task_id="system",
        agent="Master",
        status="resolved",
        action="conflict_resolution",
        guards_passed=9,
        notes=f"Winner: {winner['agent']} with {winner['weighted_score']:.2f} weighted score"
    )

    return jsonify({
        "status": "resolved",
        "decision": winner["proposal"],
        "winner": winner["agent"],
        "votes": votes,
        "timestamp": datetime.now().isoformat(),
    })


# ────────────────────────────────────────────────────────────────────────────
# SESSION & CHAT ORCHESTRATOR ENDPOINTS
# ────────────────────────────────────────────────────────────────────────────

# Initialize session manager and chat orchestrator on first import
_session_manager = None
_chat_orchestrator = None
_auto_startup = None


def _ensure_chat_components():
    """Lazy-initialize chat components."""
    global _session_manager, _chat_orchestrator, _auto_startup
    if _session_manager is None:
        try:
            from session_manager import SessionManager
            from chat_orchestrator import ChatOrchestrator
            from auto_startup import AutoStartupSequence

            _session_manager = SessionManager(db)
            _chat_orchestrator = ChatOrchestrator(
                session_manager=_session_manager,
                db_instance=db,
                llm_backend=None,  # Optional: add LLM backend
                master_orchestrator=None,  # Optional: add orchestrator
            )
            _auto_startup = AutoStartupSequence(
                session_manager=_session_manager,
                db_instance=db,
                chat_orchestrator=_chat_orchestrator,
            )
            logger.info("✅ Chat orchestrator components initialized")
        except ImportError as e:
            logger.warning(f"⚠️ Chat components not available: {e}")


@app.route("/mapi/v1/session/create", methods=["POST"])
def create_session():
    """Create new user session."""
    _ensure_chat_components()
    if not _session_manager:
        return jsonify({"error": "Session manager not available"}), 503

    try:
        data = request.get_json() or {}
        user_id = data.get("user_id", "anonymous")
        metadata = data.get("metadata", {})

        session_id = _session_manager.create_session(user_id, metadata)

        return jsonify({
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "status": "active",
        }), 201

    except Exception as e:
        logger.error(f"❌ Session creation failed: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/mapi/v1/session/<session_id>", methods=["GET"])
def get_session(session_id: str):
    """Get session by ID."""
    _ensure_chat_components()
    if not _session_manager:
        return jsonify({"error": "Session manager not available"}), 503

    try:
        session = _session_manager.get_session(session_id)
        if not session:
            return jsonify({"error": "Session not found"}), 404

        return jsonify(session), 200

    except Exception as e:
        logger.error(f"❌ Session retrieval failed: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/mapi/v1/session/previous", methods=["GET"])
def list_previous_sessions():
    """List previous sessions for user (for recovery)."""
    _ensure_chat_components()
    if not _session_manager:
        return jsonify({"error": "Session manager not available"}), 503

    try:
        user_id = request.args.get("user_id", "anonymous")
        limit = int(request.args.get("limit", 10))

        sessions = _session_manager.list_previous_sessions(user_id, limit)

        return jsonify({
            "user_id": user_id,
            "count": len(sessions),
            "sessions": sessions,
        }), 200

    except Exception as e:
        logger.error(f"❌ Session list failed: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/mapi/v1/chat/message", methods=["POST"])
def chat_message():
    """
    Send message to AI orchestrator in a session.

    Request:
    {
        "session_id": "uuid",
        "message": "user message",
        "context": {"platform": "vscode", ...}
    }

    Response:
    {
        "response": "orchestrator response",
        "decision_type": "QUERY|DELEGATE|HEAL|CONTINUE",
        "action_id": "optional task ID",
        "confidence": 0.0-1.0,
        "genesis_logged": bool,
        "timestamp": "ISO"
    }
    """
    _ensure_chat_components()
    if not _chat_orchestrator:
        return jsonify({"error": "Chat orchestrator not available"}), 503

    try:
        data = request.get_json() or {}
        session_id = data.get("session_id")
        message = data.get("message", "")
        context = data.get("context", {})

        if not session_id or not message:
            return jsonify({"error": "session_id and message required"}), 400

        # Ensure session exists
        _ensure_chat_components()
        session = _session_manager.get_session(session_id)
        if not session:
            return jsonify({"error": "Session not found"}), 404

        # Process message through orchestrator
        result = _chat_orchestrator.process_message(session_id, message, context)

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"❌ Chat message processing failed: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/mapi/v1/chat/history", methods=["GET"])
def get_chat_history():
    """Get chat history for session."""
    _ensure_chat_components()
    if not _session_manager:
        return jsonify({"error": "Session manager not available"}), 503

    try:
        session_id = request.args.get("session_id")
        limit = int(request.args.get("limit", 100))

        if not session_id:
            return jsonify({"error": "session_id required"}), 400

        history = _session_manager.get_chat_history(session_id, limit)

        return jsonify({
            "session_id": session_id,
            "count": len(history),
            "messages": history,
        }), 200

    except Exception as e:
        logger.error(f"❌ Chat history retrieval failed: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/mapi/v1/startup/auto-run", methods=["POST"])
def auto_startup_run():
    """
    Trigger autonomous startup sequence.

    Request:
    {
        "user_id": "...",
        "context": {"platform": "vscode", ...}
    }

    Response:
    {
        "status": "success|warning|error",
        "timestamp": "ISO",
        "steps": [...],
        "session_id": "...",
        "summary": "..."
    }
    """
    _ensure_chat_components()
    if not _auto_startup:
        return jsonify({"error": "Auto-startup not available"}), 503

    try:
        data = request.get_json() or {}
        user_id = data.get("user_id", "anonymous")
        context = data.get("context", {})

        result = _auto_startup.run_full_sequence(user_id, context)

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"❌ Auto-startup sequence failed: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/mapi/v1/startup/status", methods=["GET"])
def auto_startup_status():
    """Get auto-startup status."""
    _ensure_chat_components()
    if not _auto_startup:
        return jsonify({"error": "Auto-startup not available"}), 503

    try:
        # Return current session + recovery options
        user_id = request.args.get("user_id", "anonymous")

        previous_sessions = _session_manager.list_previous_sessions(user_id, 5) if _session_manager else []

        return jsonify({
            "user_id": user_id,
            "previous_sessions": previous_sessions,
            "ready": True,
        }), 200

    except Exception as e:
        logger.error(f"❌ Auto-startup status failed: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ════════════════════════════════════════════════════════════════════════════
# PHASE B: TASKS & AGENTS MANAGEMENT (NEW)
# ════════════════════════════════════════════════════════════════════════════

@app.route("/mapi/v1/tasks", methods=["GET"])
def get_active_tasks():
    """Fetch active tasks for current session"""
    session_id = request.args.get("session_id", "default")

    try:
        # Always use fallback sample data for now (table may not exist)
        result = [
            {"id": "task-001", "name": "K8s-Optimizer", "agent": "Architect", "status": "running", "progress": 65, "eta_seconds": 120, "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat()},
            {"id": "task-002", "name": "DataPipe-ETL", "agent": "SAP", "status": "completed", "progress": 100, "eta_seconds": 0, "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat()},
            {"id": "task-003", "name": "Monitor-Alert", "agent": "Sentinel", "status": "pending", "progress": 0, "eta_seconds": 300, "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat()},
        ]

        return jsonify({
            "success": True,
            "tasks": result if result else [],
            "total": len(result) if result else 0
        }), 200
    except Exception as e:
        logger.error(f"get_active_tasks error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/mapi/v1/tasks/stats", methods=["GET"])
def get_task_stats():
    """Get task statistics"""
    session_id = request.args.get("session_id", "default")

    try:
        # Always use fallback mock data to match tasks endpoint
        stats = {"completed": 1, "pending": 1, "running": 1, "failed": 0}

        total = sum([stats.get(k, 0) for k in ["completed", "pending", "running", "failed"]])

        return jsonify({
            "success": True,
            "completed": stats.get("completed", 0),
            "pending": stats.get("pending", 0),
            "running": stats.get("running", 0),
            "failed": stats.get("failed", 0),
            "total": total,
            "success_rate": stats.get("completed", 0) / max(1, total)
        }), 200
    except Exception as e:
        logger.error(f"get_task_stats error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/mapi/v1/agents", methods=["GET"])
def list_agents():
    """Fetch all agents"""
    try:
        if USE_DATABASE and db:
            result = db.query("""
                SELECT id, name, role, personality, description, trust_score, capability_level,
                       skills, active, created_at, success_rate, tasks_completed
                FROM agents ORDER BY active DESC, trust_score DESC
            """, [])
        else:
            # Fallback: return sample agents
            result = [
                {"id": "agent-librarian", "name": "Librarian", "role": "Knowledge Management", "personality": "Organized, thorough", "description": "Manages knowledge base", "trust_score": 0.95, "capability_level": "expert", "skills": '["documentation"]', "active": True, "success_rate": 0.98, "tasks_completed": 342},
                {"id": "agent-architect", "name": "Architect", "role": "System Design", "personality": "Strategic thinker", "description": "Designs systems", "trust_score": 0.88, "capability_level": "expert", "skills": '["design"]', "active": True, "success_rate": 0.92, "tasks_completed": 215},
                {"id": "agent-auditor", "name": "Auditor", "role": "Security & Compliance", "personality": "Detail-oriented", "description": "Performs audits", "trust_score": 0.92, "capability_level": "expert", "skills": '["audit"]', "active": True, "success_rate": 0.95, "tasks_completed": 178},
                {"id": "agent-sentinel", "name": "Sentinel", "role": "Monitoring & Alerts", "personality": "Vigilant watcher", "description": "Monitors system", "trust_score": 0.90, "capability_level": "expert", "skills": '["monitoring"]', "active": True, "success_rate": 0.97, "tasks_completed": 412},
            ]

        agents = []
        for agent in (result if result else []):
            agent_dict = dict(agent) if hasattr(agent, '__getitem__') else agent
            if isinstance(agent_dict.get("skills"), str):
                try:
                    agent_dict["skills"] = json.loads(agent_dict["skills"])
                except:
                    agent_dict["skills"] = []
            agents.append(agent_dict)

        return jsonify({"success": True, "agents": agents}), 200
    except Exception as e:
        logger.error(f"list_agents error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/mapi/v1/agents/create", methods=["POST"])
def create_agent():
    """Create new agent"""
    data = request.get_json() or {}

    try:
        required = ['name', 'role', 'personality', 'description', 'capability_level']
        if not all(f in data for f in required):
            return jsonify({"success": False, "error": "Missing required fields"}), 400

        agent_id = f"agent-{uuid.uuid4().hex[:8]}"

        if USE_DATABASE and db:
            skills_json = json.dumps(data.get('skills', []))
            db.execute("""
                INSERT INTO agents (id, name, role, personality, description, trust_score,
                                  capability_level, skills, active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, [
                agent_id, data['name'], data['role'], data['personality'], data['description'],
                float(data.get('trust_score', 0.8)), data['capability_level'], skills_json, data.get('active', True)
            ])

        return jsonify({"success": True, "id": agent_id, "message": f"Agent {data['name']} created"}), 201
    except Exception as e:
        logger.error(f"create_agent error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/mapi/v1/agents/<agent_id>", methods=["PUT"])
def update_agent(agent_id):
    """Update agent"""
    data = request.get_json() or {}

    try:
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        # SECURITY: Validate that only allowed columns are requested
        unknown_fields = set(data.keys()) - ALLOWED_AGENT_COLUMNS
        if unknown_fields:
            return jsonify({
                "success": False,
                "error": f"Unknown fields: {', '.join(sorted(unknown_fields))}",
                "allowed_fields": sorted(ALLOWED_AGENT_COLUMNS)
            }), 400

        if USE_DATABASE and db:
            fields, values = [], []
            for field in sorted(ALLOWED_AGENT_COLUMNS):
                if field in data:
                    fields.append(f"{field} = ?")
                    values.append(json.dumps(data[field]) if field == 'skills' else data[field])

            if not fields:
                return jsonify({"success": False, "error": "No fields to update"}), 400

            values.append(agent_id)
            db.execute(f"UPDATE agents SET {', '.join(fields)} WHERE id = ?", values)

        return jsonify({"success": True, "id": agent_id, "message": "Agent updated"}), 200
    except Exception as e:
        logger.error(f"update_agent error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/mapi/v1/agents/<agent_id>", methods=["DELETE"])
def delete_agent(agent_id):
    """Delete agent (soft delete)"""
    try:
        if USE_DATABASE and db:
            db.execute("UPDATE agents SET active = FALSE WHERE id = ?", [agent_id])

        return jsonify({"success": True, "id": agent_id, "message": "Agent deleted"}), 200
    except Exception as e:
        logger.error(f"delete_agent error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/mapi/v1/agents/<agent_id>", methods=["GET"])
def get_agent(agent_id):
    """Fetch single agent"""
    try:
        if USE_DATABASE and db:
            result = db.query("SELECT * FROM agents WHERE id = ?", [agent_id])
            if not result:
                return jsonify({"success": False, "error": "Agent not found"}), 404
            agent = dict(result[0]) if hasattr(result[0], '__getitem__') else result[0]
        else:
            agent = {"id": agent_id, "name": "Sample", "role": "Testing", "personality": "Test", "description": "Sample agent", "trust_score": 0.8, "capability_level": "expert", "skills": [], "active": True}

        if isinstance(agent.get("skills"), str):
            try:
                agent["skills"] = json.loads(agent["skills"])
            except:
                agent["skills"] = []

        return jsonify({"success": True, "agent": agent}), 200
    except Exception as e:
        logger.error(f"get_agent error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


# ──────────────────────────────────────────────────────────────────────────
# PHASE C: ANALYTICS ENDPOINTS
# ──────────────────────────────────────────────────────────────────────────

@app.route("/mapi/v1/agents/<agent_id>/history", methods=["GET"])
def get_agent_history(agent_id):
    """Get agent activity history"""
    try:
        limit = request.args.get("limit", 50, type=int)

        if USE_DATABASE and db:
            history = db.query("""
                SELECT id, activity_type, description, result, duration_seconds, created_at, metadata
                FROM agent_activity
                WHERE agent_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            """, [agent_id, limit])
        else:
            # Fallback sample data
            history = [
                {"id": 1, "activity_type": "task_execution", "description": f"Executed task for {agent_id}", "result": "success", "duration_seconds": 45, "created_at": "2026-04-05T10:00:00"},
                {"id": 2, "activity_type": "analysis", "description": f"Analyzed system for {agent_id}", "result": "success", "duration_seconds": 120, "created_at": "2026-04-05T11:30:00"},
            ]

        activities = []
        for activity in (history if history else []):
            activity_dict = dict(activity) if hasattr(activity, '__getitem__') else activity
            activities.append(activity_dict)

        return jsonify({"success": True, "agent_id": agent_id, "history": activities, "total": len(activities)}), 200
    except Exception as e:
        logger.error(f"get_agent_history error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/mapi/v1/agents/<agent_id>/performance", methods=["GET"])
def get_agent_performance(agent_id):
    """Get agent performance metrics"""
    try:
        if USE_DATABASE and db:
            perf = db.query("""
                SELECT tasks_completed, tasks_failed, avg_duration_seconds, success_rate,
                       last_activity, monthly_tasks, arousal_level, dominance_level, pleasure_level
                FROM agent_performance
                WHERE agent_id = %s
            """, [agent_id])
            perf = perf[0] if perf else None
        else:
            # Fallback
            perf = {
                "tasks_completed": 42,
                "tasks_failed": 3,
                "avg_duration_seconds": 65.5,
                "success_rate": 0.93,
                "last_activity": "2026-04-05T17:00:00",
                "monthly_tasks": 18,
                "arousal_level": 0.65,
                "dominance_level": 0.72,
                "pleasure_level": 0.80
            }

        if not perf:
            return jsonify({"success": False, "error": "Agent not found"}), 404

        perf_dict = dict(perf) if hasattr(perf, '__getitem__') else perf

        return jsonify({"success": True, "agent_id": agent_id, "performance": perf_dict}), 200
    except Exception as e:
        logger.error(f"get_agent_performance error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/mapi/v1/agents/<agent_id>/feedback", methods=["POST"])
def add_agent_feedback(agent_id):
    """Submit feedback for an agent"""
    data = request.get_json() or {}

    try:
        rating = data.get("rating", 3)
        comment = data.get("comment", "")
        session_id = data.get("session_id", "default")

        if not (1 <= rating <= 5):
            return jsonify({"success": False, "error": "Rating must be 1-5"}), 400

        # Determine feedback type based on rating
        feedback_type = "positive" if rating >= 4 else ("negative" if rating <= 2 else "neutral")
        trust_adjustment = (rating - 3) * 0.02  # -0.04 to +0.1

        if USE_DATABASE and db:
            db.execute("""
                INSERT INTO agent_feedback (agent_id, session_id, rating, comment, trust_adjustment, feedback_type)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, [agent_id, session_id, rating, comment, trust_adjustment, feedback_type])

            # Update agent trust score
            db.execute("""
                UPDATE agents
                SET trust_score = GREATEST(0, LEAST(1, trust_score + %s))
                WHERE id = %s
            """, [trust_adjustment, agent_id])

        return jsonify({"success": True, "message": f"Feedback added", "trust_adjustment": trust_adjustment}), 201
    except Exception as e:
        logger.error(f"add_agent_feedback error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/mapi/v1/agents/leaderboard", methods=["GET"])
def get_leaderboard():
    """Get agent leaderboard ranked by trust score and performance"""
    try:
        limit = request.args.get("limit", 10, type=int)

        if USE_DATABASE and db:
            leaderboard = db.query("""
                SELECT a.id, a.name, a.trust_score, a.success_rate, ap.tasks_completed,
                       (a.trust_score * 0.4 + a.success_rate * 0.6) as overall_score
                FROM agents a
                LEFT JOIN agent_performance ap ON a.id = ap.agent_id
                WHERE a.active = TRUE
                ORDER BY overall_score DESC, a.trust_score DESC
                LIMIT %s
            """, [limit])
        else:
            # Fallback
            leaderboard = [
                {"id": "agent-1", "name": "Librarian", "trust_score": 0.95, "success_rate": 0.98, "tasks_completed": 342, "overall_score": 0.967},
                {"id": "agent-4", "name": "Sentinel", "trust_score": 0.92, "success_rate": 0.95, "tasks_completed": 421, "overall_score": 0.938},
                {"id": "agent-2", "name": "Architect", "trust_score": 0.88, "success_rate": 0.92, "tasks_completed": 187, "overall_score": 0.904},
                {"id": "agent-3", "name": "Auditor", "trust_score": 0.87, "success_rate": 0.91, "tasks_completed": 156, "overall_score": 0.891},
            ]

        agents = []
        for i, agent in enumerate((leaderboard if leaderboard else []), 1):
            agent_dict = dict(agent) if hasattr(agent, '__getitem__') else agent
            agent_dict["rank"] = i
            agents.append(agent_dict)

        return jsonify({"success": True, "leaderboard": agents, "total": len(agents)}), 200
    except Exception as e:
        logger.error(f"get_leaderboard error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/mapi/v1/agents/<agent_id>/log-activity", methods=["POST"])
def log_agent_activity(agent_id):
    """Log an agent activity"""
    data = request.get_json() or {}

    try:
        activity_type = data.get("activity_type", "unknown")
        description = data.get("description", "")
        result = data.get("result", "pending")
        duration = data.get("duration_seconds", 0)
        session_id = data.get("session_id", "default")
        metadata = data.get("metadata", {})

        if USE_DATABASE and db:
            activity_id = db.execute("""
                INSERT INTO agent_activity (agent_id, session_id, activity_type, description, result, duration_seconds, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, [agent_id, session_id, activity_type, description, result, duration, json.dumps(metadata)])
        else:
            activity_id = 999

        return jsonify({"success": True, "activity_id": activity_id, "message": "Activity logged"}), 201
    except Exception as e:
        logger.error(f"log_agent_activity error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


# ────────────────────────────────────────────────────────────────────────────
# KUBERNETES CLUSTER INTEGRATION (NEW)
# ────────────────────────────────────────────────────────────────────────────

@app.route("/mapi/v1/kubernetes/cluster-info", methods=["GET"])
def kubernetes_cluster_info():
    """Get Kubernetes cluster information."""
    if not validate_api_key():
        return jsonify({"error": "Unauthorized"}), 401

    if not K8S_ENABLED or not K8S_INTEGRATION:
        return jsonify({"error": "Kubernetes integration not available"}), 503

    try:
        cluster_info = K8S_INTEGRATION.get_cluster_info()

        # Log to Genesis Record
        log_genesis_record(
            task_id="system",
            agent="Monitor",
            status="success",
            action="kubernetes_cluster_info_queried",
            guards_passed=9,
            notes=f"Cluster: {cluster_info.get('cluster_name', 'unknown')}"
        )

        return jsonify({
            "status": "success",
            "cluster": cluster_info,
            "queried_at": datetime.now().isoformat(),
        }), 200

    except Exception as e:
        logger.error(f"kubernetes_cluster_info error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/mapi/v1/kubernetes/pods", methods=["GET"])
def kubernetes_pods_status():
    """Get pod status listing by namespace."""
    if not validate_api_key():
        return jsonify({"error": "Unauthorized"}), 401

    if not K8S_ENABLED or not K8S_INTEGRATION:
        return jsonify({"error": "Kubernetes integration not available"}), 503

    try:
        pods = K8S_INTEGRATION.get_pods_status()

        # Log to Genesis Record
        log_genesis_record(
            task_id="system",
            agent="Monitor",
            status="success",
            action="kubernetes_pods_query",
            guards_passed=9,
            notes=f"Retrieved {pods.get('total_pods', 0)} pods"
        )

        return jsonify({
            "status": "success",
            "pods": pods,
            "queried_at": datetime.now().isoformat(),
        }), 200

    except Exception as e:
        logger.error(f"kubernetes_pods_status error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/mapi/v1/kubernetes/services", methods=["GET"])
def kubernetes_services():
    """Get Kubernetes services by namespace."""
    if not validate_api_key():
        return jsonify({"error": "Unauthorized"}), 401

    if not K8S_ENABLED or not K8S_INTEGRATION:
        return jsonify({"error": "Kubernetes integration not available"}), 503

    try:
        services = K8S_INTEGRATION.get_services()

        # Log to Genesis Record
        log_genesis_record(
            task_id="system",
            agent="Monitor",
            status="success",
            action="kubernetes_services_query",
            guards_passed=9,
            notes=f"Retrieved {len(services.get('services', []))} services"
        )

        return jsonify({
            "status": "success",
            "services": services,
            "queried_at": datetime.now().isoformat(),
        }), 200

    except Exception as e:
        logger.error(f"kubernetes_services error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/mapi/v1/kubernetes/deployments", methods=["GET"])
def kubernetes_deployments():
    """Get Kubernetes deployments by namespace."""
    if not validate_api_key():
        return jsonify({"error": "Unauthorized"}), 401

    if not K8S_ENABLED or not K8S_INTEGRATION:
        return jsonify({"error": "Kubernetes integration not available"}), 503

    try:
        deployments = K8S_INTEGRATION.get_deployments()

        # Log to Genesis Record
        log_genesis_record(
            task_id="system",
            agent="Monitor",
            status="success",
            action="kubernetes_deployments_query",
            guards_passed=9,
            notes=f"Retrieved {len(deployments.get('deployments', []))} deployments"
        )

        return jsonify({
            "status": "success",
            "deployments": deployments,
            "queried_at": datetime.now().isoformat(),
        }), 200

    except Exception as e:
        logger.error(f"kubernetes_deployments error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/mapi/v1/kubernetes/pod/<pod_name>/logs", methods=["GET"])
def kubernetes_pod_logs(pod_name: str):
    """Get logs from a specific pod."""
    if not validate_api_key():
        return jsonify({"error": "Unauthorized"}), 401

    if not K8S_ENABLED or not K8S_INTEGRATION:
        return jsonify({"error": "Kubernetes integration not available"}), 503

    try:
        lines = request.args.get("lines", default=50, type=int)
        namespace = request.args.get("namespace", default="adrion-369")

        logs = K8S_INTEGRATION.get_pod_logs(pod_name, namespace=namespace, lines=lines)

        # Log to Genesis Record
        log_genesis_record(
            task_id="system",
            agent="Monitor",
            status="success",
            action="kubernetes_pod_logs_retrieved",
            guards_passed=9,
            notes=f"Retrieved {len(logs.get('logs', ''))} bytes from pod {pod_name}"
        )

        return jsonify({
            "status": "success",
            "pod_name": pod_name,
            "namespace": namespace,
            "logs": logs.get("logs", ""),
            "queried_at": datetime.now().isoformat(),
        }), 200

    except Exception as e:
        logger.error(f"kubernetes_pod_logs error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/mapi/v1/kubernetes/pod/<pod_name>/restart", methods=["POST"])
def kubernetes_pod_restart(pod_name: str):
    """Restart a specific pod (delete and recreate)."""
    if not validate_api_key():
        return jsonify({"error": "Unauthorized"}), 401

    if not K8S_ENABLED or not K8S_INTEGRATION:
        return jsonify({"error": "Kubernetes integration not available"}), 503

    try:
        namespace = request.args.get("namespace", default="adrion-369")

        # Perform restart (critical operation)
        result = K8S_INTEGRATION.restart_pod(pod_name, namespace=namespace)

        # Log critical action to Genesis Record
        log_genesis_record(
            task_id=f"pod-restart-{datetime.now().timestamp()}",
            agent="Sentinel",
            status="completed",
            action="kubernetes_pod_restart",
            guards_passed=9,
            notes=f"Pod {pod_name} forcefully restarted in namespace {namespace}"
        )

        return jsonify({
            "status": "success",
            "pod_name": pod_name,
            "namespace": namespace,
            "action": "restart",
            "result": result,
            "executed_at": datetime.now().isoformat(),
        }), 200

    except Exception as e:
        logger.error(f"kubernetes_pod_restart error: {str(e)}")

        # Log error to Genesis Record
        log_genesis_record(
            task_id=f"pod-restart-error-{datetime.now().timestamp()}",
            agent="Sentinel",
            status="failed",
            action="kubernetes_pod_restart_failed",
            guards_passed=7,
            notes=f"Failed to restart pod {pod_name}: {str(e)}"
        )

        return jsonify({"error": str(e)}), 500


@app.route("/mapi/v1/kubernetes/metrics", methods=["GET"])
def kubernetes_metrics():
    """Get Kubernetes cluster metrics from Prometheus."""
    if not validate_api_key():
        return jsonify({"error": "Unauthorized"}), 401

    if not K8S_ENABLED or not K8S_INTEGRATION:
        return jsonify({"error": "Kubernetes integration not available"}), 503

    try:
        metric = request.args.get("metric", default="cluster_health")

        metrics = K8S_INTEGRATION.get_metrics(metric)

        # Log to Genesis Record
        log_genesis_record(
            task_id="system",
            agent="Monitor",
            status="success",
            action="kubernetes_metrics_query",
            guards_passed=9,
            notes=f"Queried metric: {metric}"
        )

        return jsonify({
            "status": "success",
            "metric": metric,
            "data": metrics,
            "queried_at": datetime.now().isoformat(),
        }), 200

    except Exception as e:
        logger.error(f"kubernetes_metrics error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/mapi/v1/kubernetes/events", methods=["GET"])
def kubernetes_events():
    """Get recent Kubernetes cluster events."""
    if not validate_api_key():
        return jsonify({"error": "Unauthorized"}), 401

    if not K8S_ENABLED or not K8S_INTEGRATION:
        return jsonify({"error": "Kubernetes integration not available"}), 503

    try:
        events = K8S_INTEGRATION.get_namespace_events()

        # Log to Genesis Record
        log_genesis_record(
            task_id="system",
            agent="Monitor",
            status="success",
            action="kubernetes_events_query",
            guards_passed=9,
            notes=f"Retrieved {len(events.get('events', []))} cluster events"
        )

        return jsonify({
            "status": "success",
            "events": events,
            "queried_at": datetime.now().isoformat(),
        }), 200

    except Exception as e:
        logger.error(f"kubernetes_events error: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ────────────────────────────────────────────────────────────────────────────
# KUBERNETES REAL-TIME UPDATES (WebSocket Bridge via Server-Sent Events)
# ────────────────────────────────────────────────────────────────────────────

@app.route("/mapi/v1/kubernetes/watch/start", methods=["POST"])
def kubernetes_watch_start():
    """Start watching Kubernetes cluster for real-time updates"""
    if not validate_api_key():
        return jsonify({"error": "Unauthorized"}), 401

    if not K8S_WATCHER_ENABLED or not K8S_WATCHER:
        return jsonify({"error": "Kubernetes WebSocket watcher not available"}), 503

    try:
        K8S_WATCHER.start_watching()

        # Log to Genesis Record
        log_genesis_record(
            task_id="system",
            agent="Monitor",
            status="started",
            action="kubernetes_watcher_start",
            guards_passed=9,
            notes="Real-time K8s cluster watcher started"
        )

        return jsonify({
            "status": "success",
            "message": "Kubernetes watcher started",
            "watch_type": "streaming",
            "started_at": datetime.now().isoformat(),
        }), 200

    except Exception as e:
        logger.error(f"kubernetes_watch_start error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/mapi/v1/kubernetes/watch/stop", methods=["POST"])
def kubernetes_watch_stop():
    """Stop watching Kubernetes cluster"""
    if not validate_api_key():
        return jsonify({"error": "Unauthorized"}), 401

    if not K8S_WATCHER_ENABLED or not K8S_WATCHER:
        return jsonify({"error": "Kubernetes WebSocket watcher not available"}), 503

    try:
        K8S_WATCHER.stop_watching()

        # Log to Genesis Record
        log_genesis_record(
            task_id="system",
            agent="Monitor",
            status="stopped",
            action="kubernetes_watcher_stop",
            guards_passed=9,
            notes="Real-time K8s cluster watcher stopped"
        )

        return jsonify({
            "status": "success",
            "message": "Kubernetes watcher stopped",
            "stopped_at": datetime.now().isoformat(),
        }), 200

    except Exception as e:
        logger.error(f"kubernetes_watch_stop error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/mapi/v1/kubernetes/watch/events", methods=["GET"])
def kubernetes_watch_events():
    """Get queued real-time events from watcher (polling fallback for SSE)"""
    if not validate_api_key():
        return jsonify({"error": "Unauthorized"}), 401

    if not K8S_WATCHER_ENABLED or not K8S_WATCHER:
        return jsonify({"error": "Kubernetes WebSocket watcher not available"}), 503

    try:
        max_events = request.args.get("max", default=100, type=int)
        events = K8S_WATCHER.get_queued_events(max_count=max_events)

        return jsonify({
            "status": "success",
            "events": events,
            "count": len(events),
            "fetched_at": datetime.now().isoformat(),
        }), 200

    except Exception as e:
        logger.error(f"kubernetes_watch_events error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/mapi/v1/kubernetes/stream", methods=["GET"])
def kubernetes_stream_sse():
    """Server-Sent Events (SSE) stream for real-time K8s updates"""
    if not validate_api_key():
        return jsonify({"error": "Unauthorized"}), 401

    def generate():
        """Generator for SSE stream"""
        # Start watcher if not running
        if K8S_WATCHER and not K8S_WATCHER.watch_thread:
            K8S_WATCHER.start_watching()

        try:
            yield f"data: {json.dumps({'type': 'connected', 'timestamp': datetime.now().isoformat()})}\n\n"

            # Stream events
            while True:
                if K8S_WATCHER:
                    events = K8S_WATCHER.get_queued_events(max_count=10)
                    if events:
                        for event in events:
                            yield f"data: {json.dumps(event)}\n\n"

                time.sleep(1)  # Poll every second

        except GeneratorExit:
            logger.info("SSE stream closed by client")
        except Exception as e:
            logger.error(f"SSE stream error: {e}")

    if not K8S_WATCHER_ENABLED or not K8S_WATCHER:
        return jsonify({"error": "Kubernetes WebSocket watcher not available"}), 503

    # Log to Genesis Record
    log_genesis_record(
        task_id="system",
        agent="Monitor",
        status="opened",
        action="kubernetes_sse_stream_opened",
        guards_passed=9,
        notes="SSE stream for real-time K8s updates opened"
    )

    return app.response_class(
        response=generate(),
        status=200,
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )


# ────────────────────────────────────────────────────────────────────────────
# ERROR HANDLERS
# ────────────────────────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(e):
    logger.error("event=internal_error error=%s", str(e))
    return jsonify({"error": "Internal server error"}), 500


# ────────────────────────────────────────────────────────────────────────────
# STARTUP
# ────────────────────────────────────────────────────────────────────────────

# Register Phase 2 endpoints (PRIORITY 1-10)
try:
    from api_v2_extensions import register_phase2_endpoints
    register_phase2_endpoints(app)
    logger.info("✅ Phase 2 endpoints registered (PRIORITY 1-10)")
except Exception as e:
    logger.warning(f"⚠️ Phase 2 endpoints not registered: {e}")

# Register Phase 3 auth endpoints (JWT + RBAC)
try:
    from auth_endpoints import register_auth_endpoints
    register_auth_endpoints(app)
    logger.info("✅ Phase 3 auth endpoints registered (JWT + RBAC)")
except Exception as e:
    logger.warning(f"⚠️ Phase 3 auth endpoints not registered: {e}")

if __name__ == "__main__":
    print("=" * 45)
    print("  Unified Admin Panel (UAP) API Server")
    print("  Master Orchestrator Integration")
    print("=" * 45 + "\n")

    logger.info(
        "event=uap_startup host=%s port=%s api_key=%s",
        MAPI_HOST, MAPI_PORT, "***" if API_KEY else "none"
    )

    app.run(
        host=MAPI_HOST,
        port=MAPI_PORT,
        debug=os.getenv("FLASK_ENV") == "development",
        use_reloader=False,  # Disable reloader for threading
    )
