# 📅 PHASE 2 MASTER TIMELINE & ROADMAP

**Status:** 🔲 PLANNED (Ready to execute post-ATAM workshop)  
**Phase 2 Duration:** 16 weeks (Q2-Q3 2026: Apr 8 — Jul 31, 2026)  
**Generated:** 2026-04-05  
**Current Date:** 2026-04-05 (10 days to ATAM kick-off)

---

## EXECUTIVE SUMMARY

**Phase 2 Mission:**
Implement ADR-002 through ADR-010 (9 remaining ADRs) with rigorous quality gates, moving ADRION 369 from 10% to ~65% ADR coverage.

**Timeline Scope:** Apr 8 (distribution) → Jul 31, 2026 (Phase 2 complete)

**Key Metrics:**

- Start: 1 ADR accepted (ADR-001), 9 proposed
- End: 6-7 ADRs implemented + accepted, 2-3 in review
- Coverage: 10% → 65%+
- Code Coverage: 80%+ maintained throughout
- Guardian Laws: 9/9 (100%)

---

## CRITICAL PATH (What Must Happen & When)

```
Week 1 (Apr 8-12)        : ATAM Prep (all personas)
├─ Apr 15 (MON)          : ATAM WORKSHOP (3-4 hrs, locked date)
├─ Apr 22 (MON)          : ADR-002 Kickoff (design start)
├─ May 1 (THU)           : ADR-002 (Phase 1 design done), ADR-003 kickoff
├─ May 15 (THU)          : ADR-002-003 merged, ADR-004-007 in progress
├─ Jun 15 (SUN)          : ADR-004-009 in review, ADR-010 design
└─ Jul 15 (TUE)          : Phase 2 COMPLETE (all 9 ADRs in review/implemented)
```

---

## WEEK-BY-WEEK BREAKDOWN

### 📍 PRE-PHASE 2: April 5-14, 2026

**Week Ending Apr 12:**

| Day    | Activity                         | Owner     | Duration | Output                       |
| ------ | -------------------------------- | --------- | -------- | ---------------------------- |
| Mon 8  | Setup ATAM materials             | Librarian | 2h       | Shared doc, agenda confirmed |
| Tue 9  | Persona pre-reading (individual) | All       | 2-3h     | Prep deliverables            |
| Wed 10 | Architect pre-workshop check     | Architect | 1h       | Slide deck ready             |
| Thu 11 | SAP timeline validation          | SAP       | 1h       | Roadmap sanity check         |
| Fri 12 | Attendance confirmation          | All       | 30m      | RSVP locked (6/6)            |

**Deliverables by EOD Apr 12:**

- ✅ Workshop agenda finalized
- ✅ Shared document created + access tested
- ✅ All personas confirmed attendance
- ✅ Pre-reading materials distributed

**Blocking Issues:** None yet expected

---

### 🎯 **ATAM WORKSHOP WEEK: April 15-19, 2026**

**Mon Apr 15 (LOCKED):**

| Time (UTC)      | Block                               | Duration   | Owner               | Output                             |
| --------------- | ----------------------------------- | ---------- | ------------------- | ---------------------------------- |
| 09:00-09:45     | **BLOCK 1:** Context                | 45m        | Architect           | Current state reviewed             |
| 09:45-10:45     | **BLOCK 2:** Attributes & Scenarios | 60m        | Architect + Auditor | Quality attributes + 5-8 scenarios |
| **10:45-11:00** | **BREAK**                           | 15m        | —                   | Bathroom, coffee ☕                |
| 11:00-12:00     | **BLOCK 3:** Trade-offs & Risk      | 60m        | Sentinel + SAP      | Risk register (20+ items)          |
| 12:00-12:45     | **BLOCK 4:** Roadmap & Planning     | 45m        | SAP + Healer        | ADR sequence locked                |
| 12:45-13:00     | **WRAP-UP**                         | 15m        | Librarian           | Action items assigned              |
| **Total**       |                                     | **3h 45m** |                     | **All deliverables captured**      |

**Post-Workshop (Tue-Fri Apr 16-19):**

| Date         | Deliverable                               | Owner     | Due |
| ------------ | ----------------------------------------- | --------- | --- |
| Tue 16 (EOD) | Workshop summary doc                      | Librarian | 📋  |
| Wed 17 (EOD) | Risk register finalized + prioritized     | Sentinel  | 📋  |
| Thu 18 (EOD) | ADR sequence validated                    | SAP       | 📋  |
| Fri 19 (EOD) | ATAM-Progress.json updated (Phase 2 data) | Librarian | 📋  |

