# ETAP 2: MCP AGENTS DEPLOYMENT PLAN

**Date:** 2026-04-08
**Phase:** ETAP 2 - 6 MCP Server Deployment
**Status:** PLANNING

---

## EXECUTIVE OVERVIEW

ETAP 2 deployment activates the **6-agent swarm** (Model Context Protocol servers) that form the cognitive core of ADRION 369 v4.0:

| #   | Agent        | Role                         | Port | Module              | Status   |
| --- | ------------ | ---------------------------- | ---- | ------------------- | -------- |
| 1   | **Genesis**  | Event Sourcing Core          | 9004 | mcp_genesis_app.py  | 📋 Ready |
| 2   | **Router**   | Request Routing/Load Balance | 9001 | mcp_router_app.py   | 📋 Ready |
| 3   | **Guardian** | Security/Audit/Compliance    | 9002 | mcp_guardian_app.py | 📋 Ready |
| 4   | **Healer**   | Auto-repair/Recovery         | 9003 | mcp_healer_app.py   | 📋 Ready |
| 5   | **Oracle**   | Analytics/Prediction         | 9005 | mcp_oracle_app.py   | 📋 Ready |
| 6   | **Vortex**   | Real-time Federated Learning | 9006 | mcp_vortex_app.py   | 📋 Ready |

**Total Architecture:** 1 database + 1 cache + 6 services = Full ADRION 369 infrastructure

---

## PHASE BREAKDOWN

### Phase 1: Pre-Deployment Validation (15 min)

- Verify all .py files present
- Check dependencies installed
- Validate port availability (9001, 9002, 9003, 9004, 9005, 9006)
- Confirm .env loaded correctly

### Phase 2: Sequential Agent Startup (30 min)

- Start agents in priority order: Router → Genesis → Guardian → Healer → Oracle → Vortex
- Monitor logs for initialization errors
- Verify port listening

### Phase 3: Inter-Agent Communication (15 min)

- Test service discovery (agents find each other)
- Verify routing between agents
- Check event propagation (Genesis → Router → others)

### Phase 4: Integration Testing (20 min)

- Test 42-endpoint API surface
- Verify authentication (API keys)
- Test health checks from monitoring layer
- Confirm database writes working

### Phase 5: Deployment Gate (5 min)

- All agents running and healthy
- No errors in logs
- Ready for production

**Total Time:** ~85 minutes (1h 25m)

---

## AGENT DESCRIPTIONS & DEPENDENCIES

### 1. Router (Port 9001) - START FIRST

**Purpose:** Request routing, load balancing, message queuing
**File:** `mcp_router_app.py`
**Dependencies:**

- aiohttp (webserver)
- redis (message queue)
- asyncio (async processing)

**Startup Command:**

```bash
python mcp_router_app.py --port 9001 --log-level INFO
```

**Expected Output:**

```
Router MCP Server listening on 0.0.0.0:9001
Service discovery: READY
Message queue: redis://localhost:6379
Status: OPERATIONAL
```

---

### 2. Genesis (Port 9004) - START SECOND

**Purpose:** Event sourcing, state management, history tracking
**File:** `mcp_genesis_app.py`
**Dependencies:**

- PostgreSQL (event store)
- aiohttp (webserver)
- asyncio

**Startup Command:**

```bash
python mcp_genesis_app.py --port 9004 --db-url postgresql://adrion_app:PASSWORD@localhost:5432/genesis_record --log-level INFO
```

**Expected Output:**

```
Genesis MCP Server listening on 0.0.0.0:9004
Event store: postgres://genesis_record
State: INITIALIZED with 0 events
Status: READY for event sourcing
```

---

### 3. Guardian (Port 9002) - START THIRD

**Purpose:** Security, audit logs, 9 Laws enforcement, compliance
**File:** `mcp_guardian_app.py`
**Dependencies:**

- PostgreSQL (audit log)
- aiohttp
- cryptography (JWT, signing)

**Startup Command:**

```bash
python mcp_guardian_app.py --port 9002 --secret-key SECRET_KEY_VALUE --log-level INFO
```

