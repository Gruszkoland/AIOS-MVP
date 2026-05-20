---
title: "ROPE 3.0 — Compatibility Matrix"
version: "3.0"
status: "Design"
created: "2026-05-20"
scope: "All 33 ROPE agents, MCP layer, Flask API, Genesis-MCP"
---

# ROPE 3.0 Compatibility Matrix

> Every field is mapped. No white spots.
> "Compatible" = v2.0 caller works with v3.0 agent or vice versa without code change.
> "Degraded" = works but loses a feature silently (logs warning).
> "Breaking" = requires migration before mixing v2.0 and v3.0.

---

## 1. Backward Compatibility Overview

| Component | v2.0 → v3.0 Compatibility | Notes |
|-----------|--------------------------|-------|
| SYSTEM_PAYLOAD schema | Degraded | New fields are additive; v2.0 consumer ignores unknown fields |
| Agent persona files | Degraded | v2.0 file + v3.0 AOR = works, confidence defaults to 0.50 |
| Handoff Protocol | Breaking | v1 handoff has no retry/state machine; must migrate AOR first |
| Router-MCP entry point | Compatible | Adds `trace_id` header generation; backward safe |
| Oracle-MCP routing | Compatible | `confidence_level` mapping is additive |
| Genesis-MCP storage | Compatible | New `trace_id` index is additive; v2.0 logs stay intact |
| Guardian-MCP validation | Compatible | No schema changes to Guardian evaluation |
| Healer-MCP recovery | Compatible | Uses `trace_id` passively; fallback to session_id if absent |
| Flask API (port 8003) | Compatible | `X-Trace-ID` response header added; existing clients ignore it |
| OpenAPI spec | Compatible | New header fields are optional in request, present in response |

---

## 2. Field-Level Compatibility Matrix

### 2.1 SYSTEM_PAYLOAD Fields

| Field | v2.0 | v3.0 | Backward Compatible? | Migration Required? |
|-------|-------|-------|---------------------|---------------------|
| `agent_id` | present | present | Yes — identical | No |
| `agent_number` | present | present | Yes — identical | No |
| `version` | "2.0" | "3.0" | Degraded — v2.0 consumer sees string, no logic on it | No — cosmetic |
| `session_id` | present | present | Yes — identical | No |
| `context` | present | present | Yes — identical | No |
| `trace_id` | absent | present | Degraded — v2.0 consumer ignores the field | No |
| `confidence_level` | absent | present | Degraded — v2.0 consumer ignores the field | No for consumer; Yes for AOR v3.0 |
| `handoff_protocol` | absent | "v2" | Breaking for AOR — AOR v3.0 requires this field to select state machine | Yes — AOR must be migrated first |

### 2.2 HTTP Headers (Flask API port 8003)

| Header | v2.0 | v3.0 | Compatibility |
|--------|-------|-------|---------------|
| `X-Trace-ID` (request) | not accepted | optional | Compatible — v2.0 clients that omit it get one generated |
| `X-Trace-ID` (response) | not emitted | always present | Compatible — v2.0 clients ignore unknown headers |
| `X-ROPE-Version` (response) | not emitted | "3.0" | Compatible — v2.0 clients ignore unknown headers |

### 2.3 Genesis-MCP Decision Log Schema

| Field in log entry | v2.0 | v3.0 | Compatibility |
|--------------------|-------|-------|---------------|
| `session_id` | present | present | Compatible |
| `agent_id` | present | present | Compatible |
| `event_type` | present | present | Compatible |
| `timestamp` | present | present | Compatible |
| `trace_id` | absent | present | Compatible — v2.0 log entries lack field; queries on trace_id return only v3.0 entries |
| `confidence_level` | absent | present | Compatible — same as trace_id |
| `handoff_escalation` event type | absent | present | Additive — v2.0 logs have no such entries; no conflict |

---

## 3. Deprecated Fields

No fields are deprecated in the ROPE 2.0 → 3.0 transition. The version string changes
from "2.0" to "3.0", but the field `version` is not removed.

If future ROPE 4.0 introduces field deprecation, this section will be updated.

---

## 4. Migration Guide (Per Agent Category)

### 4.1 AOR (Agent Orchestrator, #13) — REQUIRED FIRST

**Why critical:** AOR is the handoff executor. If AOR is not migrated, no other agent
benefits from Handoff Protocol v2 or `trace_id` propagation.

Migration steps:
1. Update AOR persona file: change `version: "2.0"` → `"3.0"`, add `handoff_protocol: "v2"`
2. Inject `trace_id` generation logic (if no `trace_id` in incoming SYSTEM_PAYLOAD, generate)
3. Implement state machine (IDLE → REQUESTING → VALIDATING → TRANSFERRING → CONFIRMING)
4. Implement retry logic (max 3, exponential backoff)
5. Add EVA-33 notification hook when `confidence_level < 0.60`
6. Test with S02, S06 from VALIDATION_PLAN.md

**Estimated effort:** L (large — new state machine logic)

### 4.2 EVA (Evaluation & Observability, #33) — REQUIRED SECOND

