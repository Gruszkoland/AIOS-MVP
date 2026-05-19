# ADRION 369 — Plan Dokończenia Projektu + Ocena

**Data:** 2026-04-01
**Ocena globalna: 58/100**

---

## I. STAN OBECNY — INWENTARYZACJA

| Warstwa                          | Pliki                    | Funkcje                       | Stan                                          |
| -------------------------------- | ------------------------ | ----------------------------- | --------------------------------------------- |
| Python Arbitrage (`arbitrage/`)  | 22 .py                   | ~150+                         | ✅ Działa, testy E2E przechodzą               |
| Next.js SaaS (`micro-saas/`)     | ~30 plików               | 8 tras, 8 komponentów, 13 lib | ⚠️ Mock data, brak produkcyjnego DB           |
| Go Sentinel (`cmd/`+`internal/`) | 6 .go                    | 6 endpointów                  | ⚠️ Szkielet, brak integracji z Python         |
| Dashboard (`dashboard/`)         | 1 HTML                   | Oracle + Toroid + XRP         | ✅ Panel pełny                                |
| Harmonia Dashboard               | 14 plików                | Pipeline + RAG + Feedback     | ⚠️ Osobny ekosystem, brak bridge              |
| Docker                           | 3 compose + 3 Dockerfile | 3 serwisy                     | ⚠️ Konfiguracja, nie przetestowane end-to-end |
| Testy                            | 4 pliki                  | ~40 asercji                   | ⚠️ Brak unit testów per moduł                 |
| Dokumentacja                     | 18 docs + 40 progress    | —                             | ✅ Nadmiarowa, ale kompletna                  |
| Baza danych                      | SQLite 13 tabel          | CRUD                          | ⚠️ Lokalna, brak migracji do Supabase         |

---

## II. OCENA SZCZEGÓŁOWA (po wymiarach)

| Wymiar                                          | Waga | Ocena    | Ważony   |
| ----------------------------------------------- | ---- | -------- | -------- |
| **Logika biznesowa** (arbitrage pipeline)       | 25%  | 75/100   | 18.75    |
| **Frontend/UX** (dashboard + Next.js)           | 15%  | 50/100   | 7.50     |
| **Infrastruktura** (Docker, DB, CI/CD)          | 15%  | 30/100   | 4.50     |
| **Integracje zewnętrzne** (Stripe, Google, LLM) | 15%  | 40/100   | 6.00     |
| **Testy i jakość** (coverage, lint, types)      | 10%  | 25/100   | 2.50     |
| **Bezpieczeństwo** (G7-G9, OWASP)               | 10%  | 65/100   | 6.50     |
| **Dokumentacja i onboarding**                   | 5%   | 85/100   | 4.25     |
| **Gotowość produkcyjna** (deploy, monitoring)   | 5%   | 20/100   | 1.00     |
|                                                 |      | **SUMA** | **51.0** |

Korekta +7 za: pełny pipeline E2E, 25+ endpointów API, 162D framework architektoniczny.

**Wynik: 58/100**

---

## III. BLOKERY KRYTYCZNE (musisz rozwiązać przed produkcją)

### B1. Brak prawdziwych danych (MOCK everywhere)

- `wholesale_scout.py` → `MOCK_WHOLESALE_PRODUCTS` (hardcoded 10 items)
- `scout.py` → `_mock_scout()` (Fiverr/Upwork symulowane)
- `oracle.py` → brak `price_history` → DORMANT signal zawsze
- `mass_generator.py` → generuje manifest z mock deals
- **Impact:** Cały pipeline działa, ale na sztucznych danych. Zero walidacji rynkowej.

### B2. SQLite → Supabase/PostgreSQL migracja

- 13 tabel w SQLite, brak ORM, raw SQL queries
- `schema_wholesale.sql` istnieje ale nie jest zsynchronizowany z `database.py`
- Docker compose ma PostgreSQL ale Python go nie używa
- **Impact:** Brak współbieżności, brak multi-user, brak backupu.

### B3. Go ↔ Python brak mostu

- Go na porcie 1740, Python na 8001 — zero komunikacji między nimi
- `internal/indexing/google_api.go` gotowy ale niepodłączony
- `internal/bridge/xml_parser.go` duplikuje logikę z `wholesale_scout.py`
- **Impact:** Go servant jest martwym kodem w produkcji.

### B4. Brak CI/CD

