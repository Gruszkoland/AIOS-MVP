# ADRION 369 v2.0 - 3x3x3 DEPLOYMENT CHECKLIST

Ten dokument stanowi ostateczną weryfikację gotowości systemu w oparciu o strukturę Trójcy (Trinity), zapewniającą równowagę między zasobami, logiką a misją.

---

## 🏗️ FILAR I: MATERIAL (Infrastructure & Execution)

### 1. Konteneryzacja & Swarm

- [ ] **Docker Orchestration**: Sprawdzenie czy wszystkie serwisy (postgres, ollama, n8n, adrion-core) są w trybie `running`.
  - _Weryfikacja_: `docker ps --format "table {{.Names}}\t{{.Status}}"`
- [ ] **Volume Persistence**: Potwierdzenie zamontowania wolumenów dla `postgres_data` i `ollama_data`.
  - _Weryfikacja_: `docker volume inspect adrion-swarm_postgres_data`
- [ ] **Resource Limits**: Limit CPU/RAM dla serwera Ollama (DeepSeek 16B wymaga min. 24GB VRAM/Shared RAM).
  - _Weryfikacja_: `docker stats --no-stream`

### 2. Go Sentinel (Core Runtime)

- [ ] **Binary Stability**: Kompilacja `vortex-server` bez błędów typu `panic`.
  - _Weryfikacja_: `go build -o bin/vortex cmd/vortex-server/main.go`
- [ ] **Port Availability**: Porty 11434 (Ollama), 5432 (DB), 8080 (API) są otwarte i nasłuchują.
  - _Weryfikacja_: `netstat -ano | findstr "8080"`
- [ ] **Dependency Check**: Wszystkie moduły w `go.mod` są pobrane i zaktualizowane.
  - _Weryfikacja_: `go mod tidy`

### 3. Financial Gateways (Stripe & XRP)

- [ ] **Stripe Webhooks**: Klucz `STRIPE_SECRET` jest poprawnie załadowany i endpoint `/webhook` reaguje na testy.
  - _Weryfikacja_: `stripe trigger payment_intent.succeeded`
- [ ] **XRP Ledger Sync**: Tracker XRP widzi najnowsze Ledger Index-y.
  - _Weryfikacja_: Logi w `arbitrage/xrp_tracker.py`
- [ ] **Fiat/Crypto Balance**: Sprawdzenie czy `arbitrage/payments.py` poprawnie przelicza kursy.
  - _Weryfikacja_: Test jednostkowy `pytest tests/test_payments.py`

---

## 🧠 FILAR II: INTELLECTUAL (Logic & Monitoring)

### 1. Vortex Oracle (AI Logic)

- [ ] **Model Availability**: DeepSeek-Coder-V2 jest poprawnie załadowany w Ollama.
  - _Weryfikacja_: `ollama list`
- [ ] **Inference Latency**: Odpowiedź Oracle na prompt testowy w czasie < 2s.
  - _Weryfikacja_: `/arbitrage/oracle.py` (pomiar czasu w logach)
- [ ] **Predictive Accuracy**: Weryfikacja wag w `quantum.py` pod kątem optymalizacji arbitrażu.
  - _Weryfikacja_: Symulacja `_check_db.py`

### 2. 174Hz Signal & Resiliency

- [ ] **Healthcheck Loop**: Monitorowanie cyklu 174Hz (stabilizacja) dla mikroserwisów.
  - _Weryfikacja_: `curl http://localhost:8080/health`
- [ ] **Circuit Breaker**: System wyłącza bidding przy wykryciu anomalii (Logic Stress).
  - _Weryfikacja_: Ręczne przerwanie kontenera DB i obserwacja reakcji `sentinel`.
- [ ] **Log Rotation**: Genesis Record loguje błędy bez przepełniania dysku.
  - _Weryfikacja_: `ls -lh "Genesis Record/"`

### 3. Monitoring Stack (Loki/Grafana)

- [ ] **Loki Ingestion**: Logi z Pythona i Go trafiają do kontenera Loki.
  - _Weryfikacja_: Zapytanie `logcli` lub widok w Grafanie.
- [ ] **KPI Dashboard**: Dashboard "ADRION 369" pokazuje aktywne transakcje i ROI.
  - _Weryfikacja_: Otwórz `http://localhost:3000` (Grafana).
- [ ] **Alerting Rules**: Alerty Slack/Telegram skonfigurowane dla błędów P1.
  - _Weryfikacja_: `curl -X POST http://localhost:9093/api/v1/alerts ...`

---

## ✨ FILAR III: ESSENTIAL (Laws & Narrative)

### 1. Guardian Laws Compliance (G1-G9)

- [ ] **Privacy Audit (G7)**: Brak wycieku danych (ID, klucze) poza `localhost` w logach.
  - _Weryfikacja_: `grep -r "sk_live" .`
- [ ] **Sustainability Check (G9)**: Kod nie zawiera pętli blokujących (async logic everywhere).
  - _Weryfikacja_: Statyczna analiza `pylint arbitrage/`.
- [ ] **Transparency (G5)**: Każda decyzja Oracle posiada rekord w `Genesis Record/`.
  - _Weryfikacja_: Sprawdzenie `HEALER_LOGS.txt`.

### 2. Swarm Synchronization

- [ ] **Persona Alignment**: Sprawdzenie czy agent `AUDITOR` posiada wagę T=0.1 w `config/personas.yml`.
  - _Weryfikacja_: `cat config/personas.yml`.
- [ ] **Trinity Weighting**: Wagi perspectives w `trinity-weights.yml` sumują się do 1.0.
  - _Weryfikacja_: Manualna suma z pliku konfiguracyjnego.
- [ ] **Knowledge Base Sync**: `AIDER_CORE_KNOWLEDGE.txt` zawiera najnowsze zmiany architektoniczne.
  - _Weryfikacja_: Porównanie daty edycji z ostatnim commitem.

### 3. AMPLIFIER & Communication

- [ ] **LinkedIn Draft**: Wygenerowanie posta o sukcesie wdrożenia v2.0 (zgodnie z G6 - Authenticity).
  - _Weryfikacja_: `@amplifier generate draft`.
- [ ] **Metrics Verification**: Dane do posta pobrane bezpośrednio z `KPI_DASHBOARD_TEMPLATE.csv`.
  - _Weryfikacja_: Porównanie liczb w drafcie z CSV.
- [ ] **Public Narrative Guard**: Post nie zawiera technicznych detali naruszających G7 (Privacy).
  - _Weryfikacja_: Recenzja przez agenta `SENTINEL`.

---

**Podpisano**: Rój Agentów ADRION 369
**Data**: 2026-04-01
\*\*,filePath:
