# ADRION 369 v4.0 - UAT CHECKLIST (42 ENDPOINTS)

**Date:** 2026-04-08
**Phase:** ETAP 4 (Production Deployment)
**Status:** Ready for User Acceptance Testing
**Success Criteria:** All 42 endpoints return appropriate HTTP status codes + business logic verified

---

## TEST MATRIX OVERVIEW

| MCP Server                 | Endpoints | Priority       | Status  |
| -------------------------- | --------- | -------------- | ------- |
| Genesis-MCP                | 7         | P0 (critical)  | [ ]     |
| Router-MCP                 | 6         | P0 (critical)  | [ ]     |
| Guardian-MCP               | 7         | P0 (critical)  | [ ]     |
| Healer-MCP                 | 6         | P1 (important) | [ ]     |
| Oracle-MCP                 | 8         | P1 (important) | [ ]     |
| Vortex-MCP                 | 8         | P2 (optional)  | [ ]     |
| **System (Health/Status)** | **4**     | **P0**         | **[ ]** |
| **TOTAL**                  | **42**    | -              | **[ ]** |

---

## PART 1: GENESIS-MCP (Event Sourcing & Session Memory)

### 1.1: POST /event/record

**Purpose:** Record new event to event log
**Method:** POST
**Endpoint:** `http://localhost:9004/event/record`

**Test Case 1.1.1: Valid Event Recording**

```json
{
  "id": "evt_001",
  "event_type": "TASK_CREATED",
  "aggregate_id": "task_123",
  "actor_id": "agent_genesis",
  "payload": {
    "task_name": "Data Processing",
    "priority": 1,
    "metadata": { "batch_size": 100 }
  }
}
```

