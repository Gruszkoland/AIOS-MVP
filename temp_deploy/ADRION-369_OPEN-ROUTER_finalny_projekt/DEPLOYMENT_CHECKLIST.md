# Pre-Deployment Checklist — OpenRouter

## Phase 1: Preparation ✅

- [ ] OpenRouter account created (openrouter.ai)
- [ ] API Key generated and copied
- [ ] API Key stored securely (password manager)
- [ ] Project directory cloned/downloaded
- [ ] All directories created (verify 1_env_templates, 2_scripts, etc.)
- [ ] Read INDEX_READ_ME_FIRST.md
- [ ] Read QUICKSTART_OPENROUTER.md

## Phase 2: Configuration ✅

- [ ] Copied .env template: \cp 1_env_templates/.env.openrouter-production .env\
- [ ] Added OpenRouter API Key to .env
- [ ] Verified .env format (no trailing spaces, proper quotes)
- [ ] Configured LLM_MODEL (recommended: llama-3.1-8b or mistral-7b)
- [ ] Set LOG_LEVEL appropriately (INFO for prod, DEBUG for dev)
- [ ] Reviewed all settings in OPENROUTER_CONFIG.md

## Phase 3: Validation ✅

- [ ] Run validation script:
  \ash 2_scripts/deployment/validate-openrouter-key.sh\
- [ ] Verify output: "OpenRouter key is valid"
- [ ] Check API connectivity: "API endpoint reachable"
- [ ] Confirm rate limits shown

## Phase 4: Dependencies ✅

- [ ] Python 3.9+ installed (\python --version\)
- [ ] Virtual environment created (\python -m venv venv\)
- [ ] Virtual environment activated
- [ ] requirements.txt reviewed
- [ ] Packages installed (\pip install -r requirements.txt\)
- [ ] Verify OpenRouter library installed (\python -c "import openrouter"\)

## Phase 5: Testing ✅

- [ ] Run unit tests: \pytest 4_tests/test_openrouter_basic.py -v\
- [ ] All tests passing (expected: 15+ tests)
- [ ] Run integration test: \pytest 4_tests/test_openrouter_integration.py -v\
- [ ] Check KPI monitoring: \python -c "from arbitrage.llm import get_kpi_snapshot; print(get_kpi_snapshot())"\
- [ ] Verify canary routing: \python 4_tests/test_canary_rollout.py\

## Phase 6: Local Testing (Optional) ✅

- [ ] Start service locally: \python wsgi.py\
- [ ] Health check: \curl http://localhost:8001/api/arbitrage/status\
- [ ] Test chat endpoint manually
- [ ] Monitor logs for errors
- [ ] Check response times are acceptable

## Phase 7: Security Review ✅

- [ ] .env file NOT committed to git (\cat .gitignore | grep .env\)
- [ ] API Key never logged or exposed (\grep -r OPENROUTER_API_KEY .\ - check)
- [ ] All secrets in .env using environment variables
- [ ] SSL/TLS configuration reviewed (if applicable)
- [ ] CORS settings appropriate for your domain
- [ ] Rate limiting configured to prevent abuse

## Phase 8: Monitoring Setup ✅

- [ ] monitoring/openrouter/ directory has necessary config
- [ ] KPI thresholds set appropriately in .env
- [ ] Alert webhooks configured (Slack/Discord optional)
- [ ] Grafana/Prometheus ports accessible (if using)
- [ ] Log rotation configured (\2_scripts/monitoring/\)

## Phase 9: Documentation ✅

- [ ] Read OPENROUTER_CONFIG.md (technical details)
- [ ] Read 5_docs/COMPLETE_API_REFERENCE.md (API usage)
- [ ] Read 5_docs/TROUBLESHOOTING.md (common issues)
- [ ] Note any custom settings for your deployment
- [ ] Document any deviations from defaults

## Phase 10: Final Go/No-Go ✅

### Go Decision Criteria
- ✅ All tests passing (15+/15)
- ✅ API connectivity verified
- ✅ No security vulnerabilities
- ✅ Performance metrics acceptable (P95 < 8s)
- ✅ Error rate low (< 5%)
- ✅ Team reviewed and approved

### Decision
- [ ] **GO:** Proceed to production deployment
- [ ] **NO-GO:** Resolve issues before deployment

### Issues Found (if No-Go)
\\\
[List any issues and resolutions]
\\\

---

## Deployment Authorization

| Role | Name | Approved | Date |
|------|------|----------|------|
| Tech Lead | _____________ | ☐ | _______ |
| DevOps | _____________ | ☐ | _______ |
| Security | _____________ | ☐ | _______ |
| Product | _____________ | ☐ | _______ |

**Overall Status:** [ ] APPROVED  [ ] PENDING  [ ] BLOCKED

---

## Post-Deployment (For Production)

- [ ] Monitor system for 24 hours
- [ ] Check error rates daily
- [ ] Review cost metrics weekly
- [ ] Plan capacity scaling if needed
- [ ] Schedule security review in 30 days

---
**Checklist Version:** 1.0  
**Date:** 06-04-2026  
**Print and sign before production deployment**
