"""
Phase 2 API Extensions for UAP
New endpoints that use integrated modules
Add these to existing api.py

Routes added:
- POST /mapi/v1/task/delegate/v2 — Enhanced delegation with full master loop
- GET  /mapi/v1/task/<id>/plan — Get MCTS plan for task
- POST /mapi/v1/task/simulate — DRM preview without execution
- GET  /mapi/v1/status/v2 — Enhanced status with DB metrics
"""
import hmac
import os
import sys
from functools import wraps
from pathlib import Path

from flask import Flask, jsonify, request

sys.path.insert(0, str(Path(__file__).parent))

from integration import get_integration

from db import get_db

# PRIORITY 6 FIX: Use empty default — never ship a hardcoded key
API_KEY = os.getenv("UAP_API_KEY", "")

if not API_KEY:
    import logging as _logging
    _logging.getLogger("adrion.uap.api").warning(
        "[SECURITY] UAP_API_KEY is not set — all authenticated requests will be rejected. "
        "Set UAP_API_KEY env var before exposing this service on a network."
    )
    if os.getenv("ENVIRONMENT") == "production":
        import logging as _logging2
        _logging2.getLogger("adrion.uap.api").critical(
            "[SECURITY] UAP_API_KEY is empty in PRODUCTION — refusing to start."
        )
        sys.exit(1)

# Decorator for API key validation
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # PRIORITY 7 FIX: Reject requests if API key is empty
        if not API_KEY:
            if os.getenv("ENVIRONMENT") == "production":
                return jsonify({"error": "Server configuration error: API key not set"}), 500
            else:
                # In dev mode, warn but allow (will likely reject since no key matches empty)
                pass

        key = request.headers.get("X-API-Key") or ""
        if not API_KEY or not hmac.compare_digest(key, API_KEY):
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function