**Blocking Issues to Resolve This Week:**

- ? Schedule conflict for any persona?
- ? Risk register captured completely?
- ? ADR sequence has organizational buy-in?

---

### 🚀 **FIRST SPRINT: April 22 - May 3, 2026**

**Focus: ADR-002 (Adaptive Arousal) Design Phase**

#### Week 1 (Apr 22-26)

| Day    | Task                            | Owner                | Hours | Status |
| ------ | ------------------------------- | -------------------- | ----- | ------ |
| Mon 22 | ADR-002 kickoff (30m)           | Sentinel + Architect | 0.5h  | 🔲     |
| Mon 22 | Design doc started              | Sentinel             | 4h    | 🔲     |
| Tue 23 | Design review meeting           | Architect            | 1h    | 🔲     |
| Wed 24 | Code skeleton PR submitted      | Sentinel             | 3h    | 🔲     |
| Thu 25 | Code review (skeleton)          | Architect + Auditor  | 2h    | 🔲     |
| Fri 26 | Design doc finalized + approved | Sentinel             | 2h    | 🔲     |

**Deliverables EOD Apr 26:**

- ✅ Design doc complete (formula, params, edge cases)
- ✅ Code skeleton PR merged
- ✅ Test plan written
- ✅ Ready for Phase 2 (implementation)

**Metrics to Track:**

- Design doc % complete
- Code skeleton tests passing
- PR review turnaround time

**Blocking Issues?**

- None expected (skeleton is low-risk)

---

#### Week 2 (Apr 29 - May 3)

| Day       | Task                               | Owner    | Hours | Status |
| --------- | ---------------------------------- | -------- | ----- | ------ |
| Mon 29    | Phase 2 implementation starts      | Sentinel | 6h    | 🔲     |
| Tue 30    | Core logic implemented (50%)       | Sentinel | 6h    | 🔲     |
| Wed 1 May | Test suite started                 | Sentinel | 4h    | 🔲     |
| Thu 2     | Implementation 80% complete        | Sentinel | 6h    | 🔲     |
| Fri 3     | Code checkpoint + metrics baseline | Sentinel | 2h    | 🔲     |

**Deliverables EOD May 3:**

- ✅ ADR-002 core implementation ~80% complete
- ✅ Unit tests started (50%+ passing)
- ✅ No blockers for integration week

**Cumulative Effort So Far:**

- Sentinel: 36h (design 12h + implementation 24h)
- Architect: 4h (reviews)
- QA: 0h (integration next week)

---

### 🔗 **SECOND SPRINT: May 6-17, 2026**

**Focus: ADR-002 Completion + ADR-003 Setup**

#### Week 3 (May 6-10)

| Day    | Task                            | Owner     | Hours | Status |
| ------ | ------------------------------- | --------- | ----- | ------ |
| Mon 6  | ADR-002 implementation complete | Sentinel  | 6h    | 🔲     |
| Tue 7  | Full test coverage (aim 85%+)   | Sentinel  | 5h    | 🔲     |
| Wed 8  | Integration testing starts      | QA        | 4h    | 🔲     |
| Thu 9  | Code review rounds 1-2          | Architect | 3h    | 🔲     |
| Fri 10 | Fixes + final review            | Sentinel  | 4h    | 🔲     |

**Deliverables EOD May 10:**

- ✅ ADR-002 99% ready (in code review queue)
- ✅ Test coverage 85%+
- ✅ Integration tests passing
- ✅ ADR-003 kickoff scheduled

**Parallel Activity (May 8-10):**

- ADR-003 (TSPA Granularity) design doc in progress (Auditor leading)

**Status Update: ADR-002**

- Phase 1 (Design): 100% ✅
- Phase 2 (Implementation): 95% ✅
- Phase 3 (Integration): 80% ✅
- Merge Target: May 15

---

#### Week 4 (May 13-17)

| Day        | Task                          | Owner               | Hours | Status |
| ---------- | ----------------------------- | ------------------- | ----- | ------ |
| Mon 13     | ADR-002 final review          | Architect + Auditor | 2h    | 🔲     |
| Tue 14     | ADR-002 approved for merge    | DevOps              | 1h    | 🔲     |
| **Wed 15** | **ADR-002 MERGED TO MAIN** 🎉 | DevOps              | 0.5h  | 🔲     |
| Wed 15     | ADR-003 implementation starts | Auditor             | 6h    | 🔲     |
| Thu 16     | ADR-004 design review         | Architect           | 2h    | 🔲     |
| Fri 17     | Post-merge monitoring (24h)   | Sentinel + Ops      | 4h    | 🔲     |

