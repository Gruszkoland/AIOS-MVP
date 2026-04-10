# FAZA 2 START PLAN — Session 10 (Electron Desktop App)

**Date**: 2026-04-08
**Goal**: Set up Electron development environment + boilerplate
**Duration**: 4-5 hours
**Output**: Ready for React component migration (Session 11)

---

## 🎯 Session 10 Objectives

### Primary Goals

1. ✅ Initialize Node.js Electron project
2. ✅ Create main process (Electron window)
3. ✅ Setup IPC bridge (Electron ↔ Backend)
4. ✅ Configure build system (Vite + electron-builder)
5. ✅ Test development environment

### Success Criteria

- [ ] `npm start` launches Electron window
- [ ] Window connects to libg arbitrage backend
- [ ] Hot reload working (Vite)
- [ ] Build create valid executable

---

## 📦 Prerequisites Checklist

Before starting:

```
✅ Node.js 18 LTS installed
   → Check: node --version (expect v18.x)

❌ npm (comes with Node.js)
   → Check: npm --version

❌ Basic Electron knowledge (we'll provide templates)

❌ Python backend running
   → Run in separate terminal: python arbitrage_server.py
```

**Install Node.js if needed**: https://nodejs.org/en/ (LTS)

---

## 📋 Step-by-Step Plan

### PHASE 0: Environment Setup (15 min)

```bash
# 1. Create folder structure
mkdir -p uap/desktop/electron
cd uap/desktop/electron

# 2. Verify Node.js
node --version  # Should be v18.x
npm --version   # Should be v9.x

# 3. Initialize npm project
npm init -y

# 4. Install core dependencies
npm install --save-dev \
  electron \
  vite \
  @vitejs/plugin-react \
  electron-builder \
  electron-updater \
  typescript \
  @types/node \
  @types/react \
  @types/react-dom

npm install \
  react \
  react-dom \
  dexie \
  axios \
  react-router-dom
```

### PHASE 1: Create Electron Main Process (1 hour)

**File**: `src/main/main.ts`

Core functionality:

- App initialization & window creation
- Backend connectivity check
- IPC listeners
- Graceful shutdown

```typescript
import { app, BrowserWindow, ipcMain, Menu } from "electron";
import { createWindow, handleBackendCheck } from "./window-manager";

app.on("ready", () => createWindow());
app.on("window-all-closed", () => app.quit());

ipcMain.handle("check-backend", handleBackendCheck);
```

### PHASE 2: Create Preload Script (30 min)

**File**: `src/main/preload.ts`

Purpose: Secure IPC bridge between renderer & main process

```typescript
import { contextBridge, ipcRenderer } from "electron";

contextBridge.exposeInMainWorld("electron", {
  checkBackend: () => ipcRenderer.invoke("check-backend"),
  onBackendStatus: (callback) => ipcRenderer.on("backend-status", callback),
});
```

### PHASE 3: Create React App Shell (1 hour)

**File**: `src/renderer/App.tsx`

Minimal React setup:

- App container
- Navigation placeholder
- Backend status indicator
- CSS imports (Tailwind)

```tsx
import React, { useEffect, useState } from "react";

export const App: React.FC = () => {
  const [backendStatus, setBackendStatus] = useState("checking...");

  useEffect(() => {
    const checkBackend = async () => {
      const status = await window.electron.checkBackend();
      setBackendStatus(status ? "✅ Connected" : "❌ Offline");
    };
    checkBackend();
  }, []);

  return (
    <div className="w-screen h-screen bg-gray-900 text-white p-4">
      <h1>ADRIAN 369 - Systray</h1>
      <p>Backend: {backendStatus}</p>
    </div>
  );
};
```

### PHASE 4: Configure Build System (45 min)

**Files**:

- `vite.config.ts` — Dev server & build
- `electron-builder.yml` — MSI packaging
- `package.json` scripts

**vite.config.ts**:

```typescript
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: "dist",
    sourcemap: true,
  },
});
```

**package.json** (add scripts):

```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "start": "electron .",
    "pack": "electron-builder --dir",
    "dist": "electron-builder"
  }
}
```

### PHASE 5: Directory Structure (15 min)

Create folders:

