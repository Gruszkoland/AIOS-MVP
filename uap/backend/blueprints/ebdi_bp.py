"""
EBDI Blueprint — EBDI telemetry, Trust Scores, Guardian Laws, Crisis Mode, Conflict Resolution

Routes (url_prefix=/mapi/v1):
  GET  /agent/scores           — Trust Score heatmap for all agents
  GET  /agent/<agent>/score    — Single agent Trust Score + EBDI
  GET  /ebdi/telemetry         — Live EBDI (PAD) vectors for all agents
  GET  /guardian/laws          — 9 Guardian Laws status
  POST /crisis/activate        — Manually activate Crisis Mode
  POST /conflict/resolve       — Conflict Resolver weighted voting
"""
import logging
import os
from datetime import datetime

from flask import Blueprint, jsonify, request

from . import (
    AGENT_TRUST_SCORES,
    EBDI_TELEMETRY,
    GUARDIAN_LAWS_STATUS,
    log_genesis_record,
    require_api_key,
)

logger = logging.getLogger("adrion.uap.ebdi")

ebdi_bp = Blueprint("ebdi", __name__, url_prefix="/mapi/v1")

# Configuration (set by parent app)
USE_DATABASE = False
db = None


# ── Trust Scores ────────────────────────────────────────────────────────────


@ebdi_bp.route("/agent/scores", methods=["GET"])
@require_api_key
def agent_scores():
    """Get Trust Score heatmap for all agents."""
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


@ebdi_bp.route("/agent/<agent>/score", methods=["GET"])
@require_api_key
def agent_score(agent: str):
    """Get specific agent Trust Score + EBDI."""
    ts = AGENT_TRUST_SCORES.get(agent)
    if ts is None:
        return jsonify({"error": f"Agent {agent} not found"}), 404

    return jsonify({
        "agent": agent,
        "trust_score": ts,
        "status": "operational" if ts >= 0.6 else "needs_recalibration",
        "ebdi": EBDI_TELEMETRY.get(agent, {}),
    })


# ── EBDI Telemetry ──────────────────────────────────────────────────────────


@ebdi_bp.route("/ebdi/telemetry", methods=["GET"])
@require_api_key
def ebdi_telemetry():
    """Get live EBDI (PAD) vectors for all agents.

    Pure read — does NOT mutate state. EBDI drift is handled by the
    EBDIHomeostaticService background thread (ebdi_homeostasis.py).
    """
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


# ── Guardian Laws ───────────────────────────────────────────────────────────


@ebdi_bp.route("/guardian/laws", methods=["GET"])
@require_api_key
def guardian_laws():
    """Get 9 Guardian Laws status."""
    return jsonify({
        "laws": GUARDIAN_LAWS_STATUS,
        "compliance": sum(1 for law in GUARDIAN_LAWS_STATUS if law["status"] == "pass"),
        "total": len(GUARDIAN_LAWS_STATUS),
        "timestamp": datetime.now().isoformat(),
    })


# ── Crisis Mode ─────────────────────────────────────────────────────────────


@ebdi_bp.route("/crisis/activate", methods=["POST"])
@require_api_key
def crisis_activate():
    """Manually activate Crisis Mode (Arousal > 0.7)."""
    body = request.get_json(silent=True) or {}
    reason = body.get("reason", "Manual activation")

    # Simulate Sentinel activation
    EBDI_TELEMETRY["Sentinel"]["arousal"] = 0.95

    log_genesis_record(
        task_id="system", agent="Sentinel", status="active",
        action="crisis_mode_activated", guards_passed=8,
        notes=f"Crisis: {reason}",
        db=db, use_db=USE_DATABASE,
    )

    return jsonify({
        "status": "crisis_active",
        "agent": "Sentinel",
        "arousal": 0.95,
        "reason": reason,
        "timestamp": datetime.now().isoformat(),
    })


# ── Conflict Resolution ────────────────────────────────────────────────────


@ebdi_bp.route("/conflict/resolve", methods=["POST"])
@require_api_key
def conflict_resolve():
    """Conflict Resolver (CR) [6]: Weighted voting on agent disagreements."""
    body = request.get_json(silent=True) or {}
    proposals = body.get("proposals", [])

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
        task_id="system", agent="Master", status="resolved",
        action="conflict_resolution", guards_passed=9,
        notes=f"Winner: {winner['agent']} with {winner['weighted_score']:.2f} weighted score",
        db=db, use_db=USE_DATABASE,
    )

    return jsonify({
        "status": "resolved",
        "decision": winner["proposal"],
        "winner": winner["agent"],
        "votes": votes,
        "timestamp": datetime.now().isoformat(),
    })
