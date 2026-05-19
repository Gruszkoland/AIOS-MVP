"""
Phase B: Backend API Integration
File: uap/backend/api_phase_b.py
Date: 2026-04-05
Status: ACTIVE — registered in api.py _register_blueprints()

NOTE: This file is scheduled for consolidation into uap/backend/blueprints/ in v2.0.0.
      Until then, it is the authoritative source for tasks/agents management endpoints.

7 REST ENDPOINTS FOR TASKS & AGENTS MANAGEMENT
All endpoints require X-API-Key header (value from UAP_API_KEY env var).
"""

import hmac
import os
import sys

from flask import request, jsonify, Blueprint
from datetime import datetime
import uuid
import json
import logging

logger = logging.getLogger("adrion.uap.api_phase_b")

_UAP_API_KEY = os.getenv("UAP_API_KEY", "")
if not _UAP_API_KEY:
    if os.getenv("ENVIRONMENT") == "production":
        logger.critical(
            "[SECURITY] UAP_API_KEY is not set in PRODUCTION — refusing to start."
        )
        sys.exit(1)
    else:
        logger.warning(
            "[SECURITY] UAP_API_KEY is not set — all authenticated requests will be rejected."
        )

# Create blueprint for Phase B endpoints
phase_b_bp = Blueprint('phase_b', __name__, url_prefix='/mapi/v1')

# ──────────────────────────────────────────────────────────────────────────
# AUTHENTICATION DECORATOR
# ──────────────────────────────────────────────────────────────────────────

