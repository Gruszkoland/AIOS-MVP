# Monitoring Setup — ADRION 369 v1.0

## Architektura monitoringu

```
Application (Backend)
    ↓
Prometheus (metrics collection)
    ↓
Grafana (visualization)
    ↓
Alert Manager (notifications)
```

## Prometheus Configuration

### Instalacja Prometheus

#### Windows (Manual Installation)

1. Pobierz z: https://prometheus.io/download/
2. Rozpakuj do: `C:\Program Files\prometheus`
3. Utwórz `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
        - targets: []

rule_files:
  - "alerts.yml"

scrape_configs:
  - job_name: 'adrion-backend'
    static_configs:
      - targets: ['localhost:8002']
    metrics_path: '/metrics'

  - job_name: 'adrion-postgres'
    static_configs:
      - targets: ['localhost:9187']  # postgres_exporter

  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
```

#### Docker (Zalecane)

```yaml
  prometheus:
    image: prom/prometheus:latest
    container_name: adrion-prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    networks:
      - adrion-net
```

### Expose metrics z backendu

`uap/backend/api.py`:

```python
from prometheus_client import Counter, Histogram, generate_latest

# Define metrics
request_count = Counter('adrion_requests_total', 'Total requests', ['method', 'endpoint'])
request_duration = Histogram('adrion_request_duration_seconds', 'Request duration')
db_query_duration = Histogram('adrion_db_query_seconds', 'Database query duration')

# Middleware
@app.before_request
def track_request():
    g.start_time = time.time()

@app.after_request
def record_metrics(response):
    duration = time.time() - g.start_time
    request_count.labels(request.method, request.endpoint).inc()
    request_duration.observe(duration)
    return response

# Endpoint
@app.route('/metrics', methods=['GET'])
def metrics():
    return generate_latest()
```

## Grafana Setup

### Instalacja Grafana

#### Windows (Manual)

1. Pobierz z: https://grafana.com/grafana/download
2. Rozpakuj i uruchom: `bin\grafana-server.exe`
3. Otwórz: http://localhost:3000
4. Login: admin / admin

#### Docker

```yaml
  grafana:
    image: grafana/grafana:latest
    container_name: adrion-grafana
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin
      GF_SECURITY_ADMIN_USER: admin
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/dashboards:/etc/grafana/provisioning/dashboards:ro
      - ./monitoring/datasources.yml:/etc/grafana/provisioning/datasources/datasources.yml:ro
    networks:
      - adrion-net
```

### Konfiguracja Grafana

#### 1. Dodaj Prometheus datasource

```bash
curl -X POST http://localhost:3000/api/datasources \
  -H "Content-Type: application/json" \
  -u admin:admin \
  -d '{
    "name": "Prometheus",
    "type": "prometheus",
    "url": "http://prometheus:9090",
    "access": "proxy",
    "isDefault": true
  }'
```

#### 2. Import Dashboard

```bash
# Prometheus Stats Dashboard
curl -X POST http://localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -u admin:admin \
  -d @monitoring/dashboards/prometheus-stats.json
```

#### 3. Utwórz niestandardowy dashboard

**Metrics do śledzenia:**

```
adrion_requests_total           # Total HTTP requests
adrion_request_duration_seconds # Request latency
adrion_db_query_seconds        # Database query time
process_resident_memory_bytes  # Memory usage
process_cpu_seconds_total      # CPU usage
```

## Alerting Setup

### Alert Rules

`monitoring/alerts.yml`:

```yaml
groups:
  - name: adrion
    rules:
      - alert: HighErrorRate
        expr: rate(adrion_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate"
          description: "Error rate > 5% for 5 minutes"

      - alert: HighLatency
        expr: histogram_quantile(0.95, adrion_request_duration_seconds) > 1
        for: 5m
        annotations:
          summary: "High request latency"
          description: "P95 latency > 1 second"

      - alert: DBQuerySlow
        expr: histogram_quantile(0.95, adrion_db_query_seconds) > 0.5
        for: 5m
        annotations:
          summary: "Slow database queries"
          description: "P95 query time > 500ms"

      - alert: PostgreSQLDown
        expr: pg_up == 0
        for: 1m
        annotations:
          summary: "PostgreSQL is down"
          description: "PostgreSQL connection lost"
```

### Alert Manager Setup

```yaml
  alertmanager:
    image: prom/alertmanager:latest
    container_name: adrion-alertmanager
    ports:
      - "9093:9093"
    volumes:
      - ./monitoring/alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro
    networks:
      - adrion-net
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
```

`monitoring/alertmanager.yml`:

```yaml
global:
  resolve_timeout: 5m
  slack_api_url: '<YOUR_SLACK_WEBHOOK>'

route:
  receiver: 'slack'
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h

receivers:
  - name: 'slack'
    slack_configs:
      - channel: '#monitoring'
        title: 'ADRION Alert'
        text: '{{ .GroupLabels.alertname }}'
```

## Loki (Log Aggregation)

### Docker Setup

```yaml
  loki:
    image: grafana/loki:latest
    container_name: adrion-loki
    ports:
      - "3100:3100"
    volumes:
      - ./monitoring/loki.yml:/etc/loki/local-config.yaml
      - loki_data:/loki
    command: -config.file=/etc/loki/local-config.yaml
    networks:
      - adrion-net

  promtail:
    image: grafana/promtail:latest
    container_name: adrion-promtail
    volumes:
      - /var/log:/var/log:ro
      - ./monitoring/promtail.yml:/etc/promtail/config.yml:ro
    command: -config.file=/etc/promtail/config.yml
    depends_on:
      - loki
    networks:
      - adrion-net
```

### Log Query

W Grafana:

```
{job="adrion-backend"} | json | level="error"
```

## Quick Start (Docker Compose)

Dodaj do `docker-compose.yml`:

```yaml
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin

  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
```

Uruchom:

```bash
docker-compose up -d prometheus grafana loki

# Otwórz w przeglądarce
http://localhost:3000  # Grafana
http://localhost:9090  # Prometheus
```

## Dashboards do monitoringu

### Dashboard 1: System Health

**Queries:**
```
up                                      # Service availability
rate(requests_total[5m])                # Request rate
histogram_quantile(0.95, duration)      # P95 latency
```

### Dashboard 2: Database Performance

```
pg_database_size_bytes
pg_stat_user_tables_seq_scan_count
pg_stat_user_tables_idx_scan_count
```

### Dashboard 3: Error Tracking

```
rate(errors_total[5m])
rate(requests_total{status="5.."}[5m])
```

## Retention & Cleanup

### Prometheus

Domyślnie: 15 dni danych

Zmień w `prometheus.yml`:

```yaml
global:
  external_labels:
    cluster: 'production'

# Data retention
tsdb:
  retention_days: 90
```

### Grafana Logs

```
SELECT $__timeFilter(time) FROM logs LIMIT 100
```

## Next Steps

1. **Uruchom stos monitoringu:**
   ```bash
   docker-compose up -d prometheus grafana loki
   ```

2. **Konfiguruj backend metrics:**
   ```bash
   pip install prometheus-client
   ```

3. **Otwórz Grafana:**
   ```
   http://localhost:3000
   Admin / admin
   ```

4. **Dodaj Prometheus datasource**

5. **Utwórz niestandardowe dashboards**

6. **Ustaw alerty**

---

## Performance Baselines

Śledzenie dla ADRION 369:

- Request latency: < 500ms (P95)
- Database query: < 100ms (P95)
- Error rate: < 0.1%
- Memory usage: < 256MB
- CPU usage: < 50%

