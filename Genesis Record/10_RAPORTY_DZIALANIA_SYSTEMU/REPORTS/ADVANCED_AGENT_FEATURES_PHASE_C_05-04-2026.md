# Advanced Agent Features Plan — Phase C
**Data**: 2026-04-05 16:45 UTC
**Status**: 📋 PLANNING
**Celem**: Dodać zaawansowane funkcje do zarządzania agentami

---

## 🎯 PHASE C FEATURES

### 1. Agent History / Activity Log
Track everything agent does:
- Tasks executed (id, name, status, duration)
- Decisions made (with Trinity scores)
- Errors encountered
- Performance trending

### 2. Agent Performance Metrics
Per-agent analytics:
- Success rate (tasks completed / total attempted)
- Average response time
- Error rate
- Trust score trend (over time)
- Competency leaderboard (ranked by success rate)

### 3. Feedback & Rating System
User can rate agent decisions:
- Star rating (1-5)
- Feedback comment
- Help improve Trust Score

### 4. Agent Assignment History
Show which tasks assigned to which agent:
- Assignment reasons (why this agent?)
- Task outcome
- Agent feedback

---

## 📊 NEW DATABASE SCHEMA

### File: `db/migrations/004_agent_features.sql`

```sql
-- Agent activity log
CREATE TABLE IF NOT EXISTS agent_activity (
    id VARCHAR(255) PRIMARY KEY,
    agent_id VARCHAR(255) NOT NULL,
    activity_type VARCHAR(50),  -- 'task_execute', 'decision', 'error'
    task_id VARCHAR(255),
    description TEXT,
    metadata JSON,  -- Trinity scores, decisions, errors
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(agent_id) REFERENCES agents(id)
);

-- Agent performance snapshots (daily/hourly)
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
    trust_score FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(agent_id) REFERENCES agents(id)
);

-- User feedback on agent decisions
CREATE TABLE IF NOT EXISTS agent_feedback (
    id VARCHAR(255) PRIMARY KEY,
    agent_id VARCHAR(255) NOT NULL,
    task_id VARCHAR(255),
    rating INT,  -- 1-5 stars
    feedback_text TEXT,
    impact_on_trust FLOAT,  -- how much to adjust trust_score
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(agent_id) REFERENCES agents(id)
);

-- Agent assignment recommendations
CREATE TABLE IF NOT EXISTS agent_assignments (
    id VARCHAR(255) PRIMARY KEY,
    task_id VARCHAR(255) NOT NULL,
    agent_id VARCHAR(255) NOT NULL,
    reasoning TEXT,  -- why this agent? (skill match, load balance, etc.)
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    outcome VARCHAR(50),  -- 'success', 'partial', 'failed'
    FOREIGN KEY(agent_id) REFERENCES agents(id)
);

CREATE INDEX idx_agent_activity ON agent_activity(agent_id, created_at DESC);
CREATE INDEX idx_agent_performance ON agent_performance(agent_id, period_date DESC);
CREATE INDEX idx_agent_feedback ON agent_feedback(agent_id, created_at DESC);
CREATE INDEX idx_agent_assignments ON agent_assignments(agent_id, completed_at);
```

---

## 🔌 BACKEND API ENDPOINTS (Phase C)

### File: `uap/backend/api.py`

#### 1. GET /mapi/v1/agents/{id}/history
```python
@app.route("/mapi/v1/agents/<agent_id>/history", methods=["GET"])
@require_auth()
def get_agent_history(agent_id):
    """
    Fetch agent activity history (last 50 events)

    Response:
    {
      "history": [
        {
          "id": "activity-001",
          "agent_id": "agent-1",
          "activity_type": "task_execute",
          "task_id": "task-123",
          "description": "Successfully completed deployment",
          "metadata": {
            "trinity_scores": {"material": 0.8, "intellectual": 0.9},
            "duration_seconds": 234,
            "status": "completed"
          },
          "created_at": "2026-04-05T15:00:00Z"
        }
      ]
    }
    """
    result = db.query("""
        SELECT * FROM agent_activity
        WHERE agent_id = %s
        ORDER BY created_at DESC
        LIMIT 50
    """, [agent_id])

    return {"history": result}, 200
```