def require_api_key(f):
    """Decorator to require X-API-Key authentication (timing-safe comparison)."""
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key', '')
        if not _UAP_API_KEY or not hmac.compare_digest(api_key, _UAP_API_KEY):
            logger.warning("Unauthorized API request: %s", request.endpoint)
            return jsonify({"success": False, "error": "Unauthorized. Invalid or missing X-API-Key"}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# ──────────────────────────────────────────────────────────────────────────
# 1. GET /mapi/v1/tasks — List all active tasks
# ──────────────────────────────────────────────────────────────────────────

@phase_b_bp.route('/tasks', methods=['GET'])
@require_api_key
def get_tasks():
    """
    Fetch all active tasks from database

    Query Parameters:
    - session_id (optional): Filter by session
    - status (optional): Filter by status (pending/running/completed/failed)

    Response:
    {
      "success": true,
      "tasks": [{"id": "task-001", "name": "...", "status": "running", ...}],
      "total": 4
    }
    """
    try:
        session_id = request.args.get('session_id', 'default')
        status_filter = request.args.get('status', '')

        # Build query
        query = "SELECT * FROM tasks WHERE session_id = %s"
        params = [session_id]

        if status_filter:
            query += " AND status = %s"
            params.append(status_filter)

        query += " ORDER BY updated_at DESC LIMIT 50"

        # Execute query (pseudo-code - adjust to your DB library)
        # For demonstration, this shows the expected structure
        tasks = []
        # rows = db.execute(query, params)
        # tasks = [dict(row) for row in rows]

        # MOCK DATA for Phase B testing (replace with real DB query above)
        tasks = [
            {
                "id": "task-001",
                "session_id": "default",
                "name": "Deploy Backend to Production",
                "agent": "Architect",
                "status": "running",
                "progress": 65,
                "eta_seconds": 120,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            },
            {
                "id": "task-002",
                "session_id": "default",
                "name": "Database Migration v3.2",
                "agent": "SAP",
                "status": "running",
                "progress": 40,
                "eta_seconds": 300,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        ]

        logger.info(f"GET /tasks: returned {len(tasks)} tasks")
        return jsonify({
            "success": True,
            "tasks": tasks,
            "total": len(tasks)
        }), 200

    except Exception as e:
        logger.error(f"Error in GET /tasks: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

# ──────────────────────────────────────────────────────────────────────────
# 2. GET /mapi/v1/tasks/stats — Get task statistics
# ──────────────────────────────────────────────────────────────────────────

@phase_b_bp.route('/tasks/stats', methods=['GET'])
@require_api_key
def get_task_stats():
    """
    Get task statistics (counts by status)

    Response:
    {
      "success": true,
      "completed": 1,
      "running": 2,
      "failed": 0,
      "pending": 1,
      "total": 4
    }
    """
    try:
        # REAL IMPLEMENTATION:
        # SELECT COUNT(*) as count, status FROM tasks GROUP BY status

        # MOCK DATA for Phase B testing
        stats = {
            "completed": 1,
            "running": 2,
            "failed": 0,
            "pending": 1
        }
        stats["total"] = sum(stats.values())

        logger.info(f"GET /tasks/stats: {stats}")
        return jsonify({
            "success": True,
            **stats
        }), 200

    except Exception as e:
        logger.error(f"Error in GET /tasks/stats: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

# ──────────────────────────────────────────────────────────────────────────
# 3. GET /mapi/v1/agents — List all agents
# ──────────────────────────────────────────────────────────────────────────

@phase_b_bp.route('/agents', methods=['GET'])
@require_api_key
def list_agents():
    """
    Fetch all agents from database

    Query Parameters:
    - active (optional): true/false to filter by active status

    Response:
    {
      "success": true,
      "agents": [
        {
          "id": "agent-1",
          "name": "Librarian",
          "role": "Knowledge Management",
          "personality": "...",
          "description": "...",
          "trust_score": 0.95,
          "capability_level": "expert",
          "skills": ["documentation", "search"],
          "active": true,
          "success_rate": 0.98,
          "tasks_completed": 342
        }
      ],
      "total": 4
    }
    """
    try:
        active_only = request.args.get('active', '').lower() == 'true'

        # REAL IMPLEMENTATION:
        # query = "SELECT * FROM agents ORDER BY active DESC, trust_score DESC"
        # if active_only:
        #     query = "SELECT * FROM agents WHERE active = TRUE ORDER BY trust_score DESC"

        # MOCK DATA for Phase B testing
        agents = [
            {
                "id": "agent-1",
                "name": "Librarian",
                "role": "Knowledge Management",
                "personality": "Organized, precise, detail-oriented",
                "description": "Manages knowledge base and documentation",
                "trust_score": 0.95,
                "capability_level": "expert",
                "skills": ["documentation", "search", "organization"],
                "active": True,
                "success_rate": 0.98,
                "tasks_completed": 342,
                "created_at": datetime.now().isoformat()
            },
            {
                "id": "agent-2",
                "name": "Architect",
                "role": "System Design",
                "personality": "Strategic, visionary, forward-thinking",
                "description": "Designs system architecture and scaling patterns",
                "trust_score": 0.88,
                "capability_level": "expert",
                "skills": ["design", "architecture", "planning"],
                "active": True,
                "success_rate": 0.92,
                "tasks_completed": 187,
                "created_at": datetime.now().isoformat()
            },
            {
                "id": "agent-3",
                "name": "Auditor",
                "role": "Risk Management",
                "personality": "Thorough, analytical, cautious",
                "description": "Conducts audits and identifies risks",
                "trust_score": 0.87,
                "capability_level": "expert",
                "skills": ["audit", "risk-assessment", "compliance"],
                "active": True,
                "success_rate": 0.91,
                "tasks_completed": 156,
                "created_at": datetime.now().isoformat()
            },
            {
                "id": "agent-4",
                "name": "Sentinel",
                "role": "Security & Monitoring",
                "personality": "Vigilant, protective, always alert",
                "description": "Monitors system health and detects threats",
                "trust_score": 0.92,
                "capability_level": "expert",
                "skills": ["monitoring", "security", "alerting"],
                "active": True,
                "success_rate": 0.95,
                "tasks_completed": 421,
                "created_at": datetime.now().isoformat()
            }
        ]

        logger.info(f"GET /agents: returned {len(agents)} agents")
        return jsonify({
            "success": True,
            "agents": agents,
            "total": len(agents)
        }), 200

    except Exception as e:
        logger.error(f"Error in GET /agents: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

# ──────────────────────────────────────────────────────────────────────────
# 4. POST /mapi/v1/agents/create — Create new agent
# ──────────────────────────────────────────────────────────────────────────

@phase_b_bp.route('/agents/create', methods=['POST'])
@require_api_key
def create_agent():
    """
    Create new agent

    Request Body:
    {
      "name": "NewAgent",
      "role": "Role/Specialization",
      "personality": "Agent personality description",
      "description": "Full description",
      "capability_level": "expert",
      "skills": ["skill1", "skill2"],
      "trust_score": 0.85,
      "active": true
    }

    Response:
    {
      "success": true,
      "id": "agent-xxxxx",
      "message": "Agent created successfully"
    }
    """
    try:
        data = request.json

        # Validate required fields
        required = ['name', 'role', 'personality', 'description', 'capability_level']
        missing = [f for f in required if f not in data]
        if missing:
            return jsonify({
                "success": False,
                "error": f"Missing required fields: {', '.join(missing)}"
            }), 400

        agent_id = f"agent-{uuid.uuid4().hex[:8]}"
        skills_json = json.dumps(data.get('skills', []))

        # REAL IMPLEMENTATION:
        # cursor = db.cursor()
        # cursor.execute("""
        #     INSERT INTO agents
        #     (id, name, role, personality, description, trust_score, capability_level, skills, active)
        #     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        # """, [...])
        # db.commit()

        logger.info(f"POST /agents/create: Created agent {agent_id} ({data['name']})")
        return jsonify({
            "success": True,
            "id": agent_id,
            "message": f"Agent '{data['name']}' created successfully"
        }), 201

    except Exception as e:
        logger.error(f"Error in POST /agents/create: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

# ──────────────────────────────────────────────────────────────────────────
# 5. PUT /mapi/v1/agents/<agent_id> — Update agent
# ──────────────────────────────────────────────────────────────────────────

@phase_b_bp.route('/agents/<agent_id>', methods=['PUT'])
@require_api_key
def update_agent(agent_id):
    """
    Update existing agent

    Request Body: Any fields to update
    {
      "trust_score": 0.99,
      "personality": "Updated personality",
      "active": true,
      ...
    }

    Response:
    {
      "success": true,
      "id": "agent-xxxxx",
      "message": "Agent updated successfully"
    }
    """
    try:
        data = request.json

        # REAL IMPLEMENTATION:
        # fields = []
        # values = []
        # for field in ['name', 'role', 'personality', 'description', 'trust_score', 'capability_level', 'active']:
        #     if field in data:
        #         fields.append(f"{field} = %s")
        #         values.append(data[field])
        # cursor = db.cursor()
        # cursor.execute(f"UPDATE agents SET {', '.join(fields)}, updated_at = NOW() WHERE id = %s", [..., agent_id])
        # db.commit()

        logger.info(f"PUT /agents/{agent_id}: Updated agent")
        return jsonify({
            "success": True,
            "id": agent_id,
            "message": "Agent updated successfully"
        }), 200

    except Exception as e:
        logger.error(f"Error in PUT /agents/{agent_id}: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

# ──────────────────────────────────────────────────────────────────────────
# 6. DELETE /mapi/v1/agents/<agent_id> — Delete agent (soft delete)
# ──────────────────────────────────────────────────────────────────────────

@phase_b_bp.route('/agents/<agent_id>', methods=['DELETE'])
@require_api_key
def delete_agent(agent_id):
    """
    Soft delete agent (mark inactive)

    Response:
    {
      "success": true,
      "id": "agent-xxxxx",
      "message": "Agent deleted successfully"
    }
    """
    try:
        # REAL IMPLEMENTATION:
        # cursor = db.cursor()
        # cursor.execute("UPDATE agents SET active = FALSE, updated_at = NOW() WHERE id = %s", [agent_id])
        # db.commit()

        logger.info(f"DELETE /agents/{agent_id}: Agent soft-deleted")
        return jsonify({
            "success": True,
            "id": agent_id,
            "message": "Agent deleted successfully"
        }), 200

    except Exception as e:
        logger.error(f"Error in DELETE /agents/{agent_id}: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

# ──────────────────────────────────────────────────────────────────────────
# 7. GET /mapi/v1/agents/<agent_id> — Get single agent
# ──────────────────────────────────────────────────────────────────────────

@phase_b_bp.route('/agents/<agent_id>', methods=['GET'])
@require_api_key
def get_agent(agent_id):
    """
    Fetch single agent details by ID

    Response:
    {
      "success": true,
      "agent": {
        "id": "agent-1",
        "name": "Librarian",
        "role": "Knowledge Management",
        ...
      }
    }
    """
    try:
        # REAL IMPLEMENTATION:
        # cursor = db.cursor()
        # cursor.execute("SELECT * FROM agents WHERE id = %s", [agent_id])
        # result = cursor.fetchone()
        # if not result:
        #     return jsonify({"success": False, "error": "Agent not found"}), 404

        # MOCK DATA for Phase B testing
        agent = {
            "id": "agent-1",
            "name": "Librarian",
            "role": "Knowledge Management",
            "personality": "Organized, precise, detail-oriented",
            "description": "Manages knowledge base and documentation",
            "trust_score": 0.95,
            "capability_level": "expert",
            "skills": ["documentation", "search", "organization"],
            "active": True,
            "success_rate": 0.98,
            "tasks_completed": 342,
            "created_at": datetime.now().isoformat()
        }

        logger.info(f"GET /agents/{agent_id}: Returned agent details")
        return jsonify({
            "success": True,
            "agent": agent
        }), 200

    except Exception as e:
        logger.error(f"Error in GET /agents/{agent_id}: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

# ──────────────────────────────────────────────────────────────────────────
# EXPORT FOR REGISTRATION IN FLASK APP
# ──────────────────────────────────────────────────────────────────────────

# In uap/backend/app.py add:
# from api_phase_b import phase_b_bp
# app.register_blueprint(phase_b_bp)
