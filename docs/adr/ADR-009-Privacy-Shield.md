# ADR-009: Privacy Shield Implementation (G7)

## Status
- [ ] Proposed

## Decision
Enforce **Local-First Privacy by Default** (Guardian Law G7):
- **Default storage:** SQLite3 (local, no cloud)
- **Secrets management:** python-dotenv for .env (never committed)
- **Fallback:** PostgreSQL only in production with encrypted credentials
- **LLM inference:** Ollama local-first (11434), offline-capable
- **TLS enforcement:** All external connections use TLS 1.3+

Benefits: ✅ Data sovereignty | ✅ GDPR-compliant | ✅ Offline-capable
Trade-off: ❌ Distributed setup requires more ops knowledge

---

**Proposed By:** Guardian Persona | **Date:** 2026-04-05
