# ADRION 369 — Diagnoza Połączenia
**Data**: 2026-04-05 18:45 UTC
**Status**: ✅ SYSTEM ZAINSTALOWANY LOKALNIE + URUCHOMIONY
**Problem**: Frontend nie łączy się z Backend (CORS/Hostname issue)

---

## 🔍 CO ZNALEŹLIŚMY

### ✅ ZAINSTALOWANE I URUCHOMIONE SERWISY

```
KONTENER                  PORT    STATUS      UPTIME
─────────────────────────────────────────────────────
✅ PostgreSQL             5432    HEALTHY     5 hours
✅ Frontend (UAP)         8003    UP          5 hours
⚠️  Backend (UAP)         8002    UNHEALTHY*  5 hours
✅ PgAdmin                5050    UP          5 hours
✅ n8n (Workflow)         5678    UP          7 hours
✅ Vortex Engine          1740    UP          7 hours
✅ Healer (Monitoring)    -       UP          7 hours

* UNHEALTHY = healthcheck robi GET / (404)
  Ale serwis faktycznie pracuje na /mapi/v1/*
```

---

## ❌ PROBLEM: Localhost vs Docker Network

### Bieżąca Konfiguracja (Frontend):
```javascript
// uap/frontend/app.js line 7:
const API_BASE_URL = "http://localhost:8002/mapi/v1";
```

### Problem:
```
Frontend (w dockerze) → próbuje "http://localhost:8002"
  ↓
"localhost" w dockerze = wewnątrz kontenera frontend (nie backend!)
  ↓
Connection Refused / CORS Error
```

---

## ✅ ROZWIĄZANIE: 3 Opcje

### **OPCJA 1: Zmień Frontend API URL (Fast Fix)**

**Plik**: `uap/frontend/app.js` line 7

```javascript
// ZMIEŃ Z:
const API_BASE_URL = "http://localhost:8002/mapi/v1";

// NA (Docker container hostname):
const API_BASE_URL = "http://adrion-uap-backend:8002/mapi/v1";

// LUB (Direct container IP - jeśli znasz):
const API_BASE_URL = "http://172.22.0.3:8002/mapi/v1";
```

**Instrukcja**:
```bash
# 1. otwórz w edytorze
nano uap/frontend/app.js

# 2. Zmień linię 7
# 3. Save (Ctrl+S)

# 4. Reload frontend w przeglądarce
http://localhost:8003
```

---

### **OPCJA 2: Docker Compose Network Fix**

**Plik**: `docker-compose.yml`

Upewnij się, że frontend i backend są w tej samej sieci (powinni być):

```yaml
services:
  frontend:
    ports:
      - "8003:8003"
    networks:
      - adrion-net    # ← WAŻNE

  backend:
    ports:
      - "8002:8002"
    networks:
      - adrion-net    # ← WAŻNE

networks:
  adrion-net:
    driver: bridge
```

Jeśli tego nie ma, dodaj i:
```bash
docker-compose down
docker-compose up -d
```

---

### **OPCJA 3: Environment Configuration**

**Plik**: `.env`

```bash
# Dodaj lub zmień:
API_BASE_URL=http://adrion-uap-backend:8002/mapi/v1
FRONTEND_PORT=8003
BACKEND_PORT=8002
```

---

## 🧪 TEST POŁĄCZENIA

### Test 1: Sprawdzić czy Backend Odpowiada

```bash
# Z hosta (WSL/Terminal):
curl -X GET http://localhost:8002/mapi/v1/status \
  -H "X-API-Key: local-dev-key-123"

# Oczekiwany wynik:
{
  "success": true,
  "status": "healthy"
}
```

### Test 2: Z wewnątrz Frontend'u

```bash
# Wejdź do kontenera frontend
docker exec -it adrion-uap-frontend bash

# Test łączności
curl -X GET http://adrion-uap-backend:8002/mapi/v1/status \
  -H "X-API-Key: local-dev-key-123"

# Powinieneś dostać odpowiedź
```

### Test 3: W Przeglądarce (DevTools)

```javascript
// Otwórz http://localhost:8003 w przeglądarce
// F12 → Console

// Wklej:
fetch('http://adrion-uap-backend:8002/mapi/v1/status', {
  headers: {'X-API-Key': 'local-dev-key-123'}
})
  .then(r => r.json())
  .then(d => console.log('✅ SUCCESS:', d))
  .catch(e => console.log('❌ ERROR:', e))
```

---

## 📊 BIEŻĄCY STATUS SYSTEMU

```
Backend Health Check:
✅ PostgreSQL: Connected
✅ API Server: Running on :8002
✅ Endpoints: 11+ registered

Frontend Status:
✅ HTTP Server: Running on :8003
❌ API Connection: FAILING (wrong hostname/URL)

Database:
✅ PostgreSQL: Healthy
✅ Port: 5432
✅ User: adrion
```

---

## 🚀 QUICK FIX (5 MINUT)

```bash
# 1. Edytuj app.js
cd uap/frontend
sed -i 's|localhost:8002|adrion-uap-backend:8002|g' app.js

# 2. Odśwież frontend w przeglądarce (F5 lub Ctrl+Shift+R)
# Link: http://localhost:8003

# 3. Otwórz F12 → Console
# Powinieneś zobaczyć zamiast błędów połączenia

# 4. Przetestuj w konsoli:
fetch('http://adrion-uap-backend:8002/mapi/v1/tasks', {
  headers: {'X-API-Key': 'local-dev-key-123'}
}).then(r => r.json()).then(d => console.log(d))
```

---

## 📋 NASTĘPNE KROKI (po fixed URL)

### Opcja A: Kontynuuj Phase A & B
```
1. ✅ CSS/HTML czyste
2. ✅ Backend odpowiada
3. ✅ Frontend łączy się
4. → Uruchom testy z PHASE_A_B_EXECUTION_GUIDE
```

### Opcja B: Załaduj Migration SQL
```bash
# Load Phase B database migration:
docker exec adrion-postgres psql -U adrion -d genesis_record \
  -f /path/to/db/migrations/003_tasks_agents_tables.sql
```

### Opcja C: Testuj API endpoints
```bash
# Wszystkie 7 endpoints teraz będą dostępne:
curl -X GET http://localhost:8002/mapi/v1/tasks \
  -H "X-API-Key: local-dev-key-123"
```

---

## ✅ TLDR (Too Long; Didn't Read)

**Pytanie**: Czy ADRION 369 jest zainstalowany lokalnie?

**Odpowiedź**: ✅ **TAKO!! Jest uruchomiony na Docker!**

```
Frontend:  http://localhost:8003 ✅ Working
Backend:   http://localhost:8002 ✅ Working (wrong hostname in config)
Database:  postgresql://localhost:5432 ✅ Healthy
```

**Co do zrobienia**:
Change line 7 in `uap/frontend/app.js`:
```diff
- const API_BASE_URL = "http://localhost:8002/mapi/v1";
+ const API_BASE_URL = "http://adrion-uap-backend:8002/mapi/v1";
```

**Rezultat**: Frontend będzie połączony z Backend, a Phase A & B mogą się zacząć!

---

**Status**: 🟢 SYSTEM GOTOWY
**Czas do Setup**: < 5 minut
**Następny Krok**: Wybierz Opcję 1/2/3 i apply fix
