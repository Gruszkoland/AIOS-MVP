#!/usr/bin/env python3
"""
ShieldOS Hermetic Verification — ADRION 369
Validates that the local enclave meets zero-trust, API key separation
and hermeticity requirements.

Checks:
  1. docker.sock mounts in compose files (CRITICAL)
  2. DOCKER_HOST env vars in compose files (HIGH)
  3. External API calls without allow-list guard in source (MEDIUM)
  4. Hardcoded API key literals in source (HIGH)
  5. Per-service API key isolation in compose files (MEDIUM)
  6. Telemetry settings (LOW)
  7. Network isolation (hermetic bridge) in compose files (MEDIUM)

Score: 0-100. Recommended minimum: 70. Excellent: 90+.

Usage:
    python scripts/verify_shieldos_hermetic.py
    python scripts/verify_shieldos_hermetic.py --json
    python scripts/verify_shieldos_hermetic.py --fix-report
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── Configuration ─────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Compose files to scan
COMPOSE_GLOBS = ["docker-compose*.yml", "docker-compose*.yaml"]

# Source directories to scan for hardcoded secrets / unguarded external calls
SOURCE_DIRS = ["arbitrage", "uap", "mcp-servers"]
SOURCE_EXTS = {".py", ".go", ".js", ".ts"}

# External domains allowed without penalty (configured integrations)
ALLOWED_EXTERNAL_DOMAINS = frozenset({
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    # LLM backends (configured via env vars)
    "openrouter.ai",
    "api.openrouter.ai",
    "openai.com",
    "api.openai.com",
    "anthropic.com",
    "api.anthropic.com",
    # Business integrations (configured via env vars)
    "api.stripe.com",
    "api.apify.com",
    "api.coingecko.com",
    "api.binance.com",
    "api.xrplabs.net",
    # Platform UI assets (CDN for Swagger UI, etc.)
    "cdn.jsdelivr.net",
    "unpkg.com",
    "cdnjs.cloudflare.com",
    # Scraping targets (arbitrage business logic)
    "www.fiverr.com",
    "fiverr.com",
    # Example/placeholder URLs (not real calls)
    "example.com",
    "example.org",
    # Documentation and versioning
    "github.com",
    "raw.githubusercontent.com",
    "registry.terraform.io",
    # Internal Docker DNS names
    "postgres",
    "redis",
    "localstack",
    "mcp-router",
    "vortex-mcp",
    "guardian-mcp",
    "oracle-mcp",
    "genesis-mcp",
    "healer-mcp",
    # Monitoring
    "prometheus",
    "grafana",
})

# Patterns that indicate hardcoded secrets (not CHANGE_ME placeholders)
HARDCODED_SECRET_PATTERNS: list[tuple[str, str]] = [
    # (pattern, description)
    (r'OPENAI_API_KEY\s*=\s*["\']?sk-[A-Za-z0-9]{20,}', "Hardcoded OpenAI key"),
    (r'ANTHROPIC_API_KEY\s*=\s*["\']?sk-ant-[A-Za-z0-9]{20,}', "Hardcoded Anthropic key"),
    (r'STRIPE_SECRET_KEY\s*=\s*["\']?sk_(?:live|test)_[A-Za-z0-9]{20,}', "Hardcoded Stripe key"),
    (r'APIFY_API_TOKEN\s*=\s*["\']?apify_api_[A-Za-z0-9]{20,}', "Hardcoded Apify token"),
    (r'password\s*=\s*["\'][^"\']{8,}["\']', "Possible hardcoded password in source"),
]

# Telemetry env var patterns to check are disabled in prod compose
TELEMETRY_VARS = ["TELEMETRY_ENABLED", "GF_ANALYTICS_REPORTING_ENABLED", "DISABLE_ANALYTICS"]

# ── Data classes ──────────────────────────────────────────────────────────────


@dataclass
class Violation:
    check: str
    severity: str  # CRITICAL | HIGH | MEDIUM | LOW
    file: str
    line: int
    detail: str
    deduction: int


@dataclass
class HermeticReport:
    generated_at: str
    project_root: str
    hermetic_score: int
    grade: str
    violations: list[Violation] = field(default_factory=list)
    checks_passed: list[str] = field(default_factory=list)
    checks_failed: list[str] = field(default_factory=list)
    compose_files_scanned: list[str] = field(default_factory=list)
    source_files_scanned: int = 0
    recommendation: str = ""


# ── Check implementations ─────────────────────────────────────────────────────


class HermeticChecker:
    """Runs all hermetic checks and accumulates violations."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.violations: list[Violation] = []
        self.checks_passed: list[str] = []
        self.checks_failed: list[str] = []
        self.compose_files: list[Path] = []
        self.source_files_scanned: int = 0

    def _add_violation(
        self,
        check: str,
        severity: str,
        file_path: Path,
        line_num: int,
        detail: str,
        deduction: int,
    ) -> None:
        rel = str(file_path.relative_to(self.root))
        self.violations.append(Violation(
            check=check,
            severity=severity,
            file=rel,
            line=line_num,
            detail=detail,
            deduction=deduction,
        ))
        if check not in self.checks_failed:
            self.checks_failed.append(check)

    def _pass(self, check: str) -> None:
        if check not in self.checks_passed and check not in self.checks_failed:
            self.checks_passed.append(check)

    # ── Check 1: docker.sock mounts (CRITICAL) ──────────────────────────────

    def check_docker_sock(self) -> None:
        """CRITICAL: docker.sock mounts break container isolation."""
        found_any = False
        for cf in self.compose_files:
            content = cf.read_text(encoding="utf-8", errors="replace")
            for i, line in enumerate(content.splitlines(), 1):
                if "docker.sock" in line and not line.strip().startswith("#"):
                    self._add_violation(
                        check="docker_sock_mount",
                        severity="CRITICAL",
                        file_path=cf,
                        line_num=i,
                        detail=f"docker.sock mount: {line.strip()[:80]}",
                        deduction=30,
                    )
                    found_any = True
        if not found_any:
            self._pass("docker_sock_mount")

    # ── Check 2: DOCKER_HOST env var (HIGH) ──────────────────────────────────

    def check_docker_host(self) -> None:
        """HIGH: DOCKER_HOST allows escaping to host Docker daemon."""
        found_any = False
        for cf in self.compose_files:
            content = cf.read_text(encoding="utf-8", errors="replace")
            for i, line in enumerate(content.splitlines(), 1):
                stripped = line.strip()
                if "DOCKER_HOST" in stripped and not stripped.startswith("#"):
                    self._add_violation(
                        check="docker_host_env",
                        severity="HIGH",
                        file_path=cf,
                        line_num=i,
                        detail=f"DOCKER_HOST env var: {stripped[:80]}",
                        deduction=20,
                    )
                    found_any = True
        if not found_any:
            self._pass("docker_host_env")

    # ── Check 3: Hardcoded secrets in source (HIGH) ───────────────────────────

    def check_hardcoded_secrets(self) -> None:
        """HIGH: Hardcoded API keys in Python/Go source code."""
        found_any = False
        compiled = [(re.compile(p, re.IGNORECASE), desc) for p, desc in HARDCODED_SECRET_PATTERNS]

        for source_dir_name in SOURCE_DIRS:
            source_dir = self.root / source_dir_name
            if not source_dir.exists():
                continue
            for path in source_dir.rglob("*"):
                if not path.is_file() or path.suffix not in SOURCE_EXTS:
                    continue
                # Skip hidden directories AND test files (test fixtures intentionally use fake values)
                try:
                    rel_parts = path.relative_to(self.root).parts
                except ValueError:
                    rel_parts = path.parts
                if any(part.startswith(".") for part in rel_parts):
                    continue
                if any(part in ("tests", "test") for part in rel_parts) or path.name.startswith("test_"):
                    continue
                self.source_files_scanned += 1
                try:
                    content = path.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                for pattern, desc in compiled:
                    for match in pattern.finditer(content):
                        line_num = content[: match.start()].count("\n") + 1
                        # Skip lines that are comments or contain CHANGE_ME
                        line_text = content.splitlines()[line_num - 1]
                        if "CHANGE_ME" in line_text or line_text.strip().startswith(("#", "//")):
                            continue
                        self._add_violation(
                            check="hardcoded_secret",
                            severity="HIGH",
                            file_path=path,
                            line_num=line_num,
                            detail=f"{desc}: {line_text.strip()[:60]}",
                            deduction=15,
                        )
                        found_any = True
        if not found_any:
            self._pass("hardcoded_secret")

    # ── Check 4: Unguarded external API calls (MEDIUM) ───────────────────────

    def check_external_api_calls(self) -> None:
        """MEDIUM: HTTP calls to domains outside the allow-list without env-var guard."""
        url_pattern = re.compile(r'https?://([a-zA-Z0-9._-]+)', re.IGNORECASE)
        found_any = False

        for source_dir_name in SOURCE_DIRS:
            source_dir = self.root / source_dir_name
            if not source_dir.exists():
                continue
            for path in source_dir.rglob("*"):
                if not path.is_file() or path.suffix not in SOURCE_EXTS:
                    continue
                # Skip hidden directories using relative path only
                try:
                    rel_parts = path.relative_to(self.root).parts
                except ValueError:
                    rel_parts = path.parts
                if any(part.startswith(".") for part in rel_parts):
                    continue
                try:
                    content = path.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                for i, line in enumerate(content.splitlines(), 1):
                    if line.strip().startswith(("#", "//", "*")):
                        continue
                    for m in url_pattern.finditer(line):
                        domain = m.group(1).lower()
                        if domain in ALLOWED_EXTERNAL_DOMAINS:
                            continue
                        # Check if this is behind an env var (os.getenv / os.environ)
                        context_window = content.splitlines()[max(0, i - 3): i + 2]
                        context = " ".join(context_window)
                        if any(guard in context for guard in ["os.getenv", "os.environ", "settings.", "getenv"]):
                            continue
                        self._add_violation(
                            check="unguarded_external_call",
                            severity="MEDIUM",
                            file_path=path,
                            line_num=i,
                            detail=f"External domain not in allow-list: {domain}",
                            deduction=5,
                        )
                        found_any = True

        if not found_any:
            self._pass("unguarded_external_call")

    # ── Check 5: Per-service API key isolation (MEDIUM) ───────────────────────

    def check_api_key_isolation(self) -> None:
        """MEDIUM: Each MCP service should have its own API key env var."""
        mcp_keys = {
            "mcp-router":   "MCP_ROUTER_API_KEY",
            "vortex-mcp":   "VORTEX_API_KEY",
            "guardian-mcp": "GUARDIAN_API_KEY",
            "oracle-mcp":   "ORACLE_API_KEY",
            "genesis-mcp":  "GENESIS_API_KEY",
            "healer-mcp":   "HEALER_API_KEY",
        }
        all_compose_content = "\n".join(
            cf.read_text(encoding="utf-8", errors="replace")
            for cf in self.compose_files
        )
        found_missing = False
        for service, key in mcp_keys.items():
            if key not in all_compose_content:
                self._add_violation(
                    check="api_key_isolation",
                    severity="MEDIUM",
                    file_path=self.root / "docker-compose.local.yml",
                    line_num=0,
                    detail=f"Service '{service}' missing per-service key: {key}",
                    deduction=5,
                )
                found_missing = True
        if not found_missing:
            self._pass("api_key_isolation")

    # ── Check 6: Telemetry disabled (LOW) ─────────────────────────────────────

    def check_telemetry(self) -> None:
        """LOW: External telemetry should be disabled or proxied."""
        local_compose = self.root / "docker-compose.local.yml"
        if not local_compose.exists():
            self._add_violation(
                check="telemetry_disabled",
                severity="LOW",
                file_path=local_compose,
                line_num=0,
                detail="docker-compose.local.yml not found — cannot verify telemetry settings",
                deduction=5,
            )
            return

        content = local_compose.read_text(encoding="utf-8", errors="replace")
        # Expect at least one TELEMETRY_ENABLED: "false" or DISABLE_ANALYTICS
        telemetry_ok = any(
            (var in content and '"false"' in content) or ("DISABLE_ANALYTICS: 1" in content)
            for var in TELEMETRY_VARS
        )
        if telemetry_ok:
            self._pass("telemetry_disabled")
        else:
            self._add_violation(
                check="telemetry_disabled",
                severity="LOW",
                file_path=local_compose,
                line_num=0,
                detail="TELEMETRY_ENABLED not explicitly set to false in docker-compose.local.yml",
                deduction=5,
            )

    # ── Check 7: Hermetic network isolation (MEDIUM) ───────────────────────────

    def check_network_isolation(self) -> None:
        """MEDIUM: Services should use a named internal bridge network."""
        local_compose = self.root / "docker-compose.local.yml"
        if not local_compose.exists():
            self._pass("network_isolation")
            return

        content = local_compose.read_text(encoding="utf-8", errors="replace")
        has_named_network = "adrion-hermetic" in content or "internal:" in content
        if has_named_network:
            self._pass("network_isolation")
        else:
            self._add_violation(
                check="network_isolation",
                severity="MEDIUM",
                file_path=local_compose,
                line_num=0,
                detail="No named hermetic network found (expected 'adrion-hermetic')",
                deduction=8,
            )

    # ── Run all checks ─────────────────────────────────────────────────────────

    def run(self) -> HermeticReport:
        # Collect compose files
        for glob in COMPOSE_GLOBS:
            self.compose_files.extend(self.root.glob(glob))
        self.compose_files = sorted(set(self.compose_files))

        # Execute checks
        self.check_docker_sock()
        self.check_docker_host()
        self.check_hardcoded_secrets()
        self.check_external_api_calls()
        self.check_api_key_isolation()
        self.check_telemetry()
        self.check_network_isolation()

        # Calculate score
        total_deduction = sum(v.deduction for v in self.violations)
        # Cap deduction per severity category
        crit_deduction = sum(v.deduction for v in self.violations if v.severity == "CRITICAL")
        high_deduction = min(
            sum(v.deduction for v in self.violations if v.severity == "HIGH"), 40
        )
        med_deduction = min(
            sum(v.deduction for v in self.violations if v.severity == "MEDIUM"), 25
        )
        low_deduction = min(
            sum(v.deduction for v in self.violations if v.severity == "LOW"), 10
        )
        score = max(0, 100 - crit_deduction - high_deduction - med_deduction - low_deduction)
        _ = total_deduction  # referenced for completeness

        if score >= 90:
            grade = "A"
            rec = "Excellent hermetic posture. No action required."
        elif score >= 80:
            grade = "B"
            rec = "Good hermetic posture. Address HIGH violations before production."
        elif score >= 70:
            grade = "C"
            rec = "Acceptable for development. Fix violations before staging deployment."
        elif score >= 50:
            grade = "D"
            rec = "Poor hermetic posture. Fix CRITICAL and HIGH violations immediately."
        else:
            grade = "F"
            rec = "CRITICAL: Hermetic enclave compromised. Do not deploy. Fix all violations."

        return HermeticReport(
            generated_at=datetime.now(timezone.utc).isoformat(),
            project_root=str(self.root),
            hermetic_score=score,
            grade=grade,
            violations=self.violations,
            checks_passed=self.checks_passed,
            checks_failed=self.checks_failed,
            compose_files_scanned=[str(cf.relative_to(self.root)) for cf in self.compose_files],
            source_files_scanned=self.source_files_scanned,
            recommendation=rec,
        )


