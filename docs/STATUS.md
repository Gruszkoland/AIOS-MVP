# Project Status & Roadmap

**Last Updated:** 2026-05-20
**Sprint:** 1 (2026-05-20 to 2026-06-03)

---

## Current Status

### ✅ Completed

- [x] Repository structure finalized (kernel, agents, ipc, poc)
- [x] Cargo workspace configured (4 crates)
- [x] Documentation skeleton (docs/INDEX.md, RFC template)
- [x] CONTRIBUTING.md guidelines (PR flow, unsafe rules, testing)
- [x] RFC #0001 (CognitiveAgent) in draft review

### 🔄 In Progress

- [ ] RFC #0001 (CognitiveAgent) — awaiting feedback
- [ ] IPC ring buffer implementation (ipc/src/lib.rs)
- [ ] SecurityGuardian first implementation (G7/G8 checks)
- [ ] PoC scheduler manager (poc/scheduler-mgr)
- [ ] CI/CD GitHub Actions workflow

### ⏳ Blocked

- None currently

### 📋 Pending (Sprint 2+)

- [ ] Full 9-law Guardian evaluation engine
- [ ] EthicsGuardian + PerformanceGuardian implementations
- [ ] End-to-end integration test (kernel → IPC → agent)
- [ ] Kubernetes manifests
- [ ] Performance benchmarking suite

---

## Metrics

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Lines of code (kernel) | ~500 | ~150 | 30% |
| Test coverage (all crates) | >= 80% | ~45% | ⚠️ Below target |
| IPC latency | < 1μs | TBD | 📊 Benchmarking |
| RFCs merged | 1 | 0 | ⏳ In review |
| CI/CD workflows | 2+ | 1 (stub) | ⚠️ Incomplete |

---

## Sprint 1 Deliverables (GO/NO-GO Gate: 2026-06-03)

### Must Have

- ✅ Monorepo structure
- ✅ Documentation (INDEX, RFC template, ARCHITECTURE)
- ✅ CONTRIBUTING.md finalized
- ⏳ RFC #0001 merged (deadline: 2026-05-24)
- ⏳ IPC ring buffer MVP (deadline: 2026-05-27)
- ⏳ PoC scheduler (deadline: 2026-05-29)
- ⏳ Guardian Laws compliance verified (deadline: 2026-05-31)
- ⏳ Test coverage >= 80% (deadline: 2026-06-01)
- ⏳ Benchmarks baseline (deadline: 2026-06-02)

### Should Have

- [ ] End-to-end flow (kernel → IPC → agent → decision)
- [ ] Fuzzing harness for IPC messages
- [ ] Property-based tests (hypothesis-like, for Rust)

### Nice to Have

- [ ] Performance dashboard (Grafana)
- [ ] Extended documentation (examples, tutorials)

---

## Sprint 2 Preview (2026-06-03 to 2026-06-17)

If Sprint 1 GO decision reached:

1. **Full Guardian Laws engine** (9 laws, not just G7/G8)
   - EthicsGuardian implementation
   - PerformanceGuardian implementation
   - Combined scoring + veto logic

2. **Agent multiplexing** (3+ agents, coordinated decisions)
   - Message routing in IPC
   - Agent capability enforcement
   - Multi-agent consensus logic

3. **Kernel scheduler enhancement**
   - Priority queues
   - Preemption logic
   - Timing guarantees

4. **Integration testing**
   - End-to-end flows with real agents
   - Chaos testing (fault injection)
   - Load testing (1k+ msgs/sec through IPC)

---

## Roadmap (Q2-Q3 2026)

```
Sprint 1 (May 20-Jun 03)  → v0.1-skeleton (PoC, 162D MVP)
Sprint 2 (Jun 03-Jun 17)  → v0.2-alpha (9-law Guardian, 3 agents)
Sprint 3 (Jun 17-Jul 01)  → v0.3-beta (full integration, load-tested)
Sprint 4 (Jul 01-Jul 15)  → v1.0-release (production-ready kernel)
```

### Milestones

| Version | Date | Goals |
|---------|------|-------|
| v0.1-skeleton | 2026-06-03 | PoC kernel, IPC, 1 agent type |
| v0.2-alpha | 2026-06-17 | 3 agent types, 9 Guardian Laws, basic integration |
| v0.3-beta | 2026-07-01 | Load testing, performance tuning, full test coverage |
| v1.0-release | 2026-07-15 | Production-ready, documentation, deployment guides |

---

## Known Issues

| Issue | Severity | Status | Owner |
|-------|----------|--------|-------|
| RFC #0001 not yet merged | HIGH | In review | @Gruszkoland |
| Test coverage below 80% | HIGH | In progress | @backend |
| CI/CD incomplete | MEDIUM | In progress | @devops |
| Benchmark baseline missing | MEDIUM | Pending | @perf |

---

## Communication

- **Daily standup:** Async updates in GitHub Discussions (AIOS MVP category)
- **Weekly sync:** Friday 9 AM UTC (status check)
- **Blocker escalation:** @-mention @Gruszkoland in issues

---

## Next Steps (Immediate)

1. **By 2026-05-22:** RFC #0001 feedback collection, iterate
2. **By 2026-05-24:** RFC #0001 merged (design locked)
3. **By 2026-05-27:** IPC ring buffer latency benchmark run (measure < 1μs)
4. **By 2026-05-29:** PoC scheduler-mgr running on Linux
5. **By 2026-06-03:** GO/NO-GO decision + Sprint 2 planning
