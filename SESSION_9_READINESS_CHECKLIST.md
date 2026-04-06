# ✅ SESJA 9 READINESS CHECKLIST

**Status**: Ready for Manual QA Testing  
**Current Date**: 6 kwietnia 2026  
**Expected QA Date**: Next available session  

---

## 📋 PRE-SESSION 9 CHECKLIST (What Must Be Ready)

### ✅ Infrastructure Checks
- [x] **Health Check Script**: `scripts/deployment_health_check.py` created & tested ✅
- [x] **Artifact Verification**: All files present (ZIP, EXE, PS1) ✅
- [x] **Port Availability**: 8002 & 8003 free on test machine ✅
- [x] **Python Environment**: 3.11.9 configured ✅

### ✅ Documentation Ready
- [x] **QA Guide**: `DEPLOYMENT_TODO_SYSTRAY_LOCAL.md` (14 sections) ✅
- [x] **Quick Start**: `SYSTRAY_QUICKSTART_5MIN.md` (5-minute guide) ✅
- [x] **Checklist**: `DEPLOYMENT_CHECKLIST_SYSTRAY.csv` (90 rows) ✅
- [x] **Troubleshooting**: Section 10 in deployment guide ✅
- [x] **Success Template**: Section 13 QA sign-off ✅

### ✅ Test Materials
- [x] **8-Point Checklist**: Defined & documented ✅
- [x] **TIER 0/1/2 Criteria**: Success metrics defined ✅
- [x] **Go/No-Go Framework**: Decision matrix ready ✅
- [x] **Expected Timings**: 70-100 minutes estimated ✅

### ✅ Support Materials
- [x] **Troubleshooting**: Top 5 issues + fixes documented ✅
- [x] **Health Indicators**: Normal baseline established ✅
- [x] **Escalation Path**: Clear documentation ✅
- [x] **Notes Template**: Ready to capture findings ✅

---

## 🚀 SESSION 9 EXECUTION PLAN

### PHASE 1: SETUP (15 minutes)
```
Tasks:
☐ Prepare Windows 10/11 VM or test machine
☐ Download ADRION-systray-1.0.0.zip
☐ Create test folder: C:\temp\ADRION-test\
☐ Extract ZIP to test folder
☐ Verify files: uap_systray.exe, uap_launcher.ps1 present
```

**Success Indicator**: All 3 files visible, ZIP size ~29 MB

---

### PHASE 2: DEPLOYMENT (10 minutes)
```
Tasks:
☐ Check ports: netstat -ano | findstr :800[23]
☐ Double-click uap_systray.exe
☐ Wait 5 seconds for startup
☐ Look for icon in system tray (bottom-right)
☐ Verify icon is GREEN circle
☐ Note any error dialogs
```

**Success Indicator**: Green icon visible in tray, no errors

**Expected Behavior**:
- t=0s: Click EXE
- t=2s: Backend starts (Flask on :8002)
- t=3s: Frontend starts (dashboard on :8003)
- t=3-5s: Icon appears in tray (green)
- t=5s: Ready for interaction

---

### PHASE 3: FUNCTIONAL TESTING (30 minutes)

#### TEST 1: Menu Interaction
```
Actions:
☐ Right-click on tray icon
☐ Verify menu appears (3 options visible)
☐ Verify options: "Open UAP", "Status", "Quit"
```

**Expected**: Menu pops up with 3 options

#### TEST 2: Dashboard Access
```
Actions:
☐ Click "Open UAP" from menu
☐ Browser should open automatically
☐ URL should be: http://localhost:8003
☐ Wait for dashboard to load (max 2 seconds)
☐ Verify UI elements: Logo, Navigation, Agent Widget
```

**Expected**: Dashboard loads with ADRION 369 UI

#### TEST 3: API Validation
```
Actions:
☐ Open new browser tab
☐ Navigate to: http://localhost:8003/mapi/v1/health
☐ Should show JSON response
☐ Check "status": should be "healthy"
```

**Expected**: JSON with "status":"healthy"

#### TEST 4: Agents List
```
Actions:
☐ In dashboard, click "Agents" menu
☐ Wait for table to load
☐ Should show 4 rows: Librarian, Architect, Auditor, Sentinel
☐ Check Librarian has ~95% trust score
```

**Expected**: 4 agents with details visible

#### TEST 5: Status Check
```
Actions:
☐ Right-click tray icon
☐ Click "Status"
☐ Should show popup/notification: "Backend: Healthy"
☐ Icon should still be GREEN
```

**Expected**: Notification appears, icon green

