# UI Testing Plan — Phase A
**Data**: 2026-04-05 16:15 UTC
**Status**: 🧪 IN PROGRESS
**Komponenty**: Tasks Panel + Agent Manager + Modals

---

## 🎯 TESTING OBJECTIVES

✅ Tasks Panel renders with mock data
✅ Progress bars animate correctly
✅ Status badges color-code properly
✅ Agent Manager grid displays 4 default agents
✅ Agent cards show all required fields
✅ Modal form opens/closes correctly
✅ Create agent form validates
✅ Edit agent pre-populates form
✅ Delete agent removes from list
✅ No console errors

---

## 📋 SETUP INSTRUCTIONS

### Start Backend
```bash
cd uap/backend
python app.py  # http://localhost:8002
```

### Start Frontend
```bash
# Option 1: Live server (if installed)
cd uap/frontend
python -m http.server 8003

# Option 2: Open directly
Open file:///path/to/uap/frontend/index.html in browser
```

### Open Developer Tools
```
F12 or Ctrl+Shift+I
→ Console tab
→ Look for any red errors
```

---

## ✅ TEST CHECKLIST — TASKS PANEL

### 1. Panel Renders
- [ ] Right side shows "Bieżące Zadania" title
- [ ] 4 task items visible with mock data
- [ ] Progress bars show percentages (65%, 40%, 0%, 100%)
- [ ] No layout breaks on right side

### 2. Task Item Display
For each task, verify:
- [ ] Task name displays (e.g., "Deploy Backend to Prod")
- [ ] Status badge shows with color:
  - [ ] Running = Blue
  - [ ] Pending = Yellow
  - [ ] Completed = Green
  - [ ] Failed = Red
- [ ] Progress bar fills correctly (width = progress%)
- [ ] Progress text shows percentage + ETA
- [ ] Agent name badge shows (e.g., "Architect")
- [ ] Task ID shows last 8 chars

### 3. Task Stats Card
- [ ] "Statystyka" card appears below tasks
- [ ] Completed count = 1
- [ ] Running count = 2
- [ ] Failed count = 0
- [ ] Stats update when new mock data loads (every 5s)

### 4. Auto-Refresh
- [ ] Wait 5 seconds
- [ ] Progress bars should animate/update
- [ ] No console errors during refresh

---

## ✅ TEST CHECKLIST — AGENT MANAGER

### 1. Tab Navigation
- [ ] New "Agent Manager" tab visible in menu
- [ ] Click tab → page switches to agent list
- [ ] Tab remains highlighted when active

### 2. Create Button
- [ ] "[+ Utwórz Nowego Agenta]" button visible on top
- [ ] Click button → modal opens
- [ ] Modal title = "Utwórz Nowego Agenta"
- [ ] Form fields empty/default values
- [ ] "Aktywny" checkbox checked by default

### 3. Agent Cards Render
- [ ] 4 agents displayed in 2-column grid
- [ ] Each card shows:
  - [ ] Agent name (Librarian, Architect, Auditor, Sentinel)
  - [ ] Status badge (green "AKTYWNY")
  - [ ] Role in blue (e.g., "Knowledge Management")
  - [ ] Personality quote (italic)
  - [ ] Description text
  - [ ] Skills as badges (blue tags)
  - [ ] Trust Score percentage
  - [ ] [Edytuj] button
  - [ ] [Usuń] button

### 4. Agent Card Styling
- [ ] Cards have left blue border (4px)
- [ ] Card text is readable (contrast OK)
- [ ] Hover effect: card lifts up (box-shadow)
- [ ] Skills badges are readable

---

## ✅ TEST CHECKLIST — MODAL FORMS

### 1. Create Agent Modal
- [ ] Modal appears centered on screen
- [ ] All form fields present:
  - [ ] Nazwa Agenta (text input)
  - [ ] Rola/Specjalizacja (text input)
  - [ ] Osobowość (textarea)
  - [ ] Opis Pełny (textarea)
  - [ ] Trust Score (number input, 0-1)
  - [ ] Capability Level (select: basic/intermediate/expert)
  - [ ] Umiejętności (text input)
  - [ ] Aktywny checkbox
- [ ] [Anuluj] button closes modal
- [ ] [Zapisz Agenta] button saves agent

### 2. Create Agent Flow
- [ ] Click [+ Utwórz Nowego Agenta]
- [ ] Fill form:
  - Name: "Catalyst"
  - Role: "Change Accelerator"
  - Personality: "Dynamic, action-oriented"
  - Description: "Drives rapid implementation"
  - Trust Score: 0.75
  - Capability: expert
  - Skills: "acceleration, momentum, implementation"
- [ ] Click [Zapisz Agenta]
- [ ] Modal closes
- [ ] Success message appears
- [ ] New agent appears in grid (5 agents now)

