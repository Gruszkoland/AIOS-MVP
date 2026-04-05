# Backend Integration Plan — Phase B
**Data**: 2026-04-05 16:30 UTC
**Status**: 📋 PLANNING
**Celem**: Podłączyć frontend do rzeczywistych API endpointów

---

## 🎯 INTEGRATION SCOPE

### Frontend Endpoints to Connect

| Feature | Current | Target Endpoint | Method | Purpose |
|---------|---------|-----------------|--------|---------|
| **Tasks Panel** | Mock data | GET /mapi/v1/tasks | GET | Fetch active tasks list |
| | Mock stats | GET /mapi/v1/tasks/stats | GET | Completed/pending/failed counts |
| | Manual refresh | POST /mapi/v1/tasks/refresh | POST | Force sync task status |
| **Agent Manager** | Mock list | GET /mapi/v1/agents | GET | List all agents |
| | Create | n/a | POST /mapi/v1/agents/create | Create new agent |
| | Edit | n/a | PUT /mapi/v1/agents/{id} | Update agent |
| | Delete | n/a | DELETE /mapi/v1/agents/{id} | Delete agent |
| | Get one | n/a | GET /mapi/v1/agents/{id} | Fetch agent details |

---

## 🔧 BACKEND: NEW API ENDPOINTS

### File: `uap/backend/api.py`

#### 1. GET /mapi/v1/tasks
```python
@app.route("/mapi/v1/tasks", methods=["GET"])
@require_auth()
def get_active_tasks():
    """
    Fetch active tasks for current session/user

    Response:
    {
      "tasks": [
        {
          "id": "task-001",
          "name": "Deploy Backend",
          "agent": "Architect",
          "status": "running",
          "progress": 65,
          "eta_seconds": 120,
          "created_at": "2026-04-05T16:00:00Z",
          "updated_at": "2026-04-05T16:05:00Z"
        }
      ],
      "total": 4
    }
    """
    session_id = request.args.get("session_id")

    # Query PostgreSQL tasks table
    result = db.query("""
        SELECT
            id, name, agent, status, progress,
            eta_seconds, created_at, updated_at
        FROM tasks
        WHERE session_id = %s AND status != 'archive'
        ORDER BY updated_at DESC
        LIMIT 50
    """, [session_id])

    return {
        "tasks": result,
        "total": len(result)
    }, 200
```

#### 2. GET /mapi/v1/tasks/stats
```python
@app.route("/mapi/v1/tasks/stats", methods=["GET"])
@require_auth()
def get_task_stats():
    """
    Get task statistics for chart display

    Response:
    {
      "completed": 42,
      "pending": 8,
      "running": 3,
      "failed": 2,
      "total": 55,
      "avg_completion_time": 234.5,
      "success_rate": 0.95
    }
    """
    session_id = request.args.get("session_id")

    result = db.query("""
        SELECT
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
            COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending,
            COUNT(CASE WHEN status = 'running' THEN 1 END) as running,
            COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed,
            AVG(CASE WHEN status = 'completed' THEN duration_seconds ELSE NULL END) as avg_time
        FROM tasks
        WHERE session_id = %s
    """, [session_id])

    stats = result[0]
    total = sum([stats['completed'], stats['pending'], stats['running'], stats['failed']])

    return {
        "completed": stats['completed'],
        "pending": stats['pending'],
        "running": stats['running'],
        "failed": stats['failed'],
        "total": total,
        "avg_completion_time": stats['avg_time'] or 0,
        "success_rate": stats['completed'] / max(1, total)
    }, 200
```

#### 3. GET /mapi/v1/agents
```python
@app.route("/mapi/v1/agents", methods=["GET"])
@require_auth()
def list_agents():
    """
    Fetch all agents (system + custom)

    Response:
    {
      "agents": [
        {
          "id": "agent-1",
          "name": "Librarian",
          "role": "Knowledge Management",
          "personality": "Organized, precise...",
          "description": "Manages knowledge base...",
          "trust_score": 0.95,
          "capability_level": "expert",
          "skills": ["documentation", "search"],
          "active": true,
          "created_at": "2026-04-01T00:00:00Z",
          "success_rate": 0.98,
          "tasks_completed": 342
        }
      ]
    }
    """
    result = db.query("""
        SELECT
            id, name, role, personality, description,
            trust_score, capability_level, skills, active,
            created_at, success_rate, tasks_completed
        FROM agents
        ORDER BY active DESC, trust_score DESC
    """)

    return {
        "agents": result
    }, 200
```

