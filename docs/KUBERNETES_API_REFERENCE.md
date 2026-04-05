# Kubernetes API Endpoints — UAP Integration

**API Base URL:** `http://localhost:8002`
**Namespace:** `adrion-369`
**Version:** 1.0
**Last Updated:** 2026-04-06

---

## Authentication

All endpoints require **API Key** authentication:

```http
GET /mapi/v1/kubernetes/cluster-info HTTP/1.1
Host: localhost:8002
X-API-Key: YOUR_API_KEY
```

**Response if API Key is missing/invalid:**

```json
{
  "error": "Unauthorized"
}
```

Status: `401 Unauthorized`

---

## Endpoints Reference

### 1. GET /mapi/v1/kubernetes/cluster-info

**Purpose:** Get Kubernetes cluster information and health status

**Request:**

```http
GET /mapi/v1/kubernetes/cluster-info HTTP/1.1
X-API-Key: YOUR_API_KEY
```

**Response (Success):**

```json
{
  "status": "success",
  "cluster": {
    "status": "connected",
    "cluster_info": "Kubernetes master is running at https://...",
    "nodes": 1,
    "timestamp": "2026-04-06T17:30:00Z"
  },
  "queried_at": "2026-04-06T17:30:00Z"
}
```

**Response (K8s unavailable):**

```json
{
  "error": "Kubernetes integration not available"
}
```

Status: `503 Service Unavailable`

**Status Code:** `200 OK` (success) | `503 Service Unavailable` | `401 Unauthorized`

---

### 2. GET /mapi/v1/kubernetes/pods

**Purpose:** Get pod status listing in the ADRION namespace

**Request:**

```http
GET /mapi/v1/kubernetes/pods HTTP/1.1
X-API-Key: YOUR_API_KEY
```

**Query Parameters:**

- None (uses default namespace: `adrion-369`)

**Response (Success):**

```json
{
  "status": "success",
  "pods": {
    "total_pods": 14,
    "running": 7,
    "pending": 7,
    "failed": 0,
    "pods": [
      {
        "name": "api-0",
        "status": "Running",
        "ip": "10.1.0.26",
        "created": "2026-04-05T10:00:00Z",
        "ready": true
      },
      {
        "name": "postgres-0",
        "status": "Pending",
        "ip": "N/A",
        "created": "2026-04-05T10:00:00Z",
        "ready": false
      }
    ]
  },
  "namespace": "adrion-369",
  "queried_at": "2026-04-06T17:30:00Z"
}
```

**Status Code:** `200 OK` | `503 Service Unavailable` | `401 Unauthorized`

---

### 3. GET /mapi/v1/kubernetes/services

**Purpose:** Get service discovery information for ADRION namespace

**Request:**

```http
GET /mapi/v1/kubernetes/services HTTP/1.1
X-API-Key: YOUR_API_KEY
```

**Response (Success):**

```json
{
  "status": "success",
  "services": {
    "count": 10,
    "services": [
      {
        "name": "api",
        "type": "ClusterIP",
        "cluster_ip": "10.96.50.123",
        "external_ip": "N/A",
        "ports": ["8001:8001", "8002:8002"],
        "selector": { "app": "api" },
        "created": "2026-04-05T10:00:00Z"
      },
      {
        "name": "nginx",
        "type": "LoadBalancer",
        "cluster_ip": "10.96.50.124",
        "external_ip": "localhost",
        "ports": ["80:80", "443:443"],
        "selector": { "app": "nginx" },
        "created": "2026-04-05T10:00:00Z"
      }
    ]
  },
  "namespace": "adrion-369",
  "queried_at": "2026-04-06T17:30:00Z"
}
```

**Status Code:** `200 OK` | `503 Service Unavailable` | `401 Unauthorized`

---

### 4. GET /mapi/v1/kubernetes/deployments

**Purpose:** Get deployment status and replica information

**Request:**

```http
GET /mapi/v1/kubernetes/deployments HTTP/1.1
X-API-Key: YOUR_API_KEY
```

**Response (Success):**

```json
{
  "status": "success",
  "deployments": {
    "count": 9,
    "deployments": [
      {
        "name": "api",
        "replicas": 2,
        "ready": 2,
        "updated": 2,
        "available": 2,
        "image": "adrion-api:latest",
        "created": "2026-04-05T10:00:00Z"
      },
      {
        "name": "vortex",
        "replicas": 1,
        "ready": 1,
        "updated": 1,
        "available": 1,
        "image": "adrion-vortex:latest",
        "created": "2026-04-05T10:00:00Z"
      }
    ]
  },
  "namespace": "adrion-369",
  "queried_at": "2026-04-06T17:30:00Z"
}
```

