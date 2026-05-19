# PHASE A & B — IMPLEMENTATION START
**Data**: 2026-04-05 17:30 UTC
**Status**: 🚀 STARTING IMPLEMENTATION
**Participant**: QA Engineer + Backend Engineer

---

## 📋 PHASE A: UI TESTING — SETUP & EXECUTION

### ✅ STEP 1: Launch Frontend

```bash
# Option 1: Python HTTP Server
cd "c:\Users\adiha\162 demencje w schemacie 369\uap\frontend"
python -m http.server 8003

# Browser: http://localhost:8003/index.html
```

**✓ CONFIRMED**: Functions exist in app.js
- ✅ initializeTasksPanel() — line 1578
- ✅ loadAgentsList() — line 1728
- ✅ openCreateAgentModal() — line 1786
- ✅ saveAgent() — line 1817
- ✅ deleteAgent() — line 1872

---

### ✅ STEP 2: BROWSER SETUP

**Open DevTools** (F12):
```
Chrome/Firefox/Edge:
1. Press F12
2. Switch to "Console" tab
3. Watch for ERRORS (red messages)
4. Run JavaScript commands below to test
```

---

### ✅ STEP 3: PHASE A TEST EXECUTION

#### TEST 1: Verify Page Loads
```javascript
// Run in browser console:
console.log("✅ Page loaded", document.title);
console.log("✅ App.js loaded", typeof initializeTasksPanel);
console.log("✅ DOM ready", document.readyState);
```

**Expected Output**:
```
✅ Page loaded Unified Admin Panel (UAP) — ADRION 369 v4.0
✅ App.js loaded function
✅ DOM ready complete
```

---

#### TEST 2: Tasks Panel Renders
```javascript
// In console - should not throw error:
initializeTasksPanel();
console.log("✅ Tasks panel initialized");
console.log("✅ Active tasks DOM:", document.getElementById("active-tasks-list"));
```

**Check HTML**: Right-click → "Inspect" on Tasks panel (right side)
- Should see `<div id="active-tasks-list">`
- Should see `<div id="stat-completed-tasks">`
- Should see `<div id="stat-pending-tasks">`

---

#### TEST 3: Agent Manager Loads
```javascript
// In console:
loadAgentsList();
console.log("✅ Agents list loaded");
console.log("✅ Agents DOM:", document.getElementById("agents-list-container"));
```

**Check HTML**: Look for agent cards in "Agent Manager" tab
- Should see 4 agent cards (Librarian, etc.)
- Each with: name, role, personality, description, skills, trust score
- [Edytuj] and [Usuń] buttons visible

---

#### TEST 4: Create Agent Modal
```javascript
// In console:
openCreateAgentModal();
console.log("✅ Modal opened");
```

**Visual Check**:
- Modal appears centered on screen
- Form fields visible:
  - Nazwa Agenta (text)
  - Rola/Specjalizacja (text)
  - Osobowość (textarea)
  - Opis Pełny (textarea)
  - Trust Score (number)
  - Capability Level (select)
  - Umiejętności (text)
  - Aktywny (checkbox)
- [Anuluj] button closes it
- [Zapisz Agenta] button ready to click

---

#### TEST 5: Agent CRUD Operations (Mock Data)

```javascript
// Test CREATE:
document.getElementById("agent-name").value = "TestBot";
document.getElementById("agent-role").value = "Testing";
document.getElementById("agent-personality").value = "Test personality";
document.getElementById("agent-description").value = "Test description";
document.getElementById("agent-skills").value = "test,mock";
saveAgent();  // Should create agent in memory
console.log("✅ Agent created");

// Test EDIT:
editingAgentId = "agent-1";  // Set to Librarian ID
openCreateAgentModal();
console.log("✅ Edit modal open");

// Test DELETE:
deleteAgent("agent-1");
console.log("✅ Agent deleted");
```

---

#### TEST 6: Auto-Refresh Tasks Panel
```javascript
// In console:
console.log("✅ Checking auto-refresh...");
// Wait 5 seconds - tasks should update automatically
setTimeout(() => {
  console.log("✅ Tasks panel should have refreshed");
}, 5000);
```

---

### ✅ STEP 4: BROWSER CONSOLE CHECK

**STOP and CHECK**: Do you see any RED errors?

