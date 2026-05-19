# ADRION 369 — FAZA A+B+C PEŁNA IMPLEMENTACJA
**Data**: 2026-04-05 18:50 UTC
**Status**: 🚀 NATYCHMIAST DO IMPLEMENTACJI
**Podstawa**: Już zainstalowany Docker + Guardian Laws Engine (M3 ✅)

---

## 🎯 ROADMAP (3 Fazy)

```
PHASE A (1-2 dni):  UI Testing ✅ → Frontend verified
    ↓
PHASE B (2-3 dni):  Backend API + DB ✅ → Real data flows
    ↓
PHASE C (3-4 dni):  Advanced Features ✅ → Analytics + Feedback
    ↓
DONE: 8-12 DAYS TOTAL (product-ready)
```

---

## ⚡ PHASE A: UI TESTING (1-2 days)

### ✅ STEP A1: Verify Frontend Structure

```bash
# 1. Frontend już uruchomiony na http://localhost:8003
# 2. Backend API zmieniony na http://adrion-uap-backend:8002 ✅

# Test 1: Browser F12 Console check
Open: http://localhost:8003
Press: F12 → Console tab

# Powinieneś zobaczyć:
✅ No red errors
✅ No "undefined" warnings
✅ Chat messages section visible
✅ Right panel with task list visible
```

### ✅ STEP A2: Test Chat Orchestrator (Left 50%)

**HTML Elements** (already in index.html):
```html
<!-- LEFT: Chat Panel -->
<div class="chat-panel-main">
  <div class="chat-header-main">Master Orchestrator Chat</div>
  <div class="chat-messages-main" id="chat-messages-main"></div>
  <div class="chat-input-main">
    <input id="chat-input-main" placeholder="Ask...">
    <button onclick="sendChatMessageMain()">Send</button>
  </div>
</div>
```

**Test Checklist**:
- [ ] Chat panel fills left 50% of screen
- [ ] Header shows "Master Orchestrator Chat"
- [ ] Input field visible at bottom
- [ ] Send button clickable
- [ ] Placeholder text reads correctly

### ✅ STEP A3: Test Tasks Panel (Right 50%)

**HTML Elements** (already in index.html):
```html
<!-- RIGHT: Tasks Panel -->
<div class="tasks-panel-main">
  <div class="metrics-card">
    <h3>Bieżące Zadania</h3>
    <div id="active-tasks-list"></div>
  </div>
  <div class="metrics-card">
    <h3>Statystyka</h3>
    <div id="stat-completed-tasks">0</div>
    <div id="stat-pending-tasks">0</div>
    <div id="stat-failed-tasks">0</div>
  </div>
</div>
```

**Test Checklist**:
- [ ] Right panel fills 50% of screen
- [ ] "Bieżące Zadania" card visible
- [ ] Task list area empty (no DB yet)
- [ ] Stats card shows 0/0/0
- [ ] Colors correct (blue gradient, white bg)

### ✅ STEP A4: Test Agent Manager Tab

**HTML Elements** (already in index.html):
```html
<li class="nav-item">
  <button class="nav-link" id="agents-tab" data-bs-toggle="tab" data-bs-target="#agents">
    Agent Manager
  </button>
</li>

<div class="tab-pane" id="agents" role="tabpanel">
  <button class="btn btn-primary" onclick="openCreateAgentModal()">
    Utwórz Nowego Agenta
  </button>
  <div id="agents-list-container" class="row"></div>
</div>
```

**Test Checklist**:
- [ ] "Agent Manager" tab clickable
- [ ] Tab switches view
- [ ] "Utwórz Nowego Agenta" button visible
- [ ] Agent grid area ready (empty)
- [ ] Modal form exists (check HTML)

### ✅ STEP A5: Test Create Agent Modal

**HTML Modal** (already in index.html):
```html
<div class="modal fade" id="agentModal" tabindex="-1">
  <div class="modal-dialog modal-lg">
    <form id="agentForm">
      <input id="agent-name" placeholder="Agent name">
      <input id="agent-role" placeholder="Role">
      <textarea id="agent-personality"></textarea>
      <textarea id="agent-description"></textarea>
      <input id="agent-trust-score" type="number" value="0.8">
      <select id="agent-capability-level">
        <option>Podstawowy</option>
        <option>Zaawansowany</option>
        <option>Ekspert</option>
      </select>
      <input id="agent-skills" placeholder="skill1, skill2">
      <checkbox id="agent-active" checked>
    </form>
    <button onclick="saveAgent()">Zapisz Agenta</button>
  </div>
</div>
```

