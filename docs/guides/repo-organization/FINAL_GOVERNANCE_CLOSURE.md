# Final Governance Closure Plan

Typ dokumentu: How-to + governance

## Scope

This document closes Phase F governance requirements for the migration program.

## CODEOWNERS

- Status: Active
- File: `.github/CODEOWNERS`
- Update: Rust crate ownership remapped to migrated paths.

## Branch Protection Policy (Procedural)

Required rules for `main` and `master`:

1. Require at least one approved review before merge.
2. Require all status checks to pass.
3. Require branch to be up to date before merge.
4. Restrict force push and branch deletion.

Execution status:

- Repo setting change required in GitHub UI.
- Technical prep in repository: Done.

## Required Check Set

Mandatory checks for merge gate:

- `repo-context-gate`
- `quality-lane / python-quality`
- `quality-lane / rust-memory-safety`
- `ADRION 369 Python CI`
- `Rust CI/CD`

## Closure Evidence

- SSOT file exists and validates.
- Version alignment check passes.
- Post-migration reference mapping report generated.
- Rust and compose path updates applied to active operational files.

## Final Sign-off Criteria

All of the following must be true:

1. PR for migration branch is merged.
2. Mandatory checks are green on merge commit.
3. Branch protection rules enabled on default branch.
4. Migration tracker moved to `closed` state.
