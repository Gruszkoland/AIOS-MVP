# GENESIS-MCP: Event Sourcing API Documentation

**Status:** ✅ INTEGRATED
**Guardian Law:** G5 (Transparency) - Complete immutable audit trail
**Pattern:** CQRS (Command Query Responsibility Segregation)
**Storage:** `Genesis Record/event_log.jsonl` (append-only JSONL)

---

## Overview

Event Sourcing in GENESIS-MCP provides:

- **Immutable Event Log**: All agent actions logged permanently
- **Materialized Views**: Fast queries via pre-computed state
- **Complete Audit Trail**: Full transparency for compliance (G5)
- **Replay Capability**: Reconstruct any state at point-in-time
- **CQRS Pattern**: Separate command (write) and query (read) paths

---

## Architecture

```
COMMAND SIDE (Write)              QUERY SIDE (Read)
┌─────────────────────┐          ┌──────────────────────┐
│ POST /event/record  │          │ GET /event/state     │ (fast)
│ Record new event    │          │ Query materialized   │
└──────────┬──────────┘          │ view (pre-computed)  │
           │                     └──────────────────────┘
           ↓
    Event Log (immutable)         Materialized View (cache)
       JSONL File                   In-memory dictionary
   Append-only, source              Re-buildable from log
   of truth                         Update on each event
```

---

## Endpoints

### 1. Record Event (COMMAND Side)

**POST** `/event/record`

Records a new event in the immutable event log.

**Request:**

```json
{
  "event_type": "TASK_COMPLETED",
  "entity_id": "agent_sentinel",
  "data": {
    "task_id": "T123",
    "status": "success",
    "priority": 8
  }
}
```

**Response (201 Created):**

```json
{
  "success": true,
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-04-07T21:45:30.123456",
  "entity_id": "agent_sentinel"
}
```

**Common Event Types:**

- `AGENT_INITIALIZED` - Agent startup
- `TASK_DISPATCHED` - Task assigned to agent
- `TASK_STARTED` - Agent began processing
- `TASK_COMPLETED` - Agent finished successfully
- `TASK_FAILED` - Agent encountered error
- `DECISION_STARTED` - Decision-making began
- `DECISION_EVALUATED` - Options evaluated
- `DECISION_EXECUTED` - Action taken
- `TRUST_UPDATED` - TS adjustment
- `HTTP_REQUEST` - API call (auto-logged)

---

### 2. Get Entity History (Query Side - Full Audit Trail)

**GET** `/event/history/<entity_id>`

Retrieve complete event history for an entity (all events that affected this entity).

**Example:**

```bash
GET /event/history/agent_sentinel
```

**Response (200 OK):**

```json
{
  "success": true,
  "entity_id": "agent_sentinel",
  "event_count": 42,
  "events": [
    {
      "event_id": "550e8400-e29b-41d4-a716-446655440000",
      "event_type": "AGENT_INITIALIZED",
      "entity_id": "agent_sentinel",
      "timestamp": "2026-04-07T20:00:00.000000",
      "data": {"ts": 0.5}
    },
    {
      "event_id": "550e8400-e29b-41d4-a716-446655440001",
      "event_type": "TASK_COMPLETED",
      "entity_id": "agent_sentinel",
      "timestamp": "2026-04-07T20:15:30.000000",
      "data": {"task_id": "T001"}
    },
    ...
  ]
}
```

**Use Cases:**

- ✅ Compliance audits (show all agent actions)
- ✅ Debugging (trace decision sequence)
- ✅ Performance analysis (identify bottlenecks)
- ✅ Legal discovery (full transaction history)

---

### 3. Get Entity State (Query Side - Materialized View)

**GET** `/event/state/<entity_id>`

Get **current state** of entity from materialized view (very fast, pre-computed).

**Example:**

```bash
GET /event/state/agent_sentinel
```

**Response (200 OK):**

```json
{
  "success": true,
  "entity_id": "agent_sentinel",
  "state": {
    "id": "agent_sentinel",
    "ts": 0.85,
    "tasks_completed": 15,
    "tasks_failed": 3,
    "last_event": "TASK_COMPLETED",
    "created_at": "2026-04-07T20:00:00.000000",
    "updated_at": "2026-04-07T21:45:30.000000"
  }
}
```

