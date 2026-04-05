# 02 — Technical Architecture: ADRION 369

**Dla kogo:** CTO, architekci systemów, technical lead inwestorzy
**Data:** 2026-04-05 | **Wersja:** v1.0.0

---

## Architektura wysokiego poziomu

```
┌──────────────────────────────────────────────────────────────────┐
│                        ADRION 369 v4.0                           │
│                    Master Orchestrator Stack                      │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │  Arbitrage  │    │     UAP     │    │   Vortex Engine     │  │
│  │   API       │    │  Dashboard  │    │   (Go, 174Hz)       │  │
│  │ Python      │    │  port:8003  │    │   port:1740         │  │
│  │ BaseHTTP    │    │  Flask      │    │   monitoring        │  │
│  └──────┬──────┘    └──────┬──────┘    └───────┬─────────────┘  │
│         │                  │                   │                 │
│         └──────────────────┼───────────────────┘                 │
│                            │                                     │
│  ┌─────────────────────────▼─────────────────────────────────┐  │
│  │                  CORE DECISION ENGINE                      │  │
│  │                                                            │  │
│  │  Trinity (3 parallel)  →  Hexagon (6 sequential)          │  │
│  │    Material score           Inventory                      │  │
│  │    Intellectual score  →    Empathy                        │  │
│  │    Essential score          Process → Debate               │  │
│  │                             Healing → Action               │  │
│  │                   ↓                                        │  │
│  │           Guardians (9 laws sequentially)                  │  │
│  │           ≥2 violations = MANDATORY DENY                   │  │
│  └───────────────────────────┬────────────────────────────────┘  │
│                              │                                   │
│  ┌───────────────────────────▼────────────────────────────────┐  │
│  │                    INFRASTRUCTURE                           │  │
│  │                                                            │  │
│  │  PostgreSQL          Redis             Ollama              │  │
│  │  genesis_record  ←── AI-Binder     ←── DeepSeek-Coder-V2  │  │
│  │  (immutable log)     (zero-copy IPC)   (localhost:11434)   │  │
│  │                                                            │  │
│  │  Prometheus + Grafana + Loki    (monitoring stack)         │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 1. Framework decyzyjny 162D (Trinity-EBDI)

### Trinity — 3 perspektywy równoległe

```python
# Trzy niezależne oceny, każda 0.0–1.0
material_score    = assess_resources()     # CPU/RAM/GPU via psutil
intellectual_score = assess_logic()        # harmonic mean — all must pass
essential_score   = assess_alignment()     # geometric mean — all must be high

# Agregacja
overall_score = aggregate(material, intellectual, essential)
# Jeśli any < threshold → pipeline STOPS tu
```

**Matematyka aggregacji:**
- `Intellectual` — `harmonic_mean(scores)`: jeden low-score = fail całości (brak "dragging up")
- `Essential` — `geometric_mean(scores)`: wszystkie muszą być wysokie jednocześnie
- `Material` — `weighted_average(cpu, ram, gpu)`: zasoby ważone priorytetem

### Hexagon — 6 trybów sekwencyjnych

| Tryb | Funkcja | Output |
|------|---------|--------|
| `Inventory` | Kataloguje dostępne zasoby i narzędzia | Resource manifest |
| `Empathy` | Analizuje kontekst użytkownika/rynku | Context map |
| `Process` | Przetwarza zgodnie z regulami biznesowymi | Processed data |
| `Debate` | Waży alternatywne podejścia | Decision rationale |
| `Healing` | Naprawia niespójności, optymalizuje | Corrected state |
| `Action` | Generuje finalną odpowiedź/akcję | Executable action |

### Guardians — 9 Praw Etycznych

```
1. Unity         — Jeden cel, spójność systemu
2. Truth         — Brak dezinformacji, weryfikowalność
3. Rhythm        — Regularność i przewidywalność działania
4. Causality     — Przezroczystość łańcuchów przyczynowych
5. Transparency  — Każda decyzja explicite uzasadniona
6. Nonmaleficence — Nie szkodź (primum non nocere)
7. Autonomy      — Szanuj autonomię użytkownika
8. Justice       — Sprawiedliwy dostęp, brak bias
9. Sustainability — Długoterminowa zrównoważoność

Próg: ≥2 naruszeń → MANDATORY DENY (niezależnie od Trinity score)
```

---

## 2. Warstwa arbitrażowa (Arbitrage Engine)

### Pipeline generowania przychodu

```
[Scout] → [Analyzer] → [Bidder] → [Payments]
   ↑            ↑           ↑           ↑
 Apify/       Ollama     Strategy   Stripe
 Upwork       LLM        Engine     Webhooks
 sources
