# ⚙️ SAP PRE-WORKSHOP DELIVERABLES

**Prepared:** 2026-04-06
**For Workshop:** 2026-04-15
**Persona:** SAP (System & Architecture Planning)

---

## SECTION 1: ADR DEPENDENCY GRAPH (Detailed)

```
LAYER 1: ARCHITECTURE FOUNDATION
┌─────────────────────────────────┐
│ ADR-001: MoE Routing (6 agents) │ ⭐ START HERE
│ Context: Single LLM → Multi-Agent│
│ Impact: Enables reasoning diversity
│ Effort: 40h (research + implementation)
│ Risk: Agent coordination complexity
└─────────────────────────────────┘
         ├──────────────────────────┬──────────────────────────┬──────────────────────┐
         │                          │                          │                      │
   ┌─────▼──────┐           ┌──────▼───────┐         ┌────────▼──────┐    ┌────────▼──────┐
   │  ADR-002   │           │   ADR-005    │         │   ADR-003     │    │   ADR-007    │
   │ Adaptive   │           │ DSPy Sigs    │         │ Resolver      │    │  RBC Store   │
   │ Arousal    │           │ (Enabler)    │         │ (Consensus)   │    │ (Recovery)   │
   │ 30h | MED  │           │ 15h | LOW    │         │ 35h | HIGH    │    │ 25h | MED    │
   └─────┬──────┘           └──────────────┘         └─────┬────────┘    └──────────────┘
         │                                                   │
         │ requires health signals                           │ depends on agent isolation
         │                                                   │
   ┌─────▼──────────┐                               ┌──────▼───────────┐
   │  ADR-008       │                               │   ADR-010        │
   │ EBDI           │                               │ Genesis Record   │
   │ Calibration    │                               │ (Audit Trail)    │
   │ 20h | MED      │                               │ 20h | HIGH       │
   └────────────────┘                               └──────────────────┘

PARALLEL TRACK: CRITICAL COMPLIANCE
                    ┌──────────────────────┐
                    │  ADR-009: Privacy    │
                    │  Shield (G7)         │
                    │  25h | CRITICAL      │
                    └──────────┬───────────┘
                               │ feeds audit trail to
                               │
                    ┌──────────▼───────────┐
                    │  ADR-010: Genesis    │
                    │  Record (Logging)    │
                    │  20h | HIGH          │
                    └──────────────────────┘

OPTIONAL/LATER
    ┌─────────────────┐    ┌──────────────────┐
    │  ADR-004        │    │  ADR-006         │
    │  Prob. SAV      │    │  Quantum         │
    │  (Quality Gate) │    │  Amplitude       │
    │  15h | OPT      │    │  (Research)      │
    └─────────────────┘    │  30h | RESEARCH  │
                           └──────────────────┘
```

**Critical Path (Longest Lead):**
ADR-001 (40h) → ADR-002 (30h) → ADR-008 (20h) = **90h minimum**

**Parallel Work:** ADR-009 + ADR-010 can start immediately (20h + 20h = 40h, parallel)

**Total Effort (All 10 ADRs):** **275 hours**

---

## SECTION 2: RESOURCE ALLOCATION MATRIX

| ADR | Title               | Priority     | Effort (h) | Owner               | Dependencies     | Parallel-Safe? | Sprint     |
| --- | ------------------- | ------------ | ---------- | ------------------- | ---------------- | -------------- | ---------- |
| 001 | MoE Routing         | **CRITICAL** | 40         | Architect           | None             | ✓              | S1 (W1-2)  |
| 002 | Adaptive Arousal    | **CRITICAL** | 30         | Architect + SAP     | ADR-001          | ✓              | S1 (W2-3)  |
| 003 | Conflict Resolution | HIGH         | 35         | Architect + Healer  | ADR-001, ADR-002 | ✓              | S2 (W4-5)  |
| 004 | Probabilistic SAV   | MEDIUM       | 15         | Auditor             | ADR-001, ADR-002 | ✓              | S3 (W6+)   |
| 005 | DSPy Signatures     | LOW          | 15         | Librarian           | ADR-001          | ✓              | S1 (W2)    |
| 006 | Quantum Amplitude   | RESEARCH     | 30         | SAP (research only) | None             | ✓ (pilot)      | S4 (pilot) |
| 007 | RBC Checkpointing   | **CRITICAL** | 25         | Healer + DevOps     | ADR-001          | ✓              | S1 (W1-2)  |
| 008 | EBDI Calibration    | **CRITICAL** | 20         | SAP + Healer        | ADR-002, ADR-007 | ✓              | S1 (W3)    |
| 009 | Privacy Shield      | **CRITICAL** | 25         | Auditor + Librarian | None             | ✓              | S1 (W1-2)  |
| 010 | Genesis Record      | **CRITICAL** | 20         | Librarian           | ADR-005, ADR-009 | ✓              | S1 (W2-3)  |

