#!/usr/bin/env python3
"""
ADRION 369 - Grafana Data Source & Dashboard Setup
Configures Prometheus, Loki, and creates basic dashboards
"""

import subprocess
import shutil
import os
import json
import time
import requests
from datetime import datetime

GRAFANA_URL = "http://localhost:3000"
GRAFANA_USER = "admin"
GRAFANA_PASSWORD = "admin"
NAMESPACE = "adrion-369"

def log_info(msg):
    print(f"[INFO] {msg}")

def log_ok(msg):
    print(f"[OK]   {msg}")

def log_err(msg):
    print(f"[ERR]  {msg}")

def wait_for_grafana(timeout=30):
    """Wait for Grafana to be ready"""
    log_info(f"Waiting for Grafana to be ready ({timeout}s timeout)...")
    start = time.time()
    
    while time.time() - start < timeout:
        try:
            response = requests.get(f"{GRAFANA_URL}/api/health", timeout=5)
            if response.status_code == 200:
                log_ok("Grafana is ready!")
                return True
        except:
            pass
        time.sleep(2)
    
    log_err("Grafana failed to respond within timeout")
    return False

def add_data_source(name, ds_type, url, access="proxy"):
    """Add a data source to Grafana"""
    log_info(f"Adding data source: {name} ({ds_type})...")
    
    payload = {
        "name": name,
        "type": ds_type,
        "url": url,
        "access": access,
        "isDefault": ds_type == "prometheus",
        "jsonData": {}
    }
    
    try:
        response = requests.post(
            f"{GRAFANA_URL}/api/datasources",
            json=payload,
            auth=(GRAFANA_USER, GRAFANA_PASSWORD),
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            log_ok(f"Data source '{name}' created")
            return response.json().get('id')
        else:
            log_err(f"Failed to create data source: {response.text[:200]}")
            return None
    except Exception as e:
        log_err(f"Exception: {e}")
        return None

def create_dashboard(name, panels, ds_id):
    """Create a basic dashboard with panels"""
    log_info(f"Creating dashboard: {name}...")
    
    dashboard = {
        "dashboard": {
            "title": name,
            "tags": ["ADRION", "Production"],
            "timezone": "UTC",
            "panels": panels,
            "refresh": "10s",
            "time": {"from": "now-1h", "to": "now"},
            "schemaVersion": 27,
            "version": 1
        },
        "overwrite": True
    }
    
    try:
        response = requests.post(
            f"{GRAFANA_URL}/api/dashboards/db",
            json=dashboard,
            auth=(GRAFANA_USER, GRAFANA_PASSWORD),
            timeout=15
        )
        
        if response.status_code in [200, 201]:
            log_ok(f"Dashboard '{name}' created")
            return response.json()
        else:
            log_err(f"Failed to create dashboard: {response.text[:200]}")
            return None
    except Exception as e:
        log_err(f"Exception: {e}")
        return None

def main():
    print("=" * 70)
    print("ADRION 369 - Grafana Configuration Script")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Check prerequisites
    log_info("Checking prerequisites...")
    try:
        response = requests.get(f"{GRAFANA_URL}/api/health", timeout=5)
        if response.status_code != 200:
            log_err("Grafana not responding - start port-forward first:")
            print("  kubectl port-forward -n adrion-369 svc/grafana 3000:3000")
            return False
    except:
        log_err("Cannot reach Grafana - start port-forward first:")
        print("  kubectl port-forward -n adrion-369 svc/grafana 3000:3000")
        return False
    
    log_ok("Grafana is accessible")
    
    # Wait for Grafana to be fully ready
    if not wait_for_grafana(timeout=30):
        return False
    
    print()
    print("[PHASE 1] Adding Data Sources")
    print("-" * 70)
    
    # Add Prometheus
    prom_id = add_data_source(
        "Prometheus",
        "prometheus",
        "http://prometheus:9090",
        access="proxy"
    )
    
    if not prom_id:
        log_err("Failed to add Prometheus - it may not be ready yet")
        prom_id = 1  # Assume ID 1
    
    # Add Loki
    loki_id = add_data_source(
        "Loki",
        "loki",
        "http://loki:3100",
        access="proxy"
    )
    
    if not loki_id:
        log_err("Failed to add Loki - it may not be ready yet")
        loki_id = 2  # Assume ID 2
    
    print()
    print("[PHASE 2] Creating Dashboards")
    print("-" * 70)
    
    # System Overview Dashboard
    panels = [
        {
            "id": 1,
            "title": "Prometheus Uptime",
            "type": "stat",
            "targets": [
                {
                    "expr": "up[5m]",
                    "refId": "A",
                    "legendFormat": "{{job}}"
                }
            ],
            "fieldConfig": {
                "defaults": {
                    "color": {"mode": "palette-classic"},
                    "custom": {},
                    "mappings": [],
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [
                            {"color": "red", "value": None},
                            {"color": "green", "value": 1}
                        ]
                    }
                }
            }
        }
    ]
    
    create_dashboard("ADRION System Overview", panels, prom_id)
    
    print()
    print("[PHASE 3] Post-Configuration")
    print("-" * 70)
    
    log_ok("Grafana configuration complete!")
    print()
    print("Next steps:")
    print("  1. Open Grafana: http://localhost:3000")
    print("  2. Login: admin / admin")
    print("  3. Navigate to: Dashboards (left menu)")
    print("  4. Review available dashboards")
    print("  5. Create custom dashboards as needed")
    print()
    print("Data sources available (for manual dashboard creation):")
    print(f"  - Prometheus (ID: {prom_id})")
    print(f"  - Loki (ID: {loki_id})")
    
    return True

if __name__ == "__main__":
    print()
    success = main()
    print()
    print("=" * 70)
    if success:
        print("[OK] Grafana setup complete")
    else:
        print("[ERR] Grafana setup incomplete - check errors above")
    print("=" * 70)
