# 📋 FAZA 2 - ELECTRON REFACTOR SETUP CHECKLIST

**Zaplanowana na**: Sesje 10-12
**Czas**: 10-12 godzin
**Status**: Ready for Planning

---

## 🎯 FAZA 2 OBJECTIVES

### Core Goals

1. Migrate from Python Systray → Native Electron window
2. React component framework for UI
3. Maintain 100% feature parity with Faza 1
4. Add MSI installer for professional distribution
5. Implement auto-update capability

---

## 🏗️ ARCHITECTURE CHANGES (Faza 1 → Faza 2)

### Faza 1 (Python Systray MVP) ✅ COMPLETE

```
Windows VM
├─ uap_systray.exe (30.7 MB)
│  └─ Python runtime
│     ├─ pystray (tray icon)
│     ├─ Flask (HTTP server)
│     └─ psutil (monitoring)
├─ Backend: Flask on :8002
├─ Frontend: HTML/JS on :8003
└─ Distribution: 29 MB ZIP
```

### Faza 2 (Electron Native) ⏳ UPCOMING

```
Windows VM
├─ ADRION-systray.exe (Electron)
│  └─ Node.js runtime
│     ├─ Electron (native window)
│     ├─ React (UI framework)
│     ├─ electron-builder (MSI)
│     └─ dexie.js (IndexedDB offline)
├─ Backend: Flask on :8002 (unchanged)
├─ Frontend: React components (embedded)
└─ Distribution: MSI installer (~50-80 MB)
```

### Key Differences

| Aspect         | Faza 1               | Faza 2                 |
| -------------- | -------------------- | ---------------------- |
| Runtime        | Python 3.11          | Node.js 18 LTS         |
| GUI            | pystray (minimalist) | Electron (full window) |
| UI Framework   | Vanilla JS           | React 18               |
| Package        | ZIP (29 MB)          | MSI (50-80 MB)         |
| Auto-update    | Manual               | electron-updater       |
| Offline Sync   | Not supported        | IndexedDB ready        |
| Dev Experience | Python standard      | Node.js standard       |
| Distribution   | ZIP unpack           | MSI installer          |

---

## 📦 DEPENDENCIES (Faza 2)

### Node.js Stack

```json
{
  "name": "adrion-systray-electron",
  "version": "2.0.0",
  "main": "dist/main.js",
  "dependencies": {
    "electron": "^27.0.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "dexie": "^3.2.4",
    "axios": "^1.4.0",
    "recharts": "^2.7.0",
    "tailwindcss": "^3.3.0"
  },
  "devDependencies": {
    "electron-builder": "^24.6.4",
    "electron-updater": "^5.3.0",
    "vite": "^4.3.0",
    "@vitejs/plugin-react": "^4.0.0"
  }
}
```

### Installation Command

```bash
npm install
npm install -D electron electron-builder electron-updater
```

---

## 🗂️ PROJECT STRUCTURE (Faza 2)

```
uap/desktop/electron/
├─ public/
│  ├─ index.html              # Main HTML
│  └─ icon.png                # App icon
├─ src/
│  ├─ main/
│  │  ├─ main.ts             # Electron main process
│  │  ├─ preload.ts          # IPC bridge
│  │  └─ ipc-handlers.ts      # Event listeners
│  ├─ renderer/
│  │  ├─ App.tsx             # React root component
│  │  ├─ components/
│  │  │  ├─ Dashboard.tsx
│  │  │  ├─ Agents.tsx
│  │  │  ├─ Tasks.tsx
│  │  │  ├─ GenesisLog.tsx
│  │  │  └─ StatusBar.tsx
│  │  ├─ hooks/
│  │  │  ├─ useBackend.ts    # Backend API
│  │  │  └─ useOfflineSync.ts # Dexie.js
│  │  ├─ styles/
│  │  │  └─ tailwind.css
│  │  └─ index.tsx           # React entry
│  ├─ db/
│  │  └─ schema.ts           # Dexie schemas
│  └─ types/
│     └─ api.ts              # API types
├─ electron-builder.yml       # Build config
├─ vite.config.ts            # Vite build config
├─ package.json
├─ tsconfig.json
└─ README.md
```

---

## 📝 SESSION 10: BOILERPLATE & SETUP (4-5 hours)

