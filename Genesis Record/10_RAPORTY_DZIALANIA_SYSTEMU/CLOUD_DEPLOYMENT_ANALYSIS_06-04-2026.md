# ANALIZA WDROŻENIA ADRION 369 — FREE CLOUD TIER

**Data:** 06-04-2026
**Autor:** MASTER ORCHESTRATOR (ADRION 369 v4.0)
**Status:** ANALIZA KOMPLETNA

---

## 1. INWENTARYZACJA STOSU TECHNICZNEGO

### Serwisy Docker (docker-compose.prod.yml)

| Serwis             | RAM Limit   | CPU           | Port   | Zależności                |
| ------------------ | ----------- | ------------- | ------ | ------------------------- |
| `adrion-api`       | 512 MB      | 0.5           | 8001   | SQLite, Ollama/OpenRouter |
| `adrion-dashboard` | 256 MB      | 0.25          | 9000   | Docker socket, SQLite     |
| `adrion-uap`       | 512 MB      | 0.5           | 8002   | PostgreSQL (K8s)          |
| `adrion-nginx`     | 128 MB      | 0.25          | 80/443 | api, dashboard, uap       |
| `loki`             | 512 MB      | 0.5           | 3100   | persistent volume         |
| `grafana`          | 512 MB      | 0.5           | 3000   | loki, alert-handler       |
| `promtail`         | ~128 MB     | —             | —      | Docker socket             |
| `alert-handler`    | ~256 MB     | —             | 8090   | —                         |
| `adrion-backup`    | ~64 MB      | —             | —      | SQLite, alert-handler     |
| **RAZEM**          | **~2.9 GB** | **~2.75 CPU** |        |                           |

### Dodatkowe moduły

| Moduł                | Stack                          | RAM est.           |
| -------------------- | ------------------------------ | ------------------ |
| `micro-saas`         | Next.js 15 + React 19 + Stripe | 256–512 MB (build) |
| `harmonia-dashboard` | Python SPA, 27 endpointów      | 128–256 MB         |
| `Ollama (LLM)`       | DeepSeek 16B / Lite            | **8–16 GB ⚠️**     |
| `Kubernetes (UAP)`   | K8s + Postgres + Ingress       | **4+ GB ⚠️**       |

---

## 2. KRYTYCZNE BLOKERY WDROŻENIA FREE-TIER

### 🔴 BLOKER #1 — Ollama / Lokalne LLM

- DeepSeek 16B = ~10 GB RAM
- DeepSeek Lite = ~4 GB RAM
- **Żaden darmowy serwer cloud nie ma tej pojemności**
- **Rozwiązanie:** `LLM_BACKEND=openrouter` → bezpłatne modele (Llama 3.1 8B, Mistral 7B) na openrouter.ai

### 🔴 BLOKER #2 — Docker Socket Mount

- `adrion-dashboard` i `promtail` montują `/var/run/docker.sock`
- Zarządzane platformy cloud (Railway, Render, Fly.io) **blokują** dostęp do socket hosta
- **Rozwiązanie:** Wyłączyć inspekcję kontenerów w Dashboard dla wdrożenia cloud; pozostawić jako degraded mode

### 🟡 BLOKER #3 — Persistencja Danych (SQLite)

- Lokalne wolumeny SQLite giną przy restarcie kontenera na efemerycznych platformach
- **Rozwiązanie:** Fly.io volumes (3 GB free) lub zewnętrzna baza (Supabase free tier: 500 MB Postgres)

### 🟡 BLOKER #4 — Monitoring Stack (Loki + Grafana)

- ~1.5 GB RAM samego monitoringu → niemożliwy na free tier
- **Rozwiązanie:** Zastąpić Grafana Cloud Free (10,000 serii, 50 GB logs/miesiac) lub Betterstack free tier

---

## 3. MACIERZ PLATFORM FREE-TIER

