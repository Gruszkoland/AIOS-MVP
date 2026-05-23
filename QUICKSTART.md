# AIOS-MVP — Quickstart (Rust path)

This guide gets you from zero to a passing `cargo test --workspace` in under 15 minutes.

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Rust stable | >= 1.75 | `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh` |
| Git | any | system package manager |

No C compiler, Python, or Docker is needed to build and test the Rust workspace.

## Clone and build

```bash
git clone https://github.com/Gruszkoland/AIOS-MVP.git
cd AIOS-MVP
cargo build --workspace
cargo test --workspace
```

Expected output:

```
test result: ok. 12 passed; 0 failed  (aios-kernel)
test result: ok. 11 passed; 0 failed  (aios-ipc)
test result: ok. 6 passed; 0 failed   (aios-agents)
```

## Crate overview

### `kernel` -- 162D decision topology

```rust
use aios_kernel::{DecisionVector, Guardian, compute_consensus, ConsensusVerdict};

let mut v = DecisionVector::uniform(200);
v.set_guardian_scores(Guardian::Sentinel, [30; 6]);

match compute_consensus(&v) {
    ConsensusVerdict::VetoDeny     => println!("Sentinel vetoed"),
    ConsensusVerdict::Approve      => println!("Approved"),
    ConsensusVerdict::DeferToHuman => println!("Human review needed"),
    ConsensusVerdict::Deny         => println!("Denied"),
}
```

### `ipc` -- zero-copy ring buffer

```rust
use aios_ipc::RingBuffer;
let mut bus: RingBuffer<16, 64> = RingBuffer::new();
bus.push(b"payload").unwrap();
let mut out = [0u8; 64];
let n = bus.pop(&mut out).unwrap();
```

### `agents` -- Guardian trait

Implement `CognitiveAgent` for any guardian:
- `name()` -- static identifier
- `criticality()` -- Advisory / SoftRealtime / HardRealtimeForbidden
- `observe()` -- receive a `StandardObservation`
- `decide()` -- emit an `AdvisoryDecision`

## PoC orchestrator

```bash
cd poc/scheduler-mgr
cargo run --release
# HTTP at http://localhost:8000
```

## Linting

```bash
cargo fmt --all
cargo clippy --workspace -- -D warnings
```

## Unsafe code policy

Every `unsafe` block requires:
1. A `// SAFETY:` comment explaining the invariant.
2. Two reviewer approvals on the PR.
3. A test that panics if the invariant is violated.

See CONTRIBUTING.md for the full checklist.
