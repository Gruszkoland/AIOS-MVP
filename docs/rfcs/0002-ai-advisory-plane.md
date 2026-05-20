# RFC-0002: AI Advisory Plane

## Status
Draft

## Problem
LLM w ścieżce krytycznej schedulera = deadlock. 100ms latency = katastrofa interaktywności.

## Rozwiązanie
- Scheduler kernela działa deterministycznie przez cały czas.
- Architect agent co ~100ms proponuje nowe `sched_params` (nice, weight, quota) przez shared memory.
- Kernel atomowo odczytuje i aplikuje parametry — **nigdy nie czeka** na LLM.
- Auditor weryfikuje decyzję asynchronicznie w tle.

## Diagram
```
[LLM / Architect] ──async──> [shared memory sched_params]
                                      |
                              [kernel scheduler] <── deterministyczny
```

## References
- ADR-0001: MVP-first
- RFC-0001: CognitiveAgent Trait
