# Wdrozenie produkcyjne ADRION Arbitrage

## 1) Wymagania
- Docker Engine + docker-compose
- Plik `.env` (skopiowany z `.env.example`)

## 2) Szybki start (1 komenda)
```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

API bedzie dostepne pod adresem:
- http://localhost:8001/api/arbitrage/status

## 3) Przygotowanie .env
Skopiuj szablon i uzupelnij klucze:
```bash
cp .env.example .env
```

Windows PowerShell:
```powershell
Copy-Item .env.example .env
```

Najwazniejsze pola:
- `LLM_BACKEND=auto`
- `OPENROUTER_API_KEY=...` (zalecane)
- `OPENAI_API_KEY=...` (opcjonalnie)
- `ANTHROPIC_API_KEY=...` (opcjonalnie)
- `APIFY_API_TOKEN=...` (opcjonalnie)

## 4) Operacje produkcyjne
Podglad logow:
```bash
docker-compose -f docker-compose.prod.yml logs -f arbitrage-api
```

Restart:
```bash
docker-compose -f docker-compose.prod.yml restart arbitrage-api
```

Stop:
```bash
docker-compose -f docker-compose.prod.yml down
```

## 5) Trwalosc danych
Baza SQLite jest persistowana w katalogu:
- `./data/arbitrage.db`

To oznacza, ze restart kontenera nie usuwa danych.

## 6) Healthcheck
Kontener sprawdza endpoint:
- `/api/arbitrage/status`

Status kontenera:
```bash
docker-compose -f docker-compose.prod.yml ps
```

## 7) Aktualizacja aplikacji
Po zmianach kodu:
```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

## 8) Alternatywa bez Dockera (Windows/Linux)
Instalacja zaleznosci:
```bash
pip install -r requirements-arbitrage.txt
```

Start produkcyjny (Waitress):
```bash
waitress-serve --listen=0.0.0.0:8001 wsgi:app
```

Windows (bez Dockera, uruchomienie na stale przez Harmonogram zadan):
```powershell
python -m pip install -r requirements-arbitrage.txt
python -m waitress --listen=0.0.0.0:8001 wsgi:app
```

Zautomatyzowane skrypty operacyjne Windows:
```powershell
.\scripts\prod\start-prod.ps1 -Port 9100
.\scripts\prod\status-prod.ps1 -Port 9100
.\scripts\prod\healthcheck.ps1 -Port 9100
.\scripts\prod\stop-prod.ps1 -Port 9100
```

Skrypty tworza artefakty runtime w `.runtime\`:
- `waitress.pid`
- `waitress.log`
- `waitress.err.log`

## 9) Uwagi bezpieczenstwa
- Nie commituj pliku `.env`
- XRP wallet nie jest przechowywany na sztywno w kodzie ani w `.env`
- Wystawiaj port 8001 tylko za reverse proxy lub firewall (w publicznej sieci)

## 10) Smoke test po wdrozeniu
```bash
python -c "import urllib.request as u;print(u.urlopen('http://127.0.0.1:8001/api/arbitrage/status', timeout=5).read().decode())"
```

Aktualnie zweryfikowany lokalnie fallback bez Dockera dziala na:
- http://127.0.0.1:9100/api/arbitrage/status
