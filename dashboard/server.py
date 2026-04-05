"""
ADRION 369 — UAP Admin Dashboard Server
Serves the dashboard UI on port 8003 and provides a REST API
that bridges the frontend to arbitrage-api (8001) and Docker services.

Usage:
    python dashboard/server.py
    python dashboard/server.py --port 8003 --api http://localhost:8001

Endpoints:
    GET  /                  → index.html
    GET  /api/status        → aggregated system status
    GET  /api/agents        → agent state from arbitrage api
    GET  /api/logs          → recent log lines
    GET  /api/genesis       → Genesis Record entries
    POST /api/control/start → start all services (admin.ps1 start)
    POST /api/control/stop  → stop all services
    POST /api/control/restart/<service> → restart one service
    POST /api/control/backup → trigger backup
    GET  /api/health        → dashboard server health
"""

from __future__ import annotations

import argparse
import hmac
import json
import logging
import os
import pathlib
import subprocess
import time
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

# ── Config ────────────────────────────────────────────────────────────────────
DASHBOARD_DIR = pathlib.Path(__file__).parent
ROOT_DIR      = DASHBOARD_DIR.parent
DEFAULT_PORT  = int(os.environ.get("UAP_FRONTEND_PORT", 8003))
ARB_API       = os.environ.get("ARBITRAGE_API_BASE", "http://127.0.0.1:8001")
ADMIN_SCRIPT  = str(ROOT_DIR / "admin.ps1")
LOG_DIR       = ROOT_DIR / "logs"
GENESIS_DIR   = ROOT_DIR / "Genesis Record" / "10_RAPORTY_DZIALANIA_SYSTEMU"

# Auth: shared API key — empty string disables auth (dev mode, logged at startup)
_DASHBOARD_KEY = os.environ.get("UAP_API_KEY", "")
# CORS: restrict to configured origin
_CORS_ORIGIN = os.environ.get("CORS_ALLOWED_ORIGIN", "http://localhost:8003")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [UAP] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("uap-dashboard")

started_at = time.time()

# ── Helpers ───────────────────────────────────────────────────────────────────

def _json(data: Any) -> bytes:
    return json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")


def _fetch_api(path: str, timeout: int = 3) -> dict:
    """Proxy a GET request to the arbitrage API."""
    try:
        url = f"{ARB_API.rstrip('/')}/{path.lstrip('/')}"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except Exception as exc:
        return {"error": str(exc)}


def _docker_status(name: str) -> dict:
    """Return Docker container status dict."""
    try:
        status = subprocess.check_output(
            ["docker", "inspect", name, "--format", "{{.State.Status}}"],
            stderr=subprocess.DEVNULL, timeout=4
        ).decode().strip()
        health = subprocess.check_output(
            ["docker", "inspect", name, "--format", "{{.State.Health.Status}}"],
            stderr=subprocess.DEVNULL, timeout=4
        ).decode().strip()
        return {"name": name, "status": status, "health": health if health != "<no value>" else None}
    except Exception:
        return {"name": name, "status": "unknown", "health": None}


