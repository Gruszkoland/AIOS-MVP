#!/usr/bin/env python3
"""
Grafana Dashboard Generator — DevOps Metrics & Project Overview
Generates a comprehensive dashboard JSON with project health, commit stats, and metrics
"""

import json
import os
from datetime import datetime
from pathlib import Path

def generate_grafana_dashboard():
    """Generate a complete Grafana dashboard JSON for DevOps monitoring"""
    
    dashboard = {
        "annotations": {
            "list": [
                {
                    "builtIn": 1,
                    "datasource": "-- Grafana --",
                    "enable": True,
                    "hide": True,
                    "iconColor": "rgba(0, 211, 255, 1)",
                    "name": "Annotations & Alerts",
                    "type": "dashboard"
                }
            ]
        },
        "editable": True,
        "gnetId": None,
        "graphTooltip": 0,
        "id": None,
        "links": [],
        "panels": [
            {
                "datasource": None,
                "fieldConfig": {"defaults": {}, "overrides": []},
                "gridPos": {"h": 8, "w": 24, "x": 0, "y": 0},
                "id": 1,
                "options": {"content": generate_project_overview_text()},
                "pluginVersion": "9.0.0",
                "targets": [],
                "title": "📊 Project Portfolio Overview",
                "type": "text"
            },
            {
                "datasource": "Prometheus",
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "palette-classic"},
                        "custom": {"hideFrom": {"tooltip": False, "viz": False, "legend": False}},
                        "mappings": [],
                        "unit": "short"
                    },
                    "overrides": []
                },
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
                "id": 2,
                "options": {
                    "displayLabels": ["name", "value"],
                    "legend": {"displayMode": "table", "placement": "bottom"},
                    "pieType": "pie",
                    "tooltip": {"mode": "single", "sort": "none"}
                },
                "targets": [
                    {
                        "expr": 'sum by (project) (increase(git_commits_total[30d]))',
                        "legendFormat": "{{project}}",
                        "refId": "A"
                    }
                ],
                "title": "📈 Commits by Project (30d)",
                "type": "piechart"
            },
            {
                "datasource": "Prometheus",
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "thresholds"},
                        "mappings": [
                            {"options": {"1": {"text": "UP", "color": "green"}, "0": {"text": "DOWN", "color": "red"}}, "type": "value"}
                        ],
                        "thresholds": {"mode": "absolute", "steps": [{"color": "green", "value": None}, {"color": "red", "value": 1}]},
                        "unit": "short"
                    },
                    "overrides": []
                },
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
                "id": 3,
                "options": {
                    "colorMode": "background",
                    "graphMode": "none",
                    "justifyMode": "auto",
                    "orientation": "auto",
                    "reduceOptions": {"values": False, "fields": "", "calcs": ["lastNotNull"]},
                    "textMode": "auto"
                },
                "targets": [
                    {
                        "expr": 'up{job=~"adrion-api|consultacja_api|n8n"}',
                        "legendFormat": "{{job}}",
                        "refId": "A"
                    }
                ],
                "title": "🟢 Service Health Status",
                "type": "stat"
            },
            {
                "datasource": "Prometheus",
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "palette-classic"},
                        "custom": {"axisLabel": "", "axisPlacement": "auto", "barAlignment": 0, "drawStyle": "line", "fillOpacity": 10, "gradientMode": "none", "hideFrom": {"tooltip": False, "viz": False, "legend": False}, "lineInterpolation": "linear", "lineWidth": 1, "pointSize": 5, "scaleDistribution": {"type": "linear"}, "showPoints": "auto", "spanNulls": False, "stacking": {"group": "A", "mode": "none"}, "thresholdsStyle": {"mode": "off"}},
                        "mappings": [],
                        "thresholds": {"mode": "absolute", "steps": [{"color": "green", "value": None}, {"color": "yellow", "value": 50}, {"color": "red", "value": 80}]},
                        "unit": "percent"
                    },
                    "overrides": []
                },
                "gridPos": {"h": 8, "w": 24, "x": 0, "y": 16},
                "id": 4,
                "options": {
                    "legend": {"calcs": ["mean", "max"], "displayMode": "table", "placement": "bottom"},
                    "tooltip": {"mode": "multi"}
                },
                "targets": [
                    {
                        "expr": 'rate(container_cpu_usage_seconds_total{container=~"adrion.*|consultacja.*"}[5m])*100',
                        "legendFormat": "CPU {{container}}",
                        "refId": "A"
                    },
                    {
                        "expr": 'container_memory_usage_bytes{container=~"adrion.*|consultacja.*"}/1e6',
                        "legendFormat": "Memory {{container}} (MB)",
                        "refId": "B"
                    }
                ],
                "title": "⚡ Container Resource Usage",
                "type": "timeseries"
            },
            {
                "datasource": "Prometheus",
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "palette-classic"},
                        "custom": {"axisLabel": "Requests/sec", "axisPlacement": "auto", "barAlignment": 0, "drawStyle": "bars", "fillOpacity": 100, "gradientMode": "none", "hideFrom": {"tooltip": False, "viz": False, "legend": False}, "lineInterpolation": "linear", "lineWidth": 1, "pointSize": 5, "scaleDistribution": {"type": "linear"}, "showPoints": "never", "spanNulls": True, "stacking": {"group": "A", "mode": "normal"}, "thresholdsStyle": {"mode": "off"}},
                        "mappings": [],
                        "thresholds": {"mode": "absolute", "steps": [{"color": "green", "value": None}]},
                        "unit": "reqps"
                    },
                    "overrides": []
                },
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 24},
                "id": 5,
                "options": {
                    "legend": {"calcs": ["mean", "max"], "displayMode": "table", "placement": "bottom"},
                    "tooltip": {"mode": "multi"}
                },
                "targets": [
                    {
                        "expr": 'rate(http_requests_total{job=~"adrion-api|consultacja_api"}[5m])',
                        "legendFormat": "{{job}}",
                        "refId": "A"
                    }
                ],
                "title": "📊 API Request Rate",
                "type": "timeseries"
            },
            {
                "datasource": "Prometheus",
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "palette-classic"},
                        "custom": {"axisLabel": "Latency (ms)", "axisPlacement": "auto", "barAlignment": 0, "drawStyle": "line", "fillOpacity": 0, "gradientMode": "none", "hideFrom": {"tooltip": False, "viz": False, "legend": False}, "lineInterpolation": "linear", "lineWidth": 2, "pointSize": 5, "scaleDistribution": {"type": "linear"}, "showPoints": "auto", "spanNulls": False, "stacking": {"group": "A", "mode": "none"}, "thresholdsStyle": {"mode": "off"}},
                        "mappings": [],
                        "thresholds": {"mode": "absolute", "steps": [{"color": "green", "value": None}, {"color": "yellow", "value": 200}, {"color": "red", "value": 500}]},
                        "unit": "ms"
                    },
                    "overrides": []
                },
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 24},
                "id": 6,
                "options": {
                    "legend": {"calcs": ["mean", "max"], "displayMode": "table", "placement": "bottom"},
                    "tooltip": {"mode": "multi"}
                },
                "targets": [
                    {
                        "expr": 'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))*1000',
                        "legendFormat": "p95",
                        "refId": "A"
                    },
                    {
                        "expr": 'histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))*1000',
                        "legendFormat": "p99",
                        "refId": "B"
                    }
                ],
                "title": "⏱️ API Latency (95th/99th percentile)",
                "type": "timeseries"
            },
            {
                "datasource": "Loki",
                "fieldConfig": {"defaults": {}, "overrides": []},
                "gridPos": {"h": 8, "w": 24, "x": 0, "y": 32},
                "id": 7,
                "options": {
                    "dedupStrategy": "none",
                    "enableLogDetails": True,
                    "prettifyLogMessage": False,
                    "showCommonLabels": False,
                    "showLabels": False,
                    "showTime": True,
                    "sortOrder": 1,
                    "wrapLogMessage": False
                },
                "targets": [
                    {
                        "expr": '{job=~"adrion-.*|consultacja-.*"} | json |  level="ERROR" or level="WARN"',
                        "legendFormat": "",
                        "refId": "A"
                    }
                ],
                "title": "🚨 Error & Warning Logs (Last 24h)",
                "type": "logs"
            }
        ],
        "refresh": "30s",
        "schemaVersion": 38,
        "style": "dark",
        "tags": ["devops", "monitoring", "adrion-369", "multi-project"],
        "templating": {"list": []},
        "time": {"from": "now-7d", "to": "now"},
        "timepicker": {},
        "timezone": "",
        "title": "🎯 ADRION 369 — DevOps Dashboard",
        "uid": "adrion-devops-main",
        "version": 1
    }
    
    return dashboard

