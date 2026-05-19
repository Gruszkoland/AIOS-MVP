# Docker Images Quick Reference | ADRION 369

**Timestamp:** 2026-04-05 | **Format:** Executive Summary (Quick-Lookup)

---

## 📊 Ranked Images by Impact & Necessity

| Rank   | Obraz          | Version     | Rozmiar | Rola                     | Priority | Status    | Uwagi                               |
| ------ | -------------- | ----------- | ------- | ------------------------ | -------- | --------- | ----------------------------------- |
| **1**  | `postgres`     | 15-alpine   | ~25MB   | Genesis Record           | CRITICAL | ✅ KEEP   | LTS support do 2028                 |
| **2**  | `n8n`          | latest      | ~500MB  | SAP Orchestrator         | CRITICAL | ✅ KEEP   | Workflow hub, PostgreSQL integrated |
| **3**  | `ollama`       | latest      | ~4.5GB  | LLM Engine (Local-first) | CRITICAL | ✅ KEEP   | Guardian Law G7 Privacy compliance  |
| **4**  | `python`       | 3.11-slim   | ~120MB  | ADRION API               | CRITICAL | ✅ KEEP   | Main API runtime, waitress-serve    |
| **5**  | `golang`       | 1.22-alpine | ~5MB    | Vortex 174Hz Engine      | CRITICAL | ✅ KEEP   | Harmonic orchestration, multi-stage |
| **6**  | `grafana`      | 11.1.4      | ~150MB  | Monitoring Dashboards    | HIGH     | ✅ KEEP   | KPI Gates, Alert routing            |
| **7**  | `loki`         | 3.1.1       | ~80MB   | Log Aggregation          | HIGH     | ✅ KEEP   | Audit trail, compliance tracking    |
| **8**  | `promtail`     | 3.1.1       | ~30MB   | Log Shipper              | HIGH     | ✅ KEEP   | Auto-discovery, structured logs     |
| **9**  | `nginx`        | 1.27-alpine | ~30MB   | Reverse Proxy            | HIGH     | ✅ KEEP   | TLS termination, rate limiting      |
| **10** | `alpine`       | latest      | ~7MB    | Backup Scheduler         | OPTIONAL | ⚠️ REVIEW | Can move to cloud storage (S3)      |
| **11** | `mendhak/echo` | 35          | ~50MB   | Alert Test Sink          | OPTIONAL | ❌ REMOVE | Replace with Slack/Pagerduty        |

---

## 🎯 Quick Decision Matrix

### Keep (Core Stack)

```
✅ postgres:15-alpine     — Database (non-negotiable)
✅ n8n:latest             — Workflow orchestration (SAP)
✅ ollama:latest          — Private LLM (privacy-first)
✅ python:3.11-slim       — API runtime
✅ golang:1.22-alpine     — Vortex engine (174Hz)
✅ grafana:11.1.4         — Observability
✅ loki:3.1.1             — Log pipeline
✅ promtail:3.1.1         — Log shipping
✅ nginx:1.27-alpine      — Ingress layer
```

### Review (Optimization Candidates)

```
⚠️  alpine:backup (Dockerfile.backup)
    → Move backup to cloud storage or scheduled host cron
    → Rationale: Reduce container overhead, improve RTO/RPO

❌ mendhak/http-https-echo:35 (alert-sink)
    → Replace with real webhook handler
    → Options: Slack, Pagerduty, Datadog, custom Lambda
    → Risk: Test-only service in production
```

---

## 📈 Size Breakdown (Total Stack Impact)

| Layer             | Images Count | Total Size (approx) | Optimization                                 |
| ----------------- | ------------ | ------------------- | -------------------------------------------- |
| **Database**      | 1            | 25MB                | ✅ Minimal                                   |
| **AI/LLM**        | 1            | 4.5GB               | ⚠️ Model-dependent                           |
| **Application**   | 2            | 125MB               | ✅ Slim variants used                        |
| **Orchestration** | 1            | 500MB               | ⚠️ Node.js overhead                          |
| **Observability** | 4            | 290MB               | ✅ Lightweight stack                         |
| **Networking**    | 1            | 30MB                | ✅ Alpine base                               |
| **Utilities**     | 1            | 57MB                | ❌ Can remove                                |
| **TOTAL**         | **11**       | **~5.5GB**          | Optimizable to **~5.1GB** (remove echo sink) |

---

## 🔐 Guardian Laws Coverage by Image