**Deliverables EOD May 17:**

- ✅ **ADR-002 LIVE in production** (canary 5% → 20% rollout)
- ✅ Monitoring shows no regression (false alert rate stable/down)
- ✅ ADR-003 implementation ~60% complete
- ✅ ADR-004 design ready

**Cumulative Team Effort by May 17:**

- Sentinel: 57h
- Architect: 14h
- QA: 8h
- Auditor: 3h
- Total: 82h (of 275h estimated for all 9 ADRs)

**ADR Coverage Update:** 2/10 (20%)

---

### 🏃‍♂️ **THIRD SPRINT: May 20 - May 31, 2026**

**Focus: ADR-003 + ADR-004 + ADR-007 (parallel work, non-dependent)**

#### Week 5 (May 20-24)

**ADR-003 (TSPA):** Implementation phase (Auditor leading)

- Design: 100% ✅
- Implementation: 60% → 95% by Fri
- Review: Starts Thu
- Owner: Auditor (40h total)

**ADR-004 (Probabilistic SAV):** Design phase (Architect leading)

- Design doc draft by Wed
- Review Thu-Fri
- Owner: Architect (30h total)

**ADR-007 (RBC Checkpointing):** Kickoff phase (Sentinel leading)

- Design starts Wed
- Owner: Sentinel (30h total)

| Day    | ADR-003       | ADR-004          | ADR-007       |
| ------ | ------------- | ---------------- | ------------- |
| Tue 20 | Impl 70%      | Design review    | Kickoff prep  |
| Wed 21 | Impl 85%      | Design done      | Design starts |
| Thu 22 | Code review 1 | Code skeleton    | Design 40%    |
| Fri 23 | Fixes         | Code skeleton PR | Design 70%    |

**EOD May 24:**

- ADR-003: 90% complete, ready for final review
- ADR-004: Skeleton PR, tests started
- ADR-007: Design doc 70% done

---

#### Week 6 (May 27-31)

| Day    | ADR-003            | ADR-004       | ADR-007       | ADR-005 Kickoff |
| ------ | ------------------ | ------------- | ------------- | --------------- |
| Mon 27 | Final review       | Impl 50%      | Design 100%   | Design brief    |
| Tue 28 | MERGED 🎉          | Impl 70%      | Code skeleton | Design starts   |
| Wed 29 | Post-merge monitor | Impl 90%      | Tests started | Design 30%      |
| Thu 30 | Rollout 20%→50%    | Code review 1 | Tests 60%     | Design 60%      |
| Fri 31 | Monitoring         | Fixes         | Tests 90%     | Design 100%     |

**EOD May 31:**

- **ADR-003 MERGED** (coverage: 3/10 = 30%) ✅
- ADR-004 99% complete, in review
- ADR-007 85% complete, tests in progress
- ADR-005 design ready for code skeleton

---

### 📈 **FOURTH SPRINT: June 3-21, 2026**

**Focus: Sustained momentum - ADR-004, ADR-007 merge + ADR-005-006 progress**

#### Week 7 (June 3-7)

**Merges Expected:**

- ADR-004 (Probabilistic SAV) — Wed 5 📊
- ADR-007 (RBC Checkpointing) — Thu 6 📊

**In Progress:**

- ADR-005 (Genesis Tiering) — 50% impl
- ADR-006 (Arbitrium Consensus) — Design 80%
- ADR-008 (EBDI Calibration) — Kickoff prep

**Status:**

- ADR Coverage: 5/10 (50%) by Friday
- All ADRs drafted → All ADRs have owners

---

#### Week 8-9 (June 10-21)

**ADR-005 & ADR-006:** Implementation + review cycle

- ADR-005 (Genesis Tiering): 50% → design locked by Jun 15
- ADR-006 (Arbitrium Consensus): Impl 60% by Jun 15

**New Kickoffs:**

- ADR-008 (EBDI Calibration): Jun 12
- ADR-009 (Privacy Shield): Jun 12 (EARLY! Complex, needs time)

**Rollout Progress:**

- ADR-002: 100% (full rollout)
- ADR-003: 80% (ramping to 100%)
- ADR-004: Canary 5%
- ADR-007: Canary 5%

**EOD June 21:**

- ADR Coverage: 5/10 merged, 2 in review
- ADR-005, ADR-006 design locked
- ADR-008, ADR-009 ~30% impl each

---

### 🎯 **FINAL SPRINT: June 24 - July 15, 2026**

**Focus: Finish line - Complete remaining ADRs, hit 65%+ coverage**

#### Week 10 (June 24-28)

