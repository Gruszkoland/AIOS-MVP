# ATAM + ADR — Analiza Architektury ADRION 369

**Data:** 2026-04-05
**Wersja systemu:** v1.0.0 (Master Orchestrator v4.0)
**Autor:** Claude Sonnet 4.6 + Adiha
**Status:** ZAAKCEPTOWANY

---

## I. ATAM — Architecture Tradeoff Analysis Method

### 1.1 Cele biznesowe (Business Goals)

| #   | Cel                                                                   | Priorytet |
| --- | --------------------------------------------------------------------- | --------- |
| B1  | Autonomiczne podejmowanie decyzji zgodnych z 9 Prawami Strażników     | KRYTYCZNY |
| B2  | Local-first — pełna prywatność (brak cloud LLM dla wrażliwych danych) | KRYTYCZNY |
| B3  | Audytowalność każdej decyzji (immutable log w PostgreSQL)             | WYSOKI    |
| B4  | Skalowalność arbitrażu (leads z wielu platform jednocześnie)          | WYSOKI    |
| B5  | Testowalność i utrzymywalność (coverage ≥65%, CI/CD)                  | WYSOKI    |
| B6  | Time-to-market dla nowych agentów (wtyczki bez refaktoryzacji core)   | ŚREDNI    |

---

### 1.2 Drzewo atrybutów jakościowych (Quality Attribute Tree)

```
ATRYBUTY JAKOŚCIOWE
├── Wydajność (Performance)
│   ├── Czas odpowiedzi Trinity (< 500ms dla standardowych requestów)
│   ├── Przepustowość Hexagon (Inventory→Action pipeline)
│   └── Rate limiting (30/min quantum, 10/min scout, 5/min cycle)
│
├── Bezpieczeństwo (Security)
│   ├── Guardian Laws enforcement (fail-fast: 2+ naruszeń = ODMOWA)
│   ├── HMAC weryfikacja webhooków Stripe
│   └── Brak hardcoded secrets (env vars + manage-secrets.ps1)
│
├── Dostępność (Availability)
│   ├── Watchdog auto-restart agentów
│   ├── Circuit breakers (llm/stripe/apify/xrp_feed)
│   └── Disaster Recovery (scripts/backup/)
│
├── Skalowalność (Scalability)
│   ├── Horizontal scaling (Docker Compose → K8s ready)
│   ├── Redis zero-copy IPC między agentami
│   └── Connection pooling PostgreSQL (ThreadedConnectionPool 2-10)
│
├── Testowalność (Testability)
│   ├── Coverage gate 65% (pyproject.toml + CI/CD)
│   ├── Izolacja zależności (lazy imports + mockowanie)
│   └── Deterministyczne środowisko testowe (clean_env fixture)
│
└── Prywatosc (Privacy)
    ├── Ollama localhost (brak wysyłania danych do chmury)
    ├── Genesis Record local-only
    └── RODO-kompatybilny data flow
```

---

### 1.3 Scenariusze jakościowe (Quality Attribute Scenarios)

#### SC-01 — Spike ruchu 300% (Wydajność / Dostępność)

| Element        | Opis                                                                            |
| -------------- | ------------------------------------------------------------------------------- |
| **Źródło**     | Zewnętrzne żądania do ArbitrageHandler                                          |
| **Bodziec**    | Wzrost ruchu o 300% (np. batch scout 50 requestów/s)                            |
| **Środowisko** | Produkacja, pełne obciążenie                                                    |
| **Artefakt**   | `arbitrage/api.py` + `rate_limiter.py`                                          |
| **Odpowiedź**  | `SlidingWindowRateLimiter` zwraca 429 dla nadwyżki; legalny ruch obsłużony < 1s |
| **Miara**      | P95 latency < 1s; 0 dropped legitimate requests; rate limit hit < 5%            |

#### SC-02 — Naruszenie Prawa Strażnika (Bezpieczeństwo / Etyka)