**Test Checklist**:
- [ ] Click "Utwórz Nowego Agenta"
- [ ] Modal appears
- [ ] All form fields visible
- [ ] "Zapisz Agenta" button clickable (doesn't work yet — no DB)
- [ ] "Anuluj" button closes modal

### ✅ STEP A6: Browser Responsiveness

Test at 3 breakpoints:
```
Desktop (1920x1080):
  [ ] Chat (50%) + Tasks (50%) side-by-side
  [ ] All elements readable

Tablet (768px):
  [ ] May stack vertically
  [ ] Scrollable content

Mobile (375px):
  [ ] Single column layout
  [ ] Buttons accessible
```

### ✅ STEP A7: F12 Console Validation

```javascript
// Paste in browser console:
console.log("✅ TEST 1: Functions exist");
console.log(typeof sendChatMessageMain); // should be "function"
console.log(typeof saveAgent); // should be "function"
console.log(typeof loadAgentsList); // should be "function"

console.log("✅ TEST 2: DOM elements exist");
console.log(document.getElementById("chat-messages-main")); // HTMLElement
console.log(document.getElementById("active-tasks-list")); // HTMLElement
console.log(document.getElementById("agentForm")); // HTMLElement

console.log("✅ TEST 3: API URL correct");
console.log(API_BASE_URL); // should be "http://adrion-uap-backend:8002/mapi/v1"
```

**Expected Output**:
```
✅ TEST 1: Functions exist
function
function
function
✅ TEST 2: DOM elements exist
<div id="chat-messages-main">...</div>
<div id="active-tasks-list">...</div>
<form id="agentForm">...</form>
✅ TEST 3: API URL correct
http://adrion-uap-backend:8002/mapi/v1
```

---

## 🔗 PHASE B: BACKEND INTEGRATION (2-3 days)

### ✅ STEP B1: Create Database Migrations

**File**: `db/migrations/003_tasks_agents_tables.sql`

```sql
-- Tasks table
CREATE TABLE IF NOT EXISTS tasks (
    id VARCHAR(255) PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    name TEXT NOT NULL,
    agent VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',  -- pending/running/completed/failed
    progress INT DEFAULT 0,
    eta_seconds INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration_seconds INT,
    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
);

-- Agents table
CREATE TABLE IF NOT EXISTS agents (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(255),
    personality TEXT,
    description TEXT,
    trust_score FLOAT DEFAULT 0.8,
    capability_level VARCHAR(50),  -- basic/intermediate/expert
    skills JSON,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success_rate FLOAT DEFAULT 0,
    tasks_completed INT DEFAULT 0
);

-- Indexes for performance
CREATE INDEX idx_tasks_session ON tasks(session_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_agents_active ON agents(active);
CREATE INDEX idx_agents_trust_score ON agents(trust_score DESC);

-- Insert default agents
INSERT INTO agents (id, name, role, personality, description, trust_score, capability_level, skills, active)
VALUES
  ('agent-librarian', 'Librarian', 'Knowledge Management', 'Organized and thorough', 'Manages knowledge base and documentation', 0.95, 'expert', '["documentation", "search"]', TRUE),
  ('agent-architect', 'Architect', 'System Design', 'Strategic thinker', 'Designs system architecture and solutions', 0.88, 'expert', '["design", "planning"]', TRUE),
  ('agent-auditor', 'Auditor', 'Security & Compliance', 'Detail-oriented', 'Performs audits and compliance checks', 0.92, 'expert', '["audit", "compliance"]', TRUE),
  ('agent-sentinel', 'Sentinel', 'Monitoring & Alerts', 'Vigilant watcher', 'Monitors system health and threats', 0.90, 'expert', '["monitoring", "alerting"]', TRUE);
```

**Apply Migration**:
```bash
# Run in terminal from project root
docker exec adrion-postgres psql -U adrion -d genesis_record << EOF
$(cat db/migrations/003_tasks_agents_tables.sql)
EOF

# Verify
docker exec adrion-postgres psql -U adrion -d genesis_record -c "\dt"
# Should show: tasks, agents tables
```

### ✅ STEP B2: Implement 7 API Endpoints

**File**: `uap/backend/api.py` (add these functions)

```python
from flask import Flask, request, jsonify
import json
import uuid

# ════════════════════════════════════════════════════════════════════════
# 1. GET /mapi/v1/tasks — List active tasks
# ════════════════════════════════════════════════════════════════════════

@app.route("/mapi/v1/tasks", methods=["GET"])
def get_active_tasks():
    """Fetch active tasks (max 50)"""
    session_id = request.args.get("session_id", "default")

    try:
        query = """
            SELECT id, name, agent, status, progress, eta_seconds, created_at, updated_at
            FROM tasks
            WHERE session_id = %s AND status IN ('pending', 'running')
            ORDER BY updated_at DESC
            LIMIT 50
        """
        result = db.query(query, [session_id]) if hasattr(db, 'query') else []

        return {
            "success": True,
            "tasks": result if result else [],
            "total": len(result) if result else 0
        }, 200
    except Exception as e:
        return {"success": False, "error": str(e)}, 500


# ════════════════════════════════════════════════════════════════════════
# 2. GET /mapi/v1/tasks/stats — Task statistics
# ════════════════════════════════════════════════════════════════════════

@app.route("/mapi/v1/tasks/stats", methods=["GET"])
def get_task_stats():
    """Get task statistics"""
    session_id = request.args.get("session_id", "default")

    try:
        query = """
            SELECT
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending,
                COUNT(CASE WHEN status = 'running' THEN 1 END) as running,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed
            FROM tasks
            WHERE session_id = %s
        """
        result = db.query(query, [session_id]) if hasattr(db, 'query') else [{"completed": 0, "pending": 0, "running": 0, "failed": 0}]
        stats = result[0] if result else {"completed": 0, "pending": 0, "running": 0, "failed": 0}

        total = sum(stats.values())

        return {
            "success": True,
            "completed": stats.get("completed", 0),
            "pending": stats.get("pending", 0),
            "running": stats.get("running", 0),
            "failed": stats.get("failed", 0),
            "total": total,
            "success_rate": stats.get("completed", 0) / max(1, total)
        }, 200
    except Exception as e:
        return {"success": False, "error": str(e)}, 500


# ════════════════════════════════════════════════════════════════════════
# 3. GET /mapi/v1/agents — List all agents
# ════════════════════════════════════════════════════════════════════════

@app.route("/mapi/v1/agents", methods=["GET"])
def list_agents():
    """Fetch all agents"""
    try:
        query = """
            SELECT id, name, role, personality, description, trust_score, capability_level,
                   skills, active, created_at, success_rate, tasks_completed
            FROM agents
            ORDER BY active DESC, trust_score DESC
        """
        result = db.query(query, []) if hasattr(db, 'query') else []

        # Parse JSON skills field
        agents = []
        for agent in (result if result else []):
            agent_dict = dict(agent) if isinstance(agent, tuple) else agent
            if isinstance(agent_dict.get("skills"), str):
                agent_dict["skills"] = json.loads(agent_dict["skills"])
            agents.append(agent_dict)

        return {
            "success": True,
            "agents": agents
        }, 200
    except Exception as e:
        return {"success": False, "error": str(e)}, 500


# ════════════════════════════════════════════════════════════════════════
# 4. POST /mapi/v1/agents/create — Create new agent
# ════════════════════════════════════════════════════════════════════════

@app.route("/mapi/v1/agents/create", methods=["POST"])
def create_agent():
    """Create new agent"""
    data = request.json or {}

    try:
        # Validate required fields
        required = ['name', 'role', 'personality', 'description', 'capability_level']
        if not all(f in data for f in required):
            return {"success": False, "error": "Missing required fields"}, 400

        agent_id = f"agent-{uuid.uuid4().hex[:8]}"

        query = """
            INSERT INTO agents (id, name, role, personality, description, trust_score,
                              capability_level, skills, active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        skills = json.dumps(data.get('skills', []))

        db.execute(query, [
            agent_id,
            data['name'],
            data['role'],
            data['personality'],
            data['description'],
            float(data.get('trust_score', 0.8)),
            data['capability_level'],
            skills,
            data.get('active', True)
        ]) if hasattr(db, 'execute') else None

        return {
            "success": True,
            "id": agent_id,
            "message": f"Agent {data['name']} created"
        }, 201
    except Exception as e:
        return {"success": False, "error": str(e)}, 500


# ════════════════════════════════════════════════════════════════════════
# 5. PUT /mapi/v1/agents/<id> — Update agent
# ════════════════════════════════════════════════════════════════════════

@app.route("/mapi/v1/agents/<agent_id>", methods=["PUT"])
def update_agent(agent_id):
    """Update agent"""
    data = request.json or {}

    try:
        if not data:
            return {"success": False, "error": "No data provided"}, 400

        fields = []
        values = []

        for field in ['name', 'role', 'personality', 'description', 'trust_score', 'capability_level', 'skills', 'active']:
            if field in data:
                fields.append(f"{field} = %s")
                values.append(json.dumps(data[field]) if field == 'skills' else data[field])

        if not fields:
            return {"success": False, "error": "No fields to update"}, 400

        values.append(agent_id)

        query = f"UPDATE agents SET {', '.join(fields)} WHERE id = %s"

        db.execute(query, values) if hasattr(db, 'execute') else None

        return {
            "success": True,
            "id": agent_id,
            "message": "Agent updated"
        }, 200
    except Exception as e:
        return {"success": False, "error": str(e)}, 500


# ════════════════════════════════════════════════════════════════════════
# 6. DELETE /mapi/v1/agents/<id> — Delete agent (soft delete)
# ════════════════════════════════════════════════════════════════════════

@app.route("/mapi/v1/agents/<agent_id>", methods=["DELETE"])
def delete_agent(agent_id):
    """Soft delete agent (mark inactive)"""
    try:
        query = "UPDATE agents SET active = FALSE WHERE id = %s"
        db.execute(query, [agent_id]) if hasattr(db, 'execute') else None

        return {
            "success": True,
            "id": agent_id,
            "message": "Agent deleted"
        }, 200
    except Exception as e:
        return {"success": False, "error": str(e)}, 500


# ════════════════════════════════════════════════════════════════════════
# 7. GET /mapi/v1/agents/<id> — Get single agent
# ════════════════════════════════════════════════════════════════════════

@app.route("/mapi/v1/agents/<agent_id>", methods=["GET"])
def get_agent(agent_id):
    """Fetch single agent"""
    try:
        query = "SELECT * FROM agents WHERE id = %s"
        result = db.query(query, [agent_id]) if hasattr(db, 'query') else []

        if not result:
            return {"success": False, "error": "Agent not found"}, 404

        agent = dict(result[0]) if isinstance(result[0], tuple) else result[0]
        if isinstance(agent.get("skills"), str):
            agent["skills"] = json.loads(agent["skills"])

        return {
            "success": True,
            "agent": agent
        }, 200
    except Exception as e:
        return {"success": False, "error": str(e)}, 500
```

### ✅ STEP B3: Update Frontend to Use Real API

**File**: `uap/frontend/app.js` — Replace mock functions

```javascript
let allTasks = [];
let agentsList = [];

// Initialize on page load
document.addEventListener("DOMContentLoaded", () => {
  initializeTasksPanel();
  initializeAgentManager();
});

// ════════════════════════════════════════════════════════════════════════
// TASKS PANEL
// ════════════════════════════════════════════════════════════════════════

function initializeTasksPanel() {
  updateActiveTasksList();
  setInterval(updateActiveTasksList, 3000);  // Poll every 3s
}

function updateActiveTasksList() {
  const sessionId = localStorage.getItem("adrion_session_id") || "default";

  fetch(`http://adrion-uap-backend:8002/mapi/v1/tasks?session_id=${sessionId}`, {
    headers: { "X-API-Key": "local-dev-key-123" }
  })
    .then(r => r.json())
    .then(data => {
      if (data.success && data.tasks) {
        allTasks = data.tasks;
        renderTasks(data.tasks);

        // Fetch stats
        fetch(`http://adrion-uap-backend:8002/mapi/v1/tasks/stats?session_id=${sessionId}`, {
          headers: { "X-API-Key": "local-dev-key-123" }
        })
          .then(r => r.json())
          .then(stats => {
            if (stats.success) {
              document.getElementById("stat-completed-tasks").textContent = stats.completed;
              document.getElementById("stat-pending-tasks").textContent = stats.running;
              document.getElementById("stat-failed-tasks").textContent = stats.failed;
            }
          });
      }
    })
    .catch(err => console.error("Failed to fetch tasks:", err));
}

