# Kubernetes Monitoring & Observability Setup Guide

**Date:** 2026-04-06  
**Status:** Monitoring Configuration Active  
**Cluster:** adrion-369 (docker-desktop)

---

## QUICK START

### 1. Setup Port Forwards (5 minutes)

```bash
# Run this batch file to open all port-forwards
.\kubernetes\setup-portforwards.bat
```

This opens separate terminal windows for:

- ✅ API Gateway (8001)
- ✅ Grafana (3000)
- ✅ Prometheus (9090)
- ✅ Loki (3100)
- ✅ N8N (5678)
- ✅ Ollama (11434)

### 2. Access Grafana Dashboard

```
URL: http://localhost:3000
Username: admin
Password: admin
```

### 3. Configure Data Sources (Optional - Automated)

```bash
# Activate Python venv
.\.venv\Scripts\Activate.ps1

# Run Grafana setup script
python kubernetes/setup-grafana.py
```

---

## CURRENT POD STATUS

### Running (7/14 - 50% Ready)

- ✅ **alert-handler** (10.1.0.28): Active, monitoring
- ✅ **api** × 2 replicas (10.1.0.26-27): API endpoints operational
- ✅ **healer** (10.1.0.25): Self-healing agent ready
- ✅ **nginx** × 2 replicas (10.1.0.29-30): Ingress/LoadBalancer active
- ✅ **vortex** (10.1.0.24): Orchestration engine ready

### Initializing (7/14 - Expected)

- ⏳ **postgres-0**: First boot initialization (5-15 min typical)
- ⏳ **ollama**: Pulling 2.8GB model (~5-10 min)
- ⏳ **grafana**: Image pull + startup
- ⏳ **prometheus**: Awaiting postgres readiness
- ⏳ **loki**: Image pull + startup
- ⏳ **promtail**: Waiting for Loki readiness
- ⏳ **n8n**: Waiting for PostgreSQL readiness

---

## MONITORING SETUP

### Phase 1: Data Source Configuration

#### Prometheus

```
Name: Prometheus
Type: Prometheus
URL: http://localhost:9090
Access: Browser
Default: Yes
```

#### Loki

```
Name: Loki
Type: Loki
URL: http://localhost:3100
Access: Browser
```

### Phase 2: Dashboard Creation

**Recommended Dashboards:**

1. **System Health**
   - Pod status (Running/Pending)
   - CPU usage per container
   - Memory usage per container
   - Network I/O

2. **API Metrics**
   - Request rate (req/s)
   - Response time (p50, p95, p99)
   - Error rate (4xx, 5xx)
   - Active connections

3. **Database (PostgreSQL)**
   - Transaction rate
   - Query latency
   - Connection count
   - Replication lag (when HA enabled)

4. **Logs (Loki)**
   - Error logs by service
   - Warning logs count
   - Info logs timeline
   - Custom log queries

### Phase 3: Alert Configuration

**Key Alerts to Set:**

```
Alert: HighPodRestartCount
Condition: container_restart_count > 5 in 10 min
Severity: WARNING

Alert: DatabaseDown
Condition: up{job="postgres"} == 0
Severity: CRITICAL

Alert: HighErrorRate
Condition: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
Severity: WARNING

Alert: LowDiskSpace
Condition: (disk_free_bytes / disk_total_bytes) < 0.1
Severity: CRITICAL
```

---

## MONITORING COMMANDS

### Watch Pod Status

```bash
kubectl get pods -n adrion-369 -w
```

### Check Pod Readiness Details

```bash
kubectl describe pod <pod-name> -n adrion-369
```

### View Service Endpoints

```bash
kubectl get endpoints -n adrion-369
```

### Get Service DNS Names

```bash
kubectl get svc -n adrion-369 -o wide
# Format: <service-name>.adrion-369.svc.cluster.local
```

### Check Resource Usage

```bash
# Per node
kubectl top nodes

# Per pod
kubectl top pods -n adrion-369

# Per container
kubectl top pods -n adrion-369 --containers
```

### View Logs

```bash
# Real-time logs from pod
kubectl logs -f -n adrion-369 <pod-name>

# Last 100 lines
kubectl logs -n adrion-369 <pod-name> --tail=100

# All containers in pod (if multiple)
kubectl logs -f -n adrion-369 <pod-name> --all-containers=true

# Logs from previous crash (if pod restarted)
kubectl logs -n adrion-369 <pod-name> --previous
```

### Monitor Events

```bash
# All cluster events
kubectl get events -n adrion-369

# Watch events in real-time
kubectl get events -n adrion-369 -w --sort-by='.lastTimestamp'
```

---

## TROUBLESHOOTING

### Pod Stuck in Pending

