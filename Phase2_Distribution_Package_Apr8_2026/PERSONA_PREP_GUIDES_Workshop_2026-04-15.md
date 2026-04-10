# 👥 PERSONA-SPECIFIC PRE-WORKSHOP PREP GUIDES

**Workshop Date:** 2026-04-15 (10 days away)
**Meeting Time:** 09:00 UTC (3-4 hours)
**Role:** [See your section below]

---

## 🏛️ **ARCHITECT** — Design Decisions Lead

### Your Role in Workshop

You lead the discovery of quality attributes and scenarios. You bridge business requirements and technical implementation. You're responsible for ensuring ADR-002-010 fit together architecturally.

### Pre-Reading (by Apr 14, 2026)

**📅 CRITICAL DEADLINE: Apr 14 EOD (1 day before workshop)**

- [ ] Read all 10 ADR templates (ADR-001-010)
  - Focus on: Context, Decision, Consequences, 162D Mapping
  - Note conflicts or dependencies between ADRs
- [ ] Review current architecture diagram
  - MoE routing logic (arbitrage/orchestrator.py)
  - Trinity system (config/trinity-weights.yml)
  - 162D decision space visualization
- [ ] Study 9 Guardian Laws and their mappings
  - Which ADRs touch which laws?
  - Any law gaps?

- [ ] Understand 6 personas' responsibilities
  - How does each persona interact with your architecture?

**🗓️ WORKSHOP: Apr 15, 2026 @ 09:00 UTC (Duration: 3h 45m)**

### Your Contributions (during workshop)

**BLOCK 1 — Context (15 min presentation)**

- Explain ADRION 369 current state
- Highlight architectural patterns already in use
- Show how 6 personas fit into the system

**BLOCK 2 — Quality Attributes & Scenarios (35 min discussion lead)**

- Propose 6-8 quality attributes (see template in prep guide)
- Lead scenario brainstorming
- Map scenarios back to ADRs
- Draw sensitivity point connections

**BLOCK 3 — Trade-offs (15 min discussion)**

- Explain architectural trade-offs
- Which ADRs have conflicts? (e.g., ADR-002 vs ADR-004)
- Document consequences

**BLOCK 4 — Roadmap (10 min sequencing)**

- Propose ADR implementation sequence
- Explain dependency order
- Flag technical blockers

### Key Questions to Answer

1. "What are the top 3 architectural concerns for ADRION 369?"
2. "Which ADR will have the biggest impact on system behavior?"
3. "Where are we most likely to hit technical debt if we don't implement ADRs?"
4. "How should we sequence ADRs to minimize integration risk?"

### Pre-Workshop Deliverables

- [ ] 5 example Quality Scenarios (formatted as "Given...when...then")
- [ ] Sensitivity Points mapping doc (design decisions → impacted attributes)
- [ ] 1-slide architecture overview (to present)
- [ ] List of known ADR dependencies (e.g., ADR-002 → ADR-003)

### Bring to Workshop

- Laptop with access to code (arbitrage/\*.py)
- Architecture diagrams (digital or printed)
- Technical whiteboard (for sketches)

---

## ⚙️ **SAP (System & Architecture Planning)** — Critical Path Lead

### Your Role in Workshop

You identify dependencies, sequences work, estimates effort. You translate scenarios into implementation plans. You answer "when" and "how long" questions.

### Pre-Reading (by 2026-04-14)

- [ ] Read Implementation-Roadmap doc (your doc!)
  - Validate timeline assumptions
  - Check effort estimates

- [ ] Study all 10 ADRs for dependencies
  - Does ADR-003 depend on ADR-002?
  - Create dependency graph (on paper or tool)

- [ ] Review 10 reliability mechanisms
  - Which ADR implements which mechanism?
  - Effort per mechanism?

- [ ] Understand current CI/CD pipeline
  - How long do PR checks take?
  - When can we start merging ADR-001 code?

### Your Contributions (during workshop)

**BLOCK 1 — Framing (5 min overview)**

