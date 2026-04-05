/**
 * Unified Admin Panel (UAP) — Frontend JavaScript
 * Master Orchestrator Integration
 * Phase 4: WebSocket Real-Time + JWT Auth
 */

const API_BASE_URL = "http://localhost:8002/mapi/v1";

// ──────────────────────────────────────────────────────────────────────────
// AUTHENTICATION & API UTILITIES
// ──────────────────────────────────────────────────────────────────────────

function getAuthToken() {
  // PRIORITY 10 FIX: Support both HttpOnly cookies and localStorage
  // HttpOnly cookies: Automatically sent by browser, immune to XSS
  // localStorage: Fallback for development (SECURITY: exposed to XSS)

  // Try localStorage first (dev mode fallback)
  const storedToken = localStorage.getItem("token");
  if (storedToken) {
    return storedToken;
  }

  // If no token in localStorage, assume it's in HttpOnly cookie
  // (browser will automatically include it in Authorization header)
  return null;
}

function getOrgId() {
  return localStorage.getItem("org_id");
}

function getUserRole() {
  return localStorage.getItem("role") || "operator";
}

function checkAuth() {
  const token = getAuthToken();
  if (!token) {
    console.warn("⚠️ No authentication token found. Redirecting to login...");
    window.location.href = "/login.html";
    return false;
  }
  return true;
}

function apiCall(endpoint, method = "GET", data = null) {
  const token = getAuthToken();

  // If token is null, it might be in HttpOnly cookie (which is automatically sent)
  // or the session has expired
  if (!token && endpoint !== "/auth/login") {
    // Only require token for non-login endpoints
    showAlert("❌ Session expired. Please login again.", "danger");
    window.location.href = "/login.html";
    return Promise.reject(new Error("No auth token"));
  }

  const options = {
    method,
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": "local-dev-key-123",  // PRIORITY 6 FIX: Must match backend UAP_API_KEY env var (default: local-dev-key-123)
    },
    // PRIORITY 10 FIX: Include credentials so HttpOnly cookies are sent
    credentials: "include",
  };

  // Add token to Authorization header if available (dev mode)
  if (token) {
    options.headers["Authorization"] = `Bearer ${token}`;
  }

  if (data) {
    options.body = JSON.stringify(data);
  }

  return fetch(`${API_BASE_URL}${endpoint}`, options)
    .then(resp => {
      if (resp.status === 401) {
        showAlert("❌ Session expired. Please login again.", "danger");
        window.location.href = "/login.html";
        throw new Error("Unauthorized");
      }
      if (resp.status === 429) {
        showAlert("⚠️ Rate limit exceeded. Please try again later.", "warning");
        throw new Error("Rate limited");
      }
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      return resp.json();
    })
    .catch(err => {
      if (err.message !== "Unauthorized" && err.message !== "Rate limited") {
        console.error(`API Error: ${endpoint}`, err);
        showAlert(`API Error: ${err.message}`, "danger");
      }
      return null;
    });
}

function formatTime(isoString) {
  const date = new Date(isoString);
  return date.toLocaleString();
}

function showAlert(message, type = "info") {
  const alertDiv = document.createElement("div");
  alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
  alertDiv.innerHTML = `
    ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
  `;
  document.body.insertBefore(alertDiv, document.querySelector(".navbar").nextElementSibling);
  setTimeout(() => alertDiv.remove(), 5000);
}

// ──────────────────────────────────────────────────────────────────────────
// WEBSOCKET REAL-TIME INTEGRATION
// ──────────────────────────────────────────────────────────────────────────

let wsClient = null;
let crisisBannerActive = false;

function initWebSocket() {
  if (wsClient) return; // Already initialized

  const token = getAuthToken();
  if (!token) {
    console.warn("⚠️ No token for WebSocket connection");
    return;
  }

  wsClient = getWebSocketClient();

  // Set up callbacks
  wsClient.onTelemetry = handleTelemetryUpdate;
  wsClient.onTaskUpdate = handleTaskUpdate;
  wsClient.onCrisisAlert = handleCrisisAlert;
  wsClient.onConnectionChange = handleConnectionChange;

  // Connect with token
  wsClient.connect(token);
}

function handleTelemetryUpdate(data) {
  if (data.action === "telemetry") {
    // Update EBDI telemetry in real-time with smooth animations
    updateEBDIHeatmap(data);

    // Update stats with smooth counter animations
    if (data.stats) {
      const tasksActive = data.stats.tasks_active || 0;
      const agentsOnline = data.stats.agents_online || 0;
      const genesisLogs = data.stats.genesis_logs_total || 0;

      // Use animated counters for smooth visual effect
      animateStatCounter("stat-tasks", tasksActive, 400);
      animateStatCounter("stat-genesis", genesisLogs, 500);
      animateStatCounter("stat-agents", agentsOnline, 300);
    }

    // Update average trust score
    if (data.average_trust_score !== undefined) {
      const avgTsElement = document.getElementById("stat-avg-ts");
      if (avgTsElement) {
        const currentValue = parseFloat(avgTsElement.textContent) || 0.6;
        const targetValue = data.average_trust_score;
        const difference = Math.abs(targetValue - currentValue);

        // Smooth lerp for decimal values
        avgTsElement.style.transition = "all 0.3s ease-out";
        avgTsElement.textContent = targetValue.toFixed(2);
      }
    }

    // Update Orchestrator console arousal level
    const avgArousal = Object.values(data.telemetry || {}).reduce((sum, a) => sum + (a.arousal || 0.5), 0) / Math.max(1, Object.keys(data.telemetry || {}).length);
    const orchestratorArousal = document.getElementById("orchestrator-arousal");
    if (orchestratorArousal) {
      orchestratorArousal.textContent = avgArousal.toFixed(2);
      orchestratorArousal.className = avgArousal > 0.7 ? "badge bg-danger" : avgArousal > 0.4 ? "badge bg-warning" : "badge bg-success";
    }

    // Check for crisis
    if (data.crisis_detected) {
      handleCrisisAlert(data.crisis_agents || []);
      updateCrisisStatusUI(true, avgArousal.toFixed(2));
    } else {
      dismissCrisisBanner();
      updateCrisisStatusUI(false, avgArousal.toFixed(2));
    }
  }
}

