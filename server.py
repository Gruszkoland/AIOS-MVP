#!/usr/bin/env python3
"""
ADRION 369 Dashboard Server
Local HTTP server with Ollama API proxy + Arbitrage API + real-time status
"""
import os
import sys
# Fix Unicode output on Windows (CP1250 -> UTF-8)
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf-8-sig"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
import json
import logging
import platform
import threading
import time
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.request import urlopen, Request
from urllib.error import URLError
import urllib.parse

# Project root on sys.path so `arbitrage` package is importable
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

DASHBOARD_HOST = os.getenv("DASHBOARD_HOST", "localhost")
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "9000"))
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
STACK_CONTAINERS = [name.strip() for name in os.getenv("STACK_CONTAINERS", "adrion-api,adrion-dashboard").split(",") if name.strip()]
MONITORING_CONTAINERS = [name.strip() for name in os.getenv("MONITORING_CONTAINERS", "adrion-loki,adrion-promtail,adrion-grafana").split(",") if name.strip()]

logging.basicConfig(level=logging.INFO, format="%(asctime)s level=%(levelname)s logger=%(name)s %(message)s")
logger = logging.getLogger("adrion.dashboard")


# ─────────────────────────────────────────────────────────────────────────────
class DashboardRequestHandler(SimpleHTTPRequestHandler):
    """Handles HTTP requests with CORS, API proxy, and arbitrage endpoints."""

    # ── Routing ───────────────────────────────────────────────────────────────
    def do_GET(self):
        self._request_started_at = time.perf_counter()
        path = urllib.parse.urlparse(self.path).path

        routes = {
            "/api/ollama/status":    self.ollama_status,
            "/api/ollama/models":    self.ollama_models,
            "/api/system/info":      self.system_info,
            "/api/runtime/stack":    self.runtime_stack,
            "/api/genesis/logs":     self.genesis_logs,
            "/api/arbitrage/stats":  self.arbitrage_stats,
            "/api/arbitrage/jobs":   self.arbitrage_jobs,
            "/api/arbitrage/bids":   self.arbitrage_bids,
        }

        if path in routes:
            return routes[path]()
        if path.startswith("/api/"):
            return self.send_json({"error": "Unknown API route"})
        return super().do_GET()

    def do_POST(self):
        self._request_started_at = time.perf_counter()
        path = urllib.parse.urlparse(self.path).path
        if path == "/api/arbitrage/cycle":
            return self._trigger_cycle()
        if path == "/api/arbitrage/earn":
            return self._record_earn()
        if path == "/api/runtime/restart":
            return self._restart_stack()
        self.send_response(404)
        self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    # ── Helpers ───────────────────────────────────────────────────────────────
    def send_json(self, data: dict, status: int = 200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        duration_ms = -1
        if hasattr(self, "_request_started_at"):
            duration_ms = int((time.perf_counter() - self._request_started_at) * 1000)
        log_method = logger.error if status >= 500 else logger.warning if status >= 400 else logger.info
        log_method(
            "event=request method=%s path=%s status=%s duration_ms=%s remote_addr=%s",
            self.command,
            urllib.parse.urlparse(self.path).path,
            status,
            duration_ms,
            self.client_address[0] if self.client_address else "unknown",
        )

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def log_message(self, format, *args):
        pass  # Silence access log noise

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length)) if length else {}

    # ── Ollama ────────────────────────────────────────────────────────────────
    def ollama_status(self):
        try:
            resp = urlopen(f"{OLLAMA_URL}/api/tags", timeout=2)
            data = json.loads(resp.read())
            return self.send_json({
                "status": "online",
                "url": OLLAMA_URL,
                "models": len(data.get("models", [])),
                "timestamp": datetime.now().isoformat(),
            })
        except Exception as e:
            return self.send_json({
                "status": "offline",
                "url": OLLAMA_URL,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            })

    def ollama_models(self):
        try:
            resp = urlopen(f"{OLLAMA_URL}/api/tags", timeout=2)
            data = json.loads(resp.read())
            models = [
                {"name": m.get("name"), "size": m.get("size"), "modified": m.get("modified_at")}
                for m in data.get("models", [])
            ]
            return self.send_json({"status": "success", "models": models})
        except Exception as e:
            return self.send_json({"status": "error", "error": str(e)})

    # ── System ────────────────────────────────────────────────────────────────
    def system_info(self):
        return self.send_json({
            "platform": platform.system(),
            "platform_release": platform.release(),
            "processor": platform.processor(),
            "cwd": str(PROJECT_ROOT),
            "timestamp": datetime.now().isoformat(),
        })

    def genesis_logs(self):
        logs_path = PROJECT_ROOT / ".aider" / "logs"
        logs = []
        if logs_path.exists():
            for fname in ("session.log", "audit_trail.log"):
                fp = logs_path / fname
                if fp.exists():
                    with open(fp) as f:
                        for line in f.readlines()[-20:]:
                            logs.append({"type": fname.split(".")[0], "content": line.strip()})
        return self.send_json({"logs": logs, "timestamp": datetime.now().isoformat()})

    def runtime_stack(self):
        runtime = get_runtime_stack_info()
        return self.send_json(runtime, status=200 if runtime.get("docker_available") else 503)

    # ── Arbitrage API ─────────────────────────────────────────────────────────
    def arbitrage_stats(self):
        try:
            from arbitrage.database import init_db
            from arbitrage.xrp_tracker import get_kpi_summary
            init_db()
            return self.send_json(get_kpi_summary())
        except Exception as e:
            return self.send_json({"error": str(e)})

    def arbitrage_jobs(self):
        try:
            from arbitrage.database import init_db, get_jobs
            init_db()
            return self.send_json({"jobs": get_jobs(limit=20)})
        except Exception as e:
            return self.send_json({"error": str(e)})

    def arbitrage_bids(self):
        try:
            from arbitrage.database import init_db, get_pending_bids
            init_db()
            return self.send_json({"bids": get_pending_bids()})
        except Exception as e:
            return self.send_json({"error": str(e)})

    def _trigger_cycle(self):
        """Fire-and-forget Scout → Analyze → Bid cycle."""
        def _run():
            try:
                from arbitrage.orchestrator import run_cycle
                run_cycle()
            except Exception:
                pass
        threading.Thread(target=_run, daemon=True).start()
        return self.send_json({"status": "cycle_started", "timestamp": datetime.now().isoformat()})

    def _record_earn(self):
        """Record a USD earning. Body: {amount_usd, source_note}"""
        body = self._read_body()
        try:
            from arbitrage.database import init_db
            from arbitrage.xrp_tracker import record_earning
            init_db()
            record_earning(float(body.get("amount_usd", 0)), body.get("source_note", ""))
            return self.send_json({"status": "ok"})
        except Exception as e:
            return self.send_json({"error": str(e)})

    def _restart_stack(self):
        client = get_docker_client()
        if client is None:
            return self.send_json({
                "status": "error",
                "error": "Docker SDK unavailable inside dashboard runtime",
            }, status=503)

        body = self._read_body()
        target = str(body.get("target", "stack")).strip().lower()
        restart_plan = get_restart_targets(target)
        if not restart_plan:
            return self.send_json({
                "status": "error",
                "error": f"Unknown restart target: {target}",
            }, status=400)

        def _restart():
            try:
                for container_name in restart_plan[:-1]:
                    client.containers.get(container_name).restart(timeout=10)
                    time.sleep(1)
                if restart_plan:
                    client.containers.get(restart_plan[-1]).restart(timeout=10)
            except Exception:
                pass

        threading.Thread(target=_restart, daemon=True).start()
        return self.send_json({
            "status": "restart_started",
            "target": target,
            "targets": restart_plan,
            "timestamp": datetime.now().isoformat(),
        })


