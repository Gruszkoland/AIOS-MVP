# 🎯 ADR-002 IMPLEMENTATION PLAN

## Adaptive Arousal Threshold

**Status:** 🔲 PLANNED (Ready for Phase 2)  
**Target Start:** 2026-04-22 (post-ATAM workshop)  
**Target Completion:** 2026-05-15  
**Primary Owner:** Sentinel  
**Secondary Owner:** Architect  
**Effort Estimate:** 40-50 hours

---

## EXECUTIVE SUMMARY

**ADR-002 Vision:**
Replace static system Arousal threshold (currently 0.7) with adaptive, responsive threshold that:

- Learns from recent event history (1000-event window)
- Scales between 0.65-0.75 based on system load patterns
- Reduces false alarms while keeping true alerts fast
- Guardian Laws: G3 (Rhythm), G8 (Nonmaleficence)

**Expected Impact:**

- ✅ Sentinel alert responsiveness +15% (fewer false positives)
- ✅ System stability +8% (better threshold accuracy)
- ✅ Operator alert fatigue reduced
- ✅ Proof-of-concept for probabilistic mechanisms (ADR-004 prep)

---

## CURRENT STATE vs. TARGET STATE

### Current State (ADR-001 era)

```python
# arbitrage/guardian.py (LINE ~347, placeholder)
AROUSAL_THRESHOLD = 0.7  # Static constant

def assess_threat(self, event_vector):
    arousal = self.calculate_arousal(event_vector)
    if arousal > AROUSAL_THRESHOLD:  # Hardcoded check
        return "CRISIS"
    return "NORMAL"
```

**Problems:**

- ❌ Same threshold for high-load and low-load periods
- ❌ No learning from event history
- ❌ Spike in alerts during expected system surges
- ❌ No feedback loop from false alerts

### Target State (ADR-002)

```python
# arbitrage/guardian.py (NEW: ~500 lines)
class AdaptiveArousalEngine:
    """Implements G3 (Rhythm) via adaptive threshold"""

    def __init__(self):
        self.event_history = deque(maxlen=1000)  # Sliding window
        self.baseline_threshold = 0.70
        self.min_threshold = 0.65
        self.max_threshold = 0.75
        self.learning_rate = 0.01

    def assess_threat(self, event_vector):
        arousal = self.calculate_arousal(event_vector)
        adaptive_threshold = self.compute_adaptive_threshold()

        if arousal > adaptive_threshold:
            return "CRISIS"  # Triggered at right time
        return "NORMAL"

    def compute_adaptive_threshold(self):
        """
        Adjusts threshold based on:
        - Recent event intensity (mean arousal)
        - Event frequency (load)
        - False alert ratio (feedback)
        """
        if len(self.event_history) < 100:
            return self.baseline_threshold

        recent_intensity = mean(arousal for _, arousal in recent_100)
        load_factor = len(self.event_history) / 1000
        feedback_ratio = self.compute_false_alert_ratio()

        # Adaptive formula (G3: Rhythm)
        adjustment = (
            (recent_intensity * 0.4) +      # 40%: Event intensity
            (load_factor * 0.3) +            # 30%: System load
            (feedback_ratio * 0.3)           # 30%: Historical feedback
        )

        threshold = self.baseline_threshold + (adjustment * 0.1)
        return max(self.min_threshold, min(self.max_threshold, threshold))
```

**Benefits:**

- ✅ Responsive threshold that adapts to system state
- ✅ Learning from 1000-event history
- ✅ Guardian Law G3 (Rhythm) enforced
- ✅ Reduced false alerts (better operator experience)

---

## IMPLEMENTATION PHASES

### PHASE 1: Design & Specification (Week 1, 2026-04-22 to 2026-04-26)

**Duration:** ~10 hours  
**Owner:** Sentinel + Architect  
**Output:** Detailed design document + code skeleton

#### 1.1 Detailed Design Document

- [ ] **File:** `docs/ADR-002-Implementation-Design.md`
- [ ] Contents:
  - [ ] Mathematical formula for adaptive threshold (exact!)
  - [ ] Event history data structure (deque config)
  - [ ] Learning parameters (window size, learning rate)
  - [ ] Rollback strategy (if threshold goes wrong)
  - [ ] Monitoring/metrics (what to measure?)
  - [ ] Examples (concrete scenarios with numbers)

**Deliverable Checklist:**

- [ ] Formula can be explained in 2 paragraphs
- [ ] All parameters named and justified
- [ ] Edge cases documented (empty history, NaN arousal, etc.)
- [ ] Performance characteristics (O(n) for threshold calc? Caching?)

