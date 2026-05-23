# ADR-0002: SPSC ring buffer for IPC

**Status:** Accepted  
**Date:** 2026-05-23  
**Deciders:** Adrian Halicki

## Context

Inter-component communication must not block the kernel's hard real-time path. Options considered: async channels (tokio), shared memory with mutexes, lock-free SPSC ring buffer.

## Decision

Use a single-producer / single-consumer (SPSC) ring buffer (`aios-ipc::RingBuffer`) with const-generic capacity.

## Consequences

- **Positive:** Zero allocation, no lock contention, sub-microsecond latency target.
- **Positive:** Works in `no_std` contexts.
- **Negative:** Strictly SPSC — for MPSC scenarios a separate wrapper with a spinlock is needed.
- **Negative:** Capacity must be a power of two (checked at push time).
