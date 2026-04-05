# ADR-003: TSPA Granularity Tuning (Trust Score Model)

## Status
- [ ] Proposed

## Context
Current TS adjustment: +0.05 (success) / -0.20 (failure).
This creates rapid TS fluctuations → unpredictable agent inclusion/exclusion.

## Decision
Implement hybrid granularity model:
- Base decay: -0.02/week (natural confidence erosion)
- Event amplification: ×2 for security failures, ×0.5 for trivial errors
- Recovery path: +0.01/day (if no new errors)

## Consequences
✅ Smoother TS curves, stable agent team
✅ Security failures penalized harder (G8)
❌ Slower bad actor detection

## Guardian Laws Impact
G6 (Authenticity): High | G8 (Nonmaleficence): Critical

---

**Proposed By:** Healer | **Date:** 2026-04-05