# ── Formatters ────────────────────────────────────────────────────────────────


def print_human_report(report: HermeticReport) -> None:
    width = 62
    print()
    print("=" * width)
    print("  ShieldOS Hermetic Verification Report")
    print("=" * width)
    print(f"  Project:      {report.project_root}")
    print(f"  Generated:    {report.generated_at}")
    print(f"  Score:        {report.hermetic_score}/100  (Grade: {report.grade})")
    print(f"  Files:        {len(report.compose_files_scanned)} compose, {report.source_files_scanned} source")
    print()

    if report.checks_passed:
        print(f"  Checks PASSED ({len(report.checks_passed)}):")
        for check in sorted(report.checks_passed):
            print(f"    [OK]  {check}")

    if report.violations:
        print()
        print(f"  Violations ({len(report.violations)}):")
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        sorted_viols = sorted(report.violations, key=lambda v: severity_order.get(v.severity, 9))
        for v in sorted_viols:
            loc = f"{v.file}:{v.line}" if v.line else v.file
            print(f"    [{v.severity:<8}] {v.check}")
            print(f"              {loc}")
            print(f"              {v.detail[:70]}")
            print(f"              Score deduction: -{v.deduction}")

    print()
    print(f"  Recommendation: {report.recommendation}")
    print("=" * width)
    print()


# ── CLI ───────────────────────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="ShieldOS Hermetic Verification — ADRION 369",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit report as JSON to stdout",
    )
    parser.add_argument(
        "--project-root",
        default=str(PROJECT_ROOT),
        help="Project root directory (default: auto-detected)",
    )
    parser.add_argument(
        "--min-score",
        type=int,
        default=0,
        help="Exit with code 1 if score is below this threshold",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.project_root).resolve()

    checker = HermeticChecker(root)
    report = checker.run()

    if args.json:
        # Serialize dataclasses to dict for JSON output
        report_dict: dict[str, Any] = asdict(report)
        print(json.dumps(report_dict, indent=2))
    else:
        print_human_report(report)

    if args.min_score > 0 and report.hermetic_score < args.min_score:
        if not args.json:
            print(f"FAIL: Score {report.hermetic_score} < minimum {args.min_score}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
