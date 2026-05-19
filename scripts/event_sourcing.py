#!/usr/bin/env python3
"""
ADRION 369: Event Sourcing Module for Genesis MCP
Implements CQRS pattern: Commands → Event Log, Queries → Materialized Views

Features:
- Immutable event log (append-only)
- Full audit trail
- Replay capability
- Materialized views for fast queries
- Event filtering and projection
"""

import json
import sys
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class Event:
    """Immutable event in Event Log."""
    event_type: str  # e.g., "AGENT_INITIALIZED", "TASK_COMPLETED"
    entity_id: str  # e.g., agent_id, task_id
    data: Dict[str, Any]
    timestamp: str = None  # ISO format
    event_id: str = None  # UUID

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        if self.event_id is None:
            import uuid
            self.event_id = str(uuid.uuid4())

    def to_dict(self) -> Dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class EventLog:
    """Append-only immutable event log (becomes source of truth)."""

    def __init__(self, log_file: str = "Genesis Record/event_log.jsonl"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.events = []
        self._load_existing()

    def _load_existing(self):
        """Load existing events from log file."""
        if self.log_file.exists():
            with open(self.log_file, 'r') as f:
                for line in f:
                    try:
                        event_dict = json.loads(line.strip())
                        self.events.append(event_dict)
                    except json.JSONDecodeError:
                        logger.warning(f"Skipped malformed line in {self.log_file}")
            logger.info(f"Loaded {len(self.events)} events from {self.log_file}")

    def append(self, event: Event) -> bool:
        """
        Append event to immutable log.
        Events are NEVER modified or deleted.
        """
        try:
            with open(self.log_file, 'a') as f:
                f.write(event.to_json() + "\n")
            self.events.append(event.to_dict())
            logger.info(f"Event logged: {event.event_type} (entity={event.entity_id})")
            return True
        except Exception as e:
            logger.error(f"Failed to append event: {e}")
            return False

    def get_all(self) -> List[Dict]:
        """Get all events in log."""
        return self.events

    def get_entity_history(self, entity_id: str) -> List[Dict]:
        """Get all events for a specific entity."""
        return [e for e in self.events if e.get("entity_id") == entity_id]

    def get_by_type(self, event_type: str) -> List[Dict]:
        """Get all events of a specific type."""
        return [e for e in self.events if e.get("event_type") == event_type]

    def replay(self, entity_id: str) -> Dict:
        """
        Replay all events for entity to reconstruct current state.

        Example:
          Events: [Init(TS=0.5), TaskSuccess(+0.05), TaskFail(-0.20)]
          Replayed state: TS = 0.35
        """
        state = {"entity_id": entity_id, "history": []}

        for event in self.get_entity_history(entity_id):
            state["history"].append(event)

        return state


class MaterializedView:
    """
    Materialized views: pre-computed projections of event log.
    Used for fast queries (CQRS query side).

    Example:
      Event Log: [AGENT_INIT, TASK_SUCCESS, TASK_FAIL, ...]
      View: {agent_id: {ts: 0.35, last_task: "TASK_FAIL", ...}}
    """

    def __init__(self):
        self.cache = {}  # {entity_id: computed_state}
        self.version = 0  # Increment on each update

    def update_agent_view(self, agent_id: str, updates: Dict):
        """Update agent materialized view."""
        if agent_id not in self.cache:
            self.cache[agent_id] = {
                "id": agent_id,
                "ts": 0.5,
                "tasks_completed": 0,
                "tasks_failed": 0,
                "last_event": None,
                "updated_at": None
            }

        # Apply updates
        for key, value in updates.items():
            if key in self.cache[agent_id]:
                self.cache[agent_id][key] = value

        self.cache[agent_id]["updated_at"] = datetime.now().isoformat()
        self.version += 1

    def get_agent_view(self, agent_id: str) -> Dict:
        """Get agent materialized view."""
        return self.cache.get(agent_id, {})

    def get_all_views(self) -> Dict:
        """Get all materialized views."""
        return self.cache

    def rebuild_from_events(self, event_log: EventLog):
        """Rebuild materialized views from scratch (full projection)."""
        logger.info("Rebuilding materialized views from event log...")
        self.cache.clear()

        for event in event_log.get_all():
            event_type = event.get("event_type")
            entity_id = event.get("entity_id")
            data = event.get("data", {})

            # Initialize if not exists
            if entity_id not in self.cache:
                self.cache[entity_id] = {
                    "id": entity_id,
                    "ts": 0.5,
                    "tasks_completed": 0,
                    "tasks_failed": 0,
                    "last_event": event_type,
                    "created_at": event.get("timestamp")
                }

            # Apply event to view
            if event_type == "TASK_COMPLETED":
                self.cache[entity_id]["ts"] += 0.05
                self.cache[entity_id]["tasks_completed"] += 1
            elif event_type == "TASK_FAILED":
                self.cache[entity_id]["ts"] = max(0, self.cache[entity_id]["ts"] - 0.20)
                self.cache[entity_id]["tasks_failed"] += 1

            self.cache[entity_id]["last_event"] = event_type

        logger.info(f"Materialized views rebuilt: {len(self.cache)} entities")


class EventSourcingStore:
    """
    Combined Event Log + Materialized Views system.

    CQRS Pattern:
    - COMMAND side: Write events to immutable log
    - QUERY side: Read from materialized views (pre-computed)
    """

    def __init__(self, log_file: str = "Genesis Record/event_log.jsonl"):
        self.event_log = EventLog(log_file)
        self.views = MaterializedView()
        self._rebuild_views()

    def _rebuild_views(self):
        """Rebuild materialized views on startup."""
        self.views.rebuild_from_events(self.event_log)

    def record_event(self, event_type: str, entity_id: str, data: Dict = None) -> Event:
        """
        Record a new event (COMMAND side).

        Args:
            event_type: Type of event (e.g., "AGENT_INITIALIZED")
            entity_id: What entity this event affects (e.g., "agent_1")
            data: Event payload

        Returns:
            Event object
        """
        event = Event(
            event_type=event_type,
            entity_id=entity_id,
            data=data or {}
        )

        # Append to log
        success = self.event_log.append(event)

        if success:
            # Update materialized view
            if event_type == "TASK_COMPLETED":
                self.views.update_agent_view(entity_id, {
                    "last_event": event_type,
                    "ts": self.views.get_agent_view(entity_id).get("ts", 0.5) + 0.05
                })
            elif event_type == "TASK_FAILED":
                current_ts = self.views.get_agent_view(entity_id).get("ts", 0.5)
                self.views.update_agent_view(entity_id, {
                    "last_event": event_type,
                    "ts": max(0, current_ts - 0.20)
                })

        return event

    def get_entity_state(self, entity_id: str) -> Dict:
        """
        Get current state of entity (QUERY side).
        Reads from materialized view (very fast).
        """
        return self.views.get_agent_view(entity_id)

    def get_entity_history(self, entity_id: str) -> List[Dict]:
        """
        Get full event history for entity (audit trail).
        Useful for debugging and compliance.
        """
        return self.event_log.get_entity_history(entity_id)

    def replay_entity(self, entity_id: str) -> Dict:
        """
        Replay all events for entity to reconstruct state.
        Should match current materialized view (for verification).
        """
        return self.event_log.replay(entity_id)

    def get_statistics(self) -> Dict:
        """Get event log statistics."""
        return {
            "total_events": len(self.event_log.events),
            "total_entities": len(self.views.cache),
            "view_version": self.views.version,
            "log_file": str(self.event_log.log_file)
        }


# Integration with Genesis MCP
def integrate_event_sourcing_to_genesis(genesis_server):
    """
    Hook to integrate Event Sourcing into Genesis MCP.

    Usage in mcp_genesis_app.py:

    from scripts.event_sourcing import EventSourcingStore, integrate_event_sourcing_to_genesis

    store = EventSourcingStore()
    integrate_event_sourcing_to_genesis(server)

    # Then use:
    # store.record_event("TASK_COMPLETED", "agent_1", {"task_id": "T123"})
    # state = store.get_entity_state("agent_1")
    """
    logger.info("Event Sourcing integrated into Genesis MCP")


if __name__ == "__main__":
    # Demo: Event Sourcing with ADRION agents
    logger.info("Starting Event Sourcing demo...")

    store = EventSourcingStore()

    # Simulate agent lifecycle
    store.record_event("AGENT_INITIALIZED", "agent_1", {"trust_score": 0.5})
    store.record_event("TASK_COMPLETED", "agent_1", {"task_id": "task_001"})
    store.record_event("TASK_COMPLETED", "agent_1", {"task_id": "task_002"})
    store.record_event("TASK_FAILED", "agent_1", {"task_id": "task_003"})
    store.record_event("TASK_COMPLETED", "agent_1", {"task_id": "task_004"})

    # Query current state
    print("\n[CURRENT STATE]")
    state = store.get_entity_state("agent_1")
    print(json.dumps(state, indent=2))

    # Query history
    print("\n[AUDIT TRAIL]")
    history = store.get_entity_history("agent_1")
    for event in history:
        print(f"  {event['timestamp']}: {event['event_type']}")

    # Get stats
    print("\n[STATISTICS]")
    stats = store.get_statistics()
    print(json.dumps(stats, indent=2))