```

**Kluczowe moduły (`arbitrage/`):**

| Moduł | Funkcja | Test coverage |
|-------|---------|---------------|
| `api.py` | HTTP server (30+ endpoints) | 87.6% |
| `scout.py` | Lead discovery (Apify + mock) | 97.1% |
| `analyzer.py` | LLM-powered bid analysis | ~65% |
| `wholesale_scout.py` | B2B product discovery | 95.5% |
| `wholesale_orchestrator.py` | Wholesale lifecycle | 98.5% |
| `payments.py` | Stripe integration | 97.1% |
| `oracle.py` | Predictive pricing | 87.1% |
| `quantum.py` | EBDI state engine | 80.0% |
| `rate_limiter.py` | SlidingWindowRateLimiter | 73.3% |
| `circuit_breaker.py` | Per-service breakers | ~75% |

### Rate limits (per endpoint)

```
/api/quantum/*       30/min   — decision engine
/api/scout           10/min   — lead discovery
/api/cycle           5/min    — full arbitrage cycle
/api/oracle/*        20/min   — price prediction
/api/mass-generate   3/min    — bulk generation
```

---

## 3. Agenci AI (6+3 personas)

### Rdzeń (6 agentów)

| Agent | Rola | Trigger |
|-------|------|---------|
| Librarian | Kontekst historyczny, pamięć długoterminowa | Każde wywołanie |
| SAP | Planowanie strategiczne, priorytetyzacja | Nowe zadanie |
| Auditor | Walidacja jakości, code review | Post-action |
| Sentinel | Monitoring błędów, watchdog | 174Hz (Vortex) |
| Architect | Decyzje architektoniczne | Design changes |
| Healer | Naprawa długu technicznego | Degradacja |

### Rozszerzenie (3 agenty)

| Agent | Rola |
|-------|------|
| Amplifier | Wzmacnianie sygnałów rynkowych |
| BoosterLever | Optymalizacja dźwigni finansowej |
| Chronos | Zarządzanie harmonogramem, timing |

---

## 4. Infrastruktura

### Docker Compose (dev/staging)

```yaml
serwisy:
  adrion-api:        Python Flask/BaseHTTP  :5000
  adrion-uap:        UAP Dashboard          :8003
  vortex-engine:     Go sentinel            :1740
  postgres:          genesis_record DB      :5432
  redis:             AI-Binder IPC          :6379
  n8n:               Workflow automation    :5678
  ollama:            Local LLM              :11434
  prometheus:        Metrics                :9090
  grafana:           Visualization          :3000
  loki:              Log aggregation
```

### Stack technologiczny

| Warstwa | Technologie |
|---------|-------------|
| Runtime | Python 3.11, Go 1.21 |
| Framework | BaseHTTPRequestHandler, Flask 3.x |
| Database | PostgreSQL 15, SQLite (dev) |
| Cache/IPC | Redis 7.x |
| LLM | Ollama + DeepSeek-Coder-V2 |
| Monitoring | Prometheus, Grafana, Loki |
| CI/CD | GitHub Actions |
| Linting | Ruff, mypy (partial) |
| Testing | pytest, coverage.py |
| Containers | Docker Compose, K8s-ready |

---

## 5. Bezpieczeństwo architektoniczne

- **HMAC** — walidacja webhooków Stripe (SHA-256)
- **Rate limiting** — SlidingWindowRateLimiter per endpoint
- **Circuit breakers** — llm/stripe/apify/xrp_feed
- **Connection pooling** — PostgreSQL ThreadedConnectionPool(2,10)
- **Immutable audit** — Genesis Record append-only
- **Secret management** — `.env` + `manage-secrets.ps1` (nigdy w kodzie)
- **CORS** — konfigurowany przez `CORS_ALLOWED_ORIGIN` env var

---

## 6. Powiązane dokumenty

- [ATAM Analysis](../10_RAPORTY_DZIALANIA_SYSTEMU/REPORTS/ATAM_ADR_Analiza_Architektury_05-04-2026.md)
- [ADR-001 Trinity Framework](../../docs/adr/ADR-001-Trinity-EBDI-Framework.md)
- [API Schema](../../docs/API_SCHEMA.yaml)
- [Threat Model](../../docs/THREAT-MODEL.md)

---

*ADRION 369 v1.0.0 — Genesis Record 2026-04-05*