| Element        | Opis                                                            |
| -------------- | --------------------------------------------------------------- |
| **Źródło**     | Request zawierający potencjalnie szkodliwą akcję                |
| **Bodziec**    | ≥2 naruszeń wśród 9 Guardian Laws                               |
| **Środowisko** | Każde                                                           |
| **Artefakt**   | `GuardiansValidator` w `backend/app.py`                         |
| **Odpowiedź**  | MANDATORY DENIAL niezależnie od wyniku Trinity                  |
| **Miara**      | 100% compliance — żaden request z ≥2 naruszeniami NIE przejdzie |

#### SC-03 — Awaria agenta w czasie wykonania (Dostępność)

| Element        | Opis                                                |
| -------------- | --------------------------------------------------- |
| **Źródło**     | Python exception / crash w `Executor` lub `Planner` |
| **Bodziec**    | Uncaught exception w backend/agents/\*.py           |
| **Środowisko** | Produkcja                                           |
| **Artefakt**   | `backend/core/watchdog.py`                          |
| **Odpowiedź**  | Auto-restart w < 5s; alert w Genesis Record         |
| **Miara**      | MTTR < 5s; 0 utraconych zadań (Redis queue persist) |

#### SC-04 — Wyciek danych do chmury (Prywatność)

| Element        | Opis                                                           |
| -------------- | -------------------------------------------------------------- |
| **Źródło**     | Developer dodaje nowy model LLM                                |
| **Bodziec**    | Próba użycia cloud API zamiast Ollama                          |
| **Środowisko** | Deweloperskie + produkcyjne                                    |
| **Artefakt**   | `config.py` (`LLM_BACKEND=ollama`) + 9. Prawo (Sustainability) |
| **Odpowiedź**  | Guardian Law #7 (Privacy) blokuje lub loguje ostrzeżenie       |
| **Miara**      | 0 PII wysłanych poza localhost                                 |

#### SC-05 — Degradacja coverage w CI (Testowalność)

| Element        | Opis                                   |
| -------------- | -------------------------------------- |
| **Źródło**     | Pull request z nowym kodem bez testów  |
| **Bodziec**    | `coverage < 65%` po merge              |
| **Środowisko** | GitHub Actions CI                      |
| **Artefakt**   | `.github/workflows/python-ci.yml`      |
| **Odpowiedź**  | Pipeline fail — blokada merge          |
| **Miara**      | Coverage gate egzekwowany na każdym PR |

---

### 1.4 Podejścia architektoniczne (Architectural Approaches)

| ID    | Podejście                            | Zasada                                                                                            |
| ----- | ------------------------------------ | ------------------------------------------------------------------------------------------------- |
| AP-01 | Trinity równoległa (3 perspektywy)   | Material + Intellectual + Essential liczone niezależnie, łączone harmonic/geometric mean          |
| AP-02 | Hexagon sekwencyjny pipeline         | 6 trybów w ściśle określonej kolejności (fail-fast jeśli żaden tryb nie pasuje)                   |
| AP-03 | Guardian fail-fast                   | 9 praw walidowanych sekwencyjnie; ≥2 naruszeń = natychmiastowy DENY                               |
| AP-04 | Lazy imports w api.py                | `_db()`, `_scout()` itp. importowane przy pierwszym użyciu → szybszy start, łatwiejsze mockowanie |
| AP-05 | BaseHTTPRequestHandler zamiast Flask | Brak heavy framework; pełna kontrola nad request/response lifecycle                               |
| AP-06 | Local-first LLM (Ollama)             | DeepSeek-Coder-V2 na localhost; brak zależności cloud                                             |
| AP-07 | Redis jako AI-Binder                 | Zero-copy IPC między agentami; kolejkowanie bez utraty danych                                     |
| AP-08 | PostgreSQL immutable audit log       | Genesis Record as cryptographic ledger                                                            |

---

### 1.5 Punkty wrażliwe (Sensitivity Points)

