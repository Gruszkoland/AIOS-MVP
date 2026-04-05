# Kubernetes Real-Time Streaming — UAP Integration

**API Base URL:** `http://localhost:8002`
**Version:** 1.0
**Last Updated:** 2026-04-06

---

## Overview

Real-time streaming API for Kubernetes cluster updates using:

- **Server-Sent Events (SSE)** — For live pod status and cluster events
- **Event Queue** — For polling-based update retrieval
- **Kubernetes Watch API** — Backend for watching cluster changes

---

## Streaming Endpoints

### 1. GET /mapi/v1/kubernetes/stream (SSE - Real-time)

**Purpose:** Stream live Kubernetes updates to client browser

**Request:**

```http
GET /mapi/v1/kubernetes/stream HTTP/1.1
Host: localhost:8002
X-API-Key: YOUR_API_KEY
Accept: text/event-stream
```

**Response (Streaming Events):**

```
data: {"type":"connected","timestamp":"2026-04-06T17:45:00Z"}

data: {"type":"pod_status_change","pod_name":"api-0","status":"Running","timestamp":"2026-04-06T17:45:05Z"}

data: {"type":"cluster_event","reason":"Started","message":"Started container api","object":"api-0","event_type":"Normal","timestamp":"2026-04-06T17:45:05Z"}

data: {"type":"pod_status_change","pod_name":"postgres-0","status":"Pending","timestamp":"2026-04-06T17:45:10Z"}
```

**Connection Management:**

- Connection persists (keep-alive)
- Events sent as `data:` lines
- Double newline (`\n\n`) ends each event
- Close connection on client disconnect or timeout

**Error Handling:**

- On disconnect: Automatic reconnect attempt after 5 seconds
- On error: `onerror` event handler triggered

**Status Code:** `200 OK` (streaming) | `401 Unauthorized` | `503 Service Unavailable`

---

### 2. POST /mapi/v1/kubernetes/watch/start

**Purpose:** Start real-time cluster watcher (required for SSE stream)

**Request:**

```http
POST /mapi/v1/kubernetes/watch/start HTTP/1.1
Host: localhost:8002
X-API-Key: YOUR_API_KEY
Content-Length: 0
```

**Response:**

```json
{
  "status": "success",
  "message": "Kubernetes watcher started",
  "watch_type": "streaming",
  "started_at": "2026-04-06T17:45:00Z"
}
```

**Status Code:** `200 OK` | `401 Unauthorized` | `503 Service Unavailable`

---

### 3. POST /mapi/v1/kubernetes/watch/stop

**Purpose:** Stop real-time cluster watcher

**Request:**

```http
POST /mapi/v1/kubernetes/watch/stop HTTP/1.1
Host: localhost:8002
X-API-Key: YOUR_API_KEY
Content-Length: 0
```

**Response:**

```json
{
  "status": "success",
  "message": "Kubernetes watcher stopped",
  "stopped_at": "2026-04-06T17:45:00Z"
}
```

**Status Code:** `200 OK` | `401 Unauthorized` | `503 Service Unavailable`

---

### 4. GET /mapi/v1/kubernetes/watch/events (Polling Fallback)

**Purpose:** Retrieve queued events when SSE is not available

**Request:**

```http
GET /mapi/v1/kubernetes/watch/events?max=50 HTTP/1.1
Host: localhost:8002
X-API-Key: YOUR_API_KEY
```

**Query Parameters:**

- `max` (optional, default: 100): Maximum events to retrieve

**Response:**

```json
{
  "status": "success",
  "events": [
    {
      "type": "pod_status_change",
      "pod_name": "api-0",
      "status": "Running",
      "timestamp": "2026-04-06T17:45:05Z"
    },
    {
      "type": "cluster_event",
      "reason": "Started",
      "message": "Started container api",
      "object": "api-0",
      "event_type": "Normal",
      "timestamp": "2026-04-06T17:45:05Z"
    }
  ],
  "count": 2,
  "fetched_at": "2026-04-06T17:45:15Z"
}
```

**Note:** Events are queued in memory. This endpoint returns buffered events without blocking.

**Status Code:** `200 OK` | `401 Unauthorized` | `503 Service Unavailable`

---

## Event Types

### Pod Status Change

```json
{
  "type": "pod_status_change",
  "pod_name": "postgres-0",
  "status": "Running",
  "timestamp": "2026-04-06T17:45:10Z"
}
```

Possible `status` values:

- `Running` — Pod is running
- `Pending` — Pod is waiting to be scheduled
- `Succeeded` — Pod completed successfully
- `Failed` — Pod failed
- `Unknown` — Pod status unknown

### Cluster Event