**Why critical:** EVA-33 reads `confidence_level` and validates ROPE compliance.
Without EVA-33 v3.0, the validation plan cannot execute.

Migration steps:
1. Update EVA persona file: version + new fields
2. Add `confidence_level` reader from incoming SYSTEM_PAYLOAD
3. Add `low_confidence_alert` event writer to Genesis-MCP (when < 0.60)
4. Add ROPE 3.0 validator: checks `trace_id` present, `handoff_protocol` = "v2"
5. Test with S05, S08 from VALIDATION_PLAN.md

**Estimated effort:** M (medium)

### 4.3 ARB (The Arbiter, #07) — REQUIRED THIRD

**Why critical:** ARB is the escalation target for failed handoffs. Must be v3.0 to
receive escalation records that include `trace_id`.

Migration steps:
1. Update ARB persona file: version + new fields
2. Add escalation context reader from Genesis-MCP (by `trace_id`)
3. Test with S04, S06 from VALIDATION_PLAN.md

**Estimated effort:** S (small — mostly config)

### 4.4 All Remaining 30 Agents — CAN MIGRATE IN PARALLEL

After AOR, EVA-33, ARB are migrated, the remaining 30 agents can migrate in any order
or in parallel batches. Each follows the same pattern:

Migration steps (identical for all 30):
1. Run `scripts/inject_rope_headers.py --version 3.0 --target [AGENT_FILE]`
2. Verify: `trace_id`, `confidence_level`, `handoff_protocol` present in SYSTEM_PAYLOAD
3. Run ROPE 3.0 validator: expect PASS (score >= 75)

**Estimated effort per agent:** XS (script-driven, < 5 minutes each)
**Batch processing:** `scripts/inject_rope_headers.py --version 3.0 --all` (once ready)

---

## 5. Fallback Strategy

### 5.1 When v3.0 AOR Calls a v2.0 Agent

Scenario: AOR has been migrated, but target agent (e.g., CVA) is still v2.0.
The v2.0 CVA does not write `confidence_level` or `handoff_protocol`.

AOR behavior (v3.0):
1. Receives CVA output — no `confidence_level` field detected
2. Checks `handoff_protocol` field — absent (v2.0 agent)
3. Logs warning: `compatibility_mode=true, agent_id=CVA, rope_version=2.0`
4. Defaults `confidence_level` to 0.50 (neutral — no gate triggered)
5. Continues chain normally
6. Genesis-MCP entry for CVA shows `confidence_level: 0.50, compatibility_mode: true`

No chain interruption. EVA-33 can identify which agents are still on v2.0 via
`compatibility_mode: true` entries in Genesis-MCP.

### 5.2 When v2.0 Caller Uses v3.0 Agent

Scenario: A pre-migration caller (or external client) sends a request without
`trace_id` or `handoff_protocol`.

Router-MCP behavior (v3.0):
1. Detects missing `X-Trace-ID` header in incoming request
2. Generates `trace_id = uuid4()`
3. Injects into SYSTEM_PAYLOAD before routing
4. Adds `handoff_protocol: "v2"` to SYSTEM_PAYLOAD
5. All downstream agents receive valid v3.0 SYSTEM_PAYLOAD
6. Response includes `X-Trace-ID` header so v2.0 caller can optionally log it

Result: v2.0 callers are fully transparent to v3.0 system. No migration needed on
the caller side.

### 5.3 Full Rollback to v2.0

If ROPE 3.0 rollout fails (see VALIDATION_PLAN.md rollback trigger):
1. `scripts/inject_rope_headers.py --version 2.0 --all` — reverts all persona files
2. Router-MCP: disable `trace_id` generation (env var `ROPE_VERSION=2.0`)
3. AOR: disable v2 state machine, revert to v1 direct call
4. Genesis-MCP: `trace_id` index entries remain (harmless) but no new ones added
5. Healer-MCP: restore from last v2.0 checkpoint

**Rollback time estimate:** < 15 minutes for script injection + service restart.

---

## 6. Known Limitations

| # | Limitation | Impact | Workaround |
|---|-----------|--------|------------|
| L1 | v2.0 agents report `confidence_level: 0.50` by default | EVA-33 cannot distinguish calibrated 0.50 from compatibility-mode 0.50 | Use `compatibility_mode` flag in Genesis-MCP log to filter |
| L2 | `trace_id` absent in all v2.0 Genesis-MCP historical logs | Cross-version trace queries return partial history | Queries should filter by `rope_version` before joining on `trace_id` |
| L3 | `scripts/inject_rope_headers.py --version 3.0` not yet built | Cannot batch-migrate 30 agents until script is updated | Manual migration of AOR/EVA/ARB first; script update in Phase 1 |
| L4 | No per-agent confidence threshold configuration | One global threshold (0.60) for all 33 agents | Post-benchmark per-agent calibration planned for Phase 5 |

---

*Created: 2026-05-20 | Agent: backend-developer | References: ARCHITECTURE_ROPE_3.0.md, VALIDATION_PLAN.md*