| SP    | Komponent                                  | Atrybuty                 | Ryzyko                                                                       |
| ----- | ------------------------------------------ | ------------------------ | ---------------------------------------------------------------------------- |
| SP-01 | `GuardiansValidator` — próg 2 naruszeń     | Bezpieczeństwo, Etyka    | Zbyt niski próg → fałszywe odrzucenia; zbyt wysoki → przepuszczenie zagrożeń |
| SP-02 | `SlidingWindowRateLimiter` — window 60s    | Wydajność, Dostępność    | Zbyt agresywny → legitimate traffic blokowany; zbyt luźny → DoS              |
| SP-03 | `ThreadedConnectionPool(2, 10)` PostgreSQL | Skalowalność, Dostępność | Pool exhaustion przy nagłym spike → bottleneck                               |
| SP-04 | Trinity `harmonic_mean` (Intellectual)     | Trafność decyzji         | Jeden low-score Intellectual wymusza fail → conservative bias                |
| SP-05 | Ollama model loading time                  | Wydajność (startup)      | Cold start może trwać 10-60s dla dużych modeli                               |

---

### 1.6 Punkty kompromisu (Tradeoff Points)

| TP    | Decyzja                                  | Zysk                                               | Koszt                                                                      |
| ----- | ---------------------------------------- | -------------------------------------------------- | -------------------------------------------------------------------------- |
| TP-01 | **Guardian fail-fast** (≥2 = DENY)       | Bezpieczeństwo: 100% compliance                    | Wydajność: każdy request walidowany 9x sekwencyjnie                        |
| TP-02 | **Local-first Ollama**                   | Prywatność: 0 PII w chmurze                        | Wydajność: cold start 10-60s; gorsze modele niż GPT-4                      |
| TP-03 | **Sekwencyjny Hexagon** (nie równoległy) | Determinizm: powtarzalność wyników                 | Latency: min 6 kroków zawsze, nie można pominąć                            |
| TP-04 | **BaseHTTPRequestHandler** (nie Flask)   | Kontrola: lżejszy stack, łatwiejsze mockowanie     | Ekosystem: brak middleware, własna implementacja routing                   |
| TP-05 | **Immutable PostgreSQL log**             | Audytowalność: pełna historia, niemodyfikowalna    | Write performance: każda decyzja = INSERT + commit                         |
| TP-06 | **Coverage gate 65%** (nie 80%)          | Prędkość: mniej testów do pisania                  | Jakość: 35% kodu niepokryte (m.in. db.py, main.py, executor.py)            |
| TP-07 | **Lazy imports w api.py**                | Testowalność: łatwe mockowanie `_db()`, `_scout()` | Czytelność: ukryta zależność — trudniejsza do śledzenia statycznej analizy |

---

### 1.7 Zidentyfikowane ryzyka (Risks)

| R    | Ryzyko                                              | Prawdopodobieństwo | Wpływ     | Mitygacja                                         |
| ---- | --------------------------------------------------- | ------------------ | --------- | ------------------------------------------------- |
| R-01 | Trinity/Hexagon/Guardians to SIMULACJA (alpha)      | PEWNE              | KRYTYCZNY | ADR-003: plan rzeczywistej implementacji          |
| R-02 | `db.py`, `main.py`, `orchestrator.py` — 0% coverage | WYSOKI             | WYSOKI    | Milestone M3: testy dla core modules              |
| R-03 | Ollama cold start blokuje pierwszą decyzję          | ŚREDNI             | ŚREDNI    | Preload model w startup script                    |
| R-04 | Redis single-point-of-failure                       | ŚREDNI             | WYSOKI    | Redis Sentinel lub Valkey cluster na prod         |
| R-05 | PostgreSQL pool exhaustion (max=10)                 | NISKI              | WYSOKI    | Monitor metrics + alerting Prometheus             |
| R-06 | Windows TCP RST w testach api.py                    | WYSOKI (Windows)   | NISKI     | `_rate_lim_post()` wrapper — już zaimplementowany |

