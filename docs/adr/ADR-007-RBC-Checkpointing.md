# ADR-007: RBC Checkpoint Timing

## Status
- [ ] Proposed

## Decision
Optimize Rollback Checkpoint (RBC-3) frequency:
- **Automatic checkpoints:** Every 5 steps (or after destructive operations)
- **Manual savepoint:** User can trigger `/rollback` at any time
- **Storage:** Git stash + session JSON snapshot in /memories/session/
- **Retention:** Keep last 10 checkpoints (auto-cleanup older than 24h)

Benefits: ✅ Granular recovery points | ✅ Zero storage bloat
Trade-off: ❌ Git operations add ~100ms each

---

**Proposed By:** Healer Persona | **Date:** 2026-04-05