### 10.1 Project Init (30 min)

- [ ] Create `uap/desktop/electron` folder
- [ ] `npm init -y` (create package.json)
- [ ] Install Electron + dependencies
- [ ] Setup TypeScript config
- [ ] Setup Vite build tool

```bash
mkdir -p uap/desktop/electron
cd uap/desktop/electron
npm init -y
npm install --save-dev electron electron-builder vite @vitejs/plugin-react
npm install react react-dom dexie axios
```

### 10.2 Electron Main Process (1 hour)

- [ ] Create `src/main/main.ts`
  - App initialization
  - Window creation
  - Backend health check polling
  - Graceful shutdown

### 10.3 React Setup (1 hour)

- [ ] Create `src/renderer/App.tsx`
- [ ] Setup React Router
- [ ] Create layout components
- [ ] Setup Tailwind CSS

### 10.4 IPC Bridge (1 hour)

- [ ] Create `src/main/ipc-handlers.ts`
  - Backend communication
  - System tray integration
  - Settings management
  - Auto-update triggers

### 10.5 Build System (30 min)

- [ ] vite.config.ts
- [ ] electron-builder.yml
- [ ] Build scripts in package.json
- [ ] Test development build

---

## 📝 SESSION 11: COMPONENT MIGRATION (5-6 hours)

### 11.1 Dashboard Component (2 hours)

- [ ] Migrate from vanilla JS to React
- [ ] Use Recharts for charts
- [ ] Responsive grid layout
- [ ] Real-time status updates

### 11.2 Entity Components (2 hours)

- [ ] Agents page (table + details)
- [ ] Tasks page (CRUD operations)
- [ ] Genesis Log (event stream)
- [ ] Status indicator widget

### 11.3 Styling & UX (1 hour)

- [ ] Tailwind CSS integration
- [ ] Responsive design
- [ ] Dark mode support
- [ ] Loading states

### 11.4 API Integration (1 hour)

- [ ] useBackend hook
  - HTTP client setup
  - Error handling
  - Retry logic
  - Request deduplication

---

## 📝 SESSION 12: INTEGRATION & RELEASE (3-4 hours)

### 12.1 Backend Integration (1 hour)

- [ ] Verify Flask backend still runs
- [ ] Test port binding (8002)
- [ ] Health check integration
- [ ] Auto-start backend from Electron

### 12.2 Packaging (1 hour)

- [ ] electron-builder setup
- [ ] MSI installer generation
- [ ] Icon & branding
- [ ] Signing (optional for dev)

### 12.3 Testing (1 hour)

- [ ] Build & package locally
- [ ] Test MSI installer
- [ ] Verify all features work
- [ ] Performance benchmark

### 12.4 Release & Documentation (30-60 min)

- [ ] Git commit & tag v2.0.0-electron
- [ ] GitHub release + MSI upload
- [ ] Update DEPLOYMENT_SUMMARY.md
- [ ] Create migration guide Faza 1→2

---

## 🗝️ KEY MILESTONES (Faza 2)

```
Session 10         Session 11         Session 12
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│ Boilerplate │   │ Components  │   │ Integration │
│ + Electron  │   │ + Styling   │   │ + Release   │
├─────────────┤   ├─────────────┤   ├─────────────┤
│ • Setup npm │   │ • Dashboard │   │ • Build MSI │
│ • TSconfig  │   │ • Agents    │   │ • Test pkg  │
│ • Main proc │   │ • Tasks     │   │ • Git tag   │
│ • React app │   │ • Styling   │   │ • Release   │
└─────────────┘   └─────────────┘   └─────────────┘
  ↓                 ↓                 ↓
 Dev build       Component           Production
 ready           integration         ready
```

---

## ⚠️ KNOWN CHALLENGES (Faza 2)

### Challenge 1: IPC Communication

**Issue**: Electron main process ↔ React renderer process communication
**Solution**: Use `preload.ts` + contextBridge pattern
**Risk**: MEDIUM (learning curve for IPC)

### Challenge 2: Backend Auto-start

**Issue**: Start Flask backend from Electron without Python install
**Solution**: Bundle Python runtime (PyInstaller) OR use pre-built backend
**Risk**: SIZE (adds 80-100 MB)

