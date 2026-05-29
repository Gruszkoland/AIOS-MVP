# Migration Daily Checklist (Owner + Deadline)

## Daily Status Template

| Date       | Workstream   | Task | Owner | Deadline | Status                       | Blocker | Risk         | Next Action |
| ---------- | ------------ | ---- | ----- | -------- | ---------------------------- | ------- | ------------ | ----------- |
| YYYY-MM-DD | Formula      |      |       |          | Not Started/In Progress/Done |         | Low/Med/High |             |
| YYYY-MM-DD | Architecture |      |       |          | Not Started/In Progress/Done |         | Low/Med/High |             |
| YYYY-MM-DD | System       |      |       |          | Not Started/In Progress/Done |         | Low/Med/High |             |

---

## Week 1 - Boundary Freeze

| Day | Repo         | Task                                                      | Owner                   | Deadline   | DoD                          |
| --- | ------------ | --------------------------------------------------------- | ----------------------- | ---------- | ---------------------------- |
| Mon | Formula      | Merge mission and scope policy                            | Formula Repo Owner      | W1 Mon EOD | README and scope approved    |
| Tue | Architecture | Merge boundary policy and exclusions                      | Architecture Repo Owner | W1 Tue EOD | Ownership matrix approved    |
| Wed | System       | Merge operational scope and retention policy              | System Repo Owner       | W1 Wed EOD | Scope and retention approved |
| Thu | Cross-repo   | Approve dependency rule Formula -> Architecture -> System | Platform Lead           | W1 Thu EOD | Rule published               |
| Fri | Cross-repo   | Governance freeze sign-off                                | CTO/Architecture Board  | W1 Fri EOD | Freeze complete              |

## Week 2 - Canonical Extraction

| Day | Repo         | Task                                         | Owner                   | Deadline   | DoD                      |
| --- | ------------ | -------------------------------------------- | ----------------------- | ---------- | ------------------------ |
| Mon | Formula      | Consolidate canonical core docs              | Domain Architect        | W2 Mon EOD | Core docs centralized    |
| Tue | Formula      | Consolidate contracts and schemas            | Schema Owner            | W2 Tue EOD | Contract validation pass |
| Wed | Architecture | Replace canonical duplicates with references | Architecture Maintainer | W2 Wed EOD | Duplicates removed       |
| Thu | System       | Replace canonical duplicates with references | Docs Lead               | W2 Thu EOD | Duplicates removed       |
| Fri | Cross-repo   | Run canonical sync checks                    | DevEx Lead              | W2 Fri EOD | Checks green             |

## Week 3 - Architecture Consolidation

| Day | Repo         | Task                                                | Owner              | Deadline   | DoD                     |
| --- | ------------ | --------------------------------------------------- | ------------------ | ---------- | ----------------------- |
| Mon | Architecture | Separate reference modules from operational residue | Architecture Owner | W3 Mon EOD | Boundaries clean        |
| Tue | Architecture | Finalize quality matrix                             | QA Lead            | W3 Tue EOD | Matrix documented       |
| Wed | Architecture | Publish compatibility notes for System              | Release Manager    | W3 Wed EOD | Notes released          |
| Thu | System       | Validate integration against architecture output    | Integration Lead   | W3 Thu EOD | Integration checks pass |
| Fri | Cross-repo   | Weekly governance checkpoint                        | Platform Lead      | W3 Fri EOD | Checkpoint approved     |

## Week 4 - System Realignment

| Day | Repo       | Task                                                       | Owner              | Deadline   | DoD                |
| --- | ---------- | ---------------------------------------------------------- | ------------------ | ---------- | ------------------ |
| Mon | System     | Move folders to apps/services/platform/ops/docs/governance | System Maintainers | W4 Mon EOD | New layout live    |
| Tue | System     | Fix path references in scripts and CI                      | DevOps Lead        | W4 Tue EOD | CI paths fixed     |
| Wed | System     | Execute smoke suite per migration batch                    | QA + Ops           | W4 Wed EOD | Smoke pass         |
| Thu | System     | Stabilize docs and runbook links                           | Docs Lead          | W4 Thu EOD | Links validated    |
| Fri | Cross-repo | Batch close + rollback drill                               | SRE Lead           | W4 Fri EOD | Rollback validated |

## Week 5 - Archive and Retention

