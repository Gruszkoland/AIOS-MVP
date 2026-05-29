from kimi_migration.genesis_ledger import GenesisLedger, make_record


def test_genesis_append_and_count() -> None:
    ledger = GenesisLedger()
    ledger.append(make_record("a1", {"integrity": 0.2}, "trace-1", 0.5))
    ledger.append(make_record("a2", {"integrity": 0.6}, "trace-2", 0.9))
    assert ledger.count == 2
    assert ledger.latest_hash() != "GENESIS"


def test_query_by_kurs_drift() -> None:
    ledger = GenesisLedger()
    ledger.append(make_record("a1", {"integrity": 0.1}, "low", 0.4))
    ledger.append(make_record("a2", {"integrity": 0.8}, "high", 0.8))
    result = ledger.query_by_kurs_drift(0.3)
    assert len(result) == 1
    assert result[0].decision_trace == "high"
