# Dashboard ADRION 369 - Funkcjonalnosci

## 1) Architektura

Dashboard sklada sie z:

- frontend UI: `dashboard/index.html`
- backend HTTP: `server.py`
- runtime kontenerowy: `docker-compose.prod.yml`

Frontend i backend dashboardu dzialaja jako jedna usluga `adrion-dashboard` (port 9000).
Silnik arbitrage API dziala jako `adrion-api` (port 8001).

## 2) Najwazniejsze funkcje operacyjne

### Runtime i zdrowie stosu

- Odczyt statusu Ollama: `GET /api/ollama/status`
- Odczyt informacji systemowych dashboardu: `GET /api/system/info`
- Odczyt metadanych kontenerow: `GET /api/runtime/stack`
- Restart runtime z UI: `POST /api/runtime/restart` z target:
  - `stack`
  - `api`
  - `dashboard`

### Logi i obserwowalnosc

- Odczyt logow sesji i audytu: `GET /api/genesis/logs`
- Monitoring services (Loki, Promtail, Grafana) raportowany w UI przez `runtime/stack`.

### Arbitrage/XRP

- KPI i progres XRP: `GET /api/arbitrage/stats`
- Lista jobow: `GET /api/arbitrage/jobs`
- Pending bids: `GET /api/arbitrage/bids`
- Uruchomienie cyklu: `POST /api/arbitrage/cycle`
- Rejestrowanie earningu: `POST /api/arbitrage/earn`

## 3) Funkcje UI i zachowanie

### Auto-refresh

- Globalny refresh co 30s dla statusu i logow.
- Dodatkowy refresh co 15s dla sekcji arbitrage runtime.

### Karta Runtime Healthcheck

- Pokazuje stan `dashboard`, `api`, `monitoring`.
- Wylicza status zbiorczy: `ok`, `warn`, `error`.
- Koloruje karte klasami:
  - `health-ok`
  - `health-warn`
  - `health-error`

### Runtime metadata

- Pokazuje kontenery aplikacyjne i monitoringowe.
- Pokazuje mapowanie portow, status i health.
- Dynamicznie wlacza/wylacza przyciski restartu, gdy Docker control jest niedostepny.

## 4) Co jest produkcyjne vs demonstracyjne

### Produkcyjne / realnie podlaczone

- Healthcheck dashboardu i API.
- Runtime stack metadata przez Docker SDK.
- Restart stacku/API/dashboardu z poziomu UI.
- Logi Genesis z backendu.
- Integracja z endpointami arbitrage.

### Demonstracyjne / pomocnicze

- Quick actions `Start Ollama`, `Start Aider`, `Run Librarian/SAP/Auditor/AMPLIFIER` sa instrukcjami (`alert`) i nie uruchamiaja backendowego joba.
- Wbudowany chat personas ma tryb offline (mock) gdy Ollama jest niedostepna.
- Wbudowana lista zadan jest lokalna (in-memory) i nie jest trwale zapisywana po stronie serwera.

## 5) Wymagania runtime

- Docker socket podmontowany do `adrion-dashboard`:
  - `/var/run/docker.sock:/var/run/docker.sock`
- Ustawione zmienne runtime:
  - `STACK_CONTAINERS`
  - `MONITORING_CONTAINERS`
  - `DOCKER_HOST=unix:///var/run/docker.sock`
- Dostepnosc endpointu arbitrage API na porcie 8001.

## 6) Ograniczenia i ryzyka

- `Access-Control-Allow-Origin: *` ustawione globalnie w dashboard server.
- Brak autoryzacji dla endpointu restartu runtime (`/api/runtime/restart`) w obecnej implementacji.
- Czesci funkcji chat/persona opiera sie na bezposrednim fetch do `http://localhost:11434/api/generate`.

## 7) Szybki runbook operacyjny

1. Uruchom stack docker compose.
2. Sprawdz dashboard `http://127.0.0.1:9000`.
3. Zweryfikuj `Runtime Healthcheck` i runtime metadata.
4. Przy awarii uzyj `Restart API` lub `Restart Dashboard`.
5. Potwierdz powrot do statusu healthy i odswiezenie KPI arbitrage.
