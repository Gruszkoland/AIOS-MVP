# Copilot Reorganization Rollback Checklist

## Rollback Trigger Conditions
- Any config parse error in .roo/mcp.json, .vscode/settings.json, .vscode/tasks.json.
- Hook execution instability after changes.
- CI health job failing on configuration integrity.

## Rollback Steps
1. Locate latest snapshot in .reorg_snapshot/<timestamp>/.
2. Restore files:
   - .roo/mcp.json
   - .roo.json
   - .roorc
   - .roomodes
   - .vscode/settings.json
   - .vscode/tasks.json
3. Restore user hook files from snapshot:
   - %USERPROFILE%\.agents\hooks\hooks.json
   - %USERPROFILE%\.agents\hooks\scripts\track-telemetry.ps1
4. Re-run validation:
   - scripts/reporting/validate_copilot_workspace.ps1
5. Confirm workspace health and close incident.

## Recovery Verification
- JSON parse checks pass.
- No PostToolUse non_blocking_error in immediate smoke run.
- report file exists at reports/copilot_stability_report.json.

## Post-Rollback Actions
- Open incident note in PROGRESS.
- Identify root cause and patch in a new change set.
