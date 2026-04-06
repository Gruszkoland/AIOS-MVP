"""
UAP Integration Test Suite
Tests all 23 MAPI v1 endpoints + health checks
"""
import json
import sys
import time
import requests
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

# Configuration
API_BASE = "http://localhost:8002/mapi/v1"
FRONTEND_BASE = "http://127.0.0.1:8003"
TIMEOUT = 30  # Increased from 10 to 30 for slow backends

# Test results tracking
PASSED = []
FAILED = []
SKIPPED = []


class Colors:
    """ANSI color codes for terminal output (disabled on Windows for compatibility)"""
    GREEN = ""
    RED = ""
    YELLOW = ""
    BLUE = ""
    CYAN = ""
    RESET = ""
    BOLD = ""


def log_info(msg: str):
    print(f"[INFO] {msg}")


def log_success(msg: str):
    print(f"[PASS] {msg}")


def log_error(msg: str):
    print(f"[FAIL] {msg}")


def log_warn(msg: str):
    print(f"[WARN] {msg}")


def banner(text: str):
    print(f"\n{'=' * 70}")
    print(f"  {text}")
    print(f"{'=' * 70}\n")


def test_endpoint(method: str, endpoint: str, expected_status: int = 200,
                 json_data: Dict = None, params: Dict = None) -> Tuple[bool, str]:
    """Test a single API endpoint."""
    url = f"{API_BASE}{endpoint}"
    try:
        if method == "GET":
            resp = requests.get(url, params=params, timeout=TIMEOUT)
        elif method == "POST":
            resp = requests.post(url, json=json_data, timeout=TIMEOUT)
        elif method == "PUT":
            resp = requests.put(url, json=json_data, timeout=TIMEOUT)
        elif method == "DELETE":
            resp = requests.delete(url, timeout=TIMEOUT)
        else:
            return False, f"Unknown method: {method}"

        if resp.status_code == expected_status:
            return True, f"{method} {endpoint} → {resp.status_code}"
        else:
            return False, f"{method} {endpoint} → {resp.status_code} (expected {expected_status})"
    except requests.ConnectionError:
        return False, f"Connection failed: {endpoint}"
    except requests.Timeout:
        return False, f"Timeout: {endpoint}"
    except Exception as e:
        return False, f"Error: {type(e).__name__}: {str(e)[:50]}"


def run_test(name: str, method: str, endpoint: str, expected_status: int = 200,
            json_data: Dict = None, params: Dict = None) -> bool:
    """Run a test and track results."""
    success, message = test_endpoint(method, endpoint, expected_status, json_data, params)
    if success:
        log_success(message)
        PASSED.append(name)
        return True
    else:
        log_error(message)
        FAILED.append(name)
        return False


