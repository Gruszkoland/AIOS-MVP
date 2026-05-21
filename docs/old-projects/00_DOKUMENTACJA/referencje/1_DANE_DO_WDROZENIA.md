# CHECKLIST DANYCH DO WDROŻENIA — AI Transformation Agency System

**Data:** 2026-05-01 | Wypełnij PRZED wdrożeniem

---

## LEGEND

- `[ ]` Do pozyskania / Do wykonania
- `[x]` Gotowe
- `⚡` Generowane automatycznie (nie musisz tego znać — skrypt zrobi to za Ciebie)
- `🔐` Sekret — NIGDY nie udostępniaj

---

## BLOK 1 — HETZNER CLOUD (Serwer)

| # | Czynność | Gdzie | Status | Wartość |
|---|----------|-------|--------|---------|
| 1.1 | Załóż konto na hetzner.com | [hetzner.com/cloud](https://www.hetzner.com/cloud) | `[x]` | — |
| 1.2 | Zweryfikuj email + dodaj metodę płatności | Hetzner Console → Billing | `[x]` | — |
| 1.3 | Utwórz projekt: `adrion-system` | Hetzner Console → New Project | `[x]` | `adrion-system` |
| 1.4 | Wygeneruj klucz SSH lokalnie | Terminal: `ssh-keygen -t ed25519 -C "adrion-vps"` | `[x]` | `C:\Users\adiha\.ssh\id_ed25519` |
| 1.5 | Skopiuj **publiczny** klucz SSH | `cat ~/.ssh/id_ed25519.pub` | `[x]` | — |
| 1.6 | Dodaj klucz SSH do Hetzner projektu | Console → Security → SSH Keys | `[x]` | klucz `adrion-vps` |
| 1.7 | Utwórz serwer CPX32 (Ubuntu 24.04) | Console → New Server | `[x]` | `adrion-system CPX32` |
| 1.8 | Zapisz IP serwera | Po utworzeniu serwera | `[x]` | **VPS_IP:** `178.105.59.41` |
| 1.9 | Firewall: IN 22,80,443 TCP | Console → Firewalls → Create | `[x]` | `adrion-firewall` |

---

## BLOK 2 — DNS @ HOSTINGER

| # | Czynność | Gdzie | Status | Wartość |
|---|----------|-------|--------|---------|
| 2.1 | Zaloguj się do Hostinger | [hpanel.hostinger.com](https://hpanel.hostinger.com) | `[x]` | — |
| 2.2 | Weńdź w DNS Zone dla `aitransformationagency.pl` | Domeny → DNS Zone Editor | `[x]` | — |
| 2.3 | Dodaj rekord A: `@` → `178.105.59.41` TTL 300 | DNS Zone Editor | `[x]` | `@ → 178.105.59.41` |
| 2.4 | Dodaj rekord A: `*` → `178.105.59.41` TTL 300 | DNS Zone Editor (wildcard) | `[x]` | `* → 178.105.59.41` |
| 2.5 | Usuń stare rekordy A / CNAME jeśli istnieją | DNS Zone Editor | `[x]` | — |
| 2.6 | Odczekaj propagację DNS (maks. 30 min) | Sprawdź: `nslookup aitransformationagency.pl` | `[x]` | ✅ **178.105.59.41 — propagacja zakończona (2026-05-06)** |

---

## BLOK 3 — REPOZYTORIA GIT

> **Stan z GitHub (Gruszkoland) — sprawdzony automatycznie 2026-05-01**

| # | Repo | Status na GitHub | URL | Akcja |
|---|------|-----------------|-----|-------|
| 3.1 | **ADRION 369** | ✅ Prywatne — commit d95c67c (v1.3.0, 2026-05-06) | `https://github.com/Gruszkoland/adrion-369` | Gotowe — zsynchronizowane lokalnie |
| 3.2 | **n8n-produkcja** | ❌ NIE MA na GitHub | — | Do pusha |
| 3.3 | **punkt-odniesienia** | ✅ Publiczne | `https://github.com/Gruszkoland/punkt-odniesienia` | Gotowe |
| 3.4 | adrion-369-architecture | ✅ Publiczne — commit debd58d (v5.7.2, 2026-05-06) | `https://github.com/Gruszkoland/adrion-369-architecture` | Gotowe — zsynchronizowane lokalnie |

### Wybierz metodę dostarczenia kodu na VPS

**OPCJA A — rsync (szybciej, bez dodatkowego repo)**

```bash
# Z lokalnej maszyny Windows (Git Bash):
rsync -avz --exclude='.venv' --exclude='__pycache__' --exclude='.git' \
  "/c/Users/adiha/.1_Projekty/PROJEKTY/162 demencje w schemacie 369/" \
  root@<VPS_IP>:/opt/adrion-system/services/adrion/

rsync -avz --exclude='postgres_data' --exclude='.git' \
  "/c/Users/adiha/.1_Projekty/PROJEKTY/n8n-produkcja/" \
  root@<VPS_IP>:/opt/adrion-system/services/n8n-produkcja/
```

**OPCJA B — Push do GitHub (bezpieczniej, łatwiejsze aktualizacje)**

```bash
# ADRION 369 — utwórz prywatne repo "adrion-369" na GitHub
cd "C:\Users\adiha\.1_Projekty\PROJEKTY\162 demencje w schemacie 369"
git remote add origin git@github.com:Gruszkoland/adrion-369.git
git push -u origin master

# n8n-produkcja — utwórz prywatne repo "n8n-produkcja" na GitHub
cd "C:\Users\adiha\.1_Projekty\PROJEKTY\n8n-produkcja"
git init && git add . && git commit -m "init"
git remote add origin git@github.com:Gruszkoland/n8n-produkcja.git
git push -u origin main
```

| # | Czynność (Opcja B) | Gdzie | Status |
|---|----------|-------|--------|
| 3.5 | Utwórz prywatne repo `adrion-369` | github.com/new | `[x]` |
| 3.6 | Utwórz prywatne repo `n8n-produkcja` | github.com/new | `[x]` |
| 3.7 | Push ADRION 369 | GitHub — commit a63148a v1.2.0 | `[x]` |
| 3.8 | Push n8n-produkcja | GitHub — commit ef4b304 (2026-05-06) | `[x]` |
| 3.9 | adrion-369-architecture mypy | 120 → 0 błędów, commit f949c54 | `[x]` |
| 3.10 | GitHub Profile README | github.com/Gruszkoland/Gruszkoland | `[x]` |

> **Rekomendacja:** Opcja A (rsync) na start — jest szybsza. Opcja B potem, gdy projekt będzie stabilny.

---

## BLOK 4 — KLUCZE API LLM 🔐

| # | Serwis | Gdzie pobrać | Status | Wartość |
|---|--------|-------------|--------|---------|
| 4.1 | **OpenRouter** API Key | [openrouter.ai/keys](https://openrouter.ai/keys) | `[x]` | ✅ Pełny klucz zapisany w `.env` (2026-05-06) |
| 4.2 | **Anthropic** API Key | [console.anthropic.com](https://console.anthropic.com) → API Keys | `[ ]` | `sk-ant-___________` |
| 4.3 | (opcja) **OpenAI** API Key | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) | `[ ]` | `sk-proj-___________` |

> Minimalne wymaganie: jeden z 4.1 lub 4.2. OpenRouter daje dostęp do wszystkich modeli z jednym kluczem.

---

## BLOK 5 — SEKRETY APLIKACJI ⚡🔐

Poniższe **generujesz sam** — polecenia podane. Wklej wyniki w odpowiednie pole.

| # | Zmienna | Komenda generująca | Status | Wartość |
|---|---------|-------------------|--------|---------|
| 5.1 | `POSTGRES_PASSWORD` | `openssl rand -base64 24` | `[x]` | `🔐 w PROJEKTY/n8n-produkcja/.env` |
| 5.2 | `N8N_ENCRYPTION_KEY` | `openssl rand -base64 32` | `[x]` | `🔐 w PROJEKTY/n8n-produkcja/.env` |
| 5.3 | `JWT_SECRET` | `openssl rand -hex 32` | `[x]` | `🔐 w 162-demencje/.env` |
| 5.4 | `DRM_HMAC_SECRET` | `openssl rand -hex 32` | `[x]` | `🔐 w 162-demencje/.env` |
| 5.5 | `UAP_API_KEY` | `openssl rand -hex 20` | `[x]` | `🔐 w 162-demencje/.env` |
| 5.6 | `N8N_BASIC_AUTH_PASSWORD` | Wymyśl silne hasło (min. 16 znaków) | `[x]` | `🔐 w PROJEKTY/n8n-produkcja/.env` |
| 5.7 | `GRAFANA_ADMIN_PASSWORD` | Wymyśl silne hasło (min. 16 znaków) | `[x]` | `🔐 w PROJEKTY/n8n-produkcja/.env` |

> ⚠️ `N8N_ENCRYPTION_KEY` (5.2) — **NIGDY nie zmieniaj** po pierwszym uruchomieniu. Utrata klucza = utrata wszystkich credentials w n8n.

---

## BLOK 6 — POWIADOMIENIA I ALERTY (opcjonalne)

| # | Co | Gdzie | Status | Wartość |
|---|----|----|--------|---------|
| 6.1 | (opcja) Email do alertów Grafana | Dowolny email | `[ ]` | `______________@___` |
| 6.2 | (opcja) Webhook URL do alertów (Slack/Discord/n8n) | Slack: App → Incoming Webhooks | `[ ]` | `https://___________` |
| 6.3 | (opcja) Resend API Key (toolkit Punkt odniesienia) | [resend.com/api-keys](https://resend.com/api-keys) | `[ ]` | `re____________________` |

---

## BLOK 7 — BACKUP (opcjonalne — tylko jeśli chcesz S3)

Domyślnie backupy są lokalne. S3 tylko jeśli chcesz off-site.

| # | Co | Gdzie | Status | Wartość |
|---|----|----|--------|---------|
| 7.1 | Utwórz bucket S3 (lub Hetzner Object Storage) | AWS S3 / Hetzner Object Storage | `[ ]` | **S3_BUCKET:** `_______________` |
| 7.2 | Utwórz IAM user z dostępem do bucket | AWS IAM → Users → Create | `[ ]` | **S3_ACCESS_KEY:** `_______________` |
| 7.3 | Pobierz Secret Key | AWS IAM (jednorazowo przy tworzeniu) | `[ ]` | **S3_SECRET_KEY:** `🔐 _______________` |

---

## BLOK 8 — WERYFIKACJA PRZED WDROŻENIEM

Zanim dam rozkaz deploy — sprawdź że masz:

```
[x] VPS_IP wypełniony (Blok 1.8) — 178.105.59.41
[x] Przynajmniej 1 klucz LLM API (Blok 4.1) — OpenRouter zapisany w .env
[x] URL-e repozytoriów (Blok 3.1–3.4) — adrion-369 v1.2.0, adrion-369-architecture v5.7.2
[x] Wszystkie 7 sekretów z Bloku 5 wygenerowane i w .env plikach
[x] n8n-produkcja push do GitHub (Blok 3.8) — commit ef4b304
[x] GitHub Profile README — Gruszkoland/Gruszkoland
[x] Token GitHub z Claude sesji — UNIEWAŻNIONY ✅
[x] WDROŻENIE KOMPLETNE — 11/11 kontenerów healthy (2026-05-06)
     adrion_n8n ✅  adrion_backend ✅  adrion_caddy ✅  adrion_frontend ✅
     adrion_postgres ✅  adrion_prometheus ✅  adrion_grafana ✅
     adrion_alertmanager ✅  adrion_node_exporter ✅  adrion_cadvisor ✅
     adrion_postgres_exporter ✅
     Fix: n8n healthcheck localhost→127.0.0.1 (IPv6 conflict)
[x] DNS propagacja ✅ 178.105.59.41 — SSL certyfikaty aktywne via Caddy/Let's Encrypt
```

---

## KOLEJNOŚĆ WYKONANIA (optymalny flow)

```
DZISIAJ (czas: ~60 min)
  ↓
  1. Hetzner konto + serwer CX31 [20 min]
  2. DNS @ Hostinger (A + wildcard) [5 min]
  3. Generuj sekrety (openssl) [5 min]
  4. Zbierz klucze API [10 min]
  5. Sprawdź URL-e repo [5 min]
  → Poinformuj mnie: "Mam wszystko z checklisty"

AUTOMATYCZNIE (wdrożenie przez Claude)
  ↓
  6. Hardening VPS + Docker [auto]
  7. Clone repozytoriów [auto]
  8. Budowa unified docker-compose [auto]
  9. Deploy stacku [auto]
  10. Smoke test [auto]
  ↓
  GOTOWE: aitransformationagency.pl działa
```

---

## SZACOWANY CZAS ZBIERANIA DANYCH

| Blok | Czas |
|------|------|
| Hetzner konto + serwer | 20 min |
| DNS Hostinger | 5 min |
| Klucze API | 10 min |
| Generowanie sekretów | 5 min |
| URL repozytoriów | 5 min |
| **RAZEM** | **~45 min** |

---

*Kiedy wypełnisz checklistę — podaj mi VPS_IP i URL-e repo. Resztę konfiguruję ja.*