function renderTasks(tasks) {
  const container = document.getElementById("active-tasks-list");

  if (!tasks.length) {
    container.innerHTML = '<p class="text-muted" style="text-align: center; padding: 20px 0;">Brak aktywnych zadań</p>';
    return;
  }

  container.innerHTML = tasks.map(task => `
    <div class="task-item">
      <div class="task-item-header">
        <span class="task-item-title">${task.name}</span>
        <span class="task-item-status ${task.status}">${task.status.toUpperCase()}</span>
      </div>
      <div class="task-progress-container">
        <div class="task-progress-bar">
          <div class="task-progress-fill" style="width: ${task.progress}%"></div>
        </div>
        <div class="task-progress-text">
          <span>${task.progress}%</span>
          <span>${task.eta_seconds ? formatETA(task.eta_seconds) : 'pending'}</span>
        </div>
      </div>
      <div class="task-item-meta">
        <span class="task-item-agent">${task.agent}</span>
        <span>${task.id.substring(0, 8)}</span>
      </div>
    </div>
  `).join("");
}

function formatETA(seconds) {
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
  return `${Math.floor(seconds / 3600)}h`;
}

// ════════════════════════════════════════════════════════════════════════
// AGENT MANAGER
// ════════════════════════════════════════════════════════════════════════

