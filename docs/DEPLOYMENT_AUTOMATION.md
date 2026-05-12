# Phase 5B Deployment Automation Guide

**Status:** Production-Ready CI/CD Pipeline
**Deployment Time:** ~2 hours (automated)
**Manual Effort:** ~10 minutes
**Rollback Time:** < 5 minutes (automatic)

---

## 🎯 Quick Start

### Prerequisites

- GitHub Actions enabled
- kubectl configured for production cluster
- Slack webhook for notifications (optional)
- Prometheus + Alertmanager configured

### Trigger Deployment

```bash
# Option 1: Automatic on main branch push
git push origin main

# Option 2: Manual workflow dispatch (with parameters)
gh workflow run phase5b-deployment.yml \
  -f canary_percentage=10 \
  -f enable_blue_green=true
```

### Monitor Deployment

```bash
# Watch GitHub Actions progress
gh run list --workflow=phase5b-deployment.yml --limit=1

# Watch live logs
gh run watch <RUN_ID>

# Check production status
curl http://api.prod.example.com/api/mcp/guardian/g4-enhanced/health
```

---

## 📊 Pipeline Architecture

### Stages (9 sequential)

```
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 1: VALIDATE (Code quality, security, module imports)      │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 2: UNIT TESTS (30+ tests, coverage report)                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 3: INTEGRATION TESTS (with PostgreSQL + Redis)            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 4: SMOKE TESTS (Staging deployment validation)            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 5: BUILD (Docker image, push to registry)                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 6: CANARY DEPLOYMENT (10% traffic to v12)                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 7: PROGRESSIVE ROLLOUT (10% → 25% → 50% → 100%)          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 8: ROLLBACK (Automatic on SLO breach)                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 9: POST-DEPLOYMENT (Report, notifications, release)       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Deployment Flow

### Phase 1: Code Validation (Automated)

**What happens:**

1. ✓ Python 3.11 environment setup
2. ✓ Dependencies cached (pip)
3. ✓ Code format check (Black)
4. ✓ Linting (Flake8)
5. ✓ Security check (Bandit)
6. ✓ Module import validation
7. ✓ Version tag generation

**Expected time:** 2-3 minutes

**Example output:**

```
✓ G4Enhanced imports OK
✓ Perplexity imports OK
✓ Endpoint imports OK
Generated version: v12-20260512-140200-abc12345
```

---

### Phase 2: Test Suite (Automated)

**Unit Tests (30+):**

- PII Redaction (6/6 patterns)
- Circuit Breaker (state transitions)
- Cache (hit/miss, TTL)
- Perplexity Gateway (4 MCP tools)
- Guardian G4 Enhanced (evaluation logic)
- Integration (end-to-end pipeline)
- Performance (P95 latency, cache)

**Expected time:** 3-5 minutes

**Expected result:**

```
test_pii_redactor.py::TestPIIRedactor::test_redact_ssn PASSED
test_circuit_breaker.py::TestCircuitBreaker::test_opens_on_failures PASSED
test_perplexity_gateway.py::TestPerplexityGateway::test_fact_check_pii_redaction PASSED
test_guardian_g4_enhanced.py::TestGuardianG4Enhanced::test_evaluate_with_web_verification PASSED
...
✓ All 30+ tests passed (coverage: 87%)
```

**Failure handling:**

- Any test failure → Pipeline stops
- Review test logs
- Fix code locally
- Push again to trigger re-run

---

### Phase 3: Smoke Tests on Staging (Automated)

**What happens:**

1. Deploy to staging environment
2. Wait for health checks
3. Run 8 smoke test scenarios
4. Measure performance (P95, P99, cache)
5. Verify error rate < 0.1%

**Expected time:** 5-7 minutes

**Example output:**

```
✓ All endpoints responding
✓ P95 Latency: 1247ms (target: < 2000ms)
✓ Cache hit rate: 73% (target: > 60%)
✓ Error rate: 0.02% (target: < 0.1%)
✓ Circuit breaker: CLOSED (healthy)
```

**If smoke tests fail:**

- Investigate logs in GitHub Actions
- Check staging logs: `kubectl logs -l app=adrion-api -n staging`
- Do not proceed to production
- Fix issue and re-push

---

### Phase 4: Docker Build (Automated)

**What happens:**

1. Setup Docker Buildx
2. Login to container registry
3. Build multi-platform image
4. Push to ghcr.io/adrion/adrion-api:v12-*

**Expected time:** 3-5 minutes

**Result:** Image ready for deployment

---

### Phase 5: Canary Deployment (Automated)

**What happens:**

1. Pre-flight health checks (blue v11 must be healthy)
2. Deploy v12 to canary pool (1 replica)
3. Shift 10% traffic to v12
4. Monitor for 5 minutes:
   - Error rate must stay < 0.1%
   - P95 latency must stay < 2.5s
   - If 3+ error spikes → automatic rollback
5. Verify health after canary

**Expected time:** 8-10 minutes

**Canary status:**

```
✓ Current deployment healthy
✓ Canary deployed to pool
✓ Traffic shifted to 10%
✓ Monitoring: Error=0.02% P95=1,300ms Cache=72%
✓ Health verified - proceed to progressive rollout
```

**If canary fails:**

```
✗ Error rate exceeded 0.1%
✗ Initiating automatic rollback...
✓ Rolled back to blue (v11)
✓ All traffic back to v11
→ Manual investigation required
```

---

### Phase 6: Progressive Rollout (Automated)

**What happens:**

1. **10% → 25%:** Hold 10 minutes, verify metrics
2. **25% → 50%:** Hold 15 minutes, verify metrics
3. **50% → 100%:** Hold 20 minutes, verify metrics

**At each stage:**

- Check error rate < 0.1%
- Check P95 latency < 2s
- Check cache hit rate > 60%
- If any breach → automatic rollback

**Expected time:** 50 minutes total

**Example output:**

```
[10:00] Traffic: 10% → 25%
  ✓ Error rate: 0.01% | P95: 1,250ms | Cache: 73%
  ✓ SLO: PASS | Proceeding...
  ⏱️  Waiting 10 minutes...

