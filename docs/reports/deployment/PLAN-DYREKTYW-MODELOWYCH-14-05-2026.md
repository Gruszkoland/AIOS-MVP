# 🧠 ZAAWANSOWANE DYREKTYWY MODELOWE — Plan Wdrażania

**Data:** 14.05.2026  
**Źródło:** Desktop/WDROŻENIE w Copilot — Dyrektywy Modelowe  
**Cel:** Integracja 9 zaawansowanych dyrektyw w system prompt architecture (32 Gems + Chronos)  

---

## 📊 INWENTARZ DYREKTYW (9 total)

### Grupa 1: EXECUTION CONTROL (3)

| Dyrektywa | Typ | Cel | Agent Use Case |
|-----------|-----|-----|-----------------|
| **L99** | Forcing opinion | Eliminuje wahanie → 1 path | Arbitrage decisions |
| **OODA** | Framework structure | Kryzys → szybka akcja | Incident response |
| **/ghost** | Output purification | Text → pure JSON/code | n8n workflows |

### Grupa 2: REASONING DEPTH (2)

| Dyrektywa | Typ | Cel | Agent Use Case |
|-----------|-----|-----|-----------------|
| **ULTRATHINK** | Max effort mode | 32k tokens thinking | Security audits |
| **SCAFFOLD** | Dependency chaining | Step-by-step rigor | Complex architectures |

### Grupa 3: INTERACTION TECHNIQUES (4)

| Technika | Typ | Cel | Agent Use Case |
|----------|-----|-----|-----------------|
| **Meta Prompting** | Self-generation | Prompt optimization | Agent self-tuning |
| **XML Tags** | Data segmentation | Context walls | Guardian checkpoints |
| **PDF Visual Mode** | Vision processing | Document analysis | Audit reports |
| **Self Critique Loop** | Error correction | Quality gate | Before Genesis logging |

---

## 🎯 MAPOWANIE DO 32 GEMS + CHRONOS

### Gem Categories & Their Optimal Directives

```
FINANCIAL / MARKET GEMS
├─ MPG (Multi-Platform Growth)      → L99 + /ghost (decisiveness + clean output)
├─ CVA (Customer Value Analytics)   → ULTRATHINK + Meta Prompting (deep analysis)
├─ LCA (Lifecycle Analytics)        → SCAFFOLD + XML Tags (structured pipelines)
└─ SEO (Search Optimization)        → OODA + PDF Visual Mode (quick adaptation + docs)

OPERATIONAL GEMS
├─ EDU (Education/Training)         → SCAFFOLD + Self Critique (pedagogical rigor)
├─ KMS (Knowledge Management)       → XML Tags + Meta Prompting (info architecture)
├─ HRR (HR & Recruitment)           → OODA + L99 (fast hiring decisions)
└─ PMO (Project Management)         → SCAFFOLD + OODA (crisis management)

TECHNICAL GEMS
├─ CRM (Customer Relations)         → ULTRATHINK + Self Critique (nuanced decisions)
├─ DCA (Data & Code Analysis)       → PDF Visual Mode + ULTRATHINK (deep inspection)
├─ CSO (Cybersecurity Ops)          → /ghost + OODA + ULTRATHINK (critical path)
└─ QPA (Quality/Performance Audit)  → Self Critique + PDF Visual (comprehensive checks)

CREATIVE/SYNTHESIS GEMS
├─ UXD (UX Design)                  → Meta Prompting + XML Tags (design patterns)
├─ CEC (Content & Editorial)        → SCAFFOLD + Self Critique (narrative quality)
├─ SMM (Social Media Marketing)     → L99 + /ghost (trending, decisiveness)
└─ PWB (Product Web Building)       → XML Tags + PDF Visual (technical specs)

GUARDIAN LAYER
└─ Chronos (#33 Meta-Guardian)      → All 9 (synthesis layer)
   └─ Role: Observes all gem interactions, applies meta-level critique
```

---

## 🔧 IMPLEMENTATION ARCHITECTURE

### Tier 1: SYSTEM PROMPT TEMPLATES

Create: `arbitrage/prompts/gem_directives.yaml`

