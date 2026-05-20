---
title: "ROPE v3.0 — Handoff Protocol & SYSTEMPAYLOAD v3.0"
version: "3.0"
created: "2026-05-20"
status: "active"
backward_compat: "v2.0"
---

# ROPE v3.0 — Handoff Protocol

> Defines SYSTEMPAYLOAD v3.0, the 33-agent handoff matrix, and the three canonical
> handoff scenarios: success, escalation, and retry. All payloads are backward-
> compatible with v2.0 (new fields are optional with defined defaults).

---

## 1. SYSTEMPAYLOAD v3.0 Specification

### 1.1 Schema Definition

```json
{
  "$schema": "http://json-schema.org/draft-07/schema",
  "$id": "rope/systempayload/v3.0",
  "title": "SYSTEMPAYLOAD v3.0",
  "type": "object",
  "required": [
    "schema_version",
    "trace_id",
    "session_id",
    "task_id",
    "source_agent",
    "target_agent",
    "task",
    "timestamp"
  ],
  "properties": {
    "schema_version": {
      "type": "string",
      "enum": ["2.0", "3.0"],
      "description": "Schema version. New senders MUST emit '3.0'."
    },
    "trace_id": {
      "type": "string",
      "pattern": "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\\.[A-Z]{2,5}-[0-9]{2}\\.[0-9]{13}$",
      "description": "Format: {UUID4}.{AGENT_CODE}.{UNIX_MS}. Example: f4a3b2c1-dead-beef-cafe-123456789012.AIO-01.1716304800123",
      "v3_new": true
    },
    "session_id": {
      "type": "string",
      "format": "uuid",
      "description": "Stable across all hops within a single user session."
    },
    "task_id": {
      "type": "string",
      "description": "Unique identifier for this logical task (stable across retries)."
    },
    "source_agent": {
      "type": "string",
      "description": "Code of the agent sending this payload. Example: 'AIO-01', 'AGT-003'."
    },
    "target_agent": {
      "type": "string",
      "description": "Code of the agent receiving this payload."
    },
    "task": {
      "type": "object",
      "required": ["description", "acceptance_criteria"],
      "properties": {
        "description": {"type": "string"},
        "acceptance_criteria": {
          "type": "array",
          "items": {"type": "string"},
          "minItems": 1
        },
        "priority": {
          "type": "string",
          "enum": ["CRITICAL", "HIGH", "MEDIUM", "LOW"],
          "default": "MEDIUM"
        },
        "scope_files": {
          "type": "array",
          "items": {"type": "string"},
          "description": "File paths in scope. Empty = infer from task description."
        }
      }
    },
    "confidence_level": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100,
      "description": "Source agent confidence in its output (0-100). v3.0 REQUIRED; v2.0 default: 50.",
      "v3_new": true,
      "default": 50
    },
    "context": {
      "type": "object",
      "description": "Arbitrary context dict from source agent (previous outputs, analysis)."
    },
    "guardian_pre_check": {
      "type": "object",
      "properties": {
        "passed": {"type": "boolean"},
        "violations": {
          "type": "array",
          "items": {"type": "string"}
        },
        "laws_checked": {
          "type": "array",
          "items": {
            "type": "string",
            "pattern": "^G[1-9]$"
          }
        }
      },
      "description": "Guardian Laws pre-check result from source agent."
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 UTC timestamp of payload creation."
    },
    "retry_count": {
      "type": "integer",
      "minimum": 0,
      "maximum": 3,
      "default": 0,
      "description": "Number of times this handoff has been retried. ≥3 triggers escalation."
    },
    "hop_count": {
      "type": "integer",
      "minimum": 1,
      "default": 1,
      "description": "Total number of agent hops in this task chain so far.",
      "v3_new": true
    },
    "escalation_path": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Ordered list of agents that have escalated this task. Audit trail.",
      "v3_new": true
    },
    "ebdi_state": {
      "type": "object",
      "properties": {
        "pleasure": {"type": "number", "minimum": -1.0, "maximum": 1.0},
        "arousal": {"type": "number", "minimum": -1.0, "maximum": 1.0},
        "dominance": {"type": "number", "minimum": -1.0, "maximum": 1.0}
      },
      "description": "PAD vector of source agent at time of handoff. Used by ORACLE-MCP for routing.",
      "v3_new": true
    }
  }
}
```