#### 1.2 Code Skeleton

- [ ] **File:** `arbitrage/adaptive_arousal.py` (new module, ~200 lines)
- [ ] Contains:
  - [ ] `AdaptiveArousalEngine` class (interface + placeholder impl)
  - [ ] `__init__()` with all parameters
  - [ ] `compute_adaptive_threshold()` (stub that returns baseline)
  - [ ] `assess_threat()` (stub)
  - [ ] Type hints for all functions
  - [ ] Docstrings with examples

- [ ] **File:** `arbitrage/guardian.py` (modify existing)
  - [ ] Import new module
  - [ ] Instantiate `AdaptiveArousalEngine`
  - [ ] Swap out static threshold check
  - [ ] Keep backward compat (fall back to 0.7 if engine errors)

#### 1.3 Test Plan

- [ ] **File:** `tests/test_adaptive_arousal.py` (skeleton)
- [ ] Test structure:
  - [ ] Unit tests for threshold calculation
  - [ ] Integration tests with guardian.py
  - [ ] Edge case tests (empty history, extreme values)
  - [ ] Performance tests (threshold calc <1ms)

**Owner's Weekly Sync Notes:**

```
Week 1 (2026-04-22):
- Design doc started (Sentinel leading)
- Formula reviewed by Architect
- Code skeleton merged to `feature/adr-002-skeleton` branch
- Pre-review checklist: 8/8 items complete ✅
- Blocker? None
```

---

### PHASE 2: Implementation (Week 2-3, 2026-04-29 to 2026-05-10)

**Duration:** ~25 hours  
**Owner:** Sentinel (implementation), Architect (code review)  
**Output:** Full implementation + unit tests

#### 2.1 Core Implementation

- [ ] **File:** `arbitrage/adaptive_arousal.py` (full implementation)

**Code Structure:**

```python
class AdaptiveArousalEngine:
    """
    Implements ADR-002: Adaptive Arousal Threshold
    Guardian Laws: G3 (Rhythm), G8 (Nonmaleficence)
    Performance: threshold_calc = O(1) amortized (cached)
    """

    def __init__(
        self,
        baseline: float = 0.70,
        min_threshold: float = 0.65,
        max_threshold: float = 0.75,
        window_size: int = 1000,
        learning_rate: float = 0.01,
    ):
        """Initialize adaptive engine with parameters"""
        pass

    def update_history(self, event: dict, arousal: float) -> None:
        """Add event to history (called after each assessment)"""
        pass

    def compute_adaptive_threshold(self) -> float:
        """Calculate adaptive threshold based on recent history"""
        # Implementation here
        pass

    def assess_threat(self, event_vector: dict) -> str:
        """Main entry point: returns 'CRISIS' or 'NORMAL'"""
        pass

    def compute_false_alert_ratio(self) -> float:
        """Calculate feedback: how many alerts were false?"""
        pass

    def get_metrics(self) -> dict:
        """Return current metrics for monitoring"""
        # threshold, event_count, false_alert_ratio, etc.
        pass
```

**Implementation Checklist:**

- [ ] `__init__()` initializes all parameters
- [ ] Event history window (deque, size 1000)
- [ ] Threshold calculation with formula
- [ ] Feedback loop (track false alerts)
- [ ] Caching (do we recalc every time or cache?)
- [ ] Error handling (NaN, empty history, etc.)
- [ ] Logging (debug-level events for troubleshooting)
- [ ] Type hints complete
- [ ] Docstrings for all public methods

#### 2.2 Integration with guardian.py

- [ ] Modify `arbitrage/guardian.py` to use `AdaptiveArousalEngine`
- [ ] Replace:

  ```python
  # OLD:
  AROUSAL_THRESHOLD = 0.7
  if arousal > AROUSAL_THRESHOLD: ...

  # NEW:
  self.arousal_engine = AdaptiveArousalEngine(...)
  if arousal > self.arousal_engine.assess_threat(...): ...
  ```

- [ ] Maintain backward compatibility
  - [ ] Fallback to 0.7 if engine fails
  - [ ] Log all threshold changes
  - [ ] Metrics endpoint (for monitoring)

#### 2.3 Test Implementation

- [ ] **File:** `tests/test_adaptive_arousal.py` (full tests)