---

### 1.8 Analiza wrażliwości vs kompromisy — mapa

```
BEZPIECZEŃSTWO
      │
  ↑   │  TP-01 (Guardian fail-fast)   TP-02 (Local Ollama)
      │         ●                           ●
      │
      │       SP-01 (próg Guardian)     SP-05 (Ollama startup)
      │             ●                         ●
      │
  ↓   │_______________________________________________→ WYDAJNOŚĆ
      niska                                        wysoka
```

---

## II. ADR — Architecture Decision Records

Pliki ADR przechowywane w: `docs/adr/`

---

### ADR-001: Trinity-EBDI jako rdzeń frameworku decyzyjnego

**Status:** ZAAKCEPTOWANY
**Data:** 2025-Q3 (inicjalizacja projektu)

**Kontekst:**
Potrzeba autonomicznego systemu podejmowania decyzji, który jest jednocześnie etyczny, logiczny i zasobowo efektywny. Klasyczne ML classifiers nie uwzględniają kontekstu etycznego.

**Decyzja:**
Implementacja 3-stopniowego frameworku: Trinity (3 perspektywy) → Hexagon (6 trybów) → Guardians (9 praw). Każda decyzja przechodzi przez wszystkie 3 etapy.

**Konsekwencje:**

- ✅ Każda decyzja jest explicite etycznie walidowana
- ✅ Pełna audytowalność (każdy etap logowany)
- ✅ Fail-fast: błąd na dowolnym etapie zatrzymuje pipeline
- ❌ Latency: min. 3 etapy zawsze, niemożliwe "fast path"
- ❌ Złożoność: nowi deweloperzy muszą zrozumieć całą filozofię 3-6-9
- ⚠️ RYZYKO: obecna implementacja to SIMULACJA — rzeczywista logika ML nie jest podłączona

---

### ADR-002: Fail-fast Guardian Laws (próg 2 naruszeń)

**Status:** ZAAKCEPTOWANY
**Data:** 2025-Q4

**Kontekst:**
Jak agresywnie egzekwować etyczne ograniczenia? Opcje: (A) blokuj przy 1 naruszeniu, (B) blokuj przy ≥2, (C) tylko loguj, nie blokuj.

**Decyzja:**
Próg 2 naruszeń = MANDATORY DENY, niezależnie od wyniku Trinity. Wybrano opcję B jako balans między surową etyką a użytecznością.

**Konsekwencje:**

- ✅ Odporny na ataki social engineering (pojedyncze "drobne" naruszenie nie przejdzie)
- ✅ Mniej false-positives niż próg=1
- ❌ Możliwe, że 1 poważne naruszenie (np. Nonmaleficence) nie blokuje samodzielnie
- ⚠️ Przyszłość: rozważyć ważone naruszenia (critical law = natychmiastowy DENY niezależnie od liczby)

---

### ADR-003: Local-first LLM — Ollama zamiast cloud API

**Status:** ZAAKCEPTOWANY
**Data:** 2025-Q4

**Kontekst:**
ADRION 369 przetwarza potencjalnie wrażliwe dane finansowe (leads, arbitraż). Cloud LLM (GPT-4, Claude) oferuje lepszą jakość, ale wysyła dane poza infrastrukturę.

**Decyzja:**
`LLM_BACKEND=ollama` jako domyślny. DeepSeek-Coder-V2 na localhost:11434. Cloud jako opt-in tylko w `.env.offline=False` przypadkach.

**Konsekwencje:**

- ✅ Zero PII w chmurze — RODO compliance
- ✅ Brak kosztów per-token dla produkcji
- ✅ Działa offline
- ❌ Gorsze rozumowanie niż frontier models
- ❌ Cold start 10-60s przy reload modelu
- ❌ Wymaga GPU ≥8GB VRAM dla wydajnej pracy

