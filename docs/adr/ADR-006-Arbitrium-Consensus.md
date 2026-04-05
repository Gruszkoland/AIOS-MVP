# ADR-006: Arbitrium Consensus Model

## Status
- [ ] Proposed

## Decision
Formalize Conflict Resolver (CR-6) consensus voting:
- **Voting weights:** Based on TSPA (Trust Score Per Agent)
- **Quorum:** 4/6 agents (2/3 majority required)
- **Appeal mechanism:** Losing party can escalate to Auditor for review
- **Timeout:** 5s max decision time (fail-safe: default to Architect)

Benefits: ✅ Fair, TS-weighted consensus | ✅ Deterministic tie-breaking
Trade-off: ❌ Low-TS agents have less voice (but correctness > democracy)

---

**Proposed By:** Architect | **Date:** 2026-04-05
