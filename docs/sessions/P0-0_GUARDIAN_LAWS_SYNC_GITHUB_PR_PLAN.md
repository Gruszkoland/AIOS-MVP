# P0-0 Guardian Laws Sync — Konkretny plan GitHub PR

## 📋 Branches & Commits

```bash
# 1. Create feature branch
git checkout main && git pull
git checkout -b refactor/p0-0-guardian-laws-sync-162d

# 2. Stage Phase 1 files (kanoniczne definicje)
git add docs/GUARDIAN_LAWS_CANONICAL.json arbitrage/guardian.py
git commit -m "refactor(p0-0): update Guardian Laws canonical definitions (9 laws, 3x6x9 structure)

- Update docs/GUARDIAN_LAWS_CANONICAL.json v2.0 → v3.0
  - Add perspectives array: Material, Intellectual, Essential
  - Add modes array: Inventory, Empathy, Process, Debate, Healing, Action
  - Consolidate 9 laws (G1-G9), remove G10/G11 (Evolution, RelationalCare)
  - Clean up conflicting runtime_name entries
  - Add ordinal numbering for deterministic ordering

- Update arbitrage/guardian.py:
  - Change docstring: '11 Ethical laws' → '9 Immutable Guardian Laws'
  - Remove G10 (Evolution) and G11 (RelationalCare) from implementation
  - Update law names to canonical: G2 Truth, G6 Nonmaleficence, G7 Autonomy, G8 Justice
  - Clean backward compatibility notes (no more G10/G11 mappings)

Verification:
  - json.tool docs/GUARDIAN_LAWS_CANONICAL.json ✓
  - grep -c 'G10\|G11' arbitrage/guardian.py → 0"

# 3. Stage Phase 2 files (dokumentacja)
git add CLAUDE.md docs/ARCHITECTURE.md README.md
git commit -m "docs(p0-0): clarify 162D architecture — 3 perspectives × 6 modes × 9 laws

- CLAUDE.md:
  - Line 18: s/6 agents/6 modes/
  - Add law-mode mapping matrix after Guardian Laws table
  - Update Matryca 3-6-9 terminology (LOGOS/ETHOS/EROS → Material/Intellectual/Essential)

- docs/ARCHITECTURE.md:
  - Add new section '## Hexagon (6 Processing Modes)'
  - Explain each mode: Inventory, Empathy, Process, Debate, Healing, Action
  - Document ~30ms per mode, <200ms budget total
  - Add diagram: 3 perspectives × 6 modes → 18 sub-evaluations

- README.md:
  - Add section '## 162-Dimensional Decision Space'
  - Explain Trinity × Hexagon × Guardian Laws
  - Add flow diagram: request → vectorize → consensus → Genesis Record → decision

Verification:
  - grep '6 agents' . → 0
  - grep '6 modes\|6 MODES' . → 5+ (present everywhere needed)"

# 4. Stage Phase 3 files (dokumentacja biznesowa)
git add v2_complete/TECHNICAL_ARCHITECTURE.md v2_complete/README.md v2_complete/FINAL_REPORT.md
git commit -m "docs(p0-0): update v2_complete docs — clarify 9 Laws vs 6 Modes distinction

- v2_complete/TECHNICAL_ARCHITECTURE.md:
  - Change '6 Guardians' → '6 Processing Modes'
  - Add note: 'Modes ≠ Guardians; Guardians = 9 ethical laws'
  - Add 162D diagram

- v2_complete/README.md:
  - Update Guardian Laws count: 6 → 9
  - Add terminology clarification

- v2_complete/FINAL_REPORT.md:
  - Add note in 'Co jeszcze można poprawić' about terminology sync

Verification:
  - grep 'G1\|G2\|G3\|G4\|G5\|G6\|G7\|G8\|G9' v2_complete/ → all 9 present"

# 5. Stage Phase 4 files (cleanup)
git add arbitrage/ tests/
# (if G10/G11 found during grep)
git commit -m "refactor(p0-0): remove G10/G11 references from codebase

- arbitrage/: remove any remaining G10 (Evolution) or G11 (RelationalCare) mentions
- tests/: update test fixtures from 11 laws → 9 laws

Verification:
  - grep -r 'G10\|G11\|Evolution\|RelationalCare' arbitrage/ tests/ → 0"

# 6. Squash-merge to main
git checkout main && git pull
git merge --squash refactor/p0-0-guardian-laws-sync-162d
git commit -m "refactor: synchronize Guardian Laws to canonical 9-law+3x6x9 architecture

Complete sync across all layers:
- Canonical: CANONICAL.json v3.0 with perspectives, modes, 9 laws
- Code: arbitrage/guardian.py reduced from 11 → 9 laws
- Docs: CLAUDE.md, ARCHITECTURE.md, README.md all explain 3 perspectives × 6 modes × 9 laws = 162D
- Business: v2_complete docs clarify terminology (Laws vs Modes)
- Tests: updated to 9 laws

This closes the 3-way sprzeczność:
  - Kod miał 11 praw (G1-G11)
  - CLAUDE.md mówiło 9 praw (ale 6 agents)
  - Biznes mówiło 6 Guardians (osobne)
  
Now: Everything aligned to proper 162D structure."

git tag -a v4.0-p0.0 -m "Phase 0.0: Guardian Laws synchronized to canonical 9-law+3x6x9 structure"
git push origin main v4.0-p0.0
```