**Merges Expected:**

- ADR-005 (Genesis Tiering) — Jun 26 📊
- ADR-006 (Arbitrium Consensus) — Jun 27 📊

**In Progress:**

- ADR-008 (EBDI Calibration) — 70% impl
- ADR-009 (Privacy Shield) — 50% impl (complex, needs focus)
- ADR-010 (Sustainability) — Kickoff

**Status:**

- ADR Coverage: 7/10 (70%) by end of week ✅

---

#### Week 11-12 (July 1-15)

**Final Push:**

- ADR-008: Impl → Review → Merge by Jul 5 ✅
- ADR-009: Impl → Review → Merge by Jul 13 (might slip to Jul 20)
- ADR-010: Impl → Review → Merge by Jul 15 (might slip to Jul 20)

**Phase 2 FINAL STATUS (Jul 15):**

| ADR | Status         | Merge Date       | Coverage  |
| --- | -------------- | ---------------- | --------- |
| 001 | ✅ Implemented | Apr 5 (baseline) | 10%       |
| 002 | ✅ Implemented | May 15           | 20%       |
| 003 | ✅ Implemented | May 28           | 30%       |
| 004 | ✅ Implemented | Jun 5            | 40%       |
| 005 | ✅ Implemented | Jun 7            | 50%       |
| 006 | ✅ Implemented | Jun 27           | 60%       |
| 007 | ✅ Implemented | Jun 6            | 70%       |
| 008 | ✅ Implemented | Jul 5            | 80%       |
| 009 | 🔄 In Review   | Jul 13-20        | (80-90%)  |
| 010 | 🔄 In Review   | Jul 15-20        | (90-100%) |

**Phase 2 Completion: ~80% ADRs merged + live**  
_Note: ADR-009-010 might slip into early Phase 3 (post-Jul 15)_

---

## MILESTONE DATES (Locked)

| Date               | Milestone                         | Status  |
| ------------------ | --------------------------------- | ------- |
| **2026-04-15 MON** | ✅ ATAM Workshop (3-4h)           | LOCKED  |
| 2026-04-22 MON     | ADR-002 Kickoff                   | Planned |
| **2026-05-15 WED** | ADR-002 MERGED                    | Target  |
| 2026-05-28 WED     | ADR-003 MERGED                    | Target  |
| 2026-06-05 WED     | ADR-004 + ADR-007 MERGED          | Target  |
| 2026-06-27 THU     | ADR-005 + ADR-006 MERGED          | Target  |
| **2026-07-05 SAT** | Quarterly ATAM Review (Phase 2.5) | Locked  |
| 2026-07-15 TUE     | Phase 2 COMPLETE                  | Target  |
| 2026-07-20 SUN     | ADR-009-010 final merge           | Target  |
| 2026-10-05 SUN     | Quarterly ATAM Review (Phase 3)   | Locked  |

---

## PARALLEL WORKSTREAMS

### 📊 Monitoring & Observability (Continuous)

**Owned by:** Sentinel + Ops (per-milestone)

**Deliverables per milestone:**

- [ ] Prometheus dashboards updated (new metrics)
- [ ] Grafana alerts configured
- [ ] Runbooks updated (remediation paths)
- [ ] Team trained on new monitoring

**Effort:** ~3-4h per ADR merge

---

### 📋 Documentation & Knowledge Transfer (Continuous)

**Owned by:** Librarian (per-milestone)

**Deliverables per ADR:**

- [ ] ADR implementation notes (code → doc link)
- [ ] Runbook for the feature
- [ ] Guardian Laws audit trail
- [ ] 162D Decision Space update
- [ ] Monthly adoption tracker

**Effort:** ~2-3h per ADR merge

---

### 🧪 Quality Assurance (Per-milestone)

**Owned by:** QA + Architects

**Deliverables per ADR:**

- [ ] Integration test suite (Guardian Laws enforceable?)
- [ ] Canary metrics (false alert rate, latency, errors)
- [ ] Rollout health check (monitoring alerts green?)
- [ ] Regression test (old features still work?)

**Effort:** ~2-3h per ADR

---

## RESOURCE ALLOCATION (Full Sprint)

### By Persona (Weekly Hours)

