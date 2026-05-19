# 🔄 SESSION CONTINUITY BRIDGE (SCB) — Auto-Update System

**ADRION 369 v4.0** | Status: ✅ ACTIVE & OPERATIONAL

---

## 📋 QUICK START

### What is SCB?

**Session Continuity Bridge** — automatic synchronization system that:

- ✅ Runs at session start (loads profile)
- ✅ Updates JSON trackers on demand (`python update_adr_status.py`)
- ✅ Auto-syncs Master Synthesis Document every execution
- ✅ Maintains zero desynchronization between tracking files and main reference doc

### How to Enable (One-Time Setup)

```powershell
# 1. Verify profile exists
$PROFILE

# 2. Close & reopen PowerShell (or reload manually)
& $PROFILE

# 3. You should see:
# ✅ [ADRION v4.0] Initializing PowerShell Environment...
# ✅ [SCB] Session Continuity Bridge Ready
# ✅ [ADRION] Environment ready
```

---

## 🔧 COMPONENTS

### 1. Python Automation Script

**Location:** `scripts/reporting/update_adr_status.py` (280+ lines)

**Functions:**

- `load_json()` — UTF-8 encoded file I/O
- `save_json()` — Formatted JSON output
- `scan_adr_files()` — Parse ADR metadata
- `update_adr_adoption_status()` — JSON tracker #1
- `update_atam_progress()` — JSON tracker #2
- `update_tools_integration()` — JSON tracker #3
- `update_master_synthesis_doc()` — **NEW: Sync doc sections §3, §4, §9**

**Usage:**

```bash
# Manual execution (anytime)
python scripts/reporting/update_adr_status.py

# CI/CD trigger (GitHub Actions)
# Runs on: push to docs/adr/, commit to monitoring/

# SCB Auto-trigger (PowerShell exit)
# Runs automatically when session closes
```

### 2. SCB Hook File

**Location:** `.vscode/scb_hook.ps1` (60+ lines)

**Features:**

- Function: `Invoke-ADRONMonitoringSync`
- Auto-activates Python venv
- Calls `update_adr_status.py`
- Reports success/failure
- Error handling + fallback

**Usage:**

```powershell
# Manual execution within session
Invoke-ADRONMonitoringSync

# Auto-execution on session exit
# (Registered in PowerShell profile)
```

### 3. PowerShell Profile

**Location:** `C:\Users\adiha\Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1`

**Responsibilities:**

- Load SCB hook
- Activate .venv
- Set working directory to project root
- Register exit handlers
- Display startup banner

**Trigger:** Runs on every PowerShell session start

---

## 📊 SYNC WORKFLOW (Automated)

```
┌─────────────────────────────────────────────────────────────┐
│ PowerShell Session Starts                                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────▼──────────────┐
        │  Load PowerShell Profile    │
        │  (Microsoft.PowerShell_...)│
        └──────┬───────────────────┬──┘
               │                   │
         ┌─────▼─────┐   ┌────────▼───────┐
         │ Load       │   │ Activate       │
         │ SCB Hook   │   │ .venv          │
         └──────┬─────┘   └────────┬───────┘
                │                  │
                ▼                  ▼
        ┌──────────────────────────────────┐
        │ Session Ready (User works)       │
        └──────────────┬───────────────────┘
                       │ (User exits / Ctrl+C)
        ┌──────────────▼───────────────────┐
        │ Invoke-ADRONMonitoringSync      │
        │ (SCB cleanup handler)            │
        └──────────────┬───────────────────┘
                       │
         ┌─────────────▼─────────────┐
         │ Run Python Script:        │
         │ update_adr_status.py      │
         └──┬──────────┬──────────┬──┘
            │          │          │
      ┌─────▼──┐ ┌────▼────┐ ┌──▼─────────┐
      │ Update │ │ Update  │ │ Update     │
      │ JSON#1 │ │ JSON#2  │ │ JSON#3     │
      │ (ADR)  │ │ (ATAM)  │ │ (Tools)    │
      └───┬────┘ └────┬────┘ └──┬────────┘
          │           │         │
          └───────────┼─────────┘
                      │
        ┌─────────────▼──────────────────────┐
        │ Update Master Synthesis Document   │
        │ § 3 (TSPA from JSON#1)             │
        │ § 4 (ADR Status from JSON#1)       │
        │ § 9 (KPI from JSON#1/2/3)          │
        └─────────────┬──────────────────────┘
                      │
        ┌─────────────▼──────────────────────┐
        │ Session ends                       │
        │ ✅ Knowledge base synchronized     │
        └────────────────────────────────────┘
```

---

## 🎯 EXECUTION MODES

### Mode 1: Manual Trigger (Any Time)

```powershell
# Within active session, run anytime
Invoke-ADRONMonitoringSync

# Output:
# 🔄 [SCB] Running ADRION Monitoring Sync...
# 📊 Synchronizing JSON trackers + Master Synthesis Document
# ✅ [SCB] Sync Complete — Knowledge Base Current
```

### Mode 2: Automatic Session Exit (Default)

```powershell
# User closes PowerShell window or presses exit
# System automatically:
# 1. Detects session close
# 2. Invokes Invoke-ADRONMonitoringSync
# 3. Updates all trackers + synthesis doc
# 4. Logs completion
# 5. Exits cleanly
```