#### 2. GET /mapi/v1/agents/{id}/performance
```python
@app.route("/mapi/v1/agents/<agent_id>/performance", methods=["GET"])
@require_auth()
def get_agent_performance(agent_id):
    """
    Fetch agent performance metrics (last 30 days)

    Response:
    {
      "today": {
        "tasks_total": 12,
        "tasks_completed": 11,
        "tasks_failed": 1,
        "success_rate": 0.917,
        "error_rate": 0.083,
        "avg_response_time_ms": 1234.5,
        "trust_score": 0.92
      },
      "trend": [  // Last 7 days
        {"date": "2026-04-05", "success_rate": 0.917},
        {"date": "2026-04-04", "success_rate": 0.905},
        ...
      ]
    }
    """
    today = db.query("""
        SELECT * FROM agent_performance
        WHERE agent_id = %s AND period_date = CURRENT_DATE
    """, [agent_id])

    trend = db.query("""
        SELECT period_date, success_rate, error_rate
        FROM agent_performance
        WHERE agent_id = %s AND period_date >= CURRENT_DATE - INTERVAL 30 DAY
        ORDER BY period_date DESC
    """, [agent_id])

    return {
        "today": today[0] if today else {},
        "trend": trend,
        "leaderboard_rank": getAgentLeaderboardRank(agent_id)
    }, 200
```

#### 3. POST /mapi/v1/agents/{id}/feedback
```python
@app.route("/mapi/v1/agents/<agent_id>/feedback", methods=["POST"])
@require_auth()
def submit_agent_feedback(agent_id):
    """
    Submit feedback on agent decision

    Request:
    {
      "task_id": "task-123",
      "rating": 4,  // 1-5 stars
      "feedback_text": "Good decision, could be faster"
    }

    Logic:
    - Feedback allows user to rate agent
    - Rating affects Trust Score adjustment
    - Positive feedback → Trust Score ↑
    - Negative feedback → Trust Score ↓
    """
    data = request.json
    rating = data.get("rating", 3)

    # Calculate impact on trust score
    # 5 stars = +0.05, 4 stars = +0.02, 3 stars = 0, 2 stars = -0.02, 1 star = -0.05
    impact_map = {5: 0.05, 4: 0.02, 3: 0, 2: -0.02, 1: -0.05}
    impact = impact_map.get(rating, 0)

    feedback_id = f"feedback-{uuid.uuid4().hex[:8]}"

    db.execute("""
        INSERT INTO agent_feedback
        (id, agent_id, task_id, rating, feedback_text, impact_on_trust)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, [feedback_id, agent_id, data.get("task_id"), rating, data.get("feedback_text"), impact])

    # Update agent trust_score
    db.execute("""
        UPDATE agents
        SET trust_score = LEAST(1.0, GREATEST(0.0, trust_score + %s))
        WHERE id = %s
    """, [impact, agent_id])

    return {
        "id": feedback_id,
        "message": f"Feedback recorded. Trust Score adjusted by {impact:+.2f}"
    }, 201
```

#### 4. GET /mapi/v1/agents/leaderboard
```python
@app.route("/mapi/v1/agents/leaderboard", methods=["GET"])
@require_auth()
def get_agent_leaderboard():
    """
    Ranking of agents by performance

    Response:
    {
      "leaderboard": [
        {
          "rank": 1,
          "agent_id": "agent-1",
          "name": "Librarian",
          "success_rate": 0.98,
          "tasks_completed": 342,
          "trust_score": 0.95,
          "avg_response_time_ms": 850.2
        }
      ]
    }
    """
    result = db.query("""
        SELECT
            ROW_NUMBER() OVER (ORDER BY success_rate DESC) as rank,
            id, name, success_rate, tasks_completed, trust_score,
            (SELECT AVG(avg_response_time_ms) FROM agent_performance WHERE agent_id = agents.id) as avg_response_time_ms
        FROM agents
        WHERE active = TRUE
        ORDER BY success_rate DESC
    """)

    return {
        "leaderboard": result
    }, 200
```

#### 5. POST /mapi/v1/agents/{id}/log-activity
```python
@app.route("/mapi/v1/agents/<agent_id>/log-activity", methods=["POST"])
@require_auth()
def log_agent_activity(agent_id):
    """
    Log agent activity (called by orchestrator after task)

    Request:
    {
      "activity_type": "task_execute",
      "task_id": "task-123",
      "description": "Successfully executed task",
      "metadata": {
        "trinity_scores": {"material": 0.8, "intellectual": 0.9, "essential": 0.85},
        "duration_seconds": 234,
        "status": "completed"
      }
    }
    """
    data = request.json

    activity_id = f"activity-{uuid.uuid4().hex[:8]}"

    db.execute("""
        INSERT INTO agent_activity
        (id, agent_id, activity_type, task_id, description, metadata)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, [activity_id, agent_id, data.get("activity_type"), data.get("task_id"),
          data.get("description"), json.dumps(data.get("metadata", {}))])

    return {"id": activity_id}, 201
```

---

## 🎨 FRONTEND: AGENT DETAIL VIEW

### New Modal: Agent Performance Dashboard