| Persona       | Apr     | May     | Jun     | Jul     | Total    |
| ------------- | ------- | ------- | ------- | ------- | -------- |
| **Sentinel**  | 20h     | 32h     | 20h     | 18h     | **90h**  |
| **Architect** | 8h      | 16h     | 12h     | 10h     | **46h**  |
| **Auditor**   | 4h      | 12h     | 10h     | 8h      | **34h**  |
| **SAP**       | 8h      | 8h      | 6h      | 4h      | **26h**  |
| **Librarian** | 6h      | 8h      | 8h      | 6h      | **28h**  |
| **Healer**    | 2h      | 4h      | 4h      | 4h      | **14h**  |
| **DevOps/QA** | 2h      | 6h      | 8h      | 6h      | **22h**  |
| **TOTAL**     | **50h** | **86h** | **68h** | **56h** | **260h** |

**Capacity Check:**

- All 6 personas: ~50% FTE equivalent for this initiative ✅
- Sustainable? Yes (other work continues in parallel)
- Burnout risk? Low (distributed load per persona)

---

## RISK MANAGEMENT

### Critical Path Risks

| Risk                                          | Probability | Impact | Mitigation                        | Owner     |
| --------------------------------------------- | ----------- | ------ | --------------------------------- | --------- |
| **ATAM workshop conflicts**                   | 1/5         | 4/5    | Book early (lock date Apr 5)      | SAP       |
| **ADR-002 formula too complex**               | 2/5         | 3/5    | Simplify iteratively in code      | Sentinel  |
| **Test coverage gate failures**               | 2/5         | 3/5    | CI/CD enforces 80%+               | Architect |
| **Privacy Shield (ADR-009) integration risk** | 3/5         | 5/5    | Start early (Jun 12, not Jul 1)   | Sentinel  |
| **Canary rollout metrics wrong**              | 2/5         | 4/5    | Validate metrics in staging first | Ops       |
| **Key persona unavailable (vacation)**        | 2/5         | 4/5    | Document backup owner per ADR     | SAP       |

### Mitigation Strategies

**For each HIGH-risk item:**

1. ✅ Owner assigned (see table)
2. ✅ Contingency plan documented (see below)
3. ✅ Weekly risk review (Sentinel + SAP)

**Contingency Plans:**

- If ATAM conflicts → Reschedule to April 16 backup slot
- If ADR-009 slips → Extend Phase 2 to Jul 20 (acceptable)
- If test coverage fails → Require code review approval before gate override
- If key persona unavailable → Activate backup (documented in ARDC)

---

## SUCCESS CRITERIA (Phase 2 GO)

✅ **Phase 2 is successful if:**

**By July 15:**

- [ ] 8/10 ADRs merged + live (80% coverage)
- [ ] 2/10 ADRs in code review (90-100% ready)
- [ ] Test coverage 80%+ on all ADR code
- [ ] Guardian Laws audit 100% passed (9/9)
- [ ] Zero production incidents related to ADRs
- [ ] All team members trained + confident
- [ ] Monitoring dashboards live
- [ ] Documentation complete

**Extended to July 20:**

- [ ] 10/10 ADRs merged + live (100% coverage) 🎉
- [ ] Quarterly ATAM review scheduled (2026-07-05)
- [ ] Phase 3 planning underway

---

## NEXT IMMEDIATE ACTIONS

### This Week (Apr 5-12)

- [ ] Confirm all 6 personas for ATAM workshop
- [ ] Distribute prep materials + reading lists
- [ ] Lock workshop date (Apr 15, 09:00 UTC)
- [ ] Schedule ADR-002 kickoff (Apr 22, 30m)

### Post ATAM Workshop (Apr 15)

- [ ] Publish risk register + implementation sequence
- [ ] Create GitHub milestones (ADR-002 through ADR-010)
- [ ] Assign code reviewers per ADR
- [ ] Confirm resource availability (check vacation calendar)

### First Kickoff (Apr 22)

- [ ] ADR-002 design document begins
- [ ] Weekly sync scheduled (Mon 09:00 UTC, all personas)
- [ ] Metrics baseline captured (false alert rate, latency, etc.)

---

## APPROVAL & SIGN-OFF

**Timeline Confidence:** 85% (depends on ATAM workshop validation + resource stability)

**Approved By:**

- [x] MASTER ORCHESTRATOR v4.0
- [ ] Architect (Proposed lead)
- [ ] SAP (Critical path owner)
- [ ] Sentinel (ADR-002 lead)

**Status:** ✅ **READY FOR PHASE 2 EXECUTION**

**When:** April 15, 2026 (immediately post-ATAM workshop)

---

**Generated By:** MASTER ORCHESTRATOR v4.0  
**Phase 2 Start:** 2026-04-22 (kickoff)  
**Phase 2 Target End:** 2026-07-15 (80%+) → 2026-07-20 (100%)  
**Next Review:** 2026-04-15 (Post-ATAM)  
**Approval Ready:** YES ✅
