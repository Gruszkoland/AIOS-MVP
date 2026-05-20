---
title: AIOS MVP — Master Risk Matrix
version: 1.0
date: 2026-05-20
status: Living document (updated weekly)
---

# AIOS MVP — Master Risk Matrix & Mitigation Plan

**Document owner:** Project Manager
**Review cycle:** Every Friday
**Escalation:** Score ≥6 → PM, Score ≥9 → Daily standup

---

## 📊 Risk Matrix Overview

**Scale:** Probability (L=1, M=2, H=3) × Impact (L=1, M=2, H=3) = Score (1–9)

| Score | Color | Action | Frequency |
|-------|-------|--------|-----------|
| 1–2 | 🟢 Green | Monitor | Monthly |
| 3–4 | 🟢 Green | Manage | Monthly |
| 5–6 | 🟡 Yellow | Track | Weekly |
| 7–8 | 🔴 Red | Escalate | Daily |
| 9 | 🔴 CRITICAL | All-hands | Immediate |

---

## 🔴 Critical Risks (Score = 9)

### Risk #1: PARP Compliance Gap (Art. 15 misalignment)

| Aspect | Detail |
|--------|--------|
| **Description** | PARP committee reads wniosek, finds our "deterministic ethics" doesn't clearly map to EU AI Act Art. 15 ("responsibility mechanisms") → requests revision → funding delayed |
| **Probability** | 🔴 HIGH (3) — Legal language differs between PARP & EU regulation |
| **Impact** | 🔴 HIGH (3) — 6-month delay = miss market window, competitors catch up |
| **Score** | **9 / CRITICAL** |
| **Mitigation** | ✅ **Sprint 3:** Legal review (external counsel) + rewrite wniosek with side-by-side Art. 15 mapping. Deliverable: "PARP_Art15_Mapping.md" with color-coded checklist |
| **Owner** | Legal + PM |
| **Status** | 🔴 NOT STARTED |
| **Next action** | **DL 2026-05-29:** Engage external legal firm (specialization: EU AI governance) |

---

### Risk #2: Enterprise LoI Collection Failure

| Aspect | Detail |
|--------|--------|
| **Description** | June 2026 deadline for 2× LoI. Current status: 5 prospects, 0 confirmed → we miss validation gate → PARP doubts "real market demand" |
| **Probability** | 🔴 HIGH (3) — Enterprise sales cycles are 4–8 weeks |
| **Impact** | 🔴 HIGH (3) — Kill funding application (no market proof = ineligible) |
| **Score** | **9 / CRITICAL** |
| **Mitigation** | ✅ **Sprint 4:** Sales team exec calls (2 per week). Deliverables: (a) call summaries, (b) draft LoI templates, (c) GitHub proof (screenshot of working demo). Fallback: Secured pre-LOI from partner (CRIDO?) |
| **Owner** | Sales + CRO |
| **Status** | 🟡 IN PROGRESS (prospekts contacted, no response yet) |
| **Next action** | **DL 2026-05-25:** Follow-up calls to all 5 prospects, schedule demos |

---

### Risk #3: GitHub Repo Technical Debt Exposure

| Aspect | Detail |
|--------|--------|
| **Description** | Repo goes public, external security researchers find kernel vulnerabilities (buffer overflow, unsafe memory access) → media coverage "AIOS has critical flaws" → funding rejected, team morale down |
| **Probability** | 🟡 MEDIUM (2) — Rust prevents most memory bugs, but IPC layer untested |
| **Impact** | 🔴 HIGH (3) — Reputational damage at critical moment |
| **Score** | **6 / YELLOW** (elevated, not critical) |
| **Mitigation** | ✅ **Pre-launch:** Third-party security audit (SpriteSecure or Trail of Bits estimate: €5k). Deliverable: audit report + remediation log. Public commitment: "GitHub + audit report simultaneously on 2026-06-15" |
| **Owner** | Tech Lead + Security |
| **Status** | 🔴 NOT STARTED |
| **Next action** | **DL 2026-05-22:** Get security audit quote + reserve budget |

---

## 🟡 High-Priority Risks (Score = 5–8)

### Risk #4: Latency Regression (Performance doesn't meet <200ms target)