```javascript
// Copy-paste this in console to find errors:
console.clear();
console.log("=== PHASE A VALIDATION ===");
console.log("1. initializeTasksPanel exists:", typeof initializeTasksPanel === 'function' ? "✅" : "❌");
console.log("2. loadAgentsList exists:", typeof loadAgentsList === 'function' ? "✅" : "❌");
console.log("3. openCreateAgentModal exists:", typeof openCreateAgentModal === 'function' ? "✅" : "❌");
console.log("4. saveAgent exists:", typeof saveAgent === 'function' ? "✅" : "❌");
console.log("5. deleteAgent exists:", typeof deleteAgent === 'function' ? "✅" : "❌");
console.log("6. Tasks container:", document.getElementById("active-tasks-list") ? "✅" : "❌");
console.log("7. Agents container:", document.getElementById("agents-list-container") ? "✅" : "❌");
console.log("8. Modal exists:", document.getElementById("agentModal") ? "✅" : "❌");
console.log("=== RESULT ===");
console.log("If all ✅: PHASE A GREEN LIGHT! Proceed to Phase B");
```

---

## 📊 PHASE A RESULT TEMPLATE

Copy this and fill:

```
PHASE A: UI TESTING — RESULTS
Date: 2026-04-05
Tester: [Your Name]
Browser: [Chrome/Firefox/Edge] Version [XX]

=== TESTS PASSED ===
[✅ or ❌] Page loads without errors
[✅ or ❌] Tasks panel renders
[✅ or ❌] Tasks stats display
[✅ or ❌] Agent grid displays 4 agents
[✅ or ❌] Create agent modal opens
[✅ or ❌] Agent form validates
[✅ or ❌] Edit agent pre-fills form
[✅ or ❌] Delete agent removes from list
[✅ or ❌] No console errors (F12)

=== CONSOLE CHECK ===
Copy the validation script above and run.
Expected result: ALL ✅

=== ISSUES FOUND ===
[List any problems here]

=== RECOMMENDATION ===
[PROCEED TO PHASE B] / [FIX ISSUES FIRST]
```

---

## 🔧 PHASE B: BACKEND INTEGRATION — PREPARATION

### ✅ B.1: Create Database Migrations

**File**: `db/migrations/003_tasks_agents_tables.sql`

```sql
-- Drop tables if exist (for dev/testing)
DROP TABLE IF EXISTS agent_feedback;
DROP TABLE IF EXISTS agent_performance;
DROP TABLE IF EXISTS agent_activity;
DROP TABLE IF EXISTS agent_assignments;
DROP TABLE IF EXISTS agents;
DROP TABLE IF EXISTS tasks;

-- Tasks table
CREATE TABLE tasks (
    id VARCHAR(255) PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL DEFAULT 'default',
    name TEXT NOT NULL,
    agent VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    progress INT DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    eta_seconds INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration_seconds INT,
    INDEX idx_tasks_session (session_id),
    INDEX idx_tasks_status (status)
);

-- Agents table
CREATE TABLE agents (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    role VARCHAR(255),
    personality TEXT,
    description TEXT,
    trust_score FLOAT DEFAULT 0.8 CHECK (trust_score >= 0 AND trust_score <= 1),
    capability_level VARCHAR(50) CHECK (capability_level IN ('basic', 'intermediate', 'expert')),
    skills JSON,
    active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success_rate FLOAT DEFAULT 0,
    tasks_completed INT DEFAULT 0,
    INDEX idx_agents_active (active),
    INDEX idx_agents_trust (trust_score)
);

-- Insert default 4 agents
INSERT INTO agents (id, name, role, personality, description, trust_score, capability_level, skills, active, success_rate, tasks_completed)
VALUES
('agent-1', 'Librarian', 'Knowledge Management', 'Organized, precise, detail-oriented', 'Manages knowledge base, documentation, search capabilities', 0.95, 'expert', '["documentation", "search", "organization"]', 1, 0.98, 342),
('agent-2', 'Architect', 'System Design', 'Strategic, visionary, forward-thinking', 'Designs system architecture, scalability, patterns', 0.88, 'expert', '["design", "architecture", "planning"]', 1, 0.92, 187),
('agent-3', 'Auditor', 'Risk Management', 'Thorough, analytical, cautious', 'Conducts audits, identifies risks, compliance checking', 0.87, 'expert', '["audit", "risk-assessment", "compliance"]', 1, 0.91, 156),
('agent-4', 'Sentinel', 'Security & Monitoring', 'Vigilant, protective, alert', 'Monitors system health, detects threats, alerts', 0.92, 'expert', '["monitoring", "security", "alerting"]', 1, 0.95, 421);

-- Insert some mock tasks for testing
INSERT INTO tasks (id, session_id, name, agent, status, progress, eta_seconds, created_at)
VALUES
('task-001', 'default', 'Deploy Backend to Production', 'Architect', 'running', 65, 120, NOW()),
('task-002', 'default', 'Database Migration v3.2', 'SAP', 'running', 40, 300, NOW()),
('task-003', 'default', 'Security Audit Q2', 'Auditor', 'pending', 0, NULL, NOW()),
('task-004', 'default', 'System Health Check', 'Sentinel', 'completed', 100, 180, DATE_SUB(NOW(), INTERVAL 2 HOUR));
```

