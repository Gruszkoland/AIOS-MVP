# UX Refinements Plan — Phase D
**Data**: 2026-04-05 17:00 UTC
**Status**: 📋 PLANNING
**Celem**: Ulepszić doświadczenie użytkownika z zaawansowanymi filtami, sortowaniem i operacjami

---

## 🎯 PHASE D ENHANCEMENTS

### 1. Task Filtering & Search
- Filter by status (all / pending / running / completed / failed)
- Filter by agent
- Search by task name
- Date range
- Show/hide completed tasks

### 2. Task Sorting
- By name (A-Z)
- By progress (%)
- By status
- By agent
- By created date
- By updated date

### 3. Agent Filtering
- By capability level (basic/intermediate/expert)
- By activity status (active/inactive)
- By trust score range
- Search by name/role

### 4. Agent Sorting
- By name (A-Z)
- By trust score
- By success rate
- By tasks completed
- By last activity

### 5. Bulk Operations — Tasks
- Select multiple tasks (checkboxes)
- Bulk actions:
  - Mark as completed
  - Cancel/stop
  - Reassign to different agent
  - Delete batch
- Progress indicator (X of Y tasks modified)

### 6. Bulk Operations — Agents
- Select multiple agents (checkboxes)
- Bulk actions:
  - Enable/disable
  - Reset trust scores
  - Export agent profiles
- Confirmation dialogs

### 7. Export/Download
- Export tasks as CSV/JSON
- Export agent profiles
- Export leaderboard
- Export performance report

### 8. Dark Mode
- Toggle for dark/light theme
- Persistent (localStorage)
- Smooth transitions

---

## 📊 UI COMPONENTS

### Task Panel Enhancements

```html
<!-- Filter Bar -->
<div style="margin-bottom: 15px; display: flex; gap: 10px; flex-wrap: wrap;">
  <select id="task-filter-status" class="form-select" style="flex: 0 1 auto; min-width: 150px;">
    <option value="">All Status</option>
    <option value="pending">Pending</option>
    <option value="running">Running</option>
    <option value="completed">Completed</option>
    <option value="failed">Failed</option>
  </select>

  <select id="task-filter-agent" class="form-select" style="flex: 0 1 auto; min-width: 150px;">
    <option value="">All Agents</option>
    <option value="Architect">Architect</option>
    <option value="SAP">SAP</option>
    <!-- Populate dynamically -->
  </select>

  <input type="text" id="task-search" class="form-control" placeholder="Search tasks..." style="flex: 1 1 200px;">

  <select id="task-sort" class="form-select" style="flex: 0 1 auto; min-width: 150px;">
    <option value="updated">Recently Updated</option>
    <option value="name">Name (A-Z)</option>
    <option value="progress">Progress (%)</option>
    <option value="status">Status</option>
    <option value="agent">Agent</option>
  </select>

  <button class="btn btn-sm btn-outline-secondary" onclick="resetTaskFilters()">
    <i class="fas fa-redo me-1"></i>Reset
  </button>

  <button class="btn btn-sm btn-outline-primary" onclick="exportTasks()">
    <i class="fas fa-download me-1"></i>Export
  </button>
</div>

<!-- Bulk Actions (appears when items selected) -->
<div id="task-bulk-actions" style="display: none; margin-bottom: 15px; padding: 10px; background: #e7f3ff; border-radius: 6px;">
  <span id="bulk-selection-count" style="margin-right: 15px;">0 selected</span>
  <button class="btn btn-sm btn-success" onclick="bulkCompleteTask()">Complete</button>
  <button class="btn btn-sm btn-warning" onclick="bulkCancelTask()">Cancel</button>
  <button class="btn btn-sm btn-danger" onclick="bulkDeleteTask()">Delete</button>
  <button class="btn btn-sm btn-secondary ms-auto" onclick="bulkClearSelection()">Clear</button>
</div>
```

### Agent Panel Enhancements

