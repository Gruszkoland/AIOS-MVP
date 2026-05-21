# Global Anti-Patterns Map (Local)

## Technical
- Hardcoded secrets
- Non-parameterized SQL
- Destructive ops without dry-run

## Orchestration
- Handoff bez required_context_for_next
- Brak walidacji statusu po kroku
- Brak trace_id w flow wielokrokowym

## Quality
- Brak kryteriow DoD
- Brak testu smoke po zmianie krytycznej
- Nieoznaczone zalozenia i szacunki

## Rule
Kazdy agent powinien sprawdzic te antywzorce przed statusem SUCCESS.
