# 03 — Product Roadmap: ADRION 369

**Dla kogo:** Inwestorzy, Product Managers, stakeholders
**Data:** 2026-04-05 | **Wersja:** v1.0.0

---

## Status bramek (Milestones overview)

```
M1 Wymagania        ████████████████████ 100% ✅
M2 Architektura     ████████████████████ 100% ✅
M3 Dane / ML Core   ████████░░░░░░░░░░░░  40% ⚠️
M4 Skalowalność     ████████████░░░░░░░░  60% ⚠️
M5 CI/CD Quality    ████████████████████ 100% ✅ (67% coverage)
M6 Produkcja K8s    ░░░░░░░░░░░░░░░░░░░░   0% 🔜
```

---

## FAZA 1 — UKOŃCZONE (do 2026-04-05)

### Infrastruktura i jakość (M1, M2, M5) ✅

| Zadanie | Status | Data |
|---------|--------|------|
| Docker Compose: 8 serwisów | ✅ | 2026-04-01 |
| PostgreSQL schema + migracje | ✅ | 2026-04-01 |
| Redis AI-Binder IPC | ✅ | 2026-04-01 |
| Prometheus + Grafana monitoring | ✅ | 2026-04-04 |
| CI/CD GitHub Actions | ✅ | 2026-04-04 |
| Coverage gate 65% | ✅ | 2026-04-05 |
| 463 testów PASS, 0 lint errors | ✅ | 2026-04-05 |
| Rate limiter + Circuit breaker | ✅ | 2026-04-03 |
| Stripe payment integration | ✅ | 2026-04-03 |
| Apify/Upwork scout integration | ✅ | 2026-04-03 |
| ATAM Analysis + 5 ADRs | ✅ | 2026-04-05 |
| Investor Technical Docs | ✅ | 2026-04-05 |

---

## FAZA 2 — AKTYWNA (2026-04 → 2026-05)

### Priorytet P0: Core ML implementation (M3)

| Zadanie | Opis | Estymacja |
|---------|------|-----------|
| **Trinity real scoring** | Zastąpienie SIMULACJI prawdziwym ML (resource assessment via psutil, logical reasoning via Ollama, alignment scoring) | 2 tygodnie |
| **PostgreSQL insert w app.py** | Rzeczywisty Genesis Record write (nie mock) | 3 dni |
| **Hexagon real pipeline** | Implementacja 6 trybów z rzeczywistą logiką | 2 tygodnie |
| **Guardian weighted laws** | Ważone prawa: Nonmaleficence = instant DENY | 3 dni |

### Priorytet P1: Test coverage rozszerzenie

| Moduł | Obecna coverage | Cel |
|-------|----------------|-----|
| `db.py` | 0% | ≥60% |
| `main.py` | 0% | ≥60% |
| `orchestrator.py` | 0% | ≥70% |
| `executor.py` | 0% | ≥70% |
| Coverage łączna | 67% | ≥75% |

### Priorytet P1: Ollama optimizacja

| Zadanie | Opis |
|---------|------|
| Preload modelu przy starcie | Eliminacja cold start 10-60s |
| VRAM alerting | Prometheus metric dla GPU memory |
| Fallback: LLM_BACKEND=mock | Dla CI/CD bez GPU |

---

## FAZA 3 — PLANOWANA (2026-05 → 2026-06)

### Skalowalność i niezawodność (M4)

| Zadanie | Uzasadnienie | Priorytet |
|---------|-------------|-----------|
| Redis Sentinel HA | Eliminacja single-point-of-failure | P1 |
| FastAPI migration (api.py) | Async, middleware, OAuth2 przy >100 RPS | P2 |
| K8s staging deployment | Przygotowanie do produkcji | P1 |
| Horizontal scaling tests | Benchmark przy 10x obciążeniu | P2 |
| Backup automation | Codzienny backup PostgreSQL + testy przywracania | P1 |

### Nowe funkcjonalności

| Funkcja | Opis |
|---------|------|
| Multi-platform arbitraż | LinkedIn, Amazon, eBay integration (obok Upwork) |
| XRP tracker produkcyjny | `xrp_tracker.py` — live feed (obecnie 41% coverage) |
| Auto-bidding engine | Automatyczne złożenie oferty po APPROVED decision |
| Telegram/Slack alerts | Notyfikacje o decyzjach APPROVED/DENIED |

---

## FAZA 4 — WIZJA (Q3 2026)

### Produkcja i wzrost (M6)

| Cel | Opis |
|-----|------|
| K8s production | GKE/EKS deployment, autoscaling |
| SaaS model | Multi-tenant UAP Dashboard |
| Marketplace | ADRION jako platforma dla 3rd-party agentów |
| Mobile alerts | iOS/Android push notyfikacje |
| Revenue milestone | $10K MRR z automatycznego arbitrażu |

---

## Metryki sukcesu (KPIs per faza)

| Faza | Metryka | Cel |
|------|---------|-----|
| Faza 2 | Coverage | ≥75% |
| Faza 2 | Trinity latency | <500ms (prawdziwy scoring) |
| Faza 3 | API throughput | 100 RPS @ P95 <200ms |
| Faza 3 | Dostępność | 99.5% uptime |
| Faza 4 | Revenue | $10K MRR |
| Faza 4 | Decyzje/tydzień | >1000 APPROVED |

---

*ADRION 369 v1.0.0 — Genesis Record 2026-04-05*
