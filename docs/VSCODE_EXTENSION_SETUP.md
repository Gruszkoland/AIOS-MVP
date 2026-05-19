# ADRION 369 VS Code Extension — Installation & Usage

**Status:** Ready to install
**Version:** 2.0 with K8s support
**Time:** 5 minutes

---

## Installation

### Option 1: Install from VSIX (Recommended)

#### 1.1 Build the extension

```bash
cd "C:\Users\adiha\162 demencje w schemacie 369\vscode-extension-adrion"

# Install dependencies
npm install

# Build
npm run compile

# Package as VSIX
npm install -g @vscode/vsce
vsce package
```

This creates `adrion-369-extension-2.0.0.vsix`

#### 1.2 Install in VS Code

**Method A: Via Command Palette**
1. Open VS Code
2. Press `Ctrl+Shift+P`
3. Type `Extensions: Install from VSIX...`
4. Select `adrion-369-extension-2.0.0.vsix`
5. Click `Install`
6. Reload VS Code

**Method B: Via File Explorer**
1. Open File Explorer
2. Navigate to `vscode-extension-adrion/`
3. Double-click `adrion-369-extension-2.0.0.vsix`
4. VS Code opens → Click `Install`
5. Reload

---

### Option 2: Load Extension in Development Mode

If you want to develop/modify the extension:

```bash
# Open in VS Code
code "C:\Users\adiha\162 demencje w schemacie 369\vscode-extension-adrion"

# In VS Code:
# 1. Press F5 (Start Debugging)
# 2. New VS Code window opens with extension loaded
# 3. Make changes, they reload automatically
```

---

## Usage

### After Installation

1. Open VS Code
2. Look for **ADRION 369** icon in Activity Bar (left sidebar)
3. Click it to open **Swarm Dashboard**

You now have two sections:

#### 🐳 Kubernetes (Local)

**Status Commands:**
- 📊 List Pods
- 🔗 List Services
- 📈 HPA Status
- 📋 Backend Status

**Logs & Port Forwarding:**
- 📝 Backend Logs (Live) — Follow backend logs in terminal
- 🔀 Port Forward Backend — Open http://localhost:8002
- 🔀 Port Forward Frontend — Open http://localhost:8003

**Database:**
- 🗄️ Query Database — Run SQL queries

**Pod Management:**
- 🔄 Restart Backend Pods
- 🔄 Restart Backend Deployment
- 📈 Scale Backend (5 replicas)

**Debugging:**
- 💻 Node Resources
- 📦 Pod Resources
- 💾 Storage Status
- ⚠️ Recent Events

**Testing:**
- ✅ Test Backend API
- ✅ Test Frontend

#### Core Operations (Original)

All existing commands still available:
- 🚀 Start Ollama Server
- 🤖 Start Aider
- ✅ Check System Status
- etc.

---

## Common Workflows

### Workflow 1: Check Deployment Status

1. Click **📊 List Pods** → Terminal shows pod list
2. Click **📈 HPA Status** → Check auto-scaling
3. Click **⚠️ Recent Events** → See what happened recently

### Workflow 2: Debug Backend Issue

1. Click **📝 Backend Logs (Live)** → See live logs
2. Click **📋 Backend Status** → Get detailed status
3. Click **💻 Node Resources** → Check if out of memory
4. Click **🔄 Restart Backend Pods** → Restart and check again

### Workflow 3: Test Changes

1. Edit backend code
2. Click **🔄 Restart Backend Deployment** → Redeploy
3. Click **📝 Backend Logs (Live)** → Watch for errors
4. Click **🔀 Port Forward Backend** → Test API

### Workflow 4: Manual Scaling

1. Click **📈 Scale Backend (5 replicas)** → Scale to 5
2. Click **📊 List Pods** → Verify pods created
3. Click **📈 HPA Status** → Check HPA status

### Workflow 5: Database Query

1. Click **🗄️ Query Database** → Opens terminal
2. Terminal shows query result
3. Modify query as needed

---

## Keyboard Shortcuts (Optional)

Add to VS Code `keybindings.json`:

```json
[
  {
    "key": "ctrl+shift+k",
    "command": "adrion.runKubectl",
    "args": ["kubectl get pods -n adrion"]
  },
  {
    "key": "ctrl+shift+l",
    "command": "adrion.runKubectl",
    "args": ["kubectl logs -f deployment/uap-backend -n adrion", true]
  },
  {
    "key": "ctrl+shift+f",
    "command": "adrion.runKubectl",
    "args": ["kubectl port-forward svc/uap-backend 8002:8002 -n adrion"]
  }
]
```

Then use:
- `Ctrl+Shift+K` → List Pods
- `Ctrl+Shift+L` → Backend Logs
- `Ctrl+Shift+F` → Port Forward

---

## Troubleshooting

### Extension not loading?

1. Check installation: `VS Code → Extensions → ADRION 369`
2. Should show "Installed" status
3. Reload VS Code (`Ctrl+Shift+P` → "Reload Window")