**Status Code:** `200 OK` | `503 Service Unavailable` | `401 Unauthorized`

---

### 5. GET /mapi/v1/kubernetes/pod/{pod_name}/logs

**Purpose:** Retrieve logs from a specific pod

**Request:**

```http
GET /mapi/v1/kubernetes/pod/api-0/logs?lines=50 HTTP/1.1
X-API-Key: YOUR_API_KEY
```

**Query Parameters:**

- `lines` (optional, default: 50): Number of log lines to retrieve
- `namespace` (optional, default: `adrion-369`): Namespace containing the pod

**Response (Success):**

```json
{
  "status": "success",
  "pod_name": "api-0",
  "namespace": "adrion-369",
  "logs": "2026-04-06T17:00:00 [INFO] Starting API server...\n2026-04-06T17:00:01 [INFO] Listening on port 8001\n...",
  "queried_at": "2026-04-06T17:30:00Z"
}
```

**Response (Pod not found):**

```json
{
  "error": "Pod 'api-0' not found in namespace 'adrion-369'"
}
```

Status: `404 Not Found`

**Status Code:** `200 OK` | `404 Not Found` | `503 Service Unavailable` | `401 Unauthorized`

---

### 6. POST /mapi/v1/kubernetes/pod/{pod_name}/restart

**Purpose:** Restart a pod (critical operation - logs to Genesis Record)

**Warning:** This is a **destructive operation** that deletes and recreates the pod. Use with caution.

**Request:**

```http
POST /mapi/v1/kubernetes/pod/postgres-0/restart HTTP/1.1
X-API-Key: YOUR_API_KEY
Content-Type: application/json
```

**Query Parameters:**

- `namespace` (optional, default: `adrion-369`): Namespace containing the pod

**Request Body:** (empty)

**Response (Success):**

```json
{
  "status": "success",
  "pod_name": "postgres-0",
  "namespace": "adrion-369",
  "action": "restart",
  "result": "Pod restarting",
  "executed_at": "2026-04-06T17:30:00Z"
}
```

**Genesis Record Entry:**

```
task_id: "pod-restart-1712425800.123"
agent: "Sentinel"
status: "completed"
action: "kubernetes_pod_restart"
guards_passed: 9
notes: "Pod postgres-0 forcefully restarted in namespace adrion-369"
```

**Response (Pod not found):**

```json
{
  "error": "Pod 'nonexistent' not found in namespace 'adrion-369'"
}
```

Status: `404 Not Found`

**Status Code:** `200 OK` | `404 Not Found` | `503 Service Unavailable` | `401 Unauthorized`

---

### 7. GET /mapi/v1/kubernetes/metrics

**Purpose:** Query Prometheus metrics for Kubernetes cluster

**Request:**

```http
GET /mapi/v1/kubernetes/metrics?metric=cluster_health HTTP/1.1
X-API-Key: YOUR_API_KEY
```

**Query Parameters:**

- `metric` (optional, default: `cluster_health`): Metric to query
  - `cluster_health`: Overall cluster health status
  - `pod_count`: Number of pods in ADRION namespace
  - `cpu_usage`: CPU usage rate
  - `memory_usage`: Memory usage in MB

**Response (Success):**

```json
{
  "status": "success",
  "metric": "cluster_health",
  "data": {
    "status": "success",
    "data": {
      "resultType": "vector",
      "result": [
        {
          "metric": { "job": "kubernetes-cluster" },
          "value": [1712425800, "1"]
        }
      ]
    }
  },
  "queried_at": "2026-04-06T17:30:00Z"
}
```

**Response (Prometheus unavailable):**

```json
{
  "error": "Prometheus connection failed"
}
```

Status: `503 Service Unavailable`

**Status Code:** `200 OK` | `503 Service Unavailable` | `401 Unauthorized`

---

### 8. GET /mapi/v1/kubernetes/events

**Purpose:** Get recent cluster events in ADRION namespace

**Request:**

```http
GET /mapi/v1/kubernetes/events HTTP/1.1
X-API-Key: YOUR_API_KEY
```

**Response (Success):**

```json
{
  "status": "success",
  "events": {
    "count": 5,
    "events": [
      {
        "type": "Normal",
        "reason": "Started",
        "message": "Started container api",
        "object": "api-0",
        "timestamp": "2026-04-05T10:00:05Z"
      },
      {
        "type": "Warning",
        "reason": "BackOff",
        "message": "Back-off pulling image",
        "object": "postgres-0",
        "timestamp": "2026-04-05T10:01:00Z"
      }
    ]
  },
  "namespace": "adrion-369",
  "queried_at": "2026-04-06T17:30:00Z"
}
```