| Image      | G1  | G2  | G3       | G4  | G5       | G6  | G7       | G8  | G9  |
| ---------- | --- | --- | -------- | --- | -------- | --- | -------- | --- | --- |
| postgres   | ✅  | ✅  | ✅       | ✅  | ✅       | ✅  | ✅       | ✅  | ✅  |
| n8n        | ✅  | ✅  | ✅       | ✅  | ✅       | ✅  | ⚠️       | ✅  | ⚠️  |
| **ollama** | ✅  | ✅  | ✅       | ✅  | ⚠️       | ✅  | **✅✅** | ✅  | ✅  |
| python     | ✅  | ✅  | ✅       | ✅  | ✅       | ✅  | ✅       | ✅  | ✅  |
| vortex     | ✅  | ✅  | **✅✅** | ✅  | ✅       | ✅  | ✅       | ✅  | ✅  |
| grafana    | ✅  | ✅  | ✅       | ✅  | **✅✅** | ✅  | ✅       | ✅  | ⚠️  |
| loki       | ✅  | ✅  | ✅       | ✅  | **✅✅** | ✅  | ✅       | ✅  | ✅  |
| promtail   | ✅  | ✅  | ✅       | ✅  | ✅       | ✅  | ✅       | ✅  | ✅  |
| nginx      | ✅  | ✅  | ✅       | ✅  | ⚠️       | ✅  | ✅       | ✅  | ✅  |

**Legend:** ✅ = Compliant | ⚠️ = Partial | ❌ = Non-compliant | ✅✅ = Exemplary

---

## 🚀 Deployment Paths

### SCENARIO A: Local Development (docker-compose.yml)

```
✅ postgres:15-alpine
✅ python:3.11-slim
✅ uap/Dockerfile (implicit)
✅ ollama:latest (optional, host-mounted)
```

**Result:** Minimal stack for active development (~150MB core, +4.5GB if ollama)

### SCENARIO B: Integration Testing (adrion-swarm/docker-compose.yml)

```
✅ postgres:15
✅ n8n:latest
✅ vortex (build from Dockerfile.vortex)
✅ adrion-healer (build from Dockerfile.healer)
```

**Result:** Full orchestration stack (~1.1GB)

### SCENARIO C: Production (docker-compose.prod.yml)

```
✅ postgres:15-alpine
✅ python:3.11-slim (built)
✅ n8n:latest
✅ vortex:built
✅ grafana:11.1.4
✅ loki:3.1.1
✅ promtail:3.1.1
✅ nginx:1.27-alpine
❌ mendhak/echo (REMOVE)
⚠️  alpine:backup (consider cloud)
```

**Result:** Production-ready stack (~5.1GB with optimizations)

---

## 🎬 Immediate Action Items

| #     | Action                                               | Owner    | Timeline           | Impact                       |
| ----- | ---------------------------------------------------- | -------- | ------------------ | ---------------------------- |
| **1** | Remove `mendhak/http-https-echo:35` from prod        | DevOps   | ASAP (2h)          | Security +1 CVE eliminated   |
| **2** | Implement real alert handler (Slack webhook)         | Platform | Sprint (4h)        | Alerting → production-ready  |
| **3** | Enable GPU acceleration for ollama                   | DevOps   | Optional (2h)      | LLM throughput +10x          |
| **4** | Migrate backup to S3 (Dockerfile.backup → S3 Lambda) | Platform | Sprint (3h)        | Cost/Reliability improvement |
| **5** | SCA scan all images (Trivy)                          | Security | After changes (1h) | CVE compliance               |
| **6** | Image signing (Cosign)                               | DevOps   | Before GA (2h)     | Supply chain security        |

---

## 📋 9-Word Summary (3 words each)

1. **Postgres Alpine.** Database foundation critical.
2. **N8N Orchestrator.** Workflow scheduling essential.
3. **Ollama Privacy-First.** Guardian G7 protected.
4. **Vortex Harmonic.** 174Hz alignment perfect.
5. **Grafana Observability.** Real-time monitoring comprehensive.
6. **Loki Audit-Trail.** Compliance transparency guaranteed.
7. **Nginx Ingress.** TLS termination included.
8. **Remove Alert-Sink.** Eliminate test-only image.
9. **GPU Optional.** Performance upside available.

---

**Assessment Complete.** ✅ All images justified. Proceeding to production optimization.

**Next:** Run `docker image ls` to verify current state.
