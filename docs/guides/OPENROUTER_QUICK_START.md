# OpenRouter Deployment — Quick Start Guide

> **Ścieżka:** Ollama (local) → OpenRouter (cloud/free API)

## ⚡ TL;DR — 3 Kroki

```bash
# 1. Uzyskaj API Key (5 min handwork)
# https://openrouter.ai/ → Sign Up → API Keys → Generate

# 2. Uruchom deployment (Windows PowerShell)
powershell -ExecutionPolicy Bypass -File scripts/deploy_openrouter.ps1

# 3. Wklej API Key, czekaj ~15 minut, gotowe!
```

---

## 📋 Pełny Proces (30 minut)

### Faza 1: API Key (5 minut)

**Rejestracja:**

1. Wejdź na https://openrouter.ai/
2. Kliknij "Sign Up"
3. Email + Hasło (potwierdzenie email)
4. Dashboard → Settings → "API Keys"
5. Kliknij "Generate API Key"
6. **SKOPIUJ:** `sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxx`

**Walidacja:**

```bash
curl -H "Authorization: Bearer sk-or-v1-YOUR_KEY" \
  https://openrouter.ai/api/v1/models | grep -c llama-3.1

# Oczekiwane: 1 (potwierdzenie, że model dostępny)
```

---

### Faza 2: Deployment (15-20 minut)

#### WINDOWS (PowerShell)

```powershell
# Otwórz PowerShell w katalogu projektu
cd c:\Users\adiha\162\ demencje\ w\ schemacie\ 369

# Uruchom deployment script
powershell -ExecutionPolicy Bypass -File scripts/deploy_openrouter.ps1

# System poprosi o API Key
# Wklej: sk-or-v1-...
# Czekaj ~15 minut
```

#### LINUX / MAC (Bash)

```bash
cd ~/projects/adrion
bash scripts/deploy_openrouter.sh sk-or-v1-YOUR_KEY
```

---

## 🎯 Co Robi Script

### Automatyczne (nie dotykaj):

1. ✅ Waliduje format API Key
2. ✅ Aktualizuje `.env` (LLM_BACKEND, OPENROUTER_API_KEY)
3. ✅ Rebuildu Docker image (bez Ollama dependency)
4. ✅ Startuje kontener
5. ✅ Czeka na health check
6. ✅ Testuje endpoint
7. ✅ Zbiera metryki (latency, CPU, RAM)
8. ✅ Loguje do Genesis Record

### Ręczne (jeśli skrypt nie działa):

**Krok 1: Edytuj `.env` ręcznie**

```bash
# Plik: .env

# Zmień na:
LLM_BACKEND=openrouter
LLM_MODEL=meta-llama/llama-3.1-8b-instruct:free
OPENROUTER_API_KEY=sk-or-v1-YOUR_KEY_HERE
```

**Krok 2: Rebuild Docker**

```bash
docker-compose -f docker-compose.cloud.yml build --no-cache adrion-api
docker-compose -f docker-compose.cloud.yml up -d adrion-api
```

**Krok 3: Test**

```bash
curl -X POST http://localhost:8001/api/arbitrage/analyze \
  -H "Content-Type: application/json" \
  -d '{"job_title": "Test", "budget_usd": 200, "description": "Test"}'
```

---

## 📊 Status — Co Powinieneś Zobaczyć

### ✅ Sukces

```
════════════════════════════════════════
✅ OpenRouter Migration Successful!
════════════════════════════════════════

📊 Deployment Summary:
  • Backend: OpenRouter API
  • Model: Llama 3.1 8B (free)
  • Status: ✅ Running
  • Latency: 1234ms
  • Health: ✅ Healthy

📝 Next Steps:
  1. Monitor logs: docker-compose logs -f adrion-api
  2. Test API: curl http://localhost:8001/api/arbitrage/analyze
  3. Check usage: https://openrouter.ai/usage
```

### ❌ Błędy - Troubleshooting

| Błąd                     | Przyczyna                   | Rozwiązanie                                                      |
| ------------------------ | --------------------------- | ---------------------------------------------------------------- |
| `Invalid API key format` | Zły format klucza           | Klucz musi zaczynać się od `sk-or-v1-`                           |
| `Network error`          | Brak internetu lub API down | Sprawdź połączenie, spróbuj https://openrouter.ai w przeglądarce |
| `Build fails`            | Docker issue                | `docker-compose build --no-cache` ponownie                       |
| `Service timeout`        | Kontener nie startuje       | `docker-compose logs -f` → sprawdź logi                          |
| `Rate limited`           | Zbyt wiele requestów        | Free tier: 20-50 req/min; subscrybuj PAID tier                   |

---

## 🔄 Rollback (Powrót na Ollama)

Jeśli OpenRouter nie działa:

```bash
# Przywróć backup
copy .env.backup.openrouter .env

# Zmień na Ollama
# Edytuj .env:
LLM_BACKEND=ollama
LLM_MODEL=deepseek-coder-v2:16b

# Restart
docker-compose restart adrion-api

# Czekaj ~5 minut (Ollama model loaduje)
```

---

## 💰 Koszty