**Legend:**

- **W1-6 = Weeks 1-6** (after workshop approval)
- **S1-4 = Sprints 1-4** (2-3 weeks per sprint)
- **All effort = pair-programming estimates** (2 people, synchronous)

---

## SECTION 3: DETAILED TIMELINE (2-Week Sprints)

```
SPRINT 1: Weeks 1-2 (May 1-14, 2026)
┌──────────────────────────────────────────────────────────────┐
│ WEEK 1 (May 1-7)                                             │
│ ├─ Mon: Kickoff + Environment setup (dev/test/prod)         │
│ ├─ Tue-Wed: ADR-001 design review + proof-of-concept         │
│ │           (MoE routing skeleton, 6 agents stubbed)         │
│ ├─ Thu: ADR-007 (RBC) design + checkpoint schema             │
│ ├─ Thu-Fri: ADR-009 (Privacy Shield) spec + legal review     │
│ │           (required before code!)                          │
│ └─ Fri: All team standup, blockers assessment                │
│                                                              │
│ WEEK 2 (May 8-14)                                            │
│ ├─ Mon-Tue: ADR-001 implementation (agent scaffold)          │
│ ├─ Mon-Tue: ADR-009 implementation (redaction logic)         │
│ ├─ Tue-Wed: ADR-010 setup (Genesis Record JSON schema)       │
│ ├─ Wed-Thu: ADR-002 research (Arousal thresholds)            │
│ ├─ Thu: Code review + merge ADR-001, ADR-009, ADR-010       │
│ └─ Fri: Integration test + demo to stakeholders              │
│                                                              │
│ ✓ DONE: ADR-001, ADR-007 (setup), ADR-009, ADR-010          │
│ ✓ BLOCKED: ADR-002 (awaits ADR-001 agents)                  │
│ ⏳ IN PROGRESS: ADR-005 (DSPy contracts)                     │
└──────────────────────────────────────────────────────────────┘

SPRINT 2: Weeks 3-4 (May 15-28, 2026)
┌──────────────────────────────────────────────────────────────┐
│ WEEK 3 (May 15-21)                                           │
│ ├─ Mon-Tue: ADR-002 implementation (Arousal baseline)        │
│ ├─ Tue-Wed: ADR-008 calibration (EBDI telemetry)            │
│ ├─ Wed: ADR-007 checkpoint persistence (SQLite schema)       │
│ ├─ Thu: Code review + merge ADR-002, ADR-008, ADR-007       │
│ └─ Fri: Stress test (1000 concurrent tasks → RBC recovery)   │
│                                                              │
│ WEEK 4 (May 22-28)                                           │
│ ├─ Mon-Tue: ADR-003 (Conflict Resolver) design + prototype   │
│ ├─ Tue-Wed: ADR-005 (DSPy Signatures) full rollout           │
│ ├─ Wed-Thu: Integration: ADR-002 + ADR-003 conflict voting   │
│ ├─ Thu: Code review + merge ADR-003, ADR-005                │
│ └─ Fri: E2E test: Crisis scenario (Healer + Sentinel + CR)   │
│                                                              │
│ ✓ DONE: ADR-001-010 (excluding ADR-006 research)            │
│ ⏳ PARALLEL: ADR-006 (Quantum) started as pilot              │
│ ✓ GATE: All unit tests >80%, integration tests >70%          │
└──────────────────────────────────────────────────────────────┘

SPRINT 3: Weeks 5-6 (May 29 — June 11, 2026)
┌──────────────────────────────────────────────────────────────┐
│ WEEK 5-6: Hardening + Documentation                          │
│ ├─ Performance optimization (target: <500ms E2E latency)      │
│ ├─ Load testing (10K events/min sustained)                   │
│ ├─ Security audit (Trinity + Guardian Laws validation)       │
│ ├─ Documentation completeness (ADR runbooks)                 │
│ ├─ Production readiness review                               │
│ └─ Go/No-Go decision                                         │
│                                                              │
│ ✓ RELEASE CANDIDATE v1.0 (mid-June 2026)                    │
└──────────────────────────────────────────────────────────────┘
```