- Zero GitHub Actions / pipeline
- Zero lintingu zautomatyzowanego
- Zero testów w pre-commit / pre-push
- **Impact:** Każdy deploy to ręczna praca.

---

## IV. PLAN DOKOŃCZENIA — 9 ETAPÓW (Trinity 3-6-9)

### ═══ TRIAD 1: STABILIZACJA (Fundamenty) ═══

#### Etap 1: Prawdziwe źródła danych

**Priorytet:** KRYTYCZNY | **Effort:** 3-5 dni | **Blokuje:** wszystko dalej

| Zadanie | Plik                           | Opis                                                       |
| ------- | ------------------------------ | ---------------------------------------------------------- |
| 1.1     | `arbitrage/wholesale_scout.py` | Podłączyć 1 prawdziwy feed XML/JSON z hurtowni (PL lub DE) |
| 1.2     | `arbitrage/scout.py`           | Aktywować Apify connector z prawdziwym tokenem             |
| 1.3     | `arbitrage/oracle.py`          | Dodać `price_history` z prawdziwych danych (min. 30 dni)   |
| 1.4     | `.env` / `.env.adrion`         | Wypełnić prawdziwe klucze API                              |

**Kryterium Done:** `run_wholesale_cycle(use_mock=False)` zwraca ≥1 deal z marżą >15%.

#### Etap 2: Migracja DB → PostgreSQL

**Priorytet:** WYSOKI | **Effort:** 2-3 dni

| Zadanie | Plik                                    | Opis                                                           |
| ------- | --------------------------------------- | -------------------------------------------------------------- |
| 2.1     | `arbitrage/database.py`                 | Abstrakcja `get_conn()` → obsługuje SQLite LUB PostgreSQL      |
| 2.2     | `adrion-swarm/docker-compose.yml`       | Potwierdzić PostgreSQL na porcie 5432 z danymi z `.env.adrion` |
| 2.3     | Nowy: `scripts/migrate_sqlite_to_pg.py` | Jednorazowy skrypt migracji danych                             |
| 2.4     | `arbitrage/schema_wholesale.sql`        | Sync z aktualną definicją tabel w `database.py`                |

**Kryterium Done:** `init_db()` działa z `DB_HOST=adrion-db` i wszystkie 13 tabel istnieją w PostgreSQL.

#### Etap 3: Testy automatyczne

**Priorytet:** WYSOKI | **Effort:** 2 dni

| Zadanie | Plik                              | Opis                                                                       |
| ------- | --------------------------------- | -------------------------------------------------------------------------- |
| 3.1     | `tests/test_oracle.py`            | Unit testy: `oracle_predict()`, `fibonacci_levels()`, `assign_solfeggio()` |
| 3.2     | `tests/test_quantum.py`           | Unit testy: `quantum_decide()`, `entangle_markets()`, `AutopoiezaTracker`  |
| 3.3     | `tests/test_database.py`          | CRUD testy: `upsert_deal()`, `get_deals()`, `record_kpi_event()`           |
| 3.4     | `tests/test_mass_generator.py`    | `generate_manifest()`, `slugify()`, `build_product_entry()`                |
| 3.5     | `pytest.ini` lub `pyproject.toml` | Konfiguracja pytest, coverage ≥60%                                         |

**Kryterium Done:** `pytest --cov=arbitrage` → 60%+ coverage, zero failures.

---

### ═══ TRIAD 2: INTEGRACJA (Połączenia) ═══

#### Etap 4: Go ↔ Python Bridge

**Priorytet:** ŚREDNI | **Effort:** 2-3 dni

| Zadanie | Plik                                                       | Opis                                                         |
| ------- | ---------------------------------------------------------- | ------------------------------------------------------------ |
| 4.1     | `internal/api/handlers.go`                                 | Dodać proxy do Python API (port 8001) lub gRPC               |
| 4.2     | `cmd/vortex-server/main.go`                                | Route `/wholesale/scan` → wywołuje Python `/wholesale/scout` |
| 4.3     | `internal/indexing/google_api.go`                          | Podłączyć do Mass Generator → auto-index nowych stron        |
| 4.4     | Usunąć duplikację: `xml_parser.go` vs `wholesale_scout.py` | Jedna ścieżka parsowania                                     |

**Kryterium Done:** `curl localhost:1740/wholesale/scan` → zwraca wyniki z Python pipeline.

#### Etap 5: Stripe + Next.js produkcja

**Priorytet:** ŚREDNI | **Effort:** 2-3 dni