### 3. Edit Agent Flow
- [ ] Click [Edytuj] on "Librarian" card
- [ ] Modal title = "Edytuj Agenta: Librarian"
- [ ] Form pre-populated with Librarian data:
  - [ ] Name = "Librarian"
  - [ ] Role = "Knowledge Management"
  - [ ] Trust Score = 0.95
  - [ ] Active = checked
- [ ] Change personality to: "Super organized!"
- [ ] Change trust score to 0.97
- [ ] Click [Zapisz Agenta]
- [ ] Success message
- [ ] Librarian card updates with new personality

### 4. Delete Agent Flow
- [ ] Click [Usuń] on "Catalyst" card
- [ ] Confirmation dialog: "Czy na pewno chcesz usunąć tego agenta?"
- [ ] Click OK
- [ ] Success message: "✅ Agent usunięty"
- [ ] Agent removed from grid (4 agents again)

---

## 🔍 BROWSER CONSOLE CHECK

### Open DevTools (F12)
Look for:
- [ ] No red errors (❌)
- [ ] No "undefined function" warnings
- [ ] No 404 errors for assets

### Errors to Watch For:
```
❌ initializeTasksPanel is not defined
❌ Uncaught TypeError: Cannot read property of undefined
❌ Missing Bootstrap modal directive
❌ Template literal syntax errors
```

If errors found:
1. Screenshot error message (with line number)
2. Check if function names match in HTML onclick handlers
3. Verify form IDs in JavaScript

---

## 📱 RESPONSIVE CHECK

### Desktop (1920x1080)
- [ ] 2-column task/agent layout
- [ ] All content visible without scrolling
- [ ] Modals centered

### Tablet (768px)
- [ ] Right panel stacks below chat
- [ ] Agent grid still 2-column
- [ ] Touchable buttons

### Mobile (375px)
- [ ] Content stacks vertically
- [ ] Agent grid = 1 column
- [ ] Modals full-width

---

## 🚀 PERFORMANCE CHECK

### Network Tab
```
Check if:
- All CSS loads (0 errors)
- No slow API calls blocking
- app.js loads without delay
```

### Performance Tab
```
Click → Record → Perform action → Stop
Look for:
- Long tasks > 50ms?
- Layout thrashing?
- Excessive repaints?
```

---

## 📝 TEST RESULTS TEMPLATE

```
TESTER: [Your Name]
DATE: 2026-04-05
BROWSER: Chrome 1XX / Firefox XX

TASKS PANEL:
- Rendering: ✅ PASS / ❌ FAIL
  Issues: [list any problems]
- Progress bars: ✅ PASS / ❌ FAIL
  Issues: [list any problems]
- Auto-refresh: ✅ PASS / ❌ FAIL
  Issues: [list any problems]

AGENT MANAGER:
- Grid display: ✅ PASS / ❌ FAIL
- Create agent: ✅ PASS / ❌ FAIL
- Edit agent: ✅ PASS / ❌ FAIL
- Delete agent: ✅ PASS / ❌ FAIL

CONSOLE ERRORS: [None / List specific errors]

RECOMMENDATIONS:
- [Improvement 1]
- [Improvement 2]
```

---

## ⚡ QUICK TEST (5 minutes)

If short on time, run this minimal test:

1. Open http://localhost:8003/uap/frontend/index.html
2. Go to Chat (Home) tab → verify right panel shows 4 tasks ✅
3. Click Agent Manager tab → verify 4 agent cards visible ✅
4. Click [+ Utwórz Nowego Agenta] → modal opens ✅
5. Fill form → click Save → agent added ✅
6. Click [Usuń] on new agent → deleted ✅
7. Check F12 Console → no red errors ✅
8. **Result**: If all ✅ then UI is working!

---

## 🐛 COMMON ISSUES & FIXES

### Issue: "initializeTasksPanel is not defined"
**Fix**: Check that function declaration is BEFORE the DOMContentLoaded call
```javascript
// CORRECT order:
function initializeTasksPanel() { ... }
document.addEventListener("DOMContentLoaded", () => {
  initializeTasksPanel();
});
```

### Issue: Modal doesn't open
**Fix**: Verify Bootstrap Modal is loaded
```html
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
```

### Issue: Agent form clears after save
**Fix**: Check that `document.getElementById("agentForm").reset()` is called in saveAgent()

### Issue: Tasks don't update every 5 seconds
**Fix**: Verify `setInterval(updateActiveTasksList, 5000)` is in initializeTasksPanel()

### Issue: Agent cards not 2-column
**Fix**: Check viewport width > 1200px (grid-template-columns uses media query)

---

## ✅ SIGN-OFF

Once all tests pass:
1. Take screenshot of Tasks Panel ✅
2. Take screenshot of Agent Manager grid ✅
3. Take screenshot of Create Agent modal ✅
4. Verify no console errors ✅
5. Mark **Phase A: COMPLETE**

---

**Next Steps After Phase A**:
→ Phase B: Backend Integration (connect to real API endpoints)
→ Phase C: Advanced Features (agent history, performance tracking)
→ Phase D: UX Refinements (filters, bulk ops, sorting)
