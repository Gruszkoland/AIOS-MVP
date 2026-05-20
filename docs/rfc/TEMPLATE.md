# RFC Template — AIOS MVP

Please copy this template when proposing a new RFC. Follow the structure below and open a PR with the RFC document only (no implementation code yet).

---

## RFC [#]: [Title]

**Date:** YYYY-MM-DD
**Author:** [Your Name]
**Status:** Draft | Review | Accepted | Declined | Implemented

---

## 1. Problem Statement

What problem does this RFC solve? Why is the current approach insufficient?

**Context:**
- Current behavior / limitation
- Impact on system, performance, or safety
- Why this matters now

---

## 2. Proposed Solution

Describe the high-level approach. Include:

- What changes at the API/interface level?
- How does this affect kernel, agents, or IPC?
- Are there breaking changes?

**Example (RFC #0001):**
```rust
pub trait CognitiveAgent: Send + Sync {
    async fn analyze(&self, context: &Context) -> Result<Recommendation>;
}
```

---

## 3. Design Details

Go deeper. Include:

- Data structures / type signatures
- Algorithm / pseudocode
- Error handling strategy
- Performance implications (latency, memory)

---

## 4. Implementation Plan

- Which crates are affected? (kernel, agents, ipc, poc?)
- What's the rollout strategy?
- Any backwards-compatibility concerns?
- Definition of Done for implementation

---

## 5. Testing Strategy

- Unit tests required?
- Integration tests required?
- Benchmarks? (is latency affected?)
- Fuzzing? (if parsing/validation changes)

---

## 6. Guardian Laws Impact

Evaluate against all 9 Guardian Laws (see `docs/GUARDIAN_LAWS_CANONICAL.json`):

| Law | Impact | Mitigation |
|-----|--------|-----------|
| G1: Unity | ... | ... |
| G2: Harmony | ... | ... |
| ... | ... | ... |
| G7: Privacy | ... | ... |
| G8: Nonmaleficence | ... | ... |
| ... | ... | ... |

**Critical analysis:** Does this RFC introduce any G7 (Privacy) or G8 (Nonmaleficence) risk? If yes, describe mitigation.

---

## 7. Alternatives Considered

What other approaches did you evaluate? Why was the proposed solution chosen?

---

## 8. Open Questions

- [ ] What about [concern X]?
- [ ] Should we [question Y]?
- [ ] Does [detail Z] need clarification?

---

## 9. References

- Link to related GitHub issues
- Link to relevant code (e.g., `kernel/src/scheduler.rs`)
- External references (papers, specs, etc.)

---

## Example: RFC #0001 (filled in)

See [rfc/0001-cognitive-agent.md](0001-cognitive-agent.md) for a complete example.
