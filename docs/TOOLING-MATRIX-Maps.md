# TOOLING MATRIX: Mapowanie Narzędzi do Guardian Laws i Persona

**Data:** 05-04-2026  
**Generator:** MASTER ORCHESTRATOR + Explore Agent  
**Cel:** Praktyczne menu narzędziowe dla każdej decyzji architektonicznej

---

## MATRIX 1: Tools × Guardian Laws (9×60 Grid)

### G1: UNITY (Jedność, koherencja systemu)

| Narzędie | Kategoria | Funkcja | Osoba | Plik | Wdrożenie |
|----------|-----------|---------|-------|------|----------|
| **Trinity System** | Framework | Harmonizuje 3 perspektywy (Material/Intellectual/Essential) | SAP, Architect | config/trinity-weights.yml | ✅ Istniejące |
| **Arbitrium Consensus** | Logic | TS-ważone głosowanie 6 agentów | Architect | arbitrage/orchestrator.py | ✅ Istniejące |
| **N8N Workflow** | Orchestration | Unifikuje connectors i stream connectors | SAP | adrion-swarm/n8n_data/ | ✅ Istniejące |
| **Multi-Agent MoE Router** | Architecture | Routing zadań do specjalistów | SAP, Architect | arbitrage/orchestrator.py#MoE_gating | ✅ Istniejące |
| **Docker Compose** | Infrastructure | Single file orchestration (dev) | Architect | docker-compose.yml | ✅ Istniejące |
| **Kubernetes Namespace** | Infrastructure | Isolated ADRION environment (prod) | Architect | kubernetes/00-namespace.yaml | ✅ Istniejące |

### G2: HARMONY (Harmonia, balans afektywny)

| Narzędie | Kategoria | Funkcja | Osoba | Plik | Wdrożenie |
|----------|-----------|---------|-------|------|----------|
| **EBDI Model** | Framework | Pleasure/Arousal/Dominance balancing | Healer, Booster | persona-agents/boosterlever.md | ✅ Istniejące |
| **Circuit Breaker Pattern** | Architecture | Zapobieganie cascade failures | Sentinel, Architect | arbitrage/circuit_breaker.py | ✅ Istniejące |
| **Rate Limiter** | Security | DDoS protection, request throttling | Sentinel | arbitrage/rate_limiter.py | ✅ Istniejące |
| **EBDI Health Monitor (PHM)** | Monitoring | Persona state observation | Healer | persona-agents/healer.md | 🔲 Need Implementation |
| **Timeout + Retry Logic** | Resilience | Exponential backoff | Architect | arbitrage/rate_limiter.py | ✅ Istniejące |

### G3: RHYTHM (Rytm, cykličność operacyjna)

| Narzędie | Kategoria | Funkcja | Osoba | Plik | Wdrożenie |
|----------|-----------|---------|-------|------|----------|
| **Chronos (Prometheus)** | Monitoring | Time-series metrics (Booster, Trinity, EBDI) | Chronos, SAP | arbitrage/metrics.py | ✅ Istniejące |
| **Grafana Dashboard** | Monitoring | Visualization + alerting (5min refresh) | Chronos | docker-compose.prod.yml | ✅ Istniejące |
| **Loki + Promtail** | Logging | Stream consistency, 7-day retention | Chronos, Librarian | docker-compose.prod.yml | ✅ Istniejące |
| **N8N Scheduler** | Orchestration | Cron-based workflow timing | SAP | adrion-swarm/n8n_data/ | ✅ Istniejące |
| **Go Echo @ 174Hz** | Monitoring | High-frequency polling (Sentinel) | Sentinel | go.mod#Echo | ✅ Istniejące |
| **Adaptive Arousal Threshold** | Logic | Dynamic Crisis Mode trigger (0.65-0.75) | Sentinel, Healer | arbitrage/guardian.py | 🔲 Need Implementation |

### G4: CAUSALITY (Przyczynowość, determinizm logiczny)

