# 07 — Risk Assessment: ADRION 369

**Dla kogo:** Inwestorzy, CTO, zarząd
**Data:** 2026-04-05 | **Wersja:** v1.0.0
**Metodologia:** ATAM Risk Register + Heat Map

---

## Risk Heat Map

```
WPŁYW
  │
K │        R-01(PEWNE/KRY)
R │
Y │
T │
Y │                    R-04
C │                  (ŚRED/WYS)
Z │         R-02
N │       (WYS/WYS)
Y │                    R-03
  │                 (ŚRED/ŚRED)
W │                               R-05
Y │                            (NISKI/WYS)
S │                R-06
O │           (WYS/NISKI)
K │                               R-07
I │                            (NISKI/NISKI)
  └─────────────────────────────────────────→
     NISKIE      ŚREDNIE      WYSOKIE    PEWNE
                                         Prawdopodobieństwo
```

---

## Rejestr ryzyk technicznych

### R-01 — Trinity/Hexagon/Guardians to SIMULACJA

| Pole | Wartość |
|------|---------|
| **Prawdopodobieństwo** | PEWNE (100% — znany fakt) |
| **Wpływ** | KRYTYCZNY |
| **Kategoria** | Dług techniczny / Product |
| **Opis** | Obecna implementacja core logic w `backend/app.py` zwraca predefiniowane mock responses. Brak rzeczywistego ML scoring, PostgreSQL write, agent spawning. |
| **Konsekwencja** | System nie może generować rzeczywistego przychodu dopóki nie zostanie zaimplementowany |
| **Mitygacja** | ZAPLANOWANA: Milestone M3 (Faza 2, ~4 tygodnie) |
| **Właściciel** | Tech Lead |

### R-02 — `db.py`, `main.py`, `orchestrator.py` — 0% coverage

| Pole | Wartość |
|------|---------|
| **Prawdopodobieństwo** | WYSOKI |
| **Wpływ** | WYSOKI |
| **Kategoria** | Jakość / Testowalność |
| **Opis** | Trzy krytyczne moduły nie mają żadnych testów, mimo coverage gate 65% ogółem. Regresje mogą przejść CI. |
| **Konsekwencja** | Silent bugs w core data pipeline |
| **Mitygacja** | Priorytet P0 Fazy 2: dopisanie testów do tych modułów |
| **Właściciel** | QA Lead |

### R-03 — Ollama cold start 10-60s

| Pole | Wartość |
|------|---------|
| **Prawdopodobieństwo** | ŚREDNI |
| **Wpływ** | ŚREDNI |
| **Kategoria** | Wydajność / UX |
| **Opis** | Po restarcie serwera lub dłuższym idle, pierwsza decyzja LLM wymaga 10-60s ładowania modelu DeepSeek-Coder-V2 do VRAM. |
| **Konsekwencja** | Timeout requestów dla pierwszego użytkownika po restarcie |
| **Mitygacja** | Preload model w startup script; healthcheck czeka na model ready |
| **Właściciel** | DevOps |

### R-04 — Redis single-point-of-failure

| Pole | Wartość |
|------|---------|
| **Prawdopodobieństwo** | ŚREDNI |
| **Wpływ** | WYSOKI |
| **Kategoria** | Dostępność |
| **Opis** | Redis (AI-Binder) działa jako single node. Crash Redis = brak IPC między agentami = system offline. |
| **Konsekwencja** | Pełny downtime systemu multi-agentowego |
| **Mitygacja** | Redis Sentinel lub Valkey cluster (Faza 3) |
| **Właściciel** | DevOps |

### R-05 — PostgreSQL pool exhaustion (max=10)

| Pole | Wartość |
|------|---------|
| **Prawdopodobieństwo** | NISKI |
| **Wpływ** | WYSOKI |
| **Kategoria** | Skalowalność |
| **Opis** | `ThreadedConnectionPool(2, 10)` — przy >10 concurrent requests następuje blokowanie oczekujące na wolne połączenie. |
| **Konsekwencja** | Degradacja wydajności, potencjalnie timeouty |
| **Mitygacja** | Prometheus alert przy pool_active ≥ 9; krótkoterminowo: pool max=20 |
| **Właściciel** | Backend Lead |

### R-06 — Windows TCP RST w prod (jeśli deployment na Windows)

| Pole | Wartość |
|------|---------|
| **Prawdopodobieństwo** | WYSOKI (tylko Windows) |
| **Wpływ** | NISKI |
| **Kategoria** | Środowisko |
| **Opis** | `BaseHTTPRequestHandler` na Windows wysyła TCP RST gdy zamknie połączenie bez odczytania pełnego body. Klienci dostają `ConnectionAbortedError`. |
| **Konsekwencja** | Nieoczekiwane błędy po stronie klienta przy rate-limit responses |
| **Mitygacja** | Zaimplementowany `_rate_lim_post()` wrapper w testach; producja powinna być na Linux |
| **Właściciel** | Backend Lead |

### R-07 — Regulatory risk (AI Act EU)

| Pole | Wartość |
|------|---------|
| **Prawdopodobieństwo** | NISKI (2026) |
| **Wpływ** | WYSOKI |
| **Kategoria** | Compliance / Legal |
| **Opis** | EU AI Act wchodzi w życie stopniowo 2024-2026. Systemy autonomicznego podejmowania decyzji finansowych mogą być klasyfikowane jako "high-risk AI". |
| **Konsekwencja** | Wymóg rejestracji, auditu, explainability documentation |
| **Mitygacja** | Guardian Laws + Genesis Record = compliance advantage; ADR dokumentacja |
| **Właściciel** | CEO / Legal |

---

## Ryzyka biznesowe (non-technical)

| Ryzyko | Prawdopodobieństwo | Wpływ | Mitygacja |
|--------|-------------------|-------|-----------|
| Zmiany API Upwork/Apify | ŚREDNI | WYSOKI | Abstraction layer w scout.py; alternatywne platformy |
| Arbitraż staje się nieopłacalny (marże <5%) | NISKI | WYSOKI | Multi-platform diversification; wholesale jako backup |
| Konkurencja wprowadza podobne rozwiązanie | ŚREDNI | ŚREDNI | Moat: Guardian Laws + local-first + patent przygotowanie |
| GPU shortage (wzrost cen / brak dostępności) | NISKI | ŚREDNI | Cloud GPU as fallback (opt-in); Ollama kompatybilny z cloud |

---

## Risk response plan

| Poziom ryzyka | Czas reakcji | Osoba odpowiedzialna |
|---------------|-------------|---------------------|
| KRYTYCZNY | <24h | Tech Lead + CEO |
| WYSOKI | <1 tydzień | Tech Lead |
| ŚREDNI | Sprint (2 tygodnie) | Backend Lead |
| NISKI | Backlog | QA Lead |

---

*ADRION 369 v1.0.0 — Genesis Record 2026-04-05*
*Pełna analiza ATAM: [ATAM_ADR_Analiza_Architektury_05-04-2026.md](../10_RAPORTY_DZIALANIA_SYSTEMU/REPORTS/ATAM_ADR_Analiza_Architektury_05-04-2026.md)*
