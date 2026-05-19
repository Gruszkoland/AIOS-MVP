import React, { useEffect, useState } from "react";
import { initializeCache } from "../lib/db";

interface Settings {
  backend_url: string;
  update_interval: number;
  llm_model: string;
}

const SettingsPage: React.FC = () => {
  // Initialize offline database on mount
  useEffect(() => {
    initializeCache();
  }, []);

  const [settings, setSettings] = useState<Settings>({
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
      } catch (e) {
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
      const response = await fetch(
        `${settings.backend_url}/api/arbitrage/status`,
        { signal: AbortSignal.timeout(3000) },
      );
      if (response.ok) {
        alert("✅ Backend connection successful!");
      } else {
        alert(`❌ Backend returned status ${response.status}`);
      }
    } catch (error) {
      alert(`❌ Connection failed: ${String(error)}`);
    }
  };

  return (
    <div className="space-y-6 max-w-2xl">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold mb-2">Settings</h2>
        <p className="text-slate-400">
          Configure ADRIAN 369 application preferences
        </p>
      </div>

      {/* Save Feedback */}
      {saved && (
        <div className="bg-green-950 rounded-lg p-4 border border-green-700 text-green-300">
          ✅ Settings saved successfully
        </div>
      )}

      {/* Settings Form */}
      <div className="bg-slate-900 rounded-lg p-6 border border-slate-700 space-y-6">
        {/* Backend URL */}
        <div>
          <label className="block text-sm font-semibold mb-2">
            Backend URL
          </label>
          <input
            type="text"
            value={settings.backend_url}
            onChange={(e) =>
              setSettings({ ...settings, backend_url: e.target.value })
            }
            className="w-full bg-slate-800 border border-slate-700 rounded px-4 py-2 text-slate-300 placeholder-slate-500 focus:outline-none focus:border-blue-500"
            placeholder="http://localhost:8001"
          />
          <p className="text-xs text-slate-500 mt-1">
            URL of the ADRIAN 369 backend API server
          </p>
          <button
            onClick={handleTestConnection}
            className="mt-2 text-sm px-3 py-1 bg-blue-900 hover:bg-blue-800 border border-blue-700 rounded text-blue-300 transition-colors"
          >
            Test Connection
          </button>
        </div>

        {/* Update Interval */}
        <div>
          <label className="block text-sm font-semibold mb-2">
            Dashboard Update Interval (ms)
          </label>
          <input
            type="number"
            value={settings.update_interval}
            onChange={(e) =>
              setSettings({
                ...settings,
                update_interval: parseInt(e.target.value) || 3000,
              })
            }
            className="w-full bg-slate-800 border border-slate-700 rounded px-4 py-2 text-slate-300 placeholder-slate-500 focus:outline-none focus:border-blue-500"
            min="1000"
            step="100"
          />
          <p className="text-xs text-slate-500 mt-1">
            How often to refresh dashboard data (minimum: 1000ms)
          </p>
        </div>

        {/* LLM Model Selection */}
        <div>
          <label className="block text-sm font-semibold mb-2">
            LLM Backend
          </label>
          <select
            value={settings.llm_model}
            onChange={(e) =>
              setSettings({ ...settings, llm_model: e.target.value })
            }
            className="w-full bg-slate-800 border border-slate-700 rounded px-4 py-2 text-slate-300 focus:outline-none focus:border-blue-500"
          >
            <option value="lmstudio">LM Studio (Local)</option>
            <option value="ollama">Ollama (Local)</option>
            <option value="openrouter">OpenRouter (Cloud)</option>
          </select>
          <p className="text-xs text-slate-500 mt-1">
            AI model backend for arbitrage analysis
          </p>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-4">
        <button
          onClick={handleSave}
          className="px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded font-semibold text-white transition-colors"
        >
          💾 Save Settings
        </button>
        <button
          onClick={handleReset}
          className="px-6 py-2 bg-slate-700 hover:bg-slate-600 rounded font-semibold text-slate-300 transition-colors"
        >
          🔄 Reset to Default
        </button>
      </div>

      {/* Info Section */}
      <div className="bg-slate-900 rounded-lg p-6 border border-slate-700">
        <h3 className="text-lg font-semibold mb-4">About ADRIAN 369</h3>
        <dl className="space-y-3 text-sm text-slate-300">
          <div>
            <dt className="text-slate-500 font-semibold">Version</dt>
            <dd className="font-mono text-slate-400">2.0.0 (Faza 2)</dd>
          </div>
          <div>
            <dt className="text-slate-500 font-semibold">Built With</dt>
            <dd className="font-mono text-slate-400">
              Electron + React + Vite + Dexie
            </dd>
          </div>
          <div>
            <dt className="text-slate-500 font-semibold">Offline Support</dt>
            <dd className="font-mono text-slate-400">✅ IndexedDB Caching</dd>
          </div>
          <div>
            <dt className="text-slate-500 font-semibold">Session</dt>
            <dd className="font-mono text-slate-400">Session 11</dd>
          </div>
        </dl>
      </div>

      {/* Offline Mode Info */}
      <div className="bg-purple-950 rounded-lg p-6 border border-purple-700">
        <h3 className="text-lg font-semibold mb-3 text-purple-300">
          📦 Offline Mode & Dexie
        </h3>
        <ul className="space-y-2 text-sm text-slate-300">
          <li>✅ Automatic caching of jobs, KPIs, and backend status</li>
          <li>✅ Falls back to cached data when backend unreachable</li>
          <li>✅ Syncs with backend when connection restored</li>
          <li>✅ Cleans up data older than 24 hours</li>
          <li>🔄 Your changes persist across app restarts</li>
        </ul>
      </div>
    </div>
  );
};

export default SettingsPage;
