/**
 * Kubernetes Monitoring Dashboard Components
 * UAP Frontend Integration
 *
 * Provides real-time Kubernetes cluster monitoring:
 * - Pod status display (poll + SSE streaming)
 * - Service discovery
 * - Deployment tracking
 * - Metrics visualization
 * - Event streaming (real-time)
 */

const K8S_API_BASE = "http://localhost:8002/mapi/v1/kubernetes";
const K8S_REFRESH_INTERVAL = 5000; // 5 seconds
const K8S_SSE_URL = `${K8S_API_BASE}/stream`;
let k8sEventSource = null;
let k8sAutoRefreshInterval = null;
let recentEvents = []; // Buffer for real-time events

// ──────────────────────────────────────────────────────────────────────────
// REAL-TIME EVENT STREAMING
// ──────────────────────────────────────────────────────────────────────────

function startRealTimeEventStream(apiKey = "") {
  const key = apiKey || localStorage.getItem("api_key") || "dev-key";

  if (k8sEventSource) {
    console.warn("Event stream already running");
    return;
  }

  try {
    k8sEventSource = new EventSource(`${K8S_SSE_URL}?api_key=${key}`, {
      headers: { "X-API-Key": key },
    });

    k8sEventSource.addEventListener("message", (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === "connected") {
          console.log("✓ Real-time stream connected");
          showNotification("Real-time monitoring connected", "success", 3000);
          updateStreamStatus(true);
        } else if (data.type === "pod_status_change") {
          handlePodStatusChange(data);
          addToRecentEvents(data);
        } else if (data.type === "cluster_event") {
          handleClusterEvent(data);
          addToRecentEvents(data);
        }
      } catch (e) {
        console.error("Failed to parse SSE data:", e);
      }
    });

    k8sEventSource.addEventListener("error", (error) => {
      console.error("Stream error:", error);
      stopRealTimeEventStream();
      updateStreamStatus(false);
      showNotification("Real-time stream disconnected", "warning", 5000);

      // Attempt reconnect after 5 seconds
      setTimeout(() => {
        console.log("Attempting to reconnect real-time stream...");
        startRealTimeEventStream(apiKey);
      }, 5000);
    });

    console.log("Real-time event stream started");
  } catch (error) {
    console.error("Failed to start event stream:", error);
    showNotification(
      `Failed to start real-time stream: ${error.message}`,
      "error",
      5000,
    );
  }
}

function stopRealTimeEventStream() {
  if (k8sEventSource) {
    k8sEventSource.close();
    k8sEventSource = null;
    updateStreamStatus(false);
    console.log("Real-time event stream stopped");
  }
}

function addToRecentEvents(event) {
  recentEvents.unshift(event);
  if (recentEvents.length > 100) {
    recentEvents = recentEvents.slice(0, 100); // Keep last 100
  }
}

function handlePodStatusChange(data) {
  const pod = data.pod_name;
  const status = data.status;
  console.log(`Pod update: ${pod} → ${status}`);

  // Update pod row in table if visible
  const podRow = document.querySelector(`[data-pod-name="${pod}"]`);
  if (podRow) {
    const statusCell = podRow.querySelector("[data-status-cell]");
    if (statusCell) {
      const badgeClass =
        status === "Running"
          ? "bg-success"
          : status === "Pending"
            ? "bg-warning"
            : "bg-danger";
      statusCell.innerHTML = `<span class="badge ${badgeClass}">${status}</span>`;
      podRow.classList.add("highlight");
      setTimeout(() => podRow.classList.remove("highlight"), 1000);
    }
  }
}

function handleClusterEvent(data) {
  console.log(`Event: ${data.reason} on ${data.object} - ${data.message}`);
}

function updateStreamStatus(isConnected) {
  const indicator = document.getElementById("stream-status-indicator");
  if (indicator) {
    if (isConnected) {
      indicator.innerHTML =
        '<span class="badge bg-success"><i class="fas fa-circle"></i> Live</span>';
    } else {
      indicator.innerHTML =
        '<span class="badge bg-danger"><i class="fas fa-circle"></i> Offline</span>';
    }
  }
}

// ──────────────────────────────────────────────────────────────────────────
// KUBERNETES DATA FETCHING
// ──────────────────────────────────────────────────────────────────────────

