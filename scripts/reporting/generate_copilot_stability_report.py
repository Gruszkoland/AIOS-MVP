from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def _safe_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    report_dir = root / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    settings_path = root / ".vscode" / "settings.json"
    tasks_path = root / ".vscode" / "tasks.json"
    mcp_path = root / ".roo" / "mcp.json"

    settings = _safe_json(settings_path)
    tasks = _safe_json(tasks_path)
    mcp = _safe_json(mcp_path)

    search_exclude = settings.get("search.exclude", {})
    watcher_exclude = settings.get("files.watcherExclude", {})

    task_count = len(tasks.get("tasks", [])) if isinstance(tasks, dict) else 0
    mcp_servers = mcp.get("mcpServers", {}) if isinstance(mcp, dict) else {}
    enabled_servers = [
        name
        for name, cfg in mcp_servers.items()
        if isinstance(cfg, dict) and not cfg.get("disabled", False)
    ]

    data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "workspace": str(root),
        "checks": {
            "settings_exists": settings_path.exists(),
            "tasks_exists": tasks_path.exists(),
            "mcp_exists": mcp_path.exists(),
            "task_count": task_count,
            "mcp_servers_enabled": len(enabled_servers),
        },
        "details": {
            "enabled_mcp_servers": enabled_servers,
            "search_exclude_keys": sorted(search_exclude.keys()),
            "watcher_exclude_keys": sorted(watcher_exclude.keys()),
        },
    }

    out = report_dir / "copilot_stability_report.json"
    out.write_text(json.dumps(data, indent=2, ensure_ascii=True), encoding="utf-8")
    print(str(out))


if __name__ == "__main__":
    main()
