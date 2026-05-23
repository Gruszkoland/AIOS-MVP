# ADR-0001: Rust no_std for the kernel crate

**Status:** Accepted  
**Date:** 2026-05-23  
**Deciders:** Adrian Halicki

## Context

The AIOS kernel must be deployable on embedded targets (e.g., bare-metal ARM Cortex-M) without an OS or allocator. The language choice directly determines whether hard real-time guarantees are achievable.

## Decision

Use Rust with `#![no_std]` for the `kernel` crate.

## Consequences

- **Positive:** Deterministic execution, no heap allocation, provable stack bounds.
- **Positive:** `unsafe` is contained and auditable (mandatory 2-reviewer rule).
- **Negative:** Standard library types (Vec, String, HashMap) are unavailable; const-generic arrays are used instead.
- **Negative:** Rustup nightly may be needed for some embedded targets (currently using stable 1.75+).