| Aspect | Detail |
|--------|--------|
| **Description** | During final stress test, P99 latency = 350ms (exceeds target) → can't demo to Enterprise → LoI falls through |
| **Probability** | 🟡 MEDIUM (2) — Consensus voting adds latency (9 agents in parallel) |
| **Impact** | 🔴 HIGH (3) — Product demo fail = deal-killer |
| **Score** | **6 / YELLOW** |
| **Mitigation** | ✅ **Sprint 3–4:** Continuous profiling (Flamegraph, perf). Early warning: if P99 >250ms by mid-Sprint 3, pivot to single-machine test (defer multi-node to v0.2). Deliverable: latency report + optimization log |
| **Owner** | Performance Engineer |
| **Status** | 🟢 BASELINE SET (mock: 45ms single-agent) |
| **Next action** | **DL 2026-06-10:** Load test with 9 agents live, publish results |

---

### Risk #5: Documentation Quality Drives PARP Rejection

| Aspect | Detail |
|--------|--------|
| **Description** | Wniosek v2 submitted, but diagrams unclear, Executive Summary too technical → PARP panel (50% non-technical) can't evaluate → "Resubmit with better visuals" → miss deadline |
| **Probability** | 🟡 MEDIUM (2) — Current docs are math-heavy, lack visuals |
| **Impact** | 🟡 MEDIUM (2) — 3-week resubmission window (recoverable) |
| **Score** | **4 / GREEN** (but watching) |
| **Mitigation** | ✅ **Sprint 1–2:** Peer review loop with non-technical reader (Ops/Finance). Deliverable: "Ready for PARP" checklist (14 items: visuals, plain English, callouts). Internal review: PM + Legal |
| **Owner** | Tech Writer + PM |
| **Status** | 🟡 IN PROGRESS (visuals drafted, review pending) |
| **Next action** | **DL 2026-05-25:** Peer review with 3 non-technical people, iterate |

---

### Risk #6: GitHub Stars / Community Engagement Fails

| Aspect | Detail |
|--------|--------|
| **Description** | Repo launches, gets 50 stars (instead of target 200+) → looks like niche project → PARP questions "Why not viral?" → funding credibility drops |
| **Probability** | 🟢 LOW (1) — AI safety + compliance = hot topic in tech |
| **Impact** | 🟡 MEDIUM (2) — Soft signal (not deal-breaker) |
| **Score** | **2 / GREEN** |
| **Mitigation** | ✅ **Sprint 4–5:** Community buzz (Hacker News, ProductHunt, Reddit /r/rust). Deliverable: 3 blog posts, 1 technical deep-dive, press release. Fallback: Ask 50 advisors to star on day 1 (synthetic but honest) |
| **Owner** | Marketing |
| **Status** | 🟢 PLANNED (content drafted) |
| **Next action** | **DL 2026-06-10:** Publish first blog post ("Why 9 agents beat 1 LLM") |

---

### Risk #7: Rust Ecosystem Instability (Tokio, async-std, etc.)

| Aspect | Detail |
|--------|--------|
| **Description** | Critical dependency (e.g., tokio) has breaking API change → code doesn't compile → scramble to fix on day of GitHub push |
| **Probability** | 🟢 LOW (1) — Major crates are stable |
| **Impact** | 🟡 MEDIUM (2) — 2–4 hours delay (annoying, not fatal) |
| **Score** | **2 / GREEN** |
| **Mitigation** | ✅ Cargo.lock checked in (pinned versions). Weekly `cargo update --dry-run` to catch early. Fallback: Feature-gate older API if needed |
| **Owner** | DevOps |
| **Status** | 🟢 UNDER CONTROL |
| **Next action** | **Every Monday:** Run `cargo update --dry-run`, report to team |

---

### Risk #8: Competitor Launches Faster (Steal market timing)

| Aspect | Detail |
|--------|--------|
| **Description** | Constitutional AI or Anthropic releases "Claude Guardian" (deterministic ethics, similar concept) before we launch → market narrative shifts → VC money flows to them |
| **Probability** | 🟡 MEDIUM (2) — They have resources, but 162D geometry is hard to copy |
| **Impact** | 🔴 HIGH (3) — TAM shrinks, harder to raise Series A |
| **Score** | **6 / YELLOW** |
| **Mitigation** | ✅ **Accelerate public disclosure:** GitHub push 2 weeks early (2026-06-01 vs 06-15) if prototype is green. File provisional patent NOW (180-day clock to full patent). Deliverable: provisional patent + GitHub + press release on same day |
| **Owner** | CTO + Legal |
| **Status** | 🟡 ON TRACK (patent draft ~40% done) |
| **Next action** | **DL 2026-05-25:** Finalize & file provisional patent |

