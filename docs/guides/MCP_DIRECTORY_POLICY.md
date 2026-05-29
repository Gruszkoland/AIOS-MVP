# MCP Directory Policy

## Canonical naming

- Root canonical directory: `mcp_servers`
- Root alias forbidden: `mcp-servers`

## Scope rule

- This policy applies to repository root only.
- Nested subprojects can retain legacy names for compatibility until migrated.

## CI enforcement

- Validation script: `scripts/reporting/validate_mcp_structure.py`
- Enforced in:

  - `.pre-commit-config.yaml`
  - `.github/workflows/python-ci.yml`
  - `.github/workflows/repo-governance.yml`

## Migration recommendation

1. Keep legacy nested paths stable during active development.
2. Add per-subproject migration issue and timeline.
3. Migrate one subproject at a time to avoid breaking automation.
