---
title: "ROPE v3.0 — Migration Guide (v2.0 → v3.0)"
version: "3.0"
created: "2026-05-20"
status: "active"
---

# ROPE v3.0 — Migration Guide

> Migration from ROPE v2.0 to v3.0. Three-phase rollout.
> Existing agents AGT-001 through AGT-024 are NOT modified — only additive changes.

---

## 1. What Changed: v2.0 → v3.0

### New SYSTEMPAYLOAD Fields

| Field              | v2.0    | v3.0           | Impact                                   |
|--------------------|---------|----------------|------------------------------------------|
| `schema_version`   | absent  | "3.0" required | Receivers must handle both "2.0" and absent |
| `trace_id`         | absent  | required       | Format: UUID.AGENT_CODE.UNIX_MS          |
| `confidence_level` | absent  | required       | Integer 0-100; default 50 when absent    |
| `hop_count`        | absent  | optional       | Default 1 when absent                    |
| `escalation_path`  | absent  | optional       | Default [] when absent                   |
| `ebdi_state`       | absent  | optional       | Default neutral PAD when absent          |
| `task.scope_files` | absent  | optional       | New sub-field; backward safe             |

### New Agents (Additive — No Existing Agent Modified)

| Slot | Code   | Name                               |
|------|--------|------------------------------------|
| 25   | AIO-01 | Autonomous Implementation Operator |
| 26   | PAA-02 | Process Architecture Agent         |
| 27   | TDO-03 | Tooling & Dependency Operator      |
| 28   | AUA-04 | Automation Upgrade Agent           |
| 29   | VTA-05 | Verification & Testing Agent       |
| 30   | GRA-06 | Governance & Risk Agent            |
| 31   | OCA-07 | Orchestration & Clarification Agent|
| 32   | KSA-08 | Knowledge Standardization Agent    |
| 33   | RIA-09 | Rollout & Iteration Agent          |

---

## 2. Backward Compatibility Matrix

### 2.1 Field-Level Compatibility

```
FIELD               v2.0 SENDER → v3.0 RECEIVER   v3.0 SENDER → v2.0 RECEIVER
─────────────────────────────────────────────────────────────────────────────
schema_version      absent → treat as "2.0"         "3.0" → unknown, ignore
trace_id            absent → generate at receiver   present → unknown, ignore
confidence_level    absent → default to 50          present → unknown, ignore
hop_count           absent → default to 1           present → unknown, ignore
escalation_path     absent → default to []          present → unknown, ignore
ebdi_state          absent → default neutral PAD    present → unknown, ignore
task.scope_files    absent → infer from description  present → unknown, ignore
─────────────────────────────────────────────────────────────────────────────
```

**Rule:** JSON receivers MUST ignore unknown fields (standard JSON extension rule).
No v2.0 agent is broken by v3.0 senders. No v3.0 agent is broken by v2.0 senders.

### 2.2 Behavior Compatibility

| Scenario                                   | v2.0 Agent | v3.0 Agent | Compatible? |
|--------------------------------------------|------------|------------|-------------|
| Receive payload without trace_id           | Normal     | Generate trace_id at entry point | YES |
| Receive payload without confidence_level   | Normal     | Treat as 50 (neutral) | YES |
| Receive payload without schema_version     | Normal     | Treat as v2.0 | YES |
| Emit payload without new v3.0 fields       | v2.0 normal | v3.0 receiver uses defaults | YES |
| Trigger OCA-07 for routing                 | v2.0 cannot trigger directly | v3.0 can route through OCA-07 | ADDITIVE |

### 2.3 Guardian Law Compatibility

Guardian Laws (G1-G9) are unchanged. The 9 new agents use the same evaluation
function: `evaluate_guardians()` from `arbitrage/guardian.py`. No law names, severities,
or veto rules changed. Canonical source remains `docs/GUARDIAN_LAWS_CANONICAL.json`.

---

## 3. Rollout Strategy

### Phase 1: Foundation (Weeks 1-2) — Deploy Infrastructure

**Goal:** Deploy v3.0 payload schema without activating new agents.
**Risk:** LOW — purely additive; no existing agent modified.

