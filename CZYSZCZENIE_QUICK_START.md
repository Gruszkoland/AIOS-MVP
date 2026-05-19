# 🧹 SZYBKI START - Czyszczenie Profilu

## ⚡ Natychmiast (5 min, Faza 1)
```powershell
# Administrator PowerShell
Remove-Item "C:\Users\adiha\AppData\Local\Temp\*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "C:\Windows\Temp\*" -Recurse -Force -ErrorAction SilentlyContinue
Clear-RecycleBin -Force -Confirm:$false
```
**Zwolni:** 2-3 GB

---

## 🔧 Dev Tools (10 min, Faza 2)
```powershell
# 1. VS Code (zamknij przedtem!)
Remove-Item "C:\Users\adiha\AppData\Roaming\Code\Cache\*" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "C:\Users\adiha\AppData\Roaming\Code\CachedExtensionVSIXs\*" -Recurse -Force

# 2. npm/pip
npm cache clean --force
pip cache purge

# 3. Docker (jeśli zamknięty)
docker system prune -a -f
```
**Zwolni:** 1-3 GB

---

## 🚨 AI Models (OSTROŻNIE! Faza 3)
```powershell
# ⚠️ Usunie pobrane modele LLM (10-50 GB)
Remove-Item "C:\Users\adiha\.ollama" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "C:\Users\adiha\.lmstudio" -Recurse -Force -ErrorAction SilentlyContinue
```
**Zwolni:** 10-50 GB

---

## 📋 Pełna Automatyzacja (Zalecane)
```powershell
# Uruchom skrypt (Administrator)
& "C:\Users\adiha\Clean-UserProfile.ps1" -Phase all
```

---

## ✅ Bezpieczne Czyszczenie - Krok po Kroku

1. **Zatrzymaj aplikacje:** VS Code, Docker, IDE, przeglądarki
2. **Faza 1:** Temp files (zawsze bezpieczne)
3. **Faza 2:** Dev cache (po zamknięciu IDE)
4. **Faza 3:** Models (jeśli masz miejsce na ponowne pobranie)
5. **Restart:** Opcjonalnie, ale zalecane

---

## 📊 Ostateczne Oszczędności
| | Min | Max |
|---|-----|-----|
| Faza 1-2 | 3 GB | 6 GB |
| + Faza 3 | 13 GB | 56 GB |

---

**Raporty:** 
- Pełna analiza: `ANALIZA_ZBEDNYCH_ELEMENTOW.md`
- Skrypt auto: `Clean-UserProfile.ps1`