#### TEST 6: Graceful Shutdown
```
Actions:
☐ Right-click tray icon
☐ Click "Quit"
☐ Wait 2 seconds
☐ Icon should disappear from tray
☐ No error dialogs
☐ Verify: netstat -ano | findstr :8002 → No results
```

**Expected**: Clean shutdown, no orphaned processes

#### TEST 7: Performance Check
```
Measurements:
☐ Startup time: < 5 seconds ✅
☐ Dashboard load: < 2 seconds ✅
☐ API response: < 500ms ✅
☐ Memory usage: < 200MB ✅
☐ CPU idle: < 5% ✅
```

**Expected**: All metrics within baseline

#### TEST 8: Restart Test
```
Actions:
☐ Double-click uap_systray.exe again
☐ Wait 5 seconds
☐ Icon should reappear (green)
☐ Repeat TEST 1-7 (abbreviated)
☐ Everything should work identically
```

**Expected**: Identical behavior to first launch

---

### PHASE 4: DOCUMENTATION (15 minutes)

#### Create QA Report
```
Steps:
☐ Copy QA Sign-Off Template (see DEPLOYMENT_TODO Section 13)
☐ Fill in: Date, Tester, Windows Version
☐ Record TIER 0 results (9 tests)
☐ Record TIER 1 results (5 tests)
☐ Record TIER 2 results (3 tests)
☐ Note any issues found
☐ Document workarounds (if needed)
☐ Make GO/NO-GO decision
☐ Sign-off with name & timestamp
```

**Template Location**: `DEPLOYMENT_TODO_SYSTRAY_LOCAL.md` Section 13

---

### PHASE 5: DECISION (5 minutes)

#### GO Decision (ALL TIER 0 + TIER 1 PASS)
```
✅ All 14 critical tests passed
✅ No blocker issues found
✅ Performance acceptable
✅ User experience smooth
→ RESULT: PROCEED TO GIT COMMIT
```

**Next Steps**:
1. Document: "QA PASS: v1.0.0-systray Ready"
2. Git: `git add uap/desktop/ && git commit -m "Faza 1: QA PASS"`
3. Tag: `git tag -a v1.0.0-systray -m "First production release"`
4. Push: `git push origin feature/systray-mvp --tags`
5. Release: Create GitHub release with ZIP upload
6. **Start Faza 2**: Electron refactor (Sessions 10-12)

#### NO-GO Decision (TIER 0 FAILS)
```
❌ Critical functionality broken
❌ Deployment fails
❌ Major UX issues
→ RESULT: IDENTIFIED BUG - FIX REQUIRED
```

**Next Steps**:
1. Document: Issue details & stack trace
2. Identify: Root cause
3. Fix: In code
4. Verify: Re-run health check
5. Retry: Manual testing again (abbreviated)

#### CONDITIONAL Decision (TIER 0 PASS, TIER 1 PARTIAL)
```
✅ Core functionality works
⚠️  Some non-critical issues
⚠️  Documented workarounds available
→ RESULT: PROCEED WITH CAUTION
```

**Next Steps**:
1. Document: Issues + workarounds in README
2. Add: Known Issues section to deployment guide
3. Git: Commit with "known issues" note
4. Tag: v1.0.0-systray-rc1 (release candidate)
5. Plan: Bug fixes for v1.0.1

---

## 📊 TIER BREAKDOWN

### TIER 0 - CRITICAL (9 tests) ✅ MUST ALL PASS
1. [ ] ZIP extraction works (file integrity)
2. [ ] EXE launches without errors
3. [ ] Icon appears in system tray (bottom-right)
4. [ ] Right-click menu appears (3 options visible)
5. [ ] "Open UAP" opens browser to localhost:8003
6. [ ] Dashboard displays ADRION 369 UI
7. [ ] Agents API returns 4 agents
8. [ ] Graceful shutdown (no orphans)
9. [ ] Restart works identically to first launch

### TIER 1 - IMPORTANT (5 tests) ⚠️ RECOMMENDED ALL PASS
1. [ ] Startup time < 5 seconds
2. [ ] Dashboard load < 2 seconds
3. [ ] Status notification shows "Healthy"
4. [ ] Memory usage < 200MB idle
5. [ ] All Tier 0 tests repeat successfully after restart

### TIER 2 - NICE-TO-HAVE (3 tests) 💡 OPTIONAL
1. [ ] Dark mode toggle (if UI has it)
2. [ ] Keyboard shortcuts working
3. [ ] Icon animations smooth (no flicker)

---

## 🎯 SUCCESS FORMULA

