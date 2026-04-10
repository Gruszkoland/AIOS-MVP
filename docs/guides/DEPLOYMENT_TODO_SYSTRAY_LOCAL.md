# 📋 TODO: Lokalne Wdrożenie Aplikacji Systray ADRION 369

**Data:** 6 kwietnia 2026
**Status:** Gotowy do wdrożenia
**Faza:** 1 (Python Systray MVP)

---

## 🎯 CEL WDROŻENIA

Wdrożenie w pełni działającej aplikacji systray na lokalnym środowisku Windows (10/11) z dostępem do dashboarda ADRION 369 poprzez ikonę w trayu.

---

## ✅ SEKCJA 1: WALIDACJA ARTEFAKTÓW (PRE-DEPLOYMENT)

### 1.1 Weryfikacja artefaktów Fazy 1

- [ ] **Artifact 1**: Pobrać `ADRION-systray-1.0.0.zip` z `uap/desktop/systray/`
  - **Ścieżka**: `C:\Users\adiha\162 demencje w schemacie 369\uap\desktop\systray\ADRION-systray-1.0.0.zip`
  - **Rozmiar**: 29 MB
  - **Zawartość**:
    - `uap_systray.exe` (30.7 MB)
    - `uap_launcher.ps1` (200 LOC)
    - Icon assets (8 wariantów)
    - README_SYSTRAY.md

- [ ] **Artifact 2**: Sprawdzić że `uap_systray.exe` istnieje i jest executable
  - **Ścieżka**: `uap/desktop/systray/dist/uap_systray.exe`
  - **Rozmiar**: 30.7 MB
  - **Tip**: Jeśli brakuje, uruchomić `scripts/build_exe.py`

- [ ] **Artifact 3**: Sprawdzić że `uap_launcher.ps1` istnieje
  - **Ścieżka**: `uap/desktop/systray/uap_launcher.ps1`
  - **Zawartość**: Port checking, process mgmt, health polling

- [ ] **Artifact 4**: Sprawdzić dokumentację
  - **Plik**: `uap/desktop/systray/README_SYSTRAY.md`
  - **Zawartość**: User guide, troubleshooting, features

---

## 🔧 SEKCJA 2: PRE-DEPLOYMENT SETUP (ŚRODOWISKO)

### 2.1 Wymagania systemowe

- [ ] **OS Check**: Windows 10 (build 19041+) lub Windows 11
  - **Komenda**: `winver` → Sprawdzić версию
- [ ] **PowerShell Check**: PowerShell 5.1 (domyślnie na Windows 10/11)
  - **Komenda**: `$PSVersionTable.PSVersion`
  - **Oczekiwane**: 5.1 lub wyżej
- [ ] **Python Check** (opcjonalne - exe jest bundled)
  - **Komenda**: `.venv\Scripts\python.exe --version`
  - **Oczekiwane**: 3.11.9+

### 2.2 Uprawnienia

- [ ] **UAC Check**: Sprawdzić że masz uprawnienia administratora (dla TaskScheduler? lub Auto-startup)
  - **Tip**: Nie wymagane dla podstawowego działania, ale przydatne dla auto-start
