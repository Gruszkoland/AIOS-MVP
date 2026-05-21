# 🔮 Automated Deployment Pipeline & Observability Sprint - Plan

**Sprint:** 3 / 3  
**Duration:** 3 weeks  
**Team:** 1 DevOps Engineer + 1 QA Automation Engineer  
**Deliverables:** CI/CD pipeline, Monitoring, Auto-scaling, Chaos testing  

---

## 🎯 Sprint Objectives

### Primary Goals
1. **GitHub Actions CI/CD Pipeline** - Automated build, test, deploy
2. **Production Monitoring** - Prometheus/Grafana/Jaeger/ELK
3. **Auto-Scaling** - Horizontal scaling rules (3-10 replicas)
4. **Chaos Engineering** - Resilience testing
5. **Health Checks** - Automated validation

### Success Metrics
```
✅ Deployment frequency:    1x per day (currently manual)
✅ Deployment time:         < 15 minutes (currently 60+ min)
✅ Time to recover:         < 5 minutes (currently 30+ min)
✅ Alert response time:     < 1 minute
✅ Observability coverage:  90% of requests traced
```

---

## 📋 Week 1: CI/CD Pipeline Setup

### Objective
Create GitHub Actions workflow for automated testing & deployment

### Current State (Manual)
```
Developer push
    ↓
Manual SSH to server
    ↓
Manual docker build
    ↓
Manual test execution
    ↓
Manual deployment
    ↓
Manual health checks
    ⏱️ Takes 60+ minutes
```

### Target State (Automated)
```
Developer push
    ↓
[AUTO] GitHub Actions triggered
    ↓
[AUTO] Lint & Format checks
    ↓
[AUTO] Unit tests (5 min)
    ↓
[AUTO] Integration tests (10 min)
    ↓
[AUTO] Build Docker image
    ↓
[AUTO] Push to ACR (Azure Container Registry)
    ↓
[AUTO] Deploy to staging
    ↓
[AUTO] Smoke tests
    ↓
[AUTO] Deploy to production (canary: 5%)
    ↓
[AUTO] Health checks & monitoring
    ⏱️ Total: 15 minutes
```

### Implementation

#### File: `.github/workflows/ci-cd.yml` (NEW)
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pylint black mypy pytest pytest-cov
      
      - name: Lint with pylint
        run: pylint mcp_servers core --fail-under=8.0
      
      - name: Format check with black
        run: black --check mcp_servers core
      
      - name: Type check with mypy
        run: mypy mcp_servers core --strict
      
      - name: Run tests
        run: |
          pytest tests/ \
            --cov=mcp_servers \
            --cov=core \
            --cov-report=xml \
            --junitxml=junit.xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml

  security-scan:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Run Bandit (security scan)
        run: |
          pip install bandit
          bandit -r mcp_servers core -f json -o bandit.json || true
      
      - name: OWASP dependency check
        uses: dependency-check/Dependency-Check_Action@main
        with:
          project: 'adrion-369'
          path: '.'
          format: 'JSON'

  build-and-push:
    needs: [lint-and-test, security-scan]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/develop'
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Docker image
        run: |
          docker build -f Dockerfile -t adrion-369:${{ github.sha }} .
          docker tag adrion-369:${{ github.sha }} adrion-369:latest
      
      - name: Push to ACR
        env:
          REGISTRY: ${{ secrets.ACR_REGISTRY }}
          USERNAME: ${{ secrets.ACR_USERNAME }}
          PASSWORD: ${{ secrets.ACR_PASSWORD }}
        run: |
          docker login -u $USERNAME -p $PASSWORD $REGISTRY
          docker tag adrion-369:latest $REGISTRY/adrion-369:${{ github.sha }}
          docker push $REGISTRY/adrion-369:${{ github.sha }}

  deploy-staging:
    needs: build-and-push
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to staging
        env:
          K8S_CONFIG: ${{ secrets.STAGING_KUBECONFIG }}
        run: |
          mkdir ~/.kube
          echo "$K8S_CONFIG" | base64 -d > ~/.kube/config
          
          # Update deployment image
          kubectl set image deployment/adrion-prod \
            adrion=${{ secrets.ACR_REGISTRY }}/adrion-369:${{ github.sha }} \
            -n staging
          
          # Wait for rollout
          kubectl rollout status deployment/adrion-prod -n staging
      
      - name: Run smoke tests
        run: |
          pip install requests
          python tests/smoke_tests.py --env staging

  deploy-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Canary deployment (5%)
        env:
          K8S_CONFIG: ${{ secrets.PROD_KUBECONFIG }}
        run: |
          mkdir ~/.kube
          echo "$K8S_CONFIG" | base64 -d > ~/.kube/config
          
          # Deploy to 5% of replicas first
          kubectl set image deployment/adrion-prod \
            adrion=${{ secrets.ACR_REGISTRY }}/adrion-369:${{ github.sha }} \
            -n production
          
          # Update with 1 replica
          kubectl scale deployment/adrion-prod --replicas=1 -n production
      
      - name: Monitor canary (5 min)
        run: |
          python scripts/monitor_canary.py \
            --duration 300 \
            --error-threshold 1.0 \
            --latency-threshold 500
      
      - name: Full deployment if canary OK
        if: success()
        env:
          K8S_CONFIG: ${{ secrets.PROD_KUBECONFIG }}
        run: |
          mkdir ~/.kube
          echo "$K8S_CONFIG" | base64 -d > ~/.kube/config
          
          # Scale to full capacity
          kubectl scale deployment/adrion-prod --replicas=3 -n production
          kubectl rollout status deployment/adrion-prod -n production
      
      - name: Run health checks
        run: |
          python tests/health_checks.py --env production --retries 5

  notify:
    needs: [deploy-production]
    runs-on: ubuntu-latest
    if: always()
    
    steps:
      - name: Slack notification
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "Deployment ${{ job.status }}: ${{ github.repository }}",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*Deployment Status*\nRepo: ${{ github.repository }}\nCommit: ${{ github.sha }}\nStatus: ${{ job.status }}"
                  }
                }
              ]
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

