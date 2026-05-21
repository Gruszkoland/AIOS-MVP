# Copilot Workspace Reorganization Runbook

## Scope
- Repair broken agent/config files.
- Stabilize PostToolUse hooks.
- Reduce indexing noise and diagnostics overload.
- Add CI health checks for Copilot/Roo configuration.

## Executed Changes
1. Repaired malformed config in .roo/mcp.json.
2. Moved secret-bearing values to environment placeholders.
3. Added missing files referenced by settings: roo.profiles.json, roo.rules.json.
4. Added root env template with required variables.
5. Disabled heavy telemetry hook by default for PostToolUse.
6. Added validation and reporting scripts.
7. Added CI workflow for ongoing config health checks.
8. Added index/search excludes for looped and archive-heavy paths.

## Verification Commands
```powershell
Set-Location C:\Users\adiha\.1_Projekty
pwsh -File scripts/reporting/validate_copilot_workspace.ps1
python scripts/reporting/generate_copilot_stability_report.py
```

## KPI Targets
- Parse errors in critical config files: 0
- PostToolUse timeout events: 0 in smoke run
- Duplicate active instruction sources: reduced to one active source per rule set
- Problems noise reduction: >= 70% after markdown/archive filtering

## Notes
- Historical archives were isolated from indexing, not deleted.
- Destructive cleanup (deletions) requires explicit user approval.