**Check why:**

```bash
kubectl describe pod <pod-name> -n adrion-369
# Look for "Events" section
```

**Common causes:**

- **ImagePullBackOff**: Image too large, waiting to pull
- **Insufficient memory**: Docker Desktop needs more RAM
- **PVC not bound**: Storage issues
- **CrashLoopBackOff**: Application error

**Solution:**

```bash
# Increase Docker Desktop memory
# Settings → Resources → Increase "Memory" slider
```

### Service Not Accessible

**Check endpoints:**

```bash
kubectl get endpoints <service-name> -n adrion-369
# Should show pod IPs
```

**Check service selector:**

```bash
kubectl get svc <service-name> -n adrion-369 -o yaml
# Verify selector matches pod labels
```

### High Resource Usage

**Check node capacity:**

```bash
kubectl describe node docker-desktop
# Look for "Allocated resources"
```

**Check pod requests/limits:**

```bash
kubectl describe pod <pod-name> -n adrion-369
# Look for "Limits" and "Requests"
```

---

## MANUAL DATA SOURCE SETUP (if automated fails)

### Prometheus

1. Open Grafana: `http://localhost:3000`
2. Left menu → Configuration → Data Sources
3. Click "Add data source"
4. Select "Prometheus"
5. URL: `http://localhost:9090`
6. Click "Save & Test"

### Loki

1. Data Sources → Add data source
2. Select "Loki"
3. URL: `http://localhost:3100`
4. Click "Save & Test"

### Create Dashboard

1. Left menu → Dashboard → New Dashboard
2. Add panels → Select data source
3. Write PromQL queries for Prometheus
4. Write LogQL queries for Loki

---

## GRAFANA QUERIES

### PromQL Examples (Prometheus)

**API Request Rate:**

```promql
rate(http_requests_total[5m])
```

**Pod UP Status:**

```promql
up{kubernetes_namespace="adrion-369"}
```

**Container CPU Usage:**

```promql
rate(container_cpu_usage_seconds_total[1m])
```

**Memory Usage:**

```promql
container_memory_usage_bytes / 1024 / 1024
```

### LogQL Examples (Loki)

**Error Logs:**

```logql
{namespace="adrion-369"} |= "ERROR"
```

**Logs from Specific Pod:**

```logql
{pod_name="api-555cb8b884-cwgp9"}
```

**Rate of Errors:**

```logql
rate({namespace="adrion-369"} |= "ERROR" [5m])
```

---

## EXPECTED TIMELINE

| Time    | Event                           |
| ------- | ------------------------------- |
| Now     | 7/14 pods running, 7 pending    |
| +5 min  | Ollama image pull completes     |
| +10 min | PostgreSQL ready, N8N starts    |
| +15 min | Grafana, Prometheus, Loki ready |
| +20 min | Full deployment operational     |
| +25 min | All dashboards configured       |

---

## SERVICES READY FOR TESTING

| Service    | URL                    | Purpose               |
| ---------- | ---------------------- | --------------------- |
| API        | http://localhost:8001  | Application API       |
| Grafana    | http://localhost:3000  | Monitoring dashboards |
| Prometheus | http://localhost:9090  | Time-series metrics   |
| Loki       | http://localhost:3100  | Log aggregation       |
| N8N        | http://localhost:5678  | Workflow automation   |
| Ollama     | http://localhost:11434 | LLM inference         |

---

## MONITORING CHECKLIST

- [ ] All port-forwards started successfully
- [ ] Grafana login working (admin/admin)
- [ ] Prometheus data source added
- [ ] Loki data source added
- [ ] At least one dashboard created
- [ ] Pod status page accessed
- [ ] Logs viewing working
- [ ] Metrics visible in Prometheus
- [ ] All 7 running pods healthy
- [ ] Waiting pods not in CrashLoop

---

## NEXT PHASES

### Phase 1: Monitoring (Current)

- [x] Pod stabilization monitoring
- [x] Port-forward setup
- [ ] Grafana data sources
- [ ] Custom dashboards

### Phase 2: Integration Testing

- [ ] API health checks
- [ ] Database connectivity
- [ ] Service inter-communication
- [ ] End-to-end workflow tests

### Phase 3: Performance Tuning

- [ ] Load testing
- [ ] Resource optimization
- [ ] Query optimization
- [ ] Cache configuration

### Phase 4: Production Hardening

- [ ] TLS certificates
- [ ] Secret rotation
- [ ] Disaster recovery
- [ ] Multi-region setup

---

**Last Updated:** 2026-04-06 00:15 UTC  
**Status:** ✅ MONITORING READY  
**Next Review:** Check pod status in ~15 minutes

_Generated by ADRION 369 Master Orchestrator_
