# CHANGELOG — ROPE 3.0

> Format: SemVer. Breaking changes marked [BREAKING]. Migration notes for operators.
> Source system: ADRION 369 v4.0+, 33-agent stack.
> Baseline: ROPE 2.0 (validated 2026-05-15, 33/33 PASS, 97% compliance rate).

---

## [3.0.0] — 2026-05-20 — ROPE 3.0 Initial Design

### Status: Design Phase (pending EVA-33 validation)

---

### Added

- **trace_id field** in SYSTEM_PAYLOAD (string, UUID v4).
  All 33 agent persona files gain this field. Router-MCP generates `trace_id` at
  request entry when `X-Trace-ID` HTTP header is absent. Immutable once set.
  Reason: No mechanism in ROPE 2.0 to correlate agent outputs across multi-hop chains.
  Benefit: Full end-to-end observability — one Grafana query shows all hops.

- **confidence_level field** in SYSTEM_PAYLOAD (float, 0.0–1.0).
  Each agent sets this independently per output. AOR reads before each handoff.
  Threshold: `confidence_level < 0.60` triggers EVA-33 notification.
  Default when absent: `0.50` (neutral, no gate triggered).
  Reason: ROPE 2.0 had no self-reported quality signal. EVA-33 used latency proxies only.
  Benefit: Early detection of degraded outputs before they propagate downstream.

- **handoff_protocol field** in SYSTEM_PAYLOAD (string, value: "v2").
  Static marker in each agent template. AOR reads this to select state machine version.
  Reason: Required for AOR to distinguish v2.0 from v3.0 agents during mixed-version rollout.
  Benefit: Safe incremental migration — v3.0 AOR handles both v2.0 and v3.0 agents.