- Expected HTTP: **201 Created** ✅
- Expected Response: `{"event_id": "evt_001", "status": "recorded"}`
- Verification: Event appears in PostgreSQL events table
- [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

**Test Case 1.1.2: Missing Required Fields**

- Send: `{"event_type": "TASK_CREATED"}` (missing actor_id)
- Expected HTTP: **400 Bad Request** ✅
- Expected Response: Error message about missing actor_id
- [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

**Test Case 1.1.3: Duplicate Event ID**

- Send: Same event_id twice
- Expected HTTP: **409 Conflict** ✅
- Expected Response: "Event already exists"
- [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

### 1.2: GET /event/state/{aggregate_id}

**Purpose:** Retrieve current state of aggregate from event log
**Method:** GET
**Endpoint:** `http://localhost:9004/event/state/task_123`

- Expected HTTP: **200 OK** ✅
- Expected Response: JSON with reconstructed state
- Response Time: **<50ms** ✅
- [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

### 1.3: GET /event/history/{aggregate_id}

**Purpose:** Retrieve complete event history
**Method:** GET
**Endpoint:** `http://localhost:9004/event/history/task_123?limit=10`

- Expected HTTP: **200 OK** ✅
- Expected Response: Array of events, sorted by timestamp
- Verify: Pagination works (`limit=10`)
- [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

### 1.4: POST /event/replay

**Purpose:** Replay events from checkpoint
**Method:** POST

```json
{
  "session_id": "sess_abc",
  "checkpoint_version": 5,
  "replay_all": false
}
```

- Expected HTTP: **200 OK** ✅
- Verify: State correctly reconstructed from events
- [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

### 1.5: GET /event/audit

**Purpose:** Retrieve audit trail (Guardian Law compliance)
**Method:** GET
**Endpoint:** `http://localhost:9004/event/audit?actor_id=agent_genesis&limit=50`

- Expected HTTP: **200 OK** ✅
- Verify: All operations logged with timestamps
- [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

### 1.6: GET /event/statistics

**Purpose:** Aggregate event statistics
**Method:** GET
**Endpoint:** `http://localhost:9004/event/statistics`

- Expected HTTP: **200 OK** ✅
- Expected Fields: `{total_events, events_per_type, avg_latency_ms}`
- [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

## PART 2: ROUTER-MCP (Task Routing & Agent Orchestration)

### 2.1: POST /route/task

**Purpose:** Route task to optimal agent (KDTree algorithm)
**Method:** POST

```json
{
  "task": {
    "id": "task_456",
    "name": "ML Model Training",
    "requirements": { "cpu": 0.8, "memory": 0.6 },
    "priority": 2
  }
}
```

- Expected HTTP: **200 OK** ✅
- Expected Response: `{agent_id: "healer-mcp-1", distance: 0.15}`
- Verify: Agent selection is optimal (O(log N) search)
- [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

### 2.2: GET /route/agents

**Purpose:** List all available agents with their capacity
**Method:** GET

- Expected HTTP: **200 OK** ✅
- Expected Response: Array of agents with health scores
- Example: `[{id: "genesis-mcp-1", capacity: 0.95, health: 0.98}]`
- [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

### 2.3: POST /route/reroute/{task_id}

**Purpose:** Re-route running task to different agent
**Method:** POST

- Expected HTTP: **200 OK** ✅ OR **404 Not Found** (if task doesn't exist)
- Verify: Task rerouted without data loss
- [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

### 2.4: GET /route/topology

**Purpose:** Retrieve 162D space topology visualization
**Method:** GET

- Expected HTTP: **200 OK** ✅
- Expected Response: JSON graph of agent positions in 162D space
- [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

### 2.5: POST /route/rebalance

**Purpose:** Trigger load rebalancing across agents
**Method:** POST

- Expected HTTP: **202 Accepted** ✅ (async operation)
- Verify: Tasks reallocated to more optimal agents
- [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

### 2.6: GET /route/metrics

**Purpose:** Routing performance metrics
**Method:** GET

- Expected HTTP: **200 OK** ✅
- Expected Fields: `{avg_route_time_ms, successful_routes, failed_routes}`
- [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

## PART 3: GUARDIAN-MCP (Security & Compliance)

### 3.1: POST /security/validate

**Purpose:** Validate request against Guardian Laws
**Method:** POST

```json
{
  "request_id": "req_789",
  "operation": "DELETE /user/123",
  "actor_id": "admin_user",
  "resource": "user_data"
}
```

- Expected HTTP: **200 OK** ✅ (if valid) or **403 Forbidden** (if violates law)
- Verify: All 9 Guardian Laws checked
- [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

### 3.2: GET /security/audit-log

**Purpose:** Retrieve compliance audit logs
**Method:** GET

- Expected HTTP: **200 OK** ✅
- Verify: All operations logged (G5 Transparency)
- [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

### 3.3: POST /security/revoke-key/{api_key_id}

**Purpose:** Revoke API key
**Method:** POST

- Expected HTTP: **200 OK** ✅
- Verify: Key no longer accepted in subsequent requests
- [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

### 3.4: GET /security/compliance-status

**Purpose:** Check compliance status vs 9 Guardian Laws
**Method:** GET

- Expected HTTP: **200 OK** ✅
- Expected Response: Matrix of 9 laws with compliance status
- Example: `{G1_Unity: "PASS", G5_Transparency: "PASS", ...}`
- [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

### 3.5: POST /security/scan-vulnerabilities

**Purpose:** Run security scan (OWASP top 10)
**Method:** POST

- Expected HTTP: **202 Accepted** ✅ (async scan)
- Verify: Scan completes and reports vulnerabilities
- [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

### 3.6: GET /security/keys

**Purpose:** List active API keys (admin only)
**Method:** GET

- Expected HTTP: **200 OK** ✅ (if authenticated)
- Expected HTTP: **401 Unauthorized** ✅ (if not authenticated)
- Verify: API keys hashed (no secrets exposed)
- [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

### 3.7: POST /security/privacy-check

**Purpose:** Verify local-first data handling (G7 Privacy)
**Method:** POST

- Expected HTTP: **200 OK** ✅
- Verify: Data stored locally, not uploaded externally
- [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

## PART 4: HEALER-MCP (Error Recovery & Self-Healing)

### 4.1: GET /health

**Purpose:** HealerMCP health status
**Method:** GET

- Expected HTTP: **200 OK** ✅
- Expected Response: `{status: "healthy", uptime_seconds: 12345}`
- [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

### 4.2: POST /heal/{agent_id}

**Purpose:** Trigger self-healing for failed agent
**Method:** POST

- Expected HTTP: **202 Accepted** ✅ (healing in progress)
- Verify: Agent recovers and returns to online status
- [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

### 4.3: GET /diagnostics

**Purpose:** System diagnostics and error history
**Method:** GET

- Expected HTTP: **200 OK** ✅
- Expected Response: Array of recent errors with root causes
- [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

### 4.4: POST /retraining

**Purpose:** Trigger model retraining (federation learning)
**Method:** POST

- Expected HTTP: **202 Accepted** ✅
- Verify: Training starts without blocking main service
- [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

### 4.5: GET /model-accuracy

**Purpose:** Retrieve current ML model accuracy metrics
**Method:** GET

- Expected HTTP: **200 OK** ✅
- Expected Fields: `{accuracy: 0.95, precision: 0.93, recall: 0.92}`
- [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

### 4.6: DELETE /cache

**Purpose:** Clear healing cache (maintenance)
**Method:** DELETE

- Expected HTTP: **204 No Content** ✅
- Verify: Cache cleared, no errors
- [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

## PART 5: ORACLE-MCP (LLM Integration & Decision Enhancement)

### 5.1: POST /llm/completion

**Purpose:** Get LLM completion from OpenRouter
**Method:** POST

```json
{
  "model": "deepseek/deepseek-chat",
  "messages": [{ "role": "user", "content": "Explain ADRION 369" }],
  "temperature": 0.7,
  "max_tokens": 500
}
```

- Expected HTTP: **200 OK** ✅
- Verify: Response completes within 30s timeout
- [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

### 5.2: POST /llm/stream

**Purpose:** Stream LLM responses (SSE)
**Method:** POST

- Expected HTTP: **200 OK** (streaming) ✅
- Verify: Response tokens stream in real-time
- [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

### 5.3: GET /llm/models

**Purpose:** List available LLM models
**Method:** GET

- Expected HTTP: **200 OK** ✅
- Expected Response: Array of available models with pricing
- [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

### 5.4: POST /llm/cache/clear

**Purpose:** Clear LLM response cache
**Method:** POST

- Expected HTTP: **204 No Content** ✅
- [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

### 5.5: GET /llm/usage

**Purpose:** Retrieve LLM API usage statistics
**Method:** GET

- Expected HTTP: **200 OK** ✅
- Expected Fields: `{total_tokens, cost_today, models_used}`
- [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

### 5.6: POST /llm/fallback

**Purpose:** Test LLM fallback (if API fails)
**Method:** POST

- Simulate OpenRouter API outage
- Expected HTTP: **200 OK** ✅ (fallback activated)
- Verify: Graceful degradation (local model or cached response)
- [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

### 5.7: DELETE /llm/sessions/{session_id}

**Purpose:** Delete cached LLM session
**Method:** DELETE

- Expected HTTP: **204 No Content** ✅
- [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

### 5.8: GET /llm/context-window

**Purpose:** Current token usage for session
**Method:** GET

- Expected HTTP: **200 OK** ✅
- Expected Response: `{used_tokens: 2048, max_tokens: 8192}`
- [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

## PART 6: VORTEX-MCP (Lead Arbitrage & Optimization)

### 6.1: POST /arbitrage/evaluate

**Purpose:** Evaluate lead arbitrage opportunity
**Method:** POST

```json
{
  "lead_id": "lead_001",
  "sources": ["crm_a", "crm_b"],
  "criteria": { "quality": 0.8, "urgency": 0.6 }
}
```

- Expected HTTP: **200 OK** ✅
- Expected Response: Arbitrage score and recommendation
- [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

### 6.2: GET /arbitrage/opportunities

**Purpose:** List available arbitrage opportunities
**Method:** GET

- Expected HTTP: **200 OK** ✅
- Verify: Returns top 10 highest-value leads
- [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

### 6.3: POST /arbitrage/execute

**Purpose:** Execute arbitrage trade
**Method:** POST

- Expected HTTP: **201 Created** ✅
- Verify: Lead assignment recorded and event logged
- [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

### 6.4: GET /arbitrage/portfolio

**Purpose:** Active arbitrage portfolio
**Method:** GET

- Expected HTTP: **200 OK** ✅
- Expected Response: Array of active arbitrage positions
- [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

### 6.5: POST /arbitrage/close/{position_id}

**Purpose:** Close arbitrage position
**Method:** POST

- Expected HTTP: **200 OK** ✅
- Verify: Position closed, P&L calculated
- [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

### 6.6: GET /arbitrage/performance

**Purpose:** Arbitrage performance metrics
**Method:** GET

- Expected HTTP: **200 OK** ✅
- Expected Fields: `{roi: 0.25, trades_executed: 145, win_rate: 0.72}`
- [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

### 6.7: DELETE /arbitrage/cache

**Purpose:** Clear arbitrage cache
**Method:** DELETE

- Expected HTTP: **204 No Content** ✅
- [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

### 6.8: POST /arbitrage/backtest

**Purpose:** Backtest arbitrage strategy on historical data
**Method:** POST

```json
{
  "strategy": "quality_score_arbitrage",
  "start_date": "2026-01-01",
  "end_date": "2026-03-31"
}
```

- Expected HTTP: **202 Accepted** ✅ (async backtest)
- Verify: Backtest completes with performance report
- [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

## PART 7: SYSTEM ENDPOINTS (Health, Status, Monitoring)

### 7.1: GET /health

**Purpose:** System health status (all MCPs)
**Method:** GET

- Expected HTTP: **200 OK** ✅ (if healthy) OR **503 Service Unavailable** (if critical)
- Expected Response: JSON with component statuses
- [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

### 7.2: GET /ready

**Purpose:** Kubernetes liveness probe
**Method:** GET

- Expected HTTP: **200 OK** ✅ OR **503** (not ready)
- [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

### 7.3: GET /metrics

**Purpose:** Prometheus metrics export
**Method:** GET

- Expected HTTP: **200 OK** ✅
- Expected Format: Prometheus text format (`metric_name 123`)
- [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

### 7.4: GET /status

**Purpose:** Detailed system status
**Method:** GET

- Expected HTTP: **200 OK** ✅
- Expected Response: Uptime, version, compiled date, etc.
- [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

## PART 8: SECURITY TESTING (OWASP Top 10)

### 8.1: SQL Injection Test

- **Test:** Send `'; DROP TABLE tasks; --` in payload
- **Expected:** Safely escaped, no table dropped
- **Result:** [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

### 8.2: XSS Protection Test

- **Test:** Send `<script>alert('xss')</script>` in input
- **Expected:** HTML sanitized, script tags removed
- **Result:** [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

### 8.3: Authentication Test

- **Test:** Access endpoint without API key
- **Expected:** **401 Unauthorized** ✅
- **Result:** [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

### 8.4: Rate Limiting Test

- **Test:** Send 2000 requests in 1 minute
- **Expected:** Requests throttled after 1000/hour limit
- **Result:** [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

### 8.5: CORS Test

- **Test:** Request from untrusted origin
- **Expected:** **403 Forbidden** ✅
- **Result:** [ ] Pass | [ ] Fail | Notes: ******\_\_\_******

---

## SUMMARY

### Test Results

- **Total Endpoints Tested:** \_\_ / 42
- **Passed:** \_\_ / 42
- **Failed:** \_\_ / 42
- **Blocked/Not Run:** \_\_ / 42

### Status

- [ ] All Critical (P0) endpoints pass
- [ ] All Important (P1) endpoints pass
- [ ] Security tests pass (OWASP Top 10)
- [ ] Performance targets met (<50ms)
- [ ] Ready for Production

### Approval

- **Tested By:** ************\_************ **Date:** **\_\_\_**
- **Approved By:** **********\_\_\_********** **Date:** **\_\_\_**

### Notes & Issues

```
___________________________________________________________________
___________________________________________________________________
___________________________________________________________________
```

---

**Generated:** 2026-04-08
**ETAP 4 (Production Deployment) - User Acceptance Testing**
**ADRION 369 v4.0 - MASTER ORCHESTRATOR**
