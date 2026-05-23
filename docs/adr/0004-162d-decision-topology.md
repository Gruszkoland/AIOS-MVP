# ADR-0004: 162-dimensional decision topology

**Status:** Accepted  
**Date:** 2026-05-23  
**Deciders:** Adrian Halicki

## Context

ADRION 369 defines a moral framework with 3 Principles, 6 Interpretation Modes, and 9 Guardians. A compact representation of all interactions is needed for consensus computation.

## Decision

Represent the decision space as a 162-dimensional u8 vector:
- `[0..54]`   — Principle x mode weights (3 x 18)
- `[54..108]` — Mode x guardian weights (6 x 9)
- `[108..162]`— Guardian x mode scores (9 x 6)

## Consequences

- **Positive:** Fixed size (162 bytes), stack-allocated, cache-friendly.
- **Positive:** Consensus can be computed in O(162) without any dynamic memory.
- **Negative:** Quantised to u8 — precision limited to 1/255 steps; sufficient for current Guardian scoring.