- [ ] **Folder Permissions**: Sprawdzić uprawnienia do `C:\Users\adiha\162 demencje w schemacie 369\`
  - **Komenda**: `ls -Force <folder>` w PowerShell pod folderem projektu

### 2.3 Porty

- [ ] **Port 8002 Check**: Sprawdzić że port 8002 jest wolny (dla backend)
  - **Komenda**: `netstat -ano | findstr :8002`
  - **Oczekiwane**: Brak wyników (port wolny)
- [ ] **Port 8003 Check**: Sprawdzić że port 8003 jest wolny (dla frontend/dashboard)
  - **Komenda**: `netstat -ano | findstr :8003`
  - **Oczekiwane**: Brak wyników (port wolny)

---

## 📦 SEKCJA 3: INSTALACJA APLIKACJI

### 3.1 Ekstrakcja artefaktów

- [ ] **Step 1**: Pobrać ZIP na desktop lub tymczasowy folder
  - **Lokalizacja**: `C:\Users\<username>\Desktop\ADRION-systray-1.0.0.zip`
  - **Lub**: `C:\Temp\ADRION-systray-1.0.0.zip`

- [ ] **Step 2**: Rozpakować ZIP
  - **Opcja A** (Explorer): Prawy-klik na ZIP → Extract All...
  - **Opcja B** (PowerShell):
    ```powershell
    Expand-Archive -Path "C:\Users\<username>\Desktop\ADRION-systray-1.0.0.zip" -DestinationPath "C:\Users\<username>\Desktop\ADRION-systray"
    ```

- [ ] **Step 3**: Weryfikować rozpakowane pliki
  - **Pliki**: `uap_systray.exe`, `uap_launcher.ps1`
  - **Komenda**: `ls C:\Users\<username>\Desktop\ADRION-systray\`

### 3.2 (Opcjonalnie) Zainstalować do Program Files

- [ ] **Step 1**: Stworzyć folder instalacyjny
  - **Ścieżka**: `C:\Program Files\ADRION-systray\` (wymaga Admin)
  - **Komenda**: `mkdir "C:\Program Files\ADRION-systray"`

- [ ] **Step 2**: Skopiować pliki
  - **Komenda**:
    ```powershell
    Copy-Item -Path "C:\Users\<username>\Desktop\ADRION-systray\*" -Destination "C:\Program Files\ADRION-systray\" -Force
    ```

- [ ] **Step 3**: Ustawić shortcut na desktop/start menu
  - **Prawy-klik** na `uap_systray.exe` → Send to → Desktop (create shortcut)
  - **Lub**: Pinned na Start Menu

---

## 🚀 SEKCJA 4: URUCHOMIENIE APLIKACJI (QA TESTING)

### 4.1 First-Run Hardware Check

- [ ] **Memory Check**: Sprawdzić wolną RAM (minimum 512MB)
  - **Komenda**: `Get-Process | Measure-Object -Property WorkingSet -Sum`
- [ ] **Disk Space**: Minimum 100MB wolnego miejsca
  - **Komenda**: `Get-Volume`

### 4.2 Launch aplikacji

- [ ] **Step 1**: Double-click `uap_systray.exe`
  - **Oczekiwane**: Brak błędów, ikona pojawia się w trayu (prawy dolny róg)
  - **Ikona**: Zielone koło = backend healthy, pomarańczowe = startup, czerwone = error

- [ ] **Step 2**: Czekać na ustabilizowanie (3-5 sekund)
  - **Co się dzieje**:
    1. Aplikacja startuje backend (`scripts/launch_uap_local_v3.py`)
    2. Backend nabywa port 8002
    3. Frontend serwuje na 8003
    4. Health check powinien przejść

- [ ] **Step 3**: Walidować ikonę w trayu
  - **Lokalizacja**: System tray (dolny prawy róg, may be hidden)
  - **Szukać**: Zielt
    eo koła z literą "A"
  - **Tip**: Być może trzeba kliknąć Show hidden icons

### 4.3 Menu Interactions (Right-click)

- [ ] **Right-click** na ikonę → Powinno pojawić się menu
  - **Opcje**:
    1. **"Open UAP"** - Otworzy dashboard w przeglądarce
    2. **"Status"** - Pokaże status backendu
    3. **"Quit"** - Zamknie aplikację

- [ ] **Test 1**: Click "Open UAP"
  - **Oczekiwane**: Przeglądarka otwiera się na `http://localhost:8003`
  - **Zawartość**: Dashboard ADRION 369 z agent delegator UI

- [ ] **Test 2**: Click "Status"
  - **Oczekiwane**: Notification pokazuje "Backend: Healthy" (zielona ikona)
  - **Jeśli czerwona**: Backend ma problemy, sprawdzić logi

- [ ] **Test 3**: Verify Backend is Running
  - **Komenda**: `netstat -ano | findstr :8002`
  - **Oczekiwane**: Proces Python.exe słucha na porcie 8002

---

## 📊 SEKCJA 5: DASHBOARD VALIDATION

### 5.1 Frontend Accessibility

- [ ] **Załadować dashboard**: Przejść do `http://localhost:8003` w przeglądarce
  - **Oczekiwane**: Strona ładuje się bez błędów
  - **Gówne elementy**:
    - Logo ADRION 369
    - Navigation menu (Agents, Tasks, Genesis Log, Settings)
    - Agent Delegator widget

### 5.2 API Health Check

- [ ] **Test /mapi/v1/health endpoint**: Otworzyć `http://localhost:8003/mapi/v1/health`
  - **Oczekiwane**: JSON response:
    ```json
    {
      "status": "healthy",
      "timestamp": "2026-04-06T...",
      "backend": "running",
      "database": "connected"
    }
    ```

- [ ] **Test /mapi/v1/agents endpoint**: Otworzyć `http://localhost:8003/mapi/v1/agents`
  - **Oczekiwane**: Lista agentów (Librarian, Architect, Auditor, Sentinel)
  - **Jeśli 404**: Upewnić się że backend uruchomiony

