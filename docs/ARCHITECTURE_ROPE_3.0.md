---
title: "ROPE 3.0 — Architecture & Modernization Design"
version: "3.0"
status: "Design — awaiting EVA-33 validation"
created: "2026-05-20"
author: "backend-developer agent"
depends_on: "CLAUDE.md, MANIFEST.md, docs/GUARDIAN_LAWS_CANONICAL.json, docs/PERSONA-MAPPING.md"
---

# ROPE 3.0 — Architecture & Modernization Design

> **ROPE** = Reasonable Orchestration Protocol for AI agEnts.
> This document covers the v2.0 → v3.0 transition for the 33-agent system in ADRION 369.
> Canonical Guardian Laws: `docs/GUARDIAN_LAWS_CANONICAL.json`. Do not edit law names here.

---

## 1. Overview

### 1.1 Goals

ROPE 3.0 introduces three targeted changes to v2.0:

| Goal | Change | Benefit |
|------|--------|---------|
| Distributed tracing | `trace_id` field in SYSTEM_PAYLOAD | Correlate all 33 agents in a single request chain |
| Output quality signal | `confidence_level` field (0.0–1.0) | EVA-33 can flag low-confidence outputs before handoff |
| Reliable handoff | Handoff Protocol v2 (state machine + retry) | Eliminate silent failures between agents |

ROPE 2.0 had no mechanism to correlate agent outputs across a multi-hop decision chain.
When a request traversed MPG → AOR → ARB → EVA, each step operated blindly — no shared
context ID, no confidence signal to stop a degraded chain early. v3.0 fixes this.

### 1.2 Scope

- All 33 AI persona files (SYSTEM_PAYLOAD schema update)
- Handoff logic in AOR (AGT-003 equivalent in ROPE registry)
- EVA-33 validation hooks (confidence_level reader)
- MCP layer: Router-MCP, Oracle-MCP, Genesis-MCP updated endpoints
- `docs/openapi.yaml` additions (trace_id in request/response headers)

### 1.3 Non-Goals

- New agent personas (33 total stays fixed for this version)
- UI/dashboard changes
- Database schema migrations (trace_id lives in SYSTEM_PAYLOAD, not persistent DB)
- Guardian Law changes (canonical JSON locked per CLAUDE.md rule)
- Performance optimization (separate P3 wave per CLAUDE.md checklist)

---

## 2. Core Changes vs v2.0

### 2.1 trace_id (NEW)

**Why v2.0 lacked it:** Each agent invocation was stateless from the perspective of
the calling chain. Genesis-MCP stored decision logs per `session_id`, but within one
session multiple agent calls produced unlinked log entries.

**How v3.0 adds it:**
- Caller (first agent or API client) generates `uuid4` at request entry.
- Every downstream agent receives the same `trace_id` via SYSTEM_PAYLOAD.
- Genesis-MCP indexes decision logs by `(session_id, trace_id)` pair.
- Healer-MCP uses `trace_id` to identify which sub-chain to replay on repair.

**Format:** `trace_id: string` — UUID v4 (xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx).
**Immutable:** Once set by caller, no agent may change it. Mutation = G4 (Causality) violation.

**Benefit:** Full end-to-end visibility. A single Grafana query on `trace_id` shows
all 33 possible hops in chronological order.

### 2.2 confidence_level (NEW)

**Why v2.0 lacked it:** Agent outputs had no self-reported quality signal. EVA-33 had
to infer quality post-hoc from token counts and latency proxies, which is unreliable.

**How v3.0 adds it:**
- Each agent writes `confidence_level: float` in its SYSTEM_PAYLOAD output block.
- Range: 0.0 (no confidence) to 1.0 (full confidence).
- Handoff Protocol v2 reads this value before forwarding to next agent.
- Gate: if `confidence_level < 0.60`, the handoff pauses and EVA-33 is notified.
- BRAKDANYCH: Calibration baseline for each agent's typical confidence distribution
  is not yet measured. Method: run 10 benchmark scenarios (see VALIDATION_PLAN.md),
  collect p50/p95 confidence per agent, set per-agent thresholds in Phase 2.

**Format:** `confidence_level: float` in [0.0, 1.0].
**Default when agent does not set it:** `0.50` (neutral, no gate triggered).

### 2.3 Handoff Protocol v2