| Zadanie | Plik                                           | Opis                                                      |
| ------- | ---------------------------------------------- | --------------------------------------------------------- |
| 5.1     | `micro-saas/.env.local`                        | Prawdziwe Stripe klucze (test mode)                       |
| 5.2     | `micro-saas/app/api/revalidate/route.ts`       | Nowy: ISR revalidation endpoint                           |
| 5.3     | `micro-saas/app/audio-premium/[slug]/page.tsx` | Zamienić mock `getWholesaleProduct()` na fetch z API 8001 |
| 5.4     | `micro-saas/app/api/checkout/route.ts`         | Weryfikacja: webhook → DB update                          |
| 5.5     | `arbitrage/payments.py`                        | Testy z prawdziwym Stripe test mode                       |

**Kryterium Done:** Checkout flow: kliknięcie KUP → Stripe → webhook → subskrypcja aktywna.

#### Etap 6: Monitoring + Logging

**Priorytet:** ŚREDNI | **Effort:** 1-2 dni

| Zadanie | Plik                             | Opis                                                     |
| ------- | -------------------------------- | -------------------------------------------------------- |
| 6.1     | `monitoring/grafana/dashboards/` | Dashboard JSON: API latency, deals/hour, oracle accuracy |
| 6.2     | `monitoring/promtail/`           | Konfiguracja log shipping                                |
| 6.3     | `docker-compose.prod.yml`        | Dodać Grafana + Loki + Promtail serwisy                  |
| 6.4     | `arbitrage/api.py`               | Structured logging (JSON format)                         |

**Kryterium Done:** Grafana dashboard pokazuje live KPIs z ostatnich 24h.

---

### ═══ TRIAD 3: OPTYMALIZACJA (Produkcja) ═══

#### Etap 7: CI/CD Pipeline

**Priorytet:** WYSOKI | **Effort:** 1 dzień

| Zadanie | Plik                           | Opis                                                  |
| ------- | ------------------------------ | ----------------------------------------------------- |
| 7.1     | `.github/workflows/test.yml`   | Push → pytest + Go test + type check                  |
| 7.2     | `.github/workflows/deploy.yml` | Main merge → Docker build + push                      |
| 7.3     | `.github/workflows/lint.yml`   | Ruff/Flake8 + golangci-lint                           |
| 7.4     | `Makefile`                     | `make test`, `make lint`, `make build`, `make deploy` |

**Kryterium Done:** PR merge → auto test → auto deploy → zero human intervention.

#### Etap 8: Ads Automation ("Sniper-9") + Google Indexing

**Priorytet:** NISKI (ROI amplifier) | **Effort:** 3-4 dni

| Zadanie | Plik                                 | Opis                                                     |
| ------- | ------------------------------------ | -------------------------------------------------------- |
| 8.1     | Nowy: `arbitrage/sniper.py`          | Google Ads API integration, auto-campaign z deals        |
| 8.2     | `internal/indexing/google_api.go`    | Hook do Mass Generator → auto-submit URLs                |
| 8.3     | Nowy: `arbitrage/indexing_bridge.py` | Python wrapper: POST do Go `/index` endpoint             |
| 8.4     | `n8n-*.json`                         | Workflow: deal wykonany → Google Ads kampania → tracking |

**Kryterium Done:** Nowy deal z marżą >25% → auto-kampania Google Ads → strona zaindeksowana w <48h.

#### Etap 9: Bio-Feedback 528Hz + Harmonia Bridge

**Priorytet:** NISKI (UX polish) | **Effort:** 2 dni

| Zadanie | Plik                               | Opis                                                |
| ------- | ---------------------------------- | --------------------------------------------------- |
| 9.1     | `config/design-tokens.css`         | Dynamiczne tokeny reagujące na stan systemu         |
| 9.2     | `harmonia-dashboard/app.js`        | Bridge do `dashboard/index.html` — unifikacja       |
| 9.3     | `dashboard/index.html`             | Bio-feedback panel: pulsacja 528Hz = system healthy |
| 9.4     | Nowy: `scripts/harmonia_bridge.py` | API proxy: Harmonia ↔ Arbitrage                     |

**Kryterium Done:** Dashboard dynamicznie zmienia kolory/pulsację w zależności od stanu autopojeza.

---

## V. MAPA ZALEŻNOŚCI ETAPÓW

