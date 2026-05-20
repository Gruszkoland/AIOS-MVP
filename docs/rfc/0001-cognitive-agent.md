# RFC #0001: Cognitive Agent Architecture

**Date:** 2026-05-20
**Author:** Adrian Halicki
**Status:** Draft

---

## 1. Problem Statement

Currently, the `agents/` crate lacks a unified interface for LLM-based decision advisors. We need a trait that:

- Allows multiple Guardian implementations to coexist
- Ensures agents are advisory-only (not decision-makers)
- Provides type-safe, testable abstraction
- Supports async/await without blocking kernel

**Why now:** Sprint 1 requires pluggable agents; without this, we'll have tight coupling between kernel and agent logic.

---

## 2. Proposed Solution

Define a `CognitiveAgent` trait that all advisors implement:

```rust
pub trait CognitiveAgent: Send + Sync {
    /// Async analysis of context; returns recommendation or error.
    async fn analyze(&self, context: &AnalysisContext) -> Result<Recommendation>;

    /// Human-readable name for logging
    fn name(&self) -> &str;
}

pub struct Recommendation {
    pub verdict: Verdict,              // APPROVE | DENY | FLAG_FOR_REVIEW
    pub confidence: f32,                // 0.0-1.0
    pub reasoning: String,              // audit trail
    pub laws_checked: Vec<GuardianLaw>,
}

pub enum Verdict {
    Approve,
    Deny,
    FlagForReview,
}
```

---

## 3. Design Details

### Three Specialist Implementations

```
CognitiveAgent (trait)
├── SecurityGuardian     — G7/G8 privacy/safety veto
├── EthicsGuardian       — G1-G6, G9 compliance
└── PerformanceGuardian  — Resource constraints, latency budgets
```

**Message Format (via IPC):**

```rust
pub struct AnalysisContext {
    pub job_id: u32,
    pub decision_type: DecisionType,
    pub required_capabilities: CapabilityMask,
    pub deadline_ms: u32,
}

pub struct Recommendation {
    pub verdict: Verdict,
    pub confidence: f32,
    pub laws_checked: [GuardianEval; 9],  // G1-G9 results
    pub reasoning: String,
}
```

**Error Handling:**

```rust
pub enum AgentError {
    Timeout,              // Agent didn't respond in time
    Malformed,            // IPC message parsing failed
    OutOfMemory,          // Shared ring buffer full
    CapabilityDenied,     // Agent lacks capability
}
```

---

## 4. Implementation Plan

**Phase 1 (2026-05-20 to 2026-05-27):**
1. Define trait in `agents/src/lib.rs`
2. Implement `SecurityGuardian` (300 lines) — G7/G8 checks
3. Add IPC serialization (derives `serde`)
4. Write unit tests (80%+ coverage)

**Phase 2 (2026-05-27 to 2026-06-03):**
1. Implement `EthicsGuardian` (G1-G6, G9)
2. Implement `PerformanceGuardian` (resource checks)
3. Integration test: kernel → IPC → agent → recommendation
4. Load tests: 1000 msgs/sec through ring buffer

**Backwards Compatibility:**
None required (new crate, no existing implementations).

---

## 5. Testing Strategy

**Unit tests:**
- `test_security_guardian_blocks_g7_violation`
- `test_ethics_guardian_approves_all_laws`
- `test_performance_guardian_rejects_over_budget`
- `test_recommendation_serde_roundtrip`

**Integration tests:**
- End-to-end: kernel event → IPC → agent → kernel decision

**Benchmarks:**
- Agent latency: `async fn analyze()` must complete in < 10ms (soft deadline)
- Ring buffer throughput: 10k msg/sec target

**Fuzzing:**
- Fuzz `AnalysisContext` parsing from ring buffer
- Fuzz `Recommendation` JSON deserialization

---

## 6. Guardian Laws Impact

| Law | Impact | Mitigation |
|-----|--------|-----------|
| G1: Unity | Positive — agents now have unified interface | None needed |
| G2: Harmony | Positive — agents work cohesively | None needed |
| G3: Rhythm | Positive — deterministic cadence | None needed |
| G4: Causality | Positive — clear decision audit trail | None needed |
| G5: Transparency | Positive — recommendations logged | None needed |
| G6: Authenticity | Positive — no agent deception | None needed |
| G7: Privacy | **CRITICAL** — agents can see sensitive context | Use `CapabilityMask` to restrict data exposure |
| G8: Nonmaleficence | **CRITICAL** — agents must not cause harm | Timeout + deny-safe defaults if agent fails |
| G9: Sustainability | Positive — efficient IPC design | None needed |

**Mitigation strategy for G7/G8:**
- Every `AnalysisContext` includes `required_capabilities` bitset
- Kernel enforces: agent only sees data it has capability to access
- If agent times out or errors: default to `Deny` (fail-safe)
- All recommendations logged with agent ID, timestamp, reasoning

---

## 7. Alternatives Considered

### A. Function pointers instead of trait

```rust
type AgentFn = async fn(&AnalysisContext) -> Result<Recommendation>;
```

**Rejected:** Loss of polymorphism, harder to test, no state management for agents.

### B. Pub/sub (message queue)

Agents subscribe to kernel events, publish recommendations asynchronously.

**Rejected:** Race conditions with ring buffer, harder to enforce deadlines.

### C. Inline agent logic in kernel

Put all logic in `kernel/` crate.

**Rejected:** Violates separation of concerns, makes kernel bloated, harder to swap implementations.

---

## 8. Open Questions

- [ ] Should agents have state (e.g., learning from past decisions)?
- [ ] Should recommendations be weighted/combined (e.g., majority vote)?
- [ ] What's the timeout value? (proposed: soft deadline from context)
- [ ] Should we expose agent metrics (latency, accuracy) to UAP?

---

## 9. References

- GitHub issue: (TBD)
- Related code: `agents/`, `ipc/`, `kernel/`
- Guardian Laws: `docs/GUARDIAN_LAWS_CANONICAL.json`
