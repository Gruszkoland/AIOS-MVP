# 🎯 QUICK START — ADRION 369 × VS CODE (5 MINUT)

## Uruchom teraz:

```bash
# 1. Install
pip install -r mcp-servers/requirements.txt

# 2. Setup
python scripts/setup_shieldos_local.py

# 3. Containers
docker-compose -f docker-compose.local.yml up -d postgres redis

# 4. Verify
python scripts/verify_shieldos_hermetic.py

# 5. Reload VS Code
# (Ctrl+Shift+P → Reload Window)
```

## Gotowe! 🎉

VS Code Claude Code Extension teraz widzi:
- ✅ 6 MCP Servers (9000-9005)
- ✅ 9 Agent Personas (AIO, PAA, TDO, ...)
- ✅ ROPE 3.0 Workflow
- ✅ Hermetic ShieldOS

---

## Co masz:

| Komponent | Lokalizacja | Status |
|-----------|-------------|--------|
| MCP Servers | `mcp-servers/` | Ready |
| Agent Personas | `docs/ROPE_3.0_PERSONAS.md` | Ready |
| Setup Scripts | `scripts/setup_*.py` | Ready |
| Full Docs | `MASTER_DELIVERY_SUMMARY.md` | Ready |

---

## Testy:

```bash
# MCP Servers (102 tests)
cd mcp-servers && python -m pytest tests/ -v

# Trace Propagation (32 tests)
python -m pytest tests/test_trace_propagation.py -v

# Hermetic Check
python scripts/verify_shieldos_hermetic.py

# GitHub Actions (dry-run)
bash scripts/setup_shieldos_ci.sh --dry-run
```

---

## Problemy?

```bash
# Diagnostic
python scripts/setup_shieldos_local.py --dry-run --json

# Logs
tail -f logs/shieldos_setup_*.jsonl

# Health check
curl http://localhost:9000/health
```

---

## Następny krok?

Przeczytaj: **`MASTER_DELIVERY_SUMMARY.md`**

Zawiera pełny plan:
- ✅ ETAP 1: Aktivacja (co zrobiłeś teraz)
- ⏳ ETAP 2: Weryfikacja (30-60 minut)
- ⏳ ETAP 3: EVA-33 Validation (1 dzień)
- ⏳ ETAP 4: Deployment (1 tydzień)