---

## 🟢 Green Risks (Score ≤ 4, routine monitoring)

| Risk | Probability | Impact | Score | Mitigation | Owner | Status |
|------|-------------|--------|-------|-----------|-------|--------|
| **Test coverage <80%** | L (1) | M (2) | **2** | Enforce 80% gate in CI | Dev | 🟢 OK |
| **Budget overrun (GPU costs)** | M (2) | L (1) | **2** | Vendor lock-in deal (NVIDIA credits) | Finance | 🟢 OK |
| **Team burnout (6-mo sprint)** | M (2) | L (1) | **2** | 2-day weekend sprints, rotating leads | HR | 🟡 WATCH |
| **Kubernetes deployment complexity** | M (2) | L (1) | **2** | Pre-built Helm charts | DevOps | 🟢 OK |

---

## 📋 Action Tracker

### This Week (21–27 May)

| Task | Owner | DL | Status |
|------|-------|-----|--------|
| PARP Art. 15 mapping (legal review) | Legal | 2026-05-29 | 🔴 NOT STARTED → START NOW |
| Prospect exec calls (LoI push) | Sales | 2026-05-27 | 🟡 IN PROGRESS (1/5 called) |
| Security audit RFQ | CTO | 2026-05-22 | 🔴 NOT STARTED → START NOW |
| GitHub visuals (exec summary peer review) | Tech Writer | 2026-05-25 | 🟡 IN PROGRESS (50% done) |
| Provisional patent filing | Legal | 2026-05-25 | ⚠️ 40% draft |

### Next Week (28 May – 03 June)

| Task | Owner | DL | Status |
|------|-------|-----|--------|
| Risk matrix v2 (peer review complete) | PM | 2026-06-03 | 🟢 ON TRACK |
| KPI dashboard live (Google Sheets) | PM | 2026-06-03 | 🟢 ON TRACK |
| LoI collection (attempt close) | Sales | 2026-06-03 | ⚠️ AT RISK (follow-ups needed) |
| Latency profile (9-agent test) | Perf | 2026-06-10 | 🟢 SCHEDULED |

---

## 🎯 Escalation Path

**If score ≥9 (daily):**
1. PM → CTO → CEO (immediate call)
2. Contingency budget unlock (if needed)
3. Pivot decision (e.g., delay GitHub to fix security)

**If score 7–8 (daily standup):**
1. Owner → PM (morning sync)
2. Mitigation activation (if not already)

**If score 5–6 (weekly):**
1. Owner → PM (Friday wrap-up)
2. Status reported in ROADMAP.md

---

## 📈 Risk Trend (Last 30 days)

| Risk | May 1 | May 10 | May 20 | Trend |
|------|-------|--------|--------|-------|
| PARP Compliance Gap | 🟡 (6) | 🔴 (8) | 🔴 (9) | ⬆️ ESCALATING |
| Enterprise LoI | 🔴 (8) | 🟡 (6) | 🔴 (9) | ⬆️ ESCALATING (silence from prospects) |
| GitHub Repo Security | 🟡 (5) | 🟡 (6) | 🟡 (6) | → STABLE |
| Latency Performance | 🟢 (2) | 🟢 (2) | 🟢 (2) | → STABLE |

**Trend:** 2 risks escalating to CRITICAL. **Immediate action:** Daily standups for PARP + LoI.

---

## 📝 Weekly Risk Review Template

```markdown
## Risk Review — Week of [DATE]

### Top 3 Changes
- Risk #1: [old score] → [new score] (reason)
- Risk #X: [action taken this week]
- Risk #Y: [new risk discovered]

### Go/No-Go Decisions
- Proceed with GitHub push as scheduled? [YES / NO / CONDITIONAL]
- PARP submission on track? [YES / NO]
- LoI collection on track? [YES / NO]

### Next week focus
1. [Top priority]
2. [Second priority]
3. [Third priority]
```

---

**Last updated:** 2026-05-20 (Sprint 0)
**Next update:** 2026-05-27 (Sprint 1 end)
**Version:** 1.0 (DRAFT → LIVE after first week)