---

### ✅ B.2: Create Database & Load Migration

```bash
# Connect to PostgreSQL (or SQLite/MySQL depending on config)
mysql -u root -p
# or for PostgreSQL:
psql -U postgres

# Create database if not exists
CREATE DATABASE adrian_test;
USE adrian_test;

# Load migration
SOURCE db/migrations/003_tasks_agents_tables.sql;

# Verify tables created
SHOW TABLES;
# Output should show: tasks, agents

# Verify data loaded
SELECT * FROM agents;
SELECT * FROM tasks;
```

---

### ✅ B.3: Implement API Endpoints

**File**: `uap/backend/api_phase_b.py` (NEW)

Create this file with the 7 endpoints:

```python
# ──────────────────────────────────────────────────────────────────────────
# PHASE B: NEW API ENDPOINTS (7 total)
# ──────────────────────────────────────────────────────────────────────────

from flask import request, jsonify
from datetime import datetime
import uuid
import json

# Helper: Require API key authentication
def require_api_auth(f):
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get("X-API-Key")
        if api_key != "local-dev-key-123":  # Must match frontend
            return {"error": "Unauthorized"}, 401
        return f(*args, **kwargs)
    return decorated_function

# ──────────────────────────────────────────────────────────────────────────
# 1. GET /mapi/v1/tasks — List active tasks
# ──────────────────────────────────────────────────────────────────────────

@app.route("/mapi/v1/tasks", methods=["GET"])
@require_api_auth
def get_tasks():
    """Fetch all active tasks"""
    try:
        # Query database (pseudo-code - adjust to your DB)
        cursor = db.cursor()
        cursor.execute("""
            SELECT id, name, agent, status, progress, eta_seconds, created_at, updated_at
            FROM tasks
            WHERE status != 'archived'
            ORDER BY updated_at DESC
            LIMIT 50
        """)
        tasks = [dict(row) for row in cursor.fetchall()]

        return jsonify({
            "success": True,
            "tasks": tasks,
            "total": len(tasks)
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ──────────────────────────────────────────────────────────────────────────
# 2. GET /mapi/v1/tasks/stats — Task statistics
# ──────────────────────────────────────────────────────────────────────────

@app.route("/mapi/v1/tasks/stats", methods=["GET"])
@require_api_auth
def get_task_stats():
    """Get task statistics"""
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                COUNT(CASE WHEN status = 'running' THEN 1 END) as running,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending
            FROM tasks
        """)
        stats = dict(cursor.fetchone())

        return jsonify({
            "success": True,
            "completed": stats.get('completed', 0),
            "running": stats.get('running', 0),
            "failed": stats.get('failed', 0),
            "pending": stats.get('pending', 0)
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ──────────────────────────────────────────────────────────────────────────
# 3. GET /mapi/v1/agents — List all agents
# ──────────────────────────────────────────────────────────────────────────

@app.route("/mapi/v1/agents", methods=["GET"])
@require_api_auth
def list_agents():
    """Get all agents"""
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT id, name, role, personality, description, trust_score,
                   capability_level, skills, active, created_at, success_rate, tasks_completed
            FROM agents
            ORDER BY active DESC, trust_score DESC
        """)
        agents = []
        for row in cursor.fetchall():
            agent = dict(row)
            # Parse JSON skills field
            if isinstance(agent.get('skills'), str):
                agent['skills'] = json.loads(agent['skills'])
            agents.append(agent)

        return jsonify({
            "success": True,
            "agents": agents,
            "total": len(agents)
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ──────────────────────────────────────────────────────────────────────────
# 4. POST /mapi/v1/agents/create — Create new agent
# ──────────────────────────────────────────────────────────────────────────

@app.route("/mapi/v1/agents/create", methods=["POST"])
@require_api_auth
def create_agent():
    """Create new agent"""
    try:
        data = request.json

        # Validate required fields
        required = ['name', 'role', 'personality', 'description', 'capability_level']
        if not all(field in data for field in required):
            return jsonify({"error": "Missing required fields"}), 400

        agent_id = f"agent-{uuid.uuid4().hex[:8]}"
        skills_json = json.dumps(data.get('skills', []))

        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO agents
            (id, name, role, personality, description, trust_score, capability_level, skills, active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, [
            agent_id,
            data['name'],
            data['role'],
            data['personality'],
            data['description'],
            float(data.get('trust_score', 0.8)),
            data['capability_level'],
            skills_json,
            bool(data.get('active', True))
        ])
        db.commit()

        return jsonify({
            "success": True,
            "id": agent_id,
            "message": f"Agent {data['name']} created successfully"
        }), 201
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500

# ──────────────────────────────────────────────────────────────────────────
# 5. PUT /mapi/v1/agents/<agent_id> — Update agent
# ──────────────────────────────────────────────────────────────────────────

@app.route("/mapi/v1/agents/<agent_id>", methods=["PUT"])
@require_api_auth
def update_agent(agent_id):
    """Update agent"""
    try:
        data = request.json

        # Build dynamic UPDATE query
        fields = []
        values = []

        for field in ['name', 'role', 'personality', 'description', 'trust_score', 'capability_level', 'active']:
            if field in data:
                fields.append(f"{field} = %s")
                if field == 'active':
                    values.append(bool(data[field]))
                elif field == 'trust_score':
                    values.append(float(data[field]))
                else:
                    values.append(data[field])

        if 'skills' in data:
            fields.append("skills = %s")
            values.append(json.dumps(data['skills']))

        if not fields:
            return jsonify({"error": "No fields to update"}), 400

        values.append(agent_id)

        cursor = db.cursor()
        cursor.execute(f"UPDATE agents SET updated_at = NOW(), {', '.join(fields)} WHERE id = %s", values)
        db.commit()

        return jsonify({
            "success": True,
            "id": agent_id,
            "message": "Agent updated successfully"
        }), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500

# ──────────────────────────────────────────────────────────────────────────
# 6. DELETE /mapi/v1/agents/<agent_id> — Delete agent
# ──────────────────────────────────────────────────────────────────────────

@app.route("/mapi/v1/agents/<agent_id>", methods=["DELETE"])
@require_api_auth
def delete_agent(agent_id):
    """Delete agent (soft delete)"""
    try:
        cursor = db.cursor()
        cursor.execute("UPDATE agents SET active = 0, updated_at = NOW() WHERE id = %s", [agent_id])
        db.commit()

        return jsonify({
            "success": True,
            "id": agent_id,
            "message": "Agent deleted successfully"
        }), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500

# ──────────────────────────────────────────────────────────────────────────
# 7. GET /mapi/v1/agents/<agent_id> — Get single agent
# ──────────────────────────────────────────────────────────────────────────

@app.route("/mapi/v1/agents/<agent_id>", methods=["GET"])
@require_api_auth
def get_agent(agent_id):
    """Get single agent details"""
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT id, name, role, personality, description, trust_score,
                   capability_level, skills, active, created_at
            FROM agents
            WHERE id = %s
        """, [agent_id])
        result = cursor.fetchone()

        if not result:
            return jsonify({"error": "Agent not found"}), 404

        agent = dict(result)
        if isinstance(agent.get('skills'), str):
            agent['skills'] = json.loads(agent['skills'])

        return jsonify({
            "success": True,
            "agent": agent
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

**Add to `uap/backend/app.py`**:
```python
# At the top of app.py:
from api_phase_b import *