| Platforma                    | RAM Free       | Docker       | Persistence    | Śpi?      | Ocena               |
| ---------------------------- | -------------- | ------------ | -------------- | --------- | ------------------- |
| **Oracle Cloud Always Free** | 24 GB ARM      | ✅ Full      | ✅ 200 GB      | ❌ Nie    | 🥇 **NAJLEPSZY**    |
| **Fly.io**                   | 3× 256 MB      | ✅ Docker    | ✅ 3 GB vol    | ❌ Nie    | 🥈 Dobry            |
| **Railway.app**              | 512 MB         | ✅ Częściowy | ❌ Efemeryczny | ❌ Nie    | 🥉 Ograniczony      |
| **Render.com**               | 512 MB         | ✅           | ❌ Efemeryczny | ✅ 15 min | ⚠️ Dev only         |
| **Vercel**                   | Serverless     | ❌           | ❌ Funkcje     | ❌        | ✅ micro-saas TYLKO |
| **Cloudflare Workers**       | Serverless     | ❌           | KV tylko       | ❌        | ❌ Nie dotyczy      |
| **Google Cloud Run**         | 360k vCPU-s/mc | ✅           | ❌ natywnie    | ✅        | API stateless       |
| **Heroku**                   | PŁATNY         | ✅           | ❌             | —         | ❌ Brak free tier   |

---

## 4. REKOMENDOWANA STRATEGIA WDROŻENIA (3 TIER)

### 🎯 TIER A — Natychmiastowy (0 zmian w kodzie)

**micro-saas → Vercel (FREE)**

- `vercel.json` już istnieje w projekcie ✅
- Next.js 15 + React 19 — natywna obsługa
- Cron `/api/cron/daily-report` → obsługiwany przez Vercel Crons
- Stripe + Resend integracje → działają po podaniu kluczy
- Komenda: `cd micro-saas && vercel --prod`

**Czas:** 30 minut
**Koszt:** $0/miesiąc

---

### 🎯 TIER B — Krótkoterminowy (1–2 dni pracy)

**adrion-api + SQLite → Fly.io (FREE)**

```bash
# Fly.io — deploy API
fly launch --name adrion-api --region waw  # Warszawa DC
fly volumes create adrion_data --size 3    # 3 GB persistent
fly secrets set LLM_BACKEND=openrouter
fly secrets set OPENROUTER_API_KEY=<klucz>
fly deploy
```

- Wymaga: `.env` → Fly secrets
- SQLite persistent na Fly volume
- Wyłączyć w Dashboard Docker socket features (env: `DISABLE_DOCKER_INSPECT=true`)

**Czas:** 1 dzień
**Koszt:** $0/miesiąc (w limicie free tier)

---

### 🎯 TIER C — Pełny stack (Oracle Cloud Always Free — RECOMMENDED)

**Oracle ARM VM — 4 OCPU + 24 GB RAM — ZAWSZE DARMOWY**

To jedyna platforma, która może uruchomić pełny `docker-compose.prod.yml` minus Ollama.

#### Konfiguracja:

```bash
# 1. Provisioning (Oracle Cloud Console)
# Shape: VM.Standard.A1.Flex
# OCPUs: 4, Memory: 24 GB
# OS: Ubuntu 22.04 ARM64

# 2. Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker ubuntu

# 3. Clone + configure
git clone <repo>
cp .env.example .env
# Edytuj .env:
# LLM_BACKEND=openrouter
# OPENROUTER_API_KEY=<klucz>
# Usuń/wykomentuj OLLAMA_URL

# 4. Start bez Ollama
docker compose -f docker-compose.prod.yml up -d \
  adrion-api adrion-dashboard adrion-nginx \
  loki grafana promtail alert-handler adrion-backup

# 5. Zasoby = ~2.9 GB z 24 GB → 88% headroom
```

**Czas:** 2–4 godziny
**Koszt:** $0/miesiąc (Always Free, bez limitu czasowego)

---

## 5. WYMAGANE ZMIANY W KODZIE (Tier B/C)

### Zmiana #1 — Wyłączenie Ollama (środowisko .env)

```bash
# .env
LLM_BACKEND=openrouter
OPENROUTER_API_KEY=sk-or-xxxxx
LLM_MODEL=meta-llama/llama-3.1-8b-instruct:free
# OpenRouter free models: llama-3.1-8b:free, mistral-7b:free
```

### Zmiana #2 — Dashboard Docker-Socket Graceful Fallback

```python
# server.py — dodaj env check
DISABLE_DOCKER_INSPECT = os.getenv("DISABLE_DOCKER_INSPECT", "false").lower() == "true"
```

Jest to 1-liniowa zmiana umożliwiająca uruchomienie Dashboard bez Docker socket (degraded mode).

### Zmiana #3 — docker-compose dla Cloud (nowy plik)

Utworzyć `docker-compose.cloud.yml` — wersja bez Ollama, bez Docker socket, z Fly/Oracle volumes.

---

## 6. KALKULACJA ZASOBÓW — ORACLE FREE TIER