---

## SECTION 4: CRITICAL PATH ANALYSIS

**Sequence that MUST happen in order:**

```
START
  │
  ├─→ ADR-001 (40h) ──→ [can't proceed without agents]
  │
  ├─→ ADR-002 (30h) ──→ [can't tune health without ADR-001]
  │
  ├─→ ADR-008 (20h) ──→ [calibration needs both ADR-001 + ADR-002]
  │
  └─→ GATE before ADR-009
          │
          └─→ ADR-009 (25h) ─→ [must have Privacy before logging all decisions]
          │
          └─→ ADR-010 (20h) ─→ [Genesis logs decisions with Privacy applied]
                │
                └─→ ADR-003 (35h) [can skip if we rely on simple arbitrage]

PARALLEL (no blockers):
  • ADR-005 (DSPy) — start Week 2 (enabler, not blocker)
  • ADR-007 (RBC) — start Week 1 (infrastructure, independent)
  • ADR-004 (Prob SAV) — start Week 3 (after core tests stable)
  • ADR-006 (Quantum) — research track (no production dependency)
```

**Total Critical Path:** 40 + 30 + 20 + 25 + 20 = **135 hours** (@40h/week = ~3.4 weeks)

**With Contingency (15%):** **155 hours** (~4 weeks practical)

---

## SECTION 5: EFFORT JUSTIFICATION PER ADR

| ADR     | Estimate | Breakdown                                             | Risks                                |     Contingency |
| ------- | -------: | ----------------------------------------------------- | ------------------------------------ | --------------: |
| **001** |      40h | 10h research, 20h code, 10h testing                   | Agent isolation bugs → +5h debugging |              5h |
| **002** |      30h | 10h threshold tuning, 15h telemetry, 5h tests         | Thresholds need re-tuning → +8h      |              3h |
| **003** |      35h | 12h voting logic, 15h trust scoring, 8h tests         | Tie-breaking edge cases → +6h        |              5h |
| **004** |      15h | 8h algorithm research, 5h POC, 2h tests               | May require Monte Carlo → +5h        |              2h |
| **005** |      15h | 10h contracts design, 3h validation, 2h docs          | Schema compatibility → +4h           |              2h |
| **006** |      30h | 15h quantum research (literature), 15h POC            | Physics verification complex → +10h  | 8h (pilot only) |
| **007** |      25h | 8h checkpoint schema, 12h persistence layer, 5h tests | Durability on network failure → +6h  |              4h |
| **008** |      20h | 8h EBDI metrics, 8h calibration loop, 4h tests        | Converging baselines → +5h           |              3h |
| **009** |      25h | 10h redaction rules, 10h legal compliance, 5h tests   | Compliance finds gap → +8h           |              4h |
| **010** |      20h | 8h schema design, 8h logging infra, 4h tests          | Query performance → +5h              |              3h |

**Total Base Effort:** 275h
**Total Contingency:** 45h (16%)
**Budget:** **320 hours** (2 pair-programmers × 8 weeks)

---

## SECTION 6: RESOURCE PLAN

**Team Composition (6 people, 8 weeks):**

| Persona       | Weekly Hours | ADRs Lead                             | Role                     |
| ------------- | ------------ | ------------------------------------- | ------------------------ |
| **ARCHITECT** | 40h          | ADR-001, ADR-002, ADR-003             | Design lead              |
| **SAP**       | 40h          | ADR-002 (tuning), ADR-008 (metrics)   | Timeline + QA            |
| **AUDITOR**   | 32h          | ADR-004 (gates), ADR-009 (compliance) | Code review              |
| **SENTINEL**  | 24h          | ADR-003 (risk), ADR-008 (health)      | Testing + risk scenarios |
| **LIBRARIAN** | 32h          | ADR-005 (schemas), ADR-010 (docs)     | Documentation + runbooks |
| **HEALER**    | 32h          | ADR-007 (recovery), ADR-008 (health)  | Testing + resilience     |

**Total:** 200h/week × 2 people rotating = **400 person-hours available**
**Planned Usage:** 320h (**80% capacity**, 20% slack for interrupts)

---

## SECTION 7: MILESTONES & GO/NO-GO GATES