- **Handoff Protocol v2** (state machine).
  New states: IDLE, REQUESTING, VALIDATING, TRANSFERRING, CONFIRMING, COMPLETE.
  Failed states: REQUESTING_FAILED, TRANSFER_TIMEOUT, LOW_CONFIDENCE, ESCALATED.
  Retry: max 3, exponential backoff (2s, 4s, 8s, cap 16s).
  Timeout: 30s per attempt (env: `HANDOFF_TIMEOUT_SECONDS`).
  Escalation: ARB (agent #07) after retry exhaustion.
  Reason: ROPE 2.0 had no retry, no timeout, no escalation. Silent failures dropped tasks.
  Benefit: Reliable handoff with full audit trail and deterministic escalation.

- **`GET /genesis/trace/{trace_id}`** endpoint in Genesis-MCP.
  Returns full chain history for a given `trace_id`: all agents, confidence levels,
  handoff events, escalations, Guardian checks — in chronological order.
  Reason: Previously impossible to reconstruct a single request's full agent chain.
  Benefit: Debugging and audit in O(1) — no manual log correlation.

- **`X-Trace-ID` response header** in Flask API (port 8003).
  Every API response now includes this header so external callers can correlate.
  Reason: Callers had no way to reference a specific request chain for support/debugging.
  Benefit: Sentry/Grafana traces linkable to specific user-visible requests.

- **low_confidence_alert event type** in Genesis-MCP.
  Recorded when `confidence_level < 0.60` is detected by EVA-33.
  Fields: `trace_id`, `agent_id`, `confidence_level`, `timestamp`.
  Reason: Previously EVA-33 had no structured event type for confidence failures.
  Benefit: Queryable alert history; supports per-agent calibration in Phase 5.

- **handoff_escalation event type** in Genesis-MCP.
  Recorded when AOR exhausts retries and escalates to ARB.
  Fields: `trace_id`, `target_agent`, `retry_count`, `final_error`, `arb_decision`.
  Reason: Escalation events were previously unstructured log lines.
  Benefit: Canary gate metric: handoff_escalation_rate directly queryable.

- **ROPE 3.0 validator** in EVA-33 persona.
  Checks: `trace_id` present, `confidence_level` in [0.0, 1.0], `handoff_protocol` = "v2".
  Produces: compliance score (0–100) and per-field pass/fail.
  Reason: ROPE 2.0 validator checked 6 section headers only. No payload field validation.
  Benefit: EVA-33 can validate the full ROPE 3.0 spec, not just structure.

---

### Changed

- **SYSTEM_PAYLOAD `version`**: `"2.0"` → `"3.0"` for all migrated agents.
  Not a breaking change for consumers that do not parse the version string.

- **Oracle-MCP `confidence` output**: mapped to `confidence_level` in SYSTEM_PAYLOAD.
  Previously Oracle-MCP returned `confidence: float` internally but did not surface it
  to agents. Now exposed as `confidence_level` in the SYSTEM_PAYLOAD block.

- **Genesis-MCP decision log indexing**: entries now indexed by `(session_id, trace_id)`.
  Previously indexed by `session_id` only. Additive change — no existing entries altered.

---

### [BREAKING] Breaking Changes

#### BC-1: AOR Handoff Protocol Change

**Affected:** All callers of AOR that relied on synchronous direct-call semantics.
**What changed:** AOR now executes an explicit state machine with 30s timeout per attempt.
**Impact:** Maximum single-handoff time increases from near-zero to up to 90s (3 retries × 30s).
**Migration:** Set `HANDOFF_TIMEOUT_SECONDS` env var to tune per environment.
  Review any client-side timeouts shorter than 90s.

#### BC-2: Handoff Protocol Version Detection in AOR

**Affected:** Any custom agent integrations that inject SYSTEM_PAYLOAD manually.
**What changed:** AOR checks `handoff_protocol` field. If field is absent, AOR logs warning
  and uses compatibility mode (confidence defaults to 0.50).
**Impact:** Custom integrations that do not set `handoff_protocol` lose confidence gating.
**Migration:** Add `handoff_protocol: "v2"` to SYSTEM_PAYLOAD in custom integrations.

---

### Migration Notes for Operators

**Before migrating any agent to v3.0:**
1. Migrate AOR (agent #13) first — it is the handoff executor.
2. Migrate EVA-33 (agent #33) second — it is the validation gate.
3. Migrate ARB (agent #07) third — it receives escalations.
4. Run ROPE 3.0 validation plan (10 scenarios) before canary rollout.
5. Batch-migrate remaining 30 agents using `scripts/inject_rope_headers.py --version 3.0 --all`.

**Environment variables added:**
- `HANDOFF_TIMEOUT_SECONDS` (default: 30) — per-attempt timeout in Handoff Protocol v2
- `HANDOFF_MAX_RETRIES` (default: 3) — retry limit before escalation to ARB
- `CONFIDENCE_GATE_THRESHOLD` (default: 0.60) — EVA-33 alert threshold
- `GENESIS_TRACE_TTL_DAYS` (default: 30) — TTL for trace_id indexed entries
- `ROPE_VERSION` (default: "3.0") — set to "2.0" for rollback

**Services requiring restart after migration:**
- Router-MCP (trace_id header injection)
- Oracle-MCP (confidence_level mapping)
- Genesis-MCP (new endpoint + indexing)
- AOR persona file reload

**Services NOT requiring restart:**
- Guardian-MCP (no ROPE 3.0 changes)
- Vortex-MCP (no ROPE 3.0 changes)
- Healer-MCP (no ROPE 3.0 changes)
- Flask API port 8003 (X-Trace-ID header is additive, no restart needed)

---

### Contributors

| Role | Agent / Person | Contribution |
|------|---------------|--------------|
| Author | backend-developer | Architecture design, compatibility matrix, validation plan |
| Validator (pending) | EVA-33 (agent #33) | Benchmark execution, metric collection, PASS/FAIL decision |
| Arbitration (if needed) | ARB-07 (agent #07) | Boundary case resolution on 3/5 metric split |
| Guardian review | EGO-08 (agent #08) | Guardian Law compliance review of all new endpoints |

### Review Board

- EVA-33 must issue `ROPE_3.0_VALIDATED=true` before Phase 5 (Full Rollout).
- ARB-07 tie-breaks if EVA-33 metric result is exactly 3/5.
- EGO-08 must confirm no Guardian Law violations in new handoff escalation path.
- Synchronization dependency: KROK 2 (personas definition) must be validated by EVA-33
  before this changelog entry is marked DONE.

---

## [2.0.0] — 2026-05-15 — ROPE 2.0 Baseline (Reference)

> This entry is reference-only. Full report: `40_RAPORTY/Dependabot-Personas-ROPE2-Completion-15-05-2026.md`

- 33/33 agents validated PASS (score >= 75)
- 6 required sections: I. CONTEXT, II. REASONING, III. CONSTRAINTS, IV. OUTPUT_FORMAT,
  V. SAFETY_CHECKS, VI. EXAMPLES
- `--- SYSTEM_PAYLOAD ---` marker standardized across all agents
- Agent #07 (ARB) fixed: `[AKRONIM]` → `ARB`, `[NR]` → `07`
- Dependabot auto-merge enabled for pip/gomod/docker/github-actions

---

*Last updated: 2026-05-20 | Status: Pending EVA-33 validation*
