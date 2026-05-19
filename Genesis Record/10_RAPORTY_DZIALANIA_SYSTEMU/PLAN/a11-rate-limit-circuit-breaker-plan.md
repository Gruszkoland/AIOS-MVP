# PLAN: A-11 Fix — Rate Limit + Circuit Breaker

**Data:** 2026-04-02  
**Cel:** Naprawić lukę A-11 (Harm-Omission) w moście Go-Python agenta ADRION 369.

---

## Kontekst

Security Audit wykazał:
- **A-11 (Harm-Omission)** | 🟡 WARN | Brak rate-limit na `/api/arbitrage/quantum/decide`  
- Bez limitowania, przy wysokim obciążeniu (np. atak lub błąd pętlowy) może dojść do kaskadowego przeciążenia i blokady całego systemu.  
- Brak Circuit Breakera dla zapytań do Go Sentinel → `quantum.py` bez zabezpieczenia przed lawiną failover-ów.

---

## Kroki Wykonawcze

| # | Krok | Cel | Kryterium ukończenia | Zależności | Priorytet | Status |
|---|------|-----|---------------------|------------|-----------|--------|
| 1 | Utwórz plan | Dokumentacja zamiaru | Ten plik istnieje | — | P0 | `done` |
| 2 | Dodaj `_SlidingWindowRateLimiter` do `api.py` | Chronić endpoint `/quantum/decide` przed zalaniem | Max 30 req/min/IP; 429 gdy przekroczony | — | P1 | `done` |
| 3 | Zastosuj limiter w `_handle_quantum_decide` i `_handle_quantum_scan` | Blokowanie na poziomie HTTP | Handler zwraca `{"error":"Rate limit exceeded"}` z HTTP 429 | Krok 2 | P1 | `done` |
| 4 | Dodaj `_CircuitBreaker` do `quantum.py` | Zapobiec kaskadowym timeout-om przy niedostępnym Go Sentinel | Po 5 błędach → circuit OPEN / skoki do fallback na 30s | — | P1 | `done` |
| 5 | Zintegruj breaker w `quantum_decide()` | Logikal trójwartościowa + ochrona przed avalanche | Brak prób HTTP przy OPEN circuit | Krok 4 | P1 | `done` |
| 6 | Zaktualizuj `SECURITY_AUDIT_REPORT.md` | Zmień status A-11 na 🟢 SAFE | Wiersz tabeli zaktualizowany | Kroki 2-5 | P2 | `done` |
| 7 | Utwórz raport końcowy w REPORTS/ | Audit Trail w Genesis Record | Plik REPORTS/ istnieje z werdyktem | Wszystkie | P2 | `done` |
| 8 | Parametryzuj przez `.env` | Umożliwić tuning bez zmian kodu | Limity i breaker czytane z env z fallbackiem | Kroki 2-5 | P1 | `done` |

---

## Architektura Rozwiązania

### Rate Limiter (api.py)
```
Klient → HTTP POST /quantum/decide
    → _SlidingWindowRateLimiter.is_allowed(client_ip)?
        NIE → HTTP 429 {"error": "Rate limit exceeded", "retry_after": 60}
        TAK → _handle_quantum_decide() (normalny przepływ)
```

**Parametry:**
- `max_requests = 30` zapytań
- `window_seconds = 60.0` sekund
- Klucz: IP klienta (`self.client_address[0]`)
- Thread-safe: `threading.Lock`

### Circuit Breaker (quantum.py)
```
use_sentinel=1 → _sentinel_breaker.is_open()?
    OPEN  → skip HTTP call → Python fallback (natychmiast)
    CLOSED/HALF-OPEN → requests.post(..., timeout=0.174)
        OK  → _sentinel_breaker.record_success()
        ERR → _sentinel_breaker.record_failure()
            failures >= 5 → circuit OPEN na 30s
```

**Parametry:**
- `failure_threshold = 5`  
- `recovery_timeout = 30.0` sekund
- Loguje ostrzeżenie przy OPEN: `Circuit Breaker OPEN — Sentinel Go offline`

---

## Prawa Strażnika

- **G8 (Nonmaleficence)**: Aktywna ochrona przed przeciążeniem ✅  
- **G9 (Sustainability)**: System pozostaje stabilny przy awaryjnym Go ✅  
- **G2 (Harmony)**: Płynna degradacja (fallback) bez przerwy w działaniu ✅  