def generate_project_overview_text():
    """Generate markdown text for project overview panel"""
    return """# 📊 ADRION 369 DevOps Dashboard

## 🎯 Active Projects

| Project | Type | Status | Commits (30d) | Last Update |
|---------|------|--------|---------------|-------------|
| **PROJEKTY/162 demencje w schemacie 369** | Core Platform | 🟢 ACTIVE | ~150+ | Last 12h |
| **PROJEKTY/Consultacja-Wielomodelowa-AI** | Multi-Model API | 🟢 ACTIVE | ~20 | Last 48h |
| **PROJEKTY/n8n-produkcja** | Workflows | 🟢 ACTIVE | ~15 | Last 72h |
| **PROJEKTY/adrion-369-architecture** | Documentation | 🟡 STABLE | ~5 | Last 7d |
| **PROJEKTY/leadgen-comet-pipeline** | Lead Generation | 🟡 STABLE | ~10 | Last 5d |

## 🔧 Key Metrics

- **Total Files**: 79,100+
- **Docker Services**: 11+ running
- **Databases**: PostgreSQL (Genesis), Redis, Loki
- **LLM Engine**: Ollama (Local)
- **Monitoring**: Grafana + Prometheus + Loki
- **Orchestration**: n8n (SAP integration)

## 📈 Dashboard Queries

This dashboard monitors:
- ✅ Service health (up/down)
- ✅ Container resource usage (CPU, Memory)
- ✅ API request rates & latency
- ✅ Error logs & warnings (Loki)
- ✅ Git commit trends (30-day)

## 🚀 Quick Links

- API: http://localhost:8001
- Consultacja: http://localhost:8000
- n8n: http://localhost:5678
- Grafana: http://localhost:3000
- PostgreSQL: localhost:5432
"""