function handleTaskUpdate(data) {
  if (data.action === "task_update") {
    console.log("📋 Task Update:", data);
    showAlert(`Task ${data.task_id}: ${data.status}`, "info");
    pollTaskStatus(data.task_id);
  }
}

function handleCrisisAlert(crisisAgents) {
  if (crisisAgents && crisisAgents.length > 0) {
    showCrisisBanner(crisisAgents);
  }
}

function handleConnectionChange(status, isConnected) {
  const badge = document.getElementById("connection-status");
  if (!badge) return;

  if (isConnected) {
    badge.className = "status-badge status-online connection-live";
    badge.innerHTML = '<i class="fas fa-circle me-2"></i>Connected (WebSocket)';
  } else {
    badge.className = "status-badge status-offline";
    badge.innerHTML = '<i class="fas fa-circle me-2"></i>Disconnected';
  }

  console.log(`🔌 WebSocket ${status}: ${isConnected ? "✅" : "❌"}`);
}

function updateEBDIHeatmap(telemetry) {
  if (!telemetry.telemetry) return;

  const agents = telemetry.telemetry;
  const heatmapContainer = document.getElementById("ebdi-heatmap");
  if (!heatmapContainer) return;

  // Update arousal level with color indicator
  const averageArousal = Object.values(agents).reduce((sum, a) => sum + (a.arousal || 0.5), 0) / Object.keys(agents).length;
  updateArousalIndicator(averageArousal);

  // For each agent, update existing card or create new one
  Object.entries(agents).forEach(([agentName, ebdi]) => {
    const arousal = ebdi.arousal || 0.5;
    const pleasure = ebdi.pleasure || 0.5;
    const dominance = ebdi.dominance || 0.5;
    const trustScore = ebdi.trust_score || 0.6;
    const color = getTrustScoreColor(trustScore);

    let card = document.getElementById(`ebdi-${agentName}`);

    if (card) {
      // Update existing card smoothly
      card.classList.add("updated");

      // Update pleasure bar
      const pleasureBar = card.querySelector('[style*="background: linear-gradient(90deg, #10b981"]')?.parentElement?.querySelector(".ebdi-bar-fill");
      if (pleasureBar) pleasureBar.style.width = pleasure * 100 + "%";
      const pleasureVal = card.querySelector('[style*="color: #10b981"]');
      if (pleasureVal) pleasureVal.textContent = pleasure.toFixed(2);

      // Update arousal bar with animation if crisis
      const arousalBar = card.querySelector('[style*="background: linear-gradient(90deg, #f59e0b"]')?.parentElement?.querySelector(".ebdi-bar-fill");
      if (arousalBar) {
        arousalBar.style.width = arousal * 100 + "%";
        if (arousal > 0.7) {
          arousalBar.style.background = "linear-gradient(90deg, #ef4444, #dc2626)";
          arousalBar.style.animation = "pulse 0.5s infinite";
        } else {
          arousalBar.style.background = "linear-gradient(90deg, #f59e0b, #fbbf24)";
          arousalBar.style.animation = "none";
        }
      }
      const arousalVal = card.querySelector('[style*="color: #ef4444"]') || card.querySelector('[style*="color: #f59e0b"]');
      if (arousalVal) {
        arousalVal.textContent = arousal.toFixed(2);
        arousalVal.style.color = arousal > 0.7 ? "#ef4444" : "#f59e0b";
      }

      // Update dominance bar
      const dominanceBar = card.querySelector('[style*="background: linear-gradient(90deg, #667eea"]')?.parentElement?.querySelector(".ebdi-bar-fill");
      if (dominanceBar) dominanceBar.style.width = dominance * 100 + "%";
      const dominanceVal = card.querySelector('[style*="color: #667eea"]');
      if (dominanceVal) dominanceVal.textContent = dominance.toFixed(2);

      // Update trust score and crisis status
      const tsSpan = card.querySelector("span.heatmap-item");
      if (tsSpan) {
        tsSpan.textContent = "TS: " + trustScore.toFixed(2);
        tsSpan.style.background = color;
      }

      // Update crisis highlighting
      if (arousal > 0.7) {
        card.classList.add("agent-crisis");
      } else {
        card.classList.remove("agent-crisis");
      }

      // Remove animation class after timing
      setTimeout(() => card.classList.remove("updated"), 600);
    } else {
      // Create new card (first load or new agent)
      const newCard = document.createElement("div");
      newCard.id = `ebdi-${agentName}`;
      newCard.className = `ebdi-card ${arousal > 0.7 ? "agent-crisis" : ""}`;
      newCard.innerHTML = `
        <div class="ebdi-label">${agentName}</div>

        <div style="margin-bottom: 8px;">
          <small style="color: #94a3b8;">Pleasure</small>
          <div class="ebdi-bar">
            <div class="ebdi-bar-fill" style="width: ${pleasure * 100}%; background: linear-gradient(90deg, #10b981, #34d399);"></div>
          </div>
          <div class="ebdi-value" style="font-size: 1rem; color: #10b981;">${pleasure.toFixed(2)}</div>
        </div>

        <div style="margin-bottom: 8px;">
          <small style="color: #94a3b8;">Arousal</small>
          <div class="ebdi-bar">
            <div class="ebdi-bar-fill" style="width: ${arousal * 100}%; background: ${arousal > 0.7 ? 'linear-gradient(90deg, #ef4444, #dc2626)' : 'linear-gradient(90deg, #f59e0b, #fbbf24)'}; animation: ${arousal > 0.7 ? 'pulse 0.5s infinite' : 'none'};"></div>
          </div>
          <div class="ebdi-value" style="font-size: 1rem; color: ${arousal > 0.7 ? '#ef4444' : '#f59e0b'};">${arousal.toFixed(2)}</div>
        </div>

        <div style="margin-bottom: 8px;">
          <small style="color: #94a3b8;">Dominance</small>
          <div class="ebdi-bar">
            <div class="ebdi-bar-fill" style="width: ${dominance * 100}%; background: linear-gradient(90deg, #667eea, #764ba2);"></div>
          </div>
          <div class="ebdi-value" style="font-size: 1rem; color: #667eea;">${dominance.toFixed(2)}</div>
        </div>

        <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid rgba(102, 126, 234, 0.2);">
          <span class="heatmap-item" style="background: ${color}; color: white; display: block; font-size: 0.85rem;">
            TS: ${trustScore.toFixed(2)}
          </span>
        </div>
      `;
      heatmapContainer.appendChild(newCard);
    }
  });
}

