# KIMI Migration Notes

## Mapping

- Source: C:/Users/adiha/Desktop/KIKI-AIOS_COMPLETE/F0-Z2_trinity_v1_kurs.py
- Target: kimi_migration/trinity_kurs.py
- Adaptation: Extracted only stable KursVector and drift evaluation API; removed runtime side effects.

- Source: C:/Users/adiha/Desktop/KIKI-AIOS_COMPLETE/F0-Z3_genesis_v1.py
- Target: kimi_migration/genesis_ledger.py
- Adaptation: Append-only ledger with lock and deterministic hash helper; simplified query by drift.

- Source: C:/Users/adiha/Desktop/KIKI-AIOS_COMPLETE/F2-Z11_antifragile_memory_v2.py
- Target: kimi_migration/antifragile_memory.py
- Adaptation: Reduced to safe patch learning/reporting model with Genesis logging hooks.

## Syntax Repair Log

- Fixed multiline string syntax breakages in copied KIKI scripts via scripts/reporting/repair_kiki_syntax.py.
- Validation result in migration zone: PY_OK=30, PY_ERR=0.

## Runtime Policy

- KIMI integration remains optional.
- Activation flag: ENABLE_KIMI_MODULES=1.
- Default runtime path unchanged when flag is not set.