def create_grafana_datasources_config():
    """Create Prometheus & Loki datasource configurations"""
    datasources = {
        "apiVersion": 1,
        "providers": [
            {
                "name": "Prometheus",
                "orgId": 1,
                "folder": "",
                "type": "prometheus",
                "disableDeletion": False,
                "updateIntervalSeconds": 10,
                "options": {
                    "httpMethod": "POST"
                },
                "url": "http://prometheus:9090",
                "access": "proxy",
                "isDefault": True,
                "jsonData": {
                    "timeInterval": "15s"
                }
            },
            {
                "name": "Loki",
                "orgId": 1,
                "folder": "",
                "type": "loki",
                "disableDeletion": False,
                "updateIntervalSeconds": 10,
                "options": {
                    "httpMethod": "GET"
                },
                "url": "http://loki:3100",
                "access": "proxy",
                "isDefault": False,
                "jsonData": {
                    "maxLines": 1000
                }
            }
        ]
    }
    return datasources

def main():
    """Generate and save Grafana dashboard"""
output_dir = Path("c:\\Users\\adiha\\.1_Projekty\\PROJEKTY\\adrion-deploy\\grafana\\provisioning\\dashboards")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate dashboard
    dashboard = generate_grafana_dashboard()
    dashboard_path = output_dir / "devops-dashboard.json"
    with open(dashboard_path, "w") as f:
        json.dump(dashboard, f, indent=2)
    print(f"✅ Dashboard saved: {dashboard_path}")
    
    # Generate datasources config
    datasources = create_grafana_datasources_config()
    datasources_path = output_dir.parent / "datasources" / "grafana-datasources.json"
    datasources_path.parent.mkdir(parents=True, exist_ok=True)
    with open(datasources_path, "w") as f:
        json.dump(datasources, f, indent=2)
    print(f"✅ Datasources config saved: {datasources_path}")
    
    print("\n🎯 Grafana dashboard generated successfully!")
    print(f"   - Dashboard JSON: {dashboard_path}")
    print(f"   - Import to Grafana: http://localhost:3000/admin/provisioning")

if __name__ == "__main__":
    main()