| Plan          | Koszt     | Req/min   | Model           |
| ------------- | --------- | --------- | --------------- |
| **Free Tier** | $0        | 20-50     | Llama 3.1 8B ✅ |
| STARTER       | $5-10/mo  | Unlimited | GPT-4 Turbo     |
| PRO           | $20-50/mo | Unlimited | Claude 3 Opus   |

**My default:** Start free, upgrade if needed

---

## 📈 Performance Comparison

| Metric           | Ollama (Local) | OpenRouter (Cloud) |
| ---------------- | -------------- | ------------------ |
| **GPU Required** | Yes (16GB)     | No                 |
| **Setup Time**   | ~30 min        | ~20 min            |
| **Latency**      | 0.5-2s         | 1-3s               |
| **Uptime**       | 99.9%          | 99.95%             |
| **Cost**         | $0 (but GPU)   | $0 (free model)    |
| **Scalability**  | Limited        | Unlimited          |

---

## 🛠️ Advanced — Opcje Konfiguracji

### Zmiana Modelu

```env
# Default: Llama 3.1 8B (free)
LLM_MODEL=meta-llama/llama-3.1-8b-instruct:free

# Inne opcje (na openrouter.ai/models):
LLM_MODEL=mistralai/mistral-7b-instruct:free
LLM_MODEL=meta-llama/llama-2-7b-chat:free
LLM_MODEL=openai/gpt-3.5-turbo (PAID)
```

### Canary Rollout (Stopniowa Migracja)

```env
# Start: 10% requests na OpenRouter, 90% na Ollama
LLM_CANARY_ENABLED=1
LLM_CANARY_PERCENT=10
LLM_CANARY_BACKEND=openrouter

# Zwiększaj % w ciągu tygodnia:
# Dzień 1: 10%
# Dzień 2: 25%
# Dzień 3: 50%
# Dzień 4: 75%
# Dzień 5: 100%
```

### Dostrajanie Temperaturdy (Determinizm)

```env
# Default: 0.2 (bardziej deterministyczne)
LLM_TEMPERATURE=0.2

# Bardziej losowe:
LLM_TEMPERATURE=0.7

# Bardzo deterministyczne:
LLM_TEMPERATURE=0.0
```

---

## 📞 FAQs

### Q: Ile czasu zajmuje deployment?

**A:** ~20 minut (15 min Docker build + 5 min health check)

### Q: Czy mogę wrócić na Ollama?

**A:** Tak! Backup `.env.backup.openrouter` czeka gotowy. Przywróć i restart.

### Q: Czy OpenRouter jest bezpieczny?

**A:** Tak! Klucz trzymasz tylko w `.env` lokalnie. API key _nie_ zapisywany do logu.

### Q: Ile kosztuje Llama 3.1 8B?

**A:** $0/miesiąc! Free tier na OpenRouter.

### Q: Jakie inne modele są dostępne?

**A:** 40+ modeli na https://openrouter.ai/models. Kliknij każdy, aby zobaczyć cenę.

### Q: Co jeśli API Key wycieknie?

**A:** 1) Usuń klucz w OpenRouter settings. 2) Wygeneruj nowy. 3) Zaktualizuj `.env`. 4) Restart.

---

## 📋 Checklist Wdrożenia

```
PRE-DEPLOYMENT:
[ ] Posiadasz OpenRouter account
[ ] API Key skopiowany i zapamiętany
[ ] Sprawdzony format: sk-or-v1-...
[ ] Backup .env utworzony (na wszelki wypadek)

DEPLOYMENT:
[ ] Uruchomiono skrypt deploy_openrouter.ps1
[ ] API Key wklejony bez błędów
[ ] Build completed (15 min oczekiwania)
[ ] Container started (docker ps pokazuje adrion-api)
[ ] Health check: PASS

VERIFICATION:
[ ] API endpoint responds (curl test)
[ ] Response zawiera `"score"` pole
[ ] Latency < 5 sekund
[ ] Logi bez ERROR keywords

POST-DEPLOYMENT:
[ ] Obserwowałeś logi (docker-compose logs -f)
[ ] Backup .env.backup.openrouter gotów
[ ] Znasz gdzie znaleźć rollback plan
[ ] Usage page: https://openrouter.ai/usage
```

---

## 🚀 Następne Kroki (Po Deployment)

1. **Obserwacja Metryki (1st hour)**
   - Latency stabilna?
   - Żadne error rate spike?
   - CPU/RAM usage w normie?

2. **Testing (Day 1)**
   - Test 10-20 arbitrage analysys
   - Porównaj wyniki vs local Ollama
   - Weryfikuj quality

3. **Optimization (Week 1)**
   - Adjust LLM_TEMPERATURE jeśli potrzeba
   - Consideruj canary rollout (stopniowa migracja)
   - Monitoring dla skalowania

4. **Scaling (If needed)**
   - Upgrade do PAID tier na OpenRouter
   - Setup batch processing dla high volume
   - Implement caching (Redis)

---

## 📞 Support

- **OpenRouter Docs:** https://openrouter.ai/docs
- **ADRION 369 Logs:** `Genesis Record/10_RAPORTY_DZIALANIA_SYSTEMU/`
- **Docker Logs:** `docker-compose logs -f adrion-api`
- **Status Page:** `docker-compose ps`

---

**Version:** 1.0
**Last Updated:** 2026-04-06
**Status:** ✅ PRODUCTION READY
