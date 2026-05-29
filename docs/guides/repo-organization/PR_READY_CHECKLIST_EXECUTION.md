# PR-Ready Checklist - Immediate Execution

## Scope

This checklist is formatted for direct PR usage and reflects tasks executed immediately in the current migration wave.

## Checklist

### A. Mission Statements in Three Repositories

- [x] System repo README updated with mission statement
  - Path: `README.md`
- [x] Architecture repo README updated with mission statement
  - Path: `PROJEKTY/adrion-369-architecture/README.md`
- [x] Formula repo README created with mission statement scaffold
  - Path: `PROJEKTY/adrion-architecture-formula/README.md`

### B. Batch #1 Real Folder Moves (No Deletion)

- [x] Migration staging path created
  - Path: `migration_batches/batch1/review-bucket/`
- [x] Folder moved: `poc/` -> `migration_batches/batch1/review-bucket/poc/`
- [x] Folder moved: `temp_swiadoma_ai/` -> `migration_batches/batch1/review-bucket/temp_swiadoma_ai/`
- [x] Folder moved: `162 demencje w schemacie 369/` -> `migration_batches/batch1/review-bucket/162 demencje w schemacie 369/`

### C. PR Artifacts and Governance Docs

- [x] PR payloads document present
  - Path: `docs/guides/repo-organization/PR_PAYLOADS.md`
- [x] Review bucket mapping present
  - Path: `docs/guides/repo-organization/REVIEW_BUCKET_MAPPING.md`
- [x] Daily migration checklist with owner/deadline present
  - Path: `docs/guides/repo-organization/MIGRATION_DAILY_CHECKLIST.md`

## Risks Introduced by Batch #1

- Relative path assumptions may break for moved folders (`poc`, temp paths).
- Any script expecting old root paths must be updated in next batch.

## Logical Rollback (Batch #1)

1. Move folders back to root:
   - `migration_batches/batch1/review-bucket/poc` -> `poc`
   - `migration_batches/batch1/review-bucket/temp_swiadoma_ai` -> `temp_swiadoma_ai`
   - `migration_batches/batch1/review-bucket/162 demencje w schemacie 369` -> `162 demencje w schemacie 369`
2. Re-run smoke commands for scripts depending on root paths.
3. Keep migration staging folder for audit trail.

## Next Immediate PR Sequence

1. PR-Formula: canonical governance and contracts freeze
2. PR-Architecture: reference boundary enforcement
3. PR-System: operational structure alignment after path updates

---

## D. Batch #2 Real Folder Moves (No Deletion)

- [x] Migration staging path created
  - Path: `migration_batches/batch2/`
- [x] Folder moved: `adrion-swarm/` -> `migration_batches/batch2/to-system/adrion-swarm/`
- [x] Folder moved: `n8n-workflows/` -> `migration_batches/batch2/to-system/n8n-workflows/`
- [x] Folder moved: `tools/` -> `migration_batches/batch2/to-system/tools/`
- [x] Folder moved: `agents/` -> `migration_batches/batch2/to-architecture/agents/`
- [x] Folder moved: `PROJEKTY/` -> `migration_batches/batch2/to-archive/PROJEKTY/`

## E. Smoke and Week 1 Gate

- [x] Path smoke PASS for governance artifacts and batch2 destinations
- [x] KPI script executed in warmup mode (result: PENDING due to insufficient events)
- [x] Week 1 Gate status: `PASS` (boundary freeze scope completed)

### Week 1 Gate Closure Notes

- Mission statements are in place for System, Architecture, and Formula repository targets.
- Governance artifacts are present and updated.
- Batch #1 and Batch #2 migration moves were executed without deletions.
