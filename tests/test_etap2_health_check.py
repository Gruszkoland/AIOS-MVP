#!/usr/bin/env python3
"""
ETAP 2 MCP Agent Health Check & Integration Test
"""

import requests
import json
import time
from datetime import datetime

def check_agent_health(name, port):
    """Check if agent is healthy"""
    try:
        resp = requests.get(f'http://127.0.0.1:{port}/health', timeout=2)
        if resp.status_code == 200:
            return True, resp.json()
        return False, f"HTTP {resp.status_code}"
    except requests.exceptions.Timeout:
        return False, "Timeout"
    except requests.exceptions.ConnectionError:
        return False, "Connection refused"
    except Exception as e:
        return False, str(e)

def main():
    print("\n" + "="*70)
    print("ETAP 2: MCP AGENT HEALTH CHECK")
    print("="*70 + "\n")

    agents = [
        ("ROUTER", 9000),
        ("GENESIS", 9004),
        ("GUARDIAN", 9002),
        ("HEALER", 9003),
        ("ORACLE", 9005),
        ("VORTEX", 9001),
    ]

    results = []
    healthy_count = 0

    for name, port in agents:
        print(f"Testing {name:12} (port {port})...", end=" ", flush=True)
        is_healthy, data = check_agent_health(name, port)

        if is_healthy:
            print("[OK]")
            results.append({
                "agent": name,
                "port": port,
                "status": "healthy",
                "data": data
            })
            healthy_count += 1
        else:
            print(f"[FAIL] {data}")
            results.append({
                "agent": name,
                "port": port,
                "status": "offline",
                "error": data
            })

    print("\n" + "-"*70)
    print(f"SUMMARY: {healthy_count}/6 agents healthy\n")

    # Save report
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "phase": "ETAP_2_MCP_DEPLOYMENT",
        "health_check": results,
        "summary": {
            "total_agents": len(agents),
            "healthy": healthy_count,
            "offline": len(agents) - healthy_count,
            "deployment_status": "SUCCESS" if healthy_count == len(agents) else "PARTIAL"
        }
    }

    output_file = "logs/etap2/health_check_report.json"
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"Report saved to: {output_file}\n")

    if healthy_count == len(agents):
        print("✓ ALL AGENTS DEPLOYED SUCCESSFULLY")
        return 0
    else:
        print(f"✗ {len(agents) - healthy_count} agents offline")
        return 1

if __name__ == "__main__":
    exit(main())