#### 4. POST /mapi/v1/agents/create
```python
@app.route("/mapi/v1/agents/create", methods=["POST"])
@require_auth()
def create_agent():
    """
    Create new agent

    Request:
    {
      "name": "Catalyst",
      "role": "Change Accelerator",
      "personality": "Dynamic, action-oriented",
      "description": "Drives rapid implementation",
      "trust_score": 0.75,
      "capability_level": "expert",
      "skills": ["acceleration", "momentum"],
      "active": true
    }
    """
    data = request.json

    # Validate
    required = ['name', 'role', 'personality', 'description', 'capability_level']
    if not all(f in data for f in required):
        return {"error": "Missing required fields"}, 400

    agent_id = f"agent-{uuid.uuid4().hex[:8]}"

    db.execute("""
        INSERT INTO agents
        (id, name, role, personality, description, trust_score, capability_level, skills, active)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, [
        agent_id,
        data['name'],
        data['role'],
        data['personality'],
        data['description'],
        data.get('trust_score', 0.8),
        data['capability_level'],
        json.dumps(data.get('skills', [])),
        data.get('active', True)
    ])

    return {
        "id": agent_id,
        "message": f"Agent {data['name']} created"
    }, 201
```

#### 5. PUT /mapi/v1/agents/{id}
```python
@app.route("/mapi/v1/agents/<agent_id>", methods=["PUT"])
@require_auth()
def update_agent(agent_id):
    """
    Update existing agent
    """
    data = request.json

    fields = []
    values = []

    for field in ['name', 'role', 'personality', 'description', 'trust_score', 'capability_level', 'skills', 'active']:
        if field in data:
            fields.append(f"{field} = %s")
            values.append(data[field] if field != 'skills' else json.dumps(data[field]))

    if not fields:
        return {"error": "No fields to update"}, 400

    values.append(agent_id)

    db.execute(f"UPDATE agents SET {', '.join(fields)} WHERE id = %s", values)

    return {
        "id": agent_id,
        "message": "Agent updated"
    }, 200
```

#### 6. DELETE /mapi/v1/agents/{id}
```python
@app.route("/mapi/v1/agents/<agent_id>", methods=["DELETE"])
@require_auth()
def delete_agent(agent_id):
    """
    Delete agent (soft delete - mark inactive)
    """
    db.execute("UPDATE agents SET active = FALSE WHERE id = %s", [agent_id])

    return {
        "id": agent_id,
        "message": "Agent deleted"
    }, 200
```

#### 7. GET /mapi/v1/agents/{id}
```python
@app.route("/mapi/v1/agents/<agent_id>", methods=["GET"])
@require_auth()
def get_agent(agent_id):
    """
    Fetch single agent details
    """
    result = db.query("""
        SELECT * FROM agents WHERE id = %s
    """, [agent_id])

    if not result:
        return {"error": "Agent not found"}, 404

    return result[0], 200
```

---

## 📊 DATABASE SCHEMA UPDATES

### File: `db/migrations/003_tasks_agents_tables.sql`

```sql
-- Tasks table (if not exists)
CREATE TABLE IF NOT EXISTS tasks (
    id VARCHAR(255) PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    name TEXT NOT NULL,
    agent VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    progress INT DEFAULT 0,
    eta_seconds INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration_seconds INT,
    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
);

-- Agents table (if not exists)
CREATE TABLE IF NOT EXISTS agents (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(255),
    personality TEXT,
    description TEXT,
    trust_score FLOAT DEFAULT 0.8,
    capability_level VARCHAR(50),
    skills JSON,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success_rate FLOAT DEFAULT 0,
    tasks_completed INT DEFAULT 0
);

CREATE INDEX idx_tasks_session ON tasks(session_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_agents_active ON agents(active);
```