**Expected Output:**

```
Guardian MCP Server listening on 0.0.0.0:9002
9 Guardian Laws: ACTIVE & MONITORED
Audit log: postgres://genesis_record.audit_log
JWT verification: ENABLED
Status: PROTECTING
```

---

### 4. Healer (Port 9003) - START FOURTH

**Purpose:** Auto-recovery, self-healing, anomaly detection
**File:** `mcp_healer_app.py`
**Dependencies:**

- PostgreSQL (recovery rules)
- asyncio
- aiohttp

**Startup Command:**

```bash
python mcp_healer_app.py --port 9003 --log-level INFO
```

**Expected Output:**

```
Healer MCP Server listening on 0.0.0.0:9003
Recovery rules loaded: N recovery procedures
Anomaly detection: ACTIVE
Health thresholds: CALIBRATED
Status: MONITORING & HEALING
```

---

### 5. Oracle (Port 9005) - START FIFTH

**Purpose:** Analytics, time-series prediction, KPI calculation
**File:** `mcp_oracle_app.py`
**Dependencies:**

- PostgreSQL (analytics tables, performance_metrics)
- numpy/pandas (analytics)
- asyncio

**Startup Command:**

```bash
python mcp_oracle_app.py --port 9005 --log-level INFO
```

**Expected Output:**

```
Oracle MCP Server listening on 0.0.0.0:9005
Analytics engine: INITIALIZED
Time-series database: postgres://performance_metrics
Prediction model: LOADED
Status: FORECASTING & ANALYZING
```

---

### 6. Vortex (Port 9006) - START LAST

**Purpose:** Real-time federated learning, model updates, swarm optimization
**File:** `mcp_vortex_app.py`
**Dependencies:**

- PostgreSQL (model store)
- Redis (federated state)
- asyncio

**Startup Command:**

```bash
python mcp_vortex_app.py --port 9006 --log-level INFO
```

**Expected Output:**

```
Vortex MCP Server listening on 0.0.0.0:9006
Federated learning: ENABLED
Model coordinator: ACTIVE
Swarm consensus: REACHED
Status: OPTIMIZING IN REAL-TIME
```

---

## STARTUP SEQUENCE

**Terminal 1 - Router (Router coordinates all traffic):**

```bash
cd c:\Users\adiha\162\ demencje\ w\ schemacie\ 369
python mcp_router_app.py --port 9001 --log-level INFO
```

**Terminal 2 - Genesis (Receives events through Router):**

```bash
cd c:\Users\adiha\162\ demencje\ w\ schemacie\ 369
python mcp_genesis_app.py --port 9004 --log-level INFO
```

**Terminal 3 - Guardian (Security oversight):**

```bash
cd c:\Users\adiha\162\ demencje\ w\ schemacie\ 369
python mcp_guardian_app.py --port 9002 --log-level INFO
```

**Terminal 4 - Healer (Self-healing):**

```bash
cd c:\Users\adiha\162\ demencje\ w\ schemacie\ 369
python mcp_healer_app.py --port 9003 --log-level INFO
```

**Terminal 5 - Oracle (Analytics):**

```bash
cd c:\Users\adiha\162\ demencje\ w\ schemacie\ 369
python mcp_oracle_app.py --port 9005 --log-level INFO
```

**Terminal 6 - Vortex (Federated learning):**

```bash
cd c:\Users\adiha\162\ demencje\ w\ schemacie\ 369
python mcp_vortex_app.py --port 9006 --log-level INFO
```

---

## API ENDPOINTS (After All Agents Running)

### Health & Status (42 total endpoints)

- `GET /health` - Full system health (Genesis)
- `GET /ready` - Kubernetes readiness (Router)
- `GET /metrics` - Prometheus metrics (Vortex)

### Authentication (Guardian)

- `POST /auth/login` - JWT token generation
- `POST /auth/validate` - Verify API key
- `GET /audit/logs` - Security audit logs
- `GET /compliance/status` - 9 Laws compliance

### Event Processing (Genesis)

