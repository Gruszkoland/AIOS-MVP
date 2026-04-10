import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from "react";
import { initializeCache } from "../lib/db";
const SettingsPage = () => {
    // Initialize offline database on mount
    useEffect(() => {
        initializeCache();
    }, []);
    const [settings, setSettings] = useState({
        backend_url: "http://localhost:8001",
        update_interval: 3000,
        llm_model: "lmstudio",
    });
    const [saved, setSaved] = useState(false);
    // Load settings from localStorage on component mount
    useEffect(() => {
        const stored = localStorage.getItem("adrion_settings");
        if (stored) {
            try {
                setSettings(JSON.parse(stored));
            }
            catch (e) {
                console.log("Failed to parse stored settings");
            }
        }
    }, []);
    const handleSave = () => {
        localStorage.setItem("adrion_settings", JSON.stringify(settings));
        localStorage.setItem("backend_url", settings.backend_url);
        setSaved(true);
        setTimeout(() => setSaved(false), 3000);
    };
    const handleReset = () => {
        setSettings({
            backend_url: "http://localhost:8001",
            update_interval: 3000,
            llm_model: "lmstudio",
        });
        localStorage.removeItem("adrion_settings");
        localStorage.removeItem("backend_url");
        setSaved(true);
        setTimeout(() => setSaved(false), 3000);
    };
    const handleTestConnection = async () => {
        try {
            const response = await fetch(`${settings.backend_url}/api/arbitrage/status`, { signal: AbortSignal.timeout(3000) });
            if (response.ok) {
                alert("✅ Backend connection successful!");
            }
            else {
                alert(`❌ Backend returned status ${response.status}`);
            }
        }
        catch (error) {
            alert(`❌ Connection failed: ${String(error)}`);
        }
    };
    return (_jsxs("div", { className: "space-y-6 max-w-2xl", children: [_jsxs("div", { children: [_jsx("h2", { className: "text-3xl font-bold mb-2", children: "Settings" }), _jsx("p", { className: "text-slate-400", children: "Configure ADRIAN 369 application preferences" })] }), saved && (_jsx("div", { className: "bg-green-950 rounded-lg p-4 border border-green-700 text-green-300", children: "\u2705 Settings saved successfully" })), _jsxs("div", { className: "bg-slate-900 rounded-lg p-6 border border-slate-700 space-y-6", children: [_jsxs("div", { children: [_jsx("label", { className: "block text-sm font-semibold mb-2", children: "Backend URL" }), _jsx("input", { type: "text", value: settings.backend_url, onChange: (e) => setSettings({ ...settings, backend_url: e.target.value }), className: "w-full bg-slate-800 border border-slate-700 rounded px-4 py-2 text-slate-300 placeholder-slate-500 focus:outline-none focus:border-blue-500", placeholder: "http://localhost:8001" }), _jsx("p", { className: "text-xs text-slate-500 mt-1", children: "URL of the ADRIAN 369 backend API server" }), _jsx("button", { onClick: handleTestConnection, className: "mt-2 text-sm px-3 py-1 bg-blue-900 hover:bg-blue-800 border border-blue-700 rounded text-blue-300 transition-colors", children: "Test Connection" })] }), _jsxs("div", { children: [_jsx("label", { className: "block text-sm font-semibold mb-2", children: "Dashboard Update Interval (ms)" }), _jsx("input", { type: "number", value: settings.update_interval, onChange: (e) => setSettings({
                                    ...settings,
                                    update_interval: parseInt(e.target.value) || 3000,
                                }), className: "w-full bg-slate-800 border border-slate-700 rounded px-4 py-2 text-slate-300 placeholder-slate-500 focus:outline-none focus:border-blue-500", min: "1000", step: "100" }), _jsx("p", { className: "text-xs text-slate-500 mt-1", children: "How often to refresh dashboard data (minimum: 1000ms)" })] }), _jsxs("div", { children: [_jsx("label", { className: "block text-sm font-semibold mb-2", children: "LLM Backend" }), _jsxs("select", { value: settings.llm_model, onChange: (e) => setSettings({ ...settings, llm_model: e.target.value }), className: "w-full bg-slate-800 border border-slate-700 rounded px-4 py-2 text-slate-300 focus:outline-none focus:border-blue-500", children: [_jsx("option", { value: "lmstudio", children: "LM Studio (Local)" }), _jsx("option", { value: "ollama", children: "Ollama (Local)" }), _jsx("option", { value: "openrouter", children: "OpenRouter (Cloud)" })] }), _jsx("p", { className: "text-xs text-slate-500 mt-1", children: "AI model backend for arbitrage analysis" })] })] }), _jsxs("div", { className: "flex gap-4", children: [_jsx("button", { onClick: handleSave, className: "px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded font-semibold text-white transition-colors", children: "\uD83D\uDCBE Save Settings" }), _jsx("button", { onClick: handleReset, className: "px-6 py-2 bg-slate-700 hover:bg-slate-600 rounded font-semibold text-slate-300 transition-colors", children: "\uD83D\uDD04 Reset to Default" })] }), _jsxs("div", { className: "bg-slate-900 rounded-lg p-6 border border-slate-700", children: [_jsx("h3", { className: "text-lg font-semibold mb-4", children: "About ADRIAN 369" }), _jsxs("dl", { className: "space-y-3 text-sm text-slate-300", children: [_jsxs("div", { children: [_jsx("dt", { className: "text-slate-500 font-semibold", children: "Version" }), _jsx("dd", { className: "font-mono text-slate-400", children: "2.0.0 (Faza 2)" })] }), _jsxs("div", { children: [_jsx("dt", { className: "text-slate-500 font-semibold", children: "Built With" }), _jsx("dd", { className: "font-mono text-slate-400", children: "Electron + React + Vite + Dexie" })] }), _jsxs("div", { children: [_jsx("dt", { className: "text-slate-500 font-semibold", children: "Offline Support" }), _jsx("dd", { className: "font-mono text-slate-400", children: "\u2705 IndexedDB Caching" })] }), _jsxs("div", { children: [_jsx("dt", { className: "text-slate-500 font-semibold", children: "Session" }), _jsx("dd", { className: "font-mono text-slate-400", children: "Session 11" })] })] })] }), _jsxs("div", { className: "bg-purple-950 rounded-lg p-6 border border-purple-700", children: [_jsx("h3", { className: "text-lg font-semibold mb-3 text-purple-300", children: "\uD83D\uDCE6 Offline Mode & Dexie" }), _jsxs("ul", { className: "space-y-2 text-sm text-slate-300", children: [_jsx("li", { children: "\u2705 Automatic caching of jobs, KPIs, and backend status" }), _jsx("li", { children: "\u2705 Falls back to cached data when backend unreachable" }), _jsx("li", { children: "\u2705 Syncs with backend when connection restored" }), _jsx("li", { children: "\u2705 Cleans up data older than 24 hours" }), _jsx("li", { children: "\uD83D\uDD04 Your changes persist across app restarts" })] })] })] }));
};
export default SettingsPage;
//# sourceMappingURL=SettingsPage.js.map