# Flask app initialization (if not already done)
app = Flask(__name__)
```

---

### ✅ B.4: Test Backend with CURL

```bash
# Test 1: Get tasks
curl -X GET http://localhost:8002/mapi/v1/tasks \
  -H "X-API-Key: local-dev-key-123" \
  -H "Content-Type: application/json"

# Test 2: Get task stats
curl -X GET http://localhost:8002/mapi/v1/tasks/stats \
  -H "X-API-Key: local-dev-key-123"

# Test 3: Get agents
curl -X GET http://localhost:8002/mapi/v1/agents \
  -H "X-API-Key: local-dev-key-123"

# Test 4: Create agent
curl -X POST http://localhost:8002/mapi/v1/agents/create \
  -H "X-API-Key: local-dev-key-123" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "TestAgent",
    "role": "Testing",
    "personality": "Test",
    "description": "Test description",
    "capability_level": "expert",
    "skills": ["test"],
    "trust_score": 0.85,
    "active": true
  }'

# Test 5: Update agent
curl -X PUT http://localhost:8002/mapi/v1/agents/agent-1 \
  -H "X-API-Key: local-dev-key-123" \
  -H "Content-Type: application/json" \
  -d '{"trust_score": 0.99}'

# Test 6: Get single agent
curl -X GET http://localhost:8002/mapi/v1/agents/agent-1 \
  -H "X-API-Key: local-dev-key-123"