```html
<!-- Filter Bar -->
<div style="margin-bottom: 15px; display: flex; gap: 10px; flex-wrap: wrap;">
  <input type="text" id="agent-search" class="form-control" placeholder="Search agents..." style="flex: 1 1 200px;">

  <select id="agent-filter-capability" class="form-select" style="flex: 0 1 auto; min-width: 150px;">
    <option value="">All Levels</option>
    <option value="basic">Basic</option>
    <option value="intermediate">Intermediate</option>
    <option value="expert">Expert</option>
  </select>

  <select id="agent-filter-status" class="form-select" style="flex: 0 1 auto; min-width: 150px;">
    <option value="">All Status</option>
    <option value="active">Active</option>
    <option value="inactive">Inactive</option>
  </select>

  <select id="agent-sort" class="form-select" style="flex: 0 1 auto; min-width: 150px;">
    <option value="name">Name (A-Z)</option>
    <option value="trust">Trust Score</option>
    <option value="success">Success Rate</option>
    <option value="tasks">Tasks Completed</option>
  </select>

  <button class="btn btn-sm btn-outline-secondary" onclick="resetAgentFilters()">
    <i class="fas fa-redo me-1"></i>Reset
  </button>

  <button class="btn btn-sm btn-outline-primary" onclick="exportAgents()">
    <i class="fas fa-download me-1"></i>Export
  </button>
</div>

<!-- Bulk Actions for Agents -->
<div id="agent-bulk-actions" style="display: none; margin-bottom: 15px; padding: 10px; background: #e7f3ff; border-radius: 6px;">
  <span id="bulk-agent-count" style="margin-right: 15px;">0 selected</span>
  <button class="btn btn-sm btn-success" onclick="bulkEnableAgent()">Enable</button>
  <button class="btn btn-sm btn-danger" onclick="bulkDisableAgent()">Disable</button>
  <button class="btn btn-sm btn-warning" onclick="bulkResetTrust()">Reset Trust</button>
  <button class="btn btn-sm btn-secondary ms-auto" onclick="bulkClearSelection()">Clear</button>
</div>

<!-- Agent Grid with Checkboxes -->
<div id="agents-list-container" class="row">
  <!-- Each card includes: <input type="checkbox" class="agent-checkbox"> -->
</div>
```

### Dark Mode Toggle

```html
<!-- Add to navbar -->
<button id="dark-mode-toggle" class="btn btn-sm btn-outline-secondary" style="margin-left: 15px;">
  <i class="fas fa-moon"></i> Dark Mode
</button>
```

---

## 🔧 JAVASCRIPT IMPLEMENTATION

### File: `uap/frontend/app.js` (Phase D additions)

