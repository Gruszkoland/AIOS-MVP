#!/bin/bash
# ADRION 369 - Faza 2 Electron Boilerplate Generator
# This script initializes the Electron project structure for Faza 2

set -e

echo "🚀 ADRION 369 - Faza 2 Electron Setup"
echo "===================================="
echo ""

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v node &> /dev/null; then
    echo "❌ Node.js not installed. Install Node.js 18 LTS first."
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ npm not installed."
    exit 1
fi

NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Node.js 18+ required. Current: $(node -v)"
    exit 1
fi

echo "✅ Node.js $(node -v)"
echo "✅ npm $(npm -v)"
echo ""

# Create project structure
echo "📁 Creating project structure..."

PROJECT_ROOT="${1:-.}"
ELECTRON_DIR="$PROJECT_ROOT/uap/desktop/electron"

mkdir -p "$ELECTRON_DIR"/{public,src/{main,renderer,db,types},src/renderer/components,src/renderer/hooks,src/renderer/styles}

echo "✅ Folders created"
echo ""

# Change to project directory
cd "$ELECTRON_DIR"

# Initialize npm project
echo "📦 Initializing npm project..."
if [ ! -f package.json ]; then
    npm init -y > /dev/null
    echo "✅ package.json created"
else
    echo "⚠️  package.json already exists"
fi
echo ""

# Install dependencies
echo "📥 Installing dependencies (this may take a few minutes)..."
npm install --save react react-dom axios recharts dexie > /dev/null 2>&1
npm install --save-dev electron electron-builder electron-updater vite @vitejs/plugin-react typescript @types/react @types/node > /dev/null 2>&1
echo "✅ Dependencies installed"
echo ""

# Create TypeScript config
echo "🔧 Creating configuration files..."

cat > tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,

    /* Bundler mode */
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "noEmit": true,
    "jsx": "react-jsx",

    /* Linting */
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
EOF
echo "✅ tsconfig.json created"

cat > tsconfig.node.json << 'EOF'
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
EOF
echo "✅ tsconfig.node.json created"

# Create Vite config
cat > vite.config.ts << 'EOF'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000
  }
})
EOF
echo "✅ vite.config.ts created"

# Create electron-builder config
cat > electron-builder.yml << 'EOF'
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
EOF
echo "✅ electron-builder.yml created"

# Update package.json scripts
echo "📝 Updating package.json..."
npm pkg set scripts.dev="vite" > /dev/null
npm pkg set scripts.build="vite build" > /dev/null
npm pkg set scripts.electron="electron ." > /dev/null
npm pkg set scripts.start="npm run build && npm run electron" > /dev/null
echo "✅ Build scripts configured"
echo ""

# Create main.ts
echo "📄 Creating Electron main process..."
cat > src/main/main.ts << 'EOF'
import { app, BrowserWindow, ipcMain } from 'electron'
import path from 'path'

let mainWindow: BrowserWindow | null

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js')
    }
  })

  // Load dev server or built app
  if (process.env.NODE_ENV === 'development') {
    mainWindow.loadURL('http://localhost:3000')
    mainWindow.webContents.openDevTools()
  } else {
    mainWindow.loadFile(path.join(__dirname, '../renderer/index.html'))
  }

  // Health check endpoint
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

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow()
  }
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})
EOF
echo "✅ main.ts created"

# Create preload.ts
cat > src/main/preload.ts << 'EOF'
import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('electron', {
  healthCheck: () => ipcRenderer.invoke('health-check'),
  getVersion: () => process.env.npm_package_version
})
EOF
echo "✅ preload.ts created"

# Create React App.tsx
cat > src/renderer/App.tsx << 'EOF'
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
EOF
echo "✅ App.tsx created"

# Create component stubs
for component in Dashboard Agents Tasks GenesisLog; do
  cat > "src/renderer/components/${component}.tsx" << EOF
import React from 'react'

function ${component}() {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h1 className="text-2xl font-bold mb-4">${component}</h1>
      <p className="text-gray-600">Component coming in Session 11...</p>
    </div>
  )
}

export default ${component}
EOF
done
echo "✅ Component stubs created"

# Create index.html
cat > public/index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ADRION 369 - Systray</title>
</head>
<body className="bg-gray-100">
  <div id="root"></div>
  <script type="module" src="/src/renderer/index.tsx"></script>
</body>
</html>
EOF
echo "✅ index.html created"

# Create React entry point
cat > src/renderer/index.tsx << 'EOF'
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
EOF
echo "✅ index.tsx created"

echo ""
echo "✅ Faza 2 Electron boilerplate ready!"
echo ""
echo "Next steps:"
echo "1. npm run dev     # Start development server"
echo "2. npm run build   # Build for production"
echo "3. npm start       # Run electron app"
echo ""
echo "Documentation: FAZA_2_ELECTRON_PLANNING.md"
EOF