---

## 📊 Week 2: Production Monitoring Setup

### Objective
Complete observability stack: Prometheus, Grafana, Jaeger, ELK

### Architecture
```
Application
    ├─→ Prometheus (metrics)
    │   └─→ Grafana (dashboards)
    ├─→ Jaeger (distributed tracing)
    └─→ ELK Stack (logs)
        ├─ Elasticsearch
        ├─ Logstash
        └─ Kibana
```

### Implementation

#### File: `docker-compose.monitoring.yml` (NEW)
```yaml
version: '3.8'

services:
  # Prometheus - Metrics collection
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
  
  # Grafana - Visualization
  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin
      GF_INSTALL_PLUGINS: grafana-piechart-panel
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
    depends_on:
      - prometheus
  
  # Jaeger - Distributed tracing
  jaeger:
    image: jaegertracing/all-in-one:latest
    container_name: jaeger
    ports:
      - "6831:6831/udp"  # Agent
      - "16686:16686"    # UI
    environment:
      COLLECTOR_ZIPKIN_HOST_PORT: ":9411"
  
  # Elasticsearch - Log storage
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.5.0
    container_name: elasticsearch
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
  
  # Logstash - Log processing
  logstash:
    image: docker.elastic.co/logstash/logstash:8.5.0
    container_name: logstash
    volumes:
      - ./monitoring/logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    ports:
      - "5000:5000/tcp"
      - "5000:5000/udp"
    environment:
      - "ELASTICSEARCH_HOSTS=http://elasticsearch:9200"
    depends_on:
      - elasticsearch
  
  # Kibana - Log visualization
  kibana:
    image: docker.elastic.co/kibana/kibana:8.5.0
    container_name: kibana
    ports:
      - "5601:5601"
    environment:
      ELASTICSEARCH_HOSTS: http://elasticsearch:9200
    depends_on:
      - elasticsearch

volumes:
  prometheus_data:
  grafana_data:
  elasticsearch_data:
```

#### File: `monitoring/prometheus.yml` (NEW)
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - alertmanager:9093

rule_files:
  - 'alert_rules.yml'

scrape_configs:
  - job_name: 'adrion-services'
    static_configs:
      - targets:
          - 'router:8000'
          - 'genesis:8001'
          - 'guardian:8002'
          - 'healer:8003'
          - 'oracle:8004'
          - 'vortex:8005'
```

#### File: `monitoring/alert_rules.yml` (NEW)
```yaml
groups:
  - name: adrion
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
      
      # High latency
      - alert: HighLatency
        expr: histogram_quantile(0.95, http_request_duration_seconds) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High latency detected (p95 > 1s)"
      
      # High memory usage
      - alert: HighMemory
        expr: process_resident_memory_bytes / 1e9 > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage (> 1GB)"
      
      # Service down
      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.job }} is down"
```

#### Python Instrumentation: `core/instrumentation.py` (NEW)
```python
from prometheus_client import Counter, Histogram, Gauge
from jaeger_client import Config
import time

