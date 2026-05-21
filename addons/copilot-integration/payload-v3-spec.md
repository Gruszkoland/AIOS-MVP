# Payload v3 Spec (Add-on)

Legacy required fields + optional v3 telemetry fields.

## Required
- agent_id
- status
- compressed_output
- key_findings
- recommended_next_agent
- required_context_for_next
- anomalies
- maturity_score

## Optional v3
- trace_id
- confidence_level
- confidence_gaps
- processing_meta

## Compatibility
Spec is backward-compatible by design.