```html
<!-- Modal: Agent Details with History + Performance -->
<div class="modal fade" id="agentDetailModal" tabindex="-1">
  <div class="modal-dialog modal-lg">
    <div class="modal-content">
      <div class="modal-header">
        <h5 id="agentDetailTitle">Agent Details</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body">
        <!-- Nav tabs: Overview | History | Performance | Feedback -->
        <ul class="nav nav-tabs" role="tablist">
          <li class="nav-item">
            <button class="nav-link active" id="detail-overview-tab" data-bs-toggle="tab" data-bs-target="#detail-overview">
              Overview
            </button>
          </li>
          <li class="nav-item">
            <button class="nav-link" id="detail-history-tab" data-bs-toggle="tab" data-bs-target="#detail-history">
              History
            </button>
          </li>
          <li class="nav-item">
            <button class="nav-link" id="detail-performance-tab" data-bs-toggle="tab" data-bs-target="#detail-performance">
              Performance
            </button>
          </li>
          <li class="nav-item">
            <button class="nav-link" id="detail-feedback-tab" data-bs-toggle="tab" data-bs-target="#detail-feedback">
              Feedback
            </button>
          </li>
        </ul>

        <div class="tab-content" style="margin-top: 15px;">
          <!-- Overview -->
          <div class="tab-pane fade show active" id="detail-overview">
            <div id="agentOverviewContent"></div>
          </div>

          <!-- History -->
          <div class="tab-pane fade" id="detail-history">
            <div id="agentHistoryContent" style="max-height: 400px; overflow-y: auto;"></div>
          </div>

          <!-- Performance -->
          <div class="tab-pane fade" id="detail-performance">
            <div id="agentPerformanceContent"></div>
            <canvas id="performanceChart" style="margin-top: 20px;"></canvas>
          </div>

          <!-- Feedback -->
          <div class="tab-pane fade" id="detail-feedback">
            <div id="agentFeedbackContent"></div>
            <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee;">
              <h6>Submit Feedback</h6>
              <div class="mb-2">
                <label>Rating (1-5 stars)</label>
                <div id="feedback-stars" style="font-size: 2rem; cursor: pointer;">
                  <span onclick="setRating(1)">⭐</span>
                  <span onclick="setRating(2)">⭐</span>
                  <span onclick="setRating(3)">⭐</span>
                  <span onclick="setRating(4)">⭐</span>
                  <span onclick="setRating(5)">⭐</span>
                </div>
              </div>
              <textarea class="form-control mb-2" id="feedback-text" placeholder="Your feedback..."></textarea>
              <button class="btn btn-primary" onclick="submitFeedback()">Submit Feedback</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
```

### JavaScript Functions