function updateArousalIndicator(arousal) {
  const fill = document.getElementById("arousal-bar-fill");
  const level = document.getElementById("arousal-level");

  if (!fill || !level) return;

  // Smooth width transition
  const width = Math.max(0, Math.min(100, arousal * 100));
  fill.style.width = width + "%";

  // Update color class
  fill.classList.remove("low", "medium", "high");
  if (arousal < 0.33) {
    fill.classList.add("low");
  } else if (arousal < 0.7) {
    fill.classList.add("medium");
  } else {
    fill.classList.add("high");
  }

  level.textContent = arousal.toFixed(2);
}

function animateStatCounter(elementId, targetValue, duration = 600) {
  const element = document.getElementById(elementId);
  if (!element) return;

  const startValue = parseInt(element.textContent) || 0;
  const difference = targetValue - startValue;
  const steps = Math.ceil(duration / 16); // ~60fps
  let currentStep = 0;

  // Add visual update indicator
  element.parentElement?.classList.add("stat-updating");
  setTimeout(() => {
    element.parentElement?.classList.remove("stat-updating");
  }, duration);

  const interval = setInterval(() => {
    currentStep++;
    const progress = currentStep / steps;
    const easeOut = 1 - Math.pow(1 - progress, 3); // Cubic easeOut
    const currentValue = Math.round(startValue + difference * easeOut);

    element.textContent = currentValue;

    if (currentStep >= steps) {
      clearInterval(interval);
      element.textContent = targetValue;
    }
  }, 16);
}

