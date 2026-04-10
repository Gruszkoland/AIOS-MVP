import React from "react";
import { BrowserRouter, Link, Route, Routes } from "react-router-dom";
import DashboardV2 from "./pages/DashboardV2";
import JobsPage from "./pages/JobsPage";
import SettingsPage from "./pages/SettingsPage";

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <div className="w-screen h-screen bg-slate-950 text-white flex flex-col">
        {/* Navigation Bar */}
        <nav className="bg-slate-900 border-b border-slate-700 px-8 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-blue-400">ADRIAN 369</h1>
            <div className="flex gap-6 text-sm">
              <Link to="/" className="hover:text-blue-400 transition-colors">
                Dashboard
              </Link>
              <Link
                to="/jobs"
                className="hover:text-blue-400 transition-colors"
              >
                Jobs
              </Link>
              <Link
                to="/settings"
                className="hover:text-blue-400 transition-colors"
              >
                Settings
              </Link>
            </div>
          </div>
        </nav>

        {/* Main Content */}
        <main className="flex-1 overflow-auto">
          <Routes>
            <Route path="/" element={<DashboardV2 />} />
            <Route path="/jobs" element={<JobsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </main>

        {/* Footer */}
        <footer className="bg-slate-900 border-t border-slate-700 px-8 py-3 text-xs text-slate-500">
          <p>Faza 2: Electron Desktop App - Session 11 Dashboard Migration</p>
        </footer>
      </div>
    </BrowserRouter>
  );
};

export default App;