---

### ADR-004: BaseHTTPRequestHandler zamiast Flask/FastAPI

**Status:** ZAAKCEPTOWANY
**Data:** 2025-Q4

**Kontekst:**
`arbitrage/api.py` potrzebuje prostego HTTP servera dla ArbitrageHandler. Opcje: Flask, FastAPI, aiohttp, stdlib http.server.

**Decyzja:**
`BaseHTTPRequestHandler` z stdlib. Brak external dependencies dla core API layer.

**Konsekwencje:**

- ✅ 0 dodatkowych zależności
- ✅ Pełna kontrola nad request/response lifecycle
- ✅ Łatwe mockowanie (lazy imports `_db()`, `_scout()` itp.)
- ❌ Brak middleware support (auth, CORS, compression)
- ❌ Windows TCP RST issue przy rate-limiting (workaround potrzebny w testach)
- ❌ Synchronous only — brak async/await
- ⚠️ Rozważyć migrację do FastAPI przy skalowaniu powyżej 100 RPS

---

### ADR-005: PostgreSQL jako immutable audit log (Genesis Record)

**Status:** ZAAKCEPTOWANY
**Data:** 2025-Q4

**Kontekst:**
Każda decyzja ADRION musi być zapisana w sposób niemodyfikowalny dla celów audytu, compliance i debugowania. Opcje: append-only PostgreSQL, SQLite, flat-file log, blockchain.

**Decyzja:**
PostgreSQL `genesis_record` DB z append-only triggerami. Brak UPDATE/DELETE permissions dla app user. Kryptograficzny hash każdego rekordu.

**Konsekwencje:**

- ✅ Pełna audytowalność — żaden log nie może być cofnięty
- ✅ ACID compliance — brak partial writes
- ✅ SQL queries dla analizy historii decyzji
- ❌ Write overhead — każda decyzja = INSERT + fsync
- ❌ Wymaga backup procedury (scripts/backup/backup-postgres.sh)
- ⚠️ WDROŻENIE: obecna implementacja w `backend/app.py` to SIMULACJA — PostgreSQL insert nie jest podłączony

---

## III. Najważniejsze elementy analizy — Milestones

### Brama M1 — Definicja wymagań ✅ ZREALIZOWANA

| Kryterium                                                                   | Stan |
| --------------------------------------------------------------------------- | ---- |
| Wymagania funkcjonalne udokumentowane (`docs/ARCHITECTURE.md`)              | ✅   |
| Wymagania niefunkcjonalne (SLA: coverage 65%, rate limits, latency targets) | ✅   |
| Ograniczenia: budżet (local-only = $0 cloud), RODO, 9 Guardian Laws         | ✅   |
| Threat Model (`docs/THREAT-MODEL.md`)                                       | ✅   |

### Brama M2 — Architektura wysokiego poziomu ✅ ZREALIZOWANA

| Kryterium                                    | Stan |
| -------------------------------------------- | ---- |
| Diagramy blokowe (Trinity→Hexagon→Guardians) | ✅   |
| API kontrakty (`docs/API_SCHEMA.yaml`)       | ✅   |
| Komunikacja async: Redis AI-Binder           | ✅   |
| Komunikacja sync: BaseHTTPRequestHandler     | ✅   |

### Brama M3 — Modelowanie danych ⚠️ CZĘŚCIOWO

| Kryterium                                                | Stan          |
| -------------------------------------------------------- | ------------- |
| Schematy DB (`db/migrations/001_initial_schema.sql`)     | ✅            |
| Data flow: Scout→Analyzer→Bidder→Payments                | ✅            |
| Data flow: Genesis Record append-only                    | ✅            |
| **Rzeczywista implementacja PostgreSQL insert w app.py** | ❌ MOCK       |
| **Rzeczywista implementacja Trinity ML scoring**         | ❌ SIMULATION |

### Brama M4 — Skalowalność i niezawodność ⚠️ CZĘŚCIOWO