- Explain ADR roadmap framework
- Show timeline visualization

**BLOCK 2 — Scenarios Validation (10 min)**

- Map scenarios to implementation effort
- Flag unrealistic expectations

**BLOCK 3 — Risk/Trade-offs (15 min)**

- For each trade-off, calculate cost/benefit
- Propose sequencing based on dependencies

**BLOCK 4 — Roadmap (20 min planning)**

- Present ADR sequence (justify order)
- Show resource allocation matrix
- Discuss milestones (2026-05-15, 2026-06-15, etc.)

### Key Questions to Answer

1. "What's the critical path for ADR implementation?"
2. "Which 3 ADRs should we do first to unblock others?"
3. "How much total effort are we talking? (210h? 300h?)"
4. "What's the earliest we can deliver ADR-002-005?"

### Pre-Workshop Deliverables

- [ ] Dependency graph (ADR-001-010, showing arrows)
- [ ] Resource allocation spreadsheet (effort per ADR, per persona)
- [ ] Detailed timeline (week-by-week, or 2-week sprints)
- [ ] Risk bottlenecks list (e.g., "All ADRs need code review capacity")

### Bring to Workshop

- Laptop with spreadsheet (or draw on board)
- Calendar (for milestone locking)
- Risk/blocker backlog

---

## 🔍 **AUDITOR** — Compliance & Guardian Laws Verification

### Your Role in Workshop

You ensure 9 Guardian Laws are honored throughout implementation. You validate quality attributes against laws. You create code review checklists. You're the compliance enforcer.

### Pre-Reading (by 2026-04-14)

- [ ] Memorize all 9 Guardian Laws (yes, memorize!)
  - G1: Unity, G2: Harmony, G3: Rhythm, G4: Causality, G5: Transparency, G6: Authenticity, G7: Privacy, G8: Nonmaleficence, G9: Sustainability

- [ ] Read each ADR and mark which laws it touches
  - ADR-001: G4, G5, G6 ✓
  - ADR-002: G3, G8
  - ... (do all 10)

- [ ] Review threat vectors in guardian.py (12 threat types)
  - Which law protects against each threat?

- [ ] Create code review checklist template
  - "For ADR PRs, ensure: G7 privacy checks, G8 safety locks, ..."

### Your Contributions (during workshop)

**BLOCK 1 — Framing (5 min overview)**

- Explain Guardian Laws as quality attributes
- Map laws to technical concerns

**BLOCK 2 — Attributes Validation (20 min)**

- Propose attributes (relate to laws)
  - Performance → G3 (Rhythm)
  - Security → G8 (Nonmaleficence)
  - Privacy → G7 (Privacy)
  - etc.

**BLOCK 3 — Risk Assessment (25 min lead)**

- Risk analysis from compliance perspective
- "If Privacy Shield ADR-009 isn't done, what's the risk?"
- Propose gates (80% test coverage, Guardian Laws audit, etc.)

**BLOCK 4 — Success Criteria (10 min)**

- Define quality gates for ADR PRs
- Code review checklist per law
- Sign-off process

### Key Questions to Answer

1. "Do all 10 ADRs honor the 9 Guardian Laws?" (Answer: Yes/No/Partially)
2. "Which ADR has the highest compliance risk?"
3. "What code review checklist do we need?"
4. "How do we measure Guardian Laws enforcement?"

### Pre-Workshop Deliverables

- [ ] ADR → Guardian Laws mapping matrix (10×9 = 90 cells)
- [ ] Code review checklist template (per law)
- [ ] Compliance risk register (20+ items)
- [ ] Quality attributes list tied to laws

### Bring to Workshop

- Printed Guardian Laws reference
- Code review checklist draft
- Risk matrix (probability × impact)

---

## 🚨 **SENTINEL** — Risk & Threat Assessment

### Your Role in Workshop

You identify threats, assess risks, propose mitigations. You're the "what could go wrong" voice. You own threat analysis and resilience planning.

### Pre-Reading (by 2026-04-14)