```python
class TestAdaptiveArousalEngine:
    def test_initialization(self):
        """Engine initializes with correct defaults"""
        pass

    def test_empty_history(self):
        """With <100 events, threshold = baseline"""
        pass

    def test_threshold_bounds(self):
        """Threshold stays within [0.65, 0.75]"""
        pass

    def test_threshold_increases_under_load(self):
        """High recent_intensity → threshold increases"""
        pass

    def test_false_alert_feedback(self):
        """False alerts reduce threshold"""
        pass

    def test_performance(self):
        """threshold_calc completes in <1ms"""
        pass

    # Edge cases
    def test_nan_arousal(self): ...
    def test_extreme_values(self): ...
    def test_rapid_fire_events(self): ...
```

**Coverage Goal:** 80%+ (enforced by CI/CD)

**Owner's Weekly Sync Notes:**

```
Week 2 (2026-04-29):
- Core implementation 60% complete
- test_empty_history passing ✅
- test_bounds failing (threshold clamping not working) 🔴
- Plan: Fix by Wed, PR ready Thu

Week 3 (2026-05-06):
- Full implementation complete
- 85% test coverage ✅
- Code review queued (5 reviewers)
- Integration with guardian.py: in progress
```

---

### PHASE 3: Integration & Testing (Week 4, 2026-05-13 to 2026-05-15)

**Duration:** ~10 hours  
**Owner:** Sentinel (final integration), QA  
**Output:** Merged to main, monitoring alerts live

#### 3.1 Integration Testing

- [ ] **File:** `tests/test_adaptive_arousal_integration.py`

```python
class TestAdaptiveArousalIntegration:
    def test_with_real_event_stream(self):
        """End-to-end: event → guardian → adaptive_arousal → alert"""
        pass

    def test_guardian_fallback_on_error(self):
        """If engine fails, reverts to static 0.7 threshold"""
        pass

    def test_metrics_endpoint(self):
        """Prometheus endpoint exposes threshold metrics"""
        pass

    def test_backwards_compatibility(self):
        """Old code paths still work"""
        pass
```

#### 3.2 Canary Deployment (Optional)

- [ ] Deploy to canary K8s pod (5% traffic)
- [ ] Monitor for 24-48h:
  - [ ] Alert rate (false positives dropped?)
  - [ ] Response time (threshold calc adds <5ms?)
  - [ ] Error rate (0%)
- [ ] Full rollout if metrics green ✅

#### 3.3 Monitoring & Observability

- [ ] **Prometheus Metrics:**

  ```python
  adaptive_arousal_threshold (gauge)          # Current threshold
  adaptive_arousal_event_count (counter)      # Total events seen
  adaptive_arousal_false_alerts (counter)     # Feedback metric
  adaptive_arousal_threshold_latency_ms (histogram)  # Calc time
  ```

- [ ] **Grafana Dashboard:**
  - Threshold over time (should see drift)
  - Event frequency (correlated with threshold)
  - Alert rate (should decrease)

- [ ] **Alerts:**
  - Threshold outside bounds (0.65-0.75) → page Sentinel
  - Threshold calc >10ms → investigate performance

---

## CODE REVIEW CHECKLIST (for Reviewers)

**Guardian Laws Compliance:**

- [ ] G3 (Rhythm): Does threshold respond to system rhythm/load? ✅
- [ ] G8 (Nonmaleficence): Are false alerts minimized (not causing harm)? ✅

**Code Quality:**

- [ ] Type hints complete
- [ ] Docstrings present (context, params, return)
- [ ] Error handling (NaN, empty history, etc.)
- [ ] No hardcoded constants (all parameters)
- [ ] Logging at DEBUG level (for troubleshooting)

**Performance:**

- [ ] Threshold calculation <1ms (measured?)
- [ ] Memory usage with 1000-event window reasonable? (~1MB?)
- [ ] No O(n) loops in hot path

**Tests:**

- [ ] Coverage ≥80%
- [ ] Happy path tests
- [ ] Edge case tests (empty history, extreme values)
- [ ] Integration tests

**Documentation:**

- [ ] ADR-002 implementation notes in code?
- [ ] Guardian Laws referenced?
- [ ] 162D Decision Space mapping?

---

## DEPENDENCY MAP

**Blockers (must complete before ADR-002):**

- ✅ ADR-001 (DSPy MoE Gating) — Already implemented
- ✅ Python 3.11 environment — Available
- ✅ CI/CD pipeline (adr-check.yml) — Ready

**Enables (ADR-002 enables these):**

- ⏳ ADR-003 (TSPA Granularity) — Uses similar learning mechanisms
- ⏳ ADR-004 (Probabilistic SAV) — Proof-of-concept for probabilistic logic
- ⏳ ADR-008 (EBDI Calibration) — Uses personality health metrics

**Parallel Work (can happen simultaneously):**