| Day | Repo       | Task                                              | Owner             | Deadline   | DoD                 |
| --- | ---------- | ------------------------------------------------- | ----------------- | ---------- | ------------------- |
| Mon | System     | Build archive manifest and checksum index         | Ops Analyst       | W5 Mon EOD | Manifest complete   |
| Tue | System     | Move heavy historical artifacts to archive target | SRE/Ops           | W5 Tue EOD | Artifacts moved     |
| Wed | System     | Keep index-only references in active repo         | System Maintainer | W5 Wed EOD | Active tree reduced |
| Thu | Cross-repo | Validate audit traceability post-move             | Compliance Lead   | W5 Thu EOD | Traceability pass   |
| Fri | Cross-repo | Approve retention policy enforcement              | Governance Lead   | W5 Fri EOD | Policy active       |

## Week 6 - Hardening and Cutover

| Day | Repo         | Task                               | Owner                  | Deadline   | DoD              |
| --- | ------------ | ---------------------------------- | ---------------------- | ---------- | ---------------- |
| Mon | Formula      | Final canonical integrity check    | Formula Owner          | W6 Mon EOD | Integrity pass   |
| Tue | Architecture | Final release candidate validation | Architecture Owner     | W6 Tue EOD | RC approved      |
| Wed | System       | Final cutover checklist execution  | System Owner           | W6 Wed EOD | Cutover complete |
| Thu | Cross-repo   | End-to-end regression and smoke    | QA + SRE               | W6 Thu EOD | Regression pass  |
| Fri | Cross-repo   | Migration closure sign-off         | CTO/Architecture Board | W6 Fri EOD | Migration closed |

---

## Risk and Rollback Register

| Risk                            | Trigger                            | Owner           | Immediate Response                  | Rollback Logic                           |
| ------------------------------- | ---------------------------------- | --------------- | ----------------------------------- | ---------------------------------------- |
| Broken paths after folder moves | CI/import failure                  | DevOps Lead     | Freeze next batch and patch paths   | Revert latest migration batch            |
| Canonical drift                 | Contract mismatch                  | Formula Owner   | Block merge, run canonical sync fix | Restore prior canonical tag              |
| Duplicate ownership returns     | Conflicting docs/code in two repos | Platform Lead   | Enforce ownership gate              | Revert conflicting PR set                |
| Archive traceability loss       | Missing report references          | Compliance Lead | Pause archival                      | Restore by checksum manifest             |
| Runtime smoke failure           | Health check failure               | SRE Lead        | Halt cutover                        | Roll back to previous stable release tag |

## Minimal Success KPIs

- Single source of truth for canonical definitions
- Zero overlapping ownership for core governance artifacts
- Reduced active-system repo weight and duplication
- Green CI gates for each repo role
- Verified rollback path in production-like rehearsal

---

## Week 1 Gate Result

- Date: 2026-05-29
- Status: PASS
- Evidence:
  - Mission statements inserted into repository READMEs (System + Architecture + Formula target)
  - Governance artifacts prepared and updated
  - Batch #1 and Batch #2 folder moves executed with no deletions
  - Path smoke checks passed for key artifacts and migration destinations
  - KPI gate script executed in warmup mode (PENDING accepted for low event count)

  ## Execution Log - 2026-05-29 (Autonomous Run)
  - 2026-05-29 | Cross-repo | Add SSOT file + CI gate (`REPO_CONTEXT_STATUS`, workflow) | Owner: Platform Lead | Status: Done | Risk: Low | Next: Keep gate in PR required checks
  - 2026-05-29 | System | Harden `.gitignore` with machine/local artifact patterns | Owner: System Maintainer | Status: Done | Risk: Low | Next: Monitor for new noisy artifacts
  - 2026-05-29 | System | Standardize MCP path convention to `mcp_servers` in compose | Owner: DevOps Lead | Status: Done | Risk: Med | Next: Continue import/path mapping audit
  - 2026-05-29 | System | Implement dynamic `PROJECT_STATE` confidence + tests | Owner: QA + Ops | Status: Done | Risk: Low | Next: Extend metric tests to integration lane
  - 2026-05-29 | Cross-repo | Complete post-migration reference mapping report | Owner: Platform Lead | Status: Done | Risk: Low | Next: Keep report updated after each move batch
  - 2026-05-29 | System | Remap active runtime references (`Cargo.toml`, CI, compose, README, CODEOWNERS) | Owner: DevOps Lead | Status: Done | Risk: Med | Next: Observe CI rerun outcomes
  - 2026-05-29 | Cross-repo | Enable Phase E quality lane workflow + governance closure plan | Owner: QA + Governance | Status: Done | Risk: Med | Next: Add checks as required in branch protection
