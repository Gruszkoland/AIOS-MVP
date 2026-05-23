# ADR-0003: LLM agents are advisory only — never on critical path

**Status:** Accepted  
**Date:** 2026-05-23  
**Deciders:** Adrian Halicki

## Context

LLM inference latency is non-deterministic (10ms–10s). Placing any LLM call on the kernel's hard real-time execution path would violate timing guarantees.

## Decision

All LLM-backed agents operate in the advisory plane with `AgentCriticality::Advisory` or `::SoftRealtime`. The kernel never awaits an LLM response on a critical path; Guardian verdicts are computed from pre-scored `DecisionVector` data only.

## Consequences

- **Positive:** Hard real-time guarantees are preserved.
- **Positive:** System degrades gracefully if LLM inference is unavailable.
- **Negative:** Advisory agents cannot react in real time to novel situations — they update the DecisionVector asynchronously.