### 1.2 Backward Compatibility with v2.0

| Field            | v2.0       | v3.0          | Migration Rule                                     |
|------------------|------------|---------------|----------------------------------------------------|
| `schema_version` | absent     | required      | v2.0 receivers treat absent as "2.0"               |
| `trace_id`       | absent     | required      | v2.0 receivers ignore unknown fields (safe)        |
| `confidence_level` | absent   | required      | Default = 50 when absent (neutral confidence)      |
| `hop_count`      | absent     | optional v3   | Default = 1 when absent                            |
| `escalation_path`| absent     | optional v3   | Default = [] when absent                           |
| `ebdi_state`     | absent     | optional v3   | Default = neutral PAD (0.0, 0.0, 0.5) when absent  |
| `retry_count`    | present    | present       | No change — fully compatible                       |
| `session_id`     | present    | present       | No change — fully compatible                       |
| `task_id`        | present    | present       | No change — fully compatible                       |
| `source_agent`   | present    | present       | No change — fully compatible                       |
| `target_agent`   | present    | present       | No change — fully compatible                       |
| `task`           | present    | present       | `scope_files` is new optional sub-field            |
| `context`        | present    | present       | No change — fully compatible                       |
| `timestamp`      | present    | present       | No change — fully compatible                       |

**Rule:** A v3.0 sender MUST emit all required v3.0 fields. A v2.0 receiver MUST ignore
unknown fields (standard JSON schema extension rule). No breaking change is introduced.

### 1.3 Trace ID Format

```
{UUID4}.{AGENT_CODE}.{UNIX_MS}

Example:
  f4a3b2c1-dead-beef-cafe-123456789012.AIO-01.1716304800123
  └─ UUID4 ──────────────────────────┘ └──┘  └────────────┘
              random UUID              agent  unix epoch ms

Propagation rule:
  - When source agent creates a NEW task: generate fresh UUID4, use own code, current ms
  - When agent FORWARDS a task (handoff): keep UUID4, replace agent code + ms
  - When agent RETRIES: keep UUID4 + agent code, update ms only
  - trace_id in output.handoff MUST use the NEXT agent's code
```

### 1.4 Confidence Level Semantics

| Range   | Interpretation                  | Routing Consequence                     |
|---------|---------------------------------|-----------------------------------------|
| 90-100  | Very high confidence            | Direct handoff to next agent            |
| 70-89   | Good confidence                 | Direct handoff; target may skip recheck |
| 50-69   | Moderate confidence             | Target agent performs own pre-check     |
| 30-49   | Low confidence                  | OCA-07 notified; may reroute            |
| 0-29    | Very low / uncertain            | Automatic escalation to OCA-07          |

---

## 2. Handoff Matrix (33 × 33)

### 2.1 Legend

- **S** = Standard handoff (direct, expected flow)
- **E** = Escalation handoff (exceptional, triggered by failure/conflict)
- **R** = Retry handoff (same task returned for correction)
- **O** = Optional handoff (may or may not occur depending on task scope)
- **X** = Not applicable (agents do not interact directly)
- **–** = Self-reference (agent does not hand off to itself)

### 2.2 New Agents × New Agents (9 × 9)

The primary interaction surface for ROPE v3.0 new agents.

```
SOURCE →         AIO-01  PAA-02  TDO-03  AUA-04  VTA-05  GRA-06  OCA-07  KSA-08  RIA-09
TARGET ↓
AIO-01             –       R       X       X       R       E       E       X       X
PAA-02             S       –       O       O       X       O       E       X       X
TDO-03             X       X       –       O       S       S       E       X       O
AUA-04             X       O       O       –       S       E       E       X       X
VTA-05             R       X       X       R       –       O       X       O       S
GRA-06             E       E       E       E       O       –       E       X       E
OCA-07             S       S       S       S       S       S       –       S       S
KSA-08             X       X       X       X       O       X       X       –       S
RIA-09             X       X       O       X       X       X       O       X       –
```

**Reading the matrix:** Row = SOURCE agent, Column = TARGET agent.
Example: `AIO-01 → VTA-05` = **R** means AIO-01 returns a corrected implementation
to VTA-05 for re-verification (retry flow).