```
Actions:
  1. Deploy updated GENESIS-MCP to accept new v3.0 fields (ignore gracefully if absent)
  2. Deploy updated GUARDIAN-MCP to log trace_id (if present) in audit entries
  3. Deploy ORACLE-MCP update: use confidence_level for routing (default 50 if absent)
  4. No changes to any AGT-001..024 behavior
  5. Deploy OCA-07 in passive monitoring mode (stall detection only, no active routing)

Verification:
  - All existing v2.0 agent tests pass unchanged
  - GENESIS-MCP accepts both v2.0 and v3.0 payloads
  - OCA-07 stall detection fires correctly for test scenarios
```

### Phase 2: New Agent Activation (Weeks 3-4) — Activate 9 New Agents

**Goal:** Activate AIO-01 through RIA-09 for new task flows.
**Risk:** MEDIUM — new agents handle new task types; no changes to existing flows.

```
Actions:
  1. Activate AIO-01: handle `status = implementation-ready` tasks
  2. Activate PAA-02: handle `architecture-design` trigger class tasks
  3. Activate TDO-03: handle `dependency-change` trigger class tasks
  4. Activate AUA-04: handle `manual-process-detected` trigger class tasks
  5. Activate VTA-05: replace manual test execution with automated agent
  6. Activate GRA-06: handle `compliance-evaluation` trigger class tasks
  7. Activate OCA-07 in active routing mode
  8. Activate KSA-08: handle `doc-gap-detected` trigger class tasks
  9. Activate RIA-09: handle `release-preparation` trigger class tasks

Dependency order:
  OCA-07 → (all others)   [OCA-07 must be active before routing can begin]
  GRA-06 → AIO-01          [GRA-06 clearance required before AIO-01 executes]
  PAA-02 → AIO-01          [PAA-02 approval required before AIO-01 executes]
  AIO-01 → VTA-05          [VTA-05 receives from AIO-01]
  VTA-05 → KSA-08 → RIA-09 [release chain]

Verification:
  - Run `tests/integration/test_rope_v3_pipeline.py`
  - Confirm trace_id propagates through a full: OCA-07 → PAA-02 → AIO-01 → VTA-05 → KSA-08 → RIA-09 chain
  - Confirm retry and escalation scenarios work (tests/test_trace_propagation.py)
```

### Phase 3: Full Integration (Weeks 5-6) — Connect to Existing Agents

**Goal:** New agents interoperate with AGT-001..024 via OCA-07 mediation.
**Risk:** LOW — OCA-07 mediates all cross-cluster interactions.

```
Actions:
  1. Connect AGT-004 Arbiter to OCA-07 escalation path
  2. Connect AGT-005 Healer to GRA-06 (Healer notified on BLOCKED clearances)
  3. Connect AGT-003 Orchestrator to PAA-02 (share architecture decisions)
  4. Connect ORACLE-MCP to OCA-07 routing decisions (route via 162D space)
  5. Connect GENESIS-MCP to all 9 new agents (audit log — already done in Phase 1)

Verification:
  - Full end-to-end test: user request → OCA-07 → PAA-02 → AIO-01 → VTA-05 → KSA-08 → RIA-09 → Release
  - Conflict test: PAA-02 REJECT + AIO-01 implemented → OCA-07 detects → AGT-004 Arbiter
  - Stall test: artificial 31-minute stall → OCA-07 fires escalation
  - Guardian Law violation test: G7 violation → GRA-06 BLOCKED → pipeline halted
```

---

## 4. Configuration Changes Required

### 4.1 Environment Variables (New in v3.0)

```bash
# Pipeline stall detection (OCA-07)
ROPE_STALL_TIMEOUT_MINUTES=30      # Default: 30 minutes

# Confidence level routing thresholds (ORACLE-MCP)
ROPE_CONFIDENCE_LOW_THRESHOLD=30   # Below this → OCA-07 involvement
ROPE_CONFIDENCE_MIN_AIO=70         # AIO-01 requires source confidence >= 70

# Automation safety limits (AUA-04)
AUTOMATION_MAX_ITERATIONS=1000     # Runaway loop guard

# Trace ID generation
ROPE_TRACE_ID_INCLUDE_MS=true      # Always true in v3.0
```

### 4.2 Database Schema (GENESIS-MCP)

Add columns to `decision_logs` table (nullable for backward compatibility):

