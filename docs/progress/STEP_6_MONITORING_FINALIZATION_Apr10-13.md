# 🔧 STEP 6: MONITORING FINALIZATION & PRE-FLIGHT CHECKS (Apr 10-13)
**Status:** IN PROGRESS → To Execute  
**Date Created:** Apr 5, 2026, 21:50 UTC  
**Execution Window:** Apr 10, 2026 → Apr 13, 2026 (EOD)

---

## OVERVIEW

Step 6 prepares operational infrastructure for Phase 2 Go-Live (Apr 22). All monitoring dashboards, error tracking, and health checks must be **operational by Apr 13** to allow Apr 14-15 final dry-run and troubleshooting.

**Key Owners:**
- **Healer:** Health monitoring + EBDI dashboards
- **Sentinel:** Threat detection + alerting rules + crisis mode triggers
- **DevOps:** Infrastructure readiness + JSON tracker sync

---

## 6A. MONITORING INFRASTRUCTURE CHECKLIST

### 1️⃣ JSON TRACKER LIVE VALIDATION

**Tracking Files (must exist + sync automatically):**

```
monitoring/
  ├── adr_status_tracker.json          (ADR implementation status)
  ├── llm_rollout_alert.json           (LLM canary deployment state)
  ├── llm_rollout_alert_history.jsonl  (Alert history, append-only)
  └── MASTER_SYNTHESIS_*.md            (Auto-updated knowledge base)
```

**Apr 10: Initialize & Validate**

| File | Status Check | Success Criterion | Action If Fail |
|------|--------------|------------------|-----------------|
| adr_status_tracker.json | Parse JSON, read ADR-001 status | Valid JSON, keys: title/status/owner/dates | Regenerate from template |
| llm_rollout_alert.json | File exists + readable | File size <5KB, contains State + Metrics | Initialize new file |
| llm_rollout_alert_history.jsonl | File exists + writable | Can append test entry | Create new file |
| MASTER_SYNTHESIS_*.md | Sync enabled + responds to updates | File updates within 30s of trigger | Check SCB hook status |

**Validation Command** (Apr 10, 09:00 UTC):
```bash
python scripts/reporting/verify_historie_to_pictures_copy.py --mode filename --top 40
# Should output: ✅ All tracking files accessible
```

**Success Marker:** All 4 JSON trackers initialized + responding to automated updates

---

### 2️⃣ HEALTH MONITORING DASHBOARDS

**Prometheus + Grafana Stack**

**Apr 10-11: Infrastructure Setup**

| Item | Target | Verification | Owner |
|------|--------|--------------|-------|
| Prometheus running | Port 9090 accessible | `curl http://localhost:9090/-/healthy` → 200 OK | DevOps |
| Grafana running | Port 3000 accessible | `curl http://localhost:3000/api/health` → 200 OK | DevOps |
| Grafana datasource (Prometheus) | Connected + synced | Dashboard queries execute <500ms | DevOps |
| EBDI metrics job | Collects agent state | `curl http://localhost:9090/api/v1/query?query=ebdi_arousal_level` | Healer |
| ADR-002 test metrics | Reports simulated data | Tests generate metrics, Prometheus scrapes | Sentinel |

**Dashboard Creation Tasks**

Create 3 monitoring dashboards in Grafana (Apr 11-12):

**Dashboard 1: Agent Health (EBDI PAD)**
```
Metrics Tracked:
  - ebdi_pleasure_level (per agent)
  - ebdi_arousal_level (per agent) — CRITICAL ALERT if >0.7
  - ebdi_dominance_level (per agent)
  
Visualization:
  - 6 gauges (one per persona)
  - Colored zones: Green (0-0.5), Yellow (0.5-0.7), Red (>0.7)
  - Update frequency: 5s
  
Alerting:
  - Alert if Arousal > 0.7 for ANY agent for >2 min
  - Action: Trigger Sentinel crisis mode
```

**Dashboard 2: ADR Implementation Progress**
```
Metrics Tracked:
  - adr_code_coverage (%)
  - adr_test_count (cumulative)
  - adr_merge_status (draft/ready/merged)
  - adr_review_blockers (count)
  
Visualization:
  - Multi-line chart (% coverage by ADR)
  - Table (status per ADR)
  - Time-series (velocity of merges)
  
Alerting:
  - Alert if coverage < 75% on merged ADRs
  - Action: Trigger Auditor code review escalation
```

**Dashboard 3: System Health (Availability)**
```
Metrics Tracked:
  - api_uptime (%)
  - error_rate (requests/min with errors)
  - response_time_p99 (ms)
  - database_connections (active)
  
Visualization:
  - Single stat (uptime %)
  - Time-series (error rate)
  - Latency heatmap
  
Alerting:
  - Alert if uptime < 99.5%
  - Alert if error rate > 5%
  - Action: Trigger Healer remediation workflow
```

