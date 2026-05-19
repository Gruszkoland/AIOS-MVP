# ADR-005: Genesis Record Tiering (Hot/Warm/Cold Storage)

## Status
- [ ] Proposed

## Decision
Implement time-series archival strategy for Genesis Record:
- **Hot** (0-7 days): PostgreSQL, full queryability, 7-day Loki retention
- **Warm** (7-90 days): Compressed JSON files in S3/NAS, searchable via filename
- **Cold** (90+ days): Gzipped archives, rare access, compliant storage

Benefits: ✅ Storage cost -70% | ✅ Query performance maintained
Trade-off: ❌ Older data requires async decompression

---

**Proposed By:** Librarian | **Date:** 2026-04-05
