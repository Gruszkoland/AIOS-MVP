# TIER 4: OBSERVABILITY & MONITORING GUIDE

## 📚 Contents (3 Repositories)

1. **Grafana** (⭐ 73.1k) — Visualization & dashboards
2. **VictoriaMetrics** (⭐ 16.7k) — Time-series database
3. **OpenObserve** (⭐ 18.5k) — Unified observability

---

## 🎯 ADRION 369 Integration Points

### Grafana Dashboard Architecture

```yaml
# dashboard-trinity-hexagon-guardians.yaml

dashboard:
  title: "ADRION 369 - Trinity/Hexagon/Guardians Metrics"

  panels:
    # ROW 1: Trinity Scores (3 gauges)
    - title: "Material Score"
      type: "gauge"
      targets:
        - expr: 'trinity_material_score{instance="adrion-api"}'
      thresholds: [0.3, 0.5, 0.9] # Red, Yellow, Green

    - title: "Intellectual Score"
      type: "gauge"
      targets:
        - expr: 'trinity_intellectual_score{instance="adrion-api"}'

    - title: "Essential Score"
      type: "gauge"
      targets:
        - expr: 'trinity_essential_score{instance="adrion-api"}'

    # ROW 2: Hexagon Latency (stacked bar)
    - title: "Hexagon Stage Latencies (ms)"
      type: "bargauge"
      targets:
        - expr: 'hexagon_stage_duration_ms{stage="inventory"}'
        - expr: 'hexagon_stage_duration_ms{stage="empathy"}'
        - expr: 'hexagon_stage_duration_ms{stage="process"}'
        - expr: 'hexagon_stage_duration_ms{stage="debate"}'
        - expr: 'hexagon_stage_duration_ms{stage="healing"}'
        - expr: 'hexagon_stage_duration_ms{stage="action"}'

    # ROW 3: Guardian Laws Compliance (heatmap/matrix)
    - title: "Guardian Laws Compliance"
      type: "heatmap"
      targets:
        - expr: 'guardian_law_passed{law=~"unity|truth|rhythm|causality|transparency|nonmaleficence|autonomy|justice|sustainability"}'
      dataFormat: "timeseries"

    # ROW 4: Vortex 174Hz Heartbeat
    - title: "Vortex Oscillation (174Hz Monitor)"
      type: "graph"
      targets:
        - expr: "vortex_oscillation_hz"
        - expr: "vortex_resonance_score"
        - expr: "vortex_health_status"

    # ROW 5: Decision Distribution
    - title: "Decision Outcomes (24h)"
      type: "piechart"
      targets:
        - expr: 'sum by(outcome) (decision_total{outcome!="pending"})'
      legendValues: ["value", "percent"]
```

### VictoriaMetrics Setup for High-Frequency Vortex

```yaml
# docker-compose.yml

services:
  victoriametrics:
    image: victoriametrics/victoria-metrics:latest
    ports:
      - "8428:8428"
    volumes:
      - vm_storage:/storage
    environment:
      # Optimize for 174Hz Vortex heartbeat
      - retention=90d # 90-day retention
      - search.latency=5s # Query latency SLA
    command:
      - "-storageDataPath=/storage"
      - "-retentionPeriod=8640h" # 90 days
      - "-maxQueueLen=1000000" # High cardinality support
      - "-logRequestsWithoutComponentInRoute"

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prom_storage:/prometheus
    command:
      - "--config.file=/etc/prometheus/prometheus.yml"
      - "--storage.tsdb.path=/prometheus"
      - "--remote_write=http://victoriametrics:8428/api/v1/write" # Push to VM

volumes:
  vm_storage:
  prom_storage:
```

### Grafana Dashboards via Terraform

```hcl
# grafana dashboards deployment

terraform {
  required_providers {
    grafana = {
      source = "grafana/grafana"
    }
  }
}

provider "grafana" {
  url  = "http://localhost:3000"
  auth = "Bearer ${var.grafana_api_key}"
}

# Trinity Scores Dashboard
resource "grafana_dashboard" "trinity_scores" {
  config_json = jsonencode({
    title   = "Trinity Scores (Real-time)"
    panels  = [
      # 3 Gauge panels for Material/Intellectual/Essential
      # Connected to Prometheus
    ]
  })
}

# Hexagon Latency Dashboard
resource "grafana_dashboard" "hexagon_latency" {
  config_json = jsonencode({
    title   = "Hexagon Stage Breakdown"
    panels  = [
      # 6-bar stacked bar chart
      # Stage: Inventory, Empathy, Process, Debate, Healing, Action
    ]
  })
}

# Guardian Laws Compliance
resource "grafana_dashboard" "guardian_compliance" {
  config_json = jsonencode({
    title   = "Guardian Laws Compliance Matrix"
    panels  = [
      # 9x time heatmap (9 laws over time)
    ]
  })
}
```

### OpenObserve for Unified Observability

```yaml
# docker-compose.yml with OpenObserve

services:
  openobserve:
    image: public.ecr.aws/zinclabs/openobserve:latest
    ports:
      - "5080:5080" # UI
    environment:
      ZO_ROOT_USER_EMAIL: "admin@adrion369.local"
      ZO_ROOT_USER_PASSWORD: "${OPENOBSERVE_PASSWORD}"
      ZO_INGESTION_ENABLED: "true"
      ZO_TRACE_ENABLED: "true"
      ZO_METRICS_ENABLED: "true"
    volumes:
      - zo_storage:/data

  # Application sends traces to OpenObserve
  # Python instrumentation:
  app:
    environment:
      - OTEL_EXPORTER_OTLP_ENDPOINT=http://openobserve:5080
      - OTEL_SERVICE_NAME=adrion-api
```

