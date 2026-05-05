"""
UAP Backend Blueprint Utilities — Shared helpers for all blueprints
"""
import hmac
import json
import logging
import os
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from flask import request

logger = logging.getLogger("adrion.uap.blueprints")

# Shared data stores (will migrate to PostgreSQL in Phase 2)
TASKS_STORE: Dict[str, Dict[str, Any]] = {}
GENESIS_LOGS: List[Dict[str, Any]] = []
CHECKPOINTS_STORE: Dict[str, Dict[str, Any]] = {}

AGENT_TRUST_SCORES: Dict[str, float] = {
    "Librarian": 0.85,
    "SAP": 0.90,
    "Auditor": 0.88,
    "Sentinel": 0.92,
    "Architect": 0.87,
    "Healer": 0.83,
    "Amplifier": 0.80,
    "BoosterLever": 0.78,
    "Chronos": 0.82,
}

EBDI_TELEMETRY: Dict[str, Dict[str, float]] = {
    agent: {"pleasure": 0.5, "arousal": 0.3, "dominance": 0.6}
    for agent in AGENT_TRUST_SCORES.keys()
}

GUARDIAN_LAWS_STATUS: List[Dict[str, Any]] = [
    {"law": "G1", "name": "Unity", "status": "pass"},
    {"law": "G2", "name": "Harmony", "status": "pass"},
    {"law": "G3", "name": "Rhythm", "status": "pass"},
    {"law": "G4", "name": "Causality", "status": "pass"},
    {"law": "G5", "name": "Transparency", "status": "pass"},
    {"law": "G6", "name": "Authenticity", "status": "pass"},
    {"law": "G7", "name": "Privacy", "status": "pass"},
    {"law": "G8", "name": "Nonmaleficence", "status": "pass"},
    {"law": "G9", "name": "Sustainability", "status": "pass"},
]

# Security: Agent column allowlist for UPDATE operations (P0-1: SQL injection prevention)
ALLOWED_AGENT_COLUMNS = frozenset({
    "name", "role", "personality", "description", "trust_score",
    "capability_level", "skills", "active"
})


# ── Shared Utilities ─────────────────────────────────────────────────────────


def get_api_key() -> str:
    """Retrieve configured API key (may be empty for development)."""
    return os.getenv("UAP_API_KEY", "")


def validate_api_key() -> bool:
    """Check API key from X-API-Key header. Returns False when key is unset.

    SECURITY: Uses constant-time comparison (hmac.compare_digest) to prevent timing attacks.
    """
    api_key = get_api_key()
    if not api_key:
        return False

    key = request.headers.get("X-API-Key", "")
    return hmac.compare_digest(key, api_key)


def require_api_key(f):
    """Decorator: Require valid API key on route.

    Usage:
        @app.route("/mapi/v1/tasks", methods=["GET"])
        @require_api_key
        def list_tasks():
            return jsonify({"tasks": []})
    """
    from functools import wraps
    from flask import jsonify

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not validate_api_key():
            return jsonify({"error": "Unauthorized: Invalid or missing X-API-Key header"}), 401
        return f(*args, **kwargs)

    return decorated_function


def generate_task_id() -> str:
    """Generate unique task ID: upc-YYYYMMDD-HHMMSS-XXXX"""
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d-%H%M%S")
    random_suffix = os.urandom(2).hex().upper()
    return f"upc-{timestamp}-{random_suffix}"


def generate_checkpoint_id() -> str:
    """Generate unique checkpoint ID: ckpt-YYYYMMDD-HHMMSS-XXXX"""
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d-%H%M%S")
    random_suffix = os.urandom(2).hex().upper()
    return f"ckpt-{timestamp}-{random_suffix}"


