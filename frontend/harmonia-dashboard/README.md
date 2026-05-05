# Harmonia 369 — Dashboard & Lead Pipeline

## Architektura

```
Użytkownik → Dashboard (:3690) → Webhook Backend (:3691) → PostgreSQL (adrion-db:5432)
                                              ↓
                                     n8n (:5678) [opcjonalnie]
```

## Szybki start

### 1. Upewnij się, że Docker jest uruchomiony
```bash
docker ps  # powinieneś zobaczyć adrion-db, adrion-n8n
```

### 2. Uruchom dashboard (port 3690)
```powershell
& ".venv/Scripts/python.exe" harmonia-dashboard/serve.py
```

### 3. Uruchom webhook backend (port 3691)
```powershell
& ".venv/Scripts/python.exe" harmonia-dashboard/webhook_server.py
```

### 4. Otwórz dashboard
Przeglądarka → **http://localhost:3690**

### 5. Test end-to-end (PowerShell)
```powershell
$body = '{"event":"scan","business_name":"Test Firma","city":"Warszawa","email":"test@test.pl","phone":"123456789","score_total":55,"score_wv":60,"score_wr":50,"score_we":55,"verdict":"Wymagana optymalizacja"}'
Invoke-RestMethod -Method POST -Uri http://localhost:3691/webhook/harmonia-369 -ContentType "application/json" -Body ([System.Text.Encoding]::UTF8.GetBytes($body))
```

## API Endpoints (Webhook Backend :3691)

| Metoda | Endpoint | Opis |
|--------|----------|------|
| POST | `/webhook/harmonia-369` | Zapis nowego leada / potwierdzenie |
| GET | `/api/leads` | Lista leadów (max 100) |
| GET | `/api/stats` | Statystyki: total, hot, warm, confirmed, avg_score |
| GET | `/health` | Health check |

## Konfiguracja n8n (opcjonalna)

Gdy chcesz skonfigurować n8n jako rozszerzony pipeline (e-mail, Slack, CRM):

1. Otwórz **http://localhost:5678** w przeglądarce
2. Ustaw konto właściciela (email: `punktodniesienia.adrian@gmail.com`)
3. Wejdź w **Settings → Credentials → Add Credential → Postgres**
   - Host: `adrion-db`
   - Port: `5432`
   - Database: `genesis_record`
   - User: `adrion`
   - Password: `adrion_pass`
4. Wejdź w **Workflows → Import from File**
   - Wybierz: `harmonia-dashboard/n8n-workflow-harmonia-369.json`
5. Przypisz Postgres credentials w nodach: `DB Save Lead`, `DB Confirm Lead`
6. Aktywuj workflow (przełącznik w prawym górnym rogu)

## Baza danych

- Host: `localhost:5432`
- DB: `genesis_record`
- User: `adrion` / `adrion_pass`
- Tabela: `leads` (status: NEW → HOT → WARM → CONFIRMED → CONTACTED → CLOSED)

## Pliki

| Plik | Opis |
|------|------|
| `index.html` | Frontend — Licznik Harmonii 369 |
| `style.css` | Style UI (dark mode) |
| `app.js` | Logika frontendowa, algorytm W=(Wv×3+Wr×6+We×9)/18 |
| `serve.py` | Serwer HTTP dla dashboardu (:3690) |
| `webhook_server.py` | Webhook backend (:3691) → PostgreSQL |
| `schema.sql` | Schemat tabeli leads |
| `n8n-workflow-harmonia-369.json` | Workflow n8n (import opcjonalny) |