# Prometheus metrics
request_count = Counter('http_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('http_request_duration_seconds', 'Request latency', ['endpoint'])
active_requests = Gauge('http_requests_active', 'Active requests')
ml_prediction_time = Histogram('ml_prediction_seconds', 'ML prediction time')

# Jaeger tracing
def init_jaeger(service_name):
    config = Config(
        config={
            'sampler': {'type': 'const', 'param': 1},
            'logging': True,
        },
        service_name=service_name,
    )
    return config.initialize_tracer()

# Middleware
def instrument_request(f):
    def wrapper(*args, **kwargs):
        active_requests.inc()
        start = time.time()
        
        try:
            result = f(*args, **kwargs)
            status = 200
            return result
        except Exception as e:
            status = 500
            raise
        finally:
            duration = time.time() - start
            active_requests.dec()
            request_duration.observe(duration)
            request_count.labels(
                method='POST',
                endpoint=f.__name__,
                status=status
            ).inc()
    return wrapper
```

---

## ⚡ Week 3: Auto-Scaling & Chaos Testing

### Auto-Scaling Configuration

#### File: `k8s/autoscaling.yaml` (NEW)
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: adrion-hpa
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: adrion-prod
  minReplicas: 3
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 50
          periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
        - type: Percent
          value: 100
          periodSeconds: 30
```

### Chaos Engineering Tests

#### File: `tests/chaos_tests.py` (NEW)
```python
import pytest
import requests
import time
import random

class TestChaosEngineering:
    """Test system resilience under adverse conditions."""
    
    BASE_URL = "http://localhost:8000"
    
    def test_high_latency_tolerance(self):
        """Test that system handles high latency gracefully."""
        # Simulate 500ms network delay
        start = time.time()
        
        # Should still complete within reasonable time
        response = requests.post(f"{self.BASE_URL}/api/predict", timeout=5)
        
        assert response.status_code in [200, 504]  # 504 is acceptable under load
        duration = time.time() - start
        assert duration < 10  # Should complete or timeout quickly
    
    def test_partial_service_failure(self):
        """Test system when one service fails."""
        # Kill oracle service
        # System should degrade gracefully
        
        response = requests.post(f"{self.BASE_URL}/api/predict")
        
        # Should return 503 or fallback, not crash
        assert response.status_code in [200, 503]
    
    def test_resource_exhaustion(self):
        """Test system under resource constraints."""
        # Stress memory and CPU
        import multiprocessing
        
        def stress_cpu():
            for _ in range(1000000):
                _ = 2 ** 10
        
        processes = [
            multiprocessing.Process(target=stress_cpu)
            for _ in range(4)
        ]
        
        for p in processes:
            p.start()
        
        try:
            # System should still respond
            response = requests.get(f"{self.BASE_URL}/health", timeout=5)
            assert response.status_code == 200
        finally:
            for p in processes:
                p.terminate()
    
    def test_cascading_failure_recovery(self):
        """Test recovery from cascading failures."""
        # Simulate failure of Router → Genesis → Guardian
        # System should recover once services are back up
        
        # Kill all services
        # ... (implement service killing)
        
        time.sleep(5)
        
        # Restart services
        # ... (implement service restart)
        
        # System should recover
        max_retries = 30
        for i in range(max_retries):
            try:
                response = requests.get(f"{self.BASE_URL}/health", timeout=2)
                if response.status_code == 200:
                    break
            except requests.RequestException:
                time.sleep(1)
        else:
            raise AssertionError("System did not recover within timeout")
```

---

## 📋 Implementation Checklist

### Week 1: CI/CD
- [ ] Set up GitHub Actions workflows
- [ ] Configure ACR (Azure Container Registry)
- [ ] Set up Kubernetes credentials
- [ ] Test full CI/CD pipeline
- [ ] Document deployment process

### Week 2: Monitoring
- [ ] Deploy Prometheus
- [ ] Deploy Grafana with dashboards
- [ ] Deploy Jaeger for tracing
- [ ] Deploy ELK stack
- [ ] Create alert rules
- [ ] Instrument application code

### Week 3: Auto-Scaling & Testing
- [ ] Configure HPA rules
- [ ] Implement chaos tests
- [ ] Run load tests
- [ ] Validate auto-scaling behavior
- [ ] Document operations playbook

---

## 📊 Success Criteria

```
Metric                          Target    Status
──────────────────────────────────────────────────
CI/CD pipeline execution time   < 15min   ⏳
Deployment frequency            1x/day    ⏳
Time to recovery                < 5min    ⏳
Alert response time             < 1min    ⏳
Monitoring coverage             90%+      ⏳
Auto-scaling response           < 2min    ⏳
Chaos test success rate         100%      ⏳
```

---

## 💰 Effort & Resources

```
Task                        Effort    Resource
─────────────────────────────────────────────────
GitHub Actions CI/CD        5h        DevOps Engineer
ACR & Kubernetes setup      3h        DevOps Engineer
Prometheus/Grafana          4h        DevOps Engineer + QA
Jaeger/ELK setup            4h        DevOps Engineer
Auto-scaling config         3h        DevOps Engineer
Chaos engineering tests     4h        QA Automation Engineer
Documentation & validation  2h        Both
─────────────────────────────────────────────────
TOTAL                       25h       1 DevOps + 1 QA Automation
```

---

*Plan prepared: 14.05.2026*  
*Target dates: Weeks 4-6 of implementation*
