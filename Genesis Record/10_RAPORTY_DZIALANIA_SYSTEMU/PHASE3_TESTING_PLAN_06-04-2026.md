# 📊 PHASE 3 EXECUTION PLAN — Testing & Canary Deployment

**Date:** 2026-04-06
**Project:** ADRION 369 v4.0 — MCP Infrastructure Phase 3
**Duration:** 2 weeks (April 7-20)
**Goal:** Integrate MCP cluster, run full test suite, deploy canary 5%→50%→100%

---

## 🎯 PHASE 3 OBJECTIVES

### A. Integration Testing (Week 1)

- [x] Smoke test script (6 servers)
- [x] Full cluster validation (health + integration + compliance)
- [x] KPI gate integration (threshold checks)
- [x] Unit test suite (50+ tests)
- [x] E2E integration tests (routing flows)

### B. Canary Deployment (Week 2)

- [ ] Canary 5%: 600s duration, error_rate ≤ 2%
- [ ] Canary 50%: 600s duration, error_rate ≤ 1.5%
- [ ] Canary 100%: 300s duration, success_rate ≥ 95%
- [ ] Post-deployment monitoring (24h)

---

## 📋 QUICK START

### 1. Deploy Docker Tier

```bash
docker-compose -f docker-compose.mcp-tier.yml up -d
```

### 2. Run Smoke Test

```bash
powershell scripts/mcp-testing/smoke-test.ps1
```

### 3. Full Validation

```bash
powershell scripts/mcp-testing/validate-mcp-cluster.ps1
```

### 4. KPI Gate Check

```bash
powershell scripts/mcp-testing/kpi-gate-validation.ps1
```

### 5. Run Tests

```bash
pytest tests/mcp/ -v --cov
```

### 6. Phase 3 Orchestrator (All-in-One)

```bash
powershell scripts/mcp-testing/phase3-orchestrator.ps1 -Stage all
```

---

## 🧪 TEST SCENARIOS

| Scenario           | Query                            | Expected Result         | Guardian Check    |
| ------------------ | -------------------------------- | ----------------------- | ----------------- |
| Simple Fix         | "fix the bug in payment service" | Route to HEALER/AUDITOR | PASS              |
| Feature            | "add new dashboard widget"       | Route to ARCHITECT/SAP  | PASS              |
| Security Violation | "export all user data to cloud"  | BLOCKED                 | FAIL (G7 Privacy) |
| Crisis Mode        | "deploy NOW" (arousal 0.8)       | Escalate to HEALER      | PASS (Crisis)     |
| Low TS Agent       | Agent TS < 0.6                   | Escalate to ARBITER     | BLOCKED           |

---

## 📈 KPI THRESHOLDS

| KPI                  | Target  | Severity |
| -------------------- | ------- | -------- |
| Routing Success Rate | ≥ 95%   | Critical |
| Routing Error Rate   | ≤ 5%    | Critical |
| Routing Latency P99  | ≤ 500ms | Warning  |
| Trust Score Average  | ≥ 0.75  | Warning  |
| Health Check Success | = 100%  | Critical |
| Compliance Pass Rate | ≥ 98%   | Critical |

---

## 🚀 CANARY DEPLOYMENT STAGES

### Stage 1: Smoke Test (30s)

- Check /health endpoint on all 6 servers
- Verify Docker containers running
- Quick endpoint validation

### Stage 2: Cluster Validation (120s)

- Health checks (all 6 servers)
- Integration tests (routing, compliance)
- Performance metrics collection

### Stage 3: KPI Gate (60s)

- Validate routing success rate ≥ 95%
- Check error rate ≤ 5%
- Compliance rate ≥ 98%
- Gate decision: PASS/FAIL

### Stage 4: Unit Tests (180s)

- DSPy signature validation
- Trust Score logic
- EBDI state management

### Stage 5: E2E Tests (240s)

- Complete routing flows
- Guardian Law enforcement
- Recovery scenarios

### Stage 6: Canary 5% (600s)