| Narzędie | Kategoria | Funkcja | Osoba | Plik | Wdrożenie |
|----------|-----------|---------|-------|------|----------|
| **DSPy Signatures** | Framework | Formal Input→Output schema, MoE gating | Architect, SAP | arbitrage/llm.py | ✅ Istniejące |
| **Graph-of-Thoughts (GoT)** | AI Method | Spekulatywne eksplorowanie strategii | Architect, SAP | arbitrage/orchestrator.py#GoT | ✅ Istniejące |
| **MCTS (Monte Carlo Tree Search)** | AI Method | UCT-based strategy search | Architect | arbitrage/quantum.py | ✅ Istniejące |
| **Event Sourcing (Genesis Record)** | Pattern | Full operation history (CQRS) | Librarian, Auditor | Genesis Record/10_RAPORTY/ | ✅ Istniejące |
| **Chain-of-Thought (CoT)** | AI Method | Intermediate reasoning steps | Healer, Auditor | arbitrage/oracle.py | ✅ Istniejące |
| **STaR (Self-Correction)** | AI Method | Rational backward justification | Auditor, Healer | arbitrage/orchestrator.py#Step3 | 🔲 Need Implementation |

### G5: TRANSPARENCY (Przejrzystość, obsługiwalność)

| Narzędie | Kategoria | Funkcja | Osoba | Plik | Wdrożenie |
|----------|-----------|---------|-------|------|----------|
| **Grafana Dashboards** | Monitoring | Metric visualization (7-day rolling) | Chronos, SAP | docker-compose.prod.yml | ✅ Istniejące |
| **Loki Logs** | Logging | Searchable, aggregated logs | Librarian, Auditor | docker-compose.prod.yml | ✅ Istniejące |
| **Genesis Record (JSON/MD)** | Logging | Operation history + Decision trail | Librarian, Auditor | Genesis Record/10_RAPORTY/ | ✅ Istniejące |
| **Ruff Linter** | Code Quality | Enforces clarity (E, F, W, I rules) | Auditor | Makefile | ✅ Istniejące |
| **API Documentation (Swagger)** | Documentation | REST endpoint specs | Architect, SAP | arbitrage/api.py | 🔲 Need Implementation |
| **ADR Records** | Documentation | Architecture Decision Records | Architect, Auditor | docs/adr/ | 🔲 Need 10 ADRs |

### G6: AUTHENTICITY (Autentyczność, integralność decyzji)

| Narzędie | Kategoria | Funkcja | Osoba | Plik | Wdrożenie |
|----------|-----------|---------|-------|------|----------|
| **PyJWT** | Security | JWT identity verification | Sentinel, Auditor | uap/websocket_server.py | ✅ Istniejące |
| **Anthropic Claude** | LLM Backend | Safety-critical task validation | Auditor, Sentinel | requirements-arbitrage.txt | ✅ Istniejące (optional) |
| **pytest + pytest-cov** | Testing | Unit/integration + coverage validation (80% gate) | Auditor | tests/, pytest.ini | ✅ Istniejące |
| **Ruff Linter** | Code Quality | Type/style consistency enforcement | Auditor | Makefile | ✅ Istniejące |
| **Dry Run Mode (DRM)** | Safety | Preview changes before execution | Architect, Auditor | orchestration workflow | 🔲 Need Implementation |
| **SimPO (Simplified Preference Opt.)** | AI Method | Length-normalized scoring | Booster | arbitrage/orchestrator.py | 🔲 Need Implementation |

### G7: PRIVACY (Prywatność, local-first) ⭐ CRITICAL