| Milestone                      | Date    | Success Criteria                           | Owner     |
| ------------------------------ | ------- | ------------------------------------------ | --------- |
| **M1: Architecture Approved**  | May 7   | ADR-001 PoC works, team alignment          | ARCHITECT |
| **M2: Core Services Deployed** | May 14  | ADR-001-010 merged, >80% unit tests        | LIBRARIAN |
| **M3: Integration Test Pass**  | May 21  | Crisis scenario (Healer recovery) succeeds | SENTINEL  |
| **M4: Compliance Gate**        | May 28  | Security audit passed, <3 findings         | AUDITOR   |
| **M5: Performance Baseline**   | June 4  | <500ms E2E latency, 10K events/min load    | SAP       |
| **M6: Release Candidate**      | June 11 | All gates pass, team votes GO/NO-GO        | ALL       |

---

## SECTION 8: RISK MITIGATION (Resource Planning)

| Risk                           | Probability | Impact   | Mitigation                                       | Owner              |
| ------------------------------ | ----------- | -------- | ------------------------------------------------ | ------------------ |
| Arousal tuning fails (ADR-002) | HIGH        | HIGH     | Parallel ADR-008 baseline research starts Week 1 | SAP + HEALER       |
| Agent isolation bugs (ADR-001) | MEDIUM      | HIGH     | RBC checkpointing (ADR-007) provides rollback    | ARCHITECT + HEALER |
| Compliance gap found (ADR-009) | MEDIUM      | CRITICAL | Legal pre-review before coding (Week 1)          | AUDITOR            |
| Load test fails (performance)  | LOW         | MEDIUM   | Allocate 1 week Week 7 for optimization          | SAP                |
| Team capacity gap              | LOW         | HIGH     | Cross-train 2 backup people (10% time)           | ALL                |

---

## SECTION 9: 2-SLIDE TIMELINE SUMMARY

### Slide 1: Critical Path (Waterfall)

```
May│ ADR-001 (40h)
   │  ├── ADR-002 (30h)
   │  │    └── ADR-008 (20h)
   │  │         └── ADR-009/010 (45h parallel)
   │  │              └── ADR-003 (35h optional)
   │
June│  [S1: Core] ──→ [S2: Hardening] ──→ [RELEASE]
   │   (3 weeks)        (2 weeks)
   │
   └─ PARALLEL: ADR-005, ADR-007 (throughout)
```

### Slide 2: Resource Utilization Over Time

```
  100% ┌─────────────────────────────────────────┐
       │ Team Capacity (6 people)                │
   80% │ ┌───────────────────────────────────────┤ Usage
       │ │                                       │
   60% │ │  [S1: Peak]  [S2: Sustain] [S3: Wind]│
       │ │   ADR-001-010   Hardening  Release   │
   40% │ │  ████████████ ████████ ██████       │
       │ │                                       │
    0% └─┴───────────────────────────────────────┘
        May 1      May 15      June 1      June 15
```

---

## SECTION 10: NEXT STEPS (Workshop Decision Points)

**For Workshop to Decide:**

1. **Hiring Decision:** Do we have 2 full-time engineers for 8 weeks?
   - If NO: Extend timeline to 12 weeks (reduce parallelism)

2. **Scope Reduction:** Is ADR-006 (Quantum) a go?
   - If NO: Save 30h, timeline → 6.5 weeks

3. **Pilot vs. Production:** Deploy ADR-001-010 to staging or production first?
   - Recommendation: Staging (2-week pilot), then prod rollout

4. **Third-Party Dependencies:** Do we need OpenRouter + Ollama integration before ADR-002?
   - Recommendation: Yes, parallel work starting Week 1

---

## CHECKLIST FOR SAP (by 2026-04-14)

- [x] ADR dependency graph (10 ADRs mapped)
- [x] Effort matrix (hours per ADR, per person)
- [x] 6-week timeline (sprint-by-sprint)
- [x] Critical path analysis (135h base + 45h contingency)
- [x] Resource plan (team allocation)
- [x] Milestones + go/no-go gates (6 decision points)
- [x] Risk mitigation matrix
- [x] 2-slide timeline visualizations
- [ ] **SUBMIT to Librarian by 2026-04-14 EOD**

---

**Ready for Workshop:** Yes ✅
**Questions?** Contact ARCHITECT + AUDITOR before 2026-04-08 for scope validation.
