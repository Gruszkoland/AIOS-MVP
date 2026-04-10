# OPENROUTER DEPLOYMENT SCHEMA — ADRION 369 v4.0

**Schemat wdrożenia w pełni zautomatyzowanego z checklistą dla użytkownika**

> **Cel:** Przełączenie z lokalnego Ollama (wymaga 16GB GPU) na OpenRouter API (libre, bez GPU)
> **Czas:** ~40 minut (większość automatyczna)
> **Koszt:** $0/miesiąc (model Llama 3.1 8B darmowy)
> **Ryzyko:** Niskie (kod już istnieje, tylko zmiana konfiguracji)

---

## 🎯 ARCHITEKTURA

### Bieżący Stan

```
User Request → arbitrage.llm.chat()
              ↓
         LLM_BACKEND=ollama
              ↓
         Local Ollama (16GB GPU)
              ↓
         Response
```

### Stan Docelowy

```
User Request → arbitrage.llm.chat()
              ↓
         LLM_BACKEND=openrouter
              ↓
         OpenRouter API (free tier)
              ↓
         Response (1-3 sec latency)
```

### Kod już obsługuje OpenRouter!

```python
# arbitrage/llm.py — linia 272
def _openrouter_chat(prompt: str, model: str = None, system: str = "") -> str:
    """Fully implemented, just needs API key."""
```

---

## 📋 FAZA 1: REJESTRACJA (5 minut) — RĘCZNIE

### Krok 1.1: Utwórz konto

```
1. Wejdź na: https://openrouter.ai/
2. Kliknij "Sign Up"
3. Email + Hasło
4. Potwierdź email
5. Dashboard → Settings → "API Keys"
6. Kliknij "Generate API Key"
7. SKOPIUJ: sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxx
```

### Krok 1.2: Zmienne walidacji

Klucz powinien:

- ✅ Zaczynać się od `sk-or-v1-`
- ✅ Mieć ~40-60 znaków
- ✅ Być unikalny (nie udostępniaj)

**USER ACTION:** Zdobądź klucz + przechowuj bezpiecznie

---

## 📝 FAZA 2: KONFIGURACJA (5 minut) — RĘCZNA + AUTO

### Krok 2.1: Edytuj `.env`

```bash
# Plik: .env (linia ~71)

# STARA KONFIGURACJA:
# LLM_BACKEND=ollama
# LLM_MODEL=deepseek-coder-v2:16b

# NOWA KONFIGURACJA:
LLM_BACKEND=openrouter
LLM_MODEL=meta-llama/llama-3.1-8b-instruct:free
OPENROUTER_API_KEY=sk-or-v1-WKLEJ_TUTAJ_KLUCZ

# Opcjonalne: dostrajanie
LLM_TEMPERATURE=0.2
LLM_TOP_P=0.9
```

### Krok 2.2: Automatyczna walidacja

```bash
python -c "
from arbitrage.config import LLM_BACKEND, OPENROUTER_KEY, LLM_MODEL
print(f'✅ Backend: {LLM_BACKEND}')
print(f'✅ Model: {LLM_MODEL}')
print(f'✅ API Key set: {bool(OPENROUTER_KEY)}')
assert LLM_BACKEND == 'openrouter'
"

# Oczekiwane:
# ✅ Backend: openrouter
# ✅ Model: meta-llama/llama-3.1-8b-instruct:free
# ✅ API Key set: True
```

**USER ACTION:** Edytuj .env + uruchom walidację

---

## ✅ FAZA 3: WERYFIKACJA KODU (2 minuty) — AUTO

### KOD JUŻ ISTNIEJE!

```bash
grep -n "_openrouter_chat" arbitrage/llm.py
# WYNIK: 272:def _openrouter_chat(prompt: str, model: str = None, system: str = "") -> str:
```

**STATUS:** ✅ Żadnych zmian w kodzie nie potrzeba

---

## 🧪 FAZA 4: TESTOWANIE (10 minut) — RĘCZNE

### Test 4.1: Bezpośredni Python

```bash
cd c:\Users\adiha\162\ demencje\ w\ schemacie\ 369
.venv\Scripts\Activate.ps1

python -c "
from arbitrage.llm import chat
response = chat('Co to jest 2+2?', force_backend='openrouter')
print(f'✅ Odpowiedź: {response}')
"

# Oczekiwane: Odpowiedź w 1-3 sekundy
# ✅ Odpowiedź: 2+2 = 4
```

### Test 4.2: API Endpoint

```bash
# Terminal 1: Start server
cd arbitrage
python -c "from arbitrage_server import app; app.run(port=8001)"

# Terminal 2: Test
curl -X POST http://localhost:8001/api/arbitrage/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "job_title": "YouTube editing",
    "budget_usd": 500,
    "description": "Professional video editing"
  }'

# Oczekiwane:
# {"score": 8.5, "recommendation": "BID", "confidence": 0.92}
```

**USER ACTION:** Uruchom testy

---

## 🐳 FAZA 5: DOCKER (15 minut) — AUTOMATYCZNA

### Script wdrożenia:

```bash
bash scripts/deploy_openrouter.sh
```

### Co robi skrypt:

1. ✅ Pyta o API Key
2. ✅ Aktualizuje .env
3. ✅ Buduje Docker obraz
4. ✅ Startuje kontener
5. ✅ Czeka na health check
6. ✅ Testuje endpoint
7. ✅ Wyświetla status