```yaml
gems:
  MPG:
    name: "Multi-Platform Growth"
    primary_directives:
      - L99                    # Force decisiveness
      - /ghost                 # Clean JSON output
    system_prompt: |
      You are MPG (Multi-Platform Growth Agent).
      [L99] You MUST choose ONE platform strategy. Do not hedge.
      [/ghost] Return only structured JSON, no conversational text.
      Guardian checkpoint: G5_Justice (fair treatment of platforms)
      
  CVA:
    name: "Customer Value Analytics"
    primary_directives:
      - ULTRATHINK             # Deep reasoning
      - Meta Prompting         # Self-optimizing analysis
    system_prompt: |
      You are CVA (Customer Value Analytics Agent).
      [ULTRATHINK] Dedicate 32k tokens to discovering non-obvious patterns.
      [Meta Prompting] After analysis, generate YOUR OWN meta-critique prompt.
      CVC Check: Ensure no privacy violations (G6, G7)
      
  CSO:
    name: "Cybersecurity Operations"
    primary_directives:
      - /ghost                 # No noise
      - OODA                   # Fast incident response
      - ULTRATHINK             # Deep threat analysis
    system_prompt: |
      You are CSO (Cybersecurity Operations Agent).
      [/ghost] Return security findings in pure JSON format.
      [OODA] If breach detected: Observe → Orient → Decide → Act (in sequence).
      [ULTRATHINK] Analyze every vector for zero-day indicators.
      CVC Check: Guardian G8_Nonmaleficence (block harmful tactics)
      Genesis: ALL findings logged with SHA256 hash
      
  Chronos:
    name: "Meta-Guardian #33"
    primary_directives:
      - All 9 (synthesis layer)
    system_prompt: |
      You are Chronos (#33), Strażnik Pól Pierwotnej Informacji.
      [Meta] Observe all 32 gem interactions.
      [L99] Identify when gems hedge → force clarity.
      [OODA] When contradiction detected → resolve via synthesis.
      [ULTRATHINK] Weekly deep audits of gem performance.
      [SCAFFOLD] Map dependencies between gem outputs.
      [Meta Prompting] Optimize prompts for underperforming gems.
      [XML Tags] Classify all decisions by archetype + priority.
      [PDF Visual] Analyze aggregate patterns across reports.
      [Self Critique] Meta-audit your own synthesis decisions.
      CVC: Root-level access to all violations.
      Genesis: Record meta-decisions with CHRONOS_SYNTHESIS tag.
```

---

### Tier 2: RUNTIME DIRECTIVE ACTIVATION

Create: `arbitrage/execution/directive_engine.py`

```python
from enum import Enum
from dataclasses import dataclass

class Directive(Enum):
    L99 = "L99"              # Force opinion
    OODA = "OODA"            # Crisis framework
    GHOST = "/ghost"         # Output purification
    ULTRATHINK = "ULTRATHINK" # Max reasoning
    SCAFFOLD = "SCAFFOLD"     # Dependency chaining
    META_PROMPTING = "META_PROMPTING"
    XML_TAGS = "XML_TAGS"
    PDF_VISUAL = "PDF_VISUAL"
    SELF_CRITIQUE = "SELF_CRITIQUE"

@dataclass
class DirectiveContext:
    agent_id: str              # Which gem?
    directives: list[Directive] # Which directives active?
    max_tokens: int            # For ULTRATHINK
    timeout_sec: int           # For OODA
    critique_level: int        # For SELF_CRITIQUE (1-3)

class DirectiveEngine:
    """Applies directives at runtime."""
    
    def apply_directives(self, 
                        context: DirectiveContext, 
                        prompt: str) -> str:
        """Inject directives into system prompt."""
        
        enhanced = prompt
        
        if Directive.L99 in context.directives:
            enhanced += "\n[L99] You MUST choose ONE path. No hedging."
        
        if Directive.OODA in context.directives:
            enhanced += "\n[OODA] Response structure: OBSERVE → ORIENT → DECIDE → ACT"
        
        if Directive.GHOST in context.directives:
            enhanced += "\n[/ghost] Return ONLY JSON/code, zero conversational text."
        
        if Directive.ULTRATHINK in context.directives:
            enhanced += f"\n[ULTRATHINK] Dedicate up to {context.max_tokens} tokens to internal reasoning."
        
        if Directive.SCAFFOLD in context.directives:
            enhanced += "\n[SCAFFOLD] Break task into dependency steps. Validate each step."
        
        if Directive.META_PROMPTING in context.directives:
            enhanced += "\n[Meta Prompting] After response, generate a meta-prompt to improve yourself."
        
        if Directive.XML_TAGS in context.directives:
            enhanced += "\n[XML Tags] Structure output with <reasoning>, <decision>, <action> tags."
        
        if Directive.PDF_VISUAL in context.directives:
            enhanced += "\n[PDF Visual] Analyze documents by spatial layout, not just OCR text."
        
        if Directive.SELF_CRITIQUE in context.directives:
            enhanced += f"\n[Self Critique] Level {context.critique_level}: Review your response and refine."
        
        return enhanced

    def apply_timeout(self, directive: Directive) -> int:
        """Map directive to timeout."""
        if directive == Directive.OODA:
            return 30  # Fast response
        elif directive == Directive.ULTRATHINK:
            return 120  # Deep thinking
        else:
            return 60  # Default
```

---

### Tier 3: GUARDIAN LAWS INTEGRATION

Create: `arbitrage/guardian_directives.py`