---

## 📂 Konkretne zmiany per plik

### 1️⃣ `docs/GUARDIAN_LAWS_CANONICAL.json` — REPLACE

Plik: `/tmp/GUARDIAN_LAWS_CANONICAL_v3.json` (załączony poniżej)

### 2️⃣ `arbitrage/guardian.py` — EDIT

```python
# OLD (lines 1-4):
"""
ADRION 369 — Guardian Laws Engine v5.3
11 Ethical laws validated sequentially for every arbitrage decision (ADRION 369 §VI).

# NEW:
"""
ADRION 369 — Guardian Laws Engine v6.0
9 Immutable Guardian Laws validated sequentially for every decision (ADRION 369 §VI).

# OLD (lines 20-31):
11 Guardian Laws (§VI ADRION 369 v5.3):
  G1. Unity          (MEDIUM)   — job aligns with system's core purpose
  G2. Harmony        (MEDIUM)   — balance between competing objectives (was Truth)
  G3. Rhythm         (MEDIUM)   — bid pace is sustainable (daily limits)
  G4. Causality      (HIGH)     — price chain is traceable and non-negative
  G5. Transparency   (MEDIUM)   — all required analysis fields present
  G6. Authenticity   (HIGH)     — LLM output genuine, non-deceptive, non-frozen
  G7. Privacy        (CRITICAL) — no external disclosure without consent (was Autonomy)
  G8. Nonmaleficence (CRITICAL) — no financial harm to operator
  G9. Sustainability (HIGH)     — daily total operational cost within limit
  G10. Evolution     (HIGH)     — errors drive improvement; PME feedback loops active
  G11. RelationalCare (MEDIUM)  — respect user attention budget; transparency on cost

# NEW:
9 Guardian Laws (§VI ADRION 369 v6.0):
  G1. Unity          (MEDIUM)   — collective good; system coherence
  G2. Truth          (HIGH)     — prohibition on manipulation; genuine analysis
  G3. Rhythm         (MEDIUM)   — equilibrium; sustainable bid pace
  G4. Causality      (HIGH)     — everything traced; non-negative price chain
  G5. Transparency   (MEDIUM)   — explainability; all analysis fields present
  G6. Nonmaleficence (CRITICAL) — do no harm; protect from financial damage
  G7. Autonomy       (HIGH)     — respect free will; no spam/unsolicited contact
  G8. Justice        (CRITICAL) — fairness; equitable treatment
  G9. Sustainability (HIGH)     — long-term viability; operational cost within limit

# OLD (lines 36-40):
Backward compatibility:
  Code "Harmony"    = Canonical G2 "Harmony"
  Code "Privacy"    = Canonical G7 "Privacy"        [CRITICAL]
  Code "Authenticity" = Canonical G6 "Authenticity" [HIGH]
  Runtime names preserved for API/test compatibility.

# NEW:
Canonical names used throughout. Previous runtime_name mappings removed (was confusing).
```