### 2.3 New Agents × Existing Agents (9 × 24)

Interaction with the existing 24 agents (AGT-001 through AGT-024, unchanged).
Shown as interaction type per group.

| New Agent | AGT-004 Arbiter | AGT-005 Healer | AGT-003 Orchestrator | AGT-006 Synthesizer | ORACLE-MCP | GUARDIAN-MCP | GENESIS-MCP |
|-----------|-----------------|----------------|----------------------|---------------------|------------|--------------|-------------|
| AIO-01    | E               | E              | X                    | X                   | O          | S            | S           |
| PAA-02    | E               | X              | S                    | X                   | S          | S            | S           |
| TDO-03    | X               | X              | X                    | X                   | X          | S            | S           |
| AUA-04    | X               | X              | O                    | X                   | X          | S            | S           |
| VTA-05    | X               | X              | X                    | X                   | X          | S            | S           |
| GRA-06    | E               | X              | X                    | X                   | O          | S            | S           |
| OCA-07    | E               | X              | S                    | X                   | S          | S            | S           |
| KSA-08    | X               | X              | X                    | X                   | X          | X            | S           |
| RIA-09    | X               | X              | X                    | S                   | X          | S            | S           |

Note: All 9 new agents write to GENESIS-MCP (audit log) on every handoff (S).
All 9 new agents call GUARDIAN-MCP for pre-check (S) on every state-changing operation.

### 2.4 Full 33 × 33 Summary (Compact View)

The matrix below compresses all 33 agents into interaction groups for readability.
Full cell-level detail for new agents is in sections 2.2 and 2.3.

```
Group A: AIO-01, PAA-02, TDO-03, AUA-04 (Implementation Cluster)
Group B: VTA-05, GRA-06 (Quality & Governance Cluster)
Group C: OCA-07, KSA-08, RIA-09 (Coordination Cluster)
Group D: AGT-001..006 (Hexagon Cluster — unchanged)
Group E: ORACLE-MCP, GUARDIAN-MCP, GENESIS-MCP, VORTEX-MCP, HEALER-MCP (MCP Layer)
Group F: Remaining AGT-007..024 (Domain-Specific Cluster — BRAKDANYCH: not documented)

Interaction matrix at group level:
         A    B    C    D    E    F
A        S    S    E    E    S    O
B        R    O    E    E    S    O
C        S    S    –    E    S    O
D        O    O    E    –    S    O
E        S    S    S    S    –    S
F        O    O    O    O    S    –
```

Note: Group F (AGT-007 through AGT-024) interactions are marked O (optional) because
their personas are not documented in available sources. BRAKDANYCH applies to their
specific trigger patterns. They interact with new agents through OCA-07 mediation.

---

## 3. Handoff Scenarios

### 3.1 Scenario A — Success Flow

Standard happy-path handoff. An agent completes its work and passes to the next
agent in the pipeline.

```
Sequence:
  [Initiator] → OCA-07 → PAA-02 → AIO-01 → VTA-05 → KSA-08 → RIA-09 → [Release]
                  |         |         |         |         |         |
               routing   design    build    verify    docs    release
               confirm   approve   code     quality   update  gate

SYSTEMPAYLOAD fields at each hop:
  - schema_version: "3.0"
  - retry_count: 0
  - confidence_level: >70 (each agent maintains or raises)
  - hop_count: incremented by 1 per hop
  - guardian_pre_check.passed: true at every hop
```

Example success payload (AIO-01 → VTA-05):

```json
{
  "schema_version": "3.0",
  "trace_id": "f4a3b2c1-dead-beef-cafe-123456789012.VTA-05.1716304800456",
  "session_id": "a1b2c3d4-0000-0000-0000-000000000001",
  "task_id": "TASK-2026-05-20-001",
  "source_agent": "AIO-01",
  "target_agent": "VTA-05",
  "task": {
    "description": "Verify implementation of rate limiting on wholesale_bp.handle_wholesale_scout",
    "acceptance_criteria": [
      "Coverage ≥80% Python",
      "No ruff violations",
      "Rate limit test returns 429 on rapid requests"
    ],
    "priority": "HIGH",
    "scope_files": ["arbitrage/blueprints/wholesale_bp.py", "tests/unit/test_wholesale.py"]
  },
  "confidence_level": 85,
  "context": {
    "aio01_output": {
      "status": "implemented",
      "files_modified": ["arbitrage/blueprints/wholesale_bp.py"],
      "test_stubs_created": ["tests/unit/test_wholesale.py"]
    }
  },
  "guardian_pre_check": {
    "passed": true,
    "violations": [],
    "laws_checked": ["G4", "G8"]
  },
  "timestamp": "2026-05-20T14:30:00Z",
  "retry_count": 0,
  "hop_count": 3,
  "escalation_path": [],
  "ebdi_state": {"pleasure": 0.4, "arousal": 0.1, "dominance": 0.7}
}
```