- `POST /events/create` - Create event
- `GET /events/{id}` - Retrieve event
- `GET /events/stream` - Event stream (SSE)
- `POST /events/replay` - Replay history

### Routing & Load Balancing (Router)

- `POST /route/request` - Route request to agent
- `GET /route/status` - Routing status
- `GET /route/topology` - Agent topology

### Self-Healing (Healer)

- `GET /health/diagnose` - Health diagnosis
- `POST /recovery/trigger` - Trigger recovery
- `GET /recovery/status` - Recovery status

### Analytics (Oracle)

- `GET /analytics/metrics` - KPI metrics
- `GET /analytics/forecast` - Predictions
- `GET /analytics/timeseries` - Time-series data
- `POST /analytics/report` - Generate report

### Federated Learning (Vortex)

- `POST /ml/train` - Trigger training
- `GET /ml/models` - List models
- `POST /ml/inference` - Run inference
- `GET /ml/consensus` - Swarm consensus state

---

## PRE-DEPLOYMENT CHECKLIST

### System Requirements

- [ ] 6 spare ports available (9001-9006)
- [ ] PostgreSQL running and accessible
- [ ] Redis running (if using caching)
- [ ] Min 4GB RAM for 6 services (600MB per service average)
- [ ] .env loaded with all credentials from ETAP 1

### File Verification

- [ ] `mcp_router_app.py` exists
- [ ] `mcp_genesis_app.py` exists
- [ ] `mcp_guardian_app.py` exists
- [ ] `mcp_healer_app.py` exists
- [ ] `mcp_oracle_app.py` exists
- [ ] `mcp_vortex_app.py` exists

### Dependencies

- [ ] aiohttp installed (`pip list | grep aiohttp`)
- [ ] redis installed
- [ ] psycopg2 installed
- [ ] All requirements from requirements-mcp.txt

### Network & Ports

- [ ] Port 9001: Free (Router)
- [ ] Port 9002: Free (Guardian)
- [ ] Port 9003: Free (Healer)
- [ ] Port 9004: Free (Genesis)
- [ ] Port 9005: Free (Oracle)
- [ ] Port 9006: Free (Vortex)

### Database

- [ ] PostgreSQL schema applied (8 tables)
- [ ] New credentials from ETAP 1 working
- [ ] genesis_record database accessible

---

## DEPLOYMENT AUTOMATION SCRIPT

Would you like me to create an automated ETAP 2 deployment script that:

1. ✅ Verifies all files and ports
2. ✅ Starts all 6 agents in correct order
3. ✅ Monitors logs for errors
4. ✅ Runs 42-endpoint tests
5. ✅ Creates deployment report

---

## RISK MITIGATION

### If Agent Fails to Start

1. Check logs for specific error
2. Verify port is free: `netstat -tuln | grep PORT`
3. Verify database/redis connection
4. Check API keys in .env
5. Try starting in foreground for debugging

### If Agents Can't Communicate

1. Check Router is running first
2. Verify service discovery: `curl http://localhost:9001/discovery`
3. Check firewall allows port communication
4. Review logs: `grep -i "connection\|error" <agent>.log`

### Rollback Plan

- All agents are stateless (state in PostgreSQL)
- Stop agents: `pkill -f "mcp_.*_app.py"`
- Data preserved in database
- Restart: Run startup commands again

---

## SUCCESS CRITERIA

✅ **ETAP 2 Complete when:**

1. All 6 agents running (ports 9001-9006 listening)
2. No errors in any service logs
3. 42 API endpoints all responding
4. Database writes confirmed from Genesis
5. API authentication working (Guardian)
6. Health checks passing (all agents)
7. Deployment report generated

**Estimated Time to Complete:** 85 minutes
**Current Starting Point:** 2026-04-08 04:36 UTC
**Estimated Completion:** 2026-04-08 06:01 UTC

---

**Next Action:** Ready to proceed with Pre-Deployment Validation?

Choose:

- AUTO - Full automated deployment with checks
- MANUAL - Step-by-step following this plan
- REVIEW - Examine plan in detail first
