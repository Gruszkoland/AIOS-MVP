"""
UAP Blueprint: Tasks (Phase B)
Replaces mock data in api_phase_b.py with TASKS_STORE from blueprints/__init__.py.

Routes (prefix: /mapi/v1):
  GET  /tasks        — list tasks (filter: session_id, status)
  GET  /tasks/stats  — task counts by status

Registered in: uap/backend/api.py _register_blueprints()
Consolidation target: v2.0.0 (PostgreSQL-backed)
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from . import TASKS_STORE, require_api_key

logger = logging.getLogger("adrion.uap.blueprints.tasks_phase_b")

tasks_phase_b_bp = Blueprint("tasks_phase_b", __name__, url_prefix="/mapi/v1")


@tasks_phase_b_bp.route("/tasks", methods=["GET"])
@require_api_key
def list_tasks():
    """List tasks from in-memory TASKS_STORE (migrates to PostgreSQL in v2.0.0)."""
    session_id = request.args.get("session_id", "")
    status_filter = request.args.get("status", "")

    tasks = list(TASKS_STORE.values())

    if session_id:
        tasks = [t for t in tasks if t.get("session_id") == session_id]
    if status_filter:
        tasks = [t for t in tasks if t.get("status") == status_filter]

    # Sort: running first, then by updated_at desc
    tasks.sort(key=lambda t: (t.get("status") != "running", t.get("updated_at", "")), reverse=False)

    logger.info("GET /tasks: returned %d tasks", len(tasks))
    return jsonify({"success": True, "tasks": tasks, "total": len(tasks)})


@tasks_phase_b_bp.route("/tasks/stats", methods=["GET"])
@require_api_key
def task_stats():
    """Aggregate task counts by status from TASKS_STORE."""
    counts: dict[str, int] = {}
    for task in TASKS_STORE.values():
        s = task.get("status", "unknown")
        counts[s] = counts.get(s, 0) + 1

    counts.setdefault("completed", 0)
    counts.setdefault("running", 0)
    counts.setdefault("failed", 0)
    counts.setdefault("pending", 0)
    counts["total"] = sum(counts.values())

    logger.info("GET /tasks/stats: %s", counts)
    return jsonify({"success": True, **counts})