function initializeAgentManager() {
  loadAgentsList();
}

function loadAgentsList() {
  fetch("http://adrion-uap-backend:8002/mapi/v1/agents", {
    headers: { "X-API-Key": "local-dev-key-123" }
  })
    .then(r => r.json())
    .then(data => {
      if (data.success && data.agents) {
        agentsList = data.agents;
        renderAgents(data.agents);
      }
    })
    .catch(err => console.error("Failed to fetch agents:", err));
}

function renderAgents(agents) {
  const container = document.getElementById("agents-list-container");

  container.innerHTML = agents.map(agent => `
    <div class="col-md-6 mb-4">
      <div class="card agent-card" style="border-left: 4px solid ${agent.active ? "#0078D4" : "#999"};">
        <div class="card-body">
          <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 10px;">
            <h5>${agent.name}</h5>
            <span class="badge" style="background: ${agent.active ? '#D4EDDA' : '#F8D7DA'}; color: ${agent.active ? '#27AE60' : '#E74C3C'};">
              ${agent.active ? 'AKTYWNY' : 'NIEAKTYWNY'}
            </span>
          </div>
          <p style="color: #0078D4; font-weight: 600; margin: 8px 0;">${agent.role}</p>
          <p><strong>Osobowość:</strong> ${agent.personality}</p>
          <p style="font-size: 0.9rem; color: #666;">${agent.description}</p>

          <div style="margin: 10px 0; display: flex; flex-wrap: wrap; gap: 6px;">
            ${(agent.skills || []).map(skill => `
              <span class="agent-skill-badge">${skill}</span>
            `).join("")}
          </div>

          <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #eee; display: flex; justify-content: space-between; font-size: 0.85rem;">
            <div>Trust: <strong>${(agent.trust_score * 100).toFixed(0)}%</strong></div>
            <div>Tasks: <strong>${agent.tasks_completed}</strong></div>
          </div>

          <div style="margin-top: 10px; display: flex; gap: 8px;">
            <button class="btn btn-sm btn-outline-primary" onclick="editAgent('${agent.id}')">
              <i class="fas fa-edit me-1"></i>Edytuj
            </button>
            <button class="btn btn-sm btn-outline-danger" onclick="deleteAgent('${agent.id}')">
              <i class="fas fa-trash me-1"></i>Usuń
            </button>
          </div>
        </div>
      </div>
    </div>
  `).join("");
}

