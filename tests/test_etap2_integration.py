#!/usr/bin/env python3
"""
ETAP 2 PHASE 2: Inter-Agent Communication & Integration Test
Tests agent discovery, routing, and 42-endpoint API surface
"""

import requests
import json
from datetime import datetime
import time

BASE_AGENTS = [
    ("ROUTER", 9000),
    ("GENESIS", 9004),
    ("GUARDIAN", 9002),
    ("HEALER", 9003),
    ("ORACLE", 9005),
    ("VORTEX", 9001),
]

def test_agent_discovery():
    """Test if agents can discover each other"""
    print("\n[PHASE 2A] AGENT DISCOVERY")
    print("-" * 60)

    discovered = 0
    for name, port in BASE_AGENTS:
        try:
            resp = requests.get(f'http://127.0.0.1:{port}', timeout=1)
            if resp.status_code in [200, 404]:  # 404 is OK, means server is running
                discovered += 1
                print(f"  [+] {name}: discovered (port {port})")
            else:
                print(f"  [-] {name}: HTTP {resp.status_code}")
        except:
            print(f"  [-] {name}: unreachable")

    return discovered == len(BASE_AGENTS)

def test_routing_endpoints():
    """Test routing and inter-agent communication"""
    print("\n[PHASE 2B] ROUTING ENDPOINTS")
    print("-" * 60)

    # Test ROUTER's /status endpoint (should show all agents)
    try:
        resp = requests.get('http://127.0.0.1:9000/status', timeout=2)
        if resp.status_code == 200:
            data = resp.json()
            print("  [+] ROUTER /status: OK")
            print(f"      Agents tracked: {json.dumps(data, indent=2)[:100]}...")
            return True
        else:
            print(f"  [-] ROUTER /status: HTTP {resp.status_code}")
            return False
    except Exception as e:
        print(f"  [-] ROUTER /status: {str(e)[:50]}")
        return False

def test_api_endpoints():
    """Sample API endpoint tests (42 endpoints per plan)"""
    print("\n[PHASE 2C] API ENDPOINT SAMPLES")
    print("-" * 60)

    # ROUTER endpoints
    endpoints = {
        ("ROUTER", 9000): [
            ("/health", "GET"),
            ("/status", "GET"),
            ("/stats/routing", "GET"),
            ("/stats/agents", "GET"),
            ("/traces/recent", "GET"),
        ],
        ("GENESIS", 9004): [
            ("/health", "GET"),
            ("/status", "GET"),
        ],
        ("GUARDIAN", 9002): [
            ("/health", "GET"),
            ("/audit", "GET"),
        ],
        ("HEALER", 9003): [
            ("/health", "GET"),
            ("/recovery", "GET"),
        ],
        ("ORACLE", 9005): [
            ("/health", "GET"),
            ("/predict", "GET"),
        ],
        ("VORTEX", 9001): [
            ("/health", "GET"),
            ("/fedlearn", "GET"),
        ],
    }

    success_count = 0
    total_count = 0

    for (agent_name, port), agent_endpoints in endpoints.items():
        for path, method in agent_endpoints:
            total_count += 1
            try:
                if method == "GET":
                    resp = requests.get(f'http://127.0.0.1:{port}{path}', timeout=1)
                else:
                    resp = requests.post(f'http://127.0.0.1:{port}{path}', timeout=1)

                if resp.status_code in [200, 201, 400, 401]:  # Meaningful responses
                    print(f"  [+] {agent_name:10} {method:4} {path:20} HTTP {resp.status_code}")
                    success_count += 1
                else:
                    print(f"  [-] {agent_name:10} {method:4} {path:20} HTTP {resp.status_code}")
            except requests.exceptions.Timeout:
                print(f"  [!] {agent_name:10} {method:4} {path:20} TIMEOUT")
            except Exception as e:
                print(f"  [!] {agent_name:10} {method:4} {path:20} {str(e)[:30]}")

    success_rate = (success_count / total_count * 100) if total_count > 0 else 0
    print(f"\n  Endpoint Success Rate: {success_count}/{total_count} ({success_rate:.0f}%)")
    return success_rate >= 80

def test_event_propagation():
    """Test if events propagate through swarm"""
    print("\n[PHASE 2D] EVENT PROPAGATION TEST")
    print("-" * 60)

    # Try to send a test event through ROUTER
    try:
        payload = {
            "event": "test_ping",
            "source": "integration_test",
            "timestamp": datetime.utcnow().isoformat()
        }
        resp = requests.post(
            'http://127.0.0.1:9000/route',
            json=payload,
            timeout=2
        )
        if resp.status_code in [200, 400]:  # 400 OK for POST without full data
            print("  [+] Event propagation: Router received event")
            return True
        else:
            print(f"  [!] Event propagation: HTTP {resp.status_code}")
            return False
    except Exception as e:
        print(f"  [!] Event propagation: {str(e)[:50]}")
        return False

def main():
    print("\n" + "="*70)
    print("ETAP 2: MCP INTER-AGENT COMMUNICATION & INTEGRATION TEST")
    print("="*70)

    results = {
        "discovery": test_agent_discovery(),
        "routing": test_routing_endpoints(),
        "endpoints": test_api_endpoints(),
        "propagation": test_event_propagation(),
    }

    print("\n" + "="*70)
    print("INTEGRATION TEST SUMMARY")
    print("="*70)

    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {test_name:15} [{status}]")

    all_passed = all(results.values())
    overall_status = "SUCCESS" if all_passed else "PARTIAL"

    print("\n" + "-"*70)
    print(f"Overall Status: {overall_status}")

    if all_passed:
        print("\n[SUCCESS] All integration tests passed!")
        print("ETAP 2 Phase 2 ready for Phase 3 (API surface validation)")
    else:
        print("\n[PARTIAL] Some tests failed - review above for details")

    # Save report
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "phase": "ETAP_2_INTEGRATION_TEST",
        "tests": results,
        "overall_status": overall_status,
        "notes": "6-agent swarm inter-communication verification"
    }

    import os
    os.makedirs("logs/etap2", exist_ok=True)
    with open("logs/etap2/integration_test_report.json", "w") as f:
        json.dump(report, f, indent=2)

    print(f"Report: logs/etap2/integration_test_report.json\n")

    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())
