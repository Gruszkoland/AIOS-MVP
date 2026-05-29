# Review Bucket Mapping - Folder by Folder

## Decision Matrix

| Folder                          | Decision              | Target Location                                                                                   | Notes                                                        |
| ------------------------------- | --------------------- | ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| `162 demencje w schemacie 369/` | `archive`             | External archival storage or dedicated audit repo                                                 | Large historical assets, keep out of active development path |
| `adrion-swarm/`                 | `keep`                | `system/services/orchestration/adrion-swarm/`                                                     | Runtime orchestration component                              |
| `agents/`                       | `move`                | Reference definitions -> `architecture/adapters/` ; runtime wrappers -> `system/services/agents/` | Split by ownership                                           |
| `tools/`                        | `move`                | Ops tools -> `system/ops/scripts/tools/` ; validation tools -> `architecture/scripts/validate/`   | Separate ops vs architecture tooling                         |
| `n8n-workflows/`                | `keep`                | `system/apps/automation/n8n-workflows/`                                                           | Operational automation assets                                |
| `PROJEKTY/`                     | `archive`             | Project archive storage                                                                           | Out-of-band initiatives, not active system runtime           |
| `poc/`                          | `move`                | Active PoC -> `architecture/experiments/poc/` ; stale PoC -> archive                              | Time-box PoC assets                                          |
| `temp_swiadoma_ai/`             | `delete-after-backup` | Backup first, then remove from active repo                                                        | Temporary directory                                          |

## Execution Rules

1. `delete-after-backup` requires:
   - full file listing
   - checksum manifest
   - explicit user approval
2. `archive` requires:
   - destination path confirmed
   - retrieval index added to system docs
3. `move` requires:
   - path mapping committed
   - import/script references updated

## Change Tracking

- Every folder decision must be executed in a separate migration PR or clearly scoped batch.
- No destructive operation is allowed without explicit confirmation.