**Success Marker:** All 3 dashboards populated & querying live data by Apr 12

---

### 3️⃣ ALERTING RULES CONFIGURATION

**Apr 11-12: Define Alerting Rules**

Create 8 Prometheus alert rules (in `monitoring/prometheus-rules.yml`):

| # | Alert | Condition | Action | Severity |
|---|-------|-----------|--------|----------|
| 1 | AROUSAL_CRITICAL | ebdi_arousal_level > 0.7 for 2 min | Page Sentinel | CRITICAL |
| 2 | COVERAGE_LOW | adr_code_coverage < 75% | Slack #phase-2-alerts | WARNING |
| 3 | UPTIME_LOW | api_uptime < 99.5% | Escalate to DevOps | CRITICAL |
| 4 | ERROR_RATE_HIGH | error_rate > 5% | Slack + Healer escalation | WARNING |
| 5 | DB_POOL_EXHAUSTED | active_connections > 45/50 | Alert DevOps + Auditor | HIGH |
| 6 | ADR_MERGE_BLOCKED | adr_review_blockers > 2 | Slack #phase-2-alerts | INFO |
| 7 | LLM_RESPONSE_SLOW | llm_latency_p99 > 2000ms | Slack #phase-2-tech | WARNING |
| 8 | MEMORY_USAGE_HIGH | system_memory_usage > 85% | Escalate to DevOps | HIGH |

**Apr 12: Alert Testing**

For each of the 8 alerts:
- [ ] Trigger test condition (synthetic metric injection)
- [ ] Verify alert fires (check Prometheus Alertmanager)
- [ ] Verify action executes (Slack message sent, log entry created)
- [ ] Clear condition, verify alert resolves

**Success Marker:** 8/8 alerts tested + verified firing & resolving correctly

---

## 6B. SCB AUTO-UPDATE VALIDATION

**Session Continuity Bridge (from Step 7, Session 5)**

**Apr 10: SCB Sync Test**

```bash
# Trigger SCB sync manually (PowerShell)
Invoke-ADRONMonitoringSync

# Should output:
# ✅ Synced adr_status_tracker.json
# ✅ Updated MASTER_SYNTHESIS_*.md (§3 TSPA, §4 ADR Status, §9 Metrics)
# ✅ All trackers in sync as of [TIMESTAMP]
```

**Apr 10: Verify Auto-Update Mechanism**

```bash
# Edit adr_status_tracker.json (manually change one ADR status)
# Wait 30 seconds
# Check MASTER_SYNTHESIS_*.md (should auto-update to reflect change)

# Expected:
# Before: ADR-001: Status = proposed
# Manually change: Status = ready
# After 30s: Check docs/Genesis Record § 4 → shows "ADR-001: ready" (updated)
```

**Success Marker:** SCB responds within 30s to manual changes + auto-updates live

---

## 6C. PRE-FLIGHT CHECKLIST (Apr 13)

**Final System Validation** — All 6 Personas + DevOps participate

### Infrastructure Ready

- [ ] **Prometheus:** Scraping metrics, targets healthy (6/6)
- [ ] **Grafana:** 3 dashboards live + queryable (100% uptime)
- [ ] **Alertmanager:** Routing rules configured (all 8 rules active)
- [ ] **JSON Trackers:** Syncing + auto-updating (SCB responding <30s)
- [ ] **Database:** Connection pool initialized (45/50 available)
- [ ] **API Server:** Responding to health checks (200 OK, <100ms)

### Documentation Ready

- [ ] **ATAM Workshop slides:** Prepared + rehearsed (Architect + Librarian)
- [ ] **Decision log template:** Ready for Apr 15 notetaking (Librarian)
- [ ] **Risk register:** Initialized + ready to populate (Sentinel)
- [ ] **Runbook template:** Created for post-ADR implementation (Librarian)
- [ ] **ADR-002 implementation guide:** Code ready to review (Sentinel)

### Team Ready

- [ ] **All 6 personas:** RSVP confirmed for Apr 15 + Apr 22 (100%)
- [ ] **Backups identified:** If conflicts exist (should be 0)
- [ ] **Time zones:** All confirmed working UTC times
- [ ] **Access provisioned:** All 6 can access workshop docs + dashboards
- [ ] **Tech check:** Everyone can join video call (Zoom/Teams test ✅)

### Dry-Run Tests (Apr 13, afternoon)

**Test 1: Monitoring Alert Test** (30 min)
- Trigger 3 random alerts (e.g., high error rate, low uptime)
- Verify team receives notifications
- Verify escalation procedures work
- Success: 3/3 alerts + actions verified

