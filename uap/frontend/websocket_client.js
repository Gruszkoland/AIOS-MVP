/**
 * Unified Admin Panel (UAP) — Phase 4
 * WebSocket Real-Time Telemetry Client
 *
 * Provides real-time EBDI updates, task status, crisis alerts
 * Autoreconnect with exponential backoff
 */

class UAP_WebSocketClient {
  constructor(
    apiBaseUrl = "http://localhost:8002",
    wsUrl = "ws://localhost:8004",
  ) {
    this.apiBaseUrl = apiBaseUrl;
    this.wsUrl = wsUrl;
    this.ws = null;
    this.authenticated = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000; // ms

    // Callbacks
    this.onTelemetry = null;
    this.onTaskUpdate = null;
    this.onCrisisAlert = null;
    this.onConnectionChange = null;

    // State
    this.latestTelemetry = null;
    this.latestTrustScores = null;
  }

  /**
   * Connect to WebSocket server
   * @param {string} token - JWT auth token
   */
  connect(token) {
    console.log(`🔌 WebSocket connecting to ${this.wsUrl}`);

    try {
      this.ws = new WebSocket(this.wsUrl);

      this.ws.onopen = () => this.onOpen(token);
      this.ws.onmessage = (event) => this.onMessage(event);
      this.ws.onerror = (event) => this.onError(event);
      this.ws.onclose = () => this.onClose();
    } catch (err) {
      console.error("❌ WebSocket connection error:", err);
      this.scheduleReconnect();
    }
  }

  onOpen(token) {
    console.log("✅ WebSocket connected");

    this.reconnectAttempts = 0;
    this.authenticated = true;

    // Subscribe to telemetry
    this.send({
      action: "subscribe",
      channel: "telemetry",
    });

    // Subscribe to task updates
    this.send({
      action: "subscribe",
      channel: "tasks",
    });

    if (this.onConnectionChange) {
      this.onConnectionChange("connected", true);
    }
  }

  onMessage(event) {
    try {
      const data = JSON.parse(event.data);

      switch (data.action) {
        case "subscribed":
          console.log(`✅ Subscribed to ${data.channel}`);
          break;

        case "telemetry":
          this.latestTelemetry = data;
          if (this.onTelemetry) {
            this.onTelemetry(data);
          }
          // Check for crisis
          if (data.crisis_detected && this.onCrisisAlert) {
            this.onCrisisAlert(data.crisis_agents);
          }
          break;

        case "trust_scores":
          this.latestTrustScores = data;
          if (this.onTelemetry) {
            this.onTelemetry({
              action: "trust_scores",
              agents: data.agents,
              average: data.average,
            });
          }
          break;

        case "task_update":
          if (this.onTaskUpdate) {
            this.onTaskUpdate(data);
          }
          break;

        default:
          console.log("📨 WebSocket message:", data.action);
      }
    } catch (err) {
      console.error("❌ Error parsing WebSocket message:", err);
    }
  }

  onError(event) {
    console.error("❌ WebSocket error:", event);
    if (this.onConnectionChange) {
      this.onConnectionChange("error", false);
    }
  }

  onClose() {
    console.warn("⚠️ WebSocket disconnected");
    this.authenticated = false;

    if (this.onConnectionChange) {
      this.onConnectionChange("disconnected", false);
    }

    this.scheduleReconnect();
  }

  /**
   * Send message to WebSocket
   * @param {object} data - Message payload
   */
  send(data) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn("⚠️ WebSocket not connected, queueing message:", data);
      return false;
    }

    this.ws.send(JSON.stringify(data));
    return true;
  }

  /**
   * Request specific data
   * @param {string} action - Action (get_status, get_ebdi, get_trust_scores)
   */
  request(action) {
    return this.send({
      action: action,
      timestamp: new Date().toISOString(),
    });
  }

  /**
   * Disconnect WebSocket
   */
  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.authenticated = false;
  }

  /**
   * Schedule reconnect with exponential backoff
   */
  scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error("❌ Max reconnect attempts reached");
      return;
    }

    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts);
    console.log(
      `⏳ Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})`,
    );

    setTimeout(() => {
      const token = localStorage.getItem("token");
      if (token) {
        this.reconnectAttempts++;
        this.connect(token);
      }
    }, delay);
  }

  /**
   * Check if connected
   */
  isConnected() {
    return (
      this.ws && this.ws.readyState === WebSocket.OPEN && this.authenticated
    );
  }

  /**
   * Get latest telemetry (cached)
   */
  getTelemetry() {
    return this.latestTelemetry;
  }

  /**
   * Get latest trust scores (cached)
   */
  getTrustScores() {
    return this.latestTrustScores;
  }
}

// Global instance
let wsClient = null;

function getWebSocketClient() {
  if (!wsClient) {
    wsClient = new UAP_WebSocketClient(
      "http://localhost:8002",
      "ws://localhost:8004",
    );
  }
  return wsClient;
}

// Export for use in app.js
if (typeof module !== "undefined" && module.exports) {
  module.exports = { UAP_WebSocketClient, getWebSocketClient };
}