**Performance:**

- ⚡ **O(1) lookup** (hash dict access)
- 📊 **1-5ms response time** vs /history (50-200ms)
- 💾 **Pre-computed** − no event replay needed

**Use Cases:**

- ✅ Dashboards (quick status check)
- ✅ Health monitoring (TS tracking)
- ✅ Load balancing (find available agents)
- ✅ Real-time decision making

---

### 4. Replay Entity (Verification)

**GET** `/event/replay/<entity_id>`

Replay all events to **verify state reconstruction**.

Useful for:

- Debugging state calculations
- Compliance verification (confirm calculations)
- Point-in-time recovery simulation

**Example:**

```bash
GET /event/replay/agent_auditor
```

**Response (200 OK):**

```json
{
  "success": true,
  "entity_id": "agent_auditor",
  "event_count": 28,
  "replay": {
    "entity_id": "agent_auditor",
    "history": [
      {
        "event_id": "...",
        "event_type": "AGENT_INITIALIZED",
        "timestamp": "...",
        "data": {...}
      },
      ...
    ]
  }
}
```

**Validation:**

```python
# In your code:
# Verify that replayed state == materialized view state
replayed = GET /event/replay/agent_id
current = GET /event/state/agent_id

if replayed_state != current_state:
    alert("State reconstruction mismatch!")  # Guardian Law G8 violation
```

---

### 5. Get Global Audit Trail

**GET** `/event/audit[?event_type=TYPE&limit=N]`

Retrieve global audit trail (all events, optionally filtered).

**Examples:**

```bash
# All events (last 100)
GET /event/audit

# Filter by event type
GET /event/audit?event_type=TASK_COMPLETED&limit=50

# All failures
GET /event/audit?event_type=TASK_FAILED&limit=1000
```

**Response (200 OK):**

```json
{
  "success": true,
  "event_count": 42,
  "limit": 100,
  "events": [
    {
      "event_id": "...",
      "event_type": "TASK_COMPLETED",
      "entity_id": "agent_1",
      "timestamp": "...",
      "data": {...}
    },
    ...
  ]
}
```

**Query Parameters:**

- `event_type` (optional): Filter by event type
- `limit` (optional, default=100): Max events to return

**Performance Note:**

- First query may be slower (~500ms)
- Results cached in memory for 5 minutes
- New events invalidate cache

---

### 6. Get Event Statistics

**GET** `/event/statistics`

Get event log statistics (monitoring/ops dashboard).

**Response (200 OK):**

```json
{
  "success": true,
  "statistics": {
    "total_events": 1247,
    "total_entities": 12,
    "view_version": 89,
    "log_file": "/path/to/Genesis Record/event_log.jsonl"
  }
}
```

**Fields:**

- `total_events`: Cumulative events recorded
- `total_entities`: Unique agents/processes tracked
- `view_version`: Version of materialized views (increments per update)
- `log_file`: Full path to JSONL event log

**Useful for:**

- Monitoring storage growth
- Health checks (0 total_events = issue)
- Tracking system scale

---

## Guardian Law Compliance

### G5 (Transparency)

✅ **Fully Implemented via Event Sourcing:**

```python
# Every agent action is logged
POST /event/record
{
  "event_type": "DECISION_EXECUTED",
  "entity_id": "agent_1",
  "data": {
    "decision": "approve_task",
    "reasoning": "confidence > 0.8",
    "impact": "high_priority_task_dispatched"
  }
}

# Full audit trail is retrievable
GET /event/history/agent_1
# → shows complete decision sequence with timestamps & data
```

**Verification:**

```bash
# Compliance check: Verify all decisions are logged
curl http://localhost:9004/event/history/agent_1 \
  | jq '.events | map(.event_type)' \
  | grep -c DECISION_EXECUTED

# Result should be > 0 (decisions are logged)
```

---

### G8 (Nonmaleficence - No Unintended Side Effects)

✅ **Enabled via Replay Capability:**

```python
# Detect unintended consequences
replay_state = GET /event/replay/agent_1
current_state = GET /event/state/agent_1

if replay_state["ts"] != current_state["ts"]:
    # State mismatch! Unintended side effect
    alert("INTEGRITY VIOLATION", level="CRITICAL")
```