```
Serwis               RAM      CPU      Status
─────────────────────────────────────────────
adrion-api           512 MB   0.5      ✅ Uruchomiony
adrion-dashboard     256 MB   0.25     ✅ (degraded - brak Docker socket)
adrion-nginx         128 MB   0.25     ✅ Uruchomiony
loki                 512 MB   0.5      ✅ Uruchomiony
grafana              512 MB   0.5      ✅ Uruchomiony
promtail             128 MB   -        ✅ Uruchomiony
alert-handler        256 MB   -        ✅ Uruchomiony
adrion-backup         64 MB   -        ✅ Uruchomiony
─────────────────────────────────────────────
RAZEM               2368 MB   2.0 CPU
DOSTĘPNE           24576 MB   4.0 OCPU
HEADROOM           22200 MB   2.0 OCPU  (90% wolne!)
═════════════════════════════════════════════
Ollama (16B)      ~10000 MB   -        ❌ NIE URUCHOMI SIĘ
→ Zastąpić OpenRouter: FREE ($0)
```

---

## 7. ALTERNATYWNE LLM DLA FREE-TIER (OpenRouter)

| Model               | OpenRouter ID                                 | Jakość   | Koszt  |
| ------------------- | --------------------------------------------- | -------- | ------ |
| Llama 3.1 8B        | `meta-llama/llama-3.1-8b-instruct:free`       | ⭐⭐⭐   | FREE   |
| Mistral 7B          | `mistralai/mistral-7b-instruct:free`          | ⭐⭐⭐   | FREE   |
| Gemma 2 9B          | `google/gemma-2-9b-it:free`                   | ⭐⭐⭐   | FREE   |
| DeepSeek R1 (small) | `deepseek/deepseek-r1-distill-llama-70b:free` | ⭐⭐⭐⭐ | FREE\* |
| Qwen 2.5 7B         | `qwen/qwen-2.5-7b-instruct:free`              | ⭐⭐⭐   | FREE   |

\*Rate limited free tiers — wystarczające dla ADRION 369 typowego użytku

---

## 8. PLAN ETAPOWY — HARMONOGRAM

```
TYDZIEŃ 1 (NOW):
├── Dzień 1-2: Deploy micro-saas na Vercel
│   └── Komenda: vercel --prod (w katalogu micro-saas)
│
├── Dzień 3-4: Oracle Cloud Account + VM provisioning
│   └── Rejestracja tylko email → Always Free bez karty*
│
└── Dzień 5-7: Deploy backend na Oracle ARM
    ├── docker-compose.cloud.yml (bez Ollama)
    ├── LLM_BACKEND=openrouter
    └── nginx + TLS via Let's Encrypt (certbot)

*UWAGA: Oracle wymaga weryfikacji karty kredytowej (nie pobiera opłat na Always Free)
```

---

## 9. RYZYKA I MITYGACJE

| Ryzyko                               | Prawdopodobieństwo | Wpływ   | Mitygacja                    |
| ------------------------------------ | ------------------ | ------- | ---------------------------- |
| Oracle zmieni limity Always Free     | Niskie             | Wysokie | Backup: Fly.io               |
| OpenRouter rate limit na free models | Średnie            | Średnie | Fallback na `mock` mode      |
| Docker socket niedostępny            | Pewne (cloud)      | Niskie  | Dashboard degraded mode      |
| SQLite corruption na volume          | Niskie             | Wysokie | `adrion-backup` cron aktywny |
| Cold start na Cloud Run              | Wysokie            | Niskie  | Nie dotyczy Oracle VM        |

---

## 10. PODSUMOWANIE DECYZYJNE

```
REKOMENDACJA FINALNA:
┌─────────────────────────────────────────────────┐
│  OPCJA 1 (MINIMALNA):                           │
│  micro-saas → VERCEL (0 zł, 30 min)            │
│                                                  │
│  OPCJA 2 (PEŁNA, RECOMMENDED):                 │
│  micro-saas → VERCEL                            │
│  backend stack → ORACLE CLOUD ARM               │
│  Ollama → zamienić na OPENROUTER FREE           │
│  Czas: 2-3 dni | Koszt: 0 zł/miesiąc          │
└─────────────────────────────────────────────────┘
```

---

## MICRO-SUMMARY (9 punktów × 3 słowa)

1. Vercel natychmiast gotowy
2. Oracle ARM najlepsza
3. Ollama niewykonalny free
4. OpenRouter zastępuje Ollama
5. Docker socket niemożliwy
6. SQLite wymaga wolumenu
7. Koszt miesięczny zero
8. Headroom 90% wolne
9. Deploy 2-3 dni