**Test 2: ATAM Facilitation Dry-Run** (45 min)
- Architect + Librarian practice workshop flow
- Test: Breakout rooms (if needed), screen sharing, timer (40 min blocks)
- Record: Any tech issues or timing problems
- Success: Dry-run completes on time + identified 0-2 issues max

**Test 3: Decision Log Capture Test** (15 min)
- Librarian tests note-taking template on mock scenario
- Verify: Notes capture decisions, trade-offs, rationale in <5 min
- Success: Template works + team can understand notes

**Test 4: Post-Workshop Artifact Collection** (20 min)
- Simulate: Collect outputs (risk register, attribute list, scenarios)
- Package: Create post-workshop summary (what Librarian will do Apr 16)
- Success: Process takes <45 min, artifacts organized + linked

---

## 6D. CONTINGENCY RESPONSES

### If Monitoring System Fails Apr 13

**Severity:** HIGH

**Fallback Plan:**
- Apr 13 afternoon: Switch to manual health checks (curl, status pages)
- Apr 14: Emergency fix (swap Prometheus instance or rebuild)
- Apr 15: Run workshop with manual monitoring (if rebuild not ready)
- Apr 22: Monitoring operational for Phase 2 kickoff or delayed

### If Alert Test Fails >2 Alerts

**Severity:** MEDIUM

**Recovery:**
- Apr 13, immediately after test: Debug failed alert rules
- Call emergency 30-min troubleshooting session
- If not resolved by Apr 13 EOD: Disable non-critical alerts (keep CRITICAL only)
- Critical alerts: Arousal, Uptime, Coverage → keep active
- Non-critical: LLM_SLOW, ADR_MERGE_BLOCKED → can disable safely

### If ATAM Dry-Run Fails

**Severity:** MEDIUM

**Recovery:**
- Apr 13 evening: Record issues in technical log
- Apr 14: 1-hour fix-and-retest (timebox tightly)
- Apr 15: Run workshop with identified workarounds documented

---

## 6E. GENESIS RECORD LOG TEMPLATE

To be filled Apr 13 (~18:00 UTC after pre-flight):

```
📋 STEP 6 Completion Log

Executed: Apr 10-13, 2026
Owner(s): Healer (monitoring), Sentinel (alerts), DevOps (infrastructure)
Period: 4 days (infrastructure setup → dry-run validation)

Infrastructure Status:
  ✅ Prometheus: Running, 6/6 targets healthy
  ✅ Grafana: 3 dashboards live + queryable
  ✅ Alertmanager: 8/8 rules configured + tested
  ✅ JSON Trackers: Auto-syncing <30s
  ✅ API Server: Responding, <100ms latency
  ✅ Database: Connected, pool optimal

Dry-Run Results:
  ✅ Monitoring Alert Test: 3/3 alerts fired + escalated correctly
  ✅ ATAM Dry-Run: Completed in 45 min, 1 timing issue flagged
  ✅ Decision Log Test: Template works, <5 min capture time
  ✅ Post-Workshop Test: Artifact collection process verified

Issues Identified: 1 (timing: need 5 min buffer before block 2)
Contingencies Activated: NONE

Success Metrics:
  ✅ 100% infrastructure ready
  ✅ 8/8 alerts tested
  ✅ 0 critical blockers
  ✅ Team confidence: Green

Files:
  - monitoring/prometheus-rules.yml (8 alert rules)
  - docs/ATAM_DryRun_Log_Apr13.md (observations)
  - Genesis Record: "Apr 13: Monitoring Finalized & Pre-Flight Complete"

Next: STEP 7 (Apr 13-14: ATAM Technical & Facilitation Dry-Run)
```

---

## SUMMARY TABLE

| Phase | Date | Owner | Deliverable | Success Criterion |
|-------|------|-------|-------------|------------------|
| **Init** | Apr 10 | DevOps | JSON trackers live | All 4 files operational |
| **Dashboard** | Apr 11-12 | Healer | 3 Grafana dashboards | All dashboard queries <500ms |
| **Alerting** | Apr 11-12 | Sentinel | 8 Prometheus rules | All rules tested + verified |
| **SCB Validation** | Apr 10 | DevOps | Auto-sync >30s | Sync responds in <30s |
| **Pre-Flight** | Apr 13 | All | Infrastructure checklist | All 20 items checked ✅ |
| **Dry-Run** | Apr 13 PM | Architect + Librarian + Healer | 4 mini tests | 3/4 tests pass 100% |

---

**Status:** ✅ READY FOR EXECUTION (Apr 10-13)

**Next Step:** STEP 7 (ATAM Technical & Facilitation Dry-Run, Apr 13-14)
