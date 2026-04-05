#!/usr/bin/env python3
"""
UAP Integration Test Suite — All 23 MAPI v1 Endpoints
Automatyczna walidacja całego systemu lokalnego.
"""

import json
import time
import requests
import sys
from datetime import datetime
from pathlib import Path

API_BASE = "http://localhost:8002/mapi/v1"
API_KEY = "local-dev-key-123"
TIMEOUT = 5

# ANSI Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

class TestRunner:
    """Integration test runner dla UAP endpoints."""
    
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
        self.start_time = time.time()
    
    def test(self, name, method, endpoint, expected_status=200, data=None, headers=None):
        """Run single endpoint test."""
        url = f"{API_BASE}{endpoint}"
        default_headers = {
            "X-API-Key": API_KEY,
            "Content-Type": "application/json"
        }
        if headers:
            default_headers.update(headers)
        
        try:
            if method == "GET":
                resp = requests.get(url, headers=default_headers, timeout=TIMEOUT)
            elif method == "POST":
                resp = requests.post(url, json=data or {}, headers=default_headers, timeout=TIMEOUT)
            elif method == "PUT":
                resp = requests.put(url, json=data or {}, headers=default_headers, timeout=TIMEOUT)
            else:
                self.log_result(name, False, "Unknown method")
                return
            
            success = resp.status_code == expected_status
            if success:
                self.passed += 1
                self.log_result(name, True, f"Status {resp.status_code}")
            else:
                self.failed += 1
                self.log_result(name, False, f"Expected {expected_status}, got {resp.status_code}")
            
            self.results.append({
                "name": name,
                "endpoint": endpoint,
                "method": method,
                "status": resp.status_code,
                "success": success,
                "response_size": len(resp.text),
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            self.failed += 1
            self.log_result(name, False, str(e))
            self.results.append({
                "name": name,
                "endpoint": endpoint,
                "method": method,
                "error": str(e),
                "success": False,
                "timestamp": datetime.now().isoformat()
            })
    
    def log_result(self, name, success, detail):
        """Print test result."""
        symbol = f"{GREEN}✅{RESET}" if success else f"{RED}❌{RESET}"
        print(f"  {symbol} {name:45s} | {detail}")
    
    def run_all_tests(self):
        """Execute all 23 MAPI v1 endpoint tests."""
        print(f"{CYAN}{'='*80}{RESET}")
        print(f"{CYAN}🧪 UAP INTEGRATION TEST SUITE{RESET}")
        print(f"{CYAN}{'='*80}{RESET}\n")
        
        # GROUP 1: Health & Status (3 endpoints)
        print(f"{YELLOW}📌 GROUP 1: Health & Status{RESET}")
        self.test("Health Check", "GET", "/health", 200)
        self.test("API Status", "GET", "/status", 200)
        self.test("System Info", "GET", "/system/info", 200)
        
        # GROUP 2: Task Management (4 endpoints)
        print(f"\n{YELLOW}📌 GROUP 2: Task Management (4){RESET}")
        self.test("Delegate Task", "POST", "/task/delegate", 201, {
            "task_type": "analysis",
            "parameters": {"data": "test"}
        })
        self.test("List Tasks", "GET", "/task/list", 200)
        self.test("Task Status (nonexistent)", "GET", "/task/status/test-nonexistent", 404)
        self.test("Abort Task", "POST", "/task/abort", 404)
        
        # GROUP 3: Agent Management (4 endpoints)
        print(f"\n{YELLOW}📌 GROUP 3: Agent Management (4){RESET}")
        self.test("Get Agent Scores (TSPA)", "GET", "/agent/scores", 200)
        self.test("Get Agent Status", "GET", "/agent/status", 200)
        self.test("Get EBDI States", "GET", "/agent/ebdi", 200)
        self.test("List All Agents", "GET", "/agent/list", 200)
        
        # GROUP 4: Genesis Record (3 endpoints)
        print(f"\n{YELLOW}📌 GROUP 4: Genesis Record (3){RESET}")
        self.test("Query Genesis Records", "GET", "/genesis/query", 200)
        self.test("Search Reports", "GET", "/genesis/search?query=task", 200)
        self.test("Export Report", "GET", "/genesis/export", 200)
        
        # GROUP 5: Orchestrator Control (3 endpoints)
        print(f"\n{YELLOW}📌 GROUP 5: Orchestrator Control (3){RESET}")
        self.test("Get Orchestrator State", "GET", "/orchestrator/state", 200)
        self.test("Get Decision Space", "GET", "/orchestrator/162d", 200)
        self.test("Get Guardian Laws", "GET", "/orchestrator/laws", 200)
        
        # GROUP 6: Crisis & Monitoring (2 endpoints)
        print(f"\n{YELLOW}📌 GROUP 6: Crisis & Monitoring (2){RESET}")
        self.test("Check Crisis Status", "GET", "/crisis/status", 200)
        self.test("Get Live Telemetry", "GET", "/telemetry/live", 200)
        
        # GROUP 7: Admin & System (2 endpoints)
        print(f"\n{YELLOW}📌 GROUP 7: Admin & System (2){RESET}")
        self.test("System Diagnostics", "GET", "/admin/diagnostics", 200)
        self.test("System Metrics", "GET", "/admin/metrics", 200)
        
        # Additional: Chat/Orchestrator (2 endpoints)
        print(f"\n{YELLOW}📌 GROUP 8: Chat & Orchestration (2){RESET}")
        self.test("Master Orchestrator Chat", "POST", "/chat/orchestrator", 200, {
            "message": "hello"
        })
        self.test("Delegate to Sub-agent", "POST", "/chat/delegate", 200, {
            "agent": "auditor",
            "task": "verify"
        })
        
        # Final Summary
        print(f"\n{CYAN}{'='*80}{RESET}")
        elapsed = time.time() - self.start_time
        total = self.passed + self.failed
        
        if self.failed == 0:
            status_color = GREEN
            status_symbol = "✅"
        else:
            status_color = RED
            status_symbol = "⚠️"
        
        print(f"{status_color}{status_symbol} TEST RESULTS{RESET}")
        print(f"{CYAN}{'='*80}{RESET}")
        print(f"  {GREEN}Passed:  {self.passed}/{total}{RESET}")
        print(f"  {RED if self.failed > 0 else GREEN}Failed:  {self.failed}/{total}{RESET}")
        print(f"  Time:    {elapsed:.2f}s")
        print(f"  Success: {100*self.passed/total:.1f}%")
        print()
        
        # Save results
        self.save_results()
        
        return self.failed == 0
    
    def save_results(self):
        """Save test results to file."""
        output_file = Path("logs/integration_test_results.json")
        output_file.parent.mkdir(exist_ok=True)
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": self.passed + self.failed,
            "passed": self.passed,
            "failed": self.failed,
            "success_rate": 100 * self.passed / (self.passed + self.failed) if self.passed + self.failed > 0 else 0,
            "duration_seconds": time.time() - self.start_time,
            "results": self.results
        }
        
        with open(output_file, "w") as f:
            json.dump(summary, f, indent=2)
        
        print(f"📊 Results saved to: {output_file}")

if __name__ == "__main__":
    runner = TestRunner()
    success = runner.run_all_tests()
    sys.exit(0 if success else 1)