def main():
    banner("UAP Integration Test Suite - All 23 MAPI v1 Endpoints")

    # Pre-flight checks
    log_info("Checking service availability...")
    try:
        resp = requests.get(f"{API_BASE}/health", timeout=30)
        if resp.status_code == 200:
            log_success("Backend API is responsive")
        else:
            log_error(f"Backend returned status {resp.status_code}")
            return False
    except Exception as e:
        log_error(f"Backend not available: {e}")
        return False

    try:
        resp = requests.get(FRONTEND_BASE, timeout=30)
        if resp.status_code == 200:
            log_success("Frontend is responsive")
        else:
            log_warn(f"Frontend returned status {resp.status_code}")
    except Exception as e:
        log_warn(f"Frontend not available: {e}")

    time.sleep(1)

    # ========================================================================
    # PHASE 1: Core Health & Status Endpoints (3 tests)
    # ========================================================================
    banner("PHASE 1: Core Health & Status Endpoints (3 tests)")

    run_test("Health Check", "GET", "/health")
    run_test("Status Endpoint", "GET", "/status")
    run_test("Version Info", "GET", "/version", 200)

    # ========================================================================
    # PHASE 2: Agent Management Endpoints (6 tests)
    # ========================================================================
    banner("PHASE 2: Agent Management Endpoints (6 tests)")

    run_test("List All Agents", "GET", "/agents")
    run_test("Get Agent Scores", "GET", "/agent/scores")
    run_test("Get Agent Score (librarian)", "GET", "/agent/librarian/score")
    run_test("Update Trust Score", "POST", "/agent/librarian/score/update",
            json_data={"new_score": 0.85})
    run_test("List Agent Metrics", "GET", "/agent/metrics")
    run_test("Get EBDI State", "GET", "/agent/librarian/ebdi")

    # ========================================================================
    # PHASE 3: Task Management Endpoints (5 tests)
    # ========================================================================
    banner("PHASE 3: Task Management Endpoints (5 tests)")

    task_payload = {
        "description": "Test task for integration suite",
        "assigned_agent": "librarian",
        "dry_run": False,
        "budget_max": 100
    }

    run_test("Submit New Task", "POST", "/task/submit",
            json_data=task_payload)
    run_test("List Tasks", "GET", "/tasks")
    run_test("Query Tasks (status filter)", "GET", "/tasks/query",
            params={"status": "submitted"})
    run_test("Get Task Details", "GET", "/task/test-task-001", 404)  # Expect 404
    run_test("Update Task Status", "PUT", "/task/test-task-001/status", 404,
            json_data={"status": "in-progress"})

    # ========================================================================
    # PHASE 4: Genesis Record Endpoints (3 tests)
    # ========================================================================
    banner("PHASE 4: Genesis Record Endpoints (3 tests)")

    run_test("Query Genesis Logs", "GET", "/genesis/logs")
    run_test("Get Genesis Summary", "GET", "/genesis/summary")
    run_test("Export Genesis Records", "GET", "/genesis/export/all")

    # ========================================================================
    # PHASE 5: EBDI Telemetry Endpoints (3 tests)
    # ========================================================================
    banner("PHASE 5: EBDI Telemetry Endpoints (3 tests)")

    run_test("Get Live Telemetry", "GET", "/telemetry/live")
    run_test("Get EBDI Baseline", "GET", "/ebdi/baseline")
    run_test("Update EBDI State", "POST", "/ebdi/update",
            json_data={"agent": "librarian", "pleasure": 0.5, "arousal": 0.3, "dominance": 0.7})

    # ========================================================================
    # PHASE 6: Checkpoint Management Endpoints (2 tests)
    # ========================================================================
    banner("PHASE 6: Checkpoint Management Endpoints (2 tests)")

    run_test("List Checkpoints", "GET", "/checkpoint/list")
    run_test("Create Checkpoint", "POST", "/checkpoint/create",
            json_data={
                "label": "Test checkpoint",
                "git_commit": "abc123def456",
                "session_state": {"test": "data"}
            })

    # ========================================================================
    # PHASE 7: System Info Endpoints (1 test)
    # ========================================================================
    banner("PHASE 7: System Info Endpoints (1 test)")

    run_test("System Information", "GET", "/system/info")

    # ========================================================================
    # Results Summary
    # ========================================================================
    banner("TEST RESULTS SUMMARY")

    total = len(PASSED) + len(FAILED) + len(SKIPPED)
    pass_rate = (len(PASSED) / total * 100) if total > 0 else 0

    print(f"Total Tests:  {total}")
    print(f"Passed:       {len(PASSED)}")
    print(f"Failed:       {len(FAILED)}")
    print(f"Skipped:      {len(SKIPPED)}")
    print(f"Pass Rate:    {pass_rate:.1f}%")

    if FAILED:
        print(f"\nFailed Tests:")
        for name in FAILED:
            print(f"  - {name}")

    # Return exit code based on results
    return len(FAILED) == 0


if __name__ == "__main__":
    banner("STARTING INTEGRATION TEST SUITE")

    success = main()

    banner("TEST SUITE COMPLETE")

    sys.exit(0 if success else 1)
