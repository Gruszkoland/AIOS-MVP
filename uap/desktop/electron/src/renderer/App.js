import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { BrowserRouter, Link, Route, Routes } from "react-router-dom";
import DashboardV2 from "./pages/DashboardV2";
import JobsPage from "./pages/JobsPage";
import SettingsPage from "./pages/SettingsPage";
export const App = () => {
    return (_jsx(BrowserRouter, { children: _jsxs("div", { className: "w-screen h-screen bg-slate-950 text-white flex flex-col", children: [_jsx("nav", { className: "bg-slate-900 border-b border-slate-700 px-8 py-4", children: _jsxs("div", { className: "flex items-center justify-between", children: [_jsx("h1", { className: "text-2xl font-bold text-blue-400", children: "ADRIAN 369" }), _jsxs("div", { className: "flex gap-6 text-sm", children: [_jsx(Link, { to: "/", className: "hover:text-blue-400 transition-colors", children: "Dashboard" }), _jsx(Link, { to: "/jobs", className: "hover:text-blue-400 transition-colors", children: "Jobs" }), _jsx(Link, { to: "/settings", className: "hover:text-blue-400 transition-colors", children: "Settings" })] })] }) }), _jsx("main", { className: "flex-1 overflow-auto", children: _jsxs(Routes, { children: [_jsx(Route, { path: "/", element: _jsx(DashboardV2, {}) }), _jsx(Route, { path: "/jobs", element: _jsx(JobsPage, {}) }), _jsx(Route, { path: "/settings", element: _jsx(SettingsPage, {}) })] }) }), _jsx("footer", { className: "bg-slate-900 border-t border-slate-700 px-8 py-3 text-xs text-slate-500", children: _jsx("p", { children: "Faza 2: Electron Desktop App - Session 11 Dashboard Migration" }) })] }) }));
};
export default App;
//# sourceMappingURL=App.js.map