```python
# Python instrumentation for OpenObserve

from opentelemetry import trace, metrics
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Setup tracer
otlp_exporter = OTLPSpanExporter(insecure=True)
trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(otlp_exporter)
)
tracer = trace.get_tracer(__name__)

# Instrument decision pipeline
def evaluate_trinity_with_trace(job, analysis):
    with tracer.start_as_current_span("trinity_evaluation") as span:
        span.set_attribute("job.id", job.id)
        span.set_attribute("job.type", job.type)

        # Trace each perspective
        with tracer.start_as_current_span("material_scoring"):
            material = _score_material(job, analysis)

        with tracer.start_as_current_span("intellectual_scoring"):
            intellectual = _score_intellectual(job, analysis)

        with tracer.start_as_current_span("essential_scoring"):
            essential = _score_essential(job, analysis)

        return {
            "material": material,
            "intellectual": intellectual,
            "essential": essential,
        }
```

---

## 🚀 Quick Start (2-3 hours)

### Setup Monitoring Stack

```bash
cd repositories/tier4-monitoring

# 1. Start Grafana
docker run -d \
  --name grafana \
  -p 3000:3000 \
  -e GF_SECURITY_ADMIN_PASSWORD=admin \
  grafana/grafana

# 2. Start Prometheus (with Vortex scrape config)
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v ./prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus

# 3. Start VictoriaMetrics
docker run -d \
  --name victoriametrics \
  -p 8428:8428 \
  victoriametrics/victoria-metrics

# 4. Point Prometheus → VictoriaMetrics (external storage)
# Edit prometheus.yml:
# remote_write:
#   - url: http://victoriametrics:8428/api/v1/write

# 5. (Optional) Start OpenObserve
docker run -d \
  --name openobserve \
  -p 5080:5080 \
  public.ecr.aws/zinclabs/openobserve:latest
```

### Create Trinity Dashboard

```python
import requests

grafana_url = "http://localhost:3000"
api_key = "your_grafana_api_key"

dashboard_payload = {
    "dashboard": {
        "title": "ADRION 369 - Trinity Scores",
        "panels": [
            # Material Gauge
            {
                "title": "Material Score",
                "type": "gauge",
                "targets": [
                    {"expr": 'trinity_material_score{instance="adrion"}'}
                ],
                "fieldConfig": {
                    "defaults": {
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "red", "value": 0},
                                {"color": "yellow", "value": 0.5},
                                {"color": "green", "value": 0.7},
                            ]
                        }
                    }
                }
            },
            # Intellectual & Essential gauges...
        ],
    }
}

response = requests.post(
    f"{grafana_url}/api/dashboards/db",
    json=dashboard_payload,
    headers={"Authorization": f"Bearer {api_key}"},
)
print(f"Dashboard created: {response.json()['id']}")
```

### Export Metrics from ADRION

```python
# arbitrage/metrics.py

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, start_http_server
import time

registry = CollectorRegistry()

# Trinity metrics
trinity_material = Gauge('trinity_material_score', 'Material score', registry=registry)
trinity_intellectual = Gauge('trinity_intellectual_score', 'Intellectual score', registry=registry)
trinity_essential = Gauge('trinity_essential_score', 'Essential score', registry=registry)

# Hexagon metrics (per stage)
hexagon_latency = Histogram(
    'hexagon_stage_duration_ms',
    'Hexagon stage execution time',
    labelnames=['stage'],
    registry=registry
)

# Guardian metrics
guardian_violations = Counter(
    'guardian_law_violations',
    'Guardian law violation count',
    labelnames=['law'],
    registry=registry
)

# Vortex metrics
vortex_oscillation = Gauge('vortex_oscillation_hz', 'Vortex frequency', registry=registry)
vortex_resonance = Gauge('vortex_resonance_score', 'Vortex resonance', registry=registry)

# Export metrics endpoint
def export_trinity_metrics(trinity_scores):
    trinity_material.set(trinity_scores['material'])
    trinity_intellectual.set(trinity_scores['intellectual'])
    trinity_essential.set(trinity_scores['essential'])

# Start metrics server on port 8765
start_http_server(8765, registry=registry)
```

---

## 📋 Integration Checklist

- [ ] Grafana installed (port 3000)
- [ ] Prometheus configured with Vortex scrape job
- [ ] VictoriaMetrics running (port 8428)
- [ ] Trinity gauge dashboard created
- [ ] Hexagon latency dashboard created
- [ ] Guardian laws heatmap dashboard created
- [ ] Vortex 174Hz monitoring dashboard created
- [ ] Metrics exported from ADRION API (port 8765)
- [ ] Grafana alerts configured (e.g. material_score < 0.3)
- [ ] Logs aggregated (Prometheus JSONl logs or Loki)
- [ ] OpenObserve traces flowing (optional)

---

## 🔗 Key References

- **Grafana Docs:** https://grafana.com/docs/grafana/latest/
- **Prometheus Setup:** https://prometheus.io/docs/prometheus/latest/configuration/
- **VictoriaMetrics:** https://docs.victoriametrics.com/
- **OpenObserve:** https://docs.openobserve.ai/
- **Prometheus Python Client:** https://github.com/prometheus/client_python

---

## 🎯 Expected Outcomes

- ✅ Real-time Trinity score gauges (live dashboard)
- ✅ Hexagon latency breakdown (bottleneck identification)
- ✅ Guardian law compliance heatmap (9 laws over 24h)
- ✅ Vortex 174Hz heartbeat visualization
- ✅ Decision outcome distribution (APPROVED vs DENIED)
- ✅ Alerting: Trinity score drops below threshold
- ✅ Historical analysis: month-over-month trends

---

**Integration Time:** 2-3 hours
**Difficulty:** ⭐⭐ (Easy to Medium)
**Priority:** 🟡 IMPORTANT