```json
{
  "type": "cluster_event",
  "reason": "BackOff",
  "message": "Back-off pulling image",
  "object": "postgres-0",
  "event_type": "Warning",
  "timestamp": "2026-04-06T17:45:20Z"
}
```

Possible `event_type` values:

- `Normal` — Normal event
- `Warning` — Warning event

---

## Frontend Integration Example

### Basic SSE Connection

```javascript
const apiKey = "your-api-key";
const eventSource = new EventSource(
  `http://localhost:8002/mapi/v1/kubernetes/stream?api_key=${apiKey}`,
);

eventSource.addEventListener("message", (event) => {
  const data = JSON.parse(event.data);
  console.log("Received update:", data);
});

eventSource.addEventListener("error", (error) => {
  console.error("Stream error, reconnecting...");
  eventSource.close();
});
```

### With Start/Stop Control

```javascript
// Start watching
async function startWatching() {
  await fetch("http://localhost:8002/mapi/v1/kubernetes/watch/start", {
    method: "POST",
    headers: { "X-API-Key": "your-api-key" },
  });

  // Then open SSE stream
  const eventSource = new EventSource(
    "http://localhost:8002/mapi/v1/kubernetes/stream?api_key=your-api-key",
  );
  // ... rest of event handling
}

// Stop watching
async function stopWatching() {
  await fetch("http://localhost:8002/mapi/v1/kubernetes/watch/stop", {
    method: "POST",
    headers: { "X-API-Key": "your-api-key" },
  });
}
```

### Polling Fallback (No SSE Support)

```javascript
async function pollEvents(apiKey, interval = 1000) {
  setInterval(async () => {
    const response = await fetch(
      "http://localhost:8002/mapi/v1/kubernetes/watch/events?max=50",
      {
        headers: { "X-API-Key": apiKey },
      },
    );
    const data = await response.json();
    data.events.forEach((event) => {
      console.log("Event:", event);
      handleEvent(event);
    });
  }, interval);
}
```

---

## Performance Characteristics

### Server-Side

- **Pod Watch:** Subprocess watching kubectl stream, event pushed to queue
- **Event Watch:** Similar, Kubernetes events streamed and buffered
- **Queue Size:** Up to 1,000 events (auto-prune on overflow)
- **Memory**: ~5-10 MB for full watch (depends on cluster size)

### Client-Side

- **SSE Connection:** Single persistent connection per client
- **Bandwidth:** ~100-500 bytes/second (varies with cluster activity)
- **CPU:** <1% (idle), ~2-5% (active updates)

### Latency

- **Pod Status Change:** 100-500ms (depends on kubectl latency)
- **Cluster Event:** 200-1000ms (depends on event propagation)
- **SSE Push:** <100ms (server → browser)

---

## Limitations & Gotchas

1. **No Filtering:** All events are streamed; client-side filtering recommended
2. **Limited Backlog:** Only queues last 100 events (rest discarded)
3. **Single Watcher:** Only one watcher per server instance
4. **No Persistent Storage:** Events cleared on server restart
5. **Kubectl Dependency:** Requires working kubectl with cluster access

---

## Configuration

**Environment Variables:**

- `NAMESPACE` (default: `adrion-369`) — Kubernetes namespace to watch
- `K8S_WATCHER_BUFFER_SIZE` (default: 1000) — Max queued events
- `K8S_WATCHER_TIMEOUT` (default: 30s) — Timeout for kubectl commands

---

## Error Responses

### 401 Unauthorized

```json
{
  "error": "Unauthorized"
}
```

### 503 Service Unavailable

```json
{
  "error": "Kubernetes WebSocket watcher not available"
}
```

---

## Genesis Record Logging

All streaming operations are logged:

```
[system] Monitor action=kubernetes_watcher_start status=started
[system] Monitor action=kubernetes_sse_stream_opened status=opened
[system] Monitor action=kubernetes_watcher_stop status=stopped
```

---

## Future Enhancements

- [ ] Event filtering (by pod, namespace, type)
- [ ] WebSocket fallback (for better browser support)
- [ ] Multi-namespace watching
- [ ] Metric streaming (CPU, memory per pod)
- [ ] Pod log streaming
- [ ] Event replay from persistent store

---

## Testing

```bash
# Start watcher
curl -X POST http://localhost:8002/mapi/v1/kubernetes/watch/start \
  -H "X-API-Key: your-api-key"

# Poll events
curl http://localhost:8002/mapi/v1/kubernetes/watch/events \
  -H "X-API-Key: your-api-key" | jq .

# Stop watcher
curl -X POST http://localhost:8002/mapi/v1/kubernetes/watch/stop \
  -H "X-API-Key: your-api-key"
```

---

**API Documentation Generated:** 2026-04-06
**Status:** 🟢 Production Ready