**Why v2.0 was insufficient:** v1 handoff was a direct function call with no timeout,
no retry, no acknowledgment, and no escalation path. A failed handoff silently dropped
the task.

**How v3.0 changes it:**
- Explicit state machine: IDLE → REQUESTING → VALIDATING → TRANSFERRING → CONFIRMING → COMPLETE
- Failed states: REQUESTING_FAILED, VALIDATING_FAILED, TRANSFER_TIMEOUT, ESCALATED
- Retry: max 3 attempts, exponential backoff (base: 2s, factor: 2x, cap: 16s)
- Timeout: 30s per attempt (configurable via `HANDOFF_TIMEOUT_SECONDS` env var)
- Escalation: after 3 failed retries → route to ARB (Arbiter) agent
- Guardian check: G8 (Nonmaleficence) evaluated before each retry to prevent harm loops

**Diagram reference:** `docs/diagrams/handoff_state_machine.mmd`

---

## 3. Agent Registry

> Source of truth for agent IDs: ROPE 2.0 validation report (40_RAPORTY/Dependabot-Personas-ROPE2-Completion-15-05-2026.md).
> All 33 agents passed ROPE 2.0 validation with score >= 75.

| # | ID | Name | Domain | Capability |
|---|----|----|------|---------|
| 01 | MPG | Master Prompt Generator | prompt_engineering | generate_structured_prompts |
| 02 | PWB | Programator Webowy | web_development | fullstack_code_generation |
| 03 | CVA | Creator of Visualization & Animation | creative_media | visual_content_production |
| 04 | QPA | Quantum Pattern Analyst | data_analysis | pattern_recognition_162D |
| 05 | SAP | Strategic Architect & Planner | strategy | multi_horizon_planning |
| 06 | BLV | BoosterLever | growth_optimization | leverage_amplification |
| 07 | ARB | The Arbiter | conflict_resolution | dispute_adjudication |
| 08 | EGO | Etos Guardian OS | ethics_compliance | guardian_law_enforcement |
| 09 | CTG | Chronos The Guardian | temporal_management | scheduling_and_timing |
| 10 | ECA | Echo Archetypow | archetype_mapping | behavioral_pattern_matching |
| 11 | CEC | Content Engine & Copywriter | content_creation | multilingual_copywriting |
| 12 | ROA | Research & OSINT Agent | intelligence_gathering | open_source_research |
| 13 | AOR | Agent Orchestrator | orchestration | multi_agent_coordination |
| 14 | LCA | Legal & Compliance Advisor | legal_compliance | regulatory_analysis |
| 15 | DBI | Data Analyst & BI | business_intelligence | data_visualization |
| 16 | UXD | UX UI Designer | user_experience | interface_design |
| 17 | DCA | DevOps & Cloud Architect | infrastructure | cloud_deployment_automation |
| 18 | SNE | Sales & Negotiation Expert | business_development | negotiation_strategy |
| 19 | QTE | QA & Test Engineer | quality_assurance | automated_test_generation |
| 20 | SEO | SEO Specialist | digital_marketing | search_optimization |
| 21 | EDU | Educator & Tutor | knowledge_transfer | adaptive_learning_design |
| 22 | PCH | Personal Coach | personal_development | behavior_change_facilitation |
| 23 | VAP | Video & Audio Producer | multimedia_production | av_content_creation |
| 24 | SMM | Social Media Manager | social_media | community_engagement |
| 25 | TLO | Translator & Localizer | linguistics | cross_cultural_localization |
| 26 | CRM | CRM & Customer Success | customer_relations | retention_optimization |
| 27 | PFT | Personal Finance & Tax | financial_planning | tax_optimization |
| 28 | CSO | Cybersecurity Specialist | security | threat_modeling_defense |
| 29 | KMS | Knowledge Manager | knowledge_management | knowledge_graph_curation |
| 30 | HRR | HR & Recruitment | human_resources | talent_acquisition |
| 31 | PMO | Product Manager | product_management | roadmap_prioritization |
| 32 | TWR | Technical Writer | technical_documentation | api_doc_generation |
| 33 | EVA | Evaluation & Observability Architect | observability | performance_benchmarking |