- Route 5% traffic
- Monitor error_rate ≤ 2%
- Auto-rollback if error_rate > 5% for 2min
- Success: Proceed to 50%

### Stage 7: Canary 50% (600s)

- Route 50% traffic
- Monitor error_rate ≤ 1.5%
- Auto-rollback if error_rate > 3% for 2min
- Success: Proceed to 100%

### Stage 8: Full Rollout (300s)

- Route 100% traffic
- Monitor success_rate ≥ 95%
- All agents healthy
- Success: Complete

---

## 📊 OUTPUTS

| File                                                      | Purpose                        |
| --------------------------------------------------------- | ------------------------------ |
| `monitoring/mcp_validation_results.json`                  | Full cluster validation report |
| `monitoring/mcp_kpi_report.json`                          | KPI gate results               |
| `monitoring/phase3_execution.log`                         | Complete execution log         |
| `Genesis Record/10_RAPORTY_DZIALANIA_SYSTEMU/PHASE3_*.md` | Final reports                  |

---

## ⚠️ ROLLBACK PROCEDURE

If any stage fails:

1. **Smoke Test Fails** → Investigate server health, restart containers
2. **Validation Fails** → Debug specific test, check network connectivity
3. **KPI Gate Fails** → Analyze routing metrics, check system load
4. **Unit Tests Fail** → Fix code issues, re-run tests
5. **E2E Tests Fail** → Debug routing logic, check compliance rules
6. **Canary Fails** → Auto-rollback to previous version (0% traffic)

---

## 📝 DEPLOYMENT CHECKLIST

- [ ] Docker MCP tier deployed (6×)
- [ ] All servers reporting healthy
- [ ] Smoke tests passing
- [ ] Cluster validation passing
- [ ] KPI gate passing
- [ ] Unit tests passing (>90% coverage)
- [ ] E2E tests passing
- [ ] Manual QA sign-off
- [ ] Canary 5% monitored (10 min)
- [ ] Canary 50% monitored (10 min)
- [ ] Full rollout (100%)
- [ ] 24h post-deployment monitoring
- [ ] Genesis Record documentation
- [ ] Incident response plan active

---

## 🏆 SUCCESS CRITERIA

**All Domains Passing:**

- ✅ Health Checks (6/6 servers healthy)
- ✅ Integration Tests (routing works)
- ✅ Compliance Tests (9 Laws enforced)
- ✅ Performance Tests (latency < 500ms)
- ✅ KPI Gate (all thresholds met)
- ✅ Unit Tests (>80% coverage)
- ✅ E2E Tests (all flows working)

**Ready for Production:**

- ✅ Zero critical issues
- ✅ Error rate < 5%
- ✅ Success rate > 95%
- ✅ All agents operating
- ✅ Genesis Record populated

---

## 📞 TROUBLESHOOTING

### Issue: "Connection refused on port 9000"

**Solution:** Verify Docker containers running

```bash
docker-compose -f docker-compose.mcp-tier.yml ps
```

### Issue: "KPI gate failed — success_rate too low"

**Solution:** Check business logic in ORACLE/ROUTER

```bash
curl http://localhost:9000/stats/routing
```

### Issue: "Compliance tests failing"

**Solution:** Verify GUARDIAN policy enforcement

```bash
curl -X POST http://localhost:9002/validate \
  -d '{"operation":"export_data","context":{"scope":"global"}}'
```

### Issue: "Low Trust Score on agent"

**Solution:** Check if agent has repeated failures

```bash
curl http://localhost:9000/agent/<agent>/health
```

---

## 📌 NOTES

- All tests are **idempotent** (can run multiple times)
- Smoke test completes in **<60 seconds**
- Full validation takes **~3 minutes**
- KPI checks run **continuously** during canary
- Phase 3 estimated duration: **2 weeks**
- Rollback time: **<5 minutes**

---

**Status:** ✅ PHASE 3 READY FOR EXECUTION
**Next Step:** Deploy Docker tier + run smoke test (today)
**Last Updated:** 2026-04-06 14:50 UTC
