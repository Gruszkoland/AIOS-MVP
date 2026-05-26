# AIOS-MVP — Roadmap

> **Vision:** A deterministic AI OS where hard real-time guarantees and
> cognitive intelligence coexist — ADRION 369 as the immutable moral floor,
> an evolving agent swarm as the adaptive intelligence layer.

---

## Released — v0.2.0-alpha (May 2026)

- [x] `aios-kernel`: 162D decision topology, `compute_consensus()`, veto logic
- [x] `aios-ipc`: SPSC zero-copy ring buffer, `MessageHeader`, `MessageKind`
- [x] `aios-agents`: `CognitiveAgent` trait, `SwarmTier` hierarchy
- [x] Swarm: `ArchetypHarmonii`, `GlosKrytyka`, `RelationalCare`, `Evolution`, `Sentinel`
- [x] 48 Rust tests (unit + integration cross-crate)
- [x] Benchmark files (Criterion) for IPC throughput and agent latency
- [x] CI: rustfmt + clippy + build + coverage(80%) + miri + cargo-deny + cargo doc
- [x] GUARDIAN_LAWS_CANONICAL.json v3.1 — 9 laws, immutable
- [x] Full security audit: OAuth2, Stripe, SQLite purged from git history

---

## Sprint 2 — Target: v0.3.0 (Q3 2026)

### Rust kernel
- [ ] Criterion benchmark baseline — measure and record actual IPC latency
- [ ] Prove sub-1µs push+pop on Linux x86_64 (or document actual number)
- [ ] `cargo +nightly miri test` — clean pass confirmed in CI
- [ ] Property-based tests with `proptest` for `DecisionVector` edge cases
- [ ] `no_std` validation on `thumbv7em-none-eabihf` target (ARM Cortex-M)

### Agent swarm
- [ ] `poc/end-to-end-flow` — full working binary connecting kernel → IPC → agents
- [ ] `ArchetypHarmonii` real HTTP endpoint: `GET /harmony` → `{score, drift, conflicts}`
- [ ] `GlosKrytyka` integration with Python guardian.py (bidirectional critique)
- [ ] `Evolution` reading from Genesis Record and writing to `memories/heuristics.json`
- [ ] Swarm health dashboard (Grafana panel pulling from `GET /harmony`)

### ADRION 369 matrix
- [ ] Python `guardian.py` — verify all 9 laws have individual tests
- [ ] `_law_authenticity()` — confirm independent implementation (not G8 alias)
- [ ] Guardian Laws compliance check in Python CI (`pytest -m guardian_laws`)

---

## Sprint 3 — Target: v0.4.0 (Q4 2026)

- [ ] MPSC ring buffer variant (multi-producer for future multi-agent scenarios)
- [ ] Formal verification sketch for consensus algorithm (TLA+ or Lean)
- [ ] `cargo fuzz` targets for `compute_consensus()` and `RingBuffer::push`
- [ ] Embedded target: compile `aios-kernel` for `thumbv7em-none-eabihf`
- [ ] Publish `aios-kernel` and `aios-ipc` to crates.io
- [ ] Publish `adrion-architecture` Python package to PyPI

---

## Long-term (v1.0.0)

- [ ] Hardware-in-the-loop: ADRION 369 matrix running on real ARM Cortex-M
- [ ] Formal proof: Guardian Law veto is unreachable for any APPROVE verdict
- [ ] ADRION 369 published as open standard (RFC-style document)
- [ ] Agent swarm with 34 fully implemented personas
- [ ] B2B-WHOLESALE-BRIDGE 2026 integration fully operational

---

## Won't do (explicit non-goals)

- ADRION 369 core laws will never exceed 9 (math is D^162 = 3×6×9, immutable)
- No heap allocation in `aios-kernel` or `aios-ipc` (`no_std` by design)
- No LLM inference on hard real-time kernel path (advisory-only by ADR-0003)
