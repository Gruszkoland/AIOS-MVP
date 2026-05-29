# Repo Reorg Map 2026-05-29

## Scope

Reorganizacja root bez kasowania plikow, z zachowaniem historii przez `git mv`.

## Executed moves

### Release docs

- `AIOS_V1_0_OPERATIONAL_RUNBOOKS.md` -> `docs/release/AIOS_V1_0_OPERATIONAL_RUNBOOKS.md`
- `AIOS_V1_0_PRODUCTION_READINESS_CHECKLIST.md` -> `docs/release/AIOS_V1_0_PRODUCTION_READINESS_CHECKLIST.md`
- `AIOS_V1_0_RELEASE_NOTES.md` -> `docs/release/AIOS_V1_0_RELEASE_NOTES.md`
- `V0_1_0_RELEASE_CHECKLIST.md` -> `docs/release/V0_1_0_RELEASE_CHECKLIST.md`

### Gate decisions

- `PHASE2_GATE_DECISION.md` -> `docs/gates/PHASE2_GATE_DECISION.md`
- `PHASE3_GATE_DECISION.md` -> `docs/gates/PHASE3_GATE_DECISION.md`
- `PHASE4_GATE_DECISION.md` -> `docs/gates/PHASE4_GATE_DECISION.md`
- `PHASE5_GATE_DECISION.md` -> `docs/gates/PHASE5_GATE_DECISION.md`
- `WEEK1_GATE_DECISION.md` -> `docs/gates/WEEK1_GATE_DECISION.md`
- `WEEK2_GATE_DECISION.md` -> `docs/gates/WEEK2_GATE_DECISION.md`
- `WEEK3_GATE_DECISION.md` -> `docs/gates/WEEK3_GATE_DECISION.md`
- `WEEK5_GATE_DECISION.md` -> `docs/gates/WEEK5_GATE_DECISION.md`

### Status docs

- `CURRENT_STATUS.md` -> `docs/status/CURRENT_STATUS.md`
- `V1_0_HARDENING_PLAN.md` -> `docs/status/V1_0_HARDENING_PLAN.md`

### Summaries

- `COMPREHENSIVE_IMPLEMENTATION_SUMMARY.md` -> `docs/summaries/COMPREHENSIVE_IMPLEMENTATION_SUMMARY.md`
- `EXECUTION_GUIDE_WEEK1-6.md` -> `docs/summaries/EXECUTION_GUIDE_WEEK1-6.md`

## MCP naming decision

- Wybrana opcja: A
- Canonical root directory: `mcp_servers`
- Forbidden alias: `mcp-servers`
- Enforced by: `scripts/reporting/validate_mcp_structure.py`
