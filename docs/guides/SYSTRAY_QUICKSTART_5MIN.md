# 🚀 QUICKSTART: Systray MVP - 5 Minutes Deployment

## ⚡ SUPER SZYBKO

### 1️⃣ POBRANIE ARTEFAKTÓW (2 min)

```powershell
# Folder gdzie są artefakty
cd "c:\Users\adiha\162 demencje w schemacie 369\uap\desktop\systray"

# Rozpakuj ZIP
Expand-Archive -Path "ADRION-systray-1.0.0.zip" -DestinationPath "C:\Users\$env:USERNAME\Desktop\ADRION-systray"
```

### 2️⃣ SPRAWDZENIE PORTÓW (1 min)

```powershell
# Sprawdź że porty są wolne
netstat -ano | findstr :8002  # Backend port
netstat -ano | findstr :8003  # Frontend port
# Oba powinny być puste (brak LISTENING)
```

### 3️⃣ URUCHOMIENIE (1 min)

```powershell
# Przejdź do folderu i uruchom EXE
cd "C:\Users\$env:USERNAME\Desktop\ADRION-systray"
.\uap_systray.exe
```

### 4️⃣ WALIDACJA (1 min)

#### Visual Check

- ✅ Ikona pojawia się w trayu (dolny prawy róg)
- ✅ Ikona jest zielona (backend healthy)

#### Menu Test

- ✅ Right-click na ikonę
- ✅ Klik "Open UAP" → Przeglądarka otwiera na `http://localhost:8003`
- ✅ Dashboard ładuje się
- ✅ Widać Agents, Tasks, Genesis Log w menu

#### Status Check

- ✅ Right-click → "Status" → Powinna być zielona (Healthy)

---

## 🎯 MINIMAL CHECKLIST (GO/NO-GO)

| #   | Test              | Expected                                    | Result        |
| --- | ----------------- | ------------------------------------------- | ------------- |
| 1   | ZIP extrahuje się | Foldery + pliki widoczne                    | ☐ PASS ☐ FAIL |
| 2   | EXE uruchamia się | Brak exceptions, brak crash                 | ☐ PASS ☐ FAIL |
| 3   | Ikona w trayu     | Zielone koło pojawia się                    | ☐ PASS ☐ FAIL |
| 4   | Menu działa       | Right-click → 3 opcje widoczne              | ☐ PASS ☐ FAIL |
| 5   | Dashboard otwiera | "Open UAP" → browser otwiera localhost:8003 | ☐ PASS ☐ FAIL |
| 6   | Agents widoczni   | /mapi/v1/agents zwraca 4 agentów            | ☐ PASS ☐ FAIL |
| 7   | Health check      | Status = "Healthy" (zielona ikona)          | ☐ PASS ☐ FAIL |
| 8   | Graceful quit     | Ikona znika, port 8002 zamrnięty            | ☐ PASS ☐ FAIL |
| 9   | Restart           | Re-launch EXE → znowu działa                | ☐ PASS ☐ FAIL |

**OVERALL: ☐ GO (8-9 PASS) ☐ NO-GO (<8 PASS)**

---

## 🔍 TROUBLESHOOTING (90 sekund fix)

### ❌ Ikona nie pojawia się

```powershell
# Debug: Sprawdź czy process startuje
Get-Process | Where-Object {$_.ProcessName -like "*uap*"}

# Jeśli nie ma → sprawdź błędy:
# 1. Porty zajęte? netstat -ano | findstr :800[23]
# 2. Uprawnienima? Uruchom jako Admin
```

### ❌ Dashboard się nie ładuje

```powershell
# Sprawdzić backend port
netstat -ano | findstr :8002

# Jeśli brak → backend crash:
# 1. Check if Python 3.11 installed
# 2. Check database exists
```

### ❌ Aplikacja się zamyka natychmiast

```powershell
# Sprawdzić event log
Get-EventLog -LogName Application -Newest 5 | Select-Object Message

# Powód: Zwykle missing dependency
dotnet --version  # Jeśli brakuje .NET
```

---

## 📊 SUCCESS FORMULA

```
IF (Icon appears in tray) AND
   (Right-click menu works) AND
   (Open UAP → browser responds) AND
   (Status shows "Healthy") AND
   (Dashboard loads)
THEN
  => READY FOR PRODUCTION ✅
```

---

**Deployment Time: ~5 minutes**
**Complexity: TRIVIAL ⚡**
**Risk: MINIMAL 🟢**

Status: READY TO DEPLOY 🚀
