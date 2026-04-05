# ADR-001: Use DSPy Signatures for MoE Gating

## Status
- [x] Accepted
- [ ] Deprecated
- [ ] Replaced by

## Context

ADRION 369's multi-agent system (MoE) requires precise routing of tasks to 6 specialized agents.
Without formal schema validation (Input→Output), MoE gating becomes error-prone.

**Problem:** Task mismatches between (Librarian, SAP, Auditor, Sentinel, Architect, Healer) cause:
- Type errors in cross-agent communication
- Invalid agent state transitions
- Unpredictable behavior in crisis mode

**Solution:** DSPy Signatures provide deklarative Input/Output schemata with automatic validation.

## Decision

Adopt DSPy Signature Validator (DSV) as the core MoE gating mechanism:
1. Every agent implements a DSPy `Signature` (Input/Output schema)
2. Before delegating tasks to agents (Step 1.5), DSV validates task schema match
3. Tasks failing validation are rejected immediately
4. Rejection triggers Auditor review + error logging

## Consequences

### Plusy (+)
- ✅ Eliminates type mismatches in agent communication
- ✅ Formal guarantee: each agent receives correct data types
- ✅ Self-documenting API (sygnatury are explicit contracts)
- ✅ Enables automated testing of MoE routing logic

### Minusy (-)
- ❌ +50ms latency per validation (acceptable for 162D space)
- ❌ Requires refactoring existing agents to DSPy (one-time cost)
- ❌ Adds dependency on `dspy` library

## Guardian Laws Impact

- **G1 (Unity):** High — ensures coherent agent communication
- **G4 (Causality):** Critical — formalizes causation chain (Task → Input schema → Agent logic)
- **G5 (Transparency):** High — signatures are human-readable contracts
- **G6 (Authenticity):** Critical — validates authenticity of input data
- **G7 (Privacy):** Low — no privacy concern, pure validation
- **G8 (Nonmaleficence):** High — fails safely (reject invalid inputs)
- **G9 (Sustainability):** Medium — validation overhead is acceptable vs. correctness

## 162D Decision Space Mapping

- **Perspective:** Intellectual (formal logic + schema validation)
- **Agents Involved:** Architect (design), SAP (implementation), Auditor (testing)
- **Reliability Mechanism:** DSV [7] — DSPy Signature Validator
- **Related ADRs:** ADR-004 (SAV verification), ADR-006 (Arbitrium consensus)

## Implementation Details

| Component | File | Status |
|-----------|------|--------|
| DSPy library | `requirements-arbitrage.txt` | ✅ Installed |
| MoE Gating Module | `arbitrage/orchestrator.py#_moe_gate()` | ✅ Implemented |
| Validator Test Suite | `tests/test_dspy_validator.py` | ✅ 80%+ coverage |
| Error Handling | `arbitrage/guardian.py` | ✅ Logged as threat vector |

## Alternatives Considered

### ❌ Option 1: No Validation
- Faster, but unmaintainable
- Violates G4 (Causality) and G6 (Authenticity)
- **Rejected:** Too risky for production

### ❌ Option 2: Pydantic Models
- Simpler to learn, but less expressive
- No composable reasoning support
- **Rejected:** Insufficient for 162D complexity

## Revisit Date

**Quarterly:** 2026-07-05 (Q2/Q3 review)  
**Triggers for earlier review:**
- Performance degrades >100ms
- >5% task rejection rate
- New agent types require different schema

---

**Approved By:** MASTER ORCHESTRATOR  
**Implementation Lead:** Architect Persona  
**Date Accepted:** 2026-04-05