| Narzędie | Kategoria | Funkcja | Osoba | Plik | Wdrożenie |
|----------|-----------|---------|-------|------|----------|
| **Python-dotenv** | Security | Local-first secrets (default env) | Guardian, SAP | arbitrage/.env | ✅ Istniejące |
| **SQLite3** | Database | Local data storage (default) | Guardian, Healer | arbitrage/database.py | ✅ Istniejące |
| **Kubernetes Secrets** | Security | Encrypted config storage (prod) | Guardian, Architect | kubernetes/01-secrets-configmaps.yaml | ✅ Istniejące |
| **TLS/SSL (crypto/x509)** | Security | Encrypted transport layer | Architect, Sentinel | kubernetes/06-ingress.yaml | ✅ Istniejące |
| **Ollama Local-First** | LLM Backend | Offline-first inference (port 11434) | Guardian, SAP | docker-compose.yml | ✅ Istniejące |
| **Network Segmentation** | Infrastructure | K8s NetworkPolicy isolation | Architect | kubernetes/k8s-netpol.yaml | 🔲 Need Implementation |

### G8: NONMALEFICENCE (Niezawodność, fail-safe)

| Narzędie | Kategoria | Funkcja | Osoba | Plik | Wdrożenie |
|----------|-----------|---------|-------|------|----------|
| **Circuit Breaker** | Resilience | Graceful degradation, fail-fast | Sentinel, Architect | arbitrage/circuit_breaker.py | ✅ Istniejące |
| **Rate Limiter** | Security | DDoS/abuse prevention | Sentinel | arbitrage/rate_limiter.py | ✅ Istniejące |
| **Guardian Module** | Security | 12 threat vector monitoring | Sentinel | arbitrage/guardian.py | ✅ Istniejące |
| **PostgreSQL HA** | Infrastructure | replicated DB (failover) | Architect, Healer | kubernetes/03-postgres.yaml | ✅ Istniejące |
| **Docker Health Checks** | Monitoring | Container restart on failure | Sentinel, Architect | docker-compose.yml | ✅ Istniejące |
| **Alerting Thresholds** | Monitoring | Grafana alerts (30s response SLA) | Sentinel | docker-compose.prod.yml | ✅ Istniejące |

### G9: SUSTAINABILITY (Zrównoważenie, optymalizacja zasobów)

