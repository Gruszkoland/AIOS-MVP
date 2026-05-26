# AI OS — Cognitive Kernel + Zero-Copy Agents

> **For:** Systems engineers building deterministic AI-advised infrastructure
> **Why:** Hard real-time kernel + LLM agents as safety layer, not decision layer

**Key characteristics:**
- Rust `no_std` kernel (deterministic, provable)
- Ring-buffer IPC (sub-μs latency)
- LLM agents as advisory plane only
- TUI kiosk mode, MVP-first
- Safety verified by design (capability model, fuzzing in DoD)

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
| `kernel` | ~370 | Deterministic no_std core — 162D topology, consensus |
| `agents` | ~140 | Guardian trait + 9 specialist implementations |
| `ipc` | ~330 | Zero-copy ring-buffer inter-process communication |
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


## Documentation

| Document | Description |
|----------|-------------|
| [QUICKSTART.md](QUICKSTART.md) | Get from zero to `cargo test` in 15 minutes |
| [docs/AGENT_SWARM.md](docs/AGENT_SWARM.md) | Swarm topology, tier definitions, conflict protocol |
| [docs/GUARDIAN_MAP.md](docs/GUARDIAN_MAP.md) | Canonical 9 Guardian Laws, persona mapping, naming history |
| [docs/GUARDIAN_LAWS_CANONICAL.json](docs/GUARDIAN_LAWS_CANONICAL.json) | Machine-readable canonical laws (v3.1) |
| [docs/adr/](docs/adr/) | Architecture Decision Records |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution guide + unsafe review checklist |

## Status — v0.2.0-alpha

Sprint 1 complete: kernel 162D topology, IPC ring buffer, and Guardian trait are implemented with full test coverage.
Current focus: Sprint 2 — benchmarking IPC latency, fuzzing the consensus engine, and end-to-end PoC integration.


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