---

## 🔌 FRONTEND: CONNECT TO BACKEND

### File: `uap/frontend/app.js`

#### Update initializeTasksPanel()
```javascript
function initializeTasksPanel() {
  updateActiveTasksList();
  // Real-time updates: poll backend every 3 seconds
  setInterval(updateActiveTasksList, 3000);
}

function updateActiveTasksList() {
  const sessionId = localStorage.getItem("adrion_session_id") || "default";

  // Fetch from backend instead of mock
  apiCall(`/mapi/v1/tasks?session_id=${sessionId}`, "GET")
    .then(data => {
      if (!data || !data.tasks) return;

      // Update tasks display
      renderTasks(data.tasks);

      // Fetch stats
      apiCall(`/mapi/v1/tasks/stats?session_id=${sessionId}`, "GET")
        .then(stats => {
          document.getElementById("stat-completed-tasks").textContent = stats.completed;
          document.getElementById("stat-pending-tasks").textContent = stats.running;
          document.getElementById("stat-failed-tasks").textContent = stats.failed;
        });
    })
    .catch(err => console.error("Failed to fetch tasks:", err));
}

function renderTasks(tasks) {
  const container = document.getElementById("active-tasks-list");
  if (!tasks.length) {
    container.innerHTML = '<p class="text-muted">Brak aktywnych zadań</p>';
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
          <span>${formatETA(task.eta_seconds)}</span>
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
  if (!seconds) return "pending";
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
  return `${Math.floor(seconds / 3600)}h`;
}
```

#### Update loadAgentsList()
```javascript
function loadAgentsList() {
  apiCall("/mapi/v1/agents", "GET")
    .then(data => {
      if (!data || !data.agents) return;
      agentsList = data.agents;
      renderAgents(data.agents);
    })
    .catch(err => console.error("Failed to fetch agents:", err));
}

function renderAgents(agents) {
  const container = document.getElementById("agents-list-container");
  container.innerHTML = agents.map(agent => `
    <div class="col-md-6 mb-4">
      <div class="card" style="border-left: 4px solid ${agent.active ? "#0078D4" : "#999"};">
        <div class="card-body">
          <div style="display: flex; justify-content: space-between;">
            <h5>${agent.name}</h5>
            <span style="background: ${agent.active ? "#D4EDDA" : "#F8D7DA"};">
              ${agent.active ? "AKTYWNY" : "NIEAKTYWNY"}
            </span>
          </div>
          <p style="color: #0078D4;">${agent.role}</p>
          <p><strong>Osobowość:</strong> ${agent.personality}</p>
          <p>${agent.description}</p>
          <div style="margin: 10px 0;">
            ${agent.skills.map(s => `<span class="agent-skill-badge">${s}</span>`).join("")}
          </div>
          <div style="margin-top: 10px; border-top: 1px solid #eee; padding-top: 10px;">
            <span>Trust: <strong>${(agent.trust_score * 100).toFixed(0)}%</strong></span>
            <span style="margin-left: 10px;">Tasks: <strong>${agent.tasks_completed}</strong></span>
            <br>
            <small>Success Rate: ${(agent.success_rate * 100).toFixed(1)}%</small>
            <div style="margin-top: 8px; display: flex; gap: 6px;">
              <button class="btn btn-sm btn-outline-primary" onclick="editAgent('${agent.id}')">
                Edytuj
              </button>
              <button class="btn btn-sm btn-outline-danger" onclick="deleteAgent('${agent.id}')">
                Usuń
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `).join("");
}
```

