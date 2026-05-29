"""Global State Register (GSR) — ADRION 369.

Central state tracking module for all 9 agent personas.
Thread-safe, persistence-capable, heartbeat-aware.

Usage:
    from gsr import GlobalStateRegister, DEFAULT_STATE_PATH

    gsr = GlobalStateRegister()
    gsr.update_agent_status("MPG-01", "active", 85, "Generating prompts")
    state = gsr.get_all_agents()
    gsr.dump_state("/path/to/PROJECT_STATE.json")

Canonical agent ID format: "{NAME}-{zero-padded-id}", e.g. "MPG-01", "RIA-09".
These are derived from AGENTS_REGISTRY in shared.py.

Logging:
    GSR emits structured JSON logs when python-json-logger is installed.
    Falls back to standard logging otherwise.
"""

from __future__ import annotations

import copy
import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import sys

_MCP_DIR = Path(__file__).parent
if str(_MCP_DIR) not in sys.path:
    sys.path.insert(0, str(_MCP_DIR))

from shared import AGENTS_REGISTRY, utc_now  # noqa: E402

# ---------------------------------------------------------------------------
# Structured JSON logging (python-json-logger — optional dependency)
# ---------------------------------------------------------------------------
logger = logging.getLogger("adrion.gsr")

try:
    from pythonjsonlogger import jsonlogger  # type: ignore[import-untyped]

    def configure_gsr_logging(level: int = logging.INFO) -> None:
        """Configure JSON-structured log output for GSR events.

        Call once at application startup if python-json-logger is installed.
        """
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(
                jsonlogger.JsonFormatter(
                    "%(asctime)s %(name)s %(levelname)s %(message)s"
                )
            )
            logger.addHandler(handler)
        logger.setLevel(level)

except ImportError:  # pragma: no cover — dependency optional
    def configure_gsr_logging(level: int = logging.INFO) -> None:  # type: ignore[misc]
        """No-op: python-json-logger not installed; standard logging active."""
        logger.setLevel(level)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
VALID_STATUSES: frozenset[str] = frozenset({"idle", "active", "error"})
DEFAULT_CONFIDENCE: int = 100
GSR_VERSION: str = "3.0"

# Path to the canonical PROJECT_STATE.json at project root
DEFAULT_STATE_PATH: Path = Path(__file__).parent.parent / "PROJECT_STATE.json"

# Build canonical agent IDs: "MPG-01", "PAA-02", ... "RIA-09"
CANONICAL_AGENT_IDS: dict[str, dict[str, Any]] = {
    f"{info['name']}-{agent_id}": info
    for agent_id, info in AGENTS_REGISTRY.items()
}


