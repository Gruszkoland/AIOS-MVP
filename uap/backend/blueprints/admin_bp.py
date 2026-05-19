"""
Admin Blueprint — Session/Chat orchestration, Dashboard stats, Kubernetes integration

Routes (url_prefix=/mapi/v1):
  Session/Chat:
    POST /session/create          — Create new user session
    GET  /session/<session_id>    — Get session by ID
    GET  /session/previous        — List previous sessions
    POST /chat/message            — Send message to AI orchestrator
    GET  /chat/history            — Get chat history for session
    POST /startup/auto-run        — Trigger autonomous startup sequence
    GET  /startup/status          — Get auto-startup status

  Dashboard:
    GET  /tasks                   — Fetch active tasks for dashboard
    GET  /tasks/stats             — Get task statistics

  Kubernetes:
    GET  /kubernetes/cluster-info       — Cluster information
    GET  /kubernetes/pods               — Pod status listing
    GET  /kubernetes/services           — Services listing
    GET  /kubernetes/deployments        — Deployments listing
    GET  /kubernetes/pod/<name>/logs    — Pod logs
    POST /kubernetes/pod/<name>/restart — Restart pod
    GET  /kubernetes/metrics            — Cluster metrics
    GET  /kubernetes/events             — Cluster events
    POST /kubernetes/watch/start        — Start K8s watcher
    POST /kubernetes/watch/stop         — Stop K8s watcher
    GET  /kubernetes/watch/events       — Get queued watcher events
    GET  /kubernetes/stream             — SSE stream for real-time K8s updates
"""
import json
import logging
import time
from datetime import datetime

from flask import Blueprint, jsonify, request

from . import TASKS_STORE, log_genesis_record, require_api_key

logger = logging.getLogger("adrion.uap.admin")

admin_bp = Blueprint("admin", __name__, url_prefix="/mapi/v1")

# Configuration (set by parent app)
USE_DATABASE = False
db = None
K8S_INTEGRATION = None
K8S_ENABLED = False
K8S_WATCHER = None
K8S_WATCHER_ENABLED = False

# Chat components (lazy-initialized)
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
                llm_backend=None,
                master_orchestrator=None,
            )
            _auto_startup = AutoStartupSequence(
                session_manager=_session_manager,
                db_instance=db,
                chat_orchestrator=_chat_orchestrator,
            )
            logger.info("Chat orchestrator components initialized")
        except ImportError as e:
            logger.warning("Chat components not available: %s", e)


# ── Session Management ──────────────────────────────────────────────────────


@admin_bp.route("/session/create", methods=["POST"])
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
        logger.error("Session creation failed: %s", e)
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/session/<session_id>", methods=["GET"])
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
        logger.error("Session retrieval failed: %s", e)
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/session/previous", methods=["GET"])
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
        logger.error("Session list failed: %s", e)
        return jsonify({"error": str(e)}), 500


# ── Chat Orchestrator ───────────────────────────────────────────────────────


@admin_bp.route("/chat/message", methods=["POST"])
def chat_message():
    """Send message to AI orchestrator in a session."""
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

        _ensure_chat_components()
        session = _session_manager.get_session(session_id)
        if not session:
            return jsonify({"error": "Session not found"}), 404

        result = _chat_orchestrator.process_message(session_id, message, context)

        return jsonify(result), 200

    except Exception as e:
        logger.error("Chat message processing failed: %s", e)
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/chat/history", methods=["GET"])
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
        logger.error("Chat history retrieval failed: %s", e)
        return jsonify({"error": str(e)}), 500


# ── Auto Startup ────────────────────────────────────────────────────────────


@admin_bp.route("/startup/auto-run", methods=["POST"])
def auto_startup_run():
    """Trigger autonomous startup sequence."""
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
        logger.error("Auto-startup sequence failed: %s", e)
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/startup/status", methods=["GET"])
def auto_startup_status():
    """Get auto-startup status."""
    _ensure_chat_components()
    if not _auto_startup:
        return jsonify({"error": "Auto-startup not available"}), 503

    try:
        user_id = request.args.get("user_id", "anonymous")
        previous_sessions = (
            _session_manager.list_previous_sessions(user_id, 5)
            if _session_manager else []
        )

        return jsonify({
            "user_id": user_id,
            "previous_sessions": previous_sessions,
            "ready": True,
        }), 200

    except Exception as e:
        logger.error("Auto-startup status failed: %s", e)
        return jsonify({"error": str(e)}), 500


