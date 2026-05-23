# Contributing to AIOS MVP

Thank you for your interest in contributing to AIOS MVP! We welcome contributions from developers, researchers, designers, and enthusiasts.

## Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors. Please read and abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

---

## Quick Start

### Prerequisites

- **Rust 1.70+** (stable)
- **Python 3.11+** (for documentation and scripts)
- **Git**
- **Docker** (optional, for containerized development)

### Local Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Gruszkoland/AIOS-MVP.git
   cd AIOS-MVP
   ```

2. **Install Rust:**
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   rustup toolchain install 1.70
   ```

3. **Build the project:**
   ```bash
   cargo build --all
   ```

4. **Run tests:**
   ```bash
   cargo test --all
   ```

5. **Check code quality:**
   ```bash
   cargo clippy --all -- -D warnings
   cargo fmt --check
   ```

### Development Workflow

```bash
# Create a feature branch
git checkout -b feature/my-feature

# Make changes
cargo build
cargo test
cargo clippy -- -D warnings

# Format code
cargo fmt --all

# Commit with descriptive message
git commit -m "feat: Add deterministic topology validation"

# Push to your fork
git push origin feature/my-feature

# Open PR on GitHub
```

---

## Branch Naming

- `feature/...` — New features
- `fix/...` — Bug fixes
- `docs/...` — Documentation
- `refactor/...` — Code refactoring
- `perf/...` — Performance improvements
- `test/...` — Tests and test infrastructure
- `chore/...` — Build, CI/CD, dependencies
- `security/...` — Security fixes

---

## Pull Request Process

### Creating a PR

1. **Create a branch** using the naming convention above:
   ```bash
   git checkout -b feature/xxx
   # or
   git checkout -b fix/xxx
   ```

2. **Label your PR** with all applicable labels before requesting review:

   | Label | When to apply |
   |-------|---------------|
   | `unsafe` | PR introduces or modifies any `unsafe` block |
   | `kernel` | Changes touch the `kernel` crate or low-level scheduling |
   | `agents` | Changes touch agent runtime, personas, or EBDI state |
   | `ipc` | Changes touch inter-process/inter-service communication |
   | `docs` | Documentation-only changes |

