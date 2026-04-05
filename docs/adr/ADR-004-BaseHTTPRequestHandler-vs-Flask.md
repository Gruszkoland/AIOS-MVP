# ADR-004: BaseHTTPRequestHandler zamiast Flask/FastAPI

**Status:** ZAAKCEPTOWANY
**Data:** 2025-Q4 | Rewizja rozważana: Q2 2026
**Autor:** ADRION Core Team

---

## Kontekst

`arbitrage/api.py` potrzebuje prostego HTTP servera dla ArbitrageHandler.
30+ endpointów: GET (status, kpis, jobs, quantum) + POST (scout, cycle, checkout, webhook).

Analizowane opcje:

| Framework                  | Zależności        | Async    | Middleware | Testowalność |
| -------------------------- | ----------------- | -------- | ---------- | ------------ |
| **BaseHTTPRequestHandler** | stdlib (0)        | ❌       | ❌ własna  | ✅ łatwa     |
| Flask                      | flask ~2MB        | partial  | ✅ bogaty  | ✅           |
| FastAPI                    | fastapi + uvicorn | ✅ pełny | ✅ bogaty  | ✅           |
| aiohttp                    | aiohttp           | ✅ pełny | ✅         | ✅           |

## Decyzja

**`BaseHTTPRequestHandler`** z Python stdlib.

Uzasadnienie: w momencie decyzji priorytetem było zero-dependency dla core layer
i maksymalna kontrola nad lifecycle requestu (szczególnie dla rate-limiting).

```python
class ArbitrageHandler(BaseHTTPRequestHandler):
    def do_GET(self): ...
    def do_POST(self): ...
    # Lazy imports: _db(), _scout(), _config() itp.
```

## Konsekwencje

### Plusy

- 0 dodatkowych zależności dla core API layer
- Pełna kontrola nad request/response lifecycle
- Lazy imports umożliwiają module-level mockowanie w testach
- Prostota: 1 plik, czytelny routing

### Minusy / Ryzyki

- Brak middleware (auth, CORS, compression, request validation)
- Synchronous only — brak async/await → bottleneck przy concurrent requests
- **Windows TCP RST**: przy rate-limiting server zamyka socket bez odczytania body
  → klient dostaje `ConnectionAbortedError` (workaround: `_rate_lim_post()` w testach)
- Własna implementacja routingu → więcej kodu do maintenance

## Punkt rewizji

Przy skalowaniu powyżej **100 RPS** lub dodaniu auth middleware → migracja na FastAPI.

Sygnały do migracji:

- [ ] P95 latency > 200ms pod obciążeniem
- [ ] Potrzeba OAuth2/JWT middleware
- [ ] Potrzeba WebSocket lub SSE

## Powiązane ADR

- Brak bezpośrednich; wpływa na architekturę testów (`tests/test_api_integration.py`)
