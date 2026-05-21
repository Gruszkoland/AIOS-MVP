from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _check_commands() -> dict:
    required = [
        "python",
        "git",
        "node",
        "npm",
        "docker",
        "pwsh",
    ]
    return {cmd: bool(shutil.which(cmd)) for cmd in required}


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    report_dir = root / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    settings = _read_json(root / ".vscode" / "settings.json")
    extensions = _read_json(root / ".vscode" / "extensions.json")
    mcp = _read_json(root / ".roo" / "mcp.json")

    recs: list[str] = []

    commands = _check_commands()
    for cmd, ok in commands.items():
        if not ok:
            recs.append(f"Install missing CLI: {cmd}")

    mcp_servers = mcp.get("mcpServers", {}) if isinstance(mcp, dict) else {}
    if not mcp_servers:
        recs.append("No MCP servers configured in .roo/mcp.json")

    disabled = [
        name
        for name, cfg in mcp_servers.items()
        if isinstance(cfg, dict) and cfg.get("disabled", False)
    ]
    if disabled:
        recs.append("Review disabled MCP servers: " + ", ".join(disabled))

    recommended_extensions = set(
        extensions.get("recommendations", []) if isinstance(extensions, dict) else []
    )
    if not recommended_extensions:
        recs.append("No recommended VS Code extensions configured")

    watcher_exclude = settings.get("files.watcherExclude", {}) if isinstance(settings, dict) else {}
    if "**/node_modules/**" not in watcher_exclude:
        recs.append("Add node_modules to files.watcherExclude")

    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "workspace": str(root),
        "command_availability": commands,
        "recommendations": recs,
        "recommendations_count": len(recs),
    }

    out = report_dir / "tooling_recommendations_report.json"
    out.write_text(json.dumps(output, indent=2, ensure_ascii=True), encoding="utf-8")
    print(str(out))


if __name__ == "__main__":
    main()