- [ ] Study 12 threat vectors (from guardian.py)
  - Example threats:
    - Cascade failures
    - LLM backend outages
    - Persona health degradation
    - Context window overflow
  - How do ADRs mitigate each?

- [ ] Read all ADRs with risk lens
  - ADR-002: Reduces Arousal threshold → lower false alarms (risk: under-detection)
  - ADR-009: Privacy Shield → no data exfil (risk: feature bloat)

- [ ] Review current monitoring stack
  - Prometheus, Grafana, Loki
  - What's not monitored? (gaps?)

- [ ] Create threat → ADR mapping
  - Threat X is mitigated by ADR-Y

### Your Contributions (during workshop)

**BLOCK 1 — Context (5 min)**

- Overview of current threat landscape
- 12 threat vectors in ADRION 369

**BLOCK 2 — Scenarios Validation (15 min)**

- Critique scenarios for realism ("Is that scenario actually a risk?")
- Propose adversarial scenarios

**BLOCK 3 — Risk Assessment (30 min lead)**

- Present risk register (20+ items)
- Probability/Impact/Priority assessment
- Propose high/medium/low prioritization
- Mitigation strategies per risk

**BLOCK 4 — Roadmap (15 min)**

- Risk-driven sequencing
  - Which ADR de-risks most?
  - Propose ADR-002 first (mitigates Arousal threats)
  - Propose ADR-009 early (mitigates Privacy threats)

### Key Questions to Answer

1. "What are the top 5 threats to ADRION 369?"
2. "Which ADR mitigates the most critical risk?"
3. "What's our residual risk after all ADRs?" (never zero!)
4. "How do we monitor for threat realization?"

### Pre-Workshop Deliverables

- [ ] Threat inventory (12 vectors + 8+ new ones you identify)
- [ ] Risk register (20-30 items with P/I/Priority)
- [ ] ADR → Threat mitigation mapping
- [ ] Monitoring proposal (what KPIs do we watch?)
- [ ] 1-slide risk matrix visualization

### Bring to Workshop

- Risk cards (physical or digital, one per risk)
- Threat vector reference sheet
- Monitoring dashboard mockup

---

## 💡 **LIBRARIAN** — Knowledge Management & Documentation

### Your Role in Workshop

You capture everything. You organize outputs. You ensure nothing is lost. You're the team's memory. You prepare documentation structure for handoff.

### Pre-Reading (by 2026-04-14)

- [ ] Understand ATAM methodology
  - Inputs: Architecture, stakeholder questions
  - Outputs: Risk register, scenarios, trade-offs
  - Read ATAM handbook (if available)

- [ ] Review current documentation structure
  - Genesis Record format
  - ADR template structure
  - JSON monitoring schema

- [ ] Create documentation capture template
  - Quality Attributes section
  - Scenarios section
  - Risks section
  - Trade-offs section
  - Action Items section

- [ ] Set up shared document (Google Doc / Confluence)
  - Structure that matches workshop sections
  - Permissions: All 6 personas read/write

### Your Contributions (during workshop)

**BLOCK 1-4 — Live Documentation (throughout)**

- Capture decisions in real-time
- Organize into sections (Attributes → Scenarios → Risks → Roadmap)
- Ask clarifying questions ("Can you rephrase that?")
- Ensure nothing is ambiguous

**Post-Workshop (48 hours)**

- Transform workshop notes into formal report
- Create ATAM-Progress.json Phase 2 update
- Prepare presentation for stakeholders

### Key Questions to Answer

1. "Did we capture all quality attributes?" (checklist validation)
2. "Are all scenarios documented with clear consequences?"
3. "Does risk register have owners for each item?"
4. "Is the implementation roadmap crystal clear?"

### Pre-Workshop Deliverables

- [ ] Shared document (Google Doc) with structure
- [ ] Capture template (sections, required fields)
- [ ] Glossary (ensure consistent terminology)
- [ ] Sign-off checklist (what makes workshop successful?)

### Bring to Workshop