### 3.2 Scenario B — Escalation Flow

Triggered when: `retry_count >= 3`, CRITICAL Guardian violation, confidence < 30,
or agent cannot resolve conflict autonomously.

```
Escalation triggers → OCA-07 → AGT-004 Arbiter → Human (if Arbiter cannot resolve)

Escalation rules:
  1. Source agent sets status = "blocked" in its output
  2. OCA-07 is automatically notified (30-minute stall timeout OR explicit block)
  3. OCA-07 routes to AGT-004 Arbiter for conflict resolution
  4. AGT-004 Arbiter applies TS-weighted voting (VETO-RULE.md)
  5. If Arbiter cannot resolve in 1 round → escalate to human operator
  6. Human decision is final; recorded in GENESIS-MCP audit log
  7. Pipeline resumes from the escalation point with retry_count = 0
```

Example escalation payload (AIO-01 blocked → OCA-07):

```json
{
  "schema_version": "3.0",
  "trace_id": "f4a3b2c1-dead-beef-cafe-123456789012.OCA-07.1716304900789",
  "session_id": "a1b2c3d4-0000-0000-0000-000000000001",
  "task_id": "TASK-2026-05-20-001",
  "source_agent": "AIO-01",
  "target_agent": "OCA-07",
  "task": {
    "description": "Verify implementation of rate limiting on wholesale_bp.handle_wholesale_scout",
    "acceptance_criteria": ["Coverage ≥80%"],
    "priority": "HIGH",
    "scope_files": ["arbitrage/blueprints/wholesale_bp.py"]
  },
  "confidence_level": 20,
  "context": {
    "block_reason": "Conflicting architecture guidance from PAA-02 and existing code pattern",
    "aio01_output": {"status": "blocked"},
    "paa02_directive": "Use middleware pattern",
    "existing_pattern": "Direct decorator pattern in other blueprints"
  },
  "guardian_pre_check": {
    "passed": true,
    "violations": [],
    "laws_checked": ["G4"]
  },
  "timestamp": "2026-05-20T14:45:00Z",
  "retry_count": 3,
  "hop_count": 5,
  "escalation_path": ["AIO-01", "OCA-07"],
  "ebdi_state": {"pleasure": -0.3, "arousal": 0.6, "dominance": 0.2}
}
```

### 3.3 Scenario C — Retry Flow

Triggered when: an agent's output fails a quality gate (VTA-05 FAIL, GRA-06 BLOCKED,
ruff violations found) and the same agent can self-correct within the retry budget.

```
Retry rules:
  1. Target agent issues verdict = FAIL or clearance = BLOCKED
  2. retry_count < 3 → payload returned to source agent with failure details
  3. Source agent corrects and re-emits with retry_count += 1, fresh UNIX_MS in trace_id
  4. retry_count = 3 → no more retries; escalation to OCA-07 (Scenario B)
  5. On retry: task_id stays the same; trace_id UUID stays the same; only .MS changes
  6. Maximum 3 retry cycles; 4th failure is automatic escalation
```

Example retry payload (VTA-05 FAIL → AIO-01):

