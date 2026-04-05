# ADR-005: PostgreSQL jako immutable audit log (Genesis Record)

**Status:** ZAAKCEPTOWANY
**Data:** 2025-Q4
**Autor:** ADRION Core Team

---

## Kontekst

Każda decyzja ADRION musi być zapisana w sposób niemodyfikowalny dla celów:

- Audytu (compliance, regulacje)
- Debugowania (dlaczego system podjął daną decyzję?)
- Uczenia (fine-tuning Trinity na historycznych danych)

Analizowane opcje:

| Opcja                      | Immutability | Queries | Skalowalność   | Złożoność     |
| -------------------------- | ------------ | ------- | -------------- | ------------- |
| **PostgreSQL append-only** | ✅ trigger   | ✅ SQL  | ✅             | średnia       |
| SQLite                     | partial      | ✅      | ❌ single-file | niska         |
| Flat-file (.jsonl)         | partial      | ❌ scan | ❌             | niska         |
| Kafka (event stream)       | ✅           | partial | ✅             | wysoka        |
| Blockchain                 | ✅           | ❌      | ❌             | bardzo wysoka |

## Decyzja

**PostgreSQL** (`genesis_record` database) z append-only enforcement:

- Application user ma TYLKO INSERT + SELECT permissions
- UPDATE i DELETE zablokowane na poziomie DB user
- Każdy rekord zawiera SHA-256 hash poprzedniego rekordu (chain integrity)
- Backup: `scripts/backup/backup-postgres.sh` (daily cron)

```sql
-- db/migrations/001_initial_schema.sql
CREATE TABLE decisions (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    request_hash TEXT NOT NULL,
    trinity_score NUMERIC(4,3),
    guardians_compliance INT,
    decision TEXT NOT NULL CHECK (decision IN ('APPROVED', 'DENIED')),
    justification TEXT,
    prev_hash TEXT,  -- chain integrity
    record_hash TEXT GENERATED ALWAYS AS (...) STORED
);
-- Brak GRANT UPDATE, DELETE dla app user
```

## Konsekwencje

### Plusy

- Pełna audytowalność: żaden log nie może być cofnięty ani zmodyfikowany
- ACID compliance: brak partial writes
- SQL queries dla analizy historii decyzji (aggregation, time-series)
- Integracja z Prometheus (metrics z DB stats)

### Minusy / Ryzyki

- Write overhead: każda decyzja = INSERT + fsync (szacowany 5-15ms overhead)
- Wymaga PostgreSQL running (nie działa w trybie embedded)
- Backup procedura krytyczna: utrata DB = utrata historii decyzji
- ⚠️ **DŁUG TECHNICZNY**: obecna implementacja w `backend/app.py` to SIMULACJA
  — rzeczywisty INSERT do PostgreSQL nie jest zaimplementowany

## Plan wdrożenia (M3)

```python
# backend/app.py — do implementacji w M3
from arbitrage.database import get_pooled_conn

def _persist_decision(decision_data: dict) -> None:
    conn = get_pooled_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO decisions (request_hash, trinity_score,
                    guardians_compliance, decision, justification)
                VALUES (%s, %s, %s, %s, %s)
            """, (...))
        conn.commit()
    finally:
        return_conn(conn)
```

## Powiązane ADR

- ADR-001: Trinity-EBDI (każda decyzja wymaga persystencji)
- `docs/DISASTER_RECOVERY.md`
- `scripts/backup/backup-postgres.sh`