- Laptop (for live note-taking)
- Backup document (in case of tech failure)
- Capture template printouts
- Phone (to photo whiteboard if needed)

---

## 🏥 **HEALER** — Remediation & Self-Healing Strategies

### Your Role in Workshop

You answer "what if it breaks?" questions. You propose recovery mechanisms. You design resilience patterns. You own remediation runbooks.

### Pre-Reading (by 2026-04-14)

- [ ] Study 10 reliability mechanisms
  - TSPA, SAV, RBC, SCB, CWM, CR, DSV, DRM, TEL, PHM
  - Which mechanisms are ready? (implemented/planned)

- [ ] Review persona health monitoring (EBDI model)
  - How do we detect degradation?
  - What's the recovery protocol?

- [ ] Read ADR that touch healing
  - ADR-002: Adaptive Arousal → Healer triggered
  - ADR-004: Probabilistic SAV → Lighter recovery
  - ADR-007: RBC Checkpointing → Rollback mechanism
  - ADR-008: EBDI Calibration → Health reset

- [ ] Design remediation runbooks
  - "What to do if Sentinel detects threat?"
  - "What to do if persona health drops?"
  - "What to do if CI/CD gate fails?"

### Your Contributions (during workshop)

**BLOCK 2 — Scenarios (15 min)**

- Propose recovery scenarios
  - "When LLM fails, system recovers via Ollama local-first"
  - "When Sentinel detects threat, Healer triggers remediation"

**BLOCK 3 — Risk Mitigation (20 min)**

- For each risk, propose remediation strategy
- Design failure modes and recovery paths
- Estimate recovery time (RTO) / Recovery point (RPO)

**BLOCK 4 — Implementation (10 min)**

- Resource requirements for remediation features
- Training for team on runbooks
- Monitoring/alerting for remediation triggers

### Key Questions to Answer

1. "What's our recovery time objective (RTO) for each failure type?"
2. "Which ADR provides the best self-healing capability?"
3. "What remediation runbooks do we need?"
4. "How do we test recovery without breaking production?"

### Pre-Workshop Deliverables

- [ ] Remediation strategy matrix (Failure Type → Recovery → Owner)
- [ ] RTO/RPO projections (per threat type)
- [ ] Recovery runbook templates (3-5 examples)
- [ ] Health monitoring proposal (KPIs per persona)
- [ ] 1-slide remediation overview

### Bring to Workshop

- Laptop with runbook templates
- Health monitoring dashboard mockup
- Recovery test plan proposal

---

## 🎯 WORKSHOP ATTENDANCE REQUIREMENTS

**All personas attend the full 3-4 hours.**

- **10 hours of collective effort** = ~1.6h per person across all prep + workshop
- **Preparation time:** 2-3 hours (by 2026-04-14)
- **Workshop time:** 3-4 hours (2026-04-15)
- **Post-workshop work:** 4-8 hours (by 2026-04-22, per role)

---

## ✅ FINAL CHECKLIST (by 2026-04-15, 08:30 UTC)

**Everyone:**

- [ ] Read this guide (your role section)
- [ ] Review the main ATAM Workshop Preparation guide
- [ ] Completed pre-reading for your role
- [ ] Submitted pre-workshop deliverables (email to Librarian by EOD 2026-04-14)

**Architect & SAP:**

- [ ] Slide deck ready (share 30 min before meeting)

**All Personas:**

- [ ] Join meeting 5 min early (technical check)
- [ ] Camera on (for engagement)
- [ ] Distractions minimized

---

## SUCCESS CRITERIA

✅ **Workshop is successful if:**

1. All 6 personas contribute meaningfully
2. 5-8 quality scenarios documented
3. 20+ risks identified & prioritized
4. Implementation sequence validated & locked
5. Resource allocation finalized
6. All output captured (no post-workshop "what did we decide?" questions)
7. Action items assigned to owners with due dates

---

**Next:** Confirm attendance by 2026-04-12, submit pre-reading by 2026-04-14

**Questions?** Contact Architect or SAP before 2026-04-08.
