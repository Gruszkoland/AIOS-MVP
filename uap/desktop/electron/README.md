# ADRIAN 369 - Electron Desktop App (Faza 2)

## Setup

```bash
npm install
npm run dev      # Start dev server
npm start         # Launch Electron window
```

## Build

```bash
npm run build     # Build renderer
npm run pack      # Package (no installer)
npm run dist      # Build MSI installer
```

## Project Structure

```
src/
 ├─ main/        Electron main process
 ├─ renderer/    React components
 └─ types/       TypeScript definitions

public/          Static assets
dist/            Build output
```

## Features

- ✅ Electron 24+
- ✅ React 18 + TypeScript
- ✅ Vite dev server (HMR)
- ✅ MSI/NSIS installer
- ✅ Backend API integration
- ✅ IPC bridge for system access

## Status

**Phase**: Session 10 - Boilerplate
**Version**: 2.0.0
**Ready for**: Session 11 component migration

## Next: Session 11

- Dashboard component from Faza 1
- Real-time status updates
- Dexie offline sync
- Advanced UI/UX
