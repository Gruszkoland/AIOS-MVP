from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


STATUS_SCORE = {
    "active": 0.85,
    "idle": 0.55,
    "error": 0.20,
}


def _parse_timestamp(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    dt = datetime.fromisoformat(normalized)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def freshness_score(updated_at: str, now: datetime, stale_after_hours: int = 48) -> float:
    updated = _parse_timestamp(updated_at)
    age_seconds = max((now - updated).total_seconds(), 0.0)
    stale_window_seconds = max(stale_after_hours, 1) * 3600
    ratio = min(age_seconds / stale_window_seconds, 1.0)
    return max(0.0, 1.0 - ratio)


def status_score(status: str) -> float:
    return STATUS_SCORE.get(status.lower().strip(), 0.40)


def task_activity_score(last_task: Any) -> float:
    if last_task is None:
        return 0.10
    if isinstance(last_task, str) and last_task.strip():
        return 1.00
    return 0.20


def compute_confidence(status: str, updated_at: str, last_task: Any, now: datetime) -> int:
    score = (
        0.50 * status_score(status)
        + 0.35 * freshness_score(updated_at, now)
        + 0.15 * task_activity_score(last_task)
    )
    return int(round(max(0.0, min(1.0, score)) * 100))


def update_project_state_confidence(state: dict[str, Any], now: datetime | None = None) -> dict[str, Any]:
    current_time = now or datetime.now(timezone.utc)
    agents = state.get("agents", {})

    active_agents = 0
    error_agents = 0
    idle_agents = 0

    for _, agent in agents.items():
        status = str(agent.get("status", "idle"))
        updated_at = str(agent.get("updated_at", state.get("timestamp", current_time.isoformat())))
        last_task = agent.get("last_task")

        agent["confidence"] = compute_confidence(status, updated_at, last_task, current_time)

        if status == "active":
            active_agents += 1
        elif status == "error":
            error_agents += 1
        else:
            idle_agents += 1

    metrics = state.setdefault("metrics", {})
    metrics["active_agents"] = active_agents
    metrics["error_agents"] = error_agents
    metrics["idle_agents"] = idle_agents
    metrics["total_agents"] = len(agents)
    metrics["last_updated"] = current_time.isoformat()

    state["timestamp"] = current_time.isoformat()
    return state