- [ ] **Test /mapi/v1/tasks endpoint**: Otworzyć `http://localhost:8003/mapi/v1/tasks`
  - **Oczekiwane**: Lista zadań (może być pusta na start)

### 5.3 Dashboard Functionality

- [ ] **Agents Page**: Klik "Agents" w menu
  - **Oczekiwane**: Tabela z 4 agentami (Librarian 95% trust, Architect 88% trust, itd.)

- [ ] **Tasks Page**: Klik "Tasks" w menu
  - **Oczekiwane**: Tabela zadań (może być pusta)

- [ ] **Genesis Log**: Klik "Genesis Log" w menu
  - **Oczekiwane**: Historia zdarzeń (może być pusta na start)

---

## 🛑 SEKCJA 6: GRACEFUL SHUTDOWN & RESTART TEST

### 6.1 Shutdown Process

- [ ] **Step 1**: Right-click na ikonę → "Quit"
  - **Oczekiwane**: Aplikacja zamyka się bez błędów
  - **Ikona**: Znika z trayu

- [ ] **Step 2**: Sprawdzić że backend został zatrzymany
  - **Komenda**: `netstat -ano | findstr :8002`
  - **Oczekiwane**: Brak procesów na porcie 8002

- [ ] **Step 3**: Sprawdzić że nie ma orphaned procesów
  - **Komenda**: `Get-Process -Name python* | Where-Object {$_.Id -gt 0}`
  - **Oczekiwane**: Brak Python procesów (lub tylko inne aplikacje)

### 6.2 Restart Test

- [ ] **Step 1**: Double-click `uap_systray.exe` ponownie
  - **Oczekiwane**: Aplikacja startuje od nowa, ikona pojawia się w trayu

- [ ] **Step 2**: Czekać na health check (3-5 sekund)
  - **Oczekiwane**: Ikona zmienia się z orange na green

- [ ] **Step 3**: Powtórzyć Section 5 (Dashboard validation)
  - **Oczekiwane**: Wszystko działa identycznie jak po pierwszym uruchomieniu

---

## 🔐 SEKCJA 7: SECURITY & COMPLIANCE CHECK

### 7.1 Process Security

- [ ] **Check Process Owner**: Sprawdzić że proces uruchamia się pod aktualnym userem
  - **Komenda**: `Get-Process -Name python* | Select-Object ProcessName, @{Name="Owner";Expression={$_.StartInfo.UserName}}`

- [ ] **Check File Permissions**: Upewnić się że `uap_systray.exe` nie jest executable dla wszystkich
  - **Komenda**: `Get-Acl "C:\Program Files\ADRION-systray\uap_systray.exe" | Format-List`

### 7.2 Network Security

- [ ] **Firewall Check**: Sprawdzić że komunikacja na portach 8002/8003 jest lokalna (127.0.0.1)
  - **Komenda**: `netstat -ano | findstr :800[23]`
  - **Oczekiwane**: Status LISTENING dla localhost only

- [ ] **No Remote Access**: Sprawdzić że backend nie słucha na 0.0.0.0 (tylko localhost)
  - **Logika**: Czy aplikacja pozwala dostęp z innego komputera?
  - **Oczekiwane**: NIE - tylko localhost powinien mieć dostęp

### 7.3 Guardian Laws Compliance ✅

- [ ] **Privacy (G7)**: Aplikacja nie wysyła danych na sieć (poza localhost)
  - **Test**: Wireshark / Windows Defender Network Traffic → Sprawdzić

- [ ] **Authenticity (G6)**: Aplikacja weryfikuje integrość backend
  - **Test**: (auto w health checks) ✅

---

## 📝 SEKCJA 8: LOGGING & MONITORING

### 8.1 Log Files Setup

- [ ] **Sprawdzić logi backend**: Sprawdzić czy są logi z aplikacji
  - **Lokalizacja**: `logs/` folder w projekcie
  - **Format**: Timestamped entries z health checks

- [ ] **PowerShell Logs**: Uruchomić `uap_launcher.ps1` z flagą `-Verbose`
  - **Komenda**:
    ```powershell
    & ".\uap_launcher.ps1" -Verbose
    ```

- [ ] **Application Logs**: Sprawdzić czy event logs zawierają informacje o aplikacji
  - **Komenda**: `Get-EventLog -LogName Application -Newest 10 | Where {$_.Source -like "*Python*"}`