```javascript
// ──────────────────────────────────────────────────────────────────────────
// TASK FILTERING & SORTING
// ──────────────────────────────────────────────────────────────────────────

let allTasks = [];
let filteredTasks = [];
let selectedTasks = [];

function initializeTaskFilters() {
  document.getElementById("task-filter-status").addEventListener("change", applyTaskFilters);
  document.getElementById("task-filter-agent").addEventListener("change", applyTaskFilters);
  document.getElementById("task-search").addEventListener("keyup", applyTaskFilters);
  document.getElementById("task-sort").addEventListener("change", applyTaskFilters);
}

function applyTaskFilters() {
  const statusFilter = document.getElementById("task-filter-status").value;
  const agentFilter = document.getElementById("task-filter-agent").value;
  const searchTerm = document.getElementById("task-search").value.toLowerCase();
  const sortBy = document.getElementById("task-sort").value;

  // Filter
  filteredTasks = allTasks.filter(task => {
    const statusMatch = !statusFilter || task.status === statusFilter;
    const agentMatch = !agentFilter || task.agent === agentFilter;
    const searchMatch = !searchTerm || task.name.toLowerCase().includes(searchTerm);
    return statusMatch && agentMatch && searchMatch;
  });

  // Sort
  filteredTasks.sort((a, b) => {
    switch (sortBy) {
      case "name":
        return a.name.localeCompare(b.name);
      case "progress":
        return b.progress - a.progress;
      case "status":
        return a.status.localeCompare(b.status);
      case "agent":
        return a.agent.localeCompare(b.agent);
      case "updated":
      default:
        return new Date(b.updated_at) - new Date(a.updated_at);
    }
  });

  renderTasks(filteredTasks);
}

function resetTaskFilters() {
  document.getElementById("task-filter-status").value = "";
  document.getElementById("task-filter-agent").value = "";
  document.getElementById("task-search").value = "";
  document.getElementById("task-sort").value = "updated";
  applyTaskFilters();
}

function exportTasks() {
  const csv = [
    ["ID", "Name", "Agent", "Status", "Progress", "ETA"].join(","),
    ...filteredTasks.map(t => [
      t.id,
      t.name,
      t.agent,
      t.status,
      t.progress,
      t.eta_seconds
    ].join(","))
  ].join("\n");

  const blob = new Blob([csv], { type: "text/csv" });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `tasks-${new Date().toISOString().split("T")[0]}.csv`;
  a.click();
}

// ──────────────────────────────────────────────────────────────────────────
// TASK BULK OPERATIONS
// ──────────────────────────────────────────────────────────────────────────

function renderTasksWithCheckboxes(tasks) {
  const container = document.getElementById("active-tasks-list");
  container.innerHTML = tasks.map(task => `
    <div class="task-item" style="display: flex; gap: 10px; align-items: flex-start;">
      <input type="checkbox" class="task-checkbox" data-task-id="${task.id}" onchange="updateBulkSelection()">
      <div style="flex: 1;">
        <div class="task-item-header">
          <span class="task-item-title">${task.name}</span>
          <span class="task-item-status ${task.status}">${task.status.toUpperCase()}</span>
        </div>
        <div class="task-progress-container">
          <div class="task-progress-bar">
            <div class="task-progress-fill" style="width: ${task.progress}%"></div>
          </div>
        </div>
      </div>
    </div>
  `).join("");
}

function updateBulkSelection() {
  selectedTasks = Array.from(document.querySelectorAll(".task-checkbox:checked"))
    .map(cb => cb.dataset.taskId);

  const bulkActionsDiv = document.getElementById("task-bulk-actions");
  if (selectedTasks.length > 0) {
    bulkActionsDiv.style.display = "flex";
    document.getElementById("bulk-selection-count").textContent = `${selectedTasks.length} selected`;
  } else {
    bulkActionsDiv.style.display = "none";
  }
}

function bulkCompleteTask() {
  if (confirm(`Mark ${selectedTasks.length} tasks as completed?`)) {
    selectedTasks.forEach(taskId => {
      apiCall(`/mapi/v1/tasks/${taskId}`, "PUT", { status: "completed" })
        .then(() => console.log(`Task ${taskId} completed`));
    });
    setTimeout(applyTaskFilters, 1000);
    bulkClearSelection();
  }
}

function bulkCancelTask() {
  if (confirm(`Cancel ${selectedTasks.length} tasks?`)) {
    selectedTasks.forEach(taskId => {
      apiCall(`/mapi/v1/tasks/${taskId}`, "PUT", { status: "cancelled" })
        .then(() => console.log(`Task ${taskId} cancelled`));
    });
    setTimeout(applyTaskFilters, 1000);
    bulkClearSelection();
  }
}

function bulkDeleteTask() {
  if (confirm(`Delete ${selectedTasks.length} tasks? This cannot be undone.`)) {
    selectedTasks.forEach(taskId => {
      apiCall(`/mapi/v1/tasks/${taskId}`, "DELETE")
        .then(() => console.log(`Task ${taskId} deleted`));
    });
    setTimeout(applyTaskFilters, 1000);
    bulkClearSelection();
  }
}

function bulkClearSelection() {
  document.querySelectorAll(".task-checkbox").forEach(cb => cb.checked = false);
  updateBulkSelection();
}

// ──────────────────────────────────────────────────────────────────────────
// AGENT FILTERING & SORTING
// ──────────────────────────────────────────────────────────────────────────

let selectedAgents = [];

function initializeAgentFilters() {
  document.getElementById("agent-search").addEventListener("keyup", applyAgentFilters);
  document.getElementById("agent-filter-capability").addEventListener("change", applyAgentFilters);
  document.getElementById("agent-filter-status").addEventListener("change", applyAgentFilters);
  document.getElementById("agent-sort").addEventListener("change", applyAgentFilters);
}

function applyAgentFilters() {
  const searchTerm = document.getElementById("agent-search").value.toLowerCase();
  const capabilityFilter = document.getElementById("agent-filter-capability").value;
  const statusFilter = document.getElementById("agent-filter-status").value;
  const sortBy = document.getElementById("agent-sort").value;

  let filtered = agentsList.filter(agent => {
    const searchMatch = !searchTerm || agent.name.toLowerCase().includes(searchTerm) ||
                       agent.role.toLowerCase().includes(searchTerm);
    const capabilityMatch = !capabilityFilter || agent.capability === capabilityFilter;
    const statusMatch = !statusFilter || (statusFilter === "active" ? agent.active : !agent.active);
    return searchMatch && capabilityMatch && statusMatch;
  });

  // Sort
  filtered.sort((a, b) => {
    switch (sortBy) {
      case "trust":
        return b.trust_score - a.trust_score;
      case "success":
        return b.success_rate - a.success_rate;
      case "tasks":
        return b.tasks_completed - a.tasks_completed;
      case "name":
      default:
        return a.name.localeCompare(b.name);
    }
  });

  renderAgentsWithCheckboxes(filtered);
}

function resetAgentFilters() {
  document.getElementById("agent-search").value = "";
  document.getElementById("agent-filter-capability").value = "";
  document.getElementById("agent-filter-status").value = "";
  document.getElementById("agent-sort").value = "name";
  applyAgentFilters();
}

function exportAgents() {
  const json = JSON.stringify(agentsList, null, 2);
  const blob = new Blob([json], { type: "application/json" });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `agents-${new Date().toISOString().split("T")[0]}.json`;
  a.click();
}

function renderAgentsWithCheckboxes(agents) {
  const container = document.getElementById("agents-list-container");
  container.innerHTML = agents.map(agent => `
    <div class="col-md-6 mb-4" style="position: relative;">
      <input type="checkbox" class="agent-checkbox" data-agent-id="${agent.id}"
             onchange="updateAgentSelection()"
             style="position: absolute; top: 10px; right: 10px; width: 20px; height: 20px; cursor: pointer;">
      <div class="card" style="border-left: 4px solid ${agent.active ? "#0078D4" : "#999"};">
        <div class="card-body">
          <!-- Rest of card content -->
        </div>
      </div>
    </div>
  `).join("");
}

function updateAgentSelection() {
  selectedAgents = Array.from(document.querySelectorAll(".agent-checkbox:checked"))
    .map(cb => cb.dataset.agentId);

  const bulkActionsDiv = document.getElementById("agent-bulk-actions");
  if (selectedAgents.length > 0) {
    bulkActionsDiv.style.display = "flex";
    document.getElementById("bulk-agent-count").textContent = `${selectedAgents.length} selected`;
  } else {
    bulkActionsDiv.style.display = "none";
  }
}

function bulkEnableAgent() {
  selectedAgents.forEach(agentId => {
    apiCall(`/mapi/v1/agents/${agentId}`, "PUT", { active: true });
  });
  showAlert(`✅ ${selectedAgents.length} agents enabled`, "success");
  setTimeout(applyAgentFilters, 500);
}

function bulkDisableAgent() {
  selectedAgents.forEach(agentId => {
    apiCall(`/mapi/v1/agents/${agentId}`, "PUT", { active: false });
  });
  showAlert(`✅ ${selectedAgents.length} agents disabled`, "success");
  setTimeout(applyAgentFilters, 500);
}

function bulkResetTrust() {
  if (confirm("Reset trust scores to 0.8?")) {
    selectedAgents.forEach(agentId => {
      apiCall(`/mapi/v1/agents/${agentId}`, "PUT", { trust_score: 0.8 });
    });
    showAlert(`✅ Trust scores reset`, "success");
    loadAgentsList();
  }
}

// ──────────────────────────────────────────────────────────────────────────
// DARK MODE
// ──────────────────────────────────────────────────────────────────────────

function initializeDarkMode() {
  const darkModeToggle = document.getElementById("dark-mode-toggle");
  const isDarkMode = localStorage.getItem("dark-mode") === "true";

  if (isDarkMode) applyDarkMode();

  darkModeToggle.addEventListener("click", () => {
    const isNowDark = !document.body.classList.contains("dark-mode");
    localStorage.setItem("dark-mode", isNowDark);
    if (isNowDark) applyDarkMode();
    else removeDarkMode();
  });
}

function applyDarkMode() {
  document.body.classList.add("dark-mode");
  document.body.style.background = "#1a1a1a";
  document.body.style.color = "#e0e0e0";
  document.querySelectorAll(".card").forEach(card => {
    card.style.background = "#2a2a2a";
    card.style.borderColor = "#444";
  });
  document.querySelectorAll(".form-control, .form-select").forEach(input => {
    input.style.background = "#333";
    input.style.color = "#e0e0e0";
    input.style.borderColor = "#444";
  });
  document.getElementById("dark-mode-toggle").innerHTML = '<i class="fas fa-sun"></i> Light Mode';
}

function removeDarkMode() {
  document.body.classList.remove("dark-mode");
  document.body.style.background = "#F5F5F5";
  document.body.style.color = "#1E3A5F";
  document.querySelectorAll(".card").forEach(card => {
    card.style.background = "#FFFFFF";
    card.style.borderColor = "#D5D8DC";
  });
  document.querySelectorAll(".form-control, .form-select").forEach(input => {
    input.style.background = "#FFFFFF";
    input.style.color = "#1E3A5F";
    input.style.borderColor = "#D5D8DC";
  });
  document.getElementById("dark-mode-toggle").innerHTML = '<i class="fas fa-moon"></i> Dark Mode';
}
```