# Test 7: Delete agent
curl -X DELETE http://localhost:8002/mapi/v1/agents/agent-1 \
  -H "X-API-Key: local-dev-key-123"
```

**Expected Response Pattern**:
```json
{
  "success": true,
  "agents": [...],
  "total": 4
}
```

---

### ✅ B.5: Connect Frontend to Backend

**Update in `uap/frontend/app.js`** - Replace mock data functions:

```javascript
// REPLACE initializeTasksPanel() function with:
function initializeTasksPanel() {
  updateActiveTasksList();
  // Poll every 3 seconds for real data
  setInterval(updateActiveTasksList, 3000);
}

function updateActiveTasksList() {
  // Call REAL API instead of mock
  apiCall("/tasks", "GET")
    .then(data => {
      if (!data || !data.tasks) {
        console.warn("No tasks returned from API");
        return;
      }
      renderTasks(data.tasks);

      // Also get stats
      apiCall("/tasks/stats", "GET")
        .then(stats => {
          document.getElementById("stat-completed-tasks").textContent = stats.completed || 0;
          document.getElementById("stat-pending-tasks").textContent = stats.running || 0;
          document.getElementById("stat-failed-tasks").textContent = stats.failed || 0;
        });
    });
}

// REPLACE loadAgentsList() with:
function loadAgentsList() {
  apiCall("/agents", "GET")
    .then(data => {
      if (!data || !data.agents) {
        console.warn("No agents returned from API");
        return;
      }
      agentsList = data.agents;
      renderAgents(data.agents);
    });
}
```

---

## 📋 EXECUTION CHECKLIST

### PHASE A: UI Testing
- [ ] Start frontend on http://localhost:8003
- [ ] Open DevTools (F12)
- [ ] Run validation script from console
- [ ] Check no red errors
- [ ] Test Tasks panel renders
- [ ] Test Agent Manager renders
- [ ] Test modals open/close
- [ ] **RESULT**: ✅ PASS or ❌ FIX ISSUES

### PHASE B: Backend Integration
- [ ] Create migration SQL file
- [ ] Load migration into database
- [ ] Implement 7 API endpoints
- [ ] Test each endpoint with curl
- [ ] Update frontend to use real API
- [ ] Verify tasks load from DB
- [ ] Verify agents load from DB
- [ ] Test create/edit/delete agents
- [ ] **RESULT**: ✅ PASS or ❌ FIX ISSUES

---

## 🎯 NEXT STEPS

**IF Phase A ✅ PASSES**:
→ Implement Phase B endpoints + database

**IF Phase B ✅ PASSES**:
→ Move to Phase C (Advanced Features: Analytics & Feedback)

**IF ANY ISSUES**:
→ Check DevTools console for specific error messages
→ Review curl command responses (should have "success": true)

---

**Status**: 🚀 READY FOR EXECUTION
**Estimated Time**: A: 1-2 hours | B: 2-3 hours