def register_phase2_endpoints(app: Flask):
    """Register Phase 2 API endpoints."""

    integration = get_integration()
    db = get_db()

    # ────────────────────────────────────────────────────────────────────
    # PUBLIC CONFIG (For development mode)
    # ────────────────────────────────────────────────────────────────────

    @app.route("/mapi/v1/config/dev", methods=["GET"])
    def config_dev():
        """
        PRIORITY 6 FIX: Public endpoint for development configuration.
        Returns API key only if NOT in production mode.
        """
        if os.getenv("ENVIRONMENT") == "production":
            return jsonify({"error": "Unauthorized"}), 403

        return jsonify({
            "api_key": API_KEY,
            "mode": "development",
            "note": "This endpoint is only available in development mode"
        }), 200

    # ────────────────────────────────────────────────────────────────────
    # ENHANCED TASK DELEGATION (Master Orchestrator Full Loop)
    # ────────────────────────────────────────────────────────────────────

    @app.route("/mapi/v1/task/delegate/v2", methods=["POST"])
    @require_api_key
    def task_delegate_v2():
        """
        Enhanced task delegation using full Master Orchestrator loop.

        KROK 1: Sensing & Routing (Ollama LLM)
        KROK 2: GoT planning (MCTS)
        KROK 2.5: Step Auto-Verification (DRM)
        KROK 3: Self-Correction (Trust Score)
        KROK 4: Action & Genesis logging
        """
        body = request.get_json(silent=True) or {}
        task_desc = body.get("task_description", "").strip()
        agent_hint = body.get("agent_hint")
        dry_run = body.get("dry_run", False)
        budget_max = body.get("budget_max", 1000)

        if not task_desc or len(task_desc) < 5:
            return jsonify({"error": "Invalid task description"}), 400

        # Execute full master loop
        result = integration.execute_master_loop(
            task_description=task_desc,
            agent_hint=agent_hint,
            dry_run=dry_run,
            budget_max=budget_max
        )

        return jsonify(result), 201

    # ────────────────────────────────────────────────────────────────────
    # MCTS PLAN VISUALIZATION
    # ────────────────────────────────────────────────────────────────────

    @app.route("/mapi/v1/task/<task_id>/plan", methods=["GET"])
    @require_api_key
    def get_task_plan(task_id: str):
        """Get MCTS plan for specific task."""
        task = db.get_task(task_id)
        if not task:
            return jsonify({"error": f"Task {task_id} not found"}), 404

        # Helper: extract plan from genesis logs
        logs = db.query_genesis_logs(limit=100)
        plan_steps = [
            log for log in logs
            if log.get("action") == "MCTS_plan_step" and log.get("task_id") == task_id
        ]

        return jsonify({
            "task_id": task_id,
            "status": task["status"],
            "plan_steps": plan_steps,
            "plan_complete": len(plan_steps) > 0,
        })

    # ────────────────────────────────────────────────────────────────────
    # DRY RUN MODE (Preview before execution)
    # ────────────────────────────────────────────────────────────────────

    @app.route("/mapi/v1/task/simulate", methods=["POST"])
    @require_api_key
    def task_simulate():
        """
        DRM: Simulate operation and show diff/impact without execution.

        Request:
        {
          "operation": "git_reset",  // or file_deletion, database_migration, deployment
          "params": { ... operation-specific params ... }
        }
        """
        body = request.get_json(silent=True) or {}
        operation = body.get("operation", "").strip()
        params = body.get("params", {})

        if not operation:
            return jsonify({"error": "Missing 'operation' parameter"}), 400

        from drm_executor import get_drm
        drm = get_drm()

        preview = drm.simulate_operation(operation, params)

        return jsonify({
            "operation": operation,
            "preview": preview,
            "dry_run_mode": True,
            "requires_approval": preview.get("requires_approval", True),
        })

    # ────────────────────────────────────────────────────────────────────
    # APPROVE OPERATION (Generate HMAC token)
    # ────────────────────────────────────────────────────────────────────

    @app.route("/mapi/v1/task/approve", methods=["POST"])
    @require_api_key
    def task_approve():
        """
        PRIORITY 4 FIX: Generate HMAC approval token for destructive operation.

        Request:
        {
          "task_id": "upc-...",
          "operation": "git_reset"
        }

        Response:
        {
          "approved": true,
          "approval_token": "sha256_hmac_signature",
          "note": "Use this token in execute_approved_operation() call"
        }
        """
        body = request.get_json(silent=True) or {}
        task_id = body.get("task_id", "")
        operation = body.get("operation", "")

        if not all([task_id, operation]):
            return jsonify({"error": "Missing task_id or operation"}), 400

        from drm_executor import get_drm
        drm = get_drm()

        approval_response = drm.approve_operation(task_id, operation)
        return jsonify(approval_response), 200

    # ────────────────────────────────────────────────────────────────────
    # EXECUTE AFTER APPROVAL (Validate HMAC token)
    # ────────────────────────────────────────────────────────────────────

    @app.route("/mapi/v1/task/execute/approved", methods=["POST"])
    @require_api_key
    def execute_approved():
        """
        Execute operation after HMAC token validation.
        PRIORITY 4 FIX: Token must be generated by /mapi/v1/task/approve endpoint.

        Request:
        {
          "task_id": "upc-...-...",
          "operation": "git_reset",
          "params": { ... },
          "approval_token": "sha256_hmac_from_approve_endpoint"
        }
        """
        body = request.get_json(silent=True) or {}
        task_id = body.get("task_id", "")
        operation = body.get("operation", "")
        params = body.get("params", {})
        approval_token = body.get("approval_token", "")

        if not all([task_id, operation, approval_token]):
            return jsonify({"error": "Missing task_id, operation, or approval_token"}), 400

        from drm_executor import get_drm
        drm = get_drm()

        # PRIORITY 4 FIX: execute_approved_operation validates token internally
        result = drm.execute_approved_operation(task_id, operation, params, approval_token)

        # Update task status
        if result.get("status") == "success":
            db.update_task_status(task_id, "completed", result)
            return jsonify(result), 200
        else:
            db.update_task_status(task_id, "failed", result)
            return jsonify(result), 400

    # ────────────────────────────────────────────────────────────────────
    # ENHANCED SYSTEM STATUS (PostgreSQL + Ollama + WebSocket)
    # ────────────────────────────────────────────────────────────────────

    @app.route("/mapi/v1/status/v2", methods=["GET"])
    @require_api_key
    def status_v2():
        """Enhanced system status with Phase 2 metrics."""
        return jsonify(integration.get_system_status())

    # ────────────────────────────────────────────────────────────────────
    # OLLAMA ROUTING EXPLANATION
    # ────────────────────────────────────────────────────────────────────

    @app.route("/mapi/v1/routing/explain", methods=["POST"])
    @require_api_key
    def explain_routing():
        """Get routing explanation from Ollama."""
        body = request.get_json(silent=True) or {}
        task_description = body.get("task_description", "")
        agent = body.get("agent", "")

        if not task_description or not agent:
            return jsonify({"error": "Missing task_description or agent"}), 400

        explanation = integration.router.explain_routing(task_description, agent)

        return jsonify({
            "task_description": task_description,
            "agent": agent,
            "explanation": explanation,
        })

    # ────────────────────────────────────────────────────────────────────
    # POSTGRESQL GENESIS RECORD QUERIES (Enhanced)
    # ────────────────────────────────────────────────────────────────────

    @app.route("/mapi/v1/genesis/v2/search", methods=["POST"])
    @require_api_key
    def genesis_search_v2():
        """Full-text search in Genesis Record."""
        body = request.get_json(silent=True) or {}
        query = body.get("query", "").strip()
        agent = body.get("agent")
        since_hours = body.get("since_hours", 24)
        status = body.get("status")

        if not query:
            return jsonify({"error": "Missing 'query' parameter"}), 400

        # Query Genesis from PostgreSQL
        logs = db.query_genesis_logs(
            agent=agent,
            since_hours=since_hours,
            status=status,
            limit=100
        )

        # Filter by query
        results = [
            log for log in logs
            if (query.lower() in log.get("action", "").lower() or
                query.lower() in log.get("notes", "").lower() or
                query.lower() in log.get("agent", "").lower())
        ]

        return jsonify({
            "query": query,
            "results": results,
            "count": len(results),
        })

    # ────────────────────────────────────────────────────────────────────
    # AGENT METRICS HISTORY
    # ────────────────────────────────────────────────────────────────────

    @app.route("/mapi/v1/agent/<agent>/metrics", methods=["GET"])
    @require_api_key
    def agent_metrics(agent: str):
        """Get latest metrics for specific agent."""
        metric = db.get_latest_metrics(agent)
        if not metric:
            return jsonify({"error": f"No metrics for agent {agent}"}), 404

        return jsonify(metric)

    # ────────────────────────────────────────────────────────────────────
    # CHECKPOINT PERSISTENCE (PostgreSQL)
    # ────────────────────────────────────────────────────────────────────

    @app.route("/mapi/v1/checkpoint/v2/list", methods=["GET"])
    @require_api_key
    def checkpoints_v2_list():
        """List checkpoints from PostgreSQL."""
        limit = int(request.args.get("limit", 50))
        checkpoints = db.list_checkpoints(limit=limit)
        return jsonify({
            "checkpoints": checkpoints,
            "count": len(checkpoints),
        })

    print("✅ Phase 2 API endpoints registered:")
    print("  GET  /mapi/v1/config/dev         — Dev config (API key, mode)")
    print("  POST /mapi/v1/task/delegate/v2  — Full master loop")
    print("  GET  /mapi/v1/task/<id>/plan    — MCTS plan")
    print("  POST /mapi/v1/task/simulate     — DRM preview")
    print("  POST /mapi/v1/task/approve      — Generate HMAC token (PRIORITY 4)")
    print("  POST /mapi/v1/task/execute/approved — Execute after token validation (PRIORITY 4)")
    print("  GET  /mapi/v1/status/v2        — Enhanced status")
    print("  POST /mapi/v1/routing/explain   — Ollama routing explanation")
    print("  POST /mapi/v1/genesis/v2/search — Full-text Genesis search")
    print("  GET  /mapi/v1/agent/<agent>/metrics — Agent EBDI history")
    print("  GET  /mapi/v1/checkpoint/v2/list — PostgreSQL checkpoints")
    print("\n🔐 Security settings:")
    print(f"  UAP_API_KEY: {'not set (⚠️ all authenticated requests rejected)' if not API_KEY else 'custom (✓ set from env)'}")