3. **CI must pass.** All gates listed in the [Continuous Integration Gates](#continuous-integration-gates) section below must be green. PRs with failing CI will not be reviewed.

4. **Reviews required:**
   - Normal PR: 1 maintainer approval
   - PR with `unsafe` label: 2 approvals required (at least one reviewer must have a security focus)
   - PR affecting G7 (Privacy) or G8 (Nonmaleficence): explicit security review required (see [SECURITY.md](SECURITY.md))

### Before Submitting

- [ ] Code follows project style guide (`cargo fmt` + `cargo clippy -- -D warnings`)
- [ ] All tests pass: `cargo test --all`
- [ ] Test coverage maintained (>=80%)
- [ ] Documentation updated (public APIs have rustdoc, architectural changes have RFC or doc comment)
- [ ] Commit messages are clear and descriptive (imperative, under 72 chars)
- [ ] No hardcoded secrets or credentials
- [ ] Every `unsafe` block has a `// SAFETY:` comment explaining invariants
- [ ] Guardian Laws compliance verified (see below)

### Definition of Done

- Build passes
- All tests green
- Docs updated
- Acceptance criteria met
- No performance regression (benchmarks within 5% of baseline)
- Guardian Laws compliance verified

---

## Continuous Integration Gates

All PRs must pass the following checks before merge. These run automatically on every push and PR via GitHub Actions.

```bash
# 1. Formatting — zero tolerance for unformatted code
cargo fmt --check

# 2. Linting — all warnings treated as errors
cargo clippy --all -- -D warnings

# 3. Unit and integration tests — full suite must be green
cargo test --all

# 4. Smoke benchmarks — must not regress more than 5% vs. baseline
cargo bench --all -- --sample-size 10
```

CI pipeline definition: `.github/workflows/` (see `rust-ci.yml` and `security-ci.yml`).

If any gate fails, the PR is blocked. Do not ask maintainers to override failing CI — fix the issue first.

---

## Testing Locally

Run the full CI suite locally before pushing. This avoids wasting CI minutes and speeds up review.

```bash
# Run full CI locally (mirrors the pipeline exactly)
cargo fmt --check
cargo clippy --all -- -D warnings
cargo test --all --verbose
cargo bench --all -- --sample-size 10

# Run tests for a specific package/module only
cargo test --package kernel --lib
cargo test --package agents --lib
cargo test --package ipc --lib

# Run doc tests
cargo test --all --doc

# Check coverage (requires cargo-tarpaulin)
cargo install cargo-tarpaulin
cargo tarpaulin --all --out Html --exclude-files tests/
# Open tarpaulin-report.html to verify >=80% coverage

# Fuzzing — nightly toolchain required
cargo +nightly fuzz run fuzz_kernel_parse
cargo +nightly fuzz run fuzz_ipc_message

# Run a single test by name
cargo test --all test_guardian_law_g7_blocks_unauthorized_access -- --nocapture
```

Target coverage: **>=80%** across all crates. The CI pipeline enforces this gate.

---

## Unsafe Code Review

The `unsafe` keyword bypasses Rust's memory safety guarantees. Every use must be justified, reviewed, and documented.

### Rules

- Every `unsafe` block **requires 2 maintainer approvals** before merge. At least one approver must have a security background.
- The PR must carry the `unsafe` label. CI will reject PRs that add `unsafe` blocks without this label.
- Every `unsafe` block **must** include a `// SAFETY:` comment directly above it that:
  - States the invariants that make the block safe
  - Explains why safe alternatives are insufficient
  - Identifies any conditions that would make the block unsound

- Benchmarks or tests must validate the assumptions stated in the `SAFETY` comment where measurable.

### Example of a compliant unsafe block

```rust
// SAFETY: `ptr` is guaranteed non-null and aligned to `T` by the caller contract
// enforced in `KernelAllocator::alloc`. The lifetime is bounded by `'arena`
// which outlives all references derived from this pointer.
let val = unsafe { &*ptr };
```

### What is NOT acceptable

```rust
// bad: no SAFETY comment
unsafe { *ptr = 42; }

// bad: vague SAFETY comment
// SAFETY: should be fine
unsafe { *ptr = 42; }
```

If you are unsure whether `unsafe` is needed, open a discussion issue first. The goal is zero unnecessary `unsafe` blocks.

---

## Documentation Requirements

### Public APIs

Every public function, struct, enum, and trait must have a rustdoc comment:

```rust
/// Evaluates all 9 Guardian Laws against the proposed decision.
///
/// Returns `GuardianVerdict::Deny` immediately on any CRITICAL violation (G7, G8).
/// Returns `GuardianVerdict::Deny` if two or more violations of any severity occur.
///
/// # Arguments
///
/// * `job` - The decision job descriptor
/// * `analysis` - Pre-computed analysis context
/// * `context` - Runtime execution context
///
/// # Errors
///
/// Returns `GuardianError::MissingContext` if required fields are absent.
pub fn evaluate_guardians(
    job: &Job,
    analysis: &Analysis,
    context: &Context,
) -> Result<GuardianVerdict, GuardianError> {
    // ...
}
```

Rustdoc is enforced by `cargo doc --no-deps --document-private-items 2>&1 | grep "warning"` — the CI pipeline treats rustdoc warnings as errors.

### Major Decisions

Every significant design decision must be captured in one of:

- A `// NOTE:` or `// DECISION:` comment in the source code at the relevant site
- A dedicated file in `docs/decisions/` following the ADR (Architecture Decision Record) format

Use the `docs/decisions/` directory for anything that would otherwise be lost in PR discussion threads.

### RFC for Architectural Changes

Any change that:
- Alters service boundaries or inter-service contracts
- Introduces a new crate or removes an existing one
- Changes the Guardian Laws evaluation pipeline
- Modifies the Trinity Score (Material/Intellectual/Essential) calculation
- Affects the 162D decision space topology

...requires an RFC document in `docs/rfc/` before implementation begins. Open a PR with the RFC document only, collect feedback, then implement in a separate PR that references the merged RFC.

RFC template: `docs/rfc/TEMPLATE.md`

---

## Coding Standards

### Rust Code Style

- Use `cargo fmt` for formatting (enforced, non-negotiable)
- Use `cargo clippy -- -D warnings` for linting — fix all warnings, no exceptions
- Document all public APIs with rustdoc (see [Documentation Requirements](#documentation-requirements))
- Prefer explicit error handling (`Result`, `Option`) over panics
- Use `no_std` in the `kernel` crate — no heap allocations
- Parameterized SQL only — no string interpolation in database queries
- Rate limit every POST endpoint via `is_allowed(client_ip)` or provide a documented exemption

### Python Code Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use `ruff check` for linting
- Use `mypy --strict` for type checking
- Add type hints to all functions (return type and parameters)
- No hardcoded secrets — use `os.getenv()` or `arbitrage.config.settings.*`

### Commit Message Format

```
<type>: <subject>

<body>

<footer>
```

**Types:** feat, fix, docs, style, refactor, perf, test, chore, security

Subject line: imperative mood, under 72 characters, no period at end.

**Example:**

```
feat: Add 162D topology validation in kernel

Implements deterministic geometry check to prevent unsafe
decision space traversal. Adds 2 ms latency to decision path.

Fixes #42
Guardian Laws: G7, G8 compliance verified
```

---

## Guardian Laws Compliance

All contributions must comply with the 9 Guardian Laws. The canonical definition lives in `docs/GUARDIAN_LAWS_CANONICAL.json` — do not use any other source.

| Law | Severity | Veto | Requirement |
|-----|----------|------|-------------|
| **G1: Unity** | MEDIUM | No | Code maintains system coherence |
| **G2: Harmony** | HIGH | No | Components work together smoothly |
| **G3: Rhythm** | MEDIUM | No | Timing and cadence are predictable |
| **G4: Causality** | HIGH | No | Cause-effect relationships are clear |
| **G5: Transparency** | MEDIUM | No | Decisions and logic are explainable |
| **G6: Authenticity** | HIGH | No | No deception or misdirection |
| **G7: Privacy** | CRITICAL | YES | No unauthorized data access or exposure |
| **G8: Nonmaleficence** | CRITICAL | YES | No harm to users or systems |
| **G9: Sustainability** | HIGH | No | Long-term viability considered |

**Evaluation rules:**
- A single CRITICAL violation (G7 or G8) results in automatic DENY — no exceptions
- Two or more violations of any severity result in DENY
- PRs that affect G7 or G8 require explicit security review in addition to normal approvals

---

## Getting Help

- **Questions?** Open a [GitHub Discussion](https://github.com/Gruszkoland/AIOS-MVP/discussions)
- **Found a bug?** [Open an issue](https://github.com/Gruszkoland/AIOS-MVP/issues)
- **Security concern?** See [SECURITY.md](SECURITY.md) — do not open a public issue
- **Feature request?** Use [GitHub Discussions > Ideas](https://github.com/Gruszkoland/AIOS-MVP/discussions/categories/ideas)
- **Unsafe block review?** Tag `@security-reviewers` in your PR description

---

## License

By contributing to AIOS MVP, you agree that your contributions will be licensed under the MIT License (see [LICENSE](LICENSE)).

---

## Unsafe code review checklist

Any PR that introduces or modifies an `unsafe` block **must** receive two approvals and satisfy all items below before merge.

### Required items (all must be checked)

- [ ] Every `unsafe` block has a `// SAFETY:` comment explaining which invariant is maintained and why it is upheld at this call site.
- [ ] The invariant cannot be violated by any safe caller — if it can, the API must be `unsafe fn` itself.
- [ ] A test exists that would panic or produce incorrect output if the invariant were violated (even a debug-mode assertion is sufficient).
- [ ] `miri` has been run on the affected code: `cargo miri test -p <crate>` passes without errors.
- [ ] No uninitialized memory is read (use `MaybeUninit` explicitly if needed).
- [ ] No data races are introduced (document why in the `SAFETY` comment if shared state is involved).
- [ ] Pointer arithmetic is bounds-checked or proven safe by construction.

### How to run miri locally

```bash
rustup toolchain install nightly
rustup component add miri --toolchain nightly
cargo +nightly miri test -p aios-kernel
cargo +nightly miri test -p aios-ipc
```

### PR label

Add the `unsafe-review` label to any PR touching `unsafe` blocks. This auto-requests reviews from the `@Gruszkoland/kernel-reviewers` team.

