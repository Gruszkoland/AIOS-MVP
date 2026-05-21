# Copilot Local Payload v3 (Compatible)

## Cel
Rozszerzony standard payloadu agentow dla lokalnej pracy w VS Code.

## Zasada kompatybilnosci
Pola legacy sa wymagane. Pola v3 sa opcjonalne i nie lamia starszych flow.

## Legacy (required)
- agent_id
- status
- compressed_output
- key_findings
- recommended_next_agent
- required_context_for_next
- anomalies
- maturity_score

## v3 (optional)
- trace_id: string (format: TASK_UUID.AGENT.TIMESTAMP_MS)
- confidence_level: integer 0-100
- confidence_gaps: string[] (aktywne, gdy confidence < 70)
- processing_meta:
  - input_tokens: number
  - output_tokens: number
  - processing_time_ms: number

## Reguly operacyjne
- confidence_level < 70 => uzupelnij confidence_gaps.
- Brak trace_id jest tolerowany, ale rekomendowany.
- processing_meta powinno byc wypelniane dla flow > 1 krok.