### Terminal not opening?

1. Go to VS Code Settings
2. Search for "Always Use Split Terminal"
3. Make sure it's enabled
4. Try again

### K8s commands not working?

1. Open terminal in VS Code (`Ctrl+\``)
2. Run: `kubectl cluster-info`
3. Should return cluster info
4. If not, Docker Desktop K8s not enabled

### Extension crashes?

1. Press `Ctrl+Shift+P`
2. Type "Toggle Developer Tools"
3. Look for error messages
4. Report issue with error output

---

## Extension Code Structure

```
vscode-extension-adrion/
├── extension.js              # Main activation + commands
├── package.json              # Extension metadata
├── media/
│   ├── icon.svg             # Activity bar icon
│   ├── main.css             # Styling
│   ├── reset.css            # CSS reset
│   └── vscode.css           # VS Code theme
└── README.md                # Extension docs
```

### To Modify

1. Edit `extension.js` (add new commands)
2. Edit `media/main.css` (change styling)
3. Press F5 to reload in debug mode

---

## What Each Command Does

### Kubernetes Section

| Button | Command | Opens | Usage |
|--------|---------|-------|-------|
| 📊 List Pods | `kubectl get pods -n adrion` | Terminal | See all running pods |
| 🔗 List Services | `kubectl get svc -n adrion` | Terminal | See internal IPs/ports |
| 📈 HPA Status | `kubectl get hpa -n adrion` | Terminal | Check auto-scaling status |
| 📝 Backend Logs | `kubectl logs -f deployment/uap-backend` | Terminal | Follow logs (live) |
| 🔀 Port Forward Backend | `kubectl port-forward svc/uap-backend 8002:8002` | Terminal | Access http://localhost:8002 |
| 🔀 Port Forward Frontend | `kubectl port-forward svc/uap-frontend 8003:8003` | Terminal | Access http://localhost:8003 |
| 🗄️ Query Database | `kubectl exec -it postgres-0 -- psql -U adrion -d genesis_record` | Terminal | SQL shell to database |
| 🔄 Restart Pods | `kubectl delete pod -l app=uap-backend -n adrion` | Terminal | Force pod restart |
| 📊 Deploy All | `kubectl apply -f kubernetes/*.yaml` | Terminal | Full deployment |
| 📋 Backend Status | `kubectl describe deployment uap-backend -n adrion` | Terminal | Detailed deployment info |
| 📈 Scale Backend | `kubectl scale deployment uap-backend --replicas=5` | Terminal | Change replica count |
| 🔄 Restart Deployment | `kubectl rollout restart deployment/uap-backend` | Terminal | Rolling restart |
| ⚠️ Recent Events | `kubectl get events -n adrion` | Terminal | See cluster events |
| 💻 Node Resources | `kubectl top nodes` | Terminal | CPU/memory usage by node |
| 📦 Pod Resources | `kubectl top pod -n adrion` | Terminal | CPU/memory usage by pod |
| 🖥️ Node Details | `kubectl describe node docker-desktop` | Terminal | Full node info |
| 💾 Storage Status | `kubectl get pvc -n adrion` | Terminal | Persistent volumes status |
| ℹ️ Cluster Info | `kubectl cluster-info` | Terminal | Cluster endpoints |
| 🌐 Nodes | `kubectl get nodes` | Terminal | Node list |
| 📂 Namespaces | `kubectl get ns` | Terminal | All namespaces |
| 📌 K8s Version | `kubectl version --short` | Terminal | Kubernetes version |
| ✅ Test Backend API | `curl -H "X-API-Key: local-dev-key-123" http://localhost:8002/mapi/v1/status` | Terminal | HTTP test |
| ✅ Test Frontend | `curl http://localhost:8003` | Terminal | Frontend test |

---

## Tips & Tricks

### Tip 1: Keep terminal open
When you click a command, terminal opens and closes after command completes. To keep it open:
- Open persistent terminal: `Ctrl+\``
- Click commands (they run in that terminal)
- Terminal stays open for next command

### Tip 2: Copy commands
Any command shown can be copied and pasted into terminal for custom variations:
```
# Click "📊 List Pods" shows:
kubectl get pods -n adrion

# Copy and modify:
kubectl get pods -n adrion -w  # Add -w for watch
```

### Tip 3: Port forward persistence
To keep port forward running:
1. Open terminal: `Ctrl+\``
2. Click "🔀 Port Forward Backend"
3. Terminal runs and stays running
4. Open `http://localhost:8002` in browser
5. Close terminal when done

---

## Next Steps

1. ✅ Install extension (copy-paste commands above)
2. ✅ Enable K8s in Docker Desktop
3. ✅ Deploy: `kubectl apply -f kubernetes/*.yaml`
4. ✅ Use extension commands to manage deployment
5. ✅ Monitor logs and resources in VS Code

---

**Status:** 🟢 READY TO INSTALL
**Test it:** Follow "Common Workflows" section above