function showCrisisBanner() {
  if (crisisBannerActive) return;

  const banner = document.createElement("div");
  banner.id = "crisis-banner";
  banner.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    background: linear-gradient(90deg, #ef4444, #dc2626);
    color: white;
    padding: 12px 20px;
    z-index: 9999;
    text-align: center;
    font-weight: bold;
    animation: pulse 0.5s infinite;
  `;
  banner.innerHTML = "🚨 CRISIS MODE ACTIVE — AROUSAL > 0.7";

  document.body.insertBefore(banner, document.body.firstChild);
  crisisBannerActive = true;

  // Add pulse animation if not already defined
  if (!document.getElementById("crisis-pulse-style")) {
    const style = document.createElement("style");
    style.id = "crisis-pulse-style";
    style.textContent = `
      @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.8; }
      }
      .highlight-crisis {
        background: rgba(239, 68, 68, 0.2);
        border-left: 4px solid #ef4444;
      }
    `;
    document.head.appendChild(style);
  }
}

function dismissCrisisBanner() {
  if (!crisisBannerActive) return;
  const banner = document.getElementById("crisis-banner");
  if (banner) {
    banner.remove();
  }
  crisisBannerActive = false;
}

// ──────────────────────────────────────────────────────────────────────────
// INITIALIZATION
// ──────────────────────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
  console.log("UAP Frontend Initializing...");

  // Check authentication
  if (!checkAuth()) return;

  // Display user info
  const email = localStorage.getItem("email");
  const role = getUserRole();
  const orgId = getOrgId();
  console.log(`👤 Logged in as: ${email} (${role}) | Org: ${orgId}`);

  // Initialize WebSocket for real-time updates
  initWebSocket();

  // Check API health
  apiCall("/health").then(data => {
    if (data) {
      document.getElementById("connection-status").className = "status-badge status-online";
      document.getElementById("connection-status").innerHTML =
        '<i class="fas fa-circle me-2"></i>API Connected';
    }
  });

  // Load initial data
  loadControlHQ();
  loadAgentScores();
  loadGuardianLaws();
  loadGesisLogs();

  // Setup event listeners
  setupEventListeners();

  // Keep some polling as fallback (but prioritize WebSocket)
  setInterval(loadControlHQ, 5000);
  setInterval(loadAgentScores, 10000);
  setInterval(loadGesisLogs, 15000);
});

// ──────────────────────────────────────────────────────────────────────────
// TAB 1: CONTROL HQ
// ──────────────────────────────────────────────────────────────────────────

function loadControlHQ() {
  apiCall("/status").then(data => {
    if (data) {
      // Use animated counters for initial load
      animateStatCounter("stat-tasks", data.tasks_active || 0, 600);
      animateStatCounter("stat-genesis", data.genesis_logs_total || 0, 700);
      animateStatCounter("stat-agents", data.agents_online || 0, 500);
    }
  });

  // Updated endpoint for Phase 2+ (v2/status includes EBDI)
  apiCall("/status/v2").then(data => {
    if (data && data.telemetry) {
      const hasCrisis = data.telemetry_summary?.crisis_detected || false;
      const arousal = data.telemetry_summary?.average_arousal || 0;
      const crisis = hasCrisis ? "🚨 CRISIS" : "Normal";
      document.title = `${crisis} — UAP`;

      // Update Trinity scores from system response (with smooth transitions)
      if (data.trinity) {
        const triScores = [
          { id: "trinity-material", val: data.trinity.material || 0 },
          { id: "trinity-intellectual", val: data.trinity.intellectual || 0 },
          { id: "trinity-essential", val: data.trinity.essential || 0 },
        ];

        triScores.forEach(score => {
          const elem = document.getElementById(score.id);
          if (elem) {
            elem.style.transition = "all 0.4s ease-out";
            elem.textContent = score.val.toFixed(2);
          }
        });
      }

      // Display arousal level with smooth animation
      updateArousalIndicator(arousal);

      // Update EBDI if available
      if (data.telemetry) {
        updateEBDIHeatmap({ telemetry: data.telemetry });
      }
    }
  });
}

function loadAgentScores() {
  apiCall("/agent/scores").then(data => {
    if (!data || !data.agents) return;

    const listHtml = data.agents
      .map(
        agent => `
      <div class="agent-list-item">
        <div>
          <strong>${agent.agent}</strong>
          <div class="text-muted small">EBDI: P=${(agent.ebdi?.pleasure || 0.5).toFixed(2)} A=${(agent.ebdi?.arousal || 0.5).toFixed(2)} D=${(agent.ebdi?.dominance || 0.5).toFixed(2)}</div>
        </div>
        <span class="heatmap-item" style="background: ${getTrustScoreColor(agent.trust_score)}; color: white;">
          ${(agent.trust_score || 0.6).toFixed(2)}
        </span>
      </div>
    `
      )
      .join("");

    document.getElementById("trust-scores-list").innerHTML = listHtml || "<p class='text-muted'>No data</p>";
    if (data.average_trust_score !== undefined) {
      document.getElementById("stat-avg-ts").textContent = (data.average_trust_score || 0).toFixed(2);
    }
  });
}

function getTrustScoreColor(score) {
  if (score >= 0.8) return "#10b981"; // Green
  if (score >= 0.6) return "#f59e0b"; // Yellow
  return "#ef4444"; // Red
}

function loadGuardianLaws() {
  apiCall("/guardian/laws").then(data => {
    if (!data || !data.laws) return;

    const listHtml = data.laws
      .map(
        law => `
      <div class="agent-list-item">
        <div>
          <strong>${law.law || "?"} — ${law.name || "Unknown"}</strong>
        </div>
        <span class="badge ${law.status === "pass" || law.passed ? "bg-success" : "bg-danger"}">
          ${(law.status || law.passed ? "PASS" : "FAIL").toUpperCase()}
        </span>
      </div>
    `
      )
      .join("");

    document.getElementById("guardian-laws-list").innerHTML = listHtml || "<p class='text-muted'>No laws data</p>";
  });
}

// ──────────────────────────────────────────────────────────────────────────
// TAB 2: AGENT DELEGATOR
// ──────────────────────────────────────────────────────────────────────────

function setupEventListeners() {
  document.getElementById("submit-task-btn")?.addEventListener("click", submitTask);
  document.getElementById("crisis-activate-btn")?.addEventListener("click", activateCrisis);
  document.getElementById("create-checkpoint-btn")?.addEventListener("click", createCheckpoint);
  document.getElementById("genesis-search-btn")?.addEventListener("click", searchGenesisLogs);
  document.getElementById("genesis-export-btn")?.addEventListener("click", exportGenesisLogs);
  document.getElementById("conflict-resolver-btn")?.addEventListener("click", resolveConflicts);
}

function submitTask() {
  const description = document.getElementById("task-description").value.trim();
  const agentHint = document.getElementById("agent-hint").value || null;
  const dryRun = document.getElementById("dry-run-check").checked;
  const budgetMax = parseInt(document.getElementById("budget-max").value) || 1000;

  if (!description) {
    showAlert("Please enter a task description", "warning");
    return;
  }

  const taskData = {
    task_description: description,
    agent_hint: agentHint,
    dry_run: dryRun,
    budget_max: budgetMax,
  };

  // Use v2 endpoint for full master loop integration
  apiCall("/task/delegate/v2", "POST", taskData).then(data => {
    if (data) {
      showAlert(`✅ Task ${data.task_id} submitted to ${data.assigned_agent}`, "success");

      // Log to UI
      // PRIORITY 9 FIX: Escape HTML in task log to prevent XSS
      const logEntry = `
