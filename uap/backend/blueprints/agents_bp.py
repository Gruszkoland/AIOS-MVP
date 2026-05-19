"""
Agent Management Blueprint — Agent CRUD + Analytics operations

Routes (url_prefix=/mapi/v1/agents):
  GET    /                     — List all agents
  POST   /                     — Create new agent
  GET    /<agent_id>           — Get single agent
  PUT    /<agent_id>           — Update agent (P0-1 allowlisted columns)
  DELETE /<agent_id>           — Soft delete agent
  GET    /<agent_id>/history   — Agent activity history
  GET    /<agent_id>/performance — Agent performance metrics
  POST   /<agent_id>/feedback  — Submit feedback for agent
  GET    /leaderboard          — Agent leaderboard
  POST   /<agent_id>/log-activity — Log an agent activity
  POST   /create               — Create agent (legacy route)
"""
import json
import logging
import uuid
from datetime import datetime

from flask import Blueprint, jsonify, request

from . import ALLOWED_AGENT_COLUMNS, require_api_key

logger = logging.getLogger("adrion.uap.agents")

agents_bp = Blueprint("agents", __name__, url_prefix="/mapi/v1/agents")

# Configuration (set by parent app via init_app pattern)
USE_DATABASE = False
db = None

# In-memory agent store (Phase 1)
AGENTS_STORE = {}


# ── CRUD ────────────────────────────────────────────────────────────────────


