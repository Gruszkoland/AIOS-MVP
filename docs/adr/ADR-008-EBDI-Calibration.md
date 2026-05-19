# ADR-008: EBDI Calibration Framework

## Status
- [ ] Proposed

## Decision
Standardize EBDI (Pleasure/Arousal/Dominance) baseline calibration:
- **Baseline per persona:** Defined in config/personas.yml
- **Measurement:** Per-operation scoring (0.0-1.0 scale)
- **Anomaly detection:** Deviation >3 steps from baseline triggers PHM
- **Recovery:** Identity Reset after 3 consecutive anomalies

Benefits: ✅ Predictable persona behavior | ✅ Early anomaly detection
Trade-off: ❌ Requires manual periodic re-calibration

---

**Proposed By:** Healer | **Date:** 2026-04-05
