# Copilot Local Observability Trace Protocol

## Cel
Spójne sledzenie wieloagentowych przeplywow i diagnoza bottleneckow.

## Minimalny standard
- Ten sam trace_id przenoszony przez wszystkie handoffy.
- Kazdy etap loguje: agent_id, timestamp, input_size, output_size, processing_time_ms.

## KPI
- routing_accuracy
- handoff_stability
- error_rate
- p95_latency

## Alerty
- Brak trace_id w 2+ kolejnych handoffach.
- confidence_level < 70 bez confidence_gaps.
- p95_latency powyzej zdefiniowanego progu.