async function fetchK8sClusterInfo(apiKey = "") {
  try {
    const response = await fetch(`${K8S_API_BASE}/cluster-info`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": apiKey || localStorage.getItem("api_key") || "dev-key",
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Failed to fetch cluster info:", error);
    return { status: "error", error: error.message };
  }
}

async function fetchK8sPods(apiKey = "") {
  try {
    const response = await fetch(`${K8S_API_BASE}/pods`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": apiKey || localStorage.getItem("api_key") || "dev-key",
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Failed to fetch pods:", error);
    return {
      status: "error",
      pods: { total_pods: 0, running: 0, pending: 0, failed: 0, pods: [] },
    };
  }
}

async function fetchK8sServices(apiKey = "") {
  try {
    const response = await fetch(`${K8S_API_BASE}/services`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": apiKey || localStorage.getItem("api_key") || "dev-key",
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Failed to fetch services:", error);
    return { status: "error", services: { count: 0, services: [] } };
  }
}

async function fetchK8sDeployments(apiKey = "") {
  try {
    const response = await fetch(`${K8S_API_BASE}/deployments`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": apiKey || localStorage.getItem("api_key") || "dev-key",
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Failed to fetch deployments:", error);
    return { status: "error", deployments: { count: 0, deployments: [] } };
  }
}

async function fetchK8sEvents(apiKey = "") {
  try {
    const response = await fetch(`${K8S_API_BASE}/events`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": apiKey || localStorage.getItem("api_key") || "dev-key",
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Failed to fetch events:", error);
    return { status: "error", events: { count: 0, events: [] } };
  }
}

async function fetchK8sMetrics(metric = "cluster_health", apiKey = "") {
  try {
    const response = await fetch(`${K8S_API_BASE}/metrics?metric=${metric}`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": apiKey || localStorage.getItem("api_key") || "dev-key",
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Failed to fetch metrics:", error);
    return { status: "error", data: {} };
  }
}

async function restartK8sPod(podName, namespace = "adrion-369", apiKey = "") {
  if (!confirm(`⚠️ Are you sure you want to restart pod: ${podName}?`)) {
    return { status: "cancelled" };
  }

  try {
    const response = await fetch(
      `${K8S_API_BASE}/pod/${podName}/restart?namespace=${namespace}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-API-Key": apiKey || localStorage.getItem("api_key") || "dev-key",
        },
      },
    );

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const result = await response.json();
    showNotification(`Pod ${podName} restart requested`, "success");
    return result;
  } catch (error) {
    console.error("Failed to restart pod:", error);
    showNotification(`Failed to restart pod: ${error.message}`, "error");
    return { status: "error", error: error.message };
  }
}

// ──────────────────────────────────────────────────────────────────────────
// UI RENDERING FUNCTIONS
// ──────────────────────────────────────────────────────────────────────────

function renderClusterInfo(data) {
  const container = document.getElementById("k8s-cluster-info");
  if (!container) return;

  if (data.status !== "success") {
    container.innerHTML = `<div class="alert alert-danger">Failed to load cluster info: ${data.error || "Unknown error"}</div>`;
    return;
  }

  const cluster = data.cluster || {};
  container.innerHTML = `
        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <h6 class="card-title">Cluster Status</h6>
                        <p>
                            <strong>Status:</strong>
                            <span class="badge ${cluster.status === "connected" ? "bg-success" : "bg-danger"}">
                                ${cluster.status || "Unknown"}
                            </span>
                        </p>
                        <p><strong>Nodes:</strong> ${cluster.nodes || 0}</p>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderPodsStatus(data) {
  const container = document.getElementById("k8s-pods-status");
  if (!container) return;

  if (data.status !== "success") {
    container.innerHTML = `<div class="alert alert-danger">Failed to load pods: ${data.error || "Unknown error"}</div>`;
    return;
  }

  const pods = data.pods || {
    total_pods: 0,
    running: 0,
    pending: 0,
    failed: 0,
    pods: [],
  };

  const html = `
        <div class="row mb-3">
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h2 class="card-title">${pods.running}</h2>
                        <p class="card-text text-success">Running</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h2 class="card-title">${pods.pending}</h2>
                        <p class="card-text text-warning">Pending</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h2 class="card-title">${pods.failed}</h2>
                        <p class="card-text text-danger">Failed</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <h2 class="card-title">${pods.total_pods}</h2>
                        <p class="card-text text-info">Total</p>
                    </div>
                </div>
            </div>
        </div>
        <div class="table-responsive">
            <table class="table table-hover table-sm">
                <thead>
                    <tr>
                        <th>Pod Name</th>
                        <th>Status</th>
                        <th>IP Address</th>
                        <th>Ready</th>
                        <th>Created</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${pods.pods
                      .map(
                        (pod) => `
                        <tr data-pod-name="${pod.name}">
                            <td><code>${pod.name}</code></td>
                            <td data-status-cell>
                                <span class="badge ${
                                  pod.status === "Running"
                                    ? "bg-success"
                                    : pod.status === "Pending"
                                      ? "bg-warning"
                                      : "bg-danger"
                                }">
                                    ${pod.status}
                                </span>
                            </td>
                            <td>${pod.ip}</td>
                            <td>${pod.ready ? "✓" : "✗"}</td>
                            <td><small>${new Date(pod.created).toLocaleString()}</small></td>
                            <td>
                                <button class="btn btn-sm btn-outline-danger" onclick="restartK8sPod('${pod.name}')">
                                    <i class="fas fa-redo"></i> Restart
                                </button>
                            </td>
                        </tr>
                    `,
                      )
                      .join("")}
                </tbody>
            </table>
        </div>
    `;

  container.innerHTML = html;
}

function renderServices(data) {
  const container = document.getElementById("k8s-services");
  if (!container) return;

  if (data.status !== "success") {
    container.innerHTML = `<div class="alert alert-danger">Failed to load services: ${data.error || "Unknown error"}</div>`;
    return;
  }

  const services = data.services || { count: 0, services: [] };

  const html = `
        <div class="alert alert-info">
            <strong>${services.count}</strong> services found in namespace <code>adrion-369</code>
        </div>
        <div class="table-responsive">
            <table class="table table-sm">
                <thead>
                    <tr>
                        <th>Service Name</th>
                        <th>Type</th>
                        <th>Cluster IP</th>
                        <th>External IP</th>
                        <th>Ports</th>
                        <th>Selector</th>
                    </tr>
                </thead>
                <tbody>
                    ${services.services
                      .map(
                        (svc) => `
                        <tr>
                            <td><code>${svc.name}</code></td>
                            <td><span class="badge bg-info">${svc.type}</span></td>
                            <td><code>${svc.cluster_ip}</code></td>
                            <td><code>${svc.external_ip}</code></td>
                            <td>
                                ${svc.ports.map((port) => `<span class="badge bg-secondary">${port}</span>`).join(" ")}
                            </td>
                            <td><small>${JSON.stringify(svc.selector)}</small></td>
                        </tr>
                    `,
                      )
                      .join("")}
                </tbody>
            </table>
        </div>
    `;

  container.innerHTML = html;
}

function renderDeployments(data) {
  const container = document.getElementById("k8s-deployments");
  if (!container) return;

  if (data.status !== "success") {
    container.innerHTML = `<div class="alert alert-danger">Failed to load deployments: ${data.error || "Unknown error"}</div>`;
    return;
  }

  const deployments = data.deployments || { count: 0, deployments: [] };

  const html = `
        <div class="alert alert-info">
            <strong>${deployments.count}</strong> deployments in namespace <code>adrion-369</code>
        </div>
        <div class="table-responsive">
            <table class="table table-sm">
                <thead>
                    <tr>
                        <th>Deployment</th>
                        <th>Image</th>
                        <th>Desired</th>
                        <th>Ready</th>
                        <th>Updated</th>
                        <th>Available</th>
                        <th>Created</th>
                    </tr>
                </thead>
                <tbody>
                    ${deployments.deployments
                      .map((dep) => {
                        const readyPercent =
                          dep.replicas > 0
                            ? Math.round((dep.ready / dep.replicas) * 100)
                            : 0;
                        return `
                            <tr>
                                <td><code>${dep.name}</code></td>
                                <td><small><code>${dep.image}</code></small></td>
                                <td>${dep.replicas}</td>
                                <td>
                                    <div class="progress" style="height: 20px;">
                                        <div class="progress-bar ${readyPercent === 100 ? "bg-success" : "bg-warning"}"
                                             style="width: ${readyPercent}%">
                                            ${dep.ready}/${dep.replicas}
                                        </div>
                                    </div>
                                </td>
                                <td>${dep.updated}</td>
                                <td>${dep.available}</td>
                                <td><small>${new Date(dep.created).toLocaleString()}</small></td>
                            </tr>
                        `;
                      })
                      .join("")}
                </tbody>
            </table>
        </div>
    `;

  container.innerHTML = html;
}

function renderEvents(data) {
  const container = document.getElementById("k8s-events");
  if (!container) return;

  if (data.status !== "success") {
    container.innerHTML = `<div class="alert alert-danger">Failed to load events: ${data.error || "Unknown error"}</div>`;
    return;
  }

  const events = data.events || { count: 0, events: [] };

  const html = `
        <div class="alert alert-info">
            <strong>${events.count}</strong> recent cluster events
        </div>
        <div class="timeline">
            ${events.events
              .map(
                (evt) => `
                <div class="timeline-item">
                    <div class="timeline-marker ${evt.type === "Normal" ? "bg-success" : "bg-warning"}"></div>
                    <div class="timeline-content">
                        <h6>
                            <span class="badge ${evt.type === "Normal" ? "bg-success" : "bg-warning"}">
                                ${evt.type}
                            </span>
                            <strong>${evt.reason}</strong> on <code>${evt.object}</code>
                        </h6>
                        <p class="text-muted">${evt.message}</p>
                        <small>${new Date(evt.timestamp).toLocaleString()}</small>
                    </div>
                </div>
            `,
              )
              .join("")}
        </div>
    `;

  container.innerHTML = html;
}

// ──────────────────────────────────────────────────────────────────────────
// AUTO-REFRESH & REAL-TIME UPDATES
// ──────────────────────────────────────────────────────────────────────────

function startK8sAutoRefresh(intervalMs = K8S_REFRESH_INTERVAL) {
  if (k8sAutoRefreshInterval) {
    clearInterval(k8sAutoRefreshInterval);
  }

  k8sAutoRefreshInterval = setInterval(async () => {
    await refreshK8sDashboard();
  }, intervalMs);

  console.log(`K8s auto-refresh started (${intervalMs}ms interval)`);
}

function stopK8sAutoRefresh() {
  if (k8sAutoRefreshInterval) {
    clearInterval(k8sAutoRefreshInterval);
    k8sAutoRefreshInterval = null;
    console.log("K8s auto-refresh stopped");
  }
}

async function refreshK8sDashboard(apiKey = "") {
  const loadingMsg = showNotification(
    "Refreshing Kubernetes dashboard...",
    "info",
    30000,
  );

  try {
    const [clusterInfo, pods, services, deployments, events] =
      await Promise.all([
        fetchK8sClusterInfo(apiKey),
        fetchK8sPods(apiKey),
        fetchK8sServices(apiKey),
        fetchK8sDeployments(apiKey),
        fetchK8sEvents(apiKey),
      ]);

    renderClusterInfo(clusterInfo);
    renderPodsStatus(pods);
    renderServices(services);
    renderDeployments(deployments);
    renderEvents(events);

    if (loadingMsg) loadingMsg.remove();
    showNotification("Kubernetes dashboard updated", "success", 3000);
  } catch (error) {
    if (loadingMsg) loadingMsg.remove();
    showNotification(
      `Failed to refresh dashboard: ${error.message}`,
      "error",
      5000,
    );
  }
}

// ──────────────────────────────────────────────────────────────────────────
// HELPER FUNCTIONS
// ──────────────────────────────────────────────────────────────────────────

function showNotification(message, type = "info", durationMs = 3000) {
  const container = document.getElementById("notifications") || document.body;

  const alertDiv = document.createElement("div");
  alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
  alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

  container.appendChild(alertDiv);

  if (durationMs > 0) {
    setTimeout(() => {
      alertDiv.remove();
    }, durationMs);
  }

  return alertDiv;
}

// ──────────────────────────────────────────────────────────────────────────
// INITIALIZATION
// ──────────────────────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
  console.log("Kubernetes Dashboard initialized");

  // Load data on page load
  refreshK8sDashboard();

  // Start auto-refresh for polling
  startK8sAutoRefresh();

  // Start real-time event stream (SSE)
  startRealTimeEventStream();
});

// Cleanup on page unload
window.addEventListener("beforeunload", () => {
  stopK8sAutoRefresh();
  stopRealTimeEventStream();
});