| Kryterium                                    | Stan           |
| -------------------------------------------- | -------------- |
| Circuit breakers (llm/stripe/apify/xrp_feed) | ✅             |
| Rate limiters (SlidingWindowRateLimiter)     | ✅             |
| Connection pooling PostgreSQL                | ✅             |
| Watchdog auto-restart                        | ✅             |
| Prometheus monitoring                        | ✅             |
| **Redis Sentinel / HA**                      | ❌ Single node |
| **K8s production deployment**                | ❌ Local only  |

### Brama M5 — Coverage & CI/CD ✅ ZREALIZOWANA (2026-04-05)

| Kryterium                   | Stan     |
| --------------------------- | -------- |
| Python coverage ≥65%        | ✅ 67.0% |
| 463 testów PASS             | ✅       |
| Ruff 0 errors               | ✅       |
| GitHub Actions CI/CD        | ✅       |
| Coverage gate w release.yml | ✅       |

---

## IV. Roadmap działań na podstawie ATAM

### Krótkoterminowe (1-2 tygodnie)

| Akcja                                                              | Uzasadnienie ATAM     | Priorytet |
| ------------------------------------------------------------------ | --------------------- | --------- |
| Pokrycie testami `db.py`, `main.py`, `orchestrator.py` (0% → ≥60%) | Brama M5: ryzyko R-02 | P0        |
| Ollama preload w startup (eliminacja cold start)                   | SP-05, TP-02          | P1        |
| Ważone Guardian Laws (CRITICAL = instant DENY)                     | TP-01 rozszerzenie    | P1        |

### Średnioterminowe (1 miesiąc)

| Akcja                                                       | Uzasadnienie ATAM | Priorytet |
| ----------------------------------------------------------- | ----------------- | --------- |
| Rzeczywista implementacja Trinity scoring (ML zamiast mock) | R-01              | P0        |
| PostgreSQL insert w app.py (nie simulacja)                  | R-01, ADR-005     | P0        |
| Migracja api.py na FastAPI (async + middleware)             | TP-04             | P2        |

### Długoterminowe (kwartał)

| Akcja                                              | Uzasadnienie ATAM | Priorytet |
| -------------------------------------------------- | ----------------- | --------- |
| Redis HA (Sentinel lub Valkey cluster)             | R-04              | P1        |
| K8s production deployment                          | Brama M4          | P2        |
| ADR dla każdej przyszłej decyzji architektonicznej | Dług techniczny   | P2        |

---

## V. Podsumowanie

**ADRION 369 v1.0 — ocena ATAM:**

```
Atrybuty ZREALIZOWANE dobrze:
  ✅ Testowalność       — 67.0% coverage, 463 testów, pełny CI/CD
  ✅ Bezpieczeństwo     — Guardian Laws, rate limiting, circuit breakers
  ✅ Prywatność         — Local-first Ollama, Genesis Record local-only
  ✅ Audytowalność      — Immutable log design, ATAM + ADR documentation

Atrybuty wymagające pracy:
  ⚠️ Wydajność          — Cold start Ollama; synchronous HTTP handler
  ⚠️ Dostępność         — Redis single-node; brak K8s prod

Krytyczny dług techniczny:
  ❌ Trinity/Hexagon/Guardians = SIMULACJA (alpha)
  ❌ PostgreSQL insert = MOCK (brak rzeczywistego zapisu)
```

**Wniosek:** Solidna architektura koncepcyjna z bardzo dobrą infrastrukturą testową (M5) i dobrym designem bezpieczeństwa. Główny bloker: przejście od symulacji do rzeczywistej implementacji logiki decyzyjnej (M3 P0).

---

_Raport wygenerowany: 2026-04-05_
_Metodologia: ATAM (CMU/SEI) + ADR (Michael Nygard pattern)_
_Zastosowanie: ADRION 369 Master Orchestrator v4.0_