```sql
-- Migration: add v3.0 fields to GENESIS-MCP decision log
ALTER TABLE decision_logs ADD COLUMN trace_id VARCHAR(80);
ALTER TABLE decision_logs ADD COLUMN confidence_level INTEGER DEFAULT 50;
ALTER TABLE decision_logs ADD COLUMN hop_count INTEGER DEFAULT 1;
ALTER TABLE decision_logs ADD COLUMN escalation_path JSONB DEFAULT '[]';
ALTER TABLE decision_logs ADD COLUMN ebdi_pleasure FLOAT DEFAULT 0.0;
ALTER TABLE decision_logs ADD COLUMN ebdi_arousal FLOAT DEFAULT 0.0;
ALTER TABLE decision_logs ADD COLUMN ebdi_dominance FLOAT DEFAULT 0.5;

-- Index for trace_id lookups
CREATE INDEX idx_decision_logs_trace_id ON decision_logs (trace_id)
  WHERE trace_id IS NOT NULL;
```

### 4.3 MCP Server Updates

| MCP Server   | v3.0 Update Required | Description                             |
|--------------|---------------------|-----------------------------------------|
| ORACLE-MCP   | YES                 | Accept confidence_level for routing     |
| GUARDIAN-MCP | YES                 | Log trace_id in audit entries           |
| GENESIS-MCP  | YES                 | Accept + store new v3.0 fields          |
| VORTEX-MCP   | NO                  | No changes required                     |
| HEALER-MCP   | NO                  | No changes required                     |

---

## 5. Testing Requirements for Migration

### 5.1 Pre-Migration Tests (must pass before Phase 1)

```bash
# All existing tests must continue to pass
python -m pytest tests/ -q --cov=arbitrage --cov-fail-under=80
python -m pytest uap/tests/ -q
go test ./... -v
```

### 5.2 v3.0-Specific Tests

```bash
# Trace propagation (see tests/test_trace_propagation.py)
python -m pytest tests/test_trace_propagation.py -v

# SYSTEMPAYLOAD schema validation
python -m pytest tests/test_systempayload_schema.py -v

# New agent unit tests
python -m pytest tests/unit/test_rope_agents/ -v

# Integration: full pipeline
python -m pytest tests/integration/test_rope_v3_pipeline.py -v
```

### 5.3 Rollback Criteria

If any of the following are observed after Phase 2 activation, roll back to v2.0 mode:
- Existing agent (AGT-001..024) test failure rate > 0%
- GENESIS-MCP audit log write failure rate > 0.1%
- OCA-07 stall detection false positive rate > 5%
- Handoff success rate drops below 95% (baseline: measured in Phase 1)

Rollback procedure:
```bash
# Deactivate new agents (do not delete)
export ROPE_V3_AGENTS_ACTIVE=false

# Revert GENESIS-MCP to v2.0 payload acceptance only
export GENESIS_SCHEMA_VERSION=2.0

# All AGT-001..024 agents continue unchanged
# No data migration needed (new columns are nullable)
```

---

## 6. Dependencies Between Tasks (CLAUDE.md Reference)

| ROPE v3.0 Task     | Depends On                    | Dependency Type |
|--------------------|-------------------------------|-----------------|
| Phase 1 deployment | GENESIS-MCP available         | HARD            |
| OCA-07 activation  | ORACLE-MCP updated            | HARD            |
| GRA-06 activation  | bandit + safety installed     | HARD            |
| AIO-01 activation  | PAA-02 + GRA-06 active        | HARD            |
| VTA-05 activation  | pytest 7.4+ installed         | HARD            |
| RIA-09 activation  | VTA-05 + GRA-06 + KSA-08 active | HARD          |
| Full integration   | All 9 agents active           | HARD            |
| KROK 1 MCP Router  | Phase 1 complete              | SOFT (parallel) |

---

## 7. Known Limitations (BRAKDANYCH)

The following items are marked BRAKDANYCH — data not available in current sources:

- **AGT-007 through AGT-024 specific trigger patterns:** Not documented in available files.
  These agents are referenced as "Group F" in the handoff matrix with interaction type O
  (optional, mediated through OCA-07). Exact handoff rules require future documentation.

- **ROPE v2.0 exact SYSTEMPAYLOAD schema:** v2.0 fields were inferred from context
  (PERSONA-MAPPING.md, WORKFLOW.md, MCP_ARCHITECTURE.md). A formal v2.0 schema document
  was not found. The compatibility rules in Section 2 are based on standard JSON extension
  principles and may need refinement once v2.0 schema is located.

- **Trust Score per Agent (TSPA) integration with new agents:** TSPA (from MCP_ARCHITECTURE.md)
  is documented for the existing 6 Hexagon agents. How TSPA applies to AIO-01..RIA-09
  requires a separate ADR (BRAKDANYCH: no specification found).
