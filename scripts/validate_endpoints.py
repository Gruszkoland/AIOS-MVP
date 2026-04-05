#!/usr/bin/env python3
"""
QuickTest: Validate 23 MAPI v1 Endpoints
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8002/mapi/v1"
HEADERS = {"X-API-Key": ""}  # Empty key for dev

def test_endpoint(method, path, data=None, name=""):
    """Test single endpoint"""
    url = f"{BASE_URL}{path}"
    try:
        if method == "GET":
            resp = requests.get(url, timeout=2)
        elif method == "POST":
            resp = requests.post(url, json=data, timeout=2, headers=HEADERS)
        elif method == "PUT":
            resp = requests.put(url, json=data, timeout=2, headers=HEADERS)
        elif method == "DELETE":
            resp = requests.delete(url, timeout=2, headers=HEADERS)
        
        status_icon = "OK" if resp.status_code < 300 else "WARN" if resp.status_code < 400 else "FAIL"
        print(f"[{status_icon}] {method:4} {path:35} -> {resp.status_code}")
        return resp.status_code < 400
    except Exception as e:
        print(f"[ERROR] {method:4} {path:35} -> {str(e)[:40]}")
        return False

print("[QUICKTEST] Validating 23 MAPI v1 Endpoints")
print("=" * 70)
print()

tests_passed = 0
tests_total = 0

# Health & Status
print("[GROUP 1] Health & Status")
tests_total += 1
if test_endpoint("GET", "/health"):
    tests_passed += 1

tests_total += 1
if test_endpoint("GET", "/status"):
    tests_passed += 1

print()

# Task Delegation
print("[GROUP 2] Task Delegation")
tests_total += 1
if test_endpoint("POST", "/task/delegate", {"task_description": "Test task", "agent_hint": "SAP"}):
    tests_passed += 1

tests_total += 1
if test_endpoint("GET", "/task/list"):
    tests_passed += 1

# Assuming we have a task ID (replacing with sample)
tests_total += 1
if test_endpoint("GET", "/task/sample-task-id"):
    tests_passed += 1

print()

# Genesis Record
print("[GROUP 3] Genesis Record")
tests_total += 1
if test_endpoint("GET",  "/genesis/logs"):
    tests_passed += 1

tests_total += 1
if test_endpoint("GET", "/genesis/export?format=json"):
    tests_passed += 1

print()

# Agent Scores & EBDI
print("[GROUP 4] Agent Scores & EBDI")
tests_total += 1
if test_endpoint("GET", "/agent/scores"):
    tests_passed += 1

tests_total += 1
if test_endpoint("GET", "/agent/Auditor/score"):
    tests_passed += 1

tests_total += 1
if test_endpoint("GET", "/ebdi/telemetry"):
    tests_passed += 1

print()

# Guardian Laws
print("[GROUP 5] Guardian Laws")
tests_total += 1
if test_endpoint("GET", "/guardian/laws"):
    tests_passed += 1

print()

# Checkpoints (RBC)
print("[GROUP 6] Checkpoints (RBC)")
tests_total += 1
if test_endpoint("POST", "/checkpoint/create", {"label": "test-checkpoint"}):
    tests_passed += 1

tests_total += 1
if test_endpoint("GET", "/checkpoint/list"):
    tests_passed += 1

print()

# Crisis & Conflict
print("[GROUP 7] Crisis & Conflict")
tests_total += 1
if test_endpoint("POST", "/crisis/activate", {"reason": "Test"}):
    tests_passed += 1

print()

# Session Management
print("[GROUP 8] Session Management")
tests_total += 1
if test_endpoint("POST", "/session/create", {"user_id": "test-user"}):
    tests_passed += 1

tests_total += 1
if test_endpoint("GET", "/session/previous?user_id=test-user"):
    tests_passed += 1

print()

# Chat Orchestrator
print("[GROUP 9] Chat Orchestrator")
tests_total += 1
if test_endpoint("POST", "/auto-run-startup", {"user_id": "test"}):
    tests_passed += 1

tests_total += 1
if test_endpoint("GET", "/startup/status?user_id=test"):
    tests_passed += 1

print()

# Tasks & Agents Management
print("[GROUP 10] Tasks & Agents Management")
tests_total += 1
if test_endpoint("GET", "/tasks?session_id=default"):
    tests_passed += 1

tests_total += 1
if test_endpoint("GET", "/tasks/stats?session_id=default"):
    tests_passed += 1

tests_total += 1
if test_endpoint("GET", "/agents"):
    tests_passed += 1

print()
print("=" * 70)
print(f"RESULTS: {tests_passed}/{tests_total} endpoints responding")
print()