```
Etap 1 (Dane)──────┐
                    ├──→ Etap 4 (Go↔Python) ──→ Etap 8 (Ads+Indexing)
Etap 2 (DB) ───────┤
                    ├──→ Etap 5 (Stripe) ──────→ Etap 9 (Bio-Feedback)
Etap 3 (Testy) ────┘
                    └──→ Etap 6 (Monitoring) ──→ Etap 7 (CI/CD)
```

Etapy 1-3 są niezależne i mogą być realizowane równolegle.
Etap 7 (CI/CD) powinien być wdrożony jak najwcześniej — można go zacząć razem z Etapem 3.

---

## VI. SZACUNEK CZASOWY

| Faza          | Etapy                  | Dni robocze | Kumulatywnie |
| ------------- | ---------------------- | ----------- | ------------ |
| Stabilizacja  | 1 + 2 + 3 (równolegle) | 5           | 5            |
| Integracja    | 4 + 5 + 6              | 7           | 12           |
| Optymalizacja | 7 + 8 + 9              | 6           | 18           |

**~18 dni roboczych** do w pełni produkcyjnego systemu (przy założeniu 1 developer, 6h/dzień).

---

## VII. CO JEST GOTOWE (nie wymaga pracy)

| Komponent                                                | Ocena  | Notatka                                     |
| -------------------------------------------------------- | ------ | ------------------------------------------- |
| ✅ Pipeline Scout → Analyze → Bid → XRP                  | 85/100 | Pełny cykl freelance                        |
| ✅ Pipeline Wholesale Scout → Oracle → Quantum → Execute | 80/100 | Singularity Run działa (mock)               |
| ✅ Mass Generator → JSON manifest → Next.js SSG          | 80/100 | 9 produktów, 5 kanałów                      |
| ✅ Dashboard: Toroidal + Oracle + XRP panels             | 75/100 | Kompletny UI                                |
| ✅ 25+ API endpoints (stdlib, no Flask)                  | 75/100 | Brak auth                                   |
| ✅ Quantum Module (Łukasiewicz 3-state)                  | 85/100 | Przetestowany                               |
| ✅ Oracle (4-layer prediction)                           | 75/100 | DORMANT bez historii cen                    |
| ✅ Design System (CSS tokens + quantum-flux)             | 80/100 | φ ratio + 3-6-9                             |
| ✅ Payments (Stripe 3-tier)                              | 70/100 | Kod gotowy, brak testów z prawdziwym Stripe |
| ✅ Dokumentacja (18 docs + 40 progress)                  | 90/100 | Nadmiarowa ale kompletna                    |
| ✅ Threat Model (12 wektorów A-01→A-12)                  | 85/100 | Symulacja security_simulation.py            |
| ✅ RAG Engine (DE/PL/AT/CH markets)                      | 70/100 | TypeScript, brak integracji                 |

---

## VIII. CO NIE DZIAŁA (wymaga pracy)

| Komponent                          | Problem                           | Etap naprawy |
| ---------------------------------- | --------------------------------- | ------------ |
| ❌ Prawdziwe dane z hurtowni       | Tylko mock                        | Etap 1       |
| ❌ PostgreSQL produkcyjny          | SQLite only                       | Etap 2       |
| ❌ Unit testy                      | 4 pliki, ~40 asercji, 0% coverage | Etap 3       |
| ❌ Go↔Python bridge                | Martwy kod Go                     | Etap 4       |
| ❌ Stripe checkout flow            | Nigdy nie testowany               | Etap 5       |
| ❌ Monitoring (Grafana/Loki)       | Puste katalogi                    | Etap 6       |
| ❌ CI/CD pipeline                  | Zero automatyzacji                | Etap 7       |
| ❌ Google Ads automation           | Spec istnieje, zero kodu          | Etap 8       |
| ❌ Harmonia↔Dashboard bridge       | Dwa osobne dashboardy             | Etap 9       |
| ⚠️ API Authentication              | Brak auth na żadnym endpoint      | Etap 5       |
| ⚠️ Rate limiting                   | Brak                              | Etap 6       |
| ⚠️ Error recovery (non-autopojeza) | Brak retry logic w scout/oracle   | Etap 3       |

---

## IX. MIKRO-STRESZCZENIE (9 × 3 słowa)

1. Mocna logika biznesowa
2. Słaba infrastruktura produkcyjna
3. Mock dane wszędzie
4. SQLite blokuje skalowanie
5. Go kod martwy
6. Testy prawie nieistniejące
7. Dashboard kompletny wizualnie
8. Dokumentacja nadmiarowo bogata
9. Osiemnaście dni dokończenia
