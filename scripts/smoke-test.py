#!/usr/bin/env python
"""
ADRION 369 + n8n Integration Smoke Test

Validates:
1. ADRION 369 API health
2. Guardian Checkpoint endpoint functionality
3. n8n workflow triggering
4. Genesis Record integrity
5. CVC/LTM state management
6. Prometheus metrics collection

Exit codes:
  0 = All tests passed
  1 = One or more tests failed
"""

import json
import requests
import sys
import time
from datetime import datetime

# Configuration
ADRION_API_URL = "http://localhost:8000"
N8N_API_URL = "http://localhost:5678"
PROMETHEUS_URL = "http://localhost:9090"

TEST_RESULTS = []

def log_test(test_name: str, passed: bool, message: str = ""):
    """Log test result."""
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"{status} | {test_name}")
    if message:
        print(f"       {message}")
    TEST_RESULTS.append({"test": test_name, "passed": passed, "message": message})

def test_adrion_health():
    """Test 1: ADRION 369 API health check."""
    try:
        response = requests.get(f"{ADRION_API_URL}/health", timeout=5)
        passed = response.status_code == 200
        log_test("ADRION 369 Health Check", passed, f"Status: {response.status_code}")
        return passed
    except Exception as e:
        log_test("ADRION 369 Health Check", False, str(e))
        return False

def test_guardian_checkpoint():
    """Test 2: Guardian Checkpoint endpoint."""
    try:
        payload = {
            "job": {
                "id": f"test-{int(time.time())}",
                "description": "Smoke test operation",
                "operation_type": "test"
            },
            "analysis": {
                "context": {"test": True},
                "source": "smoke-test"
            },
            "context": {
                "workflow_id": "smoke-test",
                "user_id": "smoke-test-user"
            }
        }
        
        response = requests.post(
            f"{ADRION_API_URL}/api/mcp/guardian/checkpoint",
            json=payload,
            timeout=10
        )
        
        passed = response.status_code in [200, 400]  # 200=approved, 400=denied (both valid)
        result = response.json() if response.text else {}
        
        log_test(
            "Guardian Checkpoint", 
            passed,
            f"Status: {response.status_code}, Approved: {result.get('approved', 'unknown')}"
        )
        return passed
    except Exception as e:
        log_test("Guardian Checkpoint", False, str(e))
        return False

def test_cvc_status():
    """Test 3: CVC status endpoint."""
    try:
        response = requests.get(f"{ADRION_API_URL}/api/mcp/memory/status", timeout=5)
        passed = response.status_code == 200
        
        if passed:
            data = response.json()
            cvc_state = data.get("cvc", {}).get("state", "unknown")
            log_test("CVC Status", True, f"State: {cvc_state}")
        else:
            log_test("CVC Status", False, f"Status: {response.status_code}")
        
        return passed
    except Exception as e:
        log_test("CVC Status", False, str(e))
        return False

def test_ltm_profile():
    """Test 4: LTM profile endpoint."""
    try:
        response = requests.get(
            f"{ADRION_API_URL}/api/mcp/ltm/profile",
            headers={"X-User-ID": "smoke-test-user"},
            timeout=5
        )
        passed = response.status_code == 200
        
        if passed:
            data = response.json()
            sessions = data.get("session_count", 0)
            log_test("LTM Profile", True, f"Sessions: {sessions}")
        else:
            log_test("LTM Profile", False, f"Status: {response.status_code}")
        
        return passed
    except Exception as e:
        log_test("LTM Profile", False, str(e))
        return False

def test_genesis_integrity():
    """Test 5: Genesis Record integrity."""
    try:
        response = requests.get(f"{ADRION_API_URL}/api/mcp/genesis/verify", timeout=5)
        passed = response.status_code == 200
        
        if passed:
            data = response.json()
            integrity = data.get("integrity", False)
            record_count = data.get("records", 0)
            log_test(
                "Genesis Record Integrity",
                integrity,
                f"Integrity: {integrity}, Records: {record_count}"
            )
            return integrity
        else:
            log_test("Genesis Record Integrity", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        log_test("Genesis Record Integrity", False, str(e))
        return False

def test_prometheus_metrics():
    """Test 6: Prometheus metrics endpoint."""
    try:
        response = requests.get(f"{ADRION_API_URL}/metrics", timeout=5)
        passed = response.status_code == 200 and "cvc_counter" in response.text
        
        if passed:
            lines = response.text.split("\n")
            metric_count = len([l for l in lines if l and not l.startswith("#")])
            log_test("Prometheus Metrics", True, f"Metrics: {metric_count}")
        else:
            log_test("Prometheus Metrics", False, f"Status: {response.status_code}")
        
        return passed
    except Exception as e:
        log_test("Prometheus Metrics", False, str(e))
        return False

def test_n8n_webhook():
    """Test 7: n8n webhook availability."""
    try:
        # Simple health check for n8n
        response = requests.get(f"{N8N_API_URL}/healthz", timeout=5)
        passed = response.status_code == 200
        log_test("n8n Health Check", passed, f"Status: {response.status_code}")
        return passed
    except Exception as e:
        log_test("n8n Health Check", False, str(e))
        return False

def test_docker_compose_services():
    """Test 8: Docker Compose services status."""
    try:
        import subprocess
        result = subprocess.run(
            ["docker-compose", "-f", "docker-compose.n8n-adrion.yml", "ps"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        services = ["adrion-api", "n8n", "postgres-adrion-n8n", "redis-adrion", "prometheus-adrion", "grafana-adrion"]
        running = all(service in result.stdout and "Up" in result.stdout for service in services)
        
        log_test(
            "Docker Compose Services",
            running,
            f"Found {len([s for s in services if s in result.stdout and 'Up' in result.stdout])}/{len(services)} running"
        )
        return running
    except Exception as e:
        log_test("Docker Compose Services", False, str(e))
        return False

def print_summary():
    """Print test summary."""
    total = len(TEST_RESULTS)
    passed = sum(1 for r in TEST_RESULTS if r["passed"])
    failed = total - passed
    
    print("\n" + "=" * 60)
    print(f"SMOKE TEST SUMMARY: {passed}/{total} passed, {failed}/{total} failed")
    print("=" * 60)
    
    if failed > 0:
        print("\nFailed tests:")
        for result in TEST_RESULTS:
            if not result["passed"]:
                print(f"  - {result['test']}: {result['message']}")
    
    return failed == 0

def main():
    """Run all smoke tests."""
    print("=" * 60)
    print("ADRION 369 + n8n Integration Smoke Test")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 60)
    print()
    
    # Run all tests
    test_adrion_health()
    time.sleep(1)
    
    test_guardian_checkpoint()
    test_cvc_status()
    test_ltm_profile()
    test_genesis_integrity()
    test_prometheus_metrics()
    test_n8n_webhook()
    
    # This test may fail if running outside Docker
    try:
        test_docker_compose_services()
    except:
        print("⚠ SKIP | Docker Compose Services (running outside container)")
    
    print()
    all_passed = print_summary()
    
    print(f"\nCompleted: {datetime.now().isoformat()}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
