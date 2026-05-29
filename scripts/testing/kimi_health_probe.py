from __future__ import annotations

from kimi_migration.feature_flags import is_kimi_enabled
from kimi_migration.trinity_kurs import KursVector, evaluate_kurs_drift
from kimi_migration.genesis_ledger import GenesisLedger, make_record
from kimi_migration.antifragile_memory import AntifragileMemory, Patch


def main() -> int:
    if not is_kimi_enabled():
        print("KIMI_HEALTH=SKIPPED (feature flag disabled)")
        return 0

    ledger = GenesisLedger()
    memory = AntifragileMemory(ledger)
    drift = evaluate_kurs_drift(KursVector(0.9, 0.9, 0.9, 0.9, 0.9), 0.3)

    patch = Patch(
        patch_id="probe-1",
        source_agent_id="probe-agent",
        target_issue="probe",
        strategy={"action": "validate"},
    )
    memory.learn_from_repair(patch, success=True)
    ledger.append(make_record("probe-agent", {"integrity": drift}, "probe-drift", 0.7))

    if ledger.count < 2:
        print("KIMI_HEALTH=FAIL ledger count too low")
        return 1

    print("KIMI_HEALTH=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