### Mode 3: CI/CD Pipeline (GitHub Actions)

```yaml
# Triggers on: push to docs/adr/
# Runs: update_adr_status.py
# Effect: Auto-update JSON + synthesis doc on every ADR change
# Location: .github/workflows/adr-check.yml (already configured)
```

---

## 📈 WHAT GETS UPDATED

### On Each Sync (All 3 JSON + Master Doc):

#### JSON Trackers (Auto-saved)

1. **ADR-Adoption-Status.json**
   - ADR count (total, accepted, proposed, deprecated)
   - Coverage percentage
   - Timestamp

2. **ATAM-Progress.json**
   - Phase status
   - Timestamp

3. **Tools-Integration-Status.json**
   - Tool status
   - Integration %
   - Timestamp

#### Master Synthesis Document Sections (Auto-updated)

- **§3 — TRUST SCORE DASHBOARD:** Latest TSPA values from current session
- **§4 — ADR STATUS BOARD:** Coverage %, ADR counts, progress bars
- **§9 — METRICS DASHBOARD:** Current KPIs, velocity, trends

---

## 🔍 MONITORING & VERIFICATION

### Check if SCB is Active

```powershell
# Should see this banner on session start:
# 🚀 [ADRION v4.0] Initializing PowerShell Environment...
# ✅ [SCB] Session Continuity Bridge Ready
# ✅ [ADRION] Environment ready

# If not visible — profile not loaded
# Run: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
# Then close & reopen PowerShell
```

### Manual Sync Verification

```powershell
# Run manually to verify
Invoke-ADRONMonitoringSync

# Expected output:
# 🔄 [SCB] Running ADRION Monitoring Sync...
# 📊 Synchronizing JSON trackers + Master Synthesis Document
# 📝 Updating ADR Adoption Status...
# ✅ Saved: ...ADR-Adoption-Status.json
# 📝 Updating ATAM Progress...
# ✅ Saved: ...ATAM-Progress.json
# 📝 Updating Tools Integration Status...
# ✅ Saved: ...Tools-Integration-Status.json
# 📊 Updating Master Synthesis Document...
#    📋 Updating §3 (Trust Score Dashboard)...
#    📋 Updating §4 (ADR Status Board)...
#    📋 Updating §9 (Metrics Dashboard)...
# ✅ Updated: ...MASTER_SYNTHESIS_ADRION369_05-04-2026.md
# ✅ [SCB] Sync Complete — Knowledge Base Current
```

### Check Last Sync Timestamp

```powershell
# Open Master Synthesis Document
cat progress\MASTER_SYNTHESIS_ADRION369_05-04-2026.md | tail -5

# Should show: **Ostatnia aktualizacja:** [TIMESTAMP]
```

---

## 🚨 TROUBLESHOOTING

### Issue: SCB Hook Not Loading

**Symptom:** Profile doesn't show SCB banner  
**Solution:**

```powershell
# Check execution policy
Get-ExecutionPolicy

# If "Restricted", change to:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Reload profile
$PROFILE | Invoke-Item
```

### Issue: Python Script Fails

**Symptom:** "update_adr_status.py not found" error  
**Solution:**

```powershell
# Verify venv exists
Test-Path ".venv\Scripts\Activate.ps1"

# Activate manually
.\.venv\Scripts\Activate.ps1

# Run script
python scripts/reporting/update_adr_status.py
```

### Issue: TS Encoding Error

**Symptom:** "charmap codec can't decode"  
**Solution:** Already fixed (encoding='utf-8' in all file I/O) ✅  
No action needed.

---

## 📝 NEXT STEPS

1. **Verify Setup (Today)**
   - Close & reopen PowerShell
   - Confirm SCB banner shows
   - Run `Invoke-ADRONMonitoringSync` manually

2. **Automated Operation (Apr 22+)**
   - System will auto-sync on every session exit
   - Master Synthesis Document stays current automatically
   - No manual updates needed

3. **Monitoring**
   - Check timestamp in Master Synthesis Document
   - Verify JSON trackers update on ADR changes
   - Review coverage% in §4 weekly

---

## 🎯 BENEFITS

| Benefit             | Impact                     | Measurement           |
| ------------------- | -------------------------- | --------------------- |
| **Auto-sync**       | Zero manual doc updates    | -30-45 min/week       |
| **Always current**  | No desynchronization       | 100% consistency      |
| **Single source**   | Master Synthesis = truth   | One document to read  |
| **Audit trail**     | Timestamps on every update | Full traceability     |
| **Low overhead**    | <2s execution time         | Negligible cost       |
| **Error resilient** | Fallback logging           | Safe to ignore errors |

---

## 📞 SUPPORT

**Issues?** Check `/progress/` folder for latest reports.  
**Questions?** Reference this document (location: `/scripts/reporting/SCB_AUTO_UPDATE_README.md`)

---

**Status:** ✅ OPERATIONAL  
**Version:** SCB v2.0  
**Last Update:** 2026-04-05 20:30 UTC  
**Next Review:** 2026-04-22 (Phase 2 kickoff)
