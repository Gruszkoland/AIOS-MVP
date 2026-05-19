# ADRION 369 - Faza 2 Electron Boilerplate Generator (PowerShell)
# Usage: .\init_faza2_electron.ps1

param(
    [string]$ProjectRoot = "."
)

function Log-Success { Write-Host "✅ $args" -ForegroundColor Green }
function Log-Error { Write-Host "❌ $args" -ForegroundColor Red }
function Log-Info { Write-Host "ℹ️  $args" -ForegroundColor Blue }
function Log-Warn { Write-Host "⚠️  $args" -ForegroundColor Yellow }

Write-Host ""
Write-Host "🚀 ADRION 369 - Faza 2 Electron Setup" -ForegroundColor Cyan -NoNewline
Write-Host " (PowerShell)" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Log-Info "Checking prerequisites..."

$Node = $null
try {
    $Node = node --version 2>$null
    Log-Success "Node.js $Node"
}
catch {
    Log-Error "Node.js not installed. Install Node.js 18 LTS first."
    exit 1
}

$Npm = $null
try {
    $Npm = npm --version 2>$null
    Log-Success "npm $Npm"
}
catch {
    Log-Error "npm not installed."
    exit 1
}

# Parse Node version
$NodeVersion = [int]($Node -split '\.')[0].TrimStart('v')
if ($NodeVersion -lt 18) {
    Log-Error "Node.js 18+ required. Current: $Node"
    exit 1
}

Write-Host ""

# Create project structure
Log-Info "Creating project structure..."
$ElectronDir = Join-Path $ProjectRoot "uap\desktop\electron"

@(
    "public",
    "src\main",
    "src\renderer",
    "src\renderer\components",
    "src\renderer\hooks",
    "src\renderer\styles",
    "src\db",
    "src\types"
) | ForEach-Object {
    $Dir = Join-Path $ElectronDir $_
    if (-not (Test-Path $Dir)) {
        New-Item -ItemType Directory -Path $Dir -Force | Out-Null
    }
}
Log-Success "Folders created"

# Change to project directory
Push-Location $ElectronDir

# Initialize npm project
Log-Info "Initializing npm project..."
if (-not (Test-Path "package.json")) {
    npm init -y 2>$null | Out-Null
    Log-Success "package.json created"
}
else {
    Log-Warn "package.json already exists"
}

# Install dependencies
Write-Host ""
Log-Info "Installing dependencies (this may take a few minutes)..."
npm install --save react react-dom axios recharts dexie 2>$null
npm install --save-dev electron electron-builder electron-updater vite "@vitejs/plugin-react" typescript "@types/react" "@types/node" "react-router-dom" 2>$null
Log-Success "Dependencies installed"

# Create TypeScript config
Write-Host ""
Log-Info "Creating configuration files..."

$TsConfig = @'
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
'@
Set-Content -Path "tsconfig.json" -Value $TsConfig
Log-Success "tsconfig.json created"

$TsConfigNode = @'
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
'@
Set-Content -Path "tsconfig.node.json" -Value $TsConfigNode
Log-Success "tsconfig.node.json created"

# Create Vite config
$ViteConfig = @'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000
  }
})
'@
Set-Content -Path "vite.config.ts" -Value $ViteConfig
Log-Success "vite.config.ts created"

# Create electron-builder config
$BuilderConfig = @'
appId: org.adrion369.systray
productName: ADRION-Systray
directories:
  buildResources: public
  output: dist

files:
  - dist
  - node_modules

win:
  certificateFile: null
  target:
    - msi
    - portable

msi:
  installerIcon: public/icon.ico
  uninstallerIcon: public/icon.ico
  allowToChangeInstallationDirectory: false
  oneClick: false
  allowElevation: true
  createDesktopShortcut: true
  createStartMenuShortcut: true
'@
Set-Content -Path "electron-builder.yml" -Value $BuilderConfig
Log-Success "electron-builder.yml created"

# Create main.ts
Log-Info "Creating source files..."
$MainTs = @'
import { app, BrowserWindow, ipcMain } from 'electron'
import path from 'path'