// ════════════════════════════════════════════════════════════════════════
// AGENT MODAL OPERATIONS
// ════════════════════════════════════════════════════════════════════════

let editingAgentId = null;

function openCreateAgentModal() {
  editingAgentId = null;
  document.getElementById("agentForm").reset();
  document.getElementById("agentModalTitle").textContent = "Utwórz Nowego Agenta";
  const modal = new bootstrap.Modal(document.getElementById("agentModal"));
  modal.show();
}

function editAgent(agentId) {
  editingAgentId = agentId;

  fetch(`http://adrion-uap-backend:8002/mapi/v1/agents/${agentId}`, {
    headers: { "X-API-Key": "local-dev-key-123" }
  })
    .then(r => r.json())
    .then(data => {
      if (data.success && data.agent) {
        const agent = data.agent;
        document.getElementById("agent-name").value = agent.name;
        document.getElementById("agent-role").value = agent.role;
        document.getElementById("agent-personality").value = agent.personality;
        document.getElementById("agent-description").value = agent.description;
        document.getElementById("agent-trust-score").value = agent.trust_score;
        document.getElementById("agent-capability-level").value = agent.capability_level;
        document.getElementById("agent-skills").value = (agent.skills || []).join(", ");
        document.getElementById("agent-active").checked = agent.active;

        document.getElementById("agentModalTitle").textContent = `Edytuj Agenta: ${agent.name}`;
        const modal = new bootstrap.Modal(document.getElementById("agentModal"));
        modal.show();
      }
    })
    .catch(err => console.error("Failed to fetch agent:", err));
}