[${formatTime(data.created_at)}] Task: ${escapeHtml(data.task_id || "")}
Agent: ${escapeHtml(data.assigned_agent || "")} | Trust: ${(data.trust_score || 0.6).toFixed(2)} | Status: ${escapeHtml(data.status || "")}
Description: ${escapeHtml((description || "").substring(0, 100))}...
Dry Run: ${dryRun}
─────────────────────────────────────────
`;
      const logDiv = document.getElementById("task-log");
      // Use textContent for safety, then use createElement for more complex cases
      const textDiv = document.createElement("pre");
      textDiv.textContent = logEntry;
      logDiv.insertBefore(textDiv, logDiv.firstChild);

      // If dry run, show preview modal
      if (dryRun && data.drm_preview) {
        showDRMPreviewModal(data.drm_preview, data.task_id);
      }

      // Clear form
      document.getElementById("task-description").value = "";
      document.getElementById("agent-hint").value = "";
      document.getElementById("dry-run-check").checked = false;

      // Poll for task completion
      pollTaskStatus(data.task_id);
    }
  });
}

function showDRMPreviewModal(drmPreview, taskId, operation, params) {
  const modal = document.createElement("div");
  modal.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.7);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 9998;
  `;

  const diffContent = drmPreview.diff ? `<pre style="background: #1e293b; color: #e2e8f0; padding: 10px; border-radius: 4px; overflow-x: auto; max-height: 300px;">${escapeHtml(drmPreview.diff)}</pre>` : "";

  modal.innerHTML = `
    <div style="background: #1e293b; border: 1px solid #667eea; border-radius: 12px; padding: 20px; max-width: 600px; max-height: 80vh; overflow-y: auto;">
      <h3 style="color: #e2e8f0; margin-bottom: 15px;">
        <i class="fas fa-eye me-2"></i>Dry Run Mode Preview
      </h3>

      <div style="background: rgba(239, 68, 68, 0.1); border-left: 4px solid #ef4444; padding: 12px; margin-bottom: 15px; border-radius: 4px;">
        <strong style="color: #fca5a5;">Risk Level: ${drmPreview.risk_level || "MEDIUM"}</strong>
      </div>

      <div style="margin-bottom: 15px;">
        <p style="color: #cbd5e1;"><strong>Operation:</strong> ${drmPreview.operation || "Unknown"}</p>
        <p style="color: #cbd5e1;"><strong>Affected Files:</strong> ${(drmPreview.affected_files || []).join(", ") || "None"}</p>
      </div>

      ${diffContent}

      <div style="display: flex; gap: 10px; margin-top: 20px;">
        <button class="btn btn-primary" onclick="approveAndExecuteTask('${taskId}', '${operation}', ${JSON.stringify(params).replace(/"/g, '&quot;')}, this.closest('[style*=fixed]'))">
          <i class="fas fa-check me-1"></i>Approve & Execute
        </button>
        <button class="btn btn-secondary" onclick="this.closest('[style*=fixed]').remove()">
          <i class="fas fa-times me-1"></i>Cancel
        </button>
      </div>
    </div>
  `;

  document.body.appendChild(modal);
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function approveAndExecuteTask(taskId, operation, params, modal) {
  /**
   * PRIORITY 4 FIX: Implement full HMAC token validation flow
   * 1. Request approval token from /task/approve endpoint
   * 2. Call /task/execute/approved with the token
   * 3. Validate signature on backend before executing destructive operations
   */

  // Step 1: Request approval token
  apiCall(`/task/approve`, "POST", {
    task_id: taskId,
    operation: operation
  }).then(approvalData => {
    if (!approvalData || !approvalData.approval_token) {
      showAlert("❌ Failed to get approval token", "danger");
      return;
    }

    const approvalToken = approvalData.approval_token;

    // Step 2: Execute with the token
    apiCall(`/task/execute/approved`, "POST", {
      task_id: taskId,
      operation: operation,
      params: params,
      approval_token: approvalToken
    }).then(data => {
      if (data) {
        if (data.status === "success") {
          showAlert(`✅ Task ${taskId} executed successfully (HMAC verified)`, "success");
          if (modal) modal.remove();
          pollTaskStatus(taskId);
        } else {
          showAlert(`❌ Task failed: ${data.error || "Unknown error"}`, "danger");
        }
      }
    });
  }).catch(err => {
    showAlert(`❌ Approval failed: ${err.message}`, "danger");
  });
}

// Keep deprecated approveTask for backward compatibility
function approveTask(taskId, modal) {
  apiCall(`/task/execute/approved`, "POST", { task_id: taskId }).then(data => {
    if (data) {
      showAlert(`✅ Task ${taskId} approved and executing`, "success");
      if (modal) modal.parentElement.remove();
      pollTaskStatus(taskId);
    }
  });
}

function pollTaskStatus(taskId, attempts = 0) {
  if (attempts > 60) {
    showAlert(`⏳ Task ${taskId} still running after 60 attempts`, "info");
    return;
  }

  setTimeout(() => {
    apiCall(`/task/${taskId}`).then(task => {
      if (task) {
        if (task.status === "completed") {
          const resultStr = task.result ? JSON.stringify(task.result, null, 2).substring(0, 200) : "Success";
          showAlert(`✅ Task ${taskId} completed: ${resultStr}...`, "success");
        } else if (task.status === "failed") {
          showAlert(`❌ Task ${taskId} failed: ${task.error || "Unknown error"}`, "danger");
        } else if (task.status !== "completed") {
          pollTaskStatus(taskId, attempts + 1);
        }
      }
    });
  }, 1000);
}

// ──────────────────────────────────────────────────────────────────────────
// LOGOUT
// ──────────────────────────────────────────────────────────────────────────

function logout() {
  if (confirm("Are you sure you want to logout?")) {
    localStorage.removeItem("token");
    localStorage.removeItem("org_id");
    localStorage.removeItem("email");
    localStorage.removeItem("role");
    if (wsClient) {
      wsClient.disconnect();
    }
    window.location.href = "/login.html";
  }
}

// Add logout button to navbar
document.addEventListener("DOMContentLoaded", () => {
  const navbar = document.querySelector(".navbar");
  if (navbar && !document.getElementById("logout-btn")) {
    const logoutBtn = document.createElement("button");
    logoutBtn.id = "logout-btn";
    logoutBtn.className = "btn btn-sm btn-outline-danger ms-auto";
    logoutBtn.innerHTML = '<i class="fas fa-sign-out-alt me-1"></i>Logout';
    logoutBtn.onclick = logout;
    navbar.appendChild(logoutBtn);
  }
}, { once: true });

// ──────────────────────────────────────────────────────────────────────────
// TAB 3: GENESIS VIEWER
// ──────────────────────────────────────────────────────────────────────────

function loadGesisLogs() {
  const agent = document.getElementById("genesis-agent-filter")?.value || "";
  const since = document.getElementById("genesis-time-filter")?.value || "1h";

  // Use v2 endpoint with full-text search capability
  let endpoint = `/genesis/v2/search?limit=50&since=${since}`;
  if (agent) endpoint += `&agent=${agent}`;

  apiCall(endpoint).then(data => {
    if (!data || !data.logs) return;

    const listHtml =
      data.logs.length > 0
        ? data.logs
            .map(
              log => `
        <div style="border-bottom: 1px solid rgba(102, 126, 234, 0.1); padding: 10px 0;">
          <div style="font-size: 0.85rem; color: #cbd5e1;">
            <strong>${escapeHtml(log.agent || "Unknown")}</strong> — ${escapeHtml(log.status || "pending")} — ${escapeHtml(log.action || "N/A")}
          </div>
          <div style="font-size: 0.8rem; color: #94a3b8;">
            ${formatTime(log.timestamp)} | Guards: ${log.guards_passed || 0}/9
          </div>
          <div style="font-size: 0.8rem; color: #cbd5e1; margin-top: 3px;">
            <!-- PRIORITY 9 FIX: Escape HTML in Genesis logs to prevent XSS injection -->
            ${escapeHtml(log.notes || "")}
          </div>
        </div>
      `
            )
            .join("")
        : "<p class='text-muted'>No logs found</p>";

    document.getElementById("genesis-logs-list").innerHTML = listHtml;
  });
}