---

## ✅ SUCCESS CRITERIA (Phase D)

- [ ] Task filters work (status, agent, search)
- [ ] Task sorting works (all options)
- [ ] Bulk task operations (complete, cancel, delete)
- [ ] Agent filters work
- [ ] Agent sorting works
- [ ] Bulk agent operations (enable, disable, reset trust)
- [ ] Export CSV for tasks
- [ ] Export JSON for agents
- [ ] Dark mode toggle works
- [ ] Dark mode persists after page reload
- [ ] Smooth transitions
- [ ] No console errors

---

## 🎨 CSS ADDITIONS for Dark Mode

```css
body.dark-mode {
  background: #1a1a1a;
  color: #e0e0e0;
}

body.dark-mode .card {
  background: #2a2a2a;
  border-color: #444;
  color: #e0e0e0;
}

body.dark-mode .form-control,
body.dark-mode .form-select {
  background: #333;
  color: #e0e0e0;
  border-color: #444;
}

body.dark-mode .btn-outline-secondary {
  color: #999;
  border-color: #555;
}

body.dark-mode .btn-outline-secondary:hover {
  background: #444;
  border-color: #666;
}
```

---

## 📋 FINAL INTEGRATION CHECKLIST

After Phase D Complete:

- [ ] All 4 phases (A, B, C, D) working together
- [ ] No console errors
- [ ] Database queries optimized
- [ ] UI responsive on all screen sizes
- [ ] Keyboard shortcuts working
- [ ] Accessibility (ARIA labels, alt text)
- [ ] Performance acceptable (< 2s load time)
- [ ] Security validated (auth, input validation)

---

**Status**: All 4 phases documented and ready for implementation
**Estimated Total Duration**: 3-4 weeks (part-time) or 1-2 weeks (full-time)
**Next Action**: Begin Phase A UI Testing