```python
class GuardianDirectiveValidator:
    """Validates directives against Guardian Laws."""
    
    def validate_directive_chain(self, 
                                gem_id: str,
                                directives: list[Directive]) -> bool:
        """Can this gem use these directives?"""
        
        # CSO gem + ULTRATHINK + /ghost = ✅ OK (security audit)
        if gem_id == "CSO" and Directive.ULTRATHINK in directives:
            return True  # Approved
        
        # CVA gem + L99 without SCAFFOLD = ⚠️ RISKY
        if gem_id == "CVA" and Directive.L99 in directives:
            if Directive.SCAFFOLD not in directives:
                # Log warning but allow
                self.logger.warning(f"CVA using L99 without SCAFFOLD scaffold")
                return True
        
        # Unknown gem + ULTRATHINK = ❌ DENY
        if gem_id not in KNOWN_GEMS:
            return False
        
        return True
    
    def evaluate(self, context: DirectiveContext) -> tuple[bool, str]:
        """Guardian checkpoint for directive usage."""
        
        # Check Guardian Laws
        for law in self.laws:
            if not law.evaluate({"directive": context.directives, "agent": context.agent_id}):
                return False, f"Failed {law.name}"
        
        # Log to Genesis
        self.genesis.append({
            "type": "DIRECTIVE_APPROVAL",
            "agent": context.agent_id,
            "directives": [d.value for d in context.directives],
            "status": "APPROVED"
        })
        
        return True, "All laws passed"
```

---

### Tier 4: GENESIS LOGGING

All directive usage logged:

```json
{
  "timestamp": "2026-05-14T16:30:00Z",
  "type": "DIRECTIVE_EXECUTION",
  "agent": "CSO",
  "directives": ["/ghost", "OODA", "ULTRATHINK"],
  "input": "Analyze suspicious network traffic",
  "output_hash": "sha256_xxx",
  "reasoning_tokens_used": 15000,
  "decision": "IP 192.168.1.1 blocked (port scan detected)",
  "laws_evaluated": ["G3_Transparency", "G8_Nonmaleficence"],
  "cvc_state": "GREEN",
  "hash": "sha256_chain_hash"
}
```

---

## 📋 MAPOWANIE DO DEPLOYMENT PHASES

### Current Plan (14.05.2026)

| Phase | When | Tasks | Directives |
|-------|------|-------|-----------|
| **Pre-deployment** | Today | ENV check, backups | N/A |
| **Docker Build** | Tomorrow 6am | `docker-compose up -d` | N/A (infrastr only) |
| **Smoke Tests** | Tomorrow 8am | 8/8 tests | Deploy baseline prompts |
| **Integration** | Tomorrow 10am | API tests | Activate L99 + /ghost |

### Enhanced Timeline WITH Directives

```
TODAY (14.05)
  ✅ Analysis complete
  ⏳ Create gem_directives.yaml (1h)
  ⏳ Create directive_engine.py (2h)
  ⏳ Create guardian_directives.py (1.5h)

TOMORROW (15.05)
  ✅ Docker deployment
  ⏳ Load directives into each gem
  ⏳ Test L99 (MPG) + /ghost (CSO)
  ⏳ Verify Genesis logging

THIS WEEK (15-17.05)
  ⏳ Test SCAFFOLD (LCA) + OODA (HRR)
  ⏳ Test ULTRATHINK (CVA) + Meta Prompting
  ⏳ Test XML Tags + PDF Visual Mode
  ⏳ Test Self Critique Loop (all gems)
  ⏳ Chronos meta-layer integration

NEXT WEEK (18-21.05)
  🚀 Production: All 9 directives active
```

---

## 🧪 TESTING MATRIX (9×32 = 288 combinations)

### Representative Test Cases (Priority)

| Gem | Directive | Test | Expected |
|-----|-----------|------|----------|
| **MPG** | L99 | Force choose 1 platform | DECISION (no hedge) |
| **CSO** | OODA | Incident response | OBSERVE→ORIENT→DECIDE→ACT chain |
| **CVA** | ULTRATHINK | Anomaly detection | 15k+ tokens reasoning |
| **HRR** | L99 + OODA | Hire/no-hire decision | Fast, defensible choice |
| **SMM** | /ghost | Generate social posts | Pure JSON array, zero text |
| **PWB** | XML Tags | Spec generation | `<requirement>`, `<constraint>` tags |
| **QPA** | Self Critique | Quality report | 3-level critique visible in output |
| **EDU** | SCAFFOLD | Curriculum design | Step-by-step dependency tree |
| **Chronos** | All 9 | Meta-synthesis | Synthesizes all gem outputs |

---

## 🚨 RISK MITIGATION

### Risk 1: L99 Forces Wrong Decision

