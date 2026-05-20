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
   cargo clippy --all
   cargo fmt --all -- --check
   ```

### Development Workflow

```bash
# Create a feature branch
git checkout -b feature/my-feature

# Make changes
cargo build
cargo test
cargo clippy

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

- `feat/...` — New features
- `fix/...` — Bug fixes
- `docs/...` — Documentation
- `refactor/...` — Code refactoring
- `perf/...` — Performance improvements
- `test/...` — Tests and test infrastructure
- `chore/...` — Build, CI/CD, dependencies
- `security/...` — Security fixes

---

## Pull Request Process

### Before Submitting

- [ ] Code follows project style guide (run `cargo fmt` + `cargo clippy`)
- [ ] All tests pass: `cargo test --all`
- [ ] Test coverage maintained (≥80%)
- [ ] Documentation updated
- [ ] Commit messages are clear and descriptive (imperative, under 72 chars)
- [ ] No hardcoded secrets or credentials
- [ ] No `unsafe` blocks without doc comments
- [ ] Guardian Laws compliance verified

### Review Requirements

- **Normal PR:** 1 maintainer approval
- **`unsafe` code:** 2 maintainer approvals required
- **Security fixes:** Security review required (see SECURITY.md)

### Definition of Done (Definition of Done)

✅ Build passes  
✅ All tests green  
✅ Docs updated  
✅ AC (Acceptance Criteria) met  
✅ No performance regression  
✅ Guardian Laws compliance verified

---

## Coding Standards

### Rust Code Style

- Use `cargo fmt` for formatting
- Use `cargo clippy` for linting (fix all warnings)
- Add type hints to all public functions
- Document public APIs with rustdoc comments
- Prefer explicit error handling over panics
- Use `no_std` in kernel crate (no allocations)

### Python Code Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use `ruff check` for linting
- Use `mypy --strict` for type checking
- Add type hints to all functions
- No hardcoded secrets

### Commit Message Format

```
<type>: <subject>

<body>

<footer>
```

**Types:** feat, fix, docs, style, refactor, perf, test, chore, security

**Example:**
```
feat: Add 162D topology validation in kernel

Implements deterministic geometry check to prevent unsafe
decision space traversal. Adds 2 ms latency to decision path.

Fixes #42
Guardian Laws: G7, G8 compliance verified
```

---

## Testing Requirements

### Unit Tests

```bash
cargo test --all
cargo test --all --doc  # Doc tests
```

### Coverage

```bash
cargo install cargo-tarpaulin
cargo tarpaulin --all --out Html --exclude-files tests/
# Open tarpaulin-report.html in browser
```

Target: **≥80% coverage**

---

## Guardian Laws Compliance

**All contributions must comply with the 9 Guardian Laws:**

| Law | Requirement |
|-----|-------------|
| **G1: Unity** | Code maintains system coherence |
| **G2: Harmony** | Components work together smoothly |
| **G3: Rhythm** | Timing and cadence are predictable |
| **G4: Causality** | Cause-effect relationships are clear |
| **G5: Transparency** | Decisions and logic are explainable |
| **G6: Authenticity** | No deception or misdirection |
| **G7: Privacy** ⚠️ CRITICAL | No unauthorized data access/exposure |
| **G8: Nonmaleficence** ⚠️ CRITICAL | No harm to users or systems |
| **G9: Sustainability** | Long-term viability considered |

**If your PR affects G7 or G8, it requires explicit security review.**

---

## Getting Help

- **Questions?** Open a [GitHub Discussion](https://github.com/Gruszkoland/AIOS-MVP/discussions)
- **Found a bug?** [Open an issue](https://github.com/Gruszkoland/AIOS-MVP/issues)
- **Security concern?** See [SECURITY.md](SECURITY.md)
- **Feature request?** Use [GitHub Discussions > Ideas](https://github.com/Gruszkoland/AIOS-MVP/discussions/categories/ideas)

---

## License

By contributing to AIOS MVP, you agree that your contributions will be licensed under the MIT License (see [LICENSE](LICENSE)).

---

**Thank you for contributing to AIOS MVP!** 🚀
