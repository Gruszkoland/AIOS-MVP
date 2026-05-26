# Changelog — AIOS-MVP

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [0.2.0] — 2026-05-26

### Added
- **kernel** — Full 162D decision topology (`DecisionVector`, `GuardianLaw`, `TrinityPerspective`, `HexagonStage`)
- **kernel** — `compute_consensus()` with weighted scoring and hard veto logic (G7/G8)
- **ipc** — SPSC `RingBuffer<N, S>` const-generic ring buffer with `MessageHeader`/`MessageKind`
- **agents** — `CognitiveAgent` trait with `SwarmTier` hierarchy
- **agents** — `ArchetypHarmonii` (meta, swarm anchor with `harmony_score()`)
- **agents** — `GlosKrytyka` (adversarial, Socratic protocol — always `Defer`)
- **agents** — `RelationalCareAgent` (systemic, `EmpathicShortcut` on high arousal)
- **agents** — `EvolutionAgent` (systemic, PME heuristics counter)
- **agents** — `SentinelAgent` (operational, veto on overload)
- **integration-tests** — 6 cross-crate pipeline tests (kernel → IPC → agent)
- **benchmarks** — Criterion benchmark files for IPC throughput and agent latency
- `QUICKSTART.md` — Rust onboarding guide
- `docs/AGENT_SWARM.md` — Swarm topology specification
- `docs/GUARDIAN_MAP.md` — Canonical Guardian Law → persona map (v2)
- `docs/adr/` — 4 Architecture Decision Records
- `deny.toml` — cargo-deny supply chain policy
- GitHub Release `v0.2.0-alpha`

### Fixed
- `poc/end-to-end-flow` — wrong crate import names corrected (`agents::` → `aios_agents::`)
- `GUARDIAN_LAWS_CANONICAL.json` v3.1 — runtime_names G2/G6/G7/G8 corrected
- G10/G11 reclassified as agent personas (not Guardian Laws)
- VERSION file synced to 0.2.0
- All GitHub Actions updated to latest versions (v4 artifacts, v5 setup-python)
- All crate versions synced to 0.2.0

### Security
- Purged `arbitrage.db`, `.gitconfig`, `db/adrion_local.db`, `uap/backend/db/adrion_local.db`
- Purged Stripe backup code, Google OAuth2 keys, Gemini/Drive/Gmail API credentials
- Full git history rewrite via `git filter-repo` — credentials no longer accessible in any commit
- Added `deny.toml` with license and advisory checks

### Architecture
- ADRION 369 is the immutable moral matrix (G1–G9 laws only)
- Agent swarm is the mutable execution layer (34+ personas, grows freely)
- Two-layer model documented in `docs/GUARDIAN_MAP.md` and `docs/AGENT_SWARM.md`

---

## [0.1.0] — 2026-04-08 (initial commit)

### Added
- Initial Rust workspace structure: `kernel`, `ipc`, `agents`, `poc/`
- Placeholder implementations for all three core crates
- Python MCP server stubs in `mcp_servers/`
- Docker Compose configurations for local development
- GitHub Actions CI skeleton
