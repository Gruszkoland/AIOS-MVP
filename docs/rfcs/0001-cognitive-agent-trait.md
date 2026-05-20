# RFC-0001: CognitiveAgent Trait

## Status
Draft

## Cel
Zdefiniować minimalny kontrakt dla agentów AI w AIOS.

## Założenia
- Agent **nigdy** nie blokuje ścieżki krytycznej kernela.
- Agent działa jako advisory plane.
- Decyzje agenta mogą być odrzucone przez warstwę deterministyczną.
- Scheduler kernela jest deterministyczny (CFS/RR); AI dostarcza tylko `sched_params` asynchronicznie co ~100ms.

## Trait (Rust)
Patrz `agents/src/lib.rs`.

## Security considerations
- sandboxing agentów (Wasmtime lub capabilities)
- capability boundaries
- brak bezpośredniej mutacji scheduler queue przez LLM
- każda decyzja logowana przez Auditor

## Evolution
- LoRA hot-swap (po weryfikacji spike technicznego)
- feedback loops (Healer → Architect)
- audyt decyzji (Auditor agent)