def _read_recent_logs(n: int = 50) -> list[dict]:
    """Read recent log entries from the newest monitor log file."""
    entries: list[dict] = []
    monitor_dir = LOG_DIR / "monitor"
    if not monitor_dir.exists():
        return entries
    files = sorted(monitor_dir.glob("*.log"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not files:
        return entries
    try:
        lines = files[0].read_text(encoding="utf-8", errors="replace").splitlines()
        for raw in lines[-n:]:
            raw = raw.strip()
            if not raw:
                continue
            level = "INFO"
            for lvl in ("OK", "FAIL", "WARN", "ERROR", "DEBUG"):
                if f"[{lvl}]" in raw or f"/{lvl}]" in raw:
                    level = lvl
                    break
            entries.append({"raw": raw, "level": level})
    except OSError:
        pass
    return entries


def _list_genesis_reports(n: int = 20) -> list[dict]:
    """List recent Genesis Record report files."""
    items: list[dict] = []
    for sub in ("REPORTS", "PROGRESS", "PLAN"):
        d = GENESIS_DIR / sub
        if not d.exists():
            continue
        for f in sorted(d.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True)[:n]:
            items.append({
                "name": f.name,
                "category": sub,
                "size_kb": round(f.stat().st_size / 1024, 1),
                "modified": time.strftime("%Y-%m-%d %H:%M", time.localtime(f.stat().st_mtime)),
            })
    items.sort(key=lambda x: x["modified"], reverse=True)
    return items[:n]


def _run_admin(command: str, *args: str) -> dict:
    """Run admin.ps1 command and return result."""
    if not pathlib.Path(ADMIN_SCRIPT).exists():
        return {"ok": False, "error": "admin.ps1 not found"}
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-File", ADMIN_SCRIPT, command, *args],
            capture_output=True, text=True, timeout=30
        )
        return {
            "ok": result.returncode == 0,
            "stdout": result.stdout[-2000:],
            "stderr": result.stderr[-500:],
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Command timed out"}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


# ── Request Handler ───────────────────────────────────────────────────────────

class DashboardHandler(BaseHTTPRequestHandler):
    """Simple single-file HTTP handler for the UAP dashboard."""

    def log_message(self, fmt: str, *args: Any) -> None:  # quieter logging
        if self.path not in ("/api/health", "/favicon.ico"):
            log.info("%s %s", self.command, self.path)

    def _serve_file(self, path: pathlib.Path, content_type: str = "text/html") -> None:
        try:
            data = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", f"{content_type}; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except FileNotFoundError:
            self._send_json({"error": "Not found"}, 404)

    def _send_json(self, data: Any, code: int = 200) -> None:
        body = _json(data)
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", _CORS_ORIGIN)
        self.end_headers()
        self.wfile.write(body)

    def _check_auth(self) -> bool:
        """Return True if request is authenticated. Always passes when key is unset (dev mode)."""
        if not _DASHBOARD_KEY:
            return True
        key = self.headers.get("X-API-Key", "")
        return hmac.compare_digest(key, _DASHBOARD_KEY)

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        try:
            return json.loads(self.rfile.read(length)) or {}
        except Exception:
            return {}

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", _CORS_ORIGIN)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-API-Key")
        self.end_headers()

    # ── GET ──────────────────────────────────────────────────────────────────

    def do_GET(self) -> None:
        path = self.path.split("?")[0].rstrip("/") or "/"

        # Static files — no auth required
        if path == "/" or path == "/index.html":
            self._serve_file(DASHBOARD_DIR / "index.html")
            return

        # Favicon — no auth required
        if path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return

        # All API routes require authentication
        if not self._check_auth():
            self._send_json({"error": "Unauthorized"}, 401)
            return

        # API routes
        if path == "/api/health":
            self._send_json({
                "status": "ok",
                "uptime_s": round(time.time() - started_at),
                "version": self._read_version(),
            })
            return

        if path == "/api/status":
            self._api_status()
            return

        if path == "/api/agents":
            self._api_agents()
            return

        if path == "/api/logs":
            qs = dict(urllib.parse.parse_qsl(self.path.split("?")[1] if "?" in self.path else ""))
            n = min(int(qs.get("n", 50)), 500)  # max 500 lines
            self._send_json({"logs": _read_recent_logs(n)})
            return

        if path == "/api/genesis":
            self._send_json({"reports": _list_genesis_reports()})
            return

        # Proxy: forward /api/arbitrage/* to arbitrage-api
        if path.startswith("/api/arbitrage"):
            self._proxy_get(path)
            return

        self._send_json({"error": "Not found"}, 404)

    # ── POST ─────────────────────────────────────────────────────────────────

    def do_POST(self) -> None:
        path = self.path.split("?")[0].rstrip("/")
        body = self._read_body()

        # All POST routes require authentication
        if not self._check_auth():
            self._send_json({"error": "Unauthorized"}, 401)
            return

        if path == "/api/control/start":
            result = _run_admin("start")
            self._send_json(result)
            return

        if path == "/api/control/stop":
            result = _run_admin("stop")
            self._send_json(result)
            return

        if path == "/api/control/restart":
            svc = body.get("service", "all")
            result = _run_admin("restart", svc)
            self._send_json(result)
            return

        if path == "/api/control/backup":
            result = _run_admin("backup")
            self._send_json(result)
            return

        if path == "/api/control/optimize":
            result = _run_admin("optimize")
            self._send_json(result)
            return

        # Proxy POST to arbitrage-api
        if path.startswith("/api/arbitrage"):
            self._proxy_post(path, body)
            return

        self._send_json({"error": "Not found"}, 404)

    # ── Internal API handlers ─────────────────────────────────────────────────

    @staticmethod
    def _read_version() -> str:
        vf = ROOT_DIR / "VERSION"
        return vf.read_text().strip() if vf.exists() else "unknown"

    def _api_status(self) -> None:
        """Aggregated status: Docker + arbitrage-api + SQLite + Ollama."""
        # Docker containers
        containers = [_docker_status(c) for c in
                      ("adrion-db", "adrion-vortex", "adrion-healer", "adrion-n8n")]

        # Arbitrage API
        arb = _fetch_api("/api/arbitrage/status")
        arb_ok = "error" not in arb

        # SQLite
        sqlite_path = ROOT_DIR / "arbitrage.db"
        sqlite = {
            "exists": sqlite_path.exists(),
            "size_mb": round(sqlite_path.stat().st_size / 1048576, 2)
            if sqlite_path.exists() else 0,
        }

        # Ollama
        ollama: dict = {"running": False}
        try:
            with urllib.request.urlopen(
                "http://localhost:11434/api/tags", timeout=2
            ) as resp:
                data = json.loads(resp.read())
                ollama = {"running": True, "model_count": len(data.get("models", []))}
        except Exception:
            pass

        # Backups
        backup_dir = ROOT_DIR / "backups"
        latest_backup = None
        if backup_dir.exists():
            files = sorted(
                backup_dir.rglob("backup_*.db"), key=lambda f: f.stat().st_mtime, reverse=True
            )
            if files:
                latest_backup = {
                    "name": files[0].name,
                    "age_hours": round((time.time() - files[0].stat().st_mtime) / 3600, 1),
                }

        self._send_json({
            "version": self._read_version(),
            "uptime_s": round(time.time() - started_at),
            "containers": containers,
            "arbitrage_api": {"running": arb_ok, "data": arb if arb_ok else {}},
            "sqlite": sqlite,
            "ollama": ollama,
            "latest_backup": latest_backup,
        })

    def _api_agents(self) -> None:
        """Fetch agent/EBDI state from vortex engine and arbitrage-api."""
        vortex: dict = {}
        try:
            with urllib.request.urlopen("http://localhost:1740/health", timeout=3) as r:
                vortex = json.loads(r.read())
        except Exception as exc:
            vortex = {"error": str(exc)}

        arb_status = _fetch_api("/api/arbitrage/status")

        agents = [
            {"name": "Librarian",  "role": "Knowledge Management",  "icon": "📚"},
            {"name": "SAP",        "role": "Strategic Action Planner","icon": "🎯"},
            {"name": "Auditor",    "role": "Compliance & Verification","icon": "🔍"},
            {"name": "Sentinel",   "role": "Security & Monitoring",  "icon": "🛡"},
            {"name": "Architect",  "role": "System Design",          "icon": "🔧"},
            {"name": "Healer",     "role": "Self-Healing Recovery",  "icon": "💊"},
            {"name": "Amplifier",  "role": "Signal Amplification",   "icon": "📡"},
            {"name": "BoosterLvr", "role": "Revenue Optimization",   "icon": "🚀"},
            {"name": "Chronos",    "role": "Temporal Coordination",  "icon": "⏱"},
        ]

        self._send_json({
            "agents": agents,
            "vortex": vortex,
            "arbitrage": arb_status,
        })

    def _proxy_get(self, path: str) -> None:
        data = _fetch_api(path)
        code = 200 if "error" not in data else 502
        self._send_json(data, code)

    def _proxy_post(self, path: str, body: dict) -> None:
        try:
            url = f"{ARB_API.rstrip('/')}/{path.lstrip('/')}"
            payload = json.dumps(body).encode("utf-8")
            req = urllib.request.Request(
                url, data=payload,
                headers={"Content-Type": "application/json", "Accept": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                self._send_json(json.loads(resp.read()))
        except Exception as exc:
            self._send_json({"error": str(exc)}, 502)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="ADRION 369 UAP Dashboard Server")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--api", default=ARB_API,
                        help="Arbitrage API base URL (default: %(default)s)")
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    global ARB_API
    ARB_API = args.api

    server = HTTPServer((args.host, args.port), DashboardHandler)
    dashboard_file = DASHBOARD_DIR / "index.html"

    log.info("┌─────────────────────────────────────────────────────────┐")
    log.info("│  ADRION 369 UAP Dashboard                               │")
    log.info("│  http://localhost:%d                                   │", args.port)
    log.info("│  Arbitrage API: %s                      │", args.api)
    log.info("│  Dashboard: %s                │",
             str(dashboard_file)[-40:].ljust(40))
    if not _DASHBOARD_KEY:
        log.warning("[SECURITY] UAP_API_KEY not set — API endpoints are UNAUTHENTICATED")
    log.info("└─────────────────────────────────────────────────────────┘")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Dashboard server stopped.")


if __name__ == "__main__":
    main()
