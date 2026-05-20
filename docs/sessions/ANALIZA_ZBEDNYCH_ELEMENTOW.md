# Analiza Zbędnych Elementów w C:\Users\adiha

**Data:** 22.04.2026 (zaktualizowano po głębokiej analizie)
**Status:** 🔴 KRYTYCZNY - tylko 27.9 GB wolne z 228 GB!

## 📊 MAPA DYSKU C: - ZIDENTYFIKOWANE POŻERACZE

**Total: 228 GB | Używane: 200 GB | WOLNE: 27.9 GB ⚠️**

### 🔴 GŁÓWNE POŻERACZE (MOŻLIWE DO USUNIĘCIA)

| # | Lokalizacja | Rozmiar | Akcja |
|---|------------|---------|-------|
| 1 | `AppData\Local\Docker\wsl\disk\docker_data.vhdx` | **40.82 GB** | Compact VHD / prune |
| 2 | `~\.ollama\models\` (1 model) | **8.29 GB** | Usuń jeśli nieużywany |
| 3 | `AppData\Local\Ollama` (instalator) | **1.80 GB** | Wyczyść cache |
| 4 | `AppData\Local\Temp` | **2.51 GB** | Natychmiast wyczyść |
| 5 | `AppData\Roaming\Code` (VS Code data) | **1.02 GB** | Wyczyść cache |
| 6 | `AppData\Local\go-build` (Go cache) | **0.84 GB** | `go clean -cache` |
| 7 | `AppData\Local\ms-playwright` | **0.57 GB** | Usuń jeśli nieużywane |
| 8 | `AppData\Local\Programs\cursor` | **0.34 GB** | Aplikacja Cursor |
| 9 | `AppData\Local\Programs\Windsurf` | **0.33 GB** | Aplikacja Windsurf |
| 10 | `AppData\Local\Programs\Microsoft VS Code` | **0.31 GB** | Aplikacja VS Code |
| 11 | `AppData\Local\Programs\PearAI` | **0.28 GB** | Aplikacja PearAI |
| 12 | `AppData\Roaming\Cursor` | **0.25 GB** | Cursor data |
| 13 | `C:\Python314` | **0.19 GB** | Python 3.14 |
| 14 | `AppData\Local\GitKraken` | **0.20 GB** | GitKraken cache |

**Suma możliwa do zwolnienia: ~57 GB** (przy agresywnym czyszczeniu)

### ⚪ NIEZIDENTYFIKOWANE ~143 GB (system + Program Files + msys64 + UWP)

Windows OS, Program Files, msys64 (MSYS2/MinGW), AppData\Local\Packages - wymagają uprawnień admina.

---

## 🎯 PLAN DZIAŁANIA - PRIORYTETY

---

## 🔥 KATEGORIA 1: FOLDER TEMP (NAJPOWAŻNIEJSZY)

**Lokalizacja:** `C:\Users\adiha\AppData\Local\Temp`  
**Rozmiar:** ~2.51 GB  
**Status:** 🔴 KRYTYCZNY - NATYCHMIAST WYCZYŚCIĆ

### Zbędne Elementy w Temp

```
❌ pip-metadata-* (setki folderów) - Cache pip
❌ pip-unpack-* (setki folderów) - Cache pip  
❌ pip-build-tracker-* - Cache build
❌ docker-tar-extract* - Cache docker
❌ docker-scout/* - Docker security scanner cache
❌ playwright-artifacts-* - Artefakty testów
❌ .net/* - Build cache .NET
❌ node-compile-cache/* - Node.js cache
❌ jest/* - Jest test cache
❌ pytest-of-Adrian/* - Pytest cache
❌ chrome_chrome_BITS_* - Chrome update temp files
❌ msedgeedge_BITS_* - Edge update temp files
❌ exthost-*.cpuprofile - VS Code profiling files
❌ vscode-*.exe - VSCode updater temp files
❌ AdobeARM* - Adobe Reader temp files
❌ *.tmp, *.tmp.ico - Generyczne temp files (SETKI)
❌ DiagOutputDir/* - Diagnostic files
❌ collab_low/, acrocef_low/ - Application sandboxes
```

### Akcja

```powershell
# Bezpieczne czyszczenie - najpierw backup
Remove-Item "C:\Users\adiha\AppData\Local\Temp\*" -Recurse -Force -ErrorAction SilentlyContinue

# Lub manualnie przez Windows:
# 1. Disk Cleanup (cleanmgr.exe)
# 2. Storage Sense settings
```

---

## 🔴 KATEGORIA 2: CACHE NARZĘDZI DEVELOPERSKICH

**Potencjalny Rozmiar:** 1-3 GB  
**Status:** 🔴 WYSOKIE - można bezpiecznie usunąć

### Foldery do czyszczenia (bezpiecznie usuwalne)

```
❌ C:\Users\adiha\.cache/              - Ogólny cache
❌ C:\Users\adiha\.vscode/extensions   - Cache ekstensji VS Code
❌ C:\Users\adiha\.ollama/             - LLM model cache (GIGABAJTY!)
❌ C:\Users\adiha\.lmstudio/           - LMStudio cache (GIGABAJTY!)
❌ C:\Users\adiha\.docker/             - Docker cache
❌ C:\Users\adiha\.codegeex/           - CodeGeex AI cache
❌ C:\Users\adiha\.codex/              - Codex AI cache
```

### Uwaga - GIGABAJTY Mają

- **`.ollama/`** - Może zawierać pobrane modele LLM (10-50+ GB)
- **`.lmstudio/`** - Może zawierać pobrane modele LLM (10-50+ GB)
- **VS Code Extensions** - Cache rozszerzeń (1-5 GB)

---

## 🟡 KATEGORIA 3: PLIKI REGISTRY I SYSTEM

**Lokalizacja:** `C:\Users\adiha` (główny katalog)  
**Status:** 🟡 ŚREDNIE - NIE usuwać bez wiedzy!

### Elementy

```
⚠️  NTUSER.DAT             - Active registry file (DO NOT TOUCH!)
⚠️  NTUSER.DAT.LOG1/2      - Registry transaction logs (~5-10 MB)
⚠️  NTUSER.DAT{...}.TM*    - Registry backup (DO NOT TOUCH!)
❌ ntuser.ini              - Registry config (~1 KB)
⚠️  Cookies                - Browser cookies (małe, ale zbędne)
⚠️  Recent                 - Recent files links (zbędne)
⚠️  Saved Games            - Automatycznie zarządzane
```

---

## 📁 KATEGORIA 4: KONFIGURACYJNE FOLDERY (ROZSĄDNIE OCENIĆ)

**Status:** 🟡 ŚREDNIE - część można usunąć

### Potencjalne do oceny

```
⚠️  C:\Users\adiha\.1_Projekty/        - Projekty (sprawdzić zapamiętane gałęzie)
⚠️  C:\Users\adiha\.aider/             - Aider AI cache
⚠️  C:\Users\adiha\.cagent/            - Cache agentów
⚠️  C:\Users\adiha\.claude/            - Claude AI cache
⚠️  C:\Users\adiha\.cline/             - Cline AI cache
⚠️  C:\Users\adiha\.continue/          - Continue extension cache
⚠️  C:\Users\adiha\.cursor/            - Cursor editor cache
⚠️  C:\Users\adiha\.mysti/             - Mysti AI cache
⚠️  C:\Users\adiha\.picoclaw/          - Picoclaw cache
❌ C:\Users\adiha\.agents/             - Agenty cache (potencjalnie do czyszczenia)
```

---

## 📁 KATEGORIA 5: AppData/Roaming (VS CODE)

**Lokalizacja:** `C:\Users\adiha\AppData\Roaming\Code`  
**Status:** 🟡 ŚREDNIE - Sprawdzić rozmiar

### Zbędne elementy VS Code

```
❌ Cache/                    - Cache aplikacji
❌ CachedExtensionVSIXs/     - Cached VSIX files
❌ CachedProfilesData/       - Cached profiles
❌ GPUCache/                 - GPU cache
❌ Crashpad/                 - Crash reports
❌ DawnGraphiteCache/        - Graphics cache
❌ DawnWebGPUCache/          - WebGPU cache
❌ languagepacks.json        - Stare paczki językowe
```

**Czyszczenie VS Code:**

```powershell
# Zamknij VS Code, potem:
Remove-Item "C:\Users\adiha\AppData\Roaming\Code\Cache\*" -Recurse -Force
Remove-Item "C:\Users\adiha\AppData\Roaming\Code\CachedExtensionVSIXs\*" -Recurse -Force
Remove-Item "C:\Users\adiha\AppData\Roaming\Code\Crashpad\*" -Recurse -Force
```

---

## 📁 KATEGORIA 6: INNE ZBĘDNE ELEMENTY

### Dokumenty/Downloads

```
⚠️  C:\Users\adiha\Downloads/          - Może zawierać stare instalatory
⚠️  C:\Users\adiha\Documents/          - Może zawierać archiwa
⚠️  C:\Users\adiha\Desktop/            - Czasami zaśmiecony
```

### OneDrive/Cloud

```
⚠️  C:\Users\adiha\OneDrive/           - Sprawdzić duplikaty
```

---

## 🎯 PLAN CZYSZCZENIA (PRIORITETY)

### 🔴 FAZA 1 - NATYCHMIAST (5-10 minut)

```powershell
# 1. Temp folder (2.51 GB)
Remove-Item "C:\Users\adiha\AppData\Local\Temp\*" -Recurse -Force -ErrorAction SilentlyContinue

# 2. Windows Temp
Remove-Item "C:\Windows\Temp\*" -Recurse -Force -ErrorAction SilentlyContinue

# 3. Prefetch
Remove-Item "C:\Windows\Prefetch\*" -Force -ErrorAction SilentlyContinue

# 4. Recycle bin
Clear-RecycleBin -Force -Confirm:$false -ErrorAction SilentlyContinue
```

**Potencjalnie zwolnione:** 2-3 GB

---

### 🟡 FAZA 2 - DEVTOOLS CACHE (10 minut)

```powershell
# Zamknij VS Code, Docker Desktop, wszystkie IDE

# 1. VS Code Cache
Remove-Item "C:\Users\adiha\AppData\Roaming\Code\Cache\*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "C:\Users\adiha\AppData\Roaming\Code\CachedExtensionVSIXs\*" -Recurse -Force -ErrorAction SilentlyContinue

# 2. NPM/Node cache
npm cache clean --force
npm cache verify

# 3. pip cache
pip cache purge

# 4. Docker images/cache (WARNING: zwolni miejsce ale usunie nieużywane obrazy)
docker system prune -a -f
docker volume prune -f

# 5. Docker Desktop cache
Remove-Item "C:\Users\adiha\AppData\Local\Docker\wsl\*" -Recurse -Force -ErrorAction SilentlyContinue
```

**Potencjalnie zwolnione:** 1-3 GB

---

### 🟡 FAZA 3 - MODELE AI (OPSJONALNE - Może zwolnić 10-50 GB!)

⚠️ **UWAGA:** To usunie pobrane modele LLM!

```powershell
# TYLKO jeśli masz backup lub możliwość przywrócić
# Ollama
Remove-Item "C:\Users\adiha\.ollama" -Recurse -Force -ErrorAction SilentlyContinue

# LMStudio
Remove-Item "C:\Users\adiha\.lmstudio" -Recurse -Force -ErrorAction SilentlyContinue
```

**Potencjalnie zwolnione:** 10-50+ GB

---

### 🟡 FAZA 4 - GŁĘBOKIE CZYSZCZENIE (30 minut)

```powershell
# 1. Usuń registry logs (bezpieczne)
Remove-Item "C:\Users\adiha\ntuser.dat.LOG*" -Force -ErrorAction SilentlyContinue

# 2. Cookies
Remove-Item "C:\Users\adiha\Cookies" -Recurse -Force -ErrorAction SilentlyContinue

# 3. Recent files
Remove-Item "C:\Users\adiha\Recent" -Recurse -Force -ErrorAction SilentlyContinue

# 4. Stare foldery cache AI
Remove-Item "C:\Users\adiha\.cache\*" -Recurse -Force -ErrorAction SilentlyContinue
```

**Potencjalnie zwolnione:** 500 MB - 1 GB

---

## ⚠️ OSTRZEŻENIA - NIE USUWAJ

```
🚫 NIGDY nie usuwaj:
   - NTUSER.DAT (registry aktywny)
   - NTUSER.DAT*.TM* (registry backup)
   - AppData/Roaming/Microsoft/* (system)
   - OneDrive/ (chyba że wiesz co robisz)
   - .1_Projekty/ (projekty!)
   - .vscode/extensions/ (możesz - przywrócą się)
   - .git* pliki (konfiguracja gita)
```

---

## 📈 POTENCJALNE OSZCZĘDNOŚCI

| Faza | Akcja | Zwolnione | Ryzyko |
|------|-------|-----------|--------|
| 1 | Temp + Recycle | **2-3 GB** | ✅ Brak |
| 2 | Dev tools cache | **1-3 GB** | ✅ Brak |
| 3 | AI models | **10-50 GB** | 🟡 Przywróć modele |
| 4 | Głębokie | **500MB-1GB** | ✅ Brak |
| **RAZEM** | **Wszystkie** | **13-57 GB!** | Zależy od fazy |

---

## 🛠️ SKRYPT DO SZYBKIEGO CZYSZCZENIA

```powershell
# Run as Administrator
# Faza 1 + 2 (Bezpieczne, brak ryzyka)

# Temp
Remove-Item "C:\Users\adiha\AppData\Local\Temp\*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "C:\Windows\Temp\*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "C:\Windows\Prefetch\*" -Force -ErrorAction SilentlyContinue

# VS Code (zamknij przedtem!)
Remove-Item "C:\Users\adiha\AppData\Roaming\Code\Cache\*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "C:\Users\adiha\AppData\Roaming\Code\CachedExtensionVSIXs\*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "C:\Users\adiha\AppData\Roaming\Code\Crashpad\*" -Recurse -Force -ErrorAction SilentlyContinue

# npm/pip
npm cache clean --force
pip cache purge

# Recycle bin
Clear-RecycleBin -Force -Confirm:$false -ErrorAction SilentlyContinue

Write-Host "✅ Czyszczenie ukończone!"
```

---

## 📝 REKOMENDACJE NA PRZYSZŁOŚĆ

1. **Automatyczne czyszczenie:**

   ```powershell
   # Zaplanuj zadanie w Windows Task Scheduler
   # Uruchamiaj raz w miesiącu
   ```

2. **Storage Sense** - włącz w Settings:
   - `Settings > System > Storage > Storage Sense`
   - Automatycznie czyści Temp co 30 dni

3. **Docker Maintenance:**

   ```powershell
   # Co miesiąc
   docker system prune -a -f
   docker volume prune -f
   ```

4. **Monitorowanie:**

   ```powershell
   # Sprawdzaj rozmiar Temp i AppData
   Get-ChildItem "C:\Users\adiha\AppData\Local" -Recurse -Force | Measure-Object -Property Length -Sum
   ```

---

## 🔍 DODATKOWE SPRAWDZENIA

Aby znaleźć inne duże foldery:

```powershell
# Top 10 największych folderów
gci -Path C:\Users\adiha -Directory -Recurse -ErrorAction SilentlyContinue | 
  ForEach-Object { @{Path=$_.FullName; Size=((gci -Path $_.FullName -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1GB) }} | 
  Sort-Object Size -Descending | Select-Object -First 10 | Format-Table
```

---

**Wygenerowano:** 22.04.2026  
**Autoryzacja:** Administrativa wymagana do wykonania czyszczenia