# ---------------------------------------------------------------------------
# GlobalStateRegister
# ---------------------------------------------------------------------------
class GlobalStateRegister:
    """Thread-safe central state register for all ADRION 369 agent personas.

    Attributes:
        _lock: Reentrant lock protecting _state from concurrent writes.
        _filepath: Optional path for automatic dump/load operations.
        _state: In-memory representation of PROJECT_STATE.json schema.
    """

    def __init__(self, state_filepath: Path | str | None = None) -> None:
        """Initialise GSR with all agents in 'idle' status.

        Args:
            state_filepath: Optional path to PROJECT_STATE.json. If the file
                already exists it is loaded automatically to preserve prior state.
        """
        self._lock = threading.Lock()
        self._filepath: Path | None = (
            Path(state_filepath) if state_filepath is not None else None
        )
        self._state: dict[str, Any] = self._build_default_state()

        if self._filepath and self._filepath.exists():
            try:
                self.load_state(self._filepath)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "GSR: Could not load existing state from %s — using defaults. Error: %s",
                    self._filepath,
                    exc,
                )

    # -- Public API ----------------------------------------------------------

    def update_agent_status(
        self,
        agent_id: str,
        status: str,
        confidence: int,
        task_description: str | None = None,
    ) -> dict[str, Any]:
        """Update a single agent's status in the register.

        Args:
            agent_id: Canonical agent identifier, e.g. "MPG-01".
            status: One of "idle", "active", "error".
            confidence: Integer 0-100 (clamped automatically).
            task_description: Free-text description of the current task.

        Returns:
            Updated agent state dict on success, or an error dict containing
            an "error" key if validation fails.
        """
        if status not in VALID_STATUSES:
            return {
                "error": (
                    f"Invalid status '{status}'. "
                    f"Must be one of: {sorted(VALID_STATUSES)}"
                ),
            }
        confidence_clamped = max(0, min(100, int(confidence)))

        with self._lock:
            if agent_id not in self._state["agents"]:
                logger.warning(
                    "GSR: Registering previously unknown agent '%s'", agent_id
                )
                self._state["agents"][agent_id] = self._default_agent_entry(agent_id)

            agent: dict[str, Any] = self._state["agents"][agent_id]
            agent["status"] = status
            agent["confidence"] = confidence_clamped
            if task_description is not None:
                agent["last_task"] = task_description
            agent["updated_at"] = utc_now()

            self._state["timestamp"] = utc_now()
            self._state["metrics"] = self._compute_metrics()

        logger.info(
            "GSR update: agent=%s status=%s confidence=%d task=%r",
            agent_id,
            status,
            confidence_clamped,
            task_description,
        )
        return copy.deepcopy(agent)

    def get_agent_state(self, agent_id: str) -> dict[str, Any]:
        """Return the current state of a single agent.

        Args:
            agent_id: Canonical agent identifier, e.g. "MPG-01".

        Returns:
            Agent state dict on success, or {"status": "not_found", "agent_id": ...}
            if the agent is not registered.
        """
        with self._lock:
            agent = self._state["agents"].get(agent_id)
            if agent is None:
                return {"status": "not_found", "agent_id": agent_id}
            return copy.deepcopy(agent)

    def get_all_agents(self) -> dict[str, Any]:
        """Return the complete GSR state including all agents and metrics.

        Returns:
            Deep copy of the internal state dict (safe for external mutation).
        """
        with self._lock:
            return copy.deepcopy(self._state)

    def heartbeat_check(self, max_age_seconds: int = 300) -> dict[str, Any]:
        """Identify agents that have not reported within max_age_seconds.

        An agent is considered 'online' if its 'updated_at' timestamp is within
        the specified threshold. Any agent with an invalid or missing timestamp
        is classified as 'offline'.

        Args:
            max_age_seconds: Age threshold in seconds (default: 300 = 5 minutes).

        Returns:
            Dict with keys: 'online' (list), 'offline' (list),
            'stale_threshold_seconds', 'total_agents', 'timestamp'.
        """
        now = datetime.now(timezone.utc)
        online: list[str] = []
        offline: list[str] = []

        with self._lock:
            for agent_id, agent in self._state["agents"].items():
                updated_at_str: str = agent.get("updated_at", "")
                try:
                    updated_at = datetime.fromisoformat(updated_at_str)
                    # Normalise to UTC if the timestamp is naive
                    if updated_at.tzinfo is None:
                        updated_at = updated_at.replace(tzinfo=timezone.utc)
                    age_seconds = (now - updated_at).total_seconds()
                    if age_seconds <= max_age_seconds:
                        online.append(agent_id)
                    else:
                        offline.append(agent_id)
                except (ValueError, TypeError):
                    offline.append(agent_id)

            # Persist heartbeat snapshot in state
            self._state["last_heartbeat"] = {
                "timestamp": now.isoformat(),
                "source": "heartbeat_check",
                "online_agents": sorted(online),
                "offline_agents": sorted(offline),
                "stale_threshold_seconds": max_age_seconds,
            }
            self._state["timestamp"] = now.isoformat()

        logger.info(
            "GSR heartbeat: online=%d offline=%d threshold=%ds",
            len(online),
            len(offline),
            max_age_seconds,
        )
        return {
            "timestamp": now.isoformat(),
            "online": sorted(online),
            "offline": sorted(offline),
            "stale_threshold_seconds": max_age_seconds,
            "total_agents": len(online) + len(offline),
        }

    def dump_state(self, filepath: Path | str | None = None) -> None:
        """Persist the current GSR state to a JSON file (PROJECT_STATE.json).

        Args:
            filepath: Target path. Falls back to the path provided at construction.

        Raises:
            ValueError: If no filepath is available (neither passed nor set at init).
        """
        target = Path(filepath) if filepath is not None else self._filepath
        if target is None:
            raise ValueError(
                "No filepath provided. Pass a path or set one at construction time."
            )

        with self._lock:
            state_snapshot = copy.deepcopy(self._state)

        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as fh:
            json.dump(state_snapshot, fh, indent=2, ensure_ascii=False)

        logger.info("GSR: State dumped to %s", target)

    def load_state(self, filepath: Path | str | None = None) -> None:
        """Load GSR state from a JSON file, merging over current defaults.

        Only known top-level keys ("agents", "metrics", "last_heartbeat",
        "version", "timestamp") are merged; unknown keys are ignored.

        Args:
            filepath: Source path. Falls back to the path provided at construction.

        Raises:
            ValueError: If no filepath is available.
            FileNotFoundError: If the specified file does not exist.
        """
        source = Path(filepath) if filepath is not None else self._filepath
        if source is None:
            raise ValueError(
                "No filepath provided. Pass a path or set one at construction time."
            )

        with open(source, "r", encoding="utf-8") as fh:
            loaded: dict[str, Any] = json.load(fh)

        with self._lock:
            for key in ("agents", "metrics", "last_heartbeat"):
                if key in loaded:
                    self._state[key] = loaded[key]
            self._state["version"] = loaded.get("version", GSR_VERSION)
            self._state["timestamp"] = loaded.get("timestamp", utc_now())

        logger.info("GSR: State loaded from %s", source)

    # -- Internal helpers ----------------------------------------------------

    def _build_default_state(self) -> dict[str, Any]:
        """Construct the initial in-memory state with all 9 agents at 'idle'."""
        now = utc_now()
        agents: dict[str, Any] = {
            agent_id: self._default_agent_entry(agent_id, info)
            for agent_id, info in CANONICAL_AGENT_IDS.items()
        }
        return {
            "timestamp": now,
            "version": GSR_VERSION,
            "agents": agents,
            "metrics": {
                "total_agents": len(agents),
                "active_agents": 0,
                "error_agents": 0,
                "idle_agents": len(agents),
                "last_updated": now,
            },
            "last_heartbeat": {
                "timestamp": now,
                "source": "gsr_init",
                "online_agents": [],
                "offline_agents": sorted(agents.keys()),
                "stale_threshold_seconds": 300,
            },
        }

    @staticmethod
    def _default_agent_entry(
        agent_id: str,
        info: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Build a single agent entry with default values.

        Args:
            agent_id: Canonical ID, e.g. "MPG-01".
            info: Optional AGENTS_REGISTRY info dict for this agent.

        Returns:
            Agent state dict ready for insertion into self._state["agents"].
        """
        name = info["name"] if info else agent_id.split("-")[0]
        domain = info.get("domain", "unknown") if info else "unknown"
        return {
            "id": agent_id,
            "name": name,
            "domain": domain,
            "status": "idle",
            "last_task": None,
            "confidence": DEFAULT_CONFIDENCE,
            "updated_at": utc_now(),
        }

    def _compute_metrics(self) -> dict[str, Any]:
        """Recompute aggregate metrics from current agent states.

        Must be called while holding self._lock.
        """
        counts: dict[str, int] = {"idle": 0, "active": 0, "error": 0}
        for agent in self._state["agents"].values():
            bucket = agent.get("status", "idle")
            counts[bucket] = counts.get(bucket, 0) + 1
        return {
            "total_agents": len(self._state["agents"]),
            "active_agents": counts.get("active", 0),
            "error_agents": counts.get("error", 0),
            "idle_agents": counts.get("idle", 0),
            "last_updated": utc_now(),
        }
