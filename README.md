# AI OS — Cognitive Kernel + Zero-Copy Agents

> **For:** Systems engineers building deterministic AI-advised infrastructure
> **Why:** Hard real-time kernel + LLM agents as safety layer, not decision layer

**Key characteristics:**
- Rust `no_std` kernel (deterministic, provable)
- Ring-buffer IPC (sub-μs latency)
- LLM agents as advisory plane only
- TUI kiosk mode, MVP-first
- Safety verified by design (capability model, fuzzing in DoD)

**Repository note:** This repository currently hosts both Rust kernel work and Python/Flask ADRION orchestration services. Operational governance sources are `MANIFEST.md`, `CLAUDE.md`, and `.github/copilot-instructions.md`.

---

## Repository layout

```
AIOS-MVP/
├── kernel/           — deterministic no_std core (162D decision topology)
├── agents/           — LLM agent traits and Guardian implementations
├── ipc/              — zero-copy ring-buffer IPC primitives
├── poc/              — proof-of-concept examples (user-space scheduler)
├── docs/             — RFC documents, architecture decisions, technical specs
├── scripts/          — build helpers and dev tooling
├── .github/          — CI/CD workflows
└── .devcontainer/    — VS Code dev container configuration
```

---

## 162-Dimensional Decision Space

ADRION 369's ethical engine multiplies three orthogonal dimensions for comprehensive decision analysis:

### 3 Perspectives (Trinity)
- **Material:** Do we have resources? (CPU, RAM, energy)
- **Intellectual:** Does this make sense? (truth, beauty, logic)
- **Essential:** Does this serve purpose? (mission, unity, commons)

### 6 Processing Modes (Hexagon)
Sequential evaluation stages, each ~30ms:
1. **Inventory** — What do I see? (observe facts)
2. **Empathy** — What does user feel? (assess emotions)
3. **Process** — How to organize? (allocate resources)
4. **Debate** — Is this safe? (multi-agent consensus)
5. **Healing** — Are manipulations present? (detect deception)
6. **Action** — Execute with logging (Genesis Record commit)

### 9 Guardian Laws (Ethical Constraints)
- **G1: Unity** (MEDIUM) — Collective good, system coherence
- **G2: Harmony** (HIGH) — Balance between competing objectives, genuine analysis
- **G3: Rhythm** (MEDIUM) — Balance, sustainable pace
- **G4: Causality** (HIGH) — Everything traced, full traceability
- **G5: Transparency** (MEDIUM) — Explainability, auditable decisions
- **G6: Authenticity** (HIGH) — Outputs must be genuine and free from deception
- **G7: Privacy** (CRITICAL) — Local-first data protection
- **G8: Nonmaleficence** (CRITICAL) — Do no harm, prevent damage
- **G9: Sustainability** (HIGH) — Long-term viability, resource limits

### Total: 3 × 6 × 9 = **162 Dimensions**

Every decision vector evaluates through all 162 dimensions. CRITICAL law violations trigger instant DENY. Any 2+ violations = DENY.

**Latency budget:** 6 modes × ~30ms = ~180ms (< 200ms hard limit)

See: [Guardian Laws Canonical](docs/GUARDIAN_LAWS_CANONICAL.json) | [ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## Getting started

```bash
git clone https://github.com/Gruszkoland/AIOS-MVP.git
cd AIOS-MVP

# Build all workspace crates
cargo build --all

# Run tests
cargo test --all

# Run the PoC scheduler orchestrator
cd poc/scheduler-mgr && cargo run --release
# Listening on http://localhost:8000
```

Further reading:
- [Architecture overview](docs/ARCHITECTURE.md) — system design, 162D decision space, data flows
- [Contributing guide](CONTRIBUTING.md) — Rust style guide, PR process, unsafe review rules

---

## Workspace crates

| Crate | Lines (approx.) | Purpose |
|-------|-----------------|---------|
| `kernel` | ~500 | Deterministic no_std core — 162D topology, consensus |
| `agents` | ~300 | Guardian trait + 9 specialist implementations |
| `ipc` | ~200 | Zero-copy ring-buffer inter-process communication |
| `poc/scheduler-mgr` | ~100 | User-space PoC orchestrator |

---

## Architectural principles

- **AI advisory only** — no LLM call sits on the hard real-time execution path; the kernel never waits for a model response
- **Shared memory / ring buffer** — zero-copy IPC replaces RPC on every critical path
- **MVP-first** — TUI kiosk mode ships before any GUI requirement is added
- **Safety by design** — capability model enforced at the kernel boundary; mandatory 2-reviewer rule for every `unsafe` block; benchmarks and fuzzing are part of the Definition of Done

---

## Definition of Done

A ticket is closed when it:

- passes `cargo build --all` and `cargo test --all`
- has up-to-date documentation in `docs/`
- has been reviewed (2 reviewers mandatory for any `unsafe` block)
- introduces no benchmark regressions
- satisfies the acceptance criteria stated in the issue

---

## Current focus — Sprint 1

1. Monorepo setup and directory structure
2. Developer tooling configuration (rustfmt, clippy, pre-commit)
3. RFC #1: `CognitiveAgent` trait definition
4. CI/CD GitHub Actions (build + test + security scan)
5. Spike: model size and runtime feasibility on target hardware
6. PoC: scheduler manager in user-space (`poc/scheduler-mgr`)
7. GO/NO-GO criteria definition

---

## License

MPL-2.0
