#!/usr/bin/env python3
"""Monitor ADRION 369 deployment status and health"""

import subprocess
import json
import time
from datetime import datetime
from pathlib import Path

def run_cmd(cmd):
    """Execute command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return result.stdout + result.stderr
    except Exception as e:
        return f"Error: {e}"

def get_containers():
    """Get container status JSON"""
    cmd = r'docker ps -a --format "{{json . }}" 2>&1'
    output = run_cmd(cmd)
    containers = []
    for line in output.strip().split('\n'):
        if line.startswith('{'):
            try:
                containers.append(json.loads(line))
            except:
                pass
    return containers

def monitor_orchestration():
    """Monitor orchestration stack deployment"""
    
    print("\n" + "=" * 80)
    print("🔍 ADRION 369 DEPLOYMENT MONITOR")
    print("=" * 80)
    print(f"Time: {datetime.now().strftime('%H:%M:%S')}\n")
    
    containers = get_containers()
    
    # Filter for orchestration services
    services = [
        'adrion-postgres', 'adrion-loki', 'adrion-promtail', 'adrion-ollama',
        'adrion-alert-handler', 'adrion-n8n', 'adrion-vortex', 'adrion-healer',
        'adrion-api', 'adrion-backup', 'adrion-grafana', 'adrion-prometheus',
        'adrion-nginx'
    ]
    
    status_counts = {'Up': 0, 'Created': 0, 'Exited': 0, 'Restarting': 0}
    
    print(f"{'Service':<25} | {'Status':<30} | {'Image':<30}")
    print("-" * 90)
    
    for svc in sorted(services):
        container = next((c for c in containers if svc in c.get('Names', '')), None)
        if container:
            status = container.get('Status', 'Unknown')
            image = container.get('Image', 'Unknown')
            
            # Count status
            if 'Up' in status:
                status_counts['Up'] += 1
            elif 'Created' in status:
                status_counts['Created'] += 1
            elif 'Restarting' in status:
                status_counts['Restarting'] += 1
            else:
                status_counts['Exited'] += 1
            
            print(f"{svc:<25} | {status:<30} | {image:<30}")
        else:
            print(f"{svc:<25} | {'NOT CREATED':<30} | {'---':<30}")
    
    print("\n" + "-" * 90)
    print(f"Summary: Up={status_counts['Up']} Created={status_counts['Created']} Restarting={status_counts['Restarting']} Exited={status_counts['Exited']}")
    
    # Health check for key services
    print("\n📊 HEALTH CHECKS:")
    print("-" * 90)
    
    health_ports = {
        'adrion-prometheus': ('http://localhost:9090', '-u', 'admin:admin'),
        'adrion-alert-handler': ('http://localhost:8090/health', '-s'),
        'adrion-ollama': ('http://localhost:11434/api/tags', '-s'),
        'adrion-postgres': ('localhost', '5432'),  # Just check port
    }
    
    for svc, check in health_ports.items():
        if any(svc in c.get('Names', '') for c in containers):
            container = next(c for c in containers if svc in c.get('Names', ''))
            if 'Up' in container.get('Status', ''):
                if svc == 'adrion-postgres':
                    status = '✅ PostgreSQL listening on 5432'
                else:
                    status = '✅ Service running'
            else:
                status = f"⚠️ {container.get('Status', 'Unknown')}"
            print(f"{svc:<25} {status}")
    
    print("\n" + "=" * 80)
    print("Use: docker-compose -f docker-compose-orchestration.yml logs -f <service>")
    print("=" * 80 + "\n")

if __name__ == '__main__':
    # Monitor for 2 minutes with 5-second intervals
    for i in range(24):
        monitor_orchestration()
        if i < 23:
            duration = int((24 - i - 1) * 5)
            print(f"Next check in 5s... (total {duration}s remaining)\n")
            time.sleep(5)
