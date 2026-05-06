"""
UAP Blueprint: Agents (Phase B)
Replaces mock data in api_phase_b.py with live AGENT_TRUST_SCORES + EBDI_TELEMETRY.

Routes (prefix: /mapi/v1):
  GET    /agents             — list agents with live trust scores
  GET    /agents/<agent_id>  — single agent details
  POST   /agents/create      — register new agent (in-memory until v2.0.0)
  PUT    /agents/<agent_id>  — update trust score / status
  DELETE /agents/<agent_id>  — soft-delete (set active=False)

Registered in: uap/backend/api.py _register_blueprints()
Consolidation target: v2.0.0 (PostgreSQL-backed)
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from . import AGENT_TRUST_SCORES, EBDI_TELEMETRY, require_api_key

logger = logging.getLogger("adrion.uap.blueprints.agents_phase_b")

agents_phase_b_bp = Blueprint("agents_phase_b", __name__, url_prefix="/mapi/v1")

# In-memory agent registry (warm from AGENT_TRUST_SCORES baseline)
_AGENTS: dict[str, dict] = {
    name: {
        "id": f"agent-{i+1}",
        "name": name,
        "trust_score": ts,
        "active": True,
        "role": _ROLES.get(name, "Specialist"),
        "skills": _SKILLS.get(name, []),
        "created_at": "2026-01-01T00:00:00+00:00",
        "tasks_completed": 0,
    }
    for i, (name, ts) in enumerate(AGENT_TRUST_SCORES.items())
}

# Role / skill metadata (static, matches GUARDIAN_LAWS_CANONICAL)
_ROLES: dict[str, str] = {
    "Librarian": "Knowledge Management",
    "SAP": "Strategic Analysis & Planning",
    "Auditor": "Risk & Compliance",
    "Sentinel": "Security & Monitoring",
    "Architect": "System Design",
    "Healer": "Self-Repair & Recovery",
    "Amplifier": "Signal Enhancement",
    "BoosterLever": "Performance Optimization",
    "Chronos": "Temporal Orchestration",
}

_SKILLS: dict[str, list[str]] = {
    "Librarian": ["documentation", "search", "rag"],
    "SAP": ["strategy", "planning", "forecasting"],
    "Auditor": ["audit", "risk-assessment", "compliance"],
    "Sentinel": ["monitoring", "security", "alerting"],
    "Architect": ["design", "architecture", "scaling"],
    "Healer": ["self-repair", "rollback", "recovery"],
    "Amplifier": ["signal-boost", "context-enrichment"],
    "BoosterLever": ["optimization", "throughput"],
    "Chronos": ["scheduling", "cadence", "timing"],
}

# Rebuild _AGENTS with correct _ROLES/_SKILLS (defined before dict comp above)
_AGENTS = {
    name: {
        "id": f"agent-{i+1}",
        "name": name,
        "trust_score": ts,
        "active": True,
        "role": _ROLES.get(name, "Specialist"),
        "skills": _SKILLS.get(name, []),
        "created_at": "2026-01-01T00:00:00+00:00",
        "tasks_completed": 0,
    }
    for i, (name, ts) in enumerate(AGENT_TRUST_SCORES.items())
}


def _enrich_agent(agent: dict) -> dict:
    """Attach live EBDI telemetry to agent record."""
    ebdi = EBDI_TELEMETRY.get(agent["name"], {})
    return {**agent, "ebdi": ebdi}


@agents_phase_b_bp.route("/agents", methods=["GET"])
@require_api_key
def list_agents():
    """Return all agents with live trust scores and EBDI telemetry."""
    active_only = request.args.get("active", "").lower() == "true"
    agents = [_enrich_agent(a) for a in _AGENTS.values() if not active_only or a["active"]]
    agents.sort(key=lambda a: a["trust_score"], reverse=True)

    logger.info("GET /agents: returned %d agents", len(agents))
    return jsonify({"success": True, "agents": agents, "total": len(agents)})


@agents_phase_b_bp.route("/agents/<agent_id>", methods=["GET"])
@require_api_key
def get_agent(agent_id: str):
    """Fetch single agent by id or name."""
    agent = next(
        (a for a in _AGENTS.values() if a["id"] == agent_id or a["name"] == agent_id),
        None,
    )
    if not agent:
        return jsonify({"success": False, "error": "Agent not found"}), 404
    return jsonify({"success": True, "agent": _enrich_agent(agent)})


@agents_phase_b_bp.route("/agents/create", methods=["POST"])
@require_api_key
def create_agent():
    """Register a new agent in the in-memory registry."""
    data = request.get_json(silent=True) or {}
    required = ["name", "role"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"success": False, "error": f"Missing fields: {missing}"}), 400

    name = data["name"].strip()
    if name in _AGENTS:
        return jsonify({"success": False, "error": f"Agent '{name}' already exists"}), 409

    agent_id = f"agent-{uuid.uuid4().hex[:8]}"
    _AGENTS[name] = {
        "id": agent_id,
        "name": name,
        "role": data["role"],
        "trust_score": float(data.get("trust_score", 0.75)),
        "active": bool(data.get("active", True)),
        "skills": data.get("skills", []),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tasks_completed": 0,
    }
    # Sync to shared trust store
    AGENT_TRUST_SCORES[name] = _AGENTS[name]["trust_score"]

    logger.info("POST /agents/create: registered agent '%s' (%s)", name, agent_id)
    return jsonify({"success": True, "id": agent_id, "message": f"Agent '{name}' created"}), 201


@agents_phase_b_bp.route("/agents/<agent_id>", methods=["PUT"])
@require_api_key
def update_agent(agent_id: str):
    """Update mutable fields (trust_score, active, skills) of an existing agent."""
    agent = next(
        (a for a in _AGENTS.values() if a["id"] == agent_id or a["name"] == agent_id),
        None,
    )
    if not agent:
        return jsonify({"success": False, "error": "Agent not found"}), 404

    data = request.get_json(silent=True) or {}
    mutable = {"trust_score", "active", "skills", "role"}
    for key in mutable & data.keys():
        agent[key] = data[key]

    # Sync trust score to shared store
    if "trust_score" in data:
        AGENT_TRUST_SCORES[agent["name"]] = float(data["trust_score"])

    logger.info("PUT /agents/%s: updated fields %s", agent_id, list(mutable & data.keys()))
    return jsonify({"success": True, "id": agent["id"], "message": "Agent updated"})


@agents_phase_b_bp.route("/agents/<agent_id>", methods=["DELETE"])
@require_api_key
def delete_agent(agent_id: str):
    """Soft-delete: set active=False (agent remains in registry)."""
    agent = next(
        (a for a in _AGENTS.values() if a["id"] == agent_id or a["name"] == agent_id),
        None,
    )
    if not agent:
        return jsonify({"success": False, "error": "Agent not found"}), 404

    agent["active"] = False
    logger.info("DELETE /agents/%s: soft-deleted '%s'", agent_id, agent["name"])
    return jsonify({"success": True, "id": agent["id"], "message": "Agent deactivated"})
