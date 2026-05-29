from kimi_migration.antifragile_memory import AntifragileMemory, Patch
from kimi_migration.genesis_ledger import GenesisLedger


def test_antifragile_learn_logs_to_ledger() -> None:
    ledger = GenesisLedger()
    memory = AntifragileMemory(ledger)

    patch = Patch(
        patch_id="p1",
        source_agent_id="agent-1",
        target_issue="issue-x",
        strategy={"step": "fix"},
    )

    memory.learn_from_repair(patch, success=True)
    assert ledger.count == 1
    assert memory.top_patches(min_success_rate=0.5)


def test_report_application_updates_success_rate() -> None:
    ledger = GenesisLedger()
    memory = AntifragileMemory(ledger)

    patch = Patch(
        patch_id="p2",
        source_agent_id="agent-2",
        target_issue="issue-y",
        strategy={"step": "patch"},
    )

    memory.learn_from_repair(patch, success=False)
    memory.report_application("p2", success=True)
    top = memory.top_patches(min_success_rate=0.2)
    assert top
