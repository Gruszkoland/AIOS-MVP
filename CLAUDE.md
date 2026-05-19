# CLAUDE.md — Root (Global Preferences)

> **Updated:** 2026-04-11 | Loaded at every conversation start across all projects.

## Projects

| Project                | Path                                                     | Framework                             | Status                |
| ---------------------- | -------------------------------------------------------- | ------------------------------------- | --------------------- |
| **ADRION 369**         | `162 demencje w schemacie 369/`                          | Flask Blueprints + Go Echo + Pydantic | Active (v4.0, 75/100) |
| **AI-Agent-OS**        | `Documents/GitHub/AI-Agent-OS`                           | Flask (alpha)                         | Maintenance           |
| **Lokal_AI_Ecosystem** | `Documents/GitHub/Lokal_AI_Ecosystem/local-ai-ecosystem` | FastAPI + Ollama + ChromaDB           | Active                |

---

## ADRION 369 (Primary Project)

> **Full project instructions in:** `162 demencje w schemacie 369/CLAUDE.md`
> That file has architecture, running, testing, checklist 75→100, and critical rules.

### Quick Reference

```bash
# Run (Flask Blueprints via app factory — the ONLY correct entry point)
cd "162 demencje w schemacie 369"
python wsgi.py                          # http://localhost:8003

# Test
python -m pytest tests/ -q --cov=arbitrage --cov-fail-under=80
go test ./... -v

# API docs
open http://localhost:8003/api/docs     # Swagger UI
```

### Architecture: Trinity-EBDI 162D Decision Framework

```
Flask App Factory (arbitrage/app.py)
  |-- 5 Blueprints (arbitrage, quantum, oracle, wholesale, payments)
  |-- Guardian Laws Engine (9 laws, CRITICAL=instant DENY)
  |-- Trinity Score (Material/Intellectual/Essential)
  |-- Circuit Breaker + Rate Limiter + LLM Canary
  |
UAP Orchestrator (uap/backend/api.py, port 8002)
  |-- 6 AI Personas (Librarian, SAP, Auditor, Sentinel, Architect, Healer)
  |
Go Vortex (cmd/vortex-server/main.go, port 1740)
  |-- EBDI state, digital root oracle, 174Hz resonance
```

### Key Rules

- Entry point: `wsgi.py` → `arbitrage.app.create_app()` (**NOT** `arbitrage_server.py`)
- Config: `arbitrage.config.settings.*` (Pydantic BaseSettings, NOT raw `os.getenv`)
- SQL: parameterized only (`?` placeholders), NEVER f-strings
- Guardian Laws source of truth: `docs/GUARDIAN_LAWS_CANONICAL.json`
- Coverage gates: Python >= 80%, Go >= 80%

---

## Lokal_AI_Ecosystem

### Running

```bash
cd Documents/GitHub/Lokal_AI_Ecosystem/local-ai-ecosystem
docker-compose up -d --build
# or: ./setup.sh
```

Access: UI → http://localhost:8080 | API → http://localhost:8000 | Ollama → http://localhost:11434

### Testing

```bash
python -m pytest tests/ -v
```

### Architecture

```
Browser → Nginx → FastAPI (main.py) → ChromaDB + SentenceTransformers (RAG)
                                    → Ollama (LLM inference)
                                    → pynvml (GPU telemetry)
```

**Key API endpoints** (`main.py`):

- `POST /api/chat/stream` — SSE streaming LLM responses
- `POST /api/upload` — ingest PDF/TXT into RAG
- `GET /api/telemetry` — VRAM usage and GPU temperature
- `POST /api/session-title` — AI-generated chat session names

**Dependencies:** `fastapi`, `uvicorn`, `chromadb`, `sentence-transformers`, `langchain`, `nvidia-ml-py`, `sqlalchemy`

---

## Workflow Rules (All Projects)

> **Updated:** 2026-04-13 | Obowiązują we wszystkich projektach i sesjach.

### 1. Plan Mode First (Tryb planowania)

**ZASADA:** Zanim napiszesz choć jedną linię kodu, ZAWSZE najpierw:
- Przedstaw architekturę rozwiązania w pseudokodzie
- Wypisz listę plików do modyfikacji/utworzenia
- Opisz zmiany w schemacie bazy danych (jeśli dotyczy)
- Wypisz nowe endpointy / zmiany w API (jeśli dotyczy)
- Wskaż walidację po stronie front-endu (jeśli dotyczy)

Dopiero po jawnym potwierdzeniu użytkownika („OK", „Tak", „Akceptuję") przejdź do implementacji.
Używaj narzędzia `EnterPlanMode` dla każdego nietrywalnego zadania.

### 2. Sub-agenci dla złożonych problemów

**ZASADA:** Przy złożonych zadaniach (refaktoryzacja modułu, analiza dużych plików, wieloetapowe migracje):
- Deleguj wyspecjalizowane fragmenty do sub-agentów za pomocą narzędzia `Agent`
- Główny kontekst zajmuje się architekturą i koordynacją
- Sub-agenci wykonują wyizolowane zadania (np. „przeanalizuj ten plik pod kątem wycieków pamięci")
- To zapobiega „zapominaniu" fragmentów kodu przy długich konwersacjach

### 3. Pętla lekcji (lessons.md)

**ZASADA:** Na początku każdej sesji roboczej przeczytaj `tasks/lessons.md` i stosuj się do zapisanych lekcji.
- Po każdym istotnym błędzie lub odkryciu — dopisz nową lekcję do pliku
- Format: `Lekcja N: [opis problemu] → [rozwiązanie/reguła]`
- Lekcje mają priorytet nad domyślnymi zachowaniami

### 4. Autonomiczne naprawianie błędów

**ZASADA:** Jeśli testy nie przechodzą lub pojawia się błąd:
- NIE pytaj użytkownika co robić
- Przeanalizuj logi błędów (stdout, stderr, pliki logów)
- Znajdź przyczynę źródłową (root cause)
- Zaproponuj i wdróż gotową poprawkę
- Uruchom testy ponownie aby potwierdzić naprawę
- Dopiero jeśli po 2 próbach naprawy problem nadal istnieje — zapytaj użytkownika