### 8.2 Performance Monitoring

- [ ] **Memory Usage**: Sprawdzić baseline RAM przy idle
  - **Komenda**: `Get-Process -Name python* | Measure-Object -Property WorkingSet -Sum`
  - **Baseline**: ~80-120MB dla systray + backend

- [ ] **CPU Usage**: Sprawdzić CPU przy idle
  - **Komenda**: `Get-Process -Name python* | Select-Object ProcessName, CPU`
  - **Oczekiwane**: ~0-2% CPU (idle state)

- [ ] **Response Time**: Zmierzyć czas odpowiedzi dashboard
  - **Test**: Załadować `http://localhost:8003` → Sprawdzić DevTools (F12) Network tab
  - **Czas**: Powinna być <2 sekundy

---

## 🎓 SEKCJA 9: FUNCTIONAL TESTING

### 9.1 Agent Interaction

- [ ] **Test 1**: Otworzyć Agents page
  - **Klik**: Agent "Librarian" → Sprawdzić szczegóły (role, trust score, itd.)

- [ ] **Test 2**: Sprawdzić Agent Delegator widget
  - **Funkcja**: Powinien automatycznie wybrać agenta dla nowych zadań
  - **Test**: (Wizualnie verify) ✅

### 9.2 Task Management

- [ ] **Test 1**: Jeśli jest Tasks page - sprawdzić czy mogą być dodane
  - **Nowe zadanie**: Klik "+" button (jeśli dostępny)
  - **Dodaj**: Testowe zadanie z nazwą "Test Task UAP Deployment"
  - **Verify**: Pojawia się na liście

- [ ] **Test 2**: Sprawdzić task details
  - **Klik** na zadanie → Sprawdzić szczegóły (status, agent, itd.)

### 9.3 Genesis Log

- [ ] **Test 1**: Sprawdzić czy Genesis Log zawiera eventy
  - **Events**: Health checks, agent activations, task completions
  - **Oczekiwane**: >=1 entry na system start

---

## ⚡ SEKCJA 10: LINUX/MAC FUTURE PREP (OPCJONALNIE)

### 10.1 Documentation for Future porting

- [ ] **Sprawdzić**: Czy jest dokumentacja cross-platform?
  - **Plik**: `uap_launcher.ps1` → Refactor do bash later
  - **Plan**: Faza 3 = macOS/Linux support

- [ ] **Sprawdzić**: Czy `uap_systray.py` jest platform-agnostic?
  - **Bibliteki**: pystray (cross-platform ✅), Pillow (cross-platform ✅)
  - **Risk**: Windows-specific paths (powershell, registry) → Plan refactor

---

## 📋 SEKCJA 11: PRODUCTION DEPLOYMENT (POST-QA)

### 11.1 Git Integration

- [ ] **Stage Changes**: Jeśli wszystkie testy przeszły
  - **Komenda**:
    ```bash
    git add uap/desktop/systray/
    git status
    ```

- [ ] **Commit**: Zapisać wdrożenie
  - **Komenda**:
    ```bash
    git commit -m "Faza 1: Python Systray MVP - Wszystkie testy QA przeszły"
    ```

- [ ] **Tag Release**: Bezpośrednio tag v1.0.0
  - **Komenda**:
    ```bash
    git tag -a v1.0.0-systray -m "Faza 1 Systray MVP - Windows 10/11 ready"
    git push origin feature/systray-mvp --tags
    ```

### 11.2 Distribution Setup

- [ ] **Upload ZIP**: Przygotować do dystrybucji
  - **Lokalizacja**: `releases/ADRION-systray-1.0.0.zip`
  - **Checksum**: MD5 sum dla integracji
    - **Komenda**: `Get-FileHash "ADRION-systray-1.0.0.zip" -Algorithm MD5`

- [ ] **Create Release Notes**: Dokumentacja dla użytkowników
  - **Zawartość**:
    - Features: System tray, auto-health check, graceful shutdown
    - Requirements: Windows 10/11, 512MB RAM, 100MB disk
    - Installation: Extract ZIP, run EXE
    - Troubleshooting: Common issues + solutions
    - Support: Contact via GitHub issues

### 11.3 Auto-Startup Setup (Opcjonalnie)

- [ ] **Windows Startup Folder**: Dodać shortcut do startup
  - **Folder**: `C:\Users\<username>\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup`
  - **Shortcut**: `uap_systray.exe`
  - **Oczekiwane**: Aplikacja uruchamia się na boot