```javascript
function openAgentDetail(agentId) {
  // Load agent overview + history + performance
  apiCall(`/mapi/v1/agents/${agentId}`, "GET")
    .then(agent => {
      document.getElementById("agentDetailTitle").textContent = `${agent.name} - Details`;
      renderAgentOverview(agent);
      loadAgentHistory(agentId);
      loadAgentPerformance(agentId);
      loadAgentFeedback(agentId);

      const modal = new bootstrap.Modal(document.getElementById("agentDetailModal"));
      modal.show();
    });
}

function loadAgentHistory(agentId) {
  apiCall(`/mapi/v1/agents/${agentId}/history`, "GET")
    .then(data => {
      const html = data.history.map(event => `
        <div style="padding: 10px; border-bottom: 1px solid #eee;">
          <strong>${event.activity_type}</strong> - ${new Date(event.created_at).toLocaleString()}
          <br>
          <small>${event.description}</small>
        </div>
      `).join("");
      document.getElementById("agentHistoryContent").innerHTML = html;
    });
}

function loadAgentPerformance(agentId) {
  apiCall(`/mapi/v1/agents/${agentId}/performance`, "GET")
    .then(data => {
      const today = data.today;
      const html = `
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
          <div style="padding: 10px; background: #f0f0f0; border-radius: 6px;">
            <div style="font-size: 0.9rem; color: #666;">Success Rate</div>
            <div style="font-size: 1.8rem; font-weight: 700; color: #0078D4;">
              ${(today.success_rate * 100).toFixed(1)}%
            </div>
          </div>
          <div style="padding: 10px; background: #f0f0f0; border-radius: 6px;">
            <div style="font-size: 0.9rem; color: #666;">Avg Response Time</div>
            <div style="font-size: 1.8rem; font-weight: 700;">
              ${today.avg_response_time_ms.toFixed(0)}ms
            </div>
          </div>
          <div style="padding: 10px; background: #f0f0f0; border-radius: 6px;">
            <div style="font-size: 0.9rem; color: #666;">Tasks Today</div>
            <div style="font-size: 1.8rem; font-weight: 700;">
              ${today.tasks_completed} / ${today.tasks_total}
            </div>
          </div>
          <div style="padding: 10px; background: #f0f0f0; border-radius: 6px;">
            <div style="font-size: 0.9rem; color: #666;">Leaderboard Rank</div>
            <div style="font-size: 1.8rem; font-weight: 700;">
              #${data.leaderboard_rank}
            </div>
          </div>
        </div>

        <div style="margin-top: 20px;">
          <h6>7-Day Trend</h6>
          <div style="display: flex; gap: 4px; height: 100px;">
            ${data.trend.map(day => `
              <div style="flex: 1; background: linear-gradient(to top, rgba(0,120,212,0.3), rgba(0,120,212,0.3)); position: relative; title='${day.date}'>
                <div style="position: absolute; bottom: 0; width: 100%; height: ${day.success_rate * 100}%; background: #0078D4; border-radius: 3px;"></div>
              </div>
            `).join("")}
          </div>
        </div>
      `;
      document.getElementById("agentPerformanceContent").innerHTML = html;
    });
}

function loadAgentFeedback(agentId) {
  apiCall(`/mapi/v1/agents/${agentId}/feedback`, "GET")
    .then(data => {
      const html = (data.feedback || []).map(fb => `
        <div style="padding: 10px; margin-bottom: 10px; background: #f9f9f9; border-radius: 6px;">
          <div style="display: flex; justify-content: space-between;">
            <span>${'⭐'.repeat(fb.rating)}</span>
            <small>${new Date(fb.created_at).toLocaleDateString()}</small>
          </div>
          <p style="margin: 5px 0; font-size: 0.9rem;">${fb.feedback_text}</p>
        </div>
      `).join("");
      document.getElementById("agentFeedbackContent").innerHTML = html || "<p>No feedback yet</p>";
    });
}

function setRating(stars) {
  currentRating = stars;
  const container = document.getElementById("feedback-stars");
  container.innerHTML = Array(5).fill(0).map((_, i) =>
    `<span onclick="setRating(${i+1})" style="opacity: ${i < stars ? 1 : 0.3}; cursor: pointer;">⭐</span>`
  ).join("");
}

function submitFeedback() {
  const taskId = currentViewingTaskId; // Set when opening modal
  const feedback = document.getElementById("feedback-text").value;

  apiCall(`/mapi/v1/agents/${currentAgentId}/feedback`, "POST", {
    task_id: taskId,
    rating: currentRating,
    feedback_text: feedback
  }).then(() => {
    showAlert("✅ Feedback submitted", "success");
    document.getElementById("feedback-text").value = "";
    loadAgentFeedback(currentAgentId);
  });
}
```

---

## 📊 LEADERBOARD UI

Add to Agent Manager page:

```html
<div class="card mt-4">
  <div class="card-header">
    <h5><i class="fas fa-trophy me-2"></i>Agent Leaderboard</h5>
  </div>
  <div class="card-body">
    <table class="table table-sm table-hover">
      <thead>
        <tr>
          <th>Rank</th>
          <th>Agent</th>
          <th>Success Rate</th>
          <th>Tasks</th>
          <th>Avg Time</th>
          <th>Trust Score</th>
        </tr>
      </thead>
      <tbody id="leaderboard-tbody">
        <!-- Populate via JS -->
      </tbody>
    </table>
  </div>
</div>
```

```javascript
function loadLeaderboard() {
  apiCall("/mapi/v1/agents/leaderboard", "GET")
    .then(data => {
      const html = data.leaderboard.map((agent, idx) => `
        <tr>
          <td><strong>🥇 ${agent.rank}</strong></td>
          <td><a href="#" onclick="openAgentDetail('${agent.agent_id}')">${agent.name}</a></td>
          <td>${(agent.success_rate * 100).toFixed(1)}%</td>
          <td>${agent.tasks_completed}</td>
          <td>${agent.avg_response_time_ms.toFixed(0)}ms</td>
          <td>${(agent.trust_score * 100).toFixed(0)}%</td>
        </tr>
      `).join("");
      document.getElementById("leaderboard-tbody").innerHTML = html;
    });
}
```

---

## ✅ SUCCESS CRITERIA (Phase C)

- [ ] Agent detail modal displays history
- [ ] Agent performance metrics load correctly
- [ ] Success rate trend chart renders
- [ ] User can submit feedback (1-5 stars)
- [ ] Trust score adjusts based on feedback
- [ ] Leaderboard displays ranked agents
- [ ] Activity log shows all agent actions
- [ ] No database errors
- [ ] Performance queries optimized (indexes work)

---

**Next Phase**: D) UX Refinements (Filters, Bulk Ops, Sorting)