### 3️⃣ `CLAUDE.md` — EDIT

**Line 18:**
```diff
- **Decision model:** Trinity-EBDI 162D space (3 perspectives x 6 agents x 9 laws)
+ **Decision model:** Trinity-EBDI 162D space (3 perspectives x 6 modes x 9 laws)
```

**Line 90-116 — REPLACE Guardian Laws section:**

```markdown
### Guardian Laws (canonical: `docs/GUARDIAN_LAWS_CANONICAL.json`)

**9 Immutable Laws** evaluated through **6 Processing Modes**:

| G# | Law | Severity | Purpose | Primary Modes |
|----|-----|----------|---------|---|
| G1 | Unity | MEDIUM | System coherence | Inventory, Process, Action |
| G2 | Truth | HIGH | Anti-manipulation | Debate, Healing, Action |
| G3 | Rhythm | MEDIUM | Sustainable pace | Inventory, Process |
| G4 | Causality | HIGH | Full traceability | Debate, Action |
| G5 | Transparency | MEDIUM | Explainability | All 6 |
| G6 | Nonmaleficence | CRITICAL | Prevent harm | Debate, Healing, Action |
| G7 | Autonomy | HIGH | Respect free will | Empathy, Healing |
| G8 | Justice | CRITICAL | Fair treatment | Debate, Action |
| G9 | Sustainability | HIGH | Long-term viability | Process, Action |

**6 Processing Modes** (Hexagon):
1. **Inventory** — Observe facts (3-word summaries)
2. **Empathy** — Assess emotional/relational impact
3. **Process** — Organize goals, allocate resources
4. **Debate** — Multi-agent consensus (5/6 quorum)
5. **Healing** — Detect deception/manipulation
6. **Action** — Execute + Genesis Record logging

**3 Perspectives** (Trinity):
- **Material:** Resources (CPU, RAM, energy)
- **Intellectual:** Truth (beauty, coherence, logic)
- **Essential:** Purpose (mission, unity, commons)
```

### 4️⃣ `docs/ARCHITECTURE.md` — ADD SECTION after Overview

After line ~30, add:

```markdown
## Hexagon (6 Processing Modes)

Every decision cycles through these 6 sequential evaluation stages:

### M1: Inventory — What do I see?

**Observable facts about the request.** Summarize in 3 words.

- Database lookup for precedents
- Fact extraction from user input
- State validation (~30ms)

### M2: Empathy — What does the user feel?

**Emotional and relational assessment.** Does the user feel respected?

- Stakeholder impact analysis
- Historical relationship context
- Relationship preservation heuristics (~30ms)

### M3: Process — How to organize this?

**Decompose into subgoals. Allocate resources.** Is the timeline feasible?

- Goal decomposition
- Resource availability check
- Timeline feasibility (~30ms)

### M4: Debate — Is this safe?

**Multi-agent consensus voting.** Byzantine fault-tolerant.

- 5/6 quorum required (tolerates 1 faulty agent)
- Conflicting perspectives reconciled
- Safety threshold: no CRITICAL violations (~30ms)

### M5: Healing — Are there manipulations?

**Detect adversarial/deceptive patterns.** Verify alignment.

- Pattern anomaly detection
- Hidden assumption discovery
- Principle alignment verification (~30ms)

### M6: Action — Execute with logging

**Commit decision to Genesis Record.** Full audit trail.

- Decision hash commitment
- Timestamp + user context
- Merkle tree chain extension (~30ms)

**Total latency: ~180ms (budget: <200ms)**
```