**USER ACTION:** Uruchom skrypt + obserwuj logi

---

## 📊 FAZA 6: WERYFIKACJA PERFORMANCE (opcje, 10 min)

### Latencja

```bash
curl -X POST http://localhost:8001/api/arbitrage/analyze \
  -H "Content-Type: application/json" \
  -w "\nCzas: %{time_total}s\n" \
  -d '{"job_title": "Test", "budget_usd": 200, "description": "Test"}'

# Oczekiwane:
# Czas: 1.5s (pierwszy request)
# Czas: 0.8s (cache)
```

### Dokładność

```
Testuj 3-5 promptów, weryfikuj czy wyniki są rozsądne:
✅ Wysoka wartość ($5000+) → score 9+
✅ Niska wartość ($50) → score 4-6
✅ Niejasny opis → niska pewność
✅ Idealne dopasowanie → score 9.5+
```

---

## ⏮️ PLAN COFNIĘCIA (jeśli coś nie działa)

### Rollback na Ollama:

```bash
# .env
LLM_BACKEND=ollama

# Restart
docker-compose -f docker-compose.cloud.yml restart adrion-api
```

### Fallback na Mock (testing):

```bash
# .env
LLM_BACKEND=mock
```

---

## 📋 CHECKLIST WDROŻENIA

```
SETUP:
[ ] Konto OpenRouter utworzone
[ ] API Key wygenerowany
[ ] API Key test curl (200 OK)

KONFIGURACJA:
[ ] .env: LLM_BACKEND=openrouter
[ ] .env: OPENROUTER_API_KEY=sk-or-v1-xxx
[ ] .env: LLM_MODEL=meta-llama/llama-3.1-8b-instruct:free
[ ] Python config załadowany bez błędów

WERYFIKACJA KODU:
[ ] arbitrage/llm.py ma _openrouter_chat()
[ ] Żadne zmiany w kodzie nie potrzebne

TESTOWANIE:
[ ] Python test działa
[ ] API endpoint zwraca valid JSON
[ ] Model name jest poprawny w response

DOCKER:
[ ] docker-compose build OK
[ ] docker-compose up -d OK
[ ] Health check PASS
[ ] Brak błędów w logach

MONITORING:
[ ] Latencja 1-3 sec (OK)
[ ] Jakość odpowiedzi (OK)
[ ] Brak rate limiting
[ ] Status $0 (free tier)

ROLLBACK (przygotowanie):
[ ] Plan cofnięcia dokumentowany
[ ] Ollama dostępne (jeśli potrzebne)
[ ] Mock mode test OK
```

---

## ⏱️ TIMELINE

| Faza            | Czas           | Automatyka    |
| --------------- | -------------- | ------------- |
| 1. Setup        | 5 min          | Ręczna        |
| 2. Konfiguracja | 5 min          | Ręczna + Auto |
| 3. Kod          | 2 min          | Auto          |
| 4. Testy        | 10 min         | Ręczna        |
| 5. Docker       | 15 min         | Auto          |
| 6. Performance  | 10 min         | Opcje         |
| **RAZEM**       | **~40-50 min** | **80% AUTO**  |

---

## 🤖 FULLY AUTOMATED SCRIPT

Plik: `scripts/deploy_openrouter.sh`

**UŻYCIE:**

```bash
bash scripts/deploy_openrouter.sh
```

**Co robi:**

1. 🔑 Pyta o API Key
2. 📝 Aktualizuje .env (sed)
3. ✅ Waliduje config (Python)
4. 🔌 Testuje OpenRouter API (curl)
5. 🐳 Buduje Docker (no-cache)
6. ▶️ Startuje service
7. ⏳ Czeka na health
8. 🧪 Testuje endpoint
9. 📊 Wyświetla status

---

## ✨ SUKCES — Co powinieneś zobaczyć

```
════════════════════════════════════════
✅ OpenRouter Deployment Complete!
════════════════════════════════════════

📊 Status:
  • LLM Backend: OpenRouter
  • Model: Llama 3.1 8B (free)
  • API Key: Configured
  • Service: Running

📝 Next steps:
  1. Monitor: docker-compose logs -f adrion-api
  2. Test API: curl http://localhost:8001/api/arbitrage/analyze
  3. Costs: https://openrouter.ai/usage
```

---

## 🚀 NATYCHMIASTOWE DALSZE KROKI

1. **Zdobądź API Key** (openrouter.ai) — 5 min
2. **Edytuj .env** — 5 min
3. **Uruchom skrypt deployment** — 15 min
4. **Obserwuj logi** — 5 min
5. **Test endpoint** — 2 min

**BOOM!** — Jesteś gotowy. OpenRouter działa.

---

## 📞 TROUBLESHOOTING

### "Invalid API Key format"

→ Klucz powinien zaczynać się od `sk-or-v1-`

### "Rate limited"

→ Free tier: 20-50 req/min. Jeśli potrzebujesz więcej: paid tier na OpenRouter

### "Timeout (5+ sec)"

→ OpenRouter działa wolno. Może spróbować inny model albo czekać

### "Build fails"

→ `docker-compose build --no-cache adrion-api` ponownie

### "API returns error"

→ Sprawdź: .env, API Key, model name, logi: `docker-compose logs -f`

---

**WERSJA:** 1.0
**DATA:** 06-04-2026
**STATUS:** READY FOR DEPLOYMENT ✅