- [ ] **Task Scheduler** (Advanced):
  - **Create Task**: `ADRION-UAP-Systray`
  - **Trigger**: On Logon
  - **Action**: Run `uap_launcher.ps1`
  - **Advanced**: Hidden window, run with highest privileges

---

## 🎯 SEKCJA 12: SUCCESS CRITERIA (GO/NO-GO DECISION)

### Kryteria Sukcesu (ALL MUST PASS)

**TIER 0 - CRITICAL:**

- [ ] ✅ ZIP można rozpakować (nie corrupted)
- [ ] ✅ EXE jest executable i startuje bez błędów
- [ ] ✅ Ikona pojawia się w trayu w ciągu 5 sekund
- [ ] ✅ Menu pojawia się przy right-click
- [ ] ✅ "Open UAP" otwiera dashboard w przeglądarce
- [ ] ✅ Dashboard ładuje się i jest responsywny
- [ ] ✅ /mapi/v1/health zwraca 200 OK
- [ ] ✅ /mapi/v1/agents zwraca listę 4 agentów
- [ ] ✅ Graceful shutdown bez orphaned procesów

**TIER 1 - IMPORTANT:**

- [ ] ✅ Memory usage <200MB (idle)
- [ ] ✅ CPU usage <5% (idle)
- [ ] ✅ Dashboard response time <2s
- [ ] ✅ Restart aplikacji działa prawidłowo
- [ ] ✅ Brak network exposure (localhost only)

**TIER 2 - NICE-TO-HAVE:**

- [ ] ✅ Logging pracuje (logi dostępne)
- [ ] ✅ Event Log integracja (optional)
- [ ] ✅ Auto-startup configuration (optional)

---

## 📊 SEKCJA 13: RESULT DOCUMENTATION

### QA Sign-Off Template

```
=== ADRION 369 SYSTRAY MVP - LOCAL DEPLOYMENT QA ===
Date: ___________
Tester: ___________
Windows Version: ___________

TIER 0 RESULTS: _____ / 9 PASS
TIER 1 RESULTS: _____ / 5 PASS
TIER 2 RESULTS: _____ / 3 PASS

Overall Status: ☐ PASS (All Tiers) ☐ CONDITIONAL PASS (Tier 0+1 only) ☐ FAIL

Issues Found:
1. _______________________________
2. _______________________________
3. _______________________________

Recommendations:
_____________________________________

Sign-Off: ____________________
```

### Rezultaty

- **GO**: Wszystkie TIER 0 + TIER 1 = Ready for Git commit + Faza 2 start
- **CONDITIONAL**: TIER 0 + some loses in TIER 1 = Ready with documented workarounds
- **NO-GO**: TIER 0 fails = Bug fix required, retry testing

---

## 🔄 SEKCJA 14: NEXT STEPS (FAZA 2)

### Po Zatwierdzeniu QA

- [ ] **Git Commit** (jeśli QA=GO)
- [ ] **Create Release** na GitHub
- [ ] **Update Docs**: `DEPLOYMENT_SUMMARY.md` + `QUICK_START_DAY1.md`
- [ ] **Start Faza 2**: Electron refactor (10-12 hours)
  - Boilerplate + React structure
  - Component migration
  - MSI installer + auto-update

---

## 📞 SUPPORT & TROUBLESHOOTING

### Common Issues

**Issue 1: Icon nie pojawia się w trayu**

- Rozwiązanie: Sprawdzić Show Hidden Icons w trayu
- Debug: `Get-Process | Where-Object {$_.ProcessName -eq "uap_systray"}`

**Issue 2: Dashboard się nie ładuje**

- Rozwiązanie: Sprawdzić port 8003 jest wolny
- Debug: `netstat -ano | findstr :8003`

**Issue 3: Backend nie startuje (czerwona ikona)**

- Rozwiązanie: Sprawdzić port 8002 jest wolny
- Debug: `netstat -ano | findstr :8002`
- Powód: Inny proces na porcie → Kill via Task Manager

**Issue 4: "Access Denied" error**

- Rozwiązanie: Uruchomić EXE jako Administrator
- Alternative: Zmniejszyć Windows Defender restrictions (Advanced Settings)

**Issue 5: PowerShell execution policy error**

- Rozwiązanie: Uruchomić PowerShell jako Admin
- Komenda: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

---

**END OF DEPLOYMENT TODO**

Ostatnia aktualizacja: 6 kwietnia 2026
Faza: 1 (Python Systray MVP) ✅ COMPLETE
Status: Gotowy do wdrożenia i testowania na Windows VM