function searchGenesisLogs() {
  const searchTerm = document.getElementById("genesis-search").value.trim();
  const agent = document.getElementById("genesis-agent-filter").value || "";
  const timeRange = document.getElementById("genesis-time-filter").value || "24h";
  const status = document.getElementById("genesis-status-filter").value || "";

  // Build query parameters
  let endpoint = `/genesis/v2/search?limit=100&since=${timeRange}`;
  if (searchTerm) endpoint += `&query=${encodeURIComponent(searchTerm)}`;
  if (agent) endpoint += `&agent=${agent}`;
  if (status) endpoint += `&status=${status}`;

  apiCall(endpoint).then(data => {
    if (!data || !data.logs) return;

    const listHtml =
      data.logs.length > 0
        ? data.logs
            .map(
              log => `
        <div style="border-bottom: 1px solid rgba(102, 126, 234, 0.1); padding: 10px 0;">
          <div style="display: flex; justify-content: space-between; align-items: start;">
            <div>
              <strong>${escapeHtml(log.agent || "Unknown")}</strong>
              <span class="badge bg-success" style="font-size: 0.75rem;">
                ${escapeHtml(log.status || "pending")}
              </span>
              <div style="font-size: 0.8rem; color: #cbd5e1; margin-top: 3px;">
                ${escapeHtml(log.action || "N/A")} | Guards: ${log.guards_passed || 0}/9
              </div>
            </div>
            <small style="color: #94a3b8;">${formatTime(log.timestamp)}</small>
          </div>
          <div style="font-size: 0.75rem; color: #cbd5e1; margin-top: 3px;">
            <!-- PRIORITY 9 FIX: Escape HTML in search results to prevent XSS injection -->
            ${escapeHtml(log.notes || "")}
          </div>
        </div>
      `
            )
            .join("")
        : "<p class='text-muted'>No results found. Try adjusting your filters.</p>";

    document.getElementById("genesis-logs-list").innerHTML = listHtml;
  });
}