```json
{
  "schema_version": "3.0",
  "trace_id": "f4a3b2c1-dead-beef-cafe-123456789012.AIO-01.1716304950000",
  "session_id": "a1b2c3d4-0000-0000-0000-000000000001",
  "task_id": "TASK-2026-05-20-001",
  "source_agent": "VTA-05",
  "target_agent": "AIO-01",
  "task": {
    "description": "Fix rate limiting implementation — coverage at 71%, below 80% threshold",
    "acceptance_criteria": [
      "Coverage ≥80%",
      "Rate limit test returns 429"
    ],
    "priority": "HIGH",
    "scope_files": ["arbitrage/blueprints/wholesale_bp.py", "tests/unit/test_wholesale.py"]
  },
  "confidence_level": 95,
  "context": {
    "vta05_verdict": "FAIL",
    "failure_details": {
      "coverage_python": 71.2,
      "coverage_threshold": 80.0,
      "missing_coverage": ["wholesale_bp.py:lines 45-62 (error path not tested)"]
    }
  },
  "guardian_pre_check": {
    "passed": true,
    "violations": [],
    "laws_checked": ["G5"]
  },
  "timestamp": "2026-05-20T14:50:00Z",
  "retry_count": 1,
  "hop_count": 4,
  "escalation_path": [],
  "ebdi_state": {"pleasure": 0.0, "arousal": 0.2, "dominance": 0.5}
}
```

---

## 4. Transport & Delivery Guarantees

### 4.1 Transport Layer

- **In-process (same service):** Python dict passed directly via function call
- **Cross-service (inter-MCP):** JSON over HTTP POST to target agent endpoint
- **Queue-based (async):** JSON message in task queue (future: Celery/asyncio)

### 4.2 Delivery Rules

| Scenario              | Delivery Mode   | Timeout    | Retry Policy          |
|-----------------------|-----------------|------------|------------------------|
| Intra-pipeline hop    | Synchronous     | 30 minutes | 3x with backoff       |
| MCP server call       | Synchronous     | 45 seconds | Circuit breaker        |
| Genesis log write     | Asynchronous    | 5 seconds  | Fire-and-forget + log  |
| Human escalation      | Manual          | 24 hours   | Alert after 4 hours    |

### 4.3 Pipeline Stall Detection

OCA-07 monitors all active handoffs. If a hop has not progressed within the stall
window (default 30 minutes, configurable via environment `ROPE_STALL_TIMEOUT_MINUTES`),
OCA-07 initiates Scenario B (escalation).

```python
ROPE_STALL_TIMEOUT_MINUTES = int(os.getenv("ROPE_STALL_TIMEOUT_MINUTES", "30"))
```

### 4.4 GENESIS-MCP Audit Log Entry

Every handoff MUST write to GENESIS-MCP regardless of scenario:

```json
{
  "event_type": "handoff",
  "trace_id": "...",
  "source_agent": "AIO-01",
  "target_agent": "VTA-05",
  "scenario": "success | escalation | retry",
  "confidence_level": 85,
  "retry_count": 0,
  "hop_count": 3,
  "timestamp": "2026-05-20T14:30:00Z"
}
```

---

## 5. Guardian Law Pre-Check Protocol

Every agent MUST call `evaluate_guardians()` before emitting a handoff payload
for any state-changing operation.

### 5.1 Minimum Guardian Checks per Agent

| Agent  | Mandatory Laws    | Rationale                                        |
|--------|-------------------|--------------------------------------------------|
| AIO-01 | G4, G8            | Causality (code must be correct), Nonmaleficence |
| PAA-02 | G1, G6            | Unity (architecture coherence), Authenticity     |
| TDO-03 | G3, G9            | Rhythm (continuity), Sustainability (deps health)|
| AUA-04 | G4, G9            | Causality (automation logic), Sustainability     |
| VTA-05 | G5, G4            | Transparency (coverage reporting), Causality     |
| GRA-06 | G7, G8            | Privacy (data exposure), Nonmaleficence (harm)   |
| OCA-07 | G1, G5            | Unity (coherence), Transparency (audit trail)    |
| KSA-08 | G5, G6            | Transparency (docs), Authenticity (accuracy)     |
| RIA-09 | G3, G9            | Rhythm (release cadence), Sustainability         |

### 5.2 CRITICAL Violation Handling

```
If guardian_pre_check.passed = false AND any violation in ["G7", "G8"]:
  → Emit handoff with target_agent = "GRA-06" (mandatory)
  → Set confidence_level = 0
  → Set task.priority = "CRITICAL"
  → Do NOT proceed with original target agent
  → Log to GENESIS-MCP with event_type = "guardian_violation"
```