# ── Dashboard Task Stats ───────────────────────────────────────────────────


@admin_bp.route("/tasks", methods=["GET"])
def get_active_tasks():
    """Fetch active tasks for current session (dashboard endpoint).

    Returns real task data from TASKS_STORE (in-memory task registry).
    Query params:
        - status: filter by task status (submitted, executing, completed, failed)
        - limit: max tasks to return (default 50)
    """
    try:
        status_filter = request.args.get("status")
        limit = request.args.get("limit", 50, type=int)

        tasks = list(TASKS_STORE.values())

        if status_filter:
            tasks = [t for t in tasks if t.get("status") == status_filter]

        tasks = tasks[:limit]

        return jsonify({
            "success": True,
            "tasks": tasks,
            "total": len(tasks),
        }), 200
    except Exception as e:
        logger.error("get_active_tasks error: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@admin_bp.route("/tasks/stats", methods=["GET"])
def get_task_stats():
    """Get task statistics (dashboard endpoint).

    Computes real counts from TASKS_STORE keyed by status.
    """
    try:
        all_tasks = list(TASKS_STORE.values())

        completed = sum(1 for t in all_tasks if t.get("status") == "completed")
        pending = sum(1 for t in all_tasks if t.get("status") in ("submitted", "dry_run"))
        running = sum(1 for t in all_tasks if t.get("status") == "executing")
        failed = sum(1 for t in all_tasks if t.get("status") == "failed")
        total = completed + pending + running + failed

        return jsonify({
            "success": True,
            "completed": completed,
            "pending": pending,
            "running": running,
            "failed": failed,
            "total": total,
            "success_rate": completed / max(1, total),
        }), 200
    except Exception as e:
        logger.error("get_task_stats error: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


# ── Kubernetes Cluster Integration ──────────────────────────────────────────


@admin_bp.route("/kubernetes/cluster-info", methods=["GET"])
@require_api_key
def kubernetes_cluster_info():
    """Get Kubernetes cluster information."""
    if not K8S_ENABLED or not K8S_INTEGRATION:
        return jsonify({"error": "Kubernetes integration not available"}), 503

    try:
        cluster_info = K8S_INTEGRATION.get_cluster_info()

        log_genesis_record(
            task_id="system", agent="Monitor", status="success",
            action="kubernetes_cluster_info_queried", guards_passed=9,
            notes=f"Cluster: {cluster_info.get('cluster_name', 'unknown')}",
            db=db, use_db=USE_DATABASE,
        )

        return jsonify({
            "status": "success",
            "cluster": cluster_info,
            "queried_at": datetime.now().isoformat(),
        }), 200

    except Exception as e:
        logger.error("kubernetes_cluster_info error: %s", e)
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/kubernetes/pods", methods=["GET"])
@require_api_key
def kubernetes_pods_status():
    """Get pod status listing by namespace."""
    if not K8S_ENABLED or not K8S_INTEGRATION:
        return jsonify({"error": "Kubernetes integration not available"}), 503

    try:
        pods = K8S_INTEGRATION.get_pods_status()

        log_genesis_record(
            task_id="system", agent="Monitor", status="success",
            action="kubernetes_pods_query", guards_passed=9,
            notes=f"Retrieved {pods.get('total_pods', 0)} pods",
            db=db, use_db=USE_DATABASE,
        )

        return jsonify({
            "status": "success",
            "pods": pods,
            "queried_at": datetime.now().isoformat(),
        }), 200

    except Exception as e:
        logger.error("kubernetes_pods_status error: %s", e)
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/kubernetes/services", methods=["GET"])
@require_api_key
def kubernetes_services():
    """Get Kubernetes services by namespace."""
    if not K8S_ENABLED or not K8S_INTEGRATION:
        return jsonify({"error": "Kubernetes integration not available"}), 503

    try:
        services = K8S_INTEGRATION.get_services()

        log_genesis_record(
            task_id="system", agent="Monitor", status="success",
            action="kubernetes_services_query", guards_passed=9,
            notes=f"Retrieved {len(services.get('services', []))} services",
            db=db, use_db=USE_DATABASE,
        )

        return jsonify({
            "status": "success",
            "services": services,
            "queried_at": datetime.now().isoformat(),
        }), 200

    except Exception as e:
        logger.error("kubernetes_services error: %s", e)
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/kubernetes/deployments", methods=["GET"])
@require_api_key
def kubernetes_deployments():
    """Get Kubernetes deployments by namespace."""
    if not K8S_ENABLED or not K8S_INTEGRATION:
        return jsonify({"error": "Kubernetes integration not available"}), 503

    try:
        deployments = K8S_INTEGRATION.get_deployments()

        log_genesis_record(
            task_id="system", agent="Monitor", status="success",
            action="kubernetes_deployments_query", guards_passed=9,
            notes=f"Retrieved {len(deployments.get('deployments', []))} deployments",
            db=db, use_db=USE_DATABASE,
        )

        return jsonify({
            "status": "success",
            "deployments": deployments,
            "queried_at": datetime.now().isoformat(),
        }), 200

    except Exception as e:
        logger.error("kubernetes_deployments error: %s", e)
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/kubernetes/pod/<pod_name>/logs", methods=["GET"])
@require_api_key
def kubernetes_pod_logs(pod_name: str):
    """Get logs from a specific pod."""
    if not K8S_ENABLED or not K8S_INTEGRATION:
        return jsonify({"error": "Kubernetes integration not available"}), 503

    try:
        lines = request.args.get("lines", default=50, type=int)
        namespace = request.args.get("namespace", default="adrion-369")

        logs = K8S_INTEGRATION.get_pod_logs(pod_name, namespace=namespace, lines=lines)

        log_genesis_record(
            task_id="system", agent="Monitor", status="success",
            action="kubernetes_pod_logs_retrieved", guards_passed=9,
            notes=f"Retrieved {len(logs.get('logs', ''))} bytes from pod {pod_name}",
            db=db, use_db=USE_DATABASE,
        )

        return jsonify({
            "status": "success",
            "pod_name": pod_name,
            "namespace": namespace,
            "logs": logs.get("logs", ""),
            "queried_at": datetime.now().isoformat(),
        }), 200

    except Exception as e:
        logger.error("kubernetes_pod_logs error: %s", e)
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/kubernetes/pod/<pod_name>/restart", methods=["POST"])
@require_api_key
def kubernetes_pod_restart(pod_name: str):
    """Restart a specific pod (delete and recreate)."""
    if not K8S_ENABLED or not K8S_INTEGRATION:
        return jsonify({"error": "Kubernetes integration not available"}), 503

    try:
        namespace = request.args.get("namespace", default="adrion-369")
        result = K8S_INTEGRATION.restart_pod(pod_name, namespace=namespace)

        log_genesis_record(
            task_id=f"pod-restart-{datetime.now().timestamp()}",
            agent="Sentinel", status="completed",
            action="kubernetes_pod_restart", guards_passed=9,
            notes=f"Pod {pod_name} forcefully restarted in namespace {namespace}",
            db=db, use_db=USE_DATABASE,
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
        logger.error("kubernetes_pod_restart error: %s", e)

        log_genesis_record(
            task_id=f"pod-restart-error-{datetime.now().timestamp()}",
            agent="Sentinel", status="failed",
            action="kubernetes_pod_restart_failed", guards_passed=7,
            notes=f"Failed to restart pod {pod_name}: {str(e)}",
            db=db, use_db=USE_DATABASE,
        )

        return jsonify({"error": str(e)}), 500


@admin_bp.route("/kubernetes/metrics", methods=["GET"])
@require_api_key
def kubernetes_metrics():
    """Get Kubernetes cluster metrics from Prometheus."""
    if not K8S_ENABLED or not K8S_INTEGRATION:
        return jsonify({"error": "Kubernetes integration not available"}), 503

    try:
        metric = request.args.get("metric", default="cluster_health")
        metrics = K8S_INTEGRATION.get_metrics(metric)

        log_genesis_record(
            task_id="system", agent="Monitor", status="success",
            action="kubernetes_metrics_query", guards_passed=9,
            notes=f"Queried metric: {metric}",
            db=db, use_db=USE_DATABASE,
        )

        return jsonify({
            "status": "success",
            "metric": metric,
            "data": metrics,
            "queried_at": datetime.now().isoformat(),
        }), 200

    except Exception as e:
        logger.error("kubernetes_metrics error: %s", e)
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/kubernetes/events", methods=["GET"])
@require_api_key
def kubernetes_events():
    """Get recent Kubernetes cluster events."""
    if not K8S_ENABLED or not K8S_INTEGRATION:
        return jsonify({"error": "Kubernetes integration not available"}), 503

    try:
        events = K8S_INTEGRATION.get_namespace_events()

        log_genesis_record(
            task_id="system", agent="Monitor", status="success",
            action="kubernetes_events_query", guards_passed=9,
            notes=f"Retrieved {len(events.get('events', []))} cluster events",
            db=db, use_db=USE_DATABASE,
        )

        return jsonify({
            "status": "success",
            "events": events,
            "queried_at": datetime.now().isoformat(),
        }), 200

    except Exception as e:
        logger.error("kubernetes_events error: %s", e)
        return jsonify({"error": str(e)}), 500


# ── Kubernetes Real-Time Updates ────────────────────────────────────────────


@admin_bp.route("/kubernetes/watch/start", methods=["POST"])
@require_api_key
def kubernetes_watch_start():
    """Start watching Kubernetes cluster for real-time updates."""
    if not K8S_WATCHER_ENABLED or not K8S_WATCHER:
        return jsonify({"error": "Kubernetes WebSocket watcher not available"}), 503

    try:
        K8S_WATCHER.start_watching()

        log_genesis_record(
            task_id="system", agent="Monitor", status="started",
            action="kubernetes_watcher_start", guards_passed=9,
            notes="Real-time K8s cluster watcher started",
            db=db, use_db=USE_DATABASE,
        )

        return jsonify({
            "status": "success",
            "message": "Kubernetes watcher started",
            "watch_type": "streaming",
            "started_at": datetime.now().isoformat(),
        }), 200

    except Exception as e:
        logger.error("kubernetes_watch_start error: %s", e)
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/kubernetes/watch/stop", methods=["POST"])
@require_api_key
def kubernetes_watch_stop():
    """Stop watching Kubernetes cluster."""
    if not K8S_WATCHER_ENABLED or not K8S_WATCHER:
        return jsonify({"error": "Kubernetes WebSocket watcher not available"}), 503

    try:
        K8S_WATCHER.stop_watching()

        log_genesis_record(
            task_id="system", agent="Monitor", status="stopped",
            action="kubernetes_watcher_stop", guards_passed=9,
            notes="Real-time K8s cluster watcher stopped",
            db=db, use_db=USE_DATABASE,
        )

        return jsonify({
            "status": "success",
            "message": "Kubernetes watcher stopped",
            "stopped_at": datetime.now().isoformat(),
        }), 200

    except Exception as e:
        logger.error("kubernetes_watch_stop error: %s", e)
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/kubernetes/watch/events", methods=["GET"])
@require_api_key
def kubernetes_watch_events():
    """Get queued real-time events from watcher (polling fallback for SSE)."""
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
        logger.error("kubernetes_watch_events error: %s", e)
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/kubernetes/stream", methods=["GET"])
@require_api_key
def kubernetes_stream_sse():
    """Server-Sent Events (SSE) stream for real-time K8s updates."""
    def generate():
        """Generator for SSE stream."""
        if K8S_WATCHER and not K8S_WATCHER.watch_thread:
            K8S_WATCHER.start_watching()

        try:
            yield f"data: {json.dumps({'type': 'connected', 'timestamp': datetime.now().isoformat()})}\n\n"

            while True:
                if K8S_WATCHER:
                    events = K8S_WATCHER.get_queued_events(max_count=10)
                    if events:
                        for event in events:
                            yield f"data: {json.dumps(event)}\n\n"
                time.sleep(1)

        except GeneratorExit:
            logger.info("SSE stream closed by client")
        except Exception as e:
            logger.error("SSE stream error: %s", e)

    if not K8S_WATCHER_ENABLED or not K8S_WATCHER:
        return jsonify({"error": "Kubernetes WebSocket watcher not available"}), 503

    log_genesis_record(
        task_id="system", agent="Monitor", status="opened",
        action="kubernetes_sse_stream_opened", guards_passed=9,
        notes="SSE stream for real-time K8s updates opened",
        db=db, use_db=USE_DATABASE,
    )

    from flask import current_app
    return current_app.response_class(
        response=generate(),
        status=200,
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
