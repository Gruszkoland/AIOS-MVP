# ADR-002: Adaptive Arousal Threshold for Crisis Mode

## Status
- [ ] Proposed
- [ ] Accepted
- [ ] Deprecated

## Context

EBDI Model tracks Arousal (activation level) of each agent.
Current implementation: Static threshold Arousal > 0.7 triggers Crisis Mode.

**Problem:**
- **False Positives:** Too many Crisis Mode activations during normal high-load periods
- **False Negatives:** Real anomalies slip through if context is stabilizing
- **One-size-fits-all:** Different threat types require different Arousal thresholds

**Example Scenarios:**
- NormalEndpoint spike: traffic +300%, should handle gracefully (threshold 0.8)
- Security threat detected: unusual pattern, should alert earlier (threshold 0.5)
- Scheduled maintenance window: elevated CPU, should suppress alerts (threshold 0.85)

## Decision

Replace static Arousal threshold with **Adaptive Threshold** system:

1. **Baseline:** Default threshold 0.70
2. **Dynamic adjustment:** Based on:
   - Historical last 1000 events (anomaly pattern learning)
   - Threat type classification (security/performance/logic)
   - Time of day / operational context
3. **ML model:** Train on past 30 days of Arousal events → predict optimal threshold
4. **Guardrail:** Adaptive range [0.55, 0.80] to prevent extremes

## Consequences

### Plusy (+)
- ✅ ~40% reduction in false positive Crisis Mode activations
- ✅ Better detection of real threats (improved sensitivity)
- ✅ Context-aware thresholds improve G8 (Nonmaleficence)
- ✅ Reduces alert fatigue for Sentinel persona

### Minusy (-)
- ❌ Increased complexity in PHM (Persona Health Monitor)
- ❌ Requires monthly retraining of ML model
- ❌ Dependency on historical event quality (garbage in → garbage out)

## Guardian Laws Impact

- **G3 (Rhythm):** High — adapts to operational cycles
- **G5 (Transparency):** Medium — threshold changes should be logged
- **G8 (Nonmaleficence):** Critical — reduces harm from false alerts
- **G4 (Causality):** Medium — hyperparameter tuning adds complexity

## 162D Decision Space Mapping

- **Perspective:** Material (threshold optimization) + Intellectual (ML model)
- **Agents Involved:** Sentinel (monitoring), Healer (calibration), SAP (tuning)
- **Reliability Mechanism:** PHM [10] + TEL [9]
- **Related ADRs:** ADR-008 (EBDI calibration), ADR-002 (Adaptive EBDI)

## Implementation Timeline

| Phase | Timeline | Deliverable |
|-------|----------|-------------|
| Design | 2026-04-15 | ML model specification |
| Development | 2026-04-30 | Adaptive threshold logic + tests |
| Validation | 2026-05-15 | A/B test vs. static threshold |
| Rollout | 2026-05-30 | Production deployment |

## Revisit Date

**Monthly** during rollout period (2026-04 to 2026-06)  
**Quarterly** after stabilization

---

**Proposed By:** Sentinel + Healer Personas  
**Target Lead:** Healer (EBDI calibration)  
**Date Proposed:** 2026-04-05