```
uap/desktop/electron/
├─ src/
│  ├─ main/
│  │  ├─ main.ts
│  │  ├─ preload.ts
│  │  └─ ipc-handlers.ts
│  └─ renderer/
│     ├─ App.tsx
│     ├─ index.tsx
│     └─ index.css
├─ public/
│  ├─ index.html
│  └─ icon.png
├─ dist/                      # Generated on build
├─ package.json
├─ vite.config.ts
├─ tsconfig.json
└─ electron-builder.yml
```

### PHASE 6: Test Development Build (30 min)

```bash
# Terminal 1: Start Python backend
cd ../../../
python arbitrage_server.py
# Expected: Server running on http://localhost:8002

# Terminal 2: Start Electron dev environment
cd uap/desktop/electron
npm install
npm run dev

# Terminal 3: Start Electron (when dev server is ready)
npm start
# Expected: Electron window opens, shows "Backend: ✅ Connected"
```

---

## 🔧 Configuration Files (Ready to Use)

### `tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "jsx": "react-jsx"
  }
}
```

### `electron-builder.yml`

```yaml
appId: "com.adrion369.systray"
productName: "ADRIAN 369 Systray"
directories:
  buildResources: "assets"
files:
  - dist/
  - node_modules/
  - package.json
win:
  target:
    - msi
    - nsis
  certificateFile: null
  certificatePassword: null
msi:
  oneClick: false
  allowToChangeInstallationDirectory: true
  createDesktopShortcut: true
  createStartMenuShortcut: true
```

---

## 📊 Expected Timeline

```
Phase 0: Env setup        ████░░░░░░░░░░░░░░░░ (15 min)
Phase 1: Main process     ████████░░░░░░░░░░░░ (60 min)
Phase 2: Preload          ████░░░░░░░░░░░░░░░░ (30 min)
Phase 3: React setup      ████████░░░░░░░░░░░░ (60 min)
Phase 4: Build config     ██████░░░░░░░░░░░░░░ (45 min)
Phase 5: Directories      ████░░░░░░░░░░░░░░░░ (15 min)
Phase 6: Testing          ██████░░░░░░░░░░░░░░ (30 min)
─────────────────────────────────────────────────
Total:                   ████████████████░░░░  (~255 min = 4.25 hours)
```

---

## 🚀 Quick Start (Copy-Paste Ready)

### Command Sequence

```powershell
# 1. Navigate to project
cd c:\Users\adiha\"162 demencje w schemacie 369"

# 2. Create Electron project directory
mkdir -p uap/desktop/electron
cd uap/desktop/electron

# 3. Initialize project
npm init -y

# 4. Install dependencies (this will take ~2-3 min)
npm install --save-dev electron vite @vitejs/plugin-react electron-builder typescript @types/node @types/react @types/react-dom
npm install react react-dom dexie axios react-router-dom

# 5. Create source directories
mkdir -p src/main src/renderer public

# 6. Create basic files (see templates below)
# [Then create files from templates provided]

# 7. Test it
npm start
```

---

## ✅ Success Indicators

**After Session 10, you should have:**

1. ✅ `uap/desktop/electron/package.json` with all dependencies
2. ✅ `src/main/main.ts` — Electron app entry point
3. ✅ `src/renderer/App.tsx` — React root component
4. ✅ `npm run dev` works (Vite dev server starts)
5. ✅ `npm start` launches Electron window
6. ✅ Window shows backend connection status
7. ✅ Hot reload works (change code, see live update)

---

## 🔗 Next Steps (Session 11)

With boilerplate complete, Session 11 will:

1. Create Dashboard React component
2. Migrate charts from vanilla JS
3. Implement real-time status updates
4. Add Dexie offline sync

---

## 📚 Reference Documents

- `FAZA_2_ELECTRON_PLANNING.md` — Complete Faza 2 overview
- `LM_STUDIO_INTEGRATION.md` — Backend configuration
- `PHASE2_DAY1_EXECUTION_CHECKLIST_Apr22.md` — Detailed Day 1 plan

---

## 💡 Pro Tips

1. **Keep backend running**: Always have `python arbitrage_server.py` running in separate terminal
2. **Use Vite**: Much faster than Webpack, built-in HMR (hot module reload)
3. **TypeScript**: Helps catch errors early, great IDE support
4. **Dexie.js**: Already configured for offline sync (don't need to install)

---

**Status**: ✅ Ready to Start
**Estimated Duration**: 4-5 hours
**Output**: Electron boilerplate + working dev environment

Ready to begin? Let's go! 🚀
