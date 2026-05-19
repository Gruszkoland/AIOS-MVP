"""
Genesis Record Blueprint — Audit trail + Checkpoint/Rollback management

Routes (url_prefix=/mapi/v1):
  GET  /genesis/logs                       — Query Genesis Record audit trail
  GET  /genesis/export                     — Export audit trail (JSON or CSV)
  POST /checkpoint/create                  — Create Rollback Checkpoint (RBC)
  GET  /checkpoint/list                    — List all checkpoints
  POST /checkpoint/<checkpoint_id>/restore — Restore from checkpoint
"""
import logging
import uuid
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request

from . import (
    CHECKPOINTS_STORE,
    GENESIS_LOGS,
    TASKS_STORE,
    log_genesis_record,
    require_api_key,
)

logger = logging.getLogger("adrion.uap.genesis")

genesis_bp = Blueprint("genesis", __name__, url_prefix="/mapi/v1")

# Configuration (set by parent app)
USE_DATABASE = False
db = None


# ── Genesis Record Audit Trail ──────────────────────────────────────────────


@genesis_bp.route("/genesis/logs", methods=["GET"])
@require_api_key
def genesis_logs():
    """Query Genesis Record audit trail.

    Query params:
        agent  — Filter by agent name
        since  — Time window ('1h', '24h', '7d')
        status — Filter by status
        limit  — Max records (default 100)
    """
    agent_filter = request.args.get("agent")
    since_str = request.args.get("since")
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
            logs = db.query_genesis_logs(
                agent=agent_filter, since_hours=since_hours,
                status=status_filter, limit=limit,
            )
        except Exception as e:
            logger.warning("DB error: %s, falling back to in-memory", e)
            logs = _filter_in_memory_logs(since_hours, agent_filter, status_filter, limit)
    else:
        logs = _filter_in_memory_logs(since_hours, agent_filter, status_filter, limit)

    return jsonify({"logs": logs, "count": len(logs)})


@genesis_bp.route("/genesis/export", methods=["GET"])
@require_api_key
def genesis_export():
    """Export audit trail as JSON or CSV.

    Query params:
        format — 'json' (default) or 'csv'
    """
    export_format = request.args.get("format", "json")

    # Get all logs from database or in-memory
    if USE_DATABASE and db:
        try:
            all_logs = db.export_genesis_logs()
        except Exception as e:
            logger.warning("DB error: %s, falling back to in-memory", e)
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

        from flask import current_app
        return current_app.response_class(
            response=output.getvalue(),
            status=200,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=genesis_export.csv"},
        )

    # JSON format
    return jsonify(all_logs)


# ── Checkpoint & Rollback (RBC) ────────────────────────────────────────────


@genesis_bp.route("/checkpoint/create", methods=["POST"])
@require_api_key
def checkpoint_create():
    """Create Rollback Checkpoint (RBC)."""
    body = request.get_json(silent=True) or {}
    label = body.get("label", "")

    checkpoint_id = f"rbc-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}-{str(uuid.uuid4())[:8]}"

    # Snapshot current session state
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
        "git_commit": "local-checkpoint",
        "session_state": {
            "tasks_count": len(tasks_snapshot),
            "logs_count": len(logs_snapshot),
            "tasks": tasks_snapshot,
            "logs": logs_snapshot,
        },
    }

    CHECKPOINTS_STORE[checkpoint_id] = checkpoint

    log_genesis_record(
        task_id="system", agent="Master", status="created",
        action="RBC_checkpoint_created", guards_passed=9,
        notes=f"Checkpoint {checkpoint_id}",
        db=db, use_db=USE_DATABASE,
    )

    return jsonify(checkpoint), 201


@genesis_bp.route("/checkpoint/list", methods=["GET"])
@require_api_key
def checkpoint_list():
    """List all Rollback Checkpoints."""
    checkpoints = sorted(
        CHECKPOINTS_STORE.values(),
        key=lambda c: c["created_at"],
        reverse=True,
    )
    return jsonify({"checkpoints": checkpoints, "count": len(checkpoints)})


@genesis_bp.route("/checkpoint/<checkpoint_id>/restore", methods=["POST"])
@require_api_key
def checkpoint_restore(checkpoint_id: str):
    """Restore from Rollback Checkpoint."""
    checkpoint = CHECKPOINTS_STORE.get(checkpoint_id)

    # Try DB if in-memory store doesn't have it
    if not checkpoint and USE_DATABASE and db:
        try:
            checkpoint = db.get_checkpoint(checkpoint_id)
        except Exception as e:
            logger.warning("Failed to fetch checkpoint from DB: %s", e)

    if not checkpoint:
        return jsonify({"error": f"Checkpoint {checkpoint_id} not found"}), 404

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
        task_id="system", agent="Master", status="restored",
        action="RBC_checkpoint_restored", guards_passed=9,
        notes=f"Restored from {checkpoint_id}: label='{checkpoint.get('label', '')}'",
        db=db, use_db=USE_DATABASE,
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


# ── Helpers ─────────────────────────────────────────────────────────────────


def _filter_in_memory_logs(
    since_hours: int,
    agent_filter: str = None,
    status_filter: str = None,
    limit: int = 100,
) -> list:
    """Filter in-memory genesis logs by time, agent, and status."""
    logs = GENESIS_LOGS.copy()
    cutoff = datetime.now() - timedelta(hours=since_hours)
    logs = [entry for entry in logs if datetime.fromisoformat(entry["timestamp"]) > cutoff]
    if agent_filter:
        logs = [entry for entry in logs if entry["agent"] == agent_filter]
    if status_filter:
        logs = [entry for entry in logs if entry["status"] == status_filter]
    logs = sorted(logs, key=lambda entry: entry["timestamp"], reverse=True)[:limit]
    return logs
