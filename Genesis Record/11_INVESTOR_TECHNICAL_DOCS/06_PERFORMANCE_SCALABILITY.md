# 06 — Performance & Scalability: ADRION 369

**Dla kogo:** CTO, DevOps, architekci infrastruktury
**Data:** 2026-04-05 | **Wersja:** v1.0.0

---

## Obecne SLA i benchmarki

### API Performance (BaseHTTPRequestHandler)

| Endpoint | Typ | Obecna latency (est.) | Target (FastAPI) |
|----------|-----|----------------------|-----------------|
| `GET /api/status` | Sync | <50ms | <20ms |
| `POST /api/scout` | Sync + Apify | 2-5s | 2-5s (I/O bound) |
| `POST /api/cycle` | Full pipeline | 5-30s | 5-30s (LLM bound) |
| `POST /api/quantum/decide` | Trinity+Guardian | 500ms-2s | <500ms |
| `GET /api/kpis` | DB query | <200ms | <50ms |

**Bottlenecks identyfikowane przez ATAM:**
1. Ollama cold start: 10-60s (jednorazowo at boot)
2. Synchronous handler: brak concurrent processing
3. Trinity SIMULACJA: po rzeczywistej implementacji = +200-500ms latency

---

## Limity i progi systemu

### Rate limits (obecne)

```
quantum/decide:    30 req/min  → 1 req/2s avg
scout:             10 req/min  → 1 req/6s avg
cycle:             5  req/min  → 1 req/12s avg
oracle/predict:    20 req/min  → 1 req/3s avg
mass-generate:     3  req/min  → 1 req/20s avg
```

### Database limits

```
PostgreSQL connection pool: min=2, max=10
  → Bottleneck przy >10 concurrent requests
  → Mitygacja: monitoring + alerting Prometheus

Redis: single-node (6379)
  → SPOF — mitygacja Q2: Redis Sentinel
```

---

## Pojemność (Capacity Planning)

### Scenariusz: 1 instancja lokalna (obecny stan)

```
Hardware: i7-12gen + RTX 3080 (10GB VRAM) + 32GB RAM
OS: Windows 10 Pro

Theoretical throughput:
  Scout operations:        ~600/hour (rate limited)
  Full arbitrage cycles:   ~300/hour
  Guardian validations:    ~1800/hour
  Concurrent connections:  max 10 (DB pool)

Daily capacity:
  Lead evaluations:        ~14,000/day
  APPROVED decisions est:  ~4,200/day (30% rate)
```

### Scenariusz: VPS (planowany)

```
Hardware: 4 vCPU + 16GB RAM + A2000 GPU (opcjonalnie)
OS: Ubuntu 22.04 LTS + Docker

Theoretical throughput po FastAPI migracji:
  Concurrent workers:      4 (uvicorn workers)
  Scout operations:        ~2400/hour
  Full cycles:             ~1200/hour
  95th percentile latency: <200ms (bez LLM)
```

### Scenariusz: K8s horizontal scaling (Faza 4)

```
Kubernetes: GKE/EKS
  adrion-api pods:     3-10 (HPA based on CPU)
  postgres:            1 (StatefulSet + PVC)
  redis:               3 (Sentinel HA)
  ollama:              1-2 (GPU node)

Target throughput:
  10,000+ req/hour
  <100ms P95 (non-LLM endpoints)
  99.5% availability SLA
```

---

## Monitoring stack

### Aktywne metryki (Prometheus)

| Metrika | Endpoint | Opis |
|---------|----------|------|
| `adrion_decisions_total` | `/metrics` | Licznik APPROVED/DENIED |
| `adrion_scout_jobs_total` | `/metrics` | Leads znalezione |
| `adrion_cycle_latency` | `/metrics` | Czas pełnego cyklu |
| `adrion_guardian_violations` | `/metrics` | Naruszenia per prawo |
| `db_pool_active` | `/metrics` | Aktywne DB connections |
| `circuit_breaker_state` | `/metrics` | CLOSED/OPEN per breaker |

### Aktywne dashboardy (Grafana)

- ADRION Overview (decyzje, latency, error rate)
- Arbitraż Pipeline (scout → analyze → bid conversion)
- Guardian Laws (heatmap naruszeń)
- Infrastructure (CPU, RAM, VRAM, disk I/O)
- Database (query time, pool utilization)

### Alerty (Prometheus Alertmanager, planowane)

```yaml
- alert: HighDecisionLatency
  expr: adrion_cycle_latency_p95 > 30s

- alert: CircuitBreakerOpen
  expr: circuit_breaker_state == 2  # OPEN

- alert: DBPoolExhausted
  expr: db_pool_active >= 9  # near max=10

- alert: LowApprovalRate
  expr: rate(adrion_decisions_total{status="APPROVED"}[1h]) < 0.2
```

---

## Testy wydajności (Benchmarks przeprowadzone)

### Test suite: 463 testów w 51.81s

```
Średni czas per test: 112ms
Najszybsze:           <1ms  (unit testy)
Najwolniejsze:        ~2s   (integration test z HTTPServer)
Parallel execution:   Nie (kolejny krok optymalizacji)
```

### BaseHTTPRequestHandler stress test (lokalne obserwacje)

```
Concurrency: 1 (synchronous)
Rate limit test: 429 zwracany poprawnie
Windows TCP RST: obsługiwany przez _rate_lim_post()
Connection reuse: nie (new conn per request)
```

---

## Roadmap wydajnościowy

| Krok | Zysk | Priorytet |
|------|------|-----------|
| Ollama model preload | Eliminacja 10-60s cold start | P1 (tydzień) |
| pytest-xdist parallel | Test suite: 51s → ~15s | P2 (tydzień) |
| FastAPI migration | Async + concurrent requests | P2 (miesiąc) |
| Connection pool tuning | ThreadedConnectionPool(5, 20) | P1 (3 dni) |
| Redis Sentinel | Eliminacja SPOF | P1 (miesiąc) |
| K8s HPA | Auto-scaling powyżej 1000 RPH | P2 (kwartał) |

---

*ADRION 369 v1.0.0 — Genesis Record 2026-04-05*