```
IF (TIER 0 ALL PASS) THEN
    IF (TIER 1 ALL PASS) THEN
        Status = GO ✅ → Commit to main
    ELSE
        Status = CONDITIONAL ⚠️ → Document issues
    ENDIF
ELSE
    Status = NO-GO ❌ → Identify & fix bug
ENDIF
```

---

## 📱 EXPECTED BEHAVIORS (Baseline)

### Normal Startup Sequence
```
t=0.0s: User double-clicks uap_systray.exe
t=0.5s: Python subprocess launched (Flask backend)
t=1.5s: Flask listens on :8002
t=2.0s: React frontend router ready on :8003
t=3.0s: Health check passes
t=3.5s: Tray icon appears (green circle)
t=4.5s: Ready for user interaction
```

**Total Time**: 4-5 seconds ✅

### Normal Shutdown Sequence
```
t=0.0s: User right-clicks tray icon, clicks "Quit"
t=0.5s: Graceful shutdown signal sent to backend
t=1.0s: Flask server stops accepting requests
t=1.5s: Connections close, database commits
t=2.0s: Process exits
t=2.5s: Tray icon disappears
```

**Total Time**: <3 seconds ✅

### Health Check Sequence
```
t=0.0s: User right-clicks → "Status"
t=0.2s: HTTP GET /mapi/v1/health sent
t=0.5s: Backend responds with JSON
t=0.7s: Notification appears
```

**Total Time**: <1 second ✅

---

## 🔧 TROUBLESHOOTING (Quick Fixes)

### Issue 1: Icon Doesn't Appear
```
Check:
☐ Is EXE running? (Task Manager: python.exe)
☐ Are ports free? (netstat -ano | findstr :8002)
☐ Show Hidden Icons in tray (Show/Hide button)
☐ Try restart EXE
```

### Issue 2: Dashboard Doesn't Load
```
Check:
☐ Is port 8003 free? (netstat -ano | findstr :8003)
☐ Browser dev tools (F12) → Check console for errors
☐ Try http://localhost:8002/health directly
☐ Check Windows Defender isn't blocking
```

### Issue 3: Random Crashes
```
Check:
☐ Free disk space? (min 100MB)
☐ Free memory? (min 512MB)
☐ Admin rights? (Try "Run as Administrator")
☐ Antivirus interfering? (Temporarily disable)
```

### Issue 4: Port Already In Use
```
Solution:
☐ netstat -ano | findstr :8002  # Find process ID
☐ taskkill /PID <ID> /F  # Kill process
☐ Try again: Launch EXE
```

### Issue 5: UI Looks Wrong
```
Check:
☐ Browser zoom 100%? (Ctrl+0)
☐ Resolution >= 1024x768?
☐ Chrome/Edge/Firefox latest version?
☐ Try F5 refresh
```

---

## 📝 NOTES FOR TESTER

**General Tips**:
1. Use Chrome/Windows 11 for best experience
2. Have admin console ready (for netstat, taskkill)
3. Take screenshots if issues occur
4. Document timings (use stopwatch/phone)
5. Test twice (first launch + restart)

**Important**:
- Don't modify any code (just test)
- Use fresh VM if possible (clean environment)
- Report even small UI glitches
- If stuck >15 min, escalate

**Keep**:
- All logs/screenshots for bug reports
- Timing measurements
- Notes on workarounds used

---

## ✅ FINAL GO/NO-GO CHECKLIST

Before declaring GO:

**Functionality** ✅
- [ ] Systray integration works
- [ ] Dashboard loads
- [ ] Agents data visible
- [ ] Menu responsive
- [ ] Shutdown clean

**Performance** ✅
- [ ] Startup <5 seconds
- [ ] Dashboard load <2 seconds
- [ ] No memory leaks
- [ ] CPU reasonable (<5% idle)

**Stability** ✅
- [ ] No crashes observed
- [ ] Restart works
- [ ] No orphaned processes
- [ ] Clean error handling

**UX** ✅
- [ ] UI intuitive
- [ ] Icons clearly visible
- [ ] Notifications informative
- [ ] Flows logical

**Compliance** ✅
- [ ] No external network calls
- [ ] All local (127.0.0.1)
- [ ] Guardian Laws enforced
- [ ] Security baseline met

---

## 🎓 SUCCESS = SESSION 9 COMPLETE

**When you can check ALL boxes above** → Status: ✅ GO

**Next Phase**: Git commit + Faza 2 Electron Refactor (Sessions 10-12)

---

**Generated**: 6 kwietnia 2026  
**For**: Session 9 Manual QA Testing  
**Status**: ✅ READY TO EXECUTE  

---

🟢 **SYSTEM READY FOR TESTING - ALL PREREQUISITES MET**
