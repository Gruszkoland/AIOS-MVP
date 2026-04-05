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
    // Command for kubectl operations
    context.subscriptions.push(vscode.commands.registerCommand("adrion.runKubectl", async (command, isLive = false) => {
        const terminal = vscode.window.createTerminal("ADRION K8s");
        terminal.show();
        if (isLive) {
            terminal.sendText(`# Live output (Ctrl+C to stop)`);
        }
        terminal.sendText(command);
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
        body { padding: 10px; font-family: var(--vscode-font-family); color: var(--vscode-foreground); background-color: var(--vscode-sideBar-background); }
        .btn { width: 100%; padding: 8px; margin-bottom: 8px; cursor: pointer; background: var(--vscode-button-background); color: var(--vscode-button-foreground); border: none; text-align: left; border-radius: 2px; }
        .btn:hover { background: var(--vscode-button-hoverBackground); }
        .section-title { font-size: 0.8em; font-weight: bold; margin: 15px 0 8px 0; color: var(--vscode-descriptionForeground); text-transform: uppercase; }
        .status-header { text-align: center; margin-bottom: 20px; border-bottom: 1px solid var(--vscode-divider); padding-bottom: 10px; }
        .logo { font-size: 1.5em; font-weight: 900; letter-spacing: 2px; color: #00FFCC; }
    </style>
</head>
<body>
    <div class="status-header">
        <div class="logo">ADRION 369</div>
        <small>Swarm Intelligence v2.0</small>
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
    <button class="btn" onclick="runTask('shell: ADRION: Start Arbitrage API Test Port')">Start Arbitrage API</button>

    <div class="section-title">Protocols</div>
    <button class="btn" onclick="runTask('ADRION: /audit - Audyt Bezpieczeństwa (Sentinel/Auditor)')">Audit Security</button>
    <button class="btn" onclick="runTask('ADRION: /boost - Dźwignie ROI (Booster)')">Boost ROI (Levers)</button>
    <button class="btn" onclick="runTask('ADRION: /heal - Samonaprawa (Healer)')">Self-Heal System</button>
    <button class="btn" onclick="runTask('ADRION: /sync - Synchronizacja Chronos (SAP)')">Sync Chronos</button>
    <button class="btn" onclick="runTask('shell: ADRION: Predeploy A-11 Validation')">Predeploy A-11</button>

    <div class="section-title">Models & LLM Rollout</div>
    <button class="btn" onclick="runTask('shell: ADRION: Show LLM Ops Dashboard')">LLM Ops Dashboard</button>
    <button class="btn" onclick="runTask('shell: ADRION: Promote LLM Canary 5%')">Promote Canary +5%</button>
    <button class="btn" onclick="runTask('shell: ADRION: Disable LLM Canary')">Emergency Disable LLM</button>
    <button class="btn" onclick="runTask('📊 Show Ollama Models')">List Local Models</button>

    <div class="section-title">Critical Gates</div>
    <button class="btn" onclick="runTask('ADRION: Local Release Gate (A-11 + Reports)')">Local Release Gate (A-11)</button>
    <button class="btn" onclick="runTask('shell: ADRION: Monitor LLM KPI Gate (15m)')">Start KPI Guard (15m)</button>

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