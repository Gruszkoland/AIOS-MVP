#!/usr/bin/env python3
"""
ADRION 369 Integration Test Suite
Tests all 23 MAPI v1 endpoints with live backend validation
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:8002/mapi/v1"
API_KEY = "local-dev-key-123"
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []
    
    def test(self, name, method, endpoint, data=None, expected_status=200):
        """Run single test"""
        url = f"{BASE_URL}{endpoint}"
        try:
            if method == "GET":
                resp = requests.get(url, headers=HEADERS, timeout=5)
            elif method == "POST":
                resp = requests.post(url, json=data, headers=HEADERS, timeout=5)
            elif method == "PUT":
                resp = requests.put(url, json=data, headers=HEADERS, timeout=5)
            
            success = resp.status_code == expected_status
            status = "PASS" if success else "FAIL"
            
            if success:
                self.passed += 1
            else:
                self.failed += 1
            
            self.tests.append({
                "name": name,
                "endpoint": endpoint,
                "status": status,
                "code": resp.status_code,
                "expected": expected_status
            })
            
            print(f"[{status}] {name:40} -> {resp.status_code}")
            return resp
        except Exception as e:
            self.failed += 1
            self.tests.append({
                "name": name,
                "endpoint": endpoint,
                "status": "ERROR",
                "error": str(e)
            })
            print(f"[ERROR] {name:40} -> {str(e)[:50]}")
            return None
    
    def summary(self):
        print("\n" + "=" * 70)
        print(f"TEST RESULTS: {self.passed} PASSED, {self.failed} FAILED")
        print("=" * 70)
        
        for test in self.tests:
            if test["status"] == "PASS":
                print(f"  ✓ {test['name']}")
            elif test["status"] == "FAIL":
                print(f"  ✗ {test['name']} (got {test['code']}, expected {test['expected']})")
            else:
                print(f"  ✗ {test['name']} ({test.get('error', 'unknown error')})")

runner = TestRunner()

print("ADRION 369 INTEGRATION TEST SUITE")
print("=" * 70)
print()

# GROUP 1: Health & Status (2 tests)
print("[GROUP 1] Health & Status")
runner.test("Health Check", "GET", "/health", expected_status=200)
runner.test("System Status", "GET", "/status", expected_status=200)
print()

# GROUP 2: Task Management (3 tests)
print("[GROUP 2] Task Management")
task_resp = runner.test("Task Delegation", "POST", "/task/delegate", 
    {"task_description": "Integration test task", "agent_hint": "Architect"},
    expected_status=201)

if task_resp and task_resp.status_code == 201:
    task_id = task_resp.json().get("task_id")
    time.sleep(1)  # Let async task complete
    runner.test("Get Task Status", "GET", f"/task/{task_id}", expected_status=200)
    runner.test("List Tasks", "GET", "/task/list", expected_status=200)
else:
    runner.test("Get Task Status", "GET", "/task/dummy-id", expected_status=404)
    runner.test("List Tasks", "GET", "/task/list", expected_status=200)
print()

# GROUP 3: Genesis Record (2 tests)
print("[GROUP 3] Genesis Record Audit Trail")
runner.test("Query Genesis Logs", "GET", "/genesis/logs", expected_status=200)
runner.test("Export Genesis Records", "GET", "/genesis/export?format=json", expected_status=200)
print()

# GROUP 4: Agent Management (3 tests)
print("[GROUP 4] Agent Management")
runner.test("List Agent Scores", "GET", "/agent/scores", expected_status=200)
runner.test("Get Single Agent Score", "GET", "/agent/Auditor/score", expected_status=200)
runner.test("Get Unknown Agent", "GET", "/agent/InvalidAgent/score", expected_status=404)
print()

# GROUP 5: EBDI Telemetry (1 test)
print("[GROUP 5] EBDI Telemetry")
runner.test("Get Live EBDI Telemetry", "GET", "/ebdi/telemetry", expected_status=200)
print()

# GROUP 6: Guardian Laws (1 test)
print("[GROUP 6] Guardian Laws Compliance")
runner.test("Get Guardian Laws", "GET", "/guardian/laws", expected_status=200)
print()

# GROUP 7: Checkpoints (2 tests)
print("[GROUP 7] Checkpoints (RBC [3])")
cp_resp = runner.test("Create Checkpoint", "POST", "/checkpoint/create",
    {"label": "integration-test-checkpoint"},
    expected_status=201)
runner.test("List Checkpoints", "GET", "/checkpoint/list", expected_status=200)
print()

# GROUP 8: Crisis Management (1 test)
print("[GROUP 8] Crisis Management")
runner.test("Activate Crisis Mode", "POST", "/crisis/activate",
    {"reason": "Integration test"},
    expected_status=200)
print()

# GROUP 9: Session Management (3 tests)
print("[GROUP 9] Session Management")
session_resp = runner.test("Create Session", "POST", "/session/create",
    {"user_id": "test-user-123"},
    expected_status=201)
runner.test("Get Previous Sessions", "GET", "/session/previous?user_id=test-user-123", expected_status=200)
if session_resp and session_resp.status_code == 201:
    session_id = session_resp.json().get("session_id")
    runner.test("Get Session", "GET", f"/session/{session_id}", expected_status=200)
else:
    runner.test("Get Session", "GET", "/session/dummy-session", expected_status=404)
print()

# GROUP 10: Conflict Resolver (1 test)
print("[GROUP 10] Conflict Resolution")
runner.test("Resolve Conflict", "POST", "/conflict/resolve",
    {
        "proposals": [
            {"agent": "Architect", "proposal": "Solution A", "confidence": 0.9},
            {"agent": "Auditor", "proposal": "Solution B", "confidence": 0.8}
        ]
    },
    expected_status=200)
print()

# GROUP 11: Tasks & Agents Dashboard (3 tests)
print("[GROUP 11] Dashboard Endpoints")
runner.test("Get Active Tasks", "GET", "/tasks?session_id=default", expected_status=200)
runner.test("Get Task Statistics", "GET", "/tasks/stats?session_id=default", expected_status=200)
runner.test("List Agents", "GET", "/agents", expected_status=200)
print()

# Final summary
runner.summary()

# Write results to file
with open("integration_test_results.json", "w") as f:
    json.dump({
        "timestamp": datetime.now().isoformat(),
        "passed": runner.passed,
        "failed": runner.failed,
        "total": len(runner.tests),
        "tests": runner.tests
    }, f, indent=2)

print()
print(f"Results saved to: integration_test_results.json")