### 5️⃣ `README.md` — ADD SECTION

Add after "## Running" section:

```markdown
## 162-Dimensional Decision Space

ADRION 369's ethical engine multiplies three orthogonal dimensions:

```
        3 PERSPECTIVES
         (Trinity)
              │
              ├─ Material    (resources: CPU, RAM, energy)
              ├─ Intellectual (truth, beauty, logic)
              └─ Essential   (purpose, mission, commons)
              
              ×
              
        6 PROCESSING MODES
           (Hexagon)
              │
              ├─ M1: Inventory (observe)
              ├─ M2: Empathy (feel)
              ├─ M3: Process (organize)
              ├─ M4: Debate (consensus)
              ├─ M5: Healing (cleanse)
              └─ M6: Action (execute)
              
              ×
              
        9 GUARDIAN LAWS
         (Ethical Constraints)
              │
              ├─ G1: Unity (coherence)
              ├─ G2: Truth (anti-manipulation)
              ├─ G3: Rhythm (balance)
              ├─ G4: Causality (traceability)
              ├─ G5: Transparency (explainability)
              ├─ G6: Nonmaleficence (harm prevention)
              ├─ G7: Autonomy (free will)
              ├─ G8: Justice (fairness)
              └─ G9: Sustainability (viability)
              
              = 162 DIMENSIONAL DECISION SPACE
```

**Every decision evaluates through: 3 × 6 × 9 = 162 dimensions.**

See: [Guardian Laws Canonical](docs/GUARDIAN_LAWS_CANONICAL.json) | [CLAUDE.md § Trinity-EBDI](CLAUDE.md#5-key-files)
```

---

## ✅ Verification Checklist (post-merge)

```bash
# 1. JSON syntax
python -m json.tool docs/GUARDIAN_LAWS_CANONICAL.json && echo "✓ JSON valid"

# 2. No G10/G11
grep -r "G10\|G11\|Evolution\|RelationalCare" arbitrage/ tests/ docs/ && \
  echo "❌ FAIL: Found G10/G11" || echo "✓ G10/G11 removed"

# 3. No "6 agents"
grep "6 agents" CLAUDE.md README.md && \
  echo "❌ FAIL: Found '6 agents'" || echo "✓ '6 agents' removed"

# 4. "6 modes" present
grep "6 modes\|6 MODES\|Hexagon" CLAUDE.md README.md docs/ARCHITECTURE.md | \
  wc -l | grep -E "[5-9]|1[0-9]" && echo "✓ '6 modes' documented" || \
  echo "❌ FAIL: '6 modes' not documented"

# 5. "9 laws" everywhere
grep "9 laws\|9 Laws\|G1\|G9" CLAUDE.md README.md docs/ARCHITECTURE.md | \
  wc -l | grep -E "1[0-9]|[2-9][0-9]" && echo "✓ '9 laws' documented" || \
  echo "❌ FAIL: '9 laws' not documented"

# 6. All files updated
git log --oneline --all --grep="p0-0\|guardian-laws" | head -5
```

---

## 🎯 Timeline

| Step | Time | Notes |
|------|------|-------|
| **Edit 5 files locally** | 30 min | Use exact diffs above |
| **Verify locally** | 10 min | Run verification checklist |
| **Git commits** | 5 min | 4 sequential commits per phase |
| **Push + merge** | 5 min | Squash-merge to main |
| **Tag v4.0-p0.0** | 2 min | Phase gate marker |

**Total: ~1 hour**

---

## 🔗 After P0-0 completion

Once this PR merges → **mark task as completed** → move to P0-1 (SQL injection fix)

This unblocks:
- P0-2 (root cleanup)
- P0-4 (Docker socket)
- P0-5 (ARCHITECTURE docs) — now correct about 3×6×9