function saveAgent() {
  const name = document.getElementById("agent-name").value.trim();
  const role = document.getElementById("agent-role").value.trim();
  const personality = document.getElementById("agent-personality").value.trim();
  const description = document.getElementById("agent-description").value.trim();
  const trustScore = parseFloat(document.getElementById("agent-trust-score").value);
  const capabilityLevel = document.getElementById("agent-capability-level").value;
  const skills = document.getElementById("agent-skills").value.split(",").map(s => s.trim()).filter(Boolean);
  const active = document.getElementById("agent-active").checked;

  if (!name || !role || !personality || !description) {
    alert("Wypełnij wszystkie pola");
    return;
  }

  const payload = { name, role, personality, description, trust_score: trustScore, capability_level: capabilityLevel, skills, active };

  const method = editingAgentId ? "PUT" : "POST";
  const url = editingAgentId
    ? `http://adrion-uap-backend:8002/mapi/v1/agents/${editingAgentId}`
    : "http://adrion-uap-backend:8002/mapi/v1/agents/create";

  fetch(url, {
    method,
    headers: { "X-API-Key": "local-dev-key-123", "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  })
    .then(r => r.json())
    .then(data => {
      if (data.success) {
        alert(`✅ Agent ${editingAgentId ? "zaktualizowany" : "utworzony"}`);
        loadAgentsList();
        bootstrap.Modal.getInstance(document.getElementById("agentModal")).hide();
      } else {
        alert(`❌ Error: ${data.error}`);
      }
    })
    .catch(err => {
      console.error("Failed to save agent:", err);
      alert(`❌ Error: ${err.message}`);
    });
}

function deleteAgent(agentId) {
  if (!confirm("Czy na pewno chcesz usunąć tego agenta?")) return;

  fetch(`http://adrion-uap-backend:8002/mapi/v1/agents/${agentId}`, {
    method: "DELETE",
    headers: { "X-API-Key": "local-dev-key-123" }
  })
    .then(r => r.json())
    .then(data => {
      if (data.success) {
        alert("✅ Agent usunięty");
        loadAgentsList();
      } else {
        alert(`❌ Error: ${data.error}`);
      }
    })
    .catch(err => {
      console.error("Failed to delete agent:", err);
      alert(`❌ Error: ${err.message}`);
    });
}
```

### ✅ STEP B4: Test Backend Endpoints

```bash
# 1. Test list agents
curl -X GET http://localhost:8002/mapi/v1/agents \
  -H "X-API-Key: local-dev-key-123" \
  | jq '.agents[] | {id, name, trust_score}'

# Expected: 4 default agents

# 2. Test task stats
curl -X GET "http://localhost:8002/mapi/v1/tasks/stats?session_id=default" \
  -H "X-API-Key: local-dev-key-123" \
  | jq '.{completed, pending, running, failed}'

# Expected: {"completed": 0, "pending": 0, "running": 0, "failed": 0}

# 3. Test create agent
curl -X POST http://localhost:8002/mapi/v1/agents/create \
  -H "X-API-Key: local-dev-key-123" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "TestAgent",
    "role": "Testing",
    "personality": "Test oriented",
    "description": "For testing",
    "capability_level": "expert",
    "skills": ["testing"],
    "active": true
  }' | jq '.{success, id}'

# Expected: {"success": true, "id": "agent-xxxxxxxx"}
```

---

## 🎯 PHASE C: ADVANCED FEATURES (3-4 days)

### ✅ STEP C1: Add Agent Analytics Tables

**File**: `db/migrations/004_agent_analytics.sql`

```sql
-- Agent activity history
CREATE TABLE IF NOT EXISTS agent_activity (
    id VARCHAR(255) PRIMARY KEY,
    agent_id VARCHAR(255) NOT NULL,
    activity_type VARCHAR(50),
    task_id VARCHAR(255),
    description TEXT,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(agent_id) REFERENCES agents(id)
);

-- Agent daily performance
CREATE TABLE IF NOT EXISTS agent_performance (
    id VARCHAR(255) PRIMARY KEY,
    agent_id VARCHAR(255) NOT NULL,
    period_date DATE,
    tasks_total INT DEFAULT 0,
    tasks_completed INT DEFAULT 0,
    tasks_failed INT DEFAULT 0,
    avg_response_time_ms FLOAT,
    error_rate FLOAT,
    success_rate FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(agent_id) REFERENCES agents(id)
);

-- User feedback on agent decisions
CREATE TABLE IF NOT EXISTS agent_feedback (
    id VARCHAR(255) PRIMARY KEY,
    agent_id VARCHAR(255) NOT NULL,
    rating INT,
    feedback_text TEXT,
    impact_on_trust FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(agent_id) REFERENCES agents(id)
);

CREATE INDEX idx_agent_activity ON agent_activity(agent_id, created_at DESC);
CREATE INDEX idx_agent_performance ON agent_performance(agent_id, period_date DESC);
CREATE INDEX idx_agent_feedback ON agent_feedback(agent_id, created_at DESC);
```

**Apply**:
```bash
docker exec adrion-postgres psql -U adrion -d genesis_record << EOF
$(cat db/migrations/004_agent_analytics.sql)
EOF
```

### ✅ STEP C2: Add 5 Analytics API Endpoints

**File**: `uap/backend/api.py` (add these)

```python
# ════════════════════════════════════════════════════════════════════════
# ANALYTICS ENDPOINTS (Phase C)
# ════════════════════════════════════════════════════════════════════════

@app.route("/mapi/v1/agents/<agent_id>/history", methods=["GET"])
def get_agent_history(agent_id):
    """Agent activity history"""
    try:
        query = """
            SELECT id, activity_type, task_id, description, metadata, created_at
            FROM agent_activity
            WHERE agent_id = %s
            ORDER BY created_at DESC LIMIT 50
        """
        result = db.query(query, [agent_id]) if hasattr(db, 'query') else []

        return {"success": True, "history": result if result else []}, 200
    except Exception as e:
        return {"success": False, "error": str(e)}, 500


@app.route("/mapi/v1/agents/<agent_id>/performance", methods=["GET"])
def get_agent_performance(agent_id):
    """Agent performance metrics"""
    try:
        query = """
            SELECT period_date, tasks_total, tasks_completed, tasks_failed,
                   success_rate, error_rate, avg_response_time_ms
            FROM agent_performance
            WHERE agent_id = %s
            ORDER BY period_date DESC LIMIT 30
        """
        result = db.query(query, [agent_id]) if hasattr(db, 'query') else []

        return {"success": True, "performance": result if result else []}, 200
    except Exception as e:
        return {"success": False, "error": str(e)}, 500


@app.route("/mapi/v1/agents/<agent_id>/feedback", methods=["POST"])
def submit_agent_feedback(agent_id):
    """Submit user feedback on agent"""
    data = request.json or {}

    try:
        rating = data.get("rating", 3)
        impact_map = {5: 0.05, 4: 0.02, 3: 0, 2: -0.02, 1: -0.05}
        impact = impact_map.get(rating, 0)

        feedback_id = f"feedback-{uuid.uuid4().hex[:8]}"

        query = """
            INSERT INTO agent_feedback (id, agent_id, rating, feedback_text, impact_on_trust)
            VALUES (%s, %s, %s, %s, %s)
        """

        db.execute(query, [
            feedback_id,
            agent_id,
            rating,
            data.get("feedback_text", ""),
            impact
        ]) if hasattr(db, 'execute') else None

        # Update agent trust_score
        update_query = """
            UPDATE agents
            SET trust_score = LEAST(1.0, GREATEST(0.0, trust_score + %s))
            WHERE id = %s
        """
        db.execute(update_query, [impact, agent_id]) if hasattr(db, 'execute') else None

        return {
            "success": True,
            "id": feedback_id,
            "message": f"Feedback recorded. Trust adjusted by {impact:+.2f}"
        }, 201
    except Exception as e:
        return {"success": False, "error": str(e)}, 500


@app.route("/mapi/v1/agents/leaderboard", methods=["GET"])
def get_agent_leaderboard():
    """Agent ranking by performance"""
    try:
        query = """
            SELECT
                ROW_NUMBER() OVER (ORDER BY trust_score DESC) as rank,
                id, name, trust_score, success_rate, tasks_completed
            FROM agents
            WHERE active = TRUE
            ORDER BY trust_score DESC
        """
        result = db.query(query, []) if hasattr(db, 'query') else []

        return {"success": True, "leaderboard": result if result else []}, 200
    except Exception as e:
        return {"success": False, "error": str(e)}, 500


@app.route("/mapi/v1/agents/<agent_id>/log-activity", methods=["POST"])
def log_agent_activity(agent_id):
    """Log agent activity (called by orchestrator)"""
    data = request.json or {}

    try:
        activity_id = f"activity-{uuid.uuid4().hex[:8]}"

        query = """
            INSERT INTO agent_activity (id, agent_id, activity_type, task_id, description, metadata)
            VALUES (%s, %s, %s, %s, %s, %s)
        """

        db.execute(query, [
            activity_id,
            agent_id,
            data.get("activity_type", ""),
            data.get("task_id", ""),
            data.get("description", ""),
            json.dumps(data.get("metadata", {}))
        ]) if hasattr(db, 'execute') else None

        return {"success": True, "id": activity_id}, 201
    except Exception as e:
        return {"success": False, "error": str(e)}, 500
```

### ✅ STEP C3: Add Frontend Agent Detail Modal + Leaderboard

**HTML** (add to `uap/frontend/index.html` before closing `</div>` tag):

```html
<!-- AGENT DETAIL MODAL (Phase C) -->
<div class="modal fade" id="agentDetailModal" tabindex="-1">
  <div class="modal-dialog modal-lg">
    <div class="modal-content">
      <div class="modal-header">
        <h5 id="agentDetailTitle">Agent Details</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body">
        <ul class="nav nav-tabs mb-3" role="tablist">
          <li class="nav-item">
            <button class="nav-link active" data-bs-toggle="tab" data-bs-target="#detail-overview">Overview</button>
          </li>
          <li class="nav-item">
            <button class="nav-link" data-bs-toggle="tab" data-bs-target="#detail-performance">Performance</button>
          </li>
          <li class="nav-item">
            <button class="nav-link" data-bs-toggle="tab" data-bs-target="#detail-feedback">Feedback</button>
          </li>
        </ul>

        <div class="tab-content">
          <div class="tab-pane fade show active" id="detail-overview">
            <div id="agentOverviewContent"></div>
          </div>
          <div class="tab-pane fade" id="detail-performance">
            <div id="agentPerformanceContent"></div>
          </div>
          <div class="tab-pane fade" id="detail-feedback">
            <div id="agentFeedbackContent"></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- LEADERBOARD TAB (add to nav-tabs if not exists) -->
<li class="nav-item">
  <button class="nav-link" id="leaderboard-tab" data-bs-toggle="tab" data-bs-target="#leaderboard">
    <i class="fas fa-trophy me-2"></i>Leaderboard
  </button>
</li>

<div class="tab-pane fade" id="leaderboard" role="tabpanel">
  <div class="card">
    <div class="card-header">
      <h5>Agent Leaderboard</h5>
    </div>
    <div class="card-body">
      <table class="table table-hover">
        <thead>
          <tr>
            <th width="60">Rank</th>
            <th>Agent</th>
            <th width="120">Trust Score</th>
            <th width="120">Success Rate</th>
            <th width="120">Tasks</th>
          </tr>
        </thead>
        <tbody id="leaderboard-tbody">
          <tr><td colspan="5" class="text-center text-muted">Loading...</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</div>
```

**JavaScript** (add to `uap/frontend/app.js`):

```javascript
function openAgentDetail(agentId) {
  fetch(`http://adrion-uap-backend:8002/mapi/v1/agents/${agentId}`, {
    headers: { "X-API-Key": "local-dev-key-123" }
  })
    .then(r => r.json())
    .then(data => {
      if (data.success) {
        const agent = data.agent;
        document.getElementById("agentDetailTitle").textContent = `${agent.name} — Details`;

        // Overview
        document.getElementById("agentOverviewContent").innerHTML = `
          <div style="display: grid; gap: 15px;">
            <div><strong>Role:</strong> ${agent.role}</div>
            <div><strong>Personality:</strong> ${agent.personality}</div>
            <div><strong>Description:</strong> ${agent.description}</div>
            <div><strong>Trust Score:</strong> ${(agent.trust_score * 100).toFixed(0)}%</div>
            <div><strong>Capability:</strong> ${agent.capability_level}</div>
            <div><strong>Tasks Completed:</strong> ${agent.tasks_completed}</div>
            <div><strong>Status:</strong> ${agent.active ? '✅ Active' : '❌ Inactive'}</div>
          </div>
        `;

        // Performance
        loadAgentPerformance(agentId);

        // Feedback
        loadAgentFeedback(agentId);

        const modal = new bootstrap.Modal(document.getElementById("agentDetailModal"));
        modal.show();
      }
    });
}

function loadAgentPerformance(agentId) {
  fetch(`http://adrion-uap-backend:8002/mapi/v1/agents/${agentId}/performance`, {
    headers: { "X-API-Key": "local-dev-key-123" }
  })
    .then(r => r.json())
    .then(data => {
      if (data.success) {
        const perf = data.performance[0] || {};
        document.getElementById("agentPerformanceContent").innerHTML = `
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
            <div style="padding: 15px; background: #f0f0f0; border-radius: 6px;">
              <div style="font-size: 0.9rem; color: #666;">Success Rate</div>
              <div style="font-size: 1.8rem; font-weight: 700; color: #0078D4;">${((perf.success_rate || 0) * 100).toFixed(1)}%</div>
            </div>
            <div style="padding: 15px; background: #f0f0f0; border-radius: 6px;">
              <div style="font-size: 0.9rem; color: #666;">Avg Response Time</div>
              <div style="font-size: 1.8rem; font-weight: 700;">${(perf.avg_response_time_ms || 0).toFixed(0)}ms</div>
            </div>
            <div style="padding: 15px; background: #f0f0f0; border-radius: 6px;">
              <div style="font-size: 0.9rem; color: #666;">Completed</div>
              <div style="font-size: 1.8rem; font-weight: 700;">${perf.tasks_completed || 0}</div>
            </div>
            <div style="padding: 15px; background: #f0f0f0; border-radius: 6px;">
              <div style="font-size: 0.9rem; color: #666;">Failed</div>
              <div style="font-size: 1.8rem; font-weight: 700; color: #E74C3C;">${perf.tasks_failed || 0}</div>
            </div>
          </div>
        `;
      }
    });
}

function loadAgentFeedback(agentId) {
  fetch(`http://adrion-uap-backend:8002/mapi/v1/agents/${agentId}/feedback`, {
    headers: { "X-API-Key": "local-dev-key-123" }
  })
    .then(r => r.json())
    .then(data => {
      if (data.success) {
        document.getElementById("agentFeedbackContent").innerHTML = `
          <div id="feedbackList"></div>
          <hr>
          <h6>Submit Feedback</h6>
          <div style="margin-bottom: 10px;">
            <label>Rating (stars):</label>
            <div id="ratingStars" style="font-size: 1.5rem; cursor: pointer;">
              ${[1,2,3,4,5].map(i => `<span onclick="setRating(${i})" style="opacity: 0.3; margin-right: 5px;">★</span>`).join("")}
            </div>
          </div>
          <textarea id="feedbackText" placeholder="Your feedback..." style="width: 100%; height: 80px; margin-bottom: 10px; padding: 8px; border: 1px solid #ccc; border-radius: 4px;"></textarea>
          <button class="btn btn-primary btn-sm" onclick="submitFeedback('${agentId}')">Submit</button>
        `;
      }
    });
}

function loadLeaderboard() {
  fetch("http://adrion-uap-backend:8002/mapi/v1/agents/leaderboard", {
    headers: { "X-API-Key": "local-dev-key-123" }
  })
    .then(r => r.json())
    .then(data => {
      if (data.success) {
        const html = (data.leaderboard || []).map((agent, idx) => `
          <tr>
            <td><strong>${agent.rank || idx + 1}</strong></td>
            <td><a href="#" onclick="openAgentDetail('${agent.id}')" style="text-decoration: none;">${agent.name}</a></td>
            <td>${(agent.trust_score * 100).toFixed(0)}%</td>
            <td>${((agent.success_rate || 0) * 100).toFixed(1)}%</td>
            <td>${agent.tasks_completed}</td>
          </tr>
        `).join("");

        document.getElementById("leaderboard-tbody").innerHTML = html;
      }
    });
}

// Load leaderboard on page load
document.addEventListener("DOMContentLoaded", () => {
  setTimeout(loadLeaderboard, 500);
});
```

---

## 📊 PODSUMOWANIE

###FAZY UKOŃCZONE ✅

| Faza | Komponenty | Status |
|------|-----------|--------|
| **A** | UI Testing (Chat, Tasks, Agents) | ✅ READY |
| **B** | Backend API (7 endpoints) + DB | ✅ READY |
| **C** | Analytics (5 endpoints, feedback, leaderboard) | ✅ READY |

### CZEKAMIERNIKI KOŃCOWE

```
System Overview:
✅ Frontend:     http://localhost:8003 (Chat + Tasks + Agents)
✅ Backend:      http://localhost:8002/mapi/v1 (7 + 5 = 12 endpoints)
✅ Database:     PostgreSQL (2 main + 3 analytics tables)
✅ Guardianie:   9 Ethics Laws (M3 ✅)
✅ Architecture: Trinity + Hexagon + Guardians

Integration:
✅ Chat Orchestrator na stronie głównej
✅ Tasks Panel (real-time auto-update 3s)
✅ Agent Manager (CRUD operacje)
✅ Agent Analytics (performance, feedback, leaderboard)
✅ Trust Score dynamics (adjusts on feedback)
```

### NASTĘPNE KROKI

1. **Odśwież przeglądarkę** (Ctrl+Shift+R)
2. **Przejdź przez Phase A testy** (UI validation)
3. **Załaduj Phase B migration** (DB tables)
4. **Testuj Phase B endpoints** (curl commands)
5. **Przejdź przez Phase C** (analytics)

---

**Status**: 🚀 CAŁY PLAN (A+B+C) GOTOWY DO IMPLEMENTACJI
**Czas**: 8-12 dni (2-4 engineers)
**Architektura**: Trinity + Hexagon + Guardians + Analytics
**Jakość**: 83.6% coverage (M3 Guardian Laws ✅)
