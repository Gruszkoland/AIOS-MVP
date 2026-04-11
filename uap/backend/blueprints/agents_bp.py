"""
Agent Management Blueprint — Agent CRUD operations
"""
import json
import logging
import uuid

from flask import Blueprint, jsonify, request

from . import require_api_key, ALLOWED_AGENT_COLUMNS

logger = logging.getLogger("adrion.uap.agents")

agents_bp = Blueprint("agents", __name__, url_prefix="/mapi/v1/agents")

# Configuration (will be set by parent app)
USE_DATABASE = False
db = None

# In-memory agent store (Phase 1)
AGENTS_STORE = {}


@agents_bp.route("/", methods=["GET"])
@require_api_key
def list_agents():
    """List all agents.

    Response:
        {
            "success": true,
            "agents": [
                {
                    "id": "agent-123",
                    "name": "Agent Name",
                    "role": "Analyzer",
                    ...
                }
            ],
            "count": 1
        }
    """
    if USE_DATABASE and db:
        try:
            agents = db.query("SELECT * FROM agents WHERE active = TRUE", [])
            agent_list = [dict(a) if hasattr(a, '__getitem__') else a for a in agents]
        except Exception as e:
            logger.error("Failed to query agents: %s", e)
            agent_list = list(AGENTS_STORE.values())
    else:
        agent_list = [a for a in AGENTS_STORE.values() if a.get("active", True)]

    return jsonify({"success": True, "agents": agent_list, "count": len(agent_list)}), 200


@agents_bp.route("/", methods=["POST"])
@require_api_key
def create_agent():
    """Create new agent.

    Request:
        {
            "name": "My Agent",
            "role": "Analyzer",
            "personality": "Logical",
            "description": "Analyzes opportunities",
            "capability_level": "expert",
            "trust_score": 0.85,
            "skills": ["analysis", "scoring"],
            "active": true
        }

    Response:
        {
            "success": true,
            "id": "agent-abc123",
            "message": "Agent My Agent created"
        }
    """
    data = request.get_json() or {}

    # Validate required fields
    required = ["name", "role", "personality", "description", "capability_level"]
    if not all(f in data for f in required):
        return jsonify({"success": False, "error": "Missing required fields"}), 400

    agent_id = f"agent-{uuid.uuid4().hex[:8]}"

    if USE_DATABASE and db:
        try:
            skills_json = json.dumps(data.get("skills", []))
            db.execute(
                """
                INSERT INTO agents (id, name, role, personality, description, trust_score,
                                  capability_level, skills, active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                [
                    agent_id,
                    data["name"],
                    data["role"],
                    data["personality"],
                    data["description"],
                    float(data.get("trust_score", 0.8)),
                    data["capability_level"],
                    skills_json,
                    data.get("active", True),
                ],
            )
        except Exception as e:
            logger.error("Failed to create agent in DB: %s", e)
            return jsonify({"success": False, "error": str(e)}), 500
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


@agents_bp.route("/<agent_id>", methods=["GET"])
@require_api_key
def get_agent(agent_id):
    """Fetch single agent."""
    if USE_DATABASE and db:
        try:
            result = db.query("SELECT * FROM agents WHERE id = ?", [agent_id])
            if not result:
                return jsonify({"success": False, "error": "Agent not found"}), 404
            agent = dict(result[0]) if hasattr(result[0], "__getitem__") else result[0]
        except Exception as e:
            logger.error("Failed to fetch agent: %s", e)
            return jsonify({"success": False, "error": str(e)}), 500
    else:
        agent = AGENTS_STORE.get(agent_id)
        if not agent:
            return jsonify({"success": False, "error": "Agent not found"}), 404

    if isinstance(agent.get("skills"), str):
        agent["skills"] = json.loads(agent["skills"])

    return jsonify({"success": True, "agent": agent}), 200


@agents_bp.route("/<agent_id>", methods=["PUT"])
@require_api_key
def update_agent(agent_id):
    """Update agent (with P0-1 security fix: sanitized column names).

    Request:
        {
            "name": "New Name",
            "trust_score": 0.95,
            ...
        }

    SECURITY: Only allows fields in ALLOWED_AGENT_COLUMNS frozenset.
    Unknown fields are rejected with clear error message.
    """
    data = request.get_json() or {}

    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400

    # P0-1: Validate that only allowed columns are requested
    unknown_fields = set(data.keys()) - ALLOWED_AGENT_COLUMNS
    if unknown_fields:
        return (
            jsonify(
                {
                    "success": False,
                    "error": f"Unknown fields: {', '.join(sorted(unknown_fields))}",
                    "allowed_fields": sorted(ALLOWED_AGENT_COLUMNS),
                }
            ),
            400,
        )

    if USE_DATABASE and db:
        try:
            fields, values = [], []
            for field in sorted(ALLOWED_AGENT_COLUMNS):
                if field in data:
                    fields.append(f"{field} = ?")
                    values.append(json.dumps(data[field]) if field == "skills" else data[field])

            if not fields:
                return jsonify({"success": False, "error": "No fields to update"}), 400

            values.append(agent_id)
            db.execute(f"UPDATE agents SET {', '.join(fields)} WHERE id = ?", values)
        except Exception as e:
            logger.error("Failed to update agent: %s", e)
            return jsonify({"success": False, "error": str(e)}), 500
    else:
        if agent_id not in AGENTS_STORE:
            return jsonify({"success": False, "error": "Agent not found"}), 404

        for field in ALLOWED_AGENT_COLUMNS:
            if field in data:
                AGENTS_STORE[agent_id][field] = data[field]

    return jsonify({"success": True, "id": agent_id, "message": "Agent updated"}), 200


@agents_bp.route("/<agent_id>", methods=["DELETE"])
@require_api_key
def delete_agent(agent_id):
    """Soft delete agent (mark as inactive)."""
    if USE_DATABASE and db:
        try:
            db.execute("UPDATE agents SET active = FALSE WHERE id = ?", [agent_id])
        except Exception as e:
            logger.error("Failed to delete agent: %s", e)
            return jsonify({"success": False, "error": str(e)}), 500
    else:
        if agent_id not in AGENTS_STORE:
            return jsonify({"success": False, "error": "Agent not found"}), 404
        AGENTS_STORE[agent_id]["active"] = False

    return jsonify({"success": True, "id": agent_id, "message": "Agent deleted"}), 200