**Note on AOR (Agent Orchestrator, #13):** AOR is the agent responsible for executing
Handoff Protocol v2. It reads `confidence_level` and propagates `trace_id`. AOR must
be updated before any other agent benefits from v3.0 changes.

**Note on EVA (Evaluation & Observability, #33):** EVA-33 is the validation agent for
ROPE compliance. It reads `confidence_level` from all incoming SYSTEM_PAYLOADs and
produces the regression benchmark report. See ROPE_3.0_VALIDATION_PLAN.md.

---

## 4. SYSTEMPAYLOAD Evolution

### 4.1 v2.0 Schema (current)

Every ROPE 2.0 agent file ends with:

```
--- SYSTEM_PAYLOAD ---
agent_id: [AKRONIM]
agent_number: "[NR]"
version: "2.0"
session_id: "${SESSION_ID}"
context: "${CONTEXT_DATA}"
```

Fields present in v2.0: `agent_id`, `agent_number`, `version`, `session_id`, `context`.
No tracing. No confidence signal. No handoff version marker.

### 4.2 v3.0 Schema (target)

```
--- SYSTEM_PAYLOAD ---
agent_id: [AKRONIM]
agent_number: "[NR]"
version: "3.0"
session_id: "${SESSION_ID}"
trace_id: "${TRACE_ID}"
confidence_level: ${CONFIDENCE_LEVEL}
handoff_protocol: "v2"
context: "${CONTEXT_DATA}"
```

Diff markers:
- `+` `trace_id` — NEW field, UUID v4, set by first caller, immutable downstream
- `+` `confidence_level` — NEW field, float 0.0–1.0, set by each agent independently
- `+` `handoff_protocol` — NEW field, value always "v2" for ROPE 3.0 agents
- `~` `version` — CHANGED from "2.0" to "3.0"

### 4.3 Field Definitions

| Field | Type | Who sets it | Rules |
|-------|------|-------------|-------|
| `agent_id` | string | Agent template | Immutable. Must match registry acronym. |
| `agent_number` | string | Agent template | Immutable. Zero-padded, e.g. "07". |
| `version` | string | Agent template | "3.0" for all ROPE 3.0 agents. |
| `session_id` | string | Caller (API client) | UUID v4. Scopes Genesis-MCP storage. |
| `trace_id` | string | First agent in chain | UUID v4. Never modified downstream. G4 violation if mutated. |
| `confidence_level` | float | Each agent independently | 0.0–1.0. If omitted, defaults to 0.50 at handoff. |
| `handoff_protocol` | string | Agent template | Always "v2". Used by AOR to select state machine version. |
| `context` | string | Runtime injection | Session context blob. Encrypted at rest in Genesis-MCP. |

### 4.4 Injection Script Update

The existing `scripts/inject_rope_headers.py` (used for ROPE 2.0 injection) must be
updated to:
1. Write `version: "3.0"` instead of "2.0"
2. Append three new lines to SYSTEM_PAYLOAD block: `trace_id`, `confidence_level`, `handoff_protocol`
3. BRAKDANYCH: Path to 33 persona files in v3.0 context. Method: run
   `scripts/inject_rope_headers.py --list-targets` after repo structure update.

---

## 5. Handoff Protocol v2

### 5.1 State Machine

States and transitions:

```
IDLE
  |
  +--(agent.execute())--> REQUESTING
                             |
                    (Guardian G8 check)
                             |
                      [pass] | [fail]
                             |        \
                       VALIDATING    REQUESTING_FAILED
                             |              |
               (confidence >= 0.60)       ESCALATED (to ARB)
                             |
                      TRANSFERRING
                             |
                    (target agent ACK)
                             |
                       CONFIRMING
                             |
                   (Genesis-MCP log write)
                             |
                        COMPLETE
```

Failed transitions loop back with retry:
- REQUESTING_FAILED: retry up to 3 times, then ESCALATED
- TRANSFER_TIMEOUT: retry from TRANSFERRING, then ESCALATED after 3 timeouts

### 5.2 Retry Logic

```python
# Pseudocode — implementation in AOR persona (agent #13)
MAX_RETRIES = 3
BASE_DELAY_SECONDS = 2
MAX_DELAY_SECONDS = 16

for attempt in range(1, MAX_RETRIES + 1):
    try:
        result = call_target_agent(target_id, payload, timeout=30)
        if result.confidence_level < 0.60:
            notify_EVA(trace_id, result.confidence_level, target_id)
        return result
    except (TimeoutError, HandoffError) as exc:
        delay = min(BASE_DELAY_SECONDS * (2 ** (attempt - 1)), MAX_DELAY_SECONDS)
        log_retry(trace_id, attempt, exc, delay)
        if attempt == MAX_RETRIES:
            escalate_to_ARB(trace_id, target_id, exc)
            raise HandoffEscalated(trace_id=trace_id)
        sleep(delay)
```

### 5.3 Escalation Path

When MAX_RETRIES exceeded:
1. AOR creates escalation record in Genesis-MCP (keyed by `trace_id`)
2. AOR calls ARB (agent #07) with full handoff failure context
3. ARB evaluates: retry with different agent | degrade gracefully | halt chain
4. ARB decision logged to Genesis-MCP under same `trace_id`
5. EVA-33 picks up escalation count in post-session benchmark report

### 5.4 Guardian Law Checks in Handoff

Before each handoff attempt, AOR evaluates:
- G8 (Nonmaleficence): does the handoff action cause downstream harm? If yes, HALT immediately.
- G4 (Causality): is there a justified reason to call this agent? If no logical cause, REQUESTING_FAILED.
- G5 (Transparency): handoff event is logged regardless of outcome.

Diagram reference: `docs/diagrams/handoff_state_machine.mmd`

---

## 6. MCP Integration

The MCP layer consists of 6 microservices on ports 9000–9005. ROPE 3.0 changes affect
three of them.

### 6.1 Router-MCP (port 9000) — UPDATED

Role: Entry point for all inter-agent routing. New in v3.0:
- Accepts `X-Trace-ID` HTTP header from external callers
- If header absent, generates `uuid4` and injects into SYSTEM_PAYLOAD
- Forwards `trace_id` to all downstream MCP servers via internal header

Tools: `route_request`, `select_agent`, `propagate_trace`
Resources: `agent_registry` (33 entries), `routing_table`

### 6.2 Vortex-MCP (port 9001) — unchanged

Role: Harmonic orchestration, 174Hz pulse, canary gates.
No ROPE 3.0 changes. Receives `trace_id` passively for log correlation only.

Tools: `health_check`, `deploy`, `rollback`
Resources: `service_telemetry`, `deployment_history`

### 6.3 Guardian-MCP (port 9002) — unchanged

Role: Policy enforcement — all 9 Guardian Laws per `docs/GUARDIAN_LAWS_CANONICAL.json`.
No ROPE 3.0 changes. `trace_id` logged on every G8/G7 CRITICAL check for audit trail.

Tools: `validate_action`, `get_audit_log`, `override_request`
Resources: `guardian_laws` (canonical JSON), `audit_entries`

### 6.4 Oracle-MCP (port 9003) — UPDATED

Role: 162D routing (3 perspectives x 6 hexagon stages x 9 laws). New in v3.0:
- `confidence` output field now mapped to `confidence_level` in SYSTEM_PAYLOAD
- Decision history indexed by `(session_id, trace_id)` for full chain replay

Tools: `route_162D`, `rank_agents`, `get_decision_history`
Resources: `decision_space` (162D grid), `trust_scores` (per agent TSPA)

### 6.5 Genesis-MCP (port 9004) — UPDATED

Role: Session persistence, decision logs, RAG-based context retrieval. New in v3.0:
- Decision log entries include `trace_id` as indexed field
- New endpoint `GET /genesis/trace/{trace_id}` returns full chain history
- Escalation records stored under `events.type = "handoff_escalation"`

Tools: `persist_decision`, `retrieve_context`, `get_trace_history`, `store_escalation`
Resources: `session_states`, `decision_logs` (JSONL, append-only), `rag_index`

### 6.6 Healer-MCP (port 9005) — unchanged

Role: Error recovery, state repair, rollback to checkpoint.
Passively uses `trace_id` to identify which chain segment to replay.

Tools: `detect_error`, `repair_state`, `replay_chain`
Resources: `checkpoints` (git-based), `error_registry`

---

## 7. Deployment Timeline

### 7.1 Phases

| Phase | Action | Gate | Owner |
|-------|--------|------|-------|
| Phase 1 — Schema | Update `inject_rope_headers.py` to write v3.0 fields | Script produces valid YAML for 33 agents | backend-developer |
| Phase 1 — Schema | Inject ROPE 3.0 headers into all 33 persona files | ROPE 3.0 validator: 33/33 PASS | backend-developer |
| Phase 2 — AOR | Implement Handoff Protocol v2 state machine in AOR | Unit tests: retry logic, timeout, escalation | backend-developer |
| Phase 2 — AOR | Integrate EVA-33 confidence hook (notify on < 0.60) | Integration test: low-confidence scenario | backend-developer |
| Phase 3 — MCP | Update Router-MCP: trace header injection | API test: `X-Trace-ID` propagated to all hops | backend-developer |
| Phase 3 — MCP | Update Oracle-MCP: confidence_level mapping | Oracle output matches SYSTEM_PAYLOAD field | backend-developer |
| Phase 3 — MCP | Update Genesis-MCP: trace-indexed logs + new endpoint | `GET /genesis/trace/{trace_id}` returns full chain | backend-developer |
| Phase 4 — Validate | Run EVA-33 benchmark (10 scenarios, see VALIDATION_PLAN.md) | Candidate >= Baseline on 4/5 metrics | EVA-33 |
| Phase 5 — Rollout | Canary: 10% → 50% → 100% traffic | Zero CRITICAL Guardian violations per phase gate | devops |

### 7.2 Canary Gates

- Gate 10%: Monitor 48h. Halt if handoff_escalation rate > 5%.
- Gate 50%: Monitor 24h. Halt if confidence_level p50 < 0.60 across any agent.
- Gate 100%: Full rollout after EVA-33 issues ROPE_3.0_VALIDATED=true.

BRAKDANYCH: Current handoff_escalation baseline rate in v2.0. Method: query Genesis-MCP
decision logs for `events.type = "handoff_error"` over last 30 days.

---

## 8. Risk Assessment

### R1 — Confidence Calibration Drift (HIGH)

**What breaks:** Agents initially report miscalibrated `confidence_level`. Agents that
always report 0.95 never trigger EVA-33 gates; agents that always report 0.40 cause
constant escalation churn.

**Mitigation:** Run 10 benchmark scenarios before Phase 5 rollout. Per-agent p50
confidence establishes baseline. Agents outside 2 sigma get manual calibration review.

**Owner:** EVA-33 (agent #33). Deadline: before Phase 5 gate.

### R2 — trace_id Mutation (MEDIUM)

**What breaks:** A single agent incorrectly regenerates `trace_id` mid-chain. Causes
log fragmentation — Genesis-MCP shows two separate chains for one request.

**Mitigation:** Validator in Router-MCP rejects any SYSTEM_PAYLOAD where incoming
`trace_id` != outgoing `trace_id`. This is a G4 (Causality) violation — auto-DENY.

**Owner:** Router-MCP update in Phase 3.

### R3 — Retry Storm (HIGH)

**What breaks:** If a target agent is persistently unavailable, all callers retry
simultaneously. Each retry waits up to 16s, but 33 agents could generate 99 retries
simultaneously.

**Mitigation:** Circuit breaker per target agent (reuse `arbitrage/circuit_breaker.py`
pattern). After 5 consecutive failures to one target, open circuit for 60s.

**Owner:** backend-developer. Implement in Phase 2 alongside AOR state machine.

### R4 — ROPE 2.0 Agents Called by ROPE 3.0 (MEDIUM)

**What breaks:** AOR (v3.0) calls an agent that has not yet been migrated to v3.0.
The called agent does not write `confidence_level` — AOR gets None, defaults to 0.50.

**Mitigation:** AOR checks `handoff_protocol` field in received SYSTEM_PAYLOAD.
If "v2" absent, log warning and use default 0.50. Never block on missing field.
Full migration must complete before Phase 5 gate.

**Compatibility details:** `docs/ROPE_3.0_COMPATIBILITY.md`

### R5 — Genesis-MCP Storage Growth (LOW)

**What breaks:** Adding `trace_id` indexing and per-trace history endpoint increases
Genesis-MCP storage linearly with request volume.

**Mitigation:** TTL on trace entries: 30 days rolling window. Configurable via
`GENESIS_TRACE_TTL_DAYS` env var. Decision logs remain append-only (audit compliance).

**Owner:** Genesis-MCP Phase 3 update.

---

## 9. 162D Decision Space Integration

ROPE 3.0 operates within the Trinity-EBDI 162D decision space defined in `docs/ARCHITECTURE.md`:
3 perspectives x 6 hexagon stages x 9 Guardian Laws = 162 dimensions.

### 9.1 How trace_id Maps to 162D

When Oracle-MCP routes a request through the 162D space, the selected dimensions are
logged alongside `trace_id`. This means any request can be reconstructed as:
- Which perspective was active (LOGOS/ETHOS/EROS = Material/Intellectual/Essential)
- Which hexagon stage was engaged (Inventory/Empathy/Process/Debate/Healing/Action)
- Which Guardian Laws were evaluated (G1–G9)

Genesis-MCP stores this as `decision_context` on each trace entry:

```json
{
  "trace_id": "a3f2...c1b7",
  "agent_id": "SAP",
  "decision_context": {
    "perspective": "LOGOS",
    "hexagon_stage": "Process",
    "guardian_laws_checked": ["G4", "G5", "G8"],
    "trust_score": 0.87
  },
  "confidence_level": 0.82
}
```

### 9.2 Agent Distribution Across 162D Space

The 33 agents naturally cluster into the 3 Trinity perspectives:

**LOGOS (Material — analytical, data-driven) — 12 agents:**
QPA, DBI, ROA, QTE, SEO, KMS, TWR, PWB, DCA, CSO, PFT, MPG

**ETHOS (Intellectual — ethical, compliance-focused) — 10 agents:**
EGO, CTG, LCA, ARB, EVA, HRR, EDU, PCH, CRM, TLO

**EROS (Essential — creative, synthesis-focused) — 11 agents:**
CVA, CEC, VAP, SMM, SAP, BLV, AOR, UXD, SNE, PMO, ECA

This distribution is informational. Oracle-MCP selects the perspective per request
context, not per agent's home cluster.

### 9.3 confidence_level Within EBDI

The EBDI model (docs/EBDI-MODEL.md) uses a PAD vector (Pleasure, Arousal, Dominance)
to compute Decision Temperature (T ∈ [0.05, 0.95]).

`confidence_level` in ROPE 3.0 is a complement to EBDI temperature:
- EBDI T is system-level (regulates caution across all agents)
- `confidence_level` is agent-level (self-reported per output)

Relationship:
- When system Arousal > 0.7 (crisis mode): all `confidence_level` values are
  penalized by factor 0.85 before EVA-33 comparison to gate threshold.
- Rationale: In crisis mode, even an agent confident in its output should be
  treated with extra skepticism. G8 (Nonmaleficence) requires additional caution.

BRAKDANYCH: The penalty factor 0.85 is provisional. Method: measure actual agent
confidence distributions during crisis vs. normal EBDI states in 10-scenario benchmark.

### 9.4 Matryca 3-6-9 in ROPE 3.0 Handoff Escalation

When a handoff escalates to ARB, ARB evaluates the failure through the Matryca lens:

- **LOGOS (Prawda):** Is the failure factual? Is the target agent technically broken?
- **ETHOS (Dobro):** Does the failure harm users or the system? Does G8 apply?
- **EROS (Tworzenie):** Can a different agent or degraded path still serve the user?

ARB documents this 3-perspective evaluation in the escalation record stored in Genesis-MCP.
This makes every escalation traceable to a reasoning framework, not just a retry log.

---

## Appendix: Reference Documents

- Architecture v4.0: `docs/ARCHITECTURE.md`
- Guardian Laws: `docs/GUARDIAN_LAWS_CANONICAL.json`
- Persona Mapping: `docs/PERSONA-MAPPING.md`
- MCP Architecture: `docs/MCP_ARCHITECTURE.md`
- ROPE 2.0 Completion Report: `40_RAPORTY/Dependabot-Personas-ROPE2-Completion-15-05-2026.md`
- Validation Plan: `docs/ROPE_3.0_VALIDATION_PLAN.md`
- Compatibility Matrix: `docs/ROPE_3.0_COMPATIBILITY.md`
- Changelog: `CHANGELOG_ROPE_3.0.md`

---

*Created: 2026-05-20 | Agent: backend-developer | Status: Pending EVA-33 validation*
