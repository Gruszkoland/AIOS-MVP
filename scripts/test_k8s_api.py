#!/usr/bin/env python3
"""
UAP Kubernetes Integration API Test Suite

Tests all 8 new Kubernetes endpoints:
- GET /mapi/v1/kubernetes/cluster-info
- GET /mapi/v1/kubernetes/pods
- GET /mapi/v1/kubernetes/services
- GET /mapi/v1/kubernetes/deployments
- GET /mapi/v1/kubernetes/pod/<pod_name>/logs
- POST /mapi/v1/kubernetes/pod/<pod_name>/restart
- GET /mapi/v1/kubernetes/metrics
- GET /mapi/v1/kubernetes/events

Usage:
  python test_k8s_api.py [--api-key KEY] [--host HOST] [--port PORT]

"""

import argparse
import json
import sys
from typing import Dict, Any, Optional
import requests
from datetime import datetime
import time

# Configuration
API_HOST = "localhost"
API_PORT = 8002
API_KEY = ""
BASE_URL = f"http://{API_HOST}:{API_PORT}"

# Colors for terminal output
class Colors:
    PASS = '\033[92m'
    FAIL = '\033[91m'
    INFO = '\033[94m'
    WARN = '\033[93m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print bold header"""
    print(f"\n{Colors.BOLD}{Colors.INFO}{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}{Colors.RESET}")


def print_test(name: str, status: str, details: str = ""):
    """Print test result"""
    symbol = "✓" if status == "PASS" else "✗"
    color = Colors.PASS if status == "PASS" else Colors.FAIL
    print(f"{color}{symbol} {name:<50} [{status}]{Colors.RESET}")
    if details:
        print(f"  {Colors.WARN}{details}{Colors.RESET}")


def print_info(text: str):
    """Print info message"""
    print(f"{Colors.INFO}ℹ {text}{Colors.RESET}")


def make_request(method: str, endpoint: str, data: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, str]] = None) -> tuple[int, Dict[str, Any]]:
    """Make API request"""
    url = f"{BASE_URL}{endpoint}"
    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, params=params, timeout=10)
        else:
            return 500, {"error": f"Unknown method: {method}"}

        try:
            return response.status_code, response.json()
        except:
            return response.status_code, {"raw": response.text[:500]}

    except requests.exceptions.ConnectionError:
        return 0, {"error": f"Cannot connect to {url}"}
    except requests.exceptions.Timeout:
        return 0, {"error": f"Request timeout to {url}"}
    except Exception as e:
        return 0, {"error": str(e)}


def test_health_check():
    """Test basic health endpoint"""
    print_header("Health Check")

    status, data = make_request("GET", "/mapi/v1/health")

    if status == 200:
        print_test("Health Endpoint", "PASS", f"Status: {data.get('status', 'unknown')}")
        return True
    else:
        print_test("Health Endpoint", "FAIL", f"HTTP {status}")
        return False


def test_cluster_info():
    """Test GET /mapi/v1/kubernetes/cluster-info"""
    print_header("Test 1: Cluster Information")

    status, data = make_request("GET", "/mapi/v1/kubernetes/cluster-info")

    if status == 200:
        print_test("Cluster Info Endpoint", "PASS")
        cluster = data.get("cluster", {})
        print_info(f"  Status: {cluster.get('status', 'unknown')}")
        print_info(f"  Nodes: {cluster.get('nodes', 'unknown')}")
        return True
    elif status == 503:
        print_test("Cluster Info Endpoint", "FAIL", "Kubernetes integration not available")
        return False
    else:
        print_test("Cluster Info Endpoint", "FAIL", f"HTTP {status}")
        return False


def test_pods_status():
    """Test GET /mapi/v1/kubernetes/pods"""
    print_header("Test 2: Pods Status")

    status, data = make_request("GET", "/mapi/v1/kubernetes/pods")

    if status == 200:
        print_test("Pods Endpoint", "PASS")
        pods = data.get("pods", {})
        print_info(f"  Total: {pods.get('total_pods', 0)}")
        print_info(f"  Running: {pods.get('running', 0)}")
        print_info(f"  Pending: {pods.get('pending', 0)}")
        print_info(f"  Failed: {pods.get('failed', 0)}")
        return True
    elif status == 503:
        print_test("Pods Endpoint", "FAIL", "Kubernetes integration not available")
        return False
    else:
        print_test("Pods Endpoint", "FAIL", f"HTTP {status}")
        return False


def test_services():
    """Test GET /mapi/v1/kubernetes/services"""
    print_header("Test 3: Services")

    status, data = make_request("GET", "/mapi/v1/kubernetes/services")

    if status == 200:
        print_test("Services Endpoint", "PASS")
        services = data.get("services", {})
        count = services.get("count", 0)
        print_info(f"  Services found: {count}")
        return True
    elif status == 503:
        print_test("Services Endpoint", "FAIL", "Kubernetes integration not available")
        return False
    else:
        print_test("Services Endpoint", "FAIL", f"HTTP {status}")
        return False


def test_deployments():
    """Test GET /mapi/v1/kubernetes/deployments"""
    print_header("Test 4: Deployments")

    status, data = make_request("GET", "/mapi/v1/kubernetes/deployments")

    if status == 200:
        print_test("Deployments Endpoint", "PASS")
        deployments = data.get("deployments", {})
        count = deployments.get("count", 0)
        print_info(f"  Deployments found: {count}")
        return True
    elif status == 503:
        print_test("Deployments Endpoint", "FAIL", "Kubernetes integration not available")
        return False
    else:
        print_test("Deployments Endpoint", "FAIL", f"HTTP {status}")
        return False