- ⏳ ADR-005, ADR-007, ADR-010 (non-dependent)

---

## RISK MITIGATION

| Risk                                   | Probability | Impact     | Mitigation                                    |
| -------------------------------------- | ----------- | ---------- | --------------------------------------------- |
| **Formula too complex**                | Med (3/5)   | Med (3/5)  | Start with simple (intensity + load), iterate |
| **Performance regression**             | Low (2/5)   | High (4/5) | Benchmark threshold_calc, gate on <1ms        |
| **False alert ratio hard to measure**  | Med (3/5)   | Low (2/5)  | Start with manual tracking, automate later    |
| **Guardian integration points missed** | Low (2/5)   | Med (3/5)  | Code review checklist includes G3, G8         |
| **Test coverage insufficient**         | Low (2/5)   | High (4/5) | CI/CD enforces 80%+, review coverage.json     |

---

## SUCCESS CRITERIA

✅ **ADR-002 is successful if:**

**Functional:**

- [ ] Adaptive threshold calc returns value in [0.65, 0.75]
- [ ] Threshold responds to system load (increases under high load)
- [ ] False alert ratio improves by ≥5%
- [ ] Zero crashes/errors in production

**Code Quality:**

- [ ] Test coverage ≥80%
- [ ] All 15 unit tests passing
- [ ] Code review: 2 approvals (Architect + Auditor)
- [ ] Type hints complete

**Operational:**

- [ ] Prometheus metrics live
- [ ] Grafana dashboard deployed
- [ ] Linked in docs/ as reference implementation
- [ ] No support tickets about "alerts too noisy"

**Guardian Laws:**

- [ ] G3 (Rhythm) enforced ✅
- [ ] G8 (Nonmaleficence) honored ✅

---

## TIMELINE (Locked)

| Date       | Milestone                     | Owner     | Status     |
| ---------- | ----------------------------- | --------- | ---------- |
| 2026-04-15 | ATAM Workshop                 | All       | 🔲 Planned |
| 2026-04-22 | Phase 1: Design doc           | Sentinel  | 🔲 Planned |
| 2026-04-26 | Code skeleton PR              | Sentinel  | 🔲 Planned |
| 2026-04-29 | Phase 2: Implementation start | Sentinel  | 🔲 Planned |
| 2026-05-07 | Phase 2: 80% done             | Sentinel  | 🔲 Planned |
| 2026-05-10 | Phase 3: Integration testing  | QA        | 🔲 Planned |
| 2026-05-13 | Code review final             | Architect | 🔲 Planned |
| 2026-05-15 | **Merged to main**            | DevOps    | 🔲 Planned |
| 2026-05-20 | Post-implementation review    | Team      | 🔲 Planned |

---

## EFFORT BREAKDOWN

**Total: 40-50 hours**

| Phase     | Activity            | Hours    | Owner               |
| --------- | ------------------- | -------- | ------------------- |
| 1         | Design doc          | 8        | Sentinel            |
| 1         | Code skeleton       | 4        | Sentinel            |
| 2         | Full implementation | 20       | Sentinel            |
| 2         | Test implementation | 8        | Sentinel            |
| 3         | Integration testing | 5        | QA                  |
| Reviews   | Code review         | 4        | Architect + Auditor |
| **Total** |                     | **~50h** |                     |

**Per person:**

- Sentinel: 40h (design + code + tests)
- Architect: 4h (reviews)
- QA: 5h (integration tests)
- Auditor: 1h (compliance review)

---

## NEXT ACTIONS (Immediate)

1. **Confirm ADR-002 as first priority** (ATAM workshop should validate)
2. **Assign Sentinel as lead** (confirm availability 2026-04-22 to 2026-05-15)
3. **Schedule kick-off meeting** (2026-04-22, 30 min) with Sentinel + Architect
4. **Reserve code reviewer slots** (Architect + Auditor + 1 senior)
5. **Create GitHub milestone** (ADR-002, due 2026-05-15)
6. **Prepare design template** (share for Week 1 completion)

---

## SIGN-OFF

**Status:** ✅ **READY FOR PHASE 2 KICKOFF**

When ATAM workshop confirms ADR-002 priority:

- Extend this plan to full 50-page sprint spec
- Schedule Sentinel → Team design review (2026-04-22)
- Create GitHub issues for each phase

**Generated By:** MASTER ORCHESTRATOR v4.0  
**Plan Confidence:** 85% (depends on ATAM workshop validation)  
**Next Review:** 2026-04-15 (Post-ATAM)  
**Approval:** Ready for implementation green light
