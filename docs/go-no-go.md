# Sprint 1 GO/NO-GO Criteria

**Sprint Duration:** 2026-05-20 to 2026-06-03 (2 weeks)

**Gate Review Date:** 2026-06-03

---

## Definition of Done

A ticket is closed when **all** of the following are met:

- ✅ `cargo build --all` passes with no warnings
- ✅ `cargo test --all` passes with >= 80% coverage
- ✅ `cargo clippy --all -- -D warnings` passes
- ✅ `cargo fmt --check` passes (formatting)
- ✅ Acceptance criteria in ticket satisfied
- ✅ Documentation updated (rustdoc, RFC, or comment)
- ✅ No performance regression (benchmarks within 5% baseline)
- ✅ Guardian Laws compliance verified (G7, G8 as CRITICAL)

---

## Sprint 1 Deliverables

### P0: Setup (MUST HAVE)

- [ ] **Monorepo structure finalized**
  - kernel/, agents/, ipc/, poc/scheduler-mgr crates
  - Cargo.toml workspace members correct
  - Acceptance: `cargo build --all` succeeds

- [ ] **Developer tooling configured**
  - `.devcontainer/` set up (VS Code)
  - `Cargo.fmt` configuration
  - `clippy.toml` strict warnings
  - Acceptance: `cargo fmt --check` passes

- [ ] **GitHub Actions CI/CD activated**
  - `.github/workflows/rust-ci.yml` (build, test, lint, bench-smoke)
  - Branch protection rules enforced (1 approval normal, 2 for `unsafe`)
  - Acceptance: CI runs on every PR

- [ ] **Documentation skeleton created**
  - docs/INDEX.md (map of all docs)
  - docs/ARCHITECTURE.md (system overview)
  - docs/RFC/ directory with template
  - Acceptance: `mdbook serve docs/` works

### P1: Design (MUST HAVE)

- [ ] **RFC #0001: CognitiveAgent approved**
  - Trait definition finalized
  - Async/await design locked
  - IPC message format defined
  - Guardian Laws impact assessed
  - Acceptance: RFC merged, no open questions

- [ ] **Capability Model documented**
  - docs/CAPABILITY_MODEL.md complete
  - 4 categories defined + default grants
  - G7/G8 mitigations specified
  - Acceptance: No undefined capabilities

### P2: PoC Implementation (MUST HAVE)

- [ ] **Scheduler manager PoC (user-space)**
  - poc/scheduler-mgr builds and runs
  - Demonstrates task scheduling (FIFO, SJF modes)
  - Includes example IPC message send/receive
  - Acceptance: `cargo run --release` works on Linux

- [ ] **IPC ring buffer working**
  - ipc/ crate implements zero-copy ring buffer
  - < 1μs latency on local shared memory
  - Lock-free producer/consumer
  - Acceptance: Benchmark result: `ring_buffer_throughput >= 100k msg/sec`

- [ ] **First Guardian Law check integrated**
  - SecurityGuardian (G7/G8) evaluates AnalysisContext
  - Denies if G7 or G8 violated
  - Logs decision with audit trail
  - Acceptance: Unit test `test_security_guardian_blocks_g7_violation` passes

### P3: Quality (SHOULD HAVE)

- [ ] **Test coverage >= 80%**
  - kernel/ >= 80%
  - agents/ >= 80%
  - ipc/ >= 80%
  - poc/ >= 70% (PoC, looser requirement)
  - Acceptance: `cargo tarpaulin --all` reports >= 80%

- [ ] **Benchmarks established**
  - IPC latency baseline: < 1μs (ring buffer)
  - Guardian Law evaluation: < 100μs (single law)
  - PoC scheduler throughput: > 10k tasks/sec
  - Acceptance: `cargo bench --all` runs, results logged

- [ ] **Unsafe code review process working**
  - Any `unsafe` block has SAFETY comment
  - Any `unsafe` PR has `unsafe` label
  - 2-reviewer approval on `unsafe` code
  - Acceptance: 0 unlabeled `unsafe` blocks in codebase

---

## GO/NO-GO Decision

### GO Criteria (MUST ALL PASS)

✅ Monorepo builds without errors
✅ CI/CD runs and enforces quality gates
✅ RFC #0001 (CognitiveAgent) merged
✅ IPC ring buffer latency < 1μs (measured)
✅ PoC scheduler manager runs without panics
✅ Test coverage >= 80% across all crates
✅ Guardian Laws compliance verified (G7, G8)
✅ No open blocker bugs
✅ CONTRIBUTING.md reviewed and approved

### NO-GO Criteria (ANY ONE BLOCKS)

❌ `cargo build --all` fails with errors
❌ `cargo test --all` fails (coverage < 80%)
❌ Benchmark regresses > 5% from baseline
❌ RFC #0001 still in Draft (design not locked)
❌ IPC latency > 1μs (architecture failure)
❌ PoC scheduler manager panics or crashes
❌ Guardian Law G7/G8 unmitigated vulnerabilities
❌ Unsafe code without SAFETY comments

---

## Timeline

| Date | Milestone | Owner | Status |
|------|-----------|-------|--------|
| 2026-05-20 | Sprint kickoff, RFC #0001 opened | @Gruszkoland | In Progress |
| 2026-05-24 | RFC #0001 merged | @team | Pending |
| 2026-05-27 | IPC ring buffer MVP complete | @backend | Pending |
| 2026-05-29 | PoC scheduler running | @backend | Pending |
| 2026-05-31 | Guardian Laws + 80% coverage | @backend | Pending |
| 2026-06-02 | Benchmarks baseline established | @perf | Pending |
| 2026-06-03 | GO/NO-GO gate review | @Gruszkoland | Pending |

---

## Escalation Path

If blocker found < 3 days before gate:

1. Owner notifies @Gruszkoland immediately
2. Assess severity (Critical / High / Medium)
3. Options:
   - **Critical:** Gate delayed 1 week, mitigate issue
   - **High:** Skip deliverable, reclassify as Sprint 2
   - **Medium:** Document and proceed (tracked as tech debt)

---

## Post-GO Actions

If GO decision is reached:

1. Tag release: `v0.1-skeleton` (GitHub Releases)
2. Write sprint retrospective: lessons learned, what worked
3. Plan Sprint 2: deeper agent implementations, full Guardian Laws evaluation
4. Open issues for Sprint 2 backlog