### Challenge 3: Offline Sync

**Issue**: Sync IndexedDB cache with backend when online
**Solution**: Dexie.js + background sync
**Risk**: MEDIUM (complex state management)

### Challenge 4: Auto-update

**Issue**: Safely update MSI without breaking current session
**Solution**: electron-updater + staged rollout
**Risk**: MEDIUM (needs testing matrix)

---

## 📊 EFFORT ESTIMATE (FAZA 2)

| Phase             | Tasks  | Hours     | Risk          |
| ----------------- | ------ | --------- | ------------- |
| Boilerplate (S10) | 9      | 4-5       | 🟢 LOW        |
| Components (S11)  | 6      | 5-6       | 🟡 MEDIUM     |
| Integration (S12) | 4      | 3-4       | 🟡 MEDIUM     |
| **TOTAL**         | **19** | **12-15** | **🟡 MEDIUM** |

**Buffer**: +20% for unknowns = **15-18 hours**
**Recommendation**: Plan 3-4 sessions (not 3)

---

## 🎯 SUCCESS CRITERIA (Faza 2)

### TIER 0: CRITICAL

- [ ] Electron app launches without errors
- [ ] All 4 components render (Dashboard, Agents, Tasks, Log)
- [ ] Backend communication works (health checks + API)
- [ ] MSI installer creates without errors
- [ ] MSI installer runs app successfully

### TIER 1: IMPORTANT

- [ ] Performance: App startup <5 seconds
- [ ] Memory: <300 MB idle (vs 120 MB Faza 1)
- [ ] All features from Faza 1 work identically
- [ ] Styling is professional (Tailwind)
- [ ] Responsive design on 1024x768 minimum

### TIER 2: NICE-TO-HAVE

- [ ] Dark mode toggle
- [ ] Keyboard shortcuts
- [ ] Offline mode indicator
- [ ] Auto-update functionality
- [ ] System tray menu (duplicate from Faza 1?)

---

## 🔄 FAZA 1→2 TRANSITION PLAN

### Keep from Faza 1 ✅

- Python backend (Flask, SQLite)
- API endpoints (/mapi/v1/\*)
- Database schema + data
- Guardian Laws compliance
- Health check protocol

### Replace in Faza 2 🔄

- GUI: pystray → Electron window
- UI Framework: Vanilla JS → React
- Build: PyInstaller → electron-builder
- Distribution: ZIP → MSI
- Runtime: Python subprocess → Node.js

### NEW in Faza 2 ⭐

- IndexedDB offline cache (Dexie.js)
- electron-updater auto-update
- React component library
- MSI silent install option
- Windows registry entries (optional)

---

## 📚 REFERENCES & RESOURCES

### Official Docs

- [Electron Official](https://www.electronjs.org)
- [React 18 Docs](https://react.dev)
- [electron-builder](https://www.electron.build)
- [Vite Build Tool](https://vitejs.dev)
- [Dexie.js Documentation](https://dexie.org)

### Learning Resources

- Electron Security Best Practices
- React Hook Patterns
- MSI Installer Customization
- Auto-update Implementation
- TypeScript + Electron Tips

---

## ✅ PRE-FAZA 2 CHECKLIST

Before starting Session 10, verify:

- [ ] Faza 1 QA is complete (PASS status)
- [ ] Git branch created: `feature/electron-refactor`
- [ ] Node.js 18 LTS installed on dev machine
- [ ] npm version 8+ available
- [ ] VS Code with ESLint + Prettier extensions
- [ ] TypeScript knowledge refreshed
- [ ] React hooks patterns studied

---

## 🎓 FAZA 2 LEARNING OBJECTIVES

By end of Faza 2, you will have:

1. ✅ Built native desktop app with Electron
2. ✅ Migrated UI to React components
3. ✅ Implemented IPC communication bridge
4. ✅ Created professional MSI installer
5. ✅ Implemented offline sync capability
6. ✅ Setup auto-update framework

---

**Document Version**: 1.0
**Created**: 6 kwietnia 2026
**Status**: Planning Complete - Ready for Session 10
**Recommended Start**: End of Session 9 (after Faza 1 QA PASS)

---

Next: Manual QA Testing (Session 9) → Faza 2 Electron (Sessions 10-12)
