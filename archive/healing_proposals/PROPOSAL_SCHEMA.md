# Healing Proposal Schema

Each healing proposal is a JSON file dropped into this directory by the HEALER agent.
**No proposal is ever executed automatically.** A human must run `scripts/approve_healing.py`
to review and approve.

## Filename convention

```
YYYY-MM-DDTHH-MM-SS_<component>_<id>.json
```

Example: `2025-07-01T14-32-00_database_h001.json`

## JSON schema

```json
{
  "proposal_id":  "h001",
  "created_at":   "2025-07-01T14:32:00Z",
  "component":    "database",
  "severity":     "HIGH",
  "symptom":      "Connection pool exhausted — 95 % utilisation for 5 min",
  "root_cause":   "Long-running query blocked pool; pool_size=5 is too small",
  "action":       "Increase DB_POOL_SIZE from 5 to 15 and restart service",
  "env_changes": {
    "DB_POOL_SIZE": "15"
  },
  "rollback":     "Revert DB_POOL_SIZE to 5 and restart",
  "evidence":     ["logs/healer.log#L420", "monitoring/alerts/2025-07-01.json"],
  "status":       "pending",
  "approved_by":  null,
  "approved_at":  null,
  "rejected_reason": null
}
```

## Status lifecycle

`pending` → (human reviews via `approve_healing.py`) → `approved` | `rejected`

Approved proposals are not executed by the script — they are marked and the operator
applies the `action` manually or via a separate deployment pipeline.