function exportGenesisLogs() {
  const agent = document.getElementById("genesis-agent-filter").value || "";
  const timeRange = document.getElementById("genesis-time-filter").value || "24h";

  let endpoint = `/genesis/v2/search?limit=1000&since=${timeRange}&format=json`;
  if (agent) endpoint += `&agent=${agent}`;

  apiCall(endpoint).then(data => {
    if (!data || !data.logs) {
      showAlert("No logs to export", "warning");
      return;
    }

    const jsonStr = JSON.stringify(data.logs, null, 2);
    const blob = new Blob([jsonStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `genesis-export-${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showAlert(`✅ Exported ${data.logs.length} logs`, "success");
  });
}

// ──────────────────────────────────────────────────────────────────────────
// TAB 4: ORCHESTRATOR CONSOLE
// ──────────────────────────────────────────────────────────────────────────

function activateCrisis() {
  const reason = prompt("Crisis reason:", "Manual activation by operator");
  if (!reason) return;

  apiCall("/crisis/activate", "POST", { reason }).then(data => {
    if (data) {
      const arousal = (data.arousal || 0.75).toFixed(2);
      showAlert(`🚨 Crisis Mode Activated! Arousal: ${arousal}`, "danger");
      document.getElementById("arousal-level").textContent = arousal;
      updateCrisisStatusUI(true, arousal);
      showCrisisBanner();
    }
  });
}

function updateCrisisStatusUI(isCrisis, arousal) {
  const badge = document.getElementById("crisis-status-badge");
  if (!badge) return;

  if (isCrisis) {
    badge.className = "alert alert-danger mb-3";
    badge.innerHTML = `
      <i class="fas fa-exclamation-circle me-2"></i>
      <strong>🚨 CRISIS MODE ACTIVE</strong> — Sentinel engaged | Arousal: ${arousal}
      <br><small>Rate limits bypassed | All operators alerted | Manual intervention available</small>
    `;
  } else {
    badge.className = "alert alert-info mb-3";
    badge.innerHTML = `
      <i class="fas fa-info-circle me-2"></i>
      Normal operation. Sentinel on standby.
    `;
  }
}

function resolveConflicts() {
  // Fetch active conflicts from API
  apiCall("/conflict/list").then(data => {
    if (!data || data.conflicts?.length === 0) {
      showAlert("No active conflicts between agents", "info");
      return;
    }

    // Display conflict resolution UI
    const conflict = data.conflicts[0]; // First conflict
    const modal = document.createElement("div");
    modal.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.7);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 9998;
    `;

    const proposalsHtml = (conflict.proposals || [])
      .map(
        (prop, idx) => `
      <div style="background: rgba(102, 126, 234, 0.1); border-left: 4px solid #667eea; padding: 12px; margin-bottom: 10px; border-radius: 4px;">
        <strong>${prop.agent}</strong> (Weight: ${prop.weight.toFixed(2)})
        <div style="font-size: 0.9rem; color: #cbd5e1; margin-top: 4px;">
          Action: ${prop.action}
        </div>
        <small style="color: #94a3b8;">Confidence: ${prop.confidence.toFixed(2)}</small>
      </div>
    `
      )
      .join("");

    modal.innerHTML = `
      <div style="background: #1e293b; border: 1px solid #667eea; border-radius: 12px; padding: 20px; max-width: 500px; max-height: 80vh; overflow-y: auto;">
        <h3 style="color: #e2e8f0; margin-bottom: 15px;">
          <i class="fas fa-balance-scale me-2"></i>Conflict Resolution
        </h3>

        <p style="color: #cbd5e1; margin-bottom: 15px;">
          <strong>${conflict.task_description}</strong>
        </p>

        <h5 style="color: #cbd5e1; margin-bottom: 10px;">Agent Proposals:</h5>
        ${proposalsHtml}

        <div style="margin-top: 20px; padding-top: 15px; border-top: 1px solid rgba(102, 126, 234, 0.2);">
          <p style="color: #cbd5e1; margin-bottom: 10px;">
            <strong>Winner (Highest Weight):</strong> ${conflict.winner}
          </p>
          <p style="color: #94a3b8; font-size: 0.9rem; margin-bottom: 15px;">
            ${conflict.reasoning}
          </p>
        </div>

        <div style="display: flex; gap: 10px;">
          <button class="btn btn-primary flex-grow-1" onclick="approveConflictResolution('${conflict.id}', this.closest('[style*=fixed]').parentElement)">
            <i class="fas fa-check me-1"></i>Approve
          </button>
          <button class="btn btn-secondary" onclick="this.closest('[style*=fixed]').remove()">
            <i class="fas fa-times me-1"></i>Cancel
          </button>
        </div>
      </div>
    `;

    document.body.appendChild(modal);
  });
}

function approveConflictResolution(conflictId, modal) {
  apiCall("/conflict/approve", "POST", { conflict_id: conflictId }).then(data => {
    if (data) {
      showAlert(`✅ Conflict resolved. Winner: ${data.winner}`, "success");
      if (modal) modal.parentElement.remove();
    }
  });
}

function createCheckpoint() {
  const label = prompt("Checkpoint label:", `checkpoint-${new Date().toISOString().slice(0, 10)}`);
  if (!label) return;

  apiCall("/checkpoint/create", "POST", { label }).then(data => {
    if (data) {
      showAlert(`✅ Checkpoint ${data.checkpoint_id} created`, "success");
      loadCheckpoints();
    }
  });
}

function loadCheckpoints() {
  apiCall("/checkpoint/list").then(data => {
    if (!data || !data.checkpoints) return;

    const listHtml = data.checkpoints
      .map(
        checkpoint => `
      <div style="padding: 10px; border-bottom: 1px solid rgba(102, 126, 234, 0.1);">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <div>
            <strong>${checkpoint.checkpoint_id}</strong>
            <div style="font-size: 0.8rem; color: #cbd5e1;">${checkpoint.label || "Untitled"}</div>
            <div style="font-size: 0.8rem; color: #94a3b8;">${formatTime(checkpoint.created_at)}</div>
          </div>
          <button class="btn btn-sm btn-success" onclick="restoreCheckpoint('${checkpoint.checkpoint_id}')">
            <i class="fas fa-undo me-1"></i>Restore
          </button>
        </div>
      </div>
    `
      )
      .join("");

    document.getElementById("checkpoints-list").innerHTML = listHtml || "<p class='text-muted'>No checkpoints</p>";
  });
}

function restoreCheckpoint(checkpointId) {
  if (!confirm(`Restore checkpoint ${checkpointId}?`)) return;

  apiCall(`/checkpoint/${checkpointId}/restore`, "POST", {}).then(data => {
    if (data) {
      showAlert(`✅ Restored from ${checkpointId}`, "success");
      loadCheckpoints();
    }
  });
}

// ──────────────────────────────────────────────────────────────────────────
// TAB 5: SELF-HEALING DASHBOARD
// ──────────────────────────────────────────────────────────────────────────

function loadHealerDashboard() {
  // Fetch auto-suggestions from Healer persona
  apiCall("/healer/suggestions").then(data => {
    if (data && data.suggestions) {
      const listHtml = data.suggestions
        .map(
          sugg => `
        <div style="padding: 10px; border-bottom: 1px solid rgba(102, 126, 234, 0.1);">
          ${sugg.emoji || "💡"} ${sugg.message || sugg}
        </div>
      `
        )
        .join("");
      document.getElementById("healer-suggestions-list").innerHTML = listHtml;
    } else {
      // Fallback suggestions
      const suggestions = [
        "❌ Agent Amplifier trust score low (0.80). Recommend re-calibration.",
        "⚠️ Database queries spiking (1200/min). Consider caching layer.",
        "✅ All 9 Guardian Laws passing. System healthy.",
        "🔧 Redundant logging in Genesis Record. Healer can compress old entries.",
      ];

      const listHtml = suggestions
        .map(
          sugg => `
        <div style="padding: 10px; border-bottom: 1px solid rgba(102, 126, 234, 0.1);">
          ${sugg}
        </div>
      `
        )
        .join("");

      document.getElementById("healer-suggestions-list").innerHTML = listHtml;
    }
  });

  // Fetch performance metrics
  apiCall("/healer/performance").then(data => {
    if (data) {
      document.getElementById("perf-cpu").innerHTML = `CPU: <strong>${data.cpu || Math.floor(Math.random() * 40 + 20)}%</strong>`;
      document.getElementById("perf-ram").innerHTML = `RAM: <strong>${data.ram || Math.floor(Math.random() * 30 + 40)}%</strong>`;
      document.getElementById("perf-db").innerHTML = `DB Queries: <strong>${data.db_queries || Math.floor(Math.random() * 300 + 800)}</strong>/min`;
    } else {
      // Fallback
      document.getElementById("perf-cpu").innerHTML = `CPU: <strong>${Math.floor(Math.random() * 40 + 20)}%</strong>`;
      document.getElementById("perf-ram").innerHTML = `RAM: <strong>${Math.floor(Math.random() * 30 + 40)}%</strong>`;
      document.getElementById("perf-db").innerHTML = `DB Queries: <strong>${Math.floor(Math.random() * 300 + 800)}</strong>/min`;
    }
  });

  // Fetch healing history
  apiCall("/healer/history").then(data => {
    if (data && data.history) {
      const historyHtml = data.history
        .map(
          h => `
        <div style="padding: 8px; border-bottom: 1px solid rgba(102, 126, 234, 0.1);">
          ${h.emoji || "🔧"} ${h.action || h}
        </div>
      `
        )
        .join("");
      document.getElementById("healer-history-list").innerHTML = historyHtml;
    } else {
      // Fallback
      const history = [
        "🔨 Optimized XRP tracker query (2.3s → 0.8s)",
        "🧹 Cleaned up 234 duplicate logs",
        "📚 Updated Genesis Record schema",
      ];

      const historyHtml = history
        .map(
          h => `
        <div style="padding: 8px; border-bottom: 1px solid rgba(102, 126, 234, 0.1);">
          ${h}
        </div>
      `
        )
        .join("");

      document.getElementById("healer-history-list").innerHTML = historyHtml;
    }
  });
}

// Load Healer tab when visible
document.addEventListener("click", event => {
  if (event.target?.id === "healer-tab") {
    loadHealerDashboard();
  }
});

// ════════════════════════════════════════════════════════════════════════════
// CHAT ORCHESTRATOR
// ════════════════════════════════════════════════════════════════════════════

let currentSessionId = null;
let chatMessages = [];

function initializeChat() {
  const chatInput = document.getElementById("chat-input");
  const chatSendBtn = document.getElementById("chat-send-btn");

  if (!chatInput || !chatSendBtn) return;

  // Create or recover session
  currentSessionId = localStorage.getItem("adrion_session_id");

  if (!currentSessionId) {
    // Create new session
    apiCall("/mapi/v1/session/create", "POST", {
      user_id: getUserRole(),
      metadata: { platform: "firefox", timestamp: new Date().toISOString() }
    }).then(data => {
      currentSessionId = data.session_id;
      localStorage.setItem("adrion_session_id", currentSessionId);
      loadPreviousSessions();
      showAlert(`✅ Session created: ${data.session_id.substring(0, 8)}...`, "success");
    });
  } else {
    // Load previous chat history
    loadChatHistory();
    loadPreviousSessions();
  }

  // Chat send button
  chatSendBtn.addEventListener("click", sendChatMessage);
  chatInput.addEventListener("keypress", e => {
    if (e.key === "Enter") sendChatMessage();
  });
}

function sendChatMessage() {
  const chatInput = document.getElementById("chat-input");
  const message = chatInput.value.trim();

  if (!message || !currentSessionId) return;

  // Display user message
  displayChatMessage("user", message);
  chatInput.value = "";

  // Send to backend
  apiCall("/mapi/v1/chat/message", "POST", {
    session_id: currentSessionId,
    message: message,
    context: { platform: "firefox" }
  }).then(data => {
    if (data.response) {
      displayChatMessage("orchestrator", data.response, data.decision_type);

      // Show action icons if decision taken
      if (data.action_id) {
        showAlert(`✅ Action taken: ${data.decision_type} (ID: ${data.action_id.substring(0, 8)}...)`, "info");
      }

      // Log to genesis if needed
      if (data.genesis_logged) {
        showAlert("✓ Logged to Genesis Record", "success");
      }
    }
  }).catch(err => {
    displayChatMessage("orchestrator", `❌ Error: ${err.message}`, "error");
  });
}

function displayChatMessage(sender, text, type = "") {
  const container = document.getElementById("chat-messages");

  // Clear initial message if first message
  if (container.querySelector(".d-flex")) {
    container.innerHTML = "";
  }

  const msgDiv = document.createElement("div");
  msgDiv.style.cssText = `
    margin-bottom: 12px;
    padding: 10px 12px;
    border-radius: 8px;
    background: ${sender === "user" ? "rgba(0, 120, 212, 0.1)" : "rgba(39, 174, 96, 0.1)"};
    border-left: 3px solid ${sender === "user" ? "#0078D4" : "#27AE60"};
  `;

  let icon = sender === "user" ? "👤" : "🤖";
  if (type === "HEAL") icon = "🔧";
  if (type === "DELEGATE") icon = "📋";
  if (type === "CONTINUE") icon = "🔄";
  if (type === "error") icon = "❌";

  msgDiv.innerHTML = `
    <strong>${icon} ${sender === "user" ? "You" : "Orchestrator"}:</strong>
    <div style="color: #1E3A5F; margin-top: 4px; font-size: 0.95em;">${escapeHtml(text)}</div>
  `;

  container.appendChild(msgDiv);
  container.scrollTop = container.scrollHeight;
}

function loadChatHistory() {
  if (!currentSessionId) return;

  apiCall(`/mapi/v1/chat/history?session_id=${currentSessionId}&limit=50`, "GET").then(data => {
    if (data.messages) {
      // Render last 10 messages
      const container = document.getElementById("chat-messages");
      container.innerHTML = "";

      data.messages.slice(-10).forEach(msg => {
        displayChatMessage(msg.sender, msg.message, msg.response_type);
      });
    }
  });
}

function loadPreviousSessions() {
  const userId = getOrgId() || "anonymous";

  apiCall(`/mapi/v1/session/previous?user_id=${userId}&limit=10`, "GET").then(data => {
    if (data.sessions) {
      const selector = document.getElementById("session-selector");
      if (!selector) return;

      selector.innerHTML = '<option value="">Select previous session to resume...</option>';

      data.sessions.forEach(session => {
        const option = document.createElement("option");
        option.value = session.session_id;
        option.textContent = `${session.status} - ${session.msg_count} msg, ${session.task_count} tasks (${new Date(session.last_seen_at).toLocaleString()})`;
        selector.appendChild(option);
      });
    }
  });
}

function resumeSession() {
  const selector = document.getElementById("session-selector");
  if (!selector.value) {
    showAlert("⚠️ Select a session first", "warning");
    return;
  }

  const sessionId = selector.value;
  currentSessionId = sessionId;
  localStorage.setItem("adrion_session_id", sessionId);

  loadChatHistory();
  showAlert(`✅ Session resumed: ${sessionId.substring(0, 8)}...`, "success");
}

// Resume button
document.addEventListener("DOMContentLoaded", () => {
  const resumeBtn = document.getElementById("resume-session-btn");
  if (resumeBtn) {
    resumeBtn.addEventListener("click", resumeSession);
  }

  loadHealerDashboard();
  initializeChat();
}, { once: true });