def test_pod_logs():
    """Test GET /mapi/v1/kubernetes/pod/{pod_name}/logs"""
    print_header("Test 5: Pod Logs")

    # Try to get logs from a known pod
    pod_name = "api-0"  # Common pod name
    status, data = make_request("GET", f"/mapi/v1/kubernetes/pod/{pod_name}/logs", params={"lines": "10"})

    if status == 200:
        print_test("Pod Logs Endpoint", "PASS")
        print_info(f"  Retrieved logs from pod: {data.get('pod_name', 'unknown')}")
        return True
    elif status == 400 or status == 404:
        print_test("Pod Logs Endpoint", "PASS", "Pod not found (expected, K8s integration working)")
        return True
    elif status == 503:
        print_test("Pod Logs Endpoint", "FAIL", "Kubernetes integration not available")
        return False
    else:
        print_test("Pod Logs Endpoint", "FAIL", f"HTTP {status}")
        return False


def test_pod_restart():
    """Test POST /mapi/v1/kubernetes/pod/{pod_name}/restart"""
    print_header("Test 6: Pod Restart (DRY RUN)")

    # Don't actually restart anything - just test endpoint
    pod_name = "test-pod"  # Non-existent pod
    status, data = make_request("POST", f"/mapi/v1/kubernetes/pod/{pod_name}/restart")

    if status == 200:
        print_test("Pod Restart Endpoint", "PASS")
        print_info(f"  Status: {data.get('status', 'unknown')}")
        return True
    elif status == 400 or status == 404:
        print_test("Pod Restart Endpoint", "PASS", "Pod not found (expected, K8s integration working)")
        return True
    elif status == 503:
        print_test("Pod Restart Endpoint", "FAIL", "Kubernetes integration not available")
        return False
    else:
        print_test("Pod Restart Endpoint", "FAIL", f"HTTP {status}")
        return False


def test_metrics():
    """Test GET /mapi/v1/kubernetes/metrics"""
    print_header("Test 7: Metrics")

    status, data = make_request("GET", "/mapi/v1/kubernetes/metrics", params={"metric": "cluster_health"})

    if status == 200:
        print_test("Metrics Endpoint", "PASS")
        print_info(f"  Metric: {data.get('metric', 'unknown')}")
        return True
    elif status == 503:
        print_test("Metrics Endpoint", "FAIL", "Kubernetes integration not available")
        return False
    else:
        print_test("Metrics Endpoint", "FAIL", f"HTTP {status}")
        return False


def test_events():
    """Test GET /mapi/v1/kubernetes/events"""
    print_header("Test 8: Cluster Events")

    status, data = make_request("GET", "/mapi/v1/kubernetes/events")

    if status == 200:
        print_test("Events Endpoint", "PASS")
        events = data.get("events", {})
        count = events.get("count", 0)
        print_info(f"  Events retrieved: {count}")
        return True
    elif status == 503:
        print_test("Events Endpoint", "FAIL", "Kubernetes integration not available")
        return False
    else:
        print_test("Events Endpoint", "FAIL", f"HTTP {status}")
        return False


def test_unauthorized():
    """Test that endpoints reject missing API key"""
    print_header("Security: API Key Validation")

    # Save current API key
    global API_KEY
    original_key = API_KEY

    # Test without API key
    API_KEY = ""
    status, data = make_request("GET", "/mapi/v1/kubernetes/cluster-info")

    # Restore API key
    API_KEY = original_key

    if status == 401:
        print_test("API Key Validation", "PASS", "Correctly rejected request without API key")
        return True
    else:
        print_test("API Key Validation", "FAIL", f"Expected 401, got {status}")
        return False


def run_all_tests():
    """Run all tests"""
    print(f"\n{Colors.BOLD}{Colors.INFO}")
    print("╔" + "="*58 + "╗")
    print("║  UAP Kubernetes Integration API Test Suite           ║")
    print("║  Testing 8 New K8s Endpoints                         ║")
    print("╚" + "="*58 + "╝")
    print(f"{Colors.RESET}")

    print_info(f"Target: {BASE_URL}")
    print_info(f"API Key: {API_KEY[:10]}..." if API_KEY else "API Key: NOT SET")

    # Test health first
    if not test_health_check():
        print(f"\n{Colors.FAIL}✗ Cannot connect to API server. Aborting.{Colors.RESET}")
        return False

    results = []

    # Run all tests
    results.append(("Cluster Info", test_cluster_info()))
    results.append(("Pods Status", test_pods_status()))
    results.append(("Services", test_services()))
    results.append(("Deployments", test_deployments()))
    results.append(("Pod Logs", test_pod_logs()))
    results.append(("Pod Restart", test_pod_restart()))
    results.append(("Metrics", test_metrics()))
    results.append(("Events", test_events()))
    results.append(("API Key Security", test_unauthorized()))

    # Summary
    print_header("Summary")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        print_test(name, "PASS" if result else "FAIL")

    print(f"\n{Colors.BOLD}Overall: {passed}/{total} tests passed{Colors.RESET}\n")

    return passed == total


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test UAP Kubernetes API endpoints")
    parser.add_argument("--api-key", default="", help="API key for authentication")
    parser.add_argument("--host", default="localhost", help="API host (default: localhost)")
    parser.add_argument("--port", type=int, default=8002, help="API port (default: 8002)")

    args = parser.parse_args()

    # Update configuration
    API_KEY = args.api_key
    API_HOST = args.host
    API_PORT = args.port
    BASE_URL = f"http://{API_HOST}:{API_PORT}"

    # Run tests
    success = run_all_tests()

    # Exit with proper code
    sys.exit(0 if success else 1)
