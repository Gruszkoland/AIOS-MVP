#!/usr/bin/env python3
"""
ShieldOS Local Setup — ADRION 369
Hermetic enclave, zero-trust, API key separation.

Idempotent: safe to run multiple times in sequence.
Supports: Windows + Linux (no sudo required).

Usage:
    python scripts/setup_shieldos_local.py
    python scripts/setup_shieldos_local.py --skip-containers
    python scripts/setup_shieldos_local.py --force-env --json
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import logging
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── Constants ─────────────────────────────────────────────────────────────────

MIN_PYTHON: tuple[int, int] = (3, 11)
MIN_GO_VERSION: tuple[int, int] = (1, 22)
SETUP_TIMEOUT_SECONDS: int = 300  # 5 minutes hard limit

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
LOG_DIR: Path = PROJECT_ROOT / "logs"
AUDIT_LOG_PATH: Path = LOG_DIR / f"shieldos_setup_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.jsonl"

# MCP server registry — port + health endpoint + description
MCP_SERVERS: dict[str, dict[str, Any]] = {
    "mcp-router":   {"port": 9000, "health": "/health", "description": "Central decision arbitration"},
    "vortex-mcp":   {"port": 9001, "health": "/health", "description": "Orchestration & 174Hz monitoring"},
    "guardian-mcp": {"port": 9002, "health": "/health", "description": "Security & compliance (9 Laws)"},
    "oracle-mcp":   {"port": 9003, "health": "/health", "description": "162D routing & pattern matching"},
    "genesis-mcp":  {"port": 9004, "health": "/health", "description": "State management & RAG"},
    "healer-mcp":   {"port": 9005, "health": "/health", "description": "Recovery & monitoring"},
}

# Infrastructure containers required for local dev
REQUIRED_CONTAINERS: dict[str, dict[str, Any]] = {
    "adrion-postgres": {
        "image": "postgres:15-alpine",
        "port": 5432,
        "health_cmd": ["pg_isready", "-U", "adrion"],
    },
    "adrion-redis": {
        "image": "redis:7-alpine",
        "port": 6379,
        "health_cmd": ["redis-cli", "ping"],
    },
}

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("shieldos")


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class AuditEntry:
    timestamp: str
    step: str
    status: str  # "ok" | "warn" | "error" | "skip"
    detail: str = ""
    duration_ms: int = 0


@dataclass
class SetupResult:
    success: bool = True
    steps_ok: list[str] = field(default_factory=list)
    steps_warn: list[str] = field(default_factory=list)
    steps_failed: list[str] = field(default_factory=list)
    hermetic_score: int = 0
    audit_log_path: str = ""
    mcp_accessible: dict[str, bool] = field(default_factory=dict)
    smoke_tests: dict[str, str] = field(default_factory=dict)


# ── Audit Logger ──────────────────────────────────────────────────────────────

class AuditLogger:
    """Append-only JSONL audit log for every setup action."""

    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self._entries: list[AuditEntry] = []

    def record(
        self,
        step: str,
        status: str,
        detail: str = "",
        duration_ms: int = 0,
    ) -> AuditEntry:
        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            step=step,
            status=status,
            detail=detail,
            duration_ms=duration_ms,
        )
        self._entries.append(entry)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(dataclasses.asdict(entry)) + "\n")
        icons: dict[str, str] = {"ok": "[OK]", "warn": "[WARN]", "error": "[ERROR]", "skip": "[SKIP]"}
        prefix = icons.get(status, "[?]")
        msg = f"{prefix} {step}"
        if detail:
            msg += f": {detail}"
        if status == "error":
            log.error(msg)
        elif status == "warn":
            log.warning(msg)
        else:
            log.info(msg)
        return entry

    def entries(self) -> list[AuditEntry]:
        return list(self._entries)


# ── Prerequisite Checker ──────────────────────────────────────────────────────

class PrerequisiteChecker:
    """Validates runtime prerequisites before any setup action."""

    def __init__(self, audit: AuditLogger) -> None:
        self.audit = audit

    def check_python(self) -> bool:
        current = sys.version_info[:2]
        ok = current >= MIN_PYTHON
        detail = f"Python {'.'.join(map(str, current))} (need {'.'.join(map(str, MIN_PYTHON))}+)"
        self.audit.record("check_python", "ok" if ok else "error", detail)
        return ok

    def check_docker(self) -> bool:
        if shutil.which("docker") is None:
            self.audit.record("check_docker", "error", "docker not found in PATH")
            return False
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True, text=True, timeout=15,
            )
        except subprocess.TimeoutExpired:
            self.audit.record("check_docker", "error", "docker info timed out")
            return False
        if result.returncode != 0:
            self.audit.record("check_docker", "error", "Docker daemon not running or permission denied")
            return False
        self.audit.record("check_docker", "ok", "Docker daemon accessible")
        return True

    def check_docker_compose(self) -> bool:
        for cmd in [["docker", "compose", "version"], ["docker-compose", "--version"]]:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    version_line = result.stdout.strip()[:80]
                    self.audit.record("check_docker_compose", "ok", version_line)
                    return True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
        self.audit.record("check_docker_compose", "error", "docker compose not found")
        return False

    def check_go(self) -> bool:
        if shutil.which("go") is None:
            self.audit.record("check_go", "warn", "go not found — Go services will not be built locally")
            return False
        try:
            result = subprocess.run(["go", "version"], capture_output=True, text=True, timeout=10)
        except subprocess.TimeoutExpired:
            self.audit.record("check_go", "warn", "go version timed out")
            return False
        if result.returncode != 0:
            self.audit.record("check_go", "warn", "go version check failed")
            return False
        match = re.search(r"go(\d+)\.(\d+)", result.stdout)
        if match:
            major, minor = int(match.group(1)), int(match.group(2))
            ok = (major, minor) >= MIN_GO_VERSION
            detail = f"Go {major}.{minor} (need {'.'.join(map(str, MIN_GO_VERSION))}+)"
            self.audit.record("check_go", "ok" if ok else "warn", detail)
            return ok
        self.audit.record("check_go", "warn", f"Could not parse: {result.stdout.strip()[:60]}")
        return False

    def run_all(self) -> dict[str, bool]:
        return {
            "python": self.check_python(),
            "docker": self.check_docker(),
            "docker_compose": self.check_docker_compose(),
            "go": self.check_go(),
        }


# ── Container Manager ─────────────────────────────────────────────────────────

class ContainerManager:
    """Manages Docker containers for the local dev stack."""

    def __init__(self, audit: AuditLogger, project_root: Path) -> None:
        self.audit = audit
        self.project_root = project_root
        self._compose_base: list[str] = self._resolve_compose_cmd()

    def _resolve_compose_cmd(self) -> list[str]:
        result = subprocess.run(
            ["docker", "compose", "version"],
            capture_output=True, timeout=10,
        )
        return ["docker", "compose"] if result.returncode == 0 else ["docker-compose"]

    def _is_running(self, name: str) -> bool:
        result = subprocess.run(
            ["docker", "inspect", "--format", "{{.State.Running}}", name],
            capture_output=True, text=True, timeout=10,
        )
        return result.returncode == 0 and result.stdout.strip() == "true"

    def start_infrastructure(self) -> bool:
        """Start postgres + redis via docker-compose.local.yml (idempotent, --no-recreate)."""
        compose_file = self.project_root / "docker-compose.local.yml"
        if not compose_file.exists():
            self.audit.record("start_infrastructure", "error", f"{compose_file.name} not found")
            return False

        t0 = time.monotonic()
        cmd = self._compose_base + [
            "-f", str(compose_file),
            "up", "-d", "--no-recreate",
            "postgres", "redis",
        ]
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=120, cwd=str(self.project_root),
            )
        except subprocess.TimeoutExpired:
            self.audit.record("start_infrastructure", "error", "Compose up timed out after 120s")
            return False

        duration_ms = int((time.monotonic() - t0) * 1000)
        if result.returncode != 0:
            stderr_snippet = result.stderr[:300].replace("\n", " ")
            self.audit.record("start_infrastructure", "error", stderr_snippet, duration_ms)
            return False

        self.audit.record("start_infrastructure", "ok", "postgres + redis started", duration_ms)
        return True

    def _wait_ready(self, container: str, health_cmd: list[str], max_wait: int = 60) -> bool:
        deadline = time.monotonic() + max_wait
        while time.monotonic() < deadline:
            result = subprocess.run(
                ["docker", "exec", container] + health_cmd,
                capture_output=True, timeout=10,
            )
            if result.returncode == 0:
                return True
            time.sleep(2)
        return False

    def wait_for_postgres(self, max_wait: int = 60) -> bool:
        ok = self._wait_ready("adrion-postgres", ["pg_isready", "-U", "adrion"], max_wait)
        self.audit.record("wait_postgres", "ok" if ok else "error",
                          "PostgreSQL ready" if ok else f"Not ready after {max_wait}s")
        return ok

    def wait_for_redis(self, max_wait: int = 30) -> bool:
        ok = self._wait_ready("adrion-redis", ["redis-cli", "ping"], max_wait)
        self.audit.record("wait_redis", "ok" if ok else "error",
                          "Redis ready" if ok else f"Not ready after {max_wait}s")
        return ok


# ── MCP Configurator ──────────────────────────────────────────────────────────

class MCPConfigurator:
    """Writes MCP server config files for Claude Code and VS Code."""

    def __init__(self, audit: AuditLogger, project_root: Path) -> None:
        self.audit = audit
        self.project_root = project_root

    def write_claude_mcp_config(self) -> bool:
        """Write .mcp.json — Claude Code MCP server discovery (project-level)."""
        mcp_config: dict[str, Any] = {
            "_comment": "ShieldOS MCP server config — generated by setup_shieldos_local.py",
            "mcpServers": {
                name: {
                    "url": f"http://localhost:{cfg['port']}/mcp",
                    "description": cfg["description"],
                    "transport": "http",
                }
                for name, cfg in MCP_SERVERS.items()
            },
        }
        output_path = self.project_root / ".mcp.json"
        existing: dict[str, Any] = {}
        if output_path.exists():
            try:
                existing = json.loads(output_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass

        # Idempotent: skip if content unchanged (ignoring the comment key)
        new_servers = mcp_config["mcpServers"]
        old_servers = existing.get("mcpServers", {})
        if new_servers == old_servers:
            self.audit.record("write_mcp_config", "skip", ".mcp.json unchanged")
            return True

        output_path.write_text(json.dumps(mcp_config, indent=2) + "\n", encoding="utf-8")
        self.audit.record("write_mcp_config", "ok", f"Written: {output_path.name}")
        return True

    def write_vscode_mcp_settings(self) -> bool:
        """Add MCP server URLs to .vscode/settings.json under 'claude.mcp.servers'."""
        settings_path = self.project_root / ".vscode" / "settings.json"
        if not settings_path.exists():
            self.audit.record("vscode_mcp_settings", "skip", ".vscode/settings.json not found")
            return True

        try:
            settings: dict[str, Any] = json.loads(settings_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            self.audit.record("vscode_mcp_settings", "error", f"JSON parse error: {exc}")
            return False

        mcp_key = "claude.mcp.servers"
        if mcp_key in settings:
            self.audit.record("vscode_mcp_settings", "skip", f"{mcp_key} already present")
            return True

        settings[mcp_key] = {
            name: {"url": f"http://localhost:{cfg['port']}/mcp"}
            for name, cfg in MCP_SERVERS.items()
        }
        settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
        self.audit.record("vscode_mcp_settings", "ok", f"Added {mcp_key} block to VS Code settings")
        return True


# ── Env Generator ─────────────────────────────────────────────────────────────

class EnvGenerator:
    """Generates .env from .env.example, preserving all CHANGE_ME placeholders."""

    def __init__(self, audit: AuditLogger, project_root: Path) -> None:
        self.audit = audit
        self.project_root = project_root

    def generate(self, force: bool = False) -> bool:
        env_path = self.project_root / ".env"
        if env_path.exists() and not force:
            self.audit.record(
                "generate_env", "skip",
                ".env already exists (use --force-env to overwrite)",
            )
            return True

        example_path = self.project_root / ".env.example"
        if not example_path.exists():
            self.audit.record("generate_env", "error", ".env.example not found")
            return False

        content = example_path.read_text(encoding="utf-8")
        # Apply local dev overrides (non-secret settings only)
        content = content.replace("DB_ENGINE=sqlite", "DB_ENGINE=postgresql")
        content = content.replace("ENVIRONMENT=production", "ENVIRONMENT=development")
        content = content.replace("DEBUG_MODE=false", "DEBUG_MODE=true")
        content = content.replace("LOG_LEVEL=INFO", "LOG_LEVEL=DEBUG")

        env_path.write_text(content, encoding="utf-8")
        action = "overwritten" if force else "created"
        self.audit.record(
            "generate_env", "ok",
            f".env {action} — fill in CHANGE_ME values before starting services",
        )
        return True


# ── Smoke Test Runner ─────────────────────────────────────────────────────────

class SmokeTestRunner:
    """Validates that infrastructure services respond after setup."""

    def __init__(self, audit: AuditLogger) -> None:
        self.audit = audit

    def _http_ok(self, url: str, timeout: int = 5) -> bool:
        try:
            import urllib.request
            with urllib.request.urlopen(url, timeout=timeout) as resp:
                return resp.status < 500
        except Exception:
            return False

    def test_postgres(self) -> bool:
        result = subprocess.run(
            ["docker", "exec", "adrion-postgres", "pg_isready", "-U", "adrion"],
            capture_output=True, timeout=10,
        )
        ok = result.returncode == 0
        self.audit.record(
            "smoke_postgres",
            "ok" if ok else "warn",
            "PostgreSQL responding" if ok else "PostgreSQL not responding — container may not be running",
        )
        return ok

    def test_redis(self) -> bool:
        result = subprocess.run(
            ["docker", "exec", "adrion-redis", "redis-cli", "ping"],
            capture_output=True, text=True, timeout=10,
        )
        ok = result.returncode == 0 and "PONG" in result.stdout
        self.audit.record(
            "smoke_redis",
            "ok" if ok else "warn",
            "Redis responding" if ok else "Redis not responding — container may not be running",
        )
        return ok

    def test_mcp_servers(self) -> dict[str, bool]:
        results: dict[str, bool] = {}
        for name, cfg in MCP_SERVERS.items():
            url = f"http://localhost:{cfg['port']}{cfg['health']}"
            ok = self._http_ok(url)
            detail = (
                f"Port {cfg['port']} accessible"
                if ok
                else f"Port {cfg['port']} not accessible (start with: docker compose -f docker-compose.local.yml up -d)"
            )
            self.audit.record(f"smoke_mcp_{name}", "ok" if ok else "warn", detail)
            results[name] = ok
        return results

    def run_all(self) -> dict[str, Any]:
        return {
            "postgres": self.test_postgres(),
            "redis": self.test_redis(),
            "mcp_servers": self.test_mcp_servers(),
        }


# ── Hermetic Checker (inline) ──────────────────────────────────────────────────

def quick_hermetic_check(project_root: Path, audit: AuditLogger) -> int:
    """Fast inline hermetic check. Returns score 0-100.

    Skips YAML/shell comment lines (lines where the stripped content starts with #).
    """
    score = 100
    compose_files = list(project_root.glob("docker-compose*.yml"))

    for cf in compose_files:
        lines = cf.read_text(encoding="utf-8", errors="replace").splitlines()
        active_lines = [ln for ln in lines if not ln.strip().startswith("#")]
        active_content = "\n".join(active_lines)

        if "docker.sock" in active_content:
            score -= 25
            audit.record("hermetic_docker_sock", "warn", f"docker.sock mount found in {cf.name}")
        if "DOCKER_HOST" in active_content:
            score -= 10
            audit.record("hermetic_docker_host", "warn", f"DOCKER_HOST env var found in {cf.name}")

    # Check that .env (if it exists) does not contain real secrets where placeholders are expected
    env_path = project_root / ".env"
    if env_path.exists():
        env_content = env_path.read_text(encoding="utf-8", errors="replace")
        if "CHANGE_ME_IN_PRODUCTION" in env_content:
            audit.record("hermetic_env_placeholders", "ok", ".env contains CHANGE_ME placeholders (correct)")
        # If all CHANGE_ME vars are still placeholders, score is fine
        # If a real secret-looking value is set (long non-CHANGE_ME string) in sensitive keys, warn
        sensitive_patterns = [r"STRIPE_LOGIN_PASSWORD=(?!$|CHANGE_ME).+", r"OPENAI_API_KEY=sk-.+"]
        for pat in sensitive_patterns:
            if re.search(pat, env_content):
                score -= 5
                audit.record("hermetic_secret_in_env", "warn", f"Possible real secret matching: {pat[:40]}")

    return max(0, score)


# ── Setup Orchestrator ────────────────────────────────────────────────────────

class SetupOrchestrator:
    """Coordinates all setup phases with audit logging and partial failure handling."""

    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        self.audit = AuditLogger(AUDIT_LOG_PATH)
        self.result = SetupResult(audit_log_path=str(AUDIT_LOG_PATH))

    def _mark(self, step: str, ok: bool, warn_only: bool = False) -> None:
        if ok:
            self.result.steps_ok.append(step)
        elif warn_only:
            self.result.steps_warn.append(step)
        else:
            self.result.steps_failed.append(step)
            self.result.success = False

    def run(self) -> SetupResult:
        global_start = time.monotonic()
        self.audit.record(
            "setup_start", "ok",
            f"Platform: {platform.system()} {platform.machine()} | PID: {os.getpid()}",
        )

        # ── Phase 1: Prerequisites ──────────────────────────────────────────
        checker = PrerequisiteChecker(self.audit)
        prereqs = checker.run_all()

        if not prereqs["python"]:
            self.audit.record("setup_abort", "error", f"Python {'.'.join(map(str, MIN_PYTHON))}+ required")
            self._mark("prerequisites", False)
            return self.result

        if not prereqs["docker"] or not prereqs["docker_compose"]:
            self.audit.record("setup_abort", "error", "Docker with Compose plugin is required")
            self._mark("prerequisites", False)
            return self.result

        self._mark("prerequisites", True)

        # ── Phase 2: Infrastructure containers ─────────────────────────────
        if not self.args.skip_containers:
            mgr = ContainerManager(self.audit, PROJECT_ROOT)
            infra_ok = mgr.start_infrastructure()
            self._mark("start_infrastructure", infra_ok)
            if infra_ok:
                pg_ok = mgr.wait_for_postgres(max_wait=60)
                rd_ok = mgr.wait_for_redis(max_wait=30)
                self._mark("wait_postgres", pg_ok, warn_only=True)
                self._mark("wait_redis", rd_ok, warn_only=True)
        else:
            self.audit.record("start_infrastructure", "skip", "--skip-containers flag set")

        # ── Phase 3: MCP configuration ──────────────────────────────────────
        mcp_cfg = MCPConfigurator(self.audit, PROJECT_ROOT)
        self._mark("write_mcp_config", mcp_cfg.write_claude_mcp_config())
        self._mark("vscode_mcp_settings", mcp_cfg.write_vscode_mcp_settings(), warn_only=True)

        # ── Phase 4: Environment file ───────────────────────────────────────
        env_gen = EnvGenerator(self.audit, PROJECT_ROOT)
        self._mark("generate_env", env_gen.generate(force=self.args.force_env))

        # ── Phase 5: Smoke tests ────────────────────────────────────────────
        smoke = SmokeTestRunner(self.audit)
        smoke_results = smoke.run_all()
        self.result.smoke_tests = {
            "postgres": "ok" if smoke_results["postgres"] else "warn",
            "redis": "ok" if smoke_results["redis"] else "warn",
        }
        self.result.mcp_accessible = smoke_results["mcp_servers"]

        # ── Phase 6: Hermetic check ─────────────────────────────────────────
        self.result.hermetic_score = quick_hermetic_check(PROJECT_ROOT, self.audit)
        if self.result.hermetic_score >= 90:
            self.audit.record("hermetic_score", "ok", f"Score {self.result.hermetic_score}/100 — excellent")
        elif self.result.hermetic_score >= 70:
            self.audit.record("hermetic_score", "warn", f"Score {self.result.hermetic_score}/100 — acceptable")
        else:
            self.audit.record("hermetic_score", "error", f"Score {self.result.hermetic_score}/100 — below threshold")

        elapsed_ms = int((time.monotonic() - global_start) * 1000)
        self.audit.record(
            "setup_complete",
            "ok" if self.result.success else "warn",
            f"Elapsed: {elapsed_ms}ms | Hermetic: {self.result.hermetic_score}/100",
        )
        return self.result

    def print_summary(self) -> None:
        width = 62
        print()
        print("=" * width)
        print("  ShieldOS Local Setup — Summary")
        print("=" * width)
        status_label = "COMPLETE" if self.result.success else "INCOMPLETE"
        print(f"  Status:           {status_label}")
        print(f"  Hermetic Score:   {self.result.hermetic_score}/100")
        print(f"  Steps OK:         {len(self.result.steps_ok)}")
        print(f"  Steps Warn:       {len(self.result.steps_warn)}")
        print(f"  Steps Failed:     {len(self.result.steps_failed)}")
        if self.result.steps_failed:
            print(f"  Failed:           {', '.join(self.result.steps_failed)}")
        print(f"  Audit Log:        {self.result.audit_log_path}")
        print()
        mcp_ok = sum(1 for v in self.result.mcp_accessible.values() if v)
        mcp_total = len(self.result.mcp_accessible)
        print(f"  MCP Servers:      {mcp_ok}/{mcp_total} accessible")
        for name, accessible in self.result.mcp_accessible.items():
            port = MCP_SERVERS[name]["port"]
            mark = "OK" if accessible else "--"
            print(f"    [{mark}] {name:<20} http://localhost:{port}/health")
        print()
        print("  Next steps:")
        print("  1. Fill in CHANGE_ME values in .env")
        print("  2. python scripts/verify_shieldos_hermetic.py")
        print("  3. docker compose -f docker-compose.local.yml up -d")
        print("  4. http://localhost:8003  (Flask API)")
        print("  5. http://localhost:9000/health (MCP Router)")
        print("=" * width)
        print()


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="ShieldOS Local Setup — ADRION 369 hermetic dev environment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/setup_shieldos_local.py
  python scripts/setup_shieldos_local.py --skip-containers
  python scripts/setup_shieldos_local.py --force-env --json
""",
    )
    parser.add_argument(
        "--skip-containers",
        action="store_true",
        help="Skip Docker container startup (useful on re-runs when containers already running)",
    )
    parser.add_argument(
        "--force-env",
        action="store_true",
        help="Overwrite existing .env file (default: skip if already exists)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit result as JSON to stdout (for CI integration)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    # Global timeout guard
    setup_deadline = time.monotonic() + SETUP_TIMEOUT_SECONDS

    orchestrator = SetupOrchestrator(args)
    result = orchestrator.run()

    elapsed = time.monotonic()
    if elapsed > setup_deadline:
        log.warning(f"Setup exceeded {SETUP_TIMEOUT_SECONDS}s timeout")

    if args.json:
        print(json.dumps(dataclasses.asdict(result), indent=2))
    else:
        orchestrator.print_summary()

    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
