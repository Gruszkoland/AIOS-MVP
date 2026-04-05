# ADR-004: Probabilistic SAV (Step Auto-Verification)

## Status
- [ ] Proposed

## Decision
Replace 100% SAV checking with probabilistic model:
- High-risk operations (destructive, security): 100% verification
- Medium-risk operations (data writes): 50% spot-check + exponential backoff
- Low-risk operations (reads, logs): 10% sampling

Benefits: ✅ 30-50% latency improvement without sacrificing safety
Trade-off: ❌ Small chance errors escape (mitigated by RBC checkpoints)

---

**Proposed By:** Auditor | **Date:** 2026-04-05