[10:10] Traffic: 25% → 50%
  ✓ Error rate: 0.02% | P95: 1,300ms | Cache: 72%
  ✓ SLO: PASS | Proceeding...
  ⏱️  Waiting 15 minutes...

[10:25] Traffic: 50% → 100%
  ✓ Error rate: 0.01% | P95: 1,280ms | Cache: 73%
  ✓ SLO: PASS | Proceeding...
  ⏱️  Waiting 20 minutes...

[10:45] ✅ DEPLOYMENT COMPLETE - 100% traffic on v12
```

---

### Phase 7: Post-Deployment (Automated)

**What happens:**

1. Generate deployment report
2. Upload report as artifact
3. Send Slack notification
4. Create GitHub Release
5. Tag version in git

**Report includes:**

- Deployment duration
- SLO achievement
- Metrics summary
- Next steps

---

## 🔧 Manual Operations

### Emergency Rollback

If something goes wrong during deployment:

```bash
# Manual rollback script (< 5 minutes)
./scripts/rollback.sh

# This will:
# 1. Shift 100% traffic back to blue (v11)
# 2. Verify health checks pass
# 3. Drain green connections
# 4. Scale down green deployment
# 5. Notify operations team
# 6. Create incident report
```

### Monitor Running Deployment

```bash
# Real-time metrics monitoring
python scripts/monitor-deployment.py \
  --endpoint http://api.prod.example.com \
  --duration 300 \
  --output /tmp/metrics.json

# Output:
# Timestamp                Error%      P95ms       Cache%      CB          Status
# 2026-05-12T14:02:00Z     0.002       1247        73.0        CLOSED      ✓ PASS
# 2026-05-12T14:02:05Z     0.001       1310        72.5        CLOSED      ✓ PASS
```

### Check Deployment Status Manually

```bash
# Health check
curl http://api.prod.example.com/api/mcp/guardian/g4-enhanced/health

# Metrics
curl http://api.prod.example.com/metrics | grep g4_

# Version check
curl http://api.prod.example.com/api/mcp/guardian/g4-enhanced/metrics | jq '.version'
```

---

## 📈 Monitoring & Alerts

### Key Metrics

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Error Rate | < 0.1% | > 0.1% |
| P95 Latency | < 2s | > 2.5s |
| P99 Latency | < 3s | > 3.5s |
| Cache Hit Rate | > 60% | < 55% |
| Circuit Breaker | CLOSED | OPEN |

### Prometheus Alerts

Located in: `prometheus/alerts-phase5b.yml`

**Critical Alerts:**

- `G4_HighErrorRate` — Error rate exceeds 0.1%
- `G4_CircuitBreakerOpen` — Perplexity API down
- `G4_InstanceDown` — API instance not responding
- `G4_MultipleSloBreach` — Multiple SLOs breached

**Warning Alerts:**

- `G4_HighP95Latency` — P95 > 2s
- `G4_LowCacheHitRate` — Cache hit < 60%
- `G4_CanaryErrorRateHigherThanBlue` — v12 errors > v11

### Slack Notifications

```
✅ Phase 5B Deployment SUCCESSFUL
Deployed Version: v12-20260512-140200-abc12345
Deployment Time: ~2 hours
Traffic Rollout: 10% → 25% → 50% → 100%

