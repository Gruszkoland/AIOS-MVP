# TIER 8: JAEGER DISTRIBUTED TRACING

## 📚 Overview

**Goals:**

- End-to-end request tracing (Trinity → Hexagon → Guardians)
- Bottleneck identification
- Cross-service visibility
- Duration breakdown per component

**Repositories needed:**

- https://github.com/jaegertracing/jaeger (⭐ 21k)
- OpenTelemetry Python SDK

---

## 🎯 ADRION 369 Integration Points

### Current State (No tracing)

```python
# Can't see:
# - Where do requests spend time?
# - Which Trinity perspective is slow?
# - Guardian Law evaluation bottleneck?
# - Service communication delays?
```

### NEW State (Full tracing via Jaeger)

```
Request comes in (t=0)
│
├─ Trinity Evaluation (t=0-150ms)
│  ├─ Material scoring: 40ms
│  ├─ Intellectual scoring (RAG): 80ms
│  └─ Essential scoring: 30ms
│
├─ Hexagon Pipeline (t=150-380ms)
│  ├─ Inventory: 35ms
│  ├─ Empathy: 45ms
│  ├─ Process: 55ms
│  ├─ Debate: 60ms
│  ├─ Healing: 50ms
│  └─ Action: 40ms
│
└─ Guardian Validation (t=380-420ms)
   └─ Evaluate 9 laws (parallel): 40ms

Response sent: TOTAL 420ms
```

---

## 🔧 Implementation

### 1. Setup Jaeger (Docker)

```yaml
# docker-compose.yml - Jaeger

services:
  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "5775:5775/udp" # Zipkin compact thrift
      - "6831:6831/udp" # Jaeger compact thrift
      - "16686:16686" # UI port
    environment:
      - COLLECTOR_ZIPKIN_HOST_PORT=:9411
```

Access UI: http://localhost:16686

---

### 2. Instrument ADRION with OpenTelemetry

```python
# arbitrage/tracing.py - NEW

from opentelemetry import trace, metrics
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

def init_tracing():
    """Initialize Jaeger tracing for ADRION"""

    # Setup Jaeger exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name="localhost",
        agent_port=6831,
    )

    # Setup tracer provider
    trace.set_tracer_provider(TracerProvider())
    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(jaeger_exporter)
    )

    # Auto-instrument libraries
    FastAPIInstrumentor().instrument()
    SQLAlchemyInstrumentor().instrument()
    RedisInstrumentor().instrument()
    RequestsInstrumentor().instrument()

    print("✓ Jaeger tracing initialized")

# Usage in app startup
from fastapi import FastAPI

app = FastAPI()

@app.on_event("startup")
async def startup():
    init_tracing()
```

---

### 3. Manual Instrumentation (Trinity → Hexagon → Guardians)

```python
# arbitrage/trinity.py - WITH TRACING

from opentelemetry import trace

tracer = trace.get_tracer(__name__)

def evaluate_trinity(job, analysis):
    """Trinity evaluation with tracing"""

    with tracer.start_as_current_span("trinity_evaluation") as span:
        # Add attributes for filtering in Jaeger UI
        span.set_attribute("job.id", job.id)
        span.set_attribute("job.type", job.type)
        span.set_attribute("job.priority", job.priority)

        # Material perspective
        with tracer.start_as_current_span("trinity.material") as material_span:
            material_span.set_attribute("component", "material")
            material_score = _score_material(job, analysis)
            material_span.set_attribute("score", material_score)

        # Intellectual perspective
        with tracer.start_as_current_span("trinity.intellectual") as intellectual_span:
            intellectual_span.set_attribute("component", "intellectual")
            intellectual_score = _score_intellectual(job, analysis)
            intellectual_span.set_attribute("score", intellectual_score)

        # Essential perspective
        with tracer.start_as_current_span("trinity.essential") as essential_span:
            essential_span.set_attribute("component", "essential")
            essential_score = _score_essential(job, analysis)
            essential_span.set_attribute("score", essential_score)

        overall = (material_score * intellectual_score * essential_score) ** (1/3)
        span.set_attribute("overall_score", overall)

        return {
            "material": material_score,
            "intellectual": intellectual_score,
            "essential": essential_score,
            "overall": overall,
        }

# arbitrage/hexagon.py - WITH TRACING

def process_hexagon(trinity_scores):
    """Hexagon pipeline with tracing"""

    with tracer.start_as_current_span("hexagon_pipeline") as pipeline_span:
        pipeline_span.set_attribute("stage_count", 6)

        # Stage 1: Inventory
        with tracer.start_as_current_span("hexagon.inventory") as stage_span:
            stage_span.set_attribute("stage", "inventory")
            stage_span.set_attribute("order", 1)
            inventory = inventory_stage_impl(trinity_scores)
            stage_span.set_attribute("result_size", len(str(inventory)))

        # Stage 2: Empathy
        with tracer.start_as_current_span("hexagon.empathy") as stage_span:
            stage_span.set_attribute("stage", "empathy")
            stage_span.set_attribute("order", 2)
            empathy = empathy_stage_impl(inventory)

        # ... stages 3-6 ...

        pipeline_span.set_attribute("total_stages", 6)
        return results

# arbitrage/guardian.py - WITH TRACING

def evaluate_guardians(decision_context):
    """Guardian Laws validation with tracing"""

    with tracer.start_as_current_span("guardian_evaluation") as guardian_span:
        guardian_span.set_attribute("law_count", 9)

        results = {}
        violations = 0

        for law_name, law_rule in GUARDIAN_LAWS.items():
            with tracer.start_as_current_span(f"guardian.{law_name}") as law_span:
                law_span.set_attribute("law", law_name)

                result = law_rule.evaluate(decision_context)
                results[law_name] = result

                law_span.set_attribute("passed", result["passed"])
                law_span.set_attribute("score", result["score"])

                if not result["passed"]:
                    violations += 1

        guardian_span.set_attribute("violations", violations)
        guardian_span.set_attribute("status", "DENY" if violations >= 2 else "APPROVE")

        return {"evaluations": results, "violations": violations}
```

