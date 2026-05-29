# MCP Servers Installation Guide

## Szybki start (VS Code Claude Code Extension)

```bash
pip install -r mcp-servers/requirements.txt          # install mcp SDK
python -m pytest mcp-servers/tests/ -q               # verify: 102 tests green
```

The `claude.mcpServers` block is already added to `.vscode/settings.json`.
Reload VS Code window — all 6 servers start automatically via stdio.

---

## Serwery (porta informacyjne — transport: stdio)

| Port | Server   | Entry point                         | Status  |
|------|----------|-------------------------------------|---------|
| 9000 | Router   | `mcp-servers/router/server.py`      | DONE    |
| 9001 | Vortex   | `mcp-servers/vortex/server.py`      | DONE    |
| 9002 | Guardian | `mcp-servers/guardian/server.py`    | DONE    |
| 9003 | Oracle   | `mcp-servers/oracle/server.py`      | DONE    |
| 9004 | Genesis  | `mcp-servers/genesis/server.py`     | DONE    |
| 9005 | Healer   | `mcp-servers/healer/server.py`      | DONE    |

## Manualne uruchomienie (diagnostyka)

```bash
python mcp-servers/router/server.py   # logs to stderr: [Router] MCP ready on port 9000
python mcp-servers/guardian/server.py # etc.
```

## Testy

```bash
python -m pytest mcp-servers/tests/test_integration.py -v
# Expected: 102 passed
```

