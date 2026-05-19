"""
Task Management Blueprint — Handles task delegation, status, and listing
"""
import logging
import threading
import time
from datetime import datetime
from functools import wraps
from typing import Optional

from flask import Blueprint, jsonify, request

from . import (
    TASKS_STORE,
    check_trust_score,
    find_best_persona,
    generate_task_id,
    log_genesis_record,
    require_api_key,
    validate_task_description,
)

logger = logging.getLogger("adrion.uap.tasks")

tasks_bp = Blueprint("tasks", __name__, url_prefix="/mapi/v1/task")

# Configuration (will move to config module)
USE_DATABASE = False  # Will be set by parent app
db = None  # Will be set by parent app
LLM_AVAILABLE = False  # Will be set by parent app


def _execute_task(task_id: str, agent: str, task_description: str, dry_run: bool = False):
    """Background task executor with optional LLM integration.

    Runs in background thread to avoid blocking HTTP response.
    """
    TASKS_STORE[task_id]["status"] = "executing"

    try:
        if dry_run:
            logger.info("event=dry_run task_id=%s agent=%s", task_id, agent)
            TASKS_STORE[task_id]["status"] = "completed"
            TASKS_STORE[task_id]["result"] = {
                "output": f"[dry_run] Would execute: {task_description}",
                "error": False,
                "confidence": 0.0,
            }
            log_genesis_record(task_id, agent, "completed", "dry_run", notes="Dry run mode")
            return

        # Try LLM execution (optional)
        try:
            from arbitrage.llm import chat as llm_chat

            llm_result = llm_chat(
                prompt=task_description,
                system=f"You are the {agent} persona in ADRION 369. Execute this task concisely.",
            )
            output = llm_result
            error = False
            confidence = 0.85
        except Exception as e:
            logger.error("Task execution error for %s: %s", task_id, e)
            output = f"[mock] {task_description}: System executed (LLM unavailable)"
            error = True
            confidence = 0.0

        TASKS_STORE[task_id]["status"] = "completed"
        TASKS_STORE[task_id]["result"] = {
            "output": output,
            "error": error,
            "confidence": confidence,
        }
        log_genesis_record(task_id, agent, "completed", "execution_success")

    except Exception as e:
        logger.error("Task execution error for %s: %s", task_id, e)
        TASKS_STORE[task_id]["status"] = "failed"
        TASKS_STORE[task_id]["result"] = {"error": str(e), "confidence": 0.0}
        log_genesis_record(task_id, agent, "failed", "execution_error", notes=str(e))


# ──────────────────────────────────────────────────────────────────────────
# Task Delegation
# ──────────────────────────────────────────────────────────────────────────


@tasks_bp.route("/delegate", methods=["POST"])
@require_api_key
def delegate_task():
    """Delegate task to best persona.

    Request:
        {
            "task_description": "Scout for XRP opportunities",
            "agent_hint": "SAP" (optional),
            "dry_run": false (optional)
        }

    Response:
        {
            "task_id": "upc-20260411-143000-ABCD",
            "status": "submitted",
            "assigned_agent": "SAP",
            "dry_run": false
        }
    """
    data = request.get_json() or {}
    task_description = data.get("task_description", "").strip()
    agent_hint = data.get("agent_hint")
    dry_run = data.get("dry_run", False)

    # Validation
    if not validate_task_description(task_description):
        return (
            jsonify(
                {
                    "error": "Invalid task_description: must be at least 5 characters",
                    "success": False,
                }
            ),
            400,
        )

    # Route to persona
    agent = find_best_persona(task_description, agent_hint=agent_hint)

    # Check trust score
    if not check_trust_score(agent):
        return (
            jsonify(
                {
                    "error": f"Agent {agent} has insufficient trust score (< 0.6)",
                    "success": False,
                }
            ),
            400,
        )

    # Create task record
    task_id = generate_task_id()
    TASKS_STORE[task_id] = {
        "task_id": task_id,
        "task_description": task_description,
        "assigned_agent": agent,
        "status": "submitted",
        "dry_run": dry_run,
        "result": None,
        "created_at": datetime.now().isoformat(),
    }

    log_genesis_record(task_id, agent, "submitted", "task_delegation")

    # Execute in background (unless dry_run)
    if not dry_run:
        thread = threading.Thread(
            target=_execute_task, args=(task_id, agent, task_description, dry_run)
        )
        thread.daemon = True
        thread.start()
    else:
        TASKS_STORE[task_id]["status"] = "dry_run"
        log_genesis_record(task_id, agent, "completed", "dry_run_created")

    return (
        jsonify(
            {
                "success": True,
                "task_id": task_id,
                "status": TASKS_STORE[task_id]["status"],
                "assigned_agent": agent,
                "dry_run": dry_run,
            }
        ),
        201,
    )


# ──────────────────────────────────────────────────────────────────────────
# Task Status & Retrieval
# ──────────────────────────────────────────────────────────────────────────


@tasks_bp.route("/<task_id>", methods=["GET"])
@require_api_key
def get_task_status(task_id: str):
    """Retrieve task status and result.

    Response:
        {
            "task_id": "upc-20260411-143000-ABCD",
            "status": "completed|executing|failed",
            "result": {...}
        }
    """
    task = TASKS_STORE.get(task_id)

    if not task:
        return jsonify({"success": False, "error": "Task not found"}), 404

    return jsonify({"success": True, "task": task}), 200


@tasks_bp.route("/list", methods=["GET"])
@require_api_key
def list_tasks():
    """List all tasks.

    Query params:
        - status: "submitted", "executing", "completed", "failed"
        - agent: Filter by agent name
        - limit: Max tasks to return (default 50)

    Response:
        {
            "count": 5,
            "tasks": [...]
        }
    """
    status_filter = request.args.get("status")
    agent_filter = request.args.get("agent")
    limit = request.args.get("limit", 50, type=int)

    filtered = list(TASKS_STORE.values())

    if status_filter:
        filtered = [t for t in filtered if t["status"] == status_filter]

    if agent_filter:
        filtered = [t for t in filtered if t["assigned_agent"] == agent_filter]

    limited = filtered[:limit]

    return (
        jsonify({"success": True, "count": len(limited), "tasks": limited}),
        200,
    )