**Status Code:** `200 OK` | `503 Service Unavailable` | `401 Unauthorized`

---

## Error Responses

### 401 Unauthorized

```json
{
  "error": "Unauthorized"
}
```

### 404 Not Found

```json
{
  "error": "Pod 'pod_name' not found in namespace 'adrion-369'"
}
```

### 503 Service Unavailable

```json
{
  "error": "Kubernetes integration not available"
}
```

### 500 Internal Server Error

```json
{
  "error": "Failed to connect to kubectl: kubectl not found"
}
```

---

## Examples

### Example 1: Check cluster health

```bash
curl -X GET "http://localhost:8002/mapi/v1/kubernetes/cluster-info" \
  -H "X-API-Key: your-secret-key"
```

### Example 2: Get all pods

```bash
curl -X GET "http://localhost:8002/mapi/v1/kubernetes/pods" \
  -H "X-API-Key: your-secret-key" \
  | python3 -m json.tool
```

### Example 3: Get pod logs

```bash
curl -X GET "http://localhost:8002/mapi/v1/kubernetes/pod/api-0/logs?lines=100" \
  -H "X-API-Key: your-secret-key"
```

### Example 4: Restart a pod (CAUTION!)

```bash
curl -X POST "http://localhost:8002/mapi/v1/kubernetes/pod/postgres-0/restart" \
  -H "X-API-Key: your-secret-key" \
  -H "Content-Type: application/json"
```

### Example 5: Query metrics

```bash
curl -X GET "http://localhost:8002/mapi/v1/kubernetes/metrics?metric=cpu_usage" \
  -H "X-API-Key: your-secret-key"
```

### Example 6: Get cluster events

```bash
curl -X GET "http://localhost:8002/mapi/v1/kubernetes/events" \
  -H "X-API-Key: your-secret-key" \
  | python3 -m json.tool
```

---

## Rate Limiting

Currently, no rate limiting is enforced. Future versions may implement:

- Per-API-key rate limits (e.g., 100 requests/minute)
- Endpoint-specific limits (e.g., restart pod max 1/minute)

---

## Genesis Record Logging

All operations are logged to Genesis Record for audit trail:

- **Cluster Info Queries:** Logged as `action: kubernetes_cluster_info_queried`
- **Pod Logs Retrieval:** Logged as `action: kubernetes_pod_logs_retrieved`
- **Pod Restart:** Logged as `action: kubernetes_pod_restart` with agent `Sentinel`
- **Metric Queries:** Logged as `action: kubernetes_metrics_query`

---

## Dependencies

### Required

- `kubectl`: Command-line tool configured to access the Kubernetes cluster
- Kubernetes cluster must be accessible and properly configured
- `KUBECONFIG` environment variable set or `~/.kube/config` file present

### Optional

- **Prometheus:** For metrics endpoint (if not available, metrics queries return empty result)
- **Loki:** For advanced logging (currently not integrated)

---

## Troubleshooting

### "Kubernetes integration not available" (503)

**Solution:**

- Ensure `kubectl` is installed and available in PATH
- Run `kubectl cluster-info` to verify cluster access
- Check `KUBECONFIG` environment variable
- Verify Docker Desktop Kubernetes is running

### "Pod not found" (404)

**Solution:**

- Pod may not exist or may be in a different namespace
- Use `GET /mapi/v1/kubernetes/pods` to list all pods
- Verify namespace parameter (default: `adrion-369`)

### "API Key: Unauthorized" (401)

**Solution:**

- Ensure `X-API-Key` header is included
- Verify API key value is correct
- Check `UAP_API_KEY` environment variable is set

---

## Future Enhancements

- [ ] WebSocket support for real-time pod status
- [ ] Pod metrics (CPU, Memory per pod)
- [ ] Advanced filtering (by label, status)
- [ ] Bulk pod restart operations
- [ ] Pod exec support (run commands in pods)
- [ ] Namespace switching support
- [ ] StorageClass and PVC monitoring

---

## API Versioning

**Current Version:** `v1`
**Stability:** Beta
**Last Breaking Change:** Never

Future API changes will be versioned under `/mapi/v2/`, `/mapi/v3/` etc.

---

**API Documentation Generated:** 2026-04-06
**Status:** 🔄 Active Development