Results:
- Error Rate: 0.01% ✓
- P95 Latency: 1,280ms ✓
- Cache Hit Rate: 73% ✓
- Uptime: 99.95% ✓

Next: Monitor production for 24 hours, verify accuracy metrics
```

---

## 🚨 Troubleshooting

### Deployment Fails at Unit Tests

```
pytest tests/test_phase5b_perplexity.py -v

# Check:
1. Do all 30+ tests pass locally?
2. Are dependencies installed: pip install -r requirements-mcp.txt
3. Is Python 3.11+ installed?
```

### Smoke Tests Fail on Staging

```
# Check staging deployment
kubectl logs -l app=adrion-api -n staging --tail=100

# Check if services are up
docker-compose ps

# Run smoke tests manually
python scripts/smoke-test.py --phase 5b --verbose
```

### Canary Deployment Stuck at 10%

```
# Check canary health
curl http://api-canary.prod.example.com/api/mcp/guardian/g4-enhanced/health

# Check metrics
curl http://api-canary.prod.example.com/metrics | grep g4_errors

# Investigate logs
kubectl logs -l app=adrion-api,version=v12 --tail=200

# If stuck > 10 minutes, trigger manual rollback
./scripts/rollback.sh
```

### Progressive Rollout Stops

```
# Check traffic split
kubectl get virtualservice adrion-api -o yaml | grep weight

# Check error metrics at current percentage
curl http://api.prod.example.com/metrics | grep g4_errors_total

# Check if circuit breaker is open
curl http://api.prod.example.com/metrics | grep circuit_breaker_state
```

---

## 📋 Pre-Deployment Checklist

Before triggering deployment:

- [ ] All code changes committed to main branch
- [ ] Feature tests pass locally (`pytest tests/test_phase5b_perplexity.py -v`)
- [ ] Code review completed
- [ ] PERPLEXITY_API_KEY configured in secrets
- [ ] Blue (v11) deployment is stable and healthy
- [ ] Monitoring infrastructure operational (Prometheus, Grafana, Slack)
- [ ] On-call team aware of deployment window
- [ ] Rollback procedures tested (last 7 days)
- [ ] Estimated deployment window: 2 hours
- [ ] Post-deployment monitoring plan ready (24h monitoring shift)

---

## 📞 Contact & Escalation

**Deployment Questions:**

- Check: `.github/workflows/phase5b-deployment.yml`
- Docs: `docs/PHASE5B_IMPLEMENTATION_GUIDE.md`
- Operations: `docs/PHASE5B_OPERATIONS.md`

**During Deployment:**

- **Stage Blocked:** Check GitHub Actions logs
- **Canary Failing:** Run `./scripts/rollback.sh` manually
- **Metrics Anomaly:** Check `prometheus/alerts-phase5b.yml` context
- **Urgent Issues:** Page on-call engineer

**Emergency Rollback:**

```
./scripts/rollback.sh  # < 5 minutes to fully revert
```

---

## 📊 Expected Outcomes

### Timeline

- Stage 1-2 (Validate + Unit Tests): 5-8 minutes
- Stage 3-4 (Integration + Smoke): 10-12 minutes  
- Stage 5 (Build): 3-5 minutes
- Stage 6-7 (Canary + Rollout): 55-65 minutes
- **Total: ~2 hours**

### Success Criteria

- ✓ All tests passing (100%)
- ✓ Error rate < 0.1% throughout
- ✓ P95 latency < 2s throughout
- ✓ Zero PII leaks detected
- ✓ 100% traffic successfully shifted to v12
- ✓ Uptime: 99.95%+

### Post-Deployment Metrics

- **Accuracy Improvement:** +15% (78% → 93%)
- **Latency Improvement:** -5% (avg 1.3s vs 1.4s)
- **Cache Hit Rate:** 70-75%
- **Deployment Time:** ~2 hours (vs 10 days manual)

---

## 🎉 Success

If you see this message in Slack:

```
✅ Phase 5B Deployment SUCCESSFUL
Guardian G4 Enhanced is now live in production at 100% traffic
```

Then celebrate! 🚀

Next phase starts immediately after 24-hour monitoring window (Phase 5C: Claude-Mem).