---

### 4. RAG Service Tracing

```python
# arbitrage/rag_integration.py - WITH TRACING

from ragflow import RAGFlow

def evaluate_intellectual_with_rag(job_context):
    """Intellectual scoring with RAG tracing"""

    with tracer.start_as_current_span("intellectual.rag") as rag_span:
        rag_span.set_attribute("component", "intellectual")

        # RAG retrieval
        with tracer.start_as_current_span("rag.retrieve") as retrieve_span:
            retrieve_span.set_attribute("query", job_context.get("type"))
            context_docs = rag.retrieve(
                query=f"Guardian Laws relevant to {job_context['type']}",
                top_k=5
            )
            retrieve_span.set_attribute("docs_retrieved", len(context_docs))

        # LLM reasoning
        with tracer.start_as_current_span("rag.reason") as reason_span:
            reason_span.set_attribute("context_size", sum(len(d) for d in context_docs))
            reasoning = rag.reason(
                query=job_context,
                context=context_docs,
                prompt="Evaluate logical correctness..."
            )
            reason_span.set_attribute("score", reasoning["score"])

        return reasoning["score"]
```

---

### 5. Database Access Tracing

```python
# Auto-instrumented via SQLAlchemyInstrumentor()
# Every DB query shows:
# - duration
# - query string
# - rows affected
# - errors if any

# Redis calls auto-instrumented via RedisInstrumentor()
# - Command
# - Key patterns
# - Duration
```

---

## 📊 Example Trace View (in Jaeger UI)

```
┌─ adri on-api POST /api/process [total: 435ms] ✓
│
├─ trinity_evaluation [150ms]
│  ├─ trinity.material [45ms]
│  │  └─ psutil.cpu_percent [2ms]
│  ├─ trinity.intellectual [80ms]
│  │  ├─ rag.retrieve [35ms]
│  │  │  └─ elasticsearch query [30ms]
│  │  └─ rag.reason [45ms]
│  │     └─ ollama inference [40ms]
│  └─ trinity.essential [25ms]
│
├─ hexagon_pipeline [220ms]
│  ├─ hexagon.inventory [35ms]
│  ├─ hexagon.empathy [45ms]
│  ├─ hexagon.process [50ms]
│  ├─ hexagon.debate [55ms]
│  ├─ hexagon.healing [20ms]
│  └─ hexagon.action [15ms]
│
├─ guardian_evaluation [55ms]
│  ├─ guardian.unity [8ms]
│  ├─ guardian.truth [7ms]
│  ├─ guardian.nonmaleficence [12ms]
│  └─ guardian.autonomy [28ms]  ← SLOW LAW!
│
└─ response serialization [10ms]

BOTTLENECK DETECTED: autonomy evaluation is 28ms (28% of guardian time)
RECOMMENDATION: Optimize autonomy law evaluation
```

---

## 🎯 Query Examples (in Jaeger UI)

### Find slow Trinity evaluations

```
service:adrion-api
operation:trinity_evaluation
duration >= 150ms
```

### Find failed Guardian evaluations

```
service:adrion-api
operation:guardian_evaluation
status=error
```

### Find jobs by priority

```
service:adrion-api
attribute:job.priority >= 8
```

---

## 📋 Implementation Checklist

- [ ] Install: `pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-jaeger`
- [ ] Start Jaeger: `docker-compose up jaeger`
- [ ] Create `arbitrage/tracing.py` with init
- [ ] Add tracing init to `arbitrage/api.py` startup
- [ ] Add manual spans to Trinity/Hexagon/Guardians
- [ ] Add manual spans to RAG integration
- [ ] Test: Submit request, check http://localhost:16686
- [ ] Configure alert: If trinity > 200ms, investigate
- [ ] Export: Traces to long-term storage (optional)

---

## 🚀 Advanced Features

### Custom Metrics

```python
from opentelemetry.sdk.metrics import MeterProvider

meter = metrics.get_meter(__name__)
trinity_duration = meter.create_histogram(
    "trinity_duration_ms",
    description="Trinity evaluation duration"
)
trinity_duration.record(duration_ms, attributes={"job_type": job.type})
```

### Trace Sampling (for high-volume)

```python
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

sampler = TraceIdRatioBased(0.1)  # Sample 10% of traces
trace.set_tracer_provider(TracerProvider(sampler=sampler))
```

### Integration with Prometheus

```python
# Export both metrics and traces to Prometheus + Jaeger
```

---

**Time to implement:** 1-2 days
**Benefits:** Complete visibility + bottleneck identification + debugging