def get_docker_client():
    try:
        import docker

        client = docker.DockerClient(base_url=os.getenv("DOCKER_HOST", "unix:///var/run/docker.sock"))
        client.ping()
        return client
    except Exception:
        return None


def get_runtime_stack_info() -> dict:
    base = {
        "docker_available": False,
        "containers": [],
        "app_containers": [],
        "monitoring_containers": [],
        "restart_targets": ["stack", "api", "dashboard"],
        "project_root": str(PROJECT_ROOT),
        "timestamp": datetime.now().isoformat(),
    }
    client = get_docker_client()
    if client is None:
        return {**base, "error": "Docker SDK unavailable"}

    try:
        containers = []
        all_runtime_containers = STACK_CONTAINERS + [name for name in MONITORING_CONTAINERS if name not in STACK_CONTAINERS]
        for container_name in all_runtime_containers:
            item = client.containers.get(container_name).attrs
            ports = []
            port_map = item.get("NetworkSettings", {}).get("Ports", {}) or {}
            for container_port, bindings in port_map.items():
                if not bindings:
                    ports.append({"container": container_port, "host": None})
                    continue
                for binding in bindings:
                    ports.append({
                        "container": container_port,
                        "host": binding.get("HostPort"),
                        "host_ip": binding.get("HostIp"),
                    })

            containers.append({
                "name": item.get("Name", "").lstrip("/"),
                "image": item.get("Config", {}).get("Image", ""),
                "status": item.get("State", {}).get("Status", "unknown"),
                "health": item.get("State", {}).get("Health", {}).get("Status", "n/a"),
                "ports": ports,
                "group": "monitoring" if container_name in MONITORING_CONTAINERS else "application",
            })

        app_containers = [item for item in containers if item["group"] == "application"]
        monitoring_containers = [item for item in containers if item["group"] == "monitoring"]
        return {
            **base,
            "docker_available": True,
            "containers": containers,
            "app_containers": app_containers,
            "monitoring_containers": monitoring_containers,
        }
    except Exception as exc:
        return {**base, "error": str(exc)}


def get_restart_targets(target: str) -> list[str]:
    targets = {
        "stack": STACK_CONTAINERS,
        "api": [STACK_CONTAINERS[0]] if STACK_CONTAINERS else [],
        "dashboard": [STACK_CONTAINERS[-1]] if STACK_CONTAINERS else [],
    }
    return targets.get(target, [])


# ─────────────────────────────────────────────────────────────────────────────
def monitor_ollama():
    while True:
        try:
            urlopen(f"{OLLAMA_URL}/api/tags", timeout=2)
            logger.info("event=ollama_status status=online url=%s", OLLAMA_URL)
        except Exception as exc:
            logger.warning("event=ollama_status status=offline url=%s error=%s", OLLAMA_URL, exc)
        time.sleep(5)


def start_dashboard_server():
    os.chdir(PROJECT_ROOT / "dashboard")
    server = HTTPServer((DASHBOARD_HOST, DASHBOARD_PORT), DashboardRequestHandler)
    public_host = "localhost" if DASHBOARD_HOST in ("0.0.0.0", "::") else DASHBOARD_HOST
    logger.info("event=dashboard_start url=http://%s:%s ollama_url=%s", public_host, DASHBOARD_PORT, OLLAMA_URL)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("event=dashboard_stop")
        server.shutdown()


if __name__ == "__main__":
    print("╔════════════════════════════════════════════╗")
    print("║  ADRION 369 Dashboard Server               ║")
    print("║  Multi-Persona AI Coding System + XRP Bot  ║")
    print("╚════════════════════════════════════════════╝\n")

    threading.Thread(target=monitor_ollama, daemon=True).start()
    start_dashboard_server()
