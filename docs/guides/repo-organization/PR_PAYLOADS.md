# PR Payloads - Repository Organization

## PR 1 - Formula Repository

### Suggested Title

`chore(formula): establish canonical scope and migration guardrails`

### Body (ready to paste)

```md
## Summary

This PR formalizes the Formula repository as the canonical source of ADRION definitions and contracts.

## Scope

- Define mission and ownership for Formula
- Freeze canonical domains (3-6-9, D162, Guardian laws, contracts)
- Explicitly mark out-of-scope content (runtime, ops, deployment)
- Add migration guardrails for downstream repos

## Changes

- Add mission statement and repository intent
- Define canonical folder ownership
- Document dependency rule: Formula -> Architecture -> System
- Add contribution policy for canonical changes

## Acceptance Criteria

- Formula has explicit canonical-only ownership
- No runtime/product ownership declared in Formula
- Downstream dependency rule documented
- Canonical change policy documented

## Risk

- Low operational risk, medium governance impact

## Rollback

- Revert documentation/governance commit set

## Validation

- Peer review by architecture owner
- Governance sign-off by platform lead
```

---

## PR 2 - Architecture Repository

### Suggested Title

`chore(architecture): enforce reference-implementation boundaries`

### Body (ready to paste)

```md
## Summary

This PR aligns the Architecture repository to the reference-implementation role.

## Scope

- Set architecture ownership for core/ecosystem/security reference modules
- Define integration-facing outputs for System repo
- Restrict operational and domain-specific drift
- Add compatibility and release expectations

## Changes

- Update mission and scope boundaries
- Define required quality gates (tests, typing, canonical sync)
- Define release and compatibility contract for System consumers
- Document exclusion of heavy operational artifacts

## Acceptance Criteria

- Architecture ownership is explicit and non-overlapping
- Canonical sync dependency on Formula documented
- Operational scope exclusions documented
- Release compatibility notes required by policy

## Risk

- Low runtime risk, medium process-change risk

## Rollback

- Revert boundary and process documents

## Validation

- Architecture owner approval
- System consumer approval for compatibility contract
```

---

## PR 3 - System Repository

### Suggested Title

`chore(system): align operational repository structure and retention policy`

### Body (ready to paste)

```md
## Summary

This PR aligns the System repository to an operations-first structure and removes conceptual overlap with Formula and Architecture repositories.

## Scope

- Confirm System ownership for apps/services/platform/ops
- Define non-ownership of canonical redefinition
- Introduce archive/retention direction for heavy historical data
- Establish dependency flow from Architecture and Formula

## Changes

- Update mission and operational ownership
- Define active vs archival artifact policy
- Add governance references for canonical imports
- Add migration safety principles for staged rollout

## Acceptance Criteria

- System scope focuses on runtime operations
- Canonical duplication policy documented
- Retention policy documented
- Dependency model documented

## Risk

- Medium migration risk if folder moves are executed without batching

## Rollback

- Batch-based rollback per migration PR
- Restore previous folder map from pre-migration tag
- Keep active runtime paths stable during rollback

## Validation

- Smoke checks after each migration batch
- Platform and ops lead sign-off
```