---

## Usage Examples

### Example 1: Track Agent Lifecycle

```python
import requests

BASE = "http://localhost:9004"

# Agent starts
requests.post(f"{BASE}/event/record", json={
    "event_type": "AGENT_INITIALIZED",
    "entity_id": "agent_sap",
    "data": {"trust_score": 0.5}
})

# Agent works
for task_id in range(1, 6):
    requests.post(f"{BASE}/event/record", json={
        "event_type": "TASK_COMPLETED",
        "entity_id": "agent_sap",
        "data": {"task_id": f"T{task_id}"}
    })

# Check current state
state = requests.get(f"{BASE}/event/state/agent_sap").json()
print(f"Agent TS: {state['state']['ts']}")  # 0.5 + 5*0.05 = 0.75

# Get full history
history = requests.get(f"{BASE}/event/history/agent_sap").json()
print(f"Events: {history['event_count']}")  # 6 (1 init + 5 tasks)
```

### Example 2: Compliance Audit

```python
# Get all task failures
response = requests.get(
    f"{BASE}/event/audit?event_type=TASK_FAILED&limit=1000"
).json()

failures = response["events"]
print(f"Total failures: {len(failures)}")

# Analyze by agent
from collections import Counter
agents = Counter(e["entity_id"] for e in failures)
print(f"Failures by agent: {dict(agents)}")

# Fail rate per agent
for agent_id, count in agents.items():
    total = requests.get(f"{BASE}/event/history/{agent_id}").json()["event_count"]
    fail_rate = count / total * 100
    print(f"{agent_id}: {fail_rate:.1f}% failure rate")
```

### Example 3: Point-in-Time Recovery Check

```python
# Before making risky change, verify current state
before = requests.get(f"{BASE}/event/state/agent_1").json()["state"]

# Make change...
# change_system()

# Verify state still matches replay
after = requests.get(f"{BASE}/event/replay/agent_1").json()["replay"]
after_state = after  # Extract current state from replay

if before == after_state:
    print("✓ State integrity verified")
else:
    print("✗ INTEGRITY VIOLATION DETECTED")
    # Rollback or alert
```

---

## Performance Tuning

| Operation          | Typical Latency | Notes                            |
| ------------------ | --------------- | -------------------------------- |
| POST /event/record | 5-10ms          | Append to JSONL (sequential I/O) |
| GET /event/state   | 1-5ms           | Hash dict lookup (O(1))          |
| GET /event/history | 50-200ms        | Scan log file (O(N))             |
| GET /event/replay  | 50-200ms        | Reconstruct from events (O(N))   |
| GET /event/audit   | 100-500ms       | Filter + collect all (O(C))      |

**Optimization Tips:**

1. Use `/event/state` for real-time queries (fast)
2. Cache history/replay results (5-minute TTL)
3. Archive event log monthly (production)
4. Consider sharding by entity_id for 100K+ agents

---

## Error Handling

**400 Bad Request**: Missing or invalid fields

```json
{ "success": false, "error": "event_type is required" }
```

**404 Not Found**: Entity has no events

```json
{ "success": false, "error": "Entity not found in log" }
```

**500 Internal Server Error**: File I/O or system issue

```json
{ "success": false, "error": "Failed to write to event log" }
```

---

## Integration Checklist

- ✅ Event Sourcing imported in mcp_genesis_app.py
- ✅ EventSourcingStore initialized at app startup
- ✅ All 6 endpoints implemented
- ✅ Auto-logging middleware added (before_request/after_request)
- ✅ Integration tests created
- ✅ Guardian Law G5 compliance verified
- ⏳ Production deployment (upcoming)

---

## References

- **Event Sourcing Implementation**: [scripts/event_sourcing.py](scripts/event_sourcing.py)
- **Integration Tests**: [tests/integration/test_genesis_event_sourcing.py](tests/integration/test_genesis_event_sourcing.py)
- **MASTER ORCHESTRATOR**: [.github/copilot-instructions.md](.github/copilot-instructions.md#protokół-333)
- **Guardian Laws**: [.github/copilot-instructions.md](.github/copilot-instructions.md#9-guardian-laws)

---

**Document Version:** 1.0
**Status:** ✅ COMPLETE
**Last Updated:** 2026-04-07