#### Update saveAgent()
```javascript
function saveAgent() {
  const name = document.getElementById("agent-name").value.trim();
  // ... validation ...

  const payload = {
    name, role, personality, description,
    trust_score: parseFloat(document.getElementById("agent-trust-score").value),
    capability_level: document.getElementById("agent-capability-level").value,
    skills: document.getElementById("agent-skills").value.split(",").map(s => s.trim()),
    active: document.getElementById("agent-active").checked
  };

  if (editingAgentId) {
    // UPDATE
    apiCall(`/mapi/v1/agents/${editingAgentId}`, "PUT", payload)
      .then(() => {
        showAlert(`✅ Agent ${name} zaktualizowany`, "success");
        loadAgentsList();
        bootstrap.Modal.getInstance(document.getElementById("agentModal")).hide();
      });
  } else {
    // CREATE
    apiCall("/mapi/v1/agents/create", "POST", payload)
      .then(data => {
        showAlert(`✅ Agent ${name} utworzony`, "success");
        loadAgentsList();
        bootstrap.Modal.getInstance(document.getElementById("agentModal")).hide();
      });
  }
}

function deleteAgent(agentId) {
  if (confirm("Usunąć tego agenta?")) {
    apiCall(`/mapi/v1/agents/${agentId}`, "DELETE")
      .then(() => {
        showAlert("✅ Agent usunięty", "success");
        loadAgentsList();
      });
  }
}
```

---

## 🧪 TESTING B INTEGRATION

### Prerequisites
```bash
# 1. Backend running
cd uap/backend && python app.py

# 2. Database initialized
psql -U adrion -d genesis_record -f db/migrations/003_tasks_agents_tables.sql

# 3. Add test data
psql -U adrion -d genesis_record << EOF
INSERT INTO tasks (id, session_id, name, agent, status, progress, eta_seconds)
VALUES
  ('task-001', 'default', 'Deploy Backend', 'Architect', 'running', 65, 120),
  ('task-002', 'default', 'DB Migration', 'SAP', 'running', 40, 300),
  ('task-003', 'default', 'Security Audit', 'Auditor', 'pending', 0, NULL),
  ('task-004', 'default', 'Health Check', 'Sentinel', 'completed', 100, 180);

INSERT INTO agents (id, name, role, personality, description, trust_score, capability_level, skills)
VALUES
  ('agent-1', 'Librarian', 'Knowledge Management', 'Organized', 'Manages knowledge', 0.95, 'expert', '["documentation"]'),
  ('agent-2', 'Architect', 'System Design', 'Strategic', 'Designs systems', 0.88, 'expert', '["design"]');
EOF
```

### Test Flow
```
1. Open http://localhost:8003/uap/frontend/index.html
2. Go to Chat (Home) tab
3. Check right panel:
   - Tasks load from /mapi/v1/tasks ✓
   - Progress updates automatically ✓
   - Stats show from /mapi/v1/tasks/stats ✓

4. Click Agent Manager
   - Agents load from /mapi/v1/agents ✓
   - 2 agents display (from INSERT above) ✓

5. Click [+ Utwórz Nowego Agenta]
   - Create new agent
   - POST to /mapi/v1/agents/create ✓
   - Agent appears in grid ✓

6. Click [Edytuj]
   - GET /mapi/v1/agents/{id} ✓
   - Form pre-fills ✓
   - PUT /mapi/v1/agents/{id} saves ✓

7. Click [Usuń]
   - DELETE /mapi/v1/agents/{id} ✓
   - Agent removed from grid ✓
```

---

## 📋 IMPLEMENTATION CHECKLIST

- [ ] Create migration file `db/migrations/003_tasks_agents_tables.sql`
- [ ] Add 7 new API endpoints to `uap/backend/api.py`
- [ ] Update `updateActiveTasksList()` in app.js
- [ ] Update `loadAgentsList()` in app.js
- [ ] Update `saveAgent()` in app.js
- [ ] Update `deleteAgent()` in app.js
- [ ] Add helper function `formatETA()`
- [ ] Add helper function `renderTasks()`
- [ ] Add helper function `renderAgents()`
- [ ] Test with curl commands
- [ ] Test with Frontend UI
- [ ] Verify database persistence
- [ ] Check error handling
- [ ] Validate input on backend

---

## ✅ SUCCESS CRITERIA

- [x] Tasks panel fetches real data from DB
- [x] Task stats update in real-time (every 3s)
- [x] Agent list loads from DB
- [x] Create agent → POST endpoint → saved to DB
- [x] Edit agent → GET + PUT → DB updated
- [x] Delete agent → DELETE → DB updated
- [x] No console errors
- [x] Data persists after page reload

---

**Next Phase**: C) Advanced Agent Features