let mainWindow: BrowserWindow | null

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      enableRemoteModule: false
    }
  })

  if (process.env.NODE_ENV === 'development') {
    mainWindow.loadURL('http://localhost:3000')
    mainWindow.webContents.openDevTools()
  } else {
    mainWindow.loadFile(path.join(__dirname, '../renderer/index.html'))
  }

  ipcMain.handle('health-check', async () => {
    try {
      const response = await fetch('http://localhost:8002/mapi/v1/health')
      return response.ok
    } catch {
      return false
    }
  })
}

app.on('ready', createWindow)
app.on('activate', () => { if (mainWindow === null) createWindow() })
app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit() })
'@
Set-Content -Path "src\main\main.ts" -Value $MainTs
Log-Success "main.ts created"

# Create preload.ts
$PreloadTs = @'
import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('electron', {
  healthCheck: () => ipcRenderer.invoke('health-check')
})
'@
Set-Content -Path "src\main\preload.ts" -Value $PreloadTs
Log-Success "preload.ts created"

# Create App.tsx
$AppTsx = @'
import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Dashboard from './components/Dashboard'
import Agents from './components/Agents'
import Tasks from './components/Tasks'
import GenesisLog from './components/GenesisLog'
import './styles/tailwind.css'

function App() {
  return (
    <Router>
      <div className="flex h-screen bg-gray-100">
        <nav className="w-64 bg-gradient-to-b from-blue-600 to-blue-800 text-white">
          <div className="p-6 font-bold text-xl">ADRION 369</div>
          <ul className="space-y-2">
            <li><a href="/" className="block px-4 py-2 hover:bg-blue-700">Dashboard</a></li>
            <li><a href="/agents" className="block px-4 py-2 hover:bg-blue-700">Agents</a></li>
            <li><a href="/tasks" className="block px-4 py-2 hover:bg-blue-700">Tasks</a></li>
            <li><a href="/log" className="block px-4 py-2 hover:bg-blue-700">Genesis Log</a></li>
          </ul>
        </nav>
        <main className="flex-1 overflow-auto p-6">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/agents" element={<Agents />} />
            <Route path="/tasks" element={<Tasks />} />
            <Route path="/log" element={<GenesisLog />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App
'@
Set-Content -Path "src\renderer\App.tsx" -Value $AppTsx
Log-Success "App.tsx created"

# Create component stubs
@("Dashboard", "Agents", "Tasks", "GenesisLog") | ForEach-Object {
    $Component = $_
    $ComponentTsx = @"
import React from 'react'

function $Component() {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h1 className="text-2xl font-bold mb-4">$Component</h1>
      <p className="text-gray-600">Component coming in Session 11...</p>
    </div>
  )
}

export default $Component
"@
    Set-Content -Path "src\renderer\components\${Component}.tsx" -Value $ComponentTsx
}
Log-Success "Component stubs created (Dashboard, Agents, Tasks, GenesisLog)"

# Create index.html
$IndexHtml = @'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ADRION 369 - Systray</title>
</head>
<body>
  <div id="root"></div>
  <script type="module" src="/src/renderer/index.tsx"></script>
</body>
</html>
'@
Set-Content -Path "public\index.html" -Value $IndexHtml
Log-Success "index.html created"

# Create index.tsx
$IndexTsx = @'
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
'@
Set-Content -Path "src\renderer\index.tsx" -Value $IndexTsx
Log-Success "index.tsx created"

# Update package.json scripts
npm pkg set scripts.dev="vite" 2>$null
npm pkg set scripts.build="vite build" 2>$null
npm pkg set scripts.electron="electron ." 2>$null
npm pkg set scripts.start="npm run build && npm run electron" 2>$null
Log-Success "Build scripts configured"

# Return to original directory
Pop-Location

Write-Host ""
Write-Host "✅ Faza 2 Electron boilerplate ready!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. cd uap/desktop/electron"
Write-Host "2. npm run dev     # Start development server"
Write-Host "3. npm run build   # Build for production"
Write-Host "4. npm start       # Run electron app"
Write-Host ""
Write-Host "Documentation: FAZA_2_ELECTRON_PLANNING.md" -ForegroundColor Yellow
Write-Host ""