@agents_bp.route("/", methods=["GET"])
@require_api_key
def list_agents():
    """List all agents."""
    try:
        if USE_DATABASE and db:
            result = db.query("""
                SELECT id, name, role, personality, description, trust_score, capability_level,
                       skills, active, created_at, success_rate, tasks_completed
                FROM agents ORDER BY active DESC, trust_score DESC
            """, [])
        else:
            result = [
                {"id": "agent-librarian", "name": "Librarian", "role": "Knowledge Management",
                 "personality": "Organized, thorough", "description": "Manages knowledge base",
                 "trust_score": 0.95, "capability_level": "expert", "skills": '["documentation"]',
                 "active": True, "success_rate": 0.98, "tasks_completed": 342},
                {"id": "agent-architect", "name": "Architect", "role": "System Design",
                 "personality": "Strategic thinker", "description": "Designs systems",
                 "trust_score": 0.88, "capability_level": "expert", "skills": '["design"]',
                 "active": True, "success_rate": 0.92, "tasks_completed": 215},
                {"id": "agent-auditor", "name": "Auditor", "role": "Security & Compliance",
                 "personality": "Detail-oriented", "description": "Performs audits",
                 "trust_score": 0.92, "capability_level": "expert", "skills": '["audit"]',
                 "active": True, "success_rate": 0.95, "tasks_completed": 178},
                {"id": "agent-sentinel", "name": "Sentinel", "role": "Monitoring & Alerts",
                 "personality": "Vigilant watcher", "description": "Monitors system",
                 "trust_score": 0.90, "capability_level": "expert", "skills": '["monitoring"]',
                 "active": True, "success_rate": 0.97, "tasks_completed": 412},
            ]

        agents = []
        for agent in (result if result else []):
            agent_dict = dict(agent) if hasattr(agent, '__getitem__') else agent
            if isinstance(agent_dict.get("skills"), str):
                try:
                    agent_dict["skills"] = json.loads(agent_dict["skills"])
                except Exception:
                    agent_dict["skills"] = []
            agents.append(agent_dict)

        return jsonify({"success": True, "agents": agents}), 200
    except Exception as e:
        logger.error("list_agents error: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@agents_bp.route("/create", methods=["POST"])
def create_agent_legacy():
    """Create new agent (legacy /create route)."""
    return _create_agent_impl()


@agents_bp.route("/", methods=["POST"])
@require_api_key
def create_agent():
    """Create new agent."""
    return _create_agent_impl()


def _create_agent_impl():
    """Shared implementation for agent creation."""
    data = request.get_json() or {}

    try:
        required = ["name", "role", "personality", "description", "capability_level"]
        if not all(f in data for f in required):
            return jsonify({"success": False, "error": "Missing required fields"}), 400

        agent_id = f"agent-{uuid.uuid4().hex[:8]}"

        if USE_DATABASE and db:
            skills_json = json.dumps(data.get("skills", []))
            db.execute("""
                INSERT INTO agents (id, name, role, personality, description, trust_score,
                                  capability_level, skills, active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                agent_id, data["name"], data["role"], data["personality"],
                data["description"], float(data.get("trust_score", 0.8)),
                data["capability_level"], skills_json, data.get("active", True),
            ])
        else:
            AGENTS_STORE[agent_id] = {
                "id": agent_id,
                "name": data["name"],
                "role": data["role"],
                "personality": data["personality"],
                "description": data["description"],
                "capability_level": data["capability_level"],
                "trust_score": data.get("trust_score", 0.8),
                "skills": data.get("skills", []),
                "active": data.get("active", True),
            }

        return jsonify({"success": True, "id": agent_id, "message": f"Agent {data['name']} created"}), 201
    except Exception as e:
        logger.error("create_agent error: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@agents_bp.route("/<agent_id>", methods=["GET"])
@require_api_key
def get_agent(agent_id: str):
    """Fetch single agent."""
    try:
        if USE_DATABASE and db:
            result = db.query("SELECT * FROM agents WHERE id = ?", [agent_id])
            if not result:
                return jsonify({"success": False, "error": "Agent not found"}), 404
            agent = dict(result[0]) if hasattr(result[0], '__getitem__') else result[0]
        else:
            agent = AGENTS_STORE.get(agent_id)
            if not agent:
                agent = {
                    "id": agent_id, "name": "Sample", "role": "Testing",
                    "personality": "Test", "description": "Sample agent",
                    "trust_score": 0.8, "capability_level": "expert",
                    "skills": [], "active": True,
                }

        if isinstance(agent.get("skills"), str):
            try:
                agent["skills"] = json.loads(agent["skills"])
            except Exception:
                agent["skills"] = []

        return jsonify({"success": True, "agent": agent}), 200
    except Exception as e:
        logger.error("get_agent error: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@agents_bp.route("/<agent_id>", methods=["PUT"])
@require_api_key
def update_agent(agent_id: str):
    """Update agent (with P0-1 security fix: sanitized column names).

    SECURITY: Only allows fields in ALLOWED_AGENT_COLUMNS frozenset.
    Unknown fields are rejected with clear error message.
    """
    data = request.get_json() or {}

    try:
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        # P0-1: Validate that only allowed columns are requested
        unknown_fields = set(data.keys()) - ALLOWED_AGENT_COLUMNS
        if unknown_fields:
            return jsonify({
                "success": False,
                "error": f"Unknown fields: {', '.join(sorted(unknown_fields))}",
                "allowed_fields": sorted(ALLOWED_AGENT_COLUMNS),
            }), 400

        if USE_DATABASE and db:
            fields, values = [], []
            for field in sorted(ALLOWED_AGENT_COLUMNS):
                if field in data:
                    fields.append(f"{field} = ?")
                    values.append(json.dumps(data[field]) if field == "skills" else data[field])

            if not fields:
                return jsonify({"success": False, "error": "No fields to update"}), 400

            values.append(agent_id)
            db.execute(f"UPDATE agents SET {', '.join(fields)} WHERE id = ?", values)
        else:
            if agent_id in AGENTS_STORE:
                for field in ALLOWED_AGENT_COLUMNS:
                    if field in data:
                        AGENTS_STORE[agent_id][field] = data[field]

        return jsonify({"success": True, "id": agent_id, "message": "Agent updated"}), 200
    except Exception as e:
        logger.error("update_agent error: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@agents_bp.route("/<agent_id>", methods=["DELETE"])
@require_api_key
def delete_agent(agent_id: str):
    """Soft delete agent (mark as inactive)."""
    try:
        if USE_DATABASE and db:
            db.execute("UPDATE agents SET active = FALSE WHERE id = ?", [agent_id])
        else:
            if agent_id in AGENTS_STORE:
                AGENTS_STORE[agent_id]["active"] = False

        return jsonify({"success": True, "id": agent_id, "message": "Agent deleted"}), 200
    except Exception as e:
        logger.error("delete_agent error: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


# ── Analytics ───────────────────────────────────────────────────────────────


@agents_bp.route("/<agent_id>/history", methods=["GET"])
def get_agent_history(agent_id: str):
    """Get agent activity history."""
    try:
        limit = request.args.get("limit", 50, type=int)

        if USE_DATABASE and db:
            history = db.query("""
                SELECT id, activity_type, description, result, duration_seconds, created_at, metadata
                FROM agent_activity
                WHERE agent_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, [agent_id, limit])
        else:
            history = [
                {"id": 1, "activity_type": "task_execution",
                 "description": f"Executed task for {agent_id}", "result": "success",
                 "duration_seconds": 45, "created_at": "2026-04-05T10:00:00"},
                {"id": 2, "activity_type": "analysis",
                 "description": f"Analyzed system for {agent_id}", "result": "success",
                 "duration_seconds": 120, "created_at": "2026-04-05T11:30:00"},
            ]

        activities = []
        for activity in (history if history else []):
            activity_dict = dict(activity) if hasattr(activity, '__getitem__') else activity
            activities.append(activity_dict)

        return jsonify({
            "success": True, "agent_id": agent_id,
            "history": activities, "total": len(activities),
        }), 200
    except Exception as e:
        logger.error("get_agent_history error: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@agents_bp.route("/<agent_id>/performance", methods=["GET"])
def get_agent_performance(agent_id: str):
    """Get agent performance metrics."""
    try:
        if USE_DATABASE and db:
            perf = db.query("""
                SELECT tasks_completed, tasks_failed, avg_duration_seconds, success_rate,
                       last_activity, monthly_tasks, arousal_level, dominance_level, pleasure_level
                FROM agent_performance
                WHERE agent_id = ?
            """, [agent_id])
            perf = perf[0] if perf else None
        else:
            perf = {
                "tasks_completed": 42, "tasks_failed": 3,
                "avg_duration_seconds": 65.5, "success_rate": 0.93,
                "last_activity": "2026-04-05T17:00:00", "monthly_tasks": 18,
                "arousal_level": 0.65, "dominance_level": 0.72, "pleasure_level": 0.80,
            }

        if not perf:
            return jsonify({"success": False, "error": "Agent not found"}), 404

        perf_dict = dict(perf) if hasattr(perf, '__getitem__') else perf

        return jsonify({"success": True, "agent_id": agent_id, "performance": perf_dict}), 200
    except Exception as e:
        logger.error("get_agent_performance error: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@agents_bp.route("/<agent_id>/feedback", methods=["POST"])
def add_agent_feedback(agent_id: str):
    """Submit feedback for an agent."""
    data = request.get_json() or {}

    try:
        rating = data.get("rating", 3)
        comment = data.get("comment", "")
        session_id = data.get("session_id", "default")

        if not (1 <= rating <= 5):
            return jsonify({"success": False, "error": "Rating must be 1-5"}), 400

        feedback_type = "positive" if rating >= 4 else ("negative" if rating <= 2 else "neutral")
        trust_adjustment = (rating - 3) * 0.02

        if USE_DATABASE and db:
            db.execute("""
                INSERT INTO agent_feedback (agent_id, session_id, rating, comment, trust_adjustment, feedback_type)
                VALUES (?, ?, ?, ?, ?, ?)
            """, [agent_id, session_id, rating, comment, trust_adjustment, feedback_type])

            db.execute("""
                UPDATE agents
                SET trust_score = MAX(0, MIN(1, trust_score + ?))
                WHERE id = ?
            """, [trust_adjustment, agent_id])

        return jsonify({
            "success": True, "message": "Feedback added",
            "trust_adjustment": trust_adjustment,
        }), 201
    except Exception as e:
        logger.error("add_agent_feedback error: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@agents_bp.route("/leaderboard", methods=["GET"])
def get_leaderboard():
    """Get agent leaderboard ranked by trust score and performance."""
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
                LIMIT ?
            """, [limit])
        else:
            leaderboard = [
                {"id": "agent-1", "name": "Librarian", "trust_score": 0.95,
                 "success_rate": 0.98, "tasks_completed": 342, "overall_score": 0.967},
                {"id": "agent-4", "name": "Sentinel", "trust_score": 0.92,
                 "success_rate": 0.95, "tasks_completed": 421, "overall_score": 0.938},
                {"id": "agent-2", "name": "Architect", "trust_score": 0.88,
                 "success_rate": 0.92, "tasks_completed": 187, "overall_score": 0.904},
                {"id": "agent-3", "name": "Auditor", "trust_score": 0.87,
                 "success_rate": 0.91, "tasks_completed": 156, "overall_score": 0.891},
            ]

        agents = []
        for i, agent in enumerate((leaderboard if leaderboard else []), 1):
            agent_dict = dict(agent) if hasattr(agent, '__getitem__') else agent
            agent_dict["rank"] = i
            agents.append(agent_dict)

        return jsonify({"success": True, "leaderboard": agents, "total": len(agents)}), 200
    except Exception as e:
        logger.error("get_leaderboard error: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@agents_bp.route("/<agent_id>/log-activity", methods=["POST"])
def log_agent_activity(agent_id: str):
    """Log an agent activity."""
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
                VALUES (?, ?, ?, ?, ?, ?, ?)
                RETURNING id
            """, [agent_id, session_id, activity_type, description, result, duration, json.dumps(metadata)])
        else:
            activity_id = 999

        return jsonify({"success": True, "activity_id": activity_id, "message": "Activity logged"}), 201
    except Exception as e:
        logger.error("log_agent_activity error: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500