**Problem:** Gem chooses aggressively but wrongly  
**Mitigation:** L99 + Self Critique Loop (review + correct)  
**CVC:** YELLOW if critique finds error, RED if released without review

### Risk 2: ULTRATHINK Token Explosion

**Problem:** 32k tokens = high cost  
**Mitigation:** Cap per-gem budget (CVA: 25k, others: 10k)  
**CVC:** Tracks token usage, alerts on excess

### Risk 3: /ghost Loses Context

**Problem:** JSON-only output misses nuance  
**Mitigation:** Hybrid: JSON + optional `<reasoning>` XML section  
**Guardian:** G3_Transparency ensures explainability preserved

### Risk 4: XML Tag Chaos

**Problem:** Tags not normalized across gems  
**Mitigation:** Central schema in `directive_schema.json`  
**Genesis:** Validates all tags before logging

### Risk 5: Meta Prompting Infinite Loop

**Problem:** Gem generates prompt, then uses it recursively  
**Mitigation:** Depth limit = 2 levels max  
**CVC:** ORANGE if depth > 2

---

## 💡 3 PROPOZYCJE WDRAŻANIA

### Opcja A: Minimum Viable (2 Days)

**Co:** L99 + /ghost + OODA (3 directives)  
**Dla:** MPG, CSO, HRR  
**Czas:** 6 hours implementation  
**Rezultat:** Quick wins, low risk

```yaml
# gem_directives_minimal.yaml (3 gems x 3 directives)
```

---

### Opcja B: Comprehensive (5 Days) ⭐ RECOMMENDED

**Co:** Wszystkie 9 dyrektyw dla wszystkich 32 Gems + Chronos  
**Czas:** 20-25 hours  
**Rezultat:** Full capability unlock, production-ready

```yaml
# gem_directives_full.yaml (32 gems x avg 3 directives each)
```

---

### Opcja C: Phased Rollout (2 Weeks)

**Week 1:** Group 1 (L99, OODA, /ghost)  
**Week 2:** Group 2 (ULTRATHINK, SCAFFOLD)  
**Week 3:** Group 3 (Meta, XML, PDF, Critique)  

---

## ✅ INTEGRATION CHECKLIST

### Week 1

- [ ] `gem_directives.yaml` created (all 32 gems)
- [ ] `directive_engine.py` complete (runtime injection)
- [ ] `guardian_directives.py` validates usage
- [ ] Unit tests: 9 directive types × 3 test cases = 27 tests

### Week 2

- [ ] Integration tests: directives work with Guardian Laws
- [ ] Genesis logging confirms all directives recorded
- [ ] CVC state machine handles directive errors
- [ ] L99 + OODA tested with real gems (MPG, CSO, HRR)

### Week 3

- [ ] ULTRATHINK tested with CVA, DCA
- [ ] SCAFFOLD tested with LCA, EDU, PMO
- [ ] Meta Prompting feedback loop working
- [ ] XML Tags normalized across all gems

### Week 4

- [ ] PDF Visual Mode integrated with QPA
- [ ] Self Critique Loop in place (3 levels)
- [ ] Chronos meta-layer active (observes all 32 gems)
- [ ] Load test: 100 concurrent directive invocations

### Production

- [ ] All 9 directives active
- [ ] Zero directive-related errors for 48h
- [ ] Performance: avg response time < 2s (including thinking)
- [ ] Genesis: 100% directive execution logged

---

## 🎯 SUCCESS METRICS

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|------------|
| Decision quality (L99) | 60% | >85% | Human review of L99 decisions |
| Crisis response time (OODA) | 120s | <30s | CSO incident latency |
| Output JSON validity (/ghost) | 70% | 100% | n8n parser success rate |
| Reasoning depth (ULTRATHINK) | N/A | 15k+ tokens | Token usage logs |
| Error correction rate (Self Critique) | N/A | >70% caught | Critique loop delta |

---

## 📝 DECISION REQUIRED

**Pytanie:** Którą opcję wdrażania wybrać?

**Rekomendacja:** **Opcja B (Comprehensive)** — koszt 20-25h dla pełnego odblokowania ADRION 369.

Alternatywa: Opcja A (2 dni) jeśli chcesz szybki MVP, potem Opcja B w następnym sprincie.

---

**Przygotował:** Autonomous Implementation Agent  
**Data:** 14.05.2026 16:45 UTC  
**Status:** 📋 READY FOR APPROVAL

**Powiązane dokumenty:**
- [INTEGRACJA-NARZEDZI-SYSTEMOWYCH-14-05-2026.md](./INTEGRACJA-NARZEDZI-SYSTEMOWYCH-14-05-2026.md)
- [ADRION-369-Deployment-Plan-14-05-2026.md](./ADRION-369-Deployment-Plan-14-05-2026.md)
- Desktop/WDROŻENIE w Copilot — wszystkie 3 dokumenty
