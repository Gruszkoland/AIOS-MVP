"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || function (mod) {
    if (mod && mod.__esModule) return mod;
    var result = {};
    if (mod != null) for (var k in mod) if (k !== "default" && Object.prototype.hasOwnProperty.call(mod, k)) __createBinding(result, mod, k);
    __setModuleDefault(result, mod);
    return result;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.deactivate = exports.activate = void 0;
const vscode = __importStar(require("vscode"));
/**
 * Activate extension
 */
function activate(context) {
    console.log("ADRION 369 Extension is active");
    const provider = new AdrionViewProvider(context.extensionUri);
    // Shared terminal instance (reuse across commands)
    let sharedTerminal;
    context.subscriptions.push(vscode.window.registerWebviewViewProvider(AdrionViewProvider.viewType, provider));
    context.subscriptions.push(vscode.commands.registerCommand("adrion.runTask", async (taskLabel) => {
        const tasks = await vscode.tasks.fetchTasks();
        const task = tasks.find((t) => t.name === taskLabel);
        if (task) {
            vscode.tasks.executeTask(task);
        }
        else {
            vscode.window.showErrorMessage(`Task "${taskLabel}" not found.`);
        }
    }));
    // Command for kubectl operations with shared terminal
    context.subscriptions.push(vscode.commands.registerCommand("adrion.runKubectl", async (command, isLive = false) => {
        // Reuse existing terminal if still exists
        if (!sharedTerminal || sharedTerminal.exitStatus !== undefined) {
            sharedTerminal = vscode.window.createTerminal("ADRION K8s");
        }
        sharedTerminal.show();
        if (isLive) {
            sharedTerminal.sendText(`# Live output (Ctrl+C to stop)`);
        }
        sharedTerminal.sendText(command);
    }));
}
exports.activate = activate;
class AdrionViewProvider {
    constructor(_extensionUri) {
        this._extensionUri = _extensionUri;
    }
    resolveWebviewView(webviewView, _context, _token) {
        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._extensionUri],
        };
        webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);
        webviewView.webview.onDidReceiveMessage((data) => {
            switch (data.type) {
                case "runTask":
                    vscode.commands.executeCommand("adrion.runTask", data.value);
                    break;
                case "runKubectl":
                    vscode.commands.executeCommand("adrion.runKubectl", data.value, data.isLive);
                    break;
            }
        });
    }
    _getHtmlForWebview(webview) {
        const styleResetUri = webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, "media", "reset.css"));
        const styleVSCodeUri = webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, "media", "vscode.css"));
        const styleMainUri = webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, "media", "main.css"));
        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="${styleResetUri}" rel="stylesheet">
    <link href="${styleVSCodeUri}" rel="stylesheet">
    <link href="${styleMainUri}" rel="stylesheet">
    <title>ADRION 369 Control Panel</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            padding: 12px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            color: #2C3E50;
            background-color: #F5F5F5;
            line-height: 1.5;
        }

        .btn {
            width: 100%;
            padding: 10px 12px;
            margin-bottom: 8px;
            cursor: pointer;
            background: linear-gradient(135deg, #0078D4 0%, #0066CC 100%);
            color: #FFFFFF;
            border: 1px solid #0066CC;
            text-align: left;
            border-radius: 4px;
            font-weight: 500;
            font-size: 0.95em;
            transition: all 0.2s ease;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .btn:hover {
            background: linear-gradient(135deg, #0066CC 0%, #0052A3 100%);
            box-shadow: 0 2px 6px rgba(0, 102, 204, 0.3);
            transform: translateY(-1px);
        }

        .btn:active {
            transform: translateY(0);
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .btn.success:hover { background: linear-gradient(135deg, #27AE60 0%, #229954 100%); }
        .btn.danger:hover { background: linear-gradient(135deg, #E74C3C 0%, #C0392B 100%); }

        .section-title {
            font-size: 0.75em;
            font-weight: 700;
            margin: 18px 0 10px 0;
            color: #1E3A5F;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-left: 3px solid #0078D4;
            padding-left: 8px;
        }

        .status-header {
            text-align: center;
            margin-bottom: 20px;
            border-bottom: 2px solid #0078D4;
            padding-bottom: 12px;
            background: linear-gradient(135deg, #FFFFFF 0%, #F8F9FA 100%);
            border-radius: 4px;
            padding: 12px;
        }

        .logo {
            font-size: 1.6em;
            font-weight: 900;
            letter-spacing: 2px;
            background: linear-gradient(135deg, #0078D4 0%, #0066CC 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .subtitle {
            font-size: 0.85em;
            color: #666;
            font-weight: 500;
        }

        .status-badge {
            display: inline-block;
            padding: 2px 8px;
            background: #E8F4F8;
            color: #0078D4;
            border-radius: 12px;
            font-size: 0.75em;
            font-weight: 600;
            margin: 5px 0;
        }
    </style>
</head>
<body>
    <div class="status-header">
        <div class="logo">ADRION 369</div>
        <div class="subtitle">Swarm Intelligence v2.0</div>
        <div class="status-badge">🟢 Production Ready</div>
    </div>

    <div class="section-title">🐳 Kubernetes (Local)</div>
    <button class="btn" onclick="runKubectlCommand('kubectl get pods -n adrion')">📊 List Pods</button>
    <button class="btn" onclick="runKubectlCommand('kubectl get svc -n adrion')">🔗 List Services</button>
    <button class="btn" onclick="runKubectlCommand('kubectl get hpa -n adrion')">📈 HPA Status</button>
    <button class="btn" onclick="runKubectlCommand('kubectl logs -f deployment/uap-backend -n adrion', true)">📝 Backend Logs (Live)</button>
    <button class="btn" onclick="runKubectlCommand('kubectl port-forward svc/uap-backend 8002:8002 -n adrion')">🔀 Port Forward Backend</button>
    <button class="btn" onclick="runKubectlCommand('kubectl port-forward svc/uap-frontend 8003:8003 -n adrion')">🔀 Port Forward Frontend</button>
    <button class="btn" onclick="runKubectlCommand('kubectl exec -it postgres-0 -n adrion -- psql -U adrion -d genesis_record -c \\"SELECT COUNT(*) FROM tasks;\\"')">🗄️ Query Database</button>
    <button class="btn" onclick="runKubectlCommand('kubectl delete pod -l app=uap-backend -n adrion')">🔄 Restart Backend Pods</button>

    <div class="section-title">📊 Deployment & Scaling</div>
    <button class="btn" onclick="runKubectlCommand('kubectl apply -f kubernetes/*.yaml')">🚀 Deploy All</button>
    <button class="btn" onclick="runKubectlCommand('kubectl describe deployment uap-backend -n adrion')">📋 Backend Status</button>
    <button class="btn" onclick="runKubectlCommand('kubectl scale deployment uap-backend --replicas=5 -n adrion')">📈 Scale Backend (5 replicas)</button>
    <button class="btn" onclick="runKubectlCommand('kubectl rollout restart deployment/uap-backend -n adrion')">🔄 Restart Backend Deployment</button>
    <button class="btn" onclick="runKubectlCommand('kubectl get events -n adrion --sort-by=.metadata.creationTimestamp | tail -20')">⚠️ Recent Events</button>

    <div class="section-title">🔍 Debugging</div>
    <button class="btn" onclick="runKubectlCommand('kubectl top nodes')">💻 Node Resources</button>
    <button class="btn" onclick="runKubectlCommand('kubectl top pod -n adrion')">📦 Pod Resources</button>
    <button class="btn" onclick="runKubectlCommand('kubectl describe node docker-desktop')">🖥️ Node Details</button>
    <button class="btn" onclick="runKubectlCommand('kubectl get pvc -n adrion')">💾 Storage Status</button>

    <div class="section-title">⚙️ Cluster Info</div>
    <button class="btn" onclick="runKubectlCommand('kubectl cluster-info')">ℹ️ Cluster Info</button>
    <button class="btn" onclick="runKubectlCommand('kubectl get nodes')">🌐 Nodes</button>
    <button class="btn" onclick="runKubectlCommand('kubectl get ns')">📂 Namespaces</button>
    <button class="btn" onclick="runKubectlCommand('kubectl version --short')">📌 K8s Version</button>

    <div class="section-title">🧪 Testing</div>
    <button class="btn" onclick="runKubectlCommand('curl -H \\"X-API-Key: local-dev-key-123\\" http://localhost:8002/mapi/v1/status')">✅ Test Backend API</button>
    <button class="btn" onclick="runKubectlCommand('curl http://localhost:8003')">✅ Test Frontend</button>

    <div class="section-title">Core Operations</div>
    <button class="btn" onclick="runTask('🚀 Start Ollama Server')">Start Ollama Server</button>
    <button class="btn" onclick="runTask('🤖 Start Aider (Librarian Mode)')">Start Aider (Swarm Mode)</button>
    <button class="btn" onclick="runTask('✅ Check System Status')">System Status Check</button>
    <button class="btn" onclick="runTask('ADRION: Start Arbitrage API Test Port')">Start Arbitrage API</button>

    <div class="section-title">Protocols</div>
    <button class="btn" onclick="runTask('ADRION: /audit - Audyt Bezpieczeństwa (Sentinel/Auditor)')">Audit Security</button>
    <button class="btn" onclick="runTask('ADRION: /boost - Dźwignie ROI (Booster)')">Boost ROI (Levers)</button>
    <button class="btn" onclick="runTask('ADRION: /heal - Samonaprawa (Healer)')">Self-Heal System</button>
    <button class="btn" onclick="runTask('ADRION: /sync - Synchronizacja Chronos (SAP)')">Sync Chronos</button>
    <button class="btn" onclick="runTask('ADRION: Predeploy A-11 Validation')">Predeploy A-11</button>

    <div class="section-title">Models & LLM Rollout</div>
    <button class="btn" onclick="runTask('ADRION: Show LLM Ops Dashboard')">LLM Ops Dashboard</button>
    <button class="btn" onclick="runTask('ADRION: Promote LLM Canary 5%')">Promote Canary +5%</button>
    <button class="btn" onclick="runTask('ADRION: Disable LLM Canary')">Emergency Disable LLM</button>
    <button class="btn" onclick="runTask('📊 Show Ollama Models')">List Local Models</button>

    <div class="section-title">Critical Gates</div>
    <button class="btn" onclick="runTask('ADRION: Local Release Gate (A-11 + Reports)')">Local Release Gate (A-11)</button>
    <button class="btn" onclick="runTask('ADRION: Monitor LLM KPI Gate (15m)')">Start KPI Guard (15m)</button>

    <script>
        const vscode = acquireVsCodeApi();

        function runTask(label) {
            vscode.postMessage({ type: 'runTask', value: label });
        }

        function runKubectlCommand(command, isLive = false) {
            vscode.postMessage({
                type: 'runKubectl',
                value: command,
                isLive: isLive
            });
        }
    </script>
</body>
</html>`;
    }
}
AdrionViewProvider.viewType = "adrion-control-view";
function deactivate() { }
exports.deactivate = deactivate;
//# sourceMappingURL=extension.js.map