| Narzędie | Kategoria | Funkcja | Osoba | Plik | Wdrożenie |
|----------|-----------|---------|-------|------|----------|
| **Docker + Kubernetes** | Infrastructure | Efficient container orchestration | Architect, SAP | docker-compose.yml, kubernetes/ | ✅ Istniejące |
| **DeepSeek-Lite LLM** | LLM Backend | Low-resource inference (fallback) | SAP | scripts/download_model_lite.sh | ✅ Istniejące |
| **Time-Series Archival** | Storage | Hot/warm/cold data tiering | Librarian, Healer | Genesis Record + Loki | 🔲 Need Implementation |
| **Resource Limits (K8s)** | Infrastructure | Memory/CPU quotas per service | Architect | kubernetes/*.yaml | ✅ Istniejące |
| **Makefile Automation** | DevOps | Efficient task execution, caching | SAP, Auditor | Makefile | ✅ Istniejące |
| **CI/CD Gating** | DevOps | Pre-flight validation (80% coverage, lint) | Auditor, Architect | .github/workflows/ | ✅ Istniejące |

---

## MATRIX 2: Tools × Persona (6 Osób × Przydzielone Narzędzia)

### LIBRARIAN (Knowledge Index & Memory Management)

| Narzędie | Funkcja | Plik | Priority | Status |
|----------|---------|------|----------|--------|
| **Loki + Grafana** | Log aggregation, searching | docker-compose.prod.yml | HIGH | ✅ |
| **SQLite3 + PostgreSQL** | Data storage (local→prod) | arbitrage/database.py | HIGH | ✅ |
| **Genesis Record (JSON/MD)** | Operation history | Genesis Record/10_RAPORTY/ | CRITICAL | ✅ |
| **Ruff Linter** | Code organization, clarity | Makefile | MEDIUM | ✅ |
| **Vector DB (RAG)** | Semantic search for decisions | Optional library | MEDIUM | 🔲 |
| **mkdocs** | Documentation generation | Optional | LOW | 🔲 |

### SAP (System Architecture Planning)

| Narzędie | Funkcja | Plik | Priority | Status |
|----------|---------|------|----------|--------|
| **Trinity System** | 3×6×9 planning matrix | config/trinity-weights.yml | CRITICAL | ✅ |
| **N8N Workflow** | Orchestration, connectors | adrion-swarm/n8n_data/ | HIGH | ✅ |
| **Graph-of-Thoughts** | Strategy exploration | arbitrage/orchestrator.py | HIGH | ✅ |
| **Prometheus Metrics** | Tracking, KPIs | arbitrage/metrics.py | HIGH | ✅ |
| **WebSockets** | Real-time data sync | uap/websocket_server.py | MEDIUM | ✅ |
| **Kubernetes** | Scaling planning | kubernetes/ | MEDIUM | ✅ |
| **Makefile** | Task automation | Makefile | MEDIUM | ✅ |

### AUDITOR (Compliance & Verification)

| Narzędie | Funkcja | Plik | Priority | Status |
|----------|---------|------|----------|--------|
| **pytest + pytest-cov** | Unit/integration + 80% gate | tests/, pytest.ini | CRITICAL | ✅ |
| **Ruff Linter** | Code quality enforcement | Makefile | HIGH | ✅ |
| **DSPy Validator** | Signature validation | arbitrage/llm.py | HIGH | ✅ |
| **PyJWT** | Auth verification | uap/websocket_server.py | MEDIUM | ✅ |
| **Genesis Record** | Audit trail review | Genesis Record/10_RAPORTY/ | HIGH | ✅ |
| **DRM (Dry Run Mode)** | Pre-approval validation | orchestration workflow | MEDIUM | 🔲 |
| **ADR Records** | Decision documentation | docs/adr/ | HIGH | 🔲 |

### SENTINEL (Security & Crisis Mode)

| Narzędie | Funkcja | Plik | Priority | Status |
|----------|---------|------|----------|--------|
| **Docker SDK** | Health checks, restart | arbitrage/main.py | HIGH | ✅ |
| **Go Echo @ 174Hz** | High-frequency monitoring | go.mod#Echo | CRITICAL | ✅ |
| **Circuit Breaker** | Cascade prevention | arbitrage/circuit_breaker.py | HIGH | ✅ |
| **Rate Limiter** | Abuse protection | arbitrage/rate_limiter.py | HIGH | ✅ |
| **Guardian Module (12 vectors)** | Threat detection | arbitrage/guardian.py | CRITICAL | ✅ |
| **Grafana Alerting** | 30s response SLA | docker-compose.prod.yml | CRITICAL | ✅ |
| **PyJWT + crypto/x509** | Identity + TLS | uap/websocket_server.py | HIGH | ✅ |

### ARCHITECT (Design & Infrastructure)

| Narzędie | Funkcja | Plik | Priority | Status |
|----------|---------|------|----------|--------|
| **Kubernetes** | Orchestration, scaling | kubernetes/ | CRITICAL | ✅ |
| **Docker Compose** | Local dev orchestration | docker-compose.yml | HIGH | ✅ |
| **CQRS Pattern** | Command/Query separation | arbitrage/api.py, oracle.py | MEDIUM | ✅ |
| **Saga Pattern** | Distributed transactions | arbitrage/executor.py | MEDIUM | ✅ |
| **Event Sourcing** | State history | Genesis Record/ | MEDIUM | ✅ |
| **DSPy MoE Gating** | Signature validation | arbitrage/llm.py | CRITICAL | ✅ |
| **Terraform** (optional) | IaC for K8s | Optional | MEDIUM | 🔲 |

### HEALER (Diagnostics & Recovery)

| Narzęzie | Funkcja | Plik | Priority | Status |
|----------|---------|------|----------|--------|
| **Git Stash + Commits** | RBC checkpointing | .git/ (native) | CRITICAL | ✅ |
| **PostgreSQL** | Recovery DB, snapshots | arbitrage/database.py | HIGH | ✅ |
| **Rollback Logic** | State reset mechanisms | EBDI + Identity Reset | HIGH | 🔲 |
| **EBDI Model** | Emotional recovery | persona-agents/healer.md | HIGH | ✅ |
| **Identity Reset (PHM)** | Persona health recovery | persona-agents/healer.md | MEDIUM | 🔲 |
| **STaR (Self-Correction)** | Backward justification | arbitrage/orchestrator.py | MEDIUM | 🔲 |
| **Prometheus Metrics** | Health diagnostics | arbitrage/metrics.py | MEDIUM | ✅ |

---

## MATRIX 3: Reliability Mechanisms × Implementation Status

| Mechanizm | Narzęzie Główne | Plik Implementacji | Status | Priority | Next Step |
|-----------|-----------------|-------------------|--------|----------|-----------|
| **TSPA** | Python native | arbitrage/orchestrator.py | ✅ | CRITICAL | ADR-003 (granularity) |
| **SAV** | get_errors + pytest | arbitrage/orchestrator.py | ✅ | CRITICAL | Probabilistic SAV (ADR-004) |
| **RBC** | Git + session JSON | .git + /memories/session/ | ✅ | CRITICAL | Timing optimization (ADR-007) |
| **SCB** | Memory system + RAG | /memories/ + Loki search | ✅ | HIGH | RAG vector DB (ADR-005) |
| **CWM** | Token counter | arbitrage/orchestrator.py | ✅ (partial) | MEDIUM | Recursive summarization (ADR-004) |
| **CR** | Arbitrium voting | arbitrage/orchestrator.py | ✅ | MEDIUM | Consensus model docs (ADR-006) |
| **DSV** | DSPy library | arbitrage/llm.py | ✅ | CRITICAL | Full MoE validation (ADR-001) |
| **DRM** | Diff generation | orchestration workflow | 🔲 | MEDIUM | Implement user approval flow |
| **TEL** | EBDI metrics | persona-agents/ | ✅ (partial) | HIGH | Real-time telemetry dashboard |
| **PHM** | EBDI monitor | persona-agents/healer.md | 🔲 | HIGH | anomaly detection + reset logic |

---

## MATRIX 4: Quick Reference — "Który Tool Do Której Decyzji?"

### Scenariusz: „Muszę zbudować nowy feature w arbitrage engine"

```
1. IDENTYFIKUJ Guardian Laws ↓
   └─ Który z 9 praw jest zagrożony?
   └─ np. G5 (Transparency) + G7 (Privacy)

2. WYBIERZ Persona(s) Wiodące ↓
   └─ Kto decyduje? SAP lub Architect?
   └─ Kto audytuje? Auditor.

3. LOOKUP Tools Mapę ↓
   └─ G5 + G7 → DSPy, Ollama, Graphan, pytest
   └─ Architect → Kubernetes, CQRS, Event Sourcing

4. ZASTOSUJ Metodologię ↓
   └─ Graph-of-Thoughts (strategy)
   └─ MCTS (option search)
   └─ Chain-of-Thought (reasoning)

5. DOKUMENTUJ w ADR ↓
   └─ Czy to NOWA decyzja? → Utwórz ADR
   └─ Czy to ZMIANA istniejącej decyzji? → Update ADR

6. WERYFIKUJ z SAV + CR ↓
   └─ SAV: Unit tests (80% gate) + Ruff linting
   └─ CR: Consensus voting if conflicting proposals

7. DEPLOYUJ z DRM ↓
   └─ Dry Run: Preview changes
   └─ User approval
   └─ Git commit + Genesis Record
```

---

## NEXT ACTIONS (Tydzień 1)

- [ ] Stwórz /docs/TOOLING-MATRIX/ katalog (4 pliki)
- [ ] Dodaj Tools-by-Guardian-Laws.md
- [ ] Dodaj Tools-by-Persona.md
- [ ] Dodaj Tools-by-Reliability-Mechanism.md
- [ ] Dodaj Quick-Decision-Reference.md (ten dokument)
- [ ] Integruj z Genesis Record monitoring

---

**Generated:** 2026-04-05  
**By:** MASTER ORCHESTRATOR v4.0 + Explore Agent  
**For:** ADRION 369 Architecture Framework Implementation