def keyword_persona_match(task_description: str) -> str:
    """Keyword-based routing heuristic (fallback when LLM is unavailable).

    Uses overlap scoring instead of first-match to avoid misrouting
    (e.g., 'find and fix the error' no longer always routes to SAP).
    Priority order for tie-breaking: Sentinel > Healer > ... > Chronos.
    """
    text = task_description.lower()

    agent_keywords = {
        "Sentinel": ["crisis", "urgent", "error", "security", "threat", "alert", "anomaly"],
        "Healer": ["heal", "fix", "optimize", "repair", "debt", "refactor", "patch"],
        "Auditor": ["analyze", "evaluate", "audit", "verify", "compliance", "check"],
        "Architect": ["design", "architecture", "blueprint", "structure", "plan"],
        "SAP": ["scout", "find", "search", "discover", "locate", "scan"],
        "Librarian": ["history", "document", "archive", "record", "retrieve", "knowledge"],
        "Amplifier": ["amplify", "boost", "scale", "expand", "grow", "promote"],
        "BoosterLever": ["leverage", "accelerate", "multiply", "enhance", "turbo"],
        "Chronos": ["schedule", "time", "deadline", "calendar", "recurring"],
    }

    scores = {
        agent: sum(1 for kw in kws if kw in text)
        for agent, kws in agent_keywords.items()
    }

    # Priority order for tie-breaking (highest priority first)
    priority_order = [
        "Sentinel", "Healer", "Auditor", "Architect", "SAP",
        "Librarian", "Amplifier", "BoosterLever", "Chronos",
    ]

    best_agent = max(priority_order, key=lambda a: scores.get(a, 0))
    if scores.get(best_agent, 0) == 0:
        return "SAP"  # Default fallback
    return best_agent


def find_best_persona(task_description: str, agent_hint: Optional[str] = None) -> str:
    """Route task to best persona using LLM with keyword fallback.

    Priority:
    1. If agent_hint is valid and in AGENT_TRUST_SCORES, use it
    2. If LLM available, use LLM to select best persona
    3. Fall back to keyword matching

    Args:
        task_description: Task to route
        agent_hint: Optional preferred agent name

    Returns:
        Agent name from AGENT_TRUST_SCORES
    """
    # Check for explicit hint
    if agent_hint and agent_hint in AGENT_TRUST_SCORES:
        return agent_hint

    # Try LLM routing (optional)
    try:
        from arbitrage.llm import chat as llm_chat

        llm_available = True  # Gracefully set to False if import fails
    except ImportError:
        llm_available = False

    if not llm_available:
        return keyword_persona_match(task_description)

    try:
        agents = list(AGENT_TRUST_SCORES.keys())
        prompt = (
            f"Task: '{task_description}'. Choose the best agent: {agents}. "
            "Reply with the agent name only, nothing else."
        )
        result = llm_chat(prompt, system="You are a task router for the ADRION 369 system.")
        agent = result.strip().strip('"').strip("'")
        if agent in AGENT_TRUST_SCORES:
            return agent
        logger.warning("LLM returned unknown agent '%s', falling back to keyword match", agent)
    except Exception as exc:
        logger.warning("LLM routing failed: %s, falling back to keyword match", exc)

    return keyword_persona_match(task_description)


def check_trust_score(agent: str) -> bool:
    """TSPA [1]: Block agent if TS < 0.6

    All agents must have trust_score >= 0.6 to execute tasks.
    """
    ts = AGENT_TRUST_SCORES.get(agent, 0)
    return ts >= 0.6


def validate_task_description(task_description: str) -> bool:
    """DSV [7]: Validate Input→Output signature.

    Task descriptions must:
    - Exist
    - Have at least 5 characters
    """
    if not task_description or len(task_description.strip()) < 5:
        return False
    return True


def log_genesis_record(
    task_id: str,
    agent: str,
    status: str,
    action: str,
    guards_passed: int = 9,
    notes: str = "",
    db=None,
    use_db: bool = False,
):
    """Log action to Genesis Record for audit trail.

    Attempts database insert with in-memory fallback.

    Args:
        task_id: Unique task identifier
        agent: Agent name that executed
        status: Task status (submitted, executing, completed, failed)
        action: Action taken (task_delegation, execution_success, etc.)
        guards_passed: Number of Guardian Laws passed (0-9)
        notes: Optional notes for context
        db: Database connection (if available)
        use_db: Whether to use database
    """
    if use_db and db:
        try:
            db.insert_genesis_log(task_id, agent, status, action, guards_passed, notes)
        except Exception as e:
            logger.error(f"Failed to insert genesis log to DB: {e}. Using in-memory fallback.")
            GENESIS_LOGS.append({
                "timestamp": datetime.now().isoformat(),
                "task_id": task_id,
                "agent": agent,
                "status": status,
                "action": action,
                "guards_passed": guards_passed,
                "notes": notes,
            })
    else:
        # Fallback to in-memory
        GENESIS_LOGS.append({
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            "agent": agent,
            "status": status,
            "action": action,
            "guards_passed": guards_passed,
            "notes": notes,
        })

    logger.info("event=genesis_log task_id=%s agent=%s action=%s", task_id, agent, action)
