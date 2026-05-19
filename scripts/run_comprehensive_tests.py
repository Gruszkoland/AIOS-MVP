#!/usr/bin/env python3
"""
ADRION 369 v4.0 - COMPREHENSIVE TEST SUITE (42 Endpoints)
============================================================
Automated UAT for all 6 MCP agents across ETAP 2 deployment

Date: 2026-04-08
Phase: ETAP 2 Validation
Status: PROD-READY TESTING
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, List, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test configuration
BASE_URLS = {
    "router": "http://localhost:9001",
    "genesis": "http://localhost:9004",
    "guardian": "http://localhost:9002",
    "healer": "http://localhost:9003",
    "oracle": "http://localhost:9005",
    "vortex": "http://localhost:9006"
}

TIMEOUT = 5  # seconds
RESPONSE_TIME_THRESHOLD = 500  # ms (slow threshold)

# Test statistics
test_results = {
    "passed": 0,
    "failed": 0,
    "timeout": 0,
    "total": 0,
    "details": []
}


class TestRunner:
    def __init__(self):
        self.session = requests.Session()
        self.start_time = None
        self.end_time = None

    def check_agent_health(self, agent_name: str, base_url: str) -> bool:
        """Pre-test: Verify agent is responding"""
        try:
            response = self.session.get(f"{base_url}/health", timeout=2)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Agent {agent_name} health check failed: {e}")
            return False

    def test_endpoint(self, agent: str, method: str, endpoint: str,
                     data=None, expected_status: int = 200) -> Dict:
        """Execute single endpoint test"""
        url = f"{BASE_URLS[agent]}{endpoint}"

        try:
            start = time.time()

            if method == "GET":
                response = self.session.get(url, timeout=TIMEOUT)
            elif method == "POST":
                response = self.session.post(url, json=data, timeout=TIMEOUT)
            elif method == "PUT":
                response = self.session.put(url, json=data, timeout=TIMEOUT)
            elif method == "DELETE":
                response = self.session.delete(url, timeout=TIMEOUT)
            else:
                raise ValueError(f"Unknown method: {method}")

            elapsed = (time.time() - start) * 1000  # Convert to ms

            success = response.status_code == expected_status
            slow = elapsed > RESPONSE_TIME_THRESHOLD

            result = {
                "agent": agent,
                "endpoint": endpoint,
                "method": method,
                "status_code": response.status_code,
                "expected_status": expected_status,
                "response_time_ms": round(elapsed, 2),
                "success": success,
                "slow": slow,
                "error": None
            }

            return result

        except requests.Timeout:
            return {
                "agent": agent,
                "endpoint": endpoint,
                "method": method,
                "status_code": 0,
                "expected_status": expected_status,
                "response_time_ms": TIMEOUT * 1000,
                "success": False,
                "slow": True,
                "error": "TIMEOUT"
            }
        except Exception as e:
            return {
                "agent": agent,
                "endpoint": endpoint,
                "method": method,
                "status_code": 0,
                "expected_status": expected_status,
                "response_time_ms": 0,
                "success": False,
                "slow": False,
                "error": str(e)
            }

    def run_test_suite(self) -> Dict:
        """Execute complete 42-endpoint test suite"""
        self.start_time = time.time()

        # Phase 1: Agent Health Checks
        logger.info("="*70)
        logger.info("PHASE 1: AGENT HEALTH CHECKS")
        logger.info("="*70)

        agent_health = {}
        for agent, url in BASE_URLS.items():
            health = self.check_agent_health(agent, url)
            agent_health[agent] = health
            status = "✅ OK" if health else "❌ FAILED"
            logger.info(f"{agent.upper():12} - {status}")

        if not all(agent_health.values()):
            logger.error("Some agents are not responding. Aborting test suite.")
            return {"error": "Agent health check failed"}

        # Phase 2: Core Health/Status Endpoints (4 tests)
        logger.info("\n" + "="*70)
        logger.info("PHASE 2: SYSTEM HEALTH & STATUS (4 endpoints)")
        logger.info("="*70)

        health_tests = [
            ("router", "GET", "/health", None, 200),
            ("router", "GET", "/status", None, 200),
            ("genesis", "GET", "/health", None, 200),
            ("guardian", "GET", "/health", None, 200),
        ]

        for agent, method, endpoint, data, expected in health_tests:
            result = self.test_endpoint(agent, method, endpoint, data, expected)
            self._record_result(result)

        # Phase 3: Genesis-MCP Tests (7 endpoints)
        logger.info("\n" + "="*70)
        logger.info("PHASE 3: GENESIS-MCP - EVENT SOURCING (7 endpoints)")
        logger.info("="*70)

        genesis_tests = [
            ("genesis", "GET", "/events", None, 200),
            ("genesis", "GET", "/state", None, 200),
            ("genesis", "GET", "/history", None, 200),
            ("genesis", "POST", "/replay", {"checkpoint_id": "test"}, 200),
            ("genesis", "GET", "/snapshots", None, 200),
            ("genesis", "POST", "/snapshot", {"aggregate_id": "test"}, 201),
            ("genesis", "GET", "/metrics", None, 200),
        ]

        for agent, method, endpoint, data, expected in genesis_tests:
            result = self.test_endpoint(agent, method, endpoint, data, expected)
            self._record_result(result)

        # Phase 4: Router-MCP Tests (6 endpoints)
        logger.info("\n" + "="*70)
        logger.info("PHASE 4: ROUTER-MCP - ORCHESTRATION (6 endpoints)")
        logger.info("="*70)

        router_tests = [
            ("router", "GET", "/agents", None, 200),
            ("router", "GET", "/status", None, 200),
            ("router", "POST", "/route", {"query": "test", "context": {}}, 200),
            ("router", "GET", "/stats/routing", None, 200),
            ("router", "GET", "/stats/agents", None, 200),
            ("router", "GET", "/traces/recent", None, 200),
        ]

        for agent, method, endpoint, data, expected in router_tests:
            result = self.test_endpoint(agent, method, endpoint, data, expected)
            self._record_result(result)

        # Phase 5: Guardian-MCP Tests (7 endpoints)
        logger.info("\n" + "="*70)
        logger.info("PHASE 5: GUARDIAN-MCP - SECURITY & AUDIT (7 endpoints)")
        logger.info("="*70)

        guardian_tests = [
            ("guardian", "GET", "/audit/logs", None, 200),
            ("guardian", "GET", "/security/check", None, 200),
            ("guardian", "GET", "/threat/assess", None, 200),
            ("guardian", "POST", "/audit/record", {"action": "TEST", "actor": "test"}, 201),
            ("guardian", "GET", "/compliance/status", None, 200),
            ("guardian", "GET", "/encryption/keys", None, 200),
            ("guardian", "GET", "/audit/summary", None, 200),
        ]

        for agent, method, endpoint, data, expected in guardian_tests:
            result = self.test_endpoint(agent, method, endpoint, data, expected)
            self._record_result(result)

        # Phase 6: Healer-MCP Tests (6 endpoints)
        logger.info("\n" + "="*70)
        logger.info("PHASE 6: HEALER-MCP - RECOVERY & DIAGNOSTICS (6 endpoints)")
        logger.info("="*70)

        healer_tests = [
            ("healer", "GET", "/health/diagnose", None, 200),
            ("healer", "POST", "/recovery/plan", {"issue": "test"}, 200),
            ("healer", "POST", "/repair", {"type": "test"}, 200),
            ("healer", "GET", "/diagnostics", None, 200),
            ("healer", "GET", "/services/status", None, 200),
            ("healer", "GET", "/metrics/health", None, 200),
        ]

        for agent, method, endpoint, data, expected in healer_tests:
            result = self.test_endpoint(agent, method, endpoint, data, expected)
            self._record_result(result)

        # Phase 7: Oracle-MCP Tests (8 endpoints)
        logger.info("\n" + "="*70)
        logger.info("PHASE 7: ORACLE-MCP - ANALYTICS & INSIGHTS (8 endpoints)")
        logger.info("="*70)

        oracle_tests = [
            ("oracle", "GET", "/analytics/metrics", None, 200),
            ("oracle", "GET", "/insights/trends", None, 200),
            ("oracle", "POST", "/forecasts", {"model": "test"}, 200),
            ("oracle", "GET", "/reports/summary", None, 200),
            ("oracle", "GET", "/performance/stats", None, 200),
            ("oracle", "GET", "/kpi/dashboard", None, 200),
            ("oracle", "POST", "/analysis/run", {"type": "test"}, 200),
            ("oracle", "GET", "/data/quality", None, 200),
        ]

        for agent, method, endpoint, data, expected in oracle_tests:
            result = self.test_endpoint(agent, method, endpoint, data, expected)
            self._record_result(result)

        # Phase 8: Vortex-MCP Tests (8 endpoints)
        logger.info("\n" + "="*70)
        logger.info("PHASE 8: VORTEX-MCP - HARMONIC ORCHESTRATION (8 endpoints)")
        logger.info("="*70)

        vortex_tests = [
            ("vortex", "GET", "/health", None, 200),
            ("vortex", "POST", "/canary/deploy", {"backend": "test", "percent": 5}, 200),
            ("vortex", "GET", "/logs/test", None, 200),
            ("vortex", "GET", "/monitor/harmonic", None, 200),
            ("vortex", "GET", "/status", None, 200),
            ("vortex", "GET", "/deployment/status", None, 200),
            ("vortex", "GET", "/rollout/metrics", None, 200),
            ("vortex", "POST", "/alert/test", {"message": "test"}, 201),
        ]

        for agent, method, endpoint, data, expected in vortex_tests:
            result = self.test_endpoint(agent, method, endpoint, data, expected)
            self._record_result(result)

        self.end_time = time.time()
        return test_results

    def _record_result(self, result: Dict):
        """Record test result"""
        test_results["total"] += 1

        if result["error"] == "TIMEOUT":
            test_results["timeout"] += 1
            status = "⏱️  TIMEOUT"
        elif result["success"]:
            test_results["passed"] += 1
            status = "✅ PASS"
        else:
            test_results["failed"] += 1
            status = "❌ FAIL"

        slow_indicator = " 🐢 SLOW" if result["slow"] else ""

        log_line = f"{status}{slow_indicator} | {result['agent'].upper():10} | {result['endpoint']:30} | " \
                  f"[{result['status_code']} vs {result['expected_status']}] | {result['response_time_ms']}ms"

        logger.info(log_line)
        test_results["details"].append(result)


def print_summary(runner: TestRunner, results: Dict):
    """Print test summary"""
    duration = runner.end_time - runner.start_time

    print("\n" + "="*70)
    print("TEST SUMMARY REPORT")
    print("="*70 + "\n")

    print(f"Total Tests: {results['total']}")
    print(f"Passed: {results['passed']} ✅")
    print(f"Failed: {results['failed']} ❌")
    print(f"Timeout: {results['timeout']} ⏱️")
    print(f"Duration: {duration:.2f}s\n")

    pass_rate = (results['passed'] / results['total'] * 100) if results['total'] > 0 else 0
    print(f"Success Rate: {pass_rate:.1f}%\n")

    # Slow endpoints
    slow_endpoints = [r for r in results['details'] if r['slow']]
    if slow_endpoints:
        print("Slow Endpoints (>500ms):")
        for r in slow_endpoints:
            print(f"  - {r['agent'].upper():10} {r['endpoint']:30} ({r['response_time_ms']}ms)")

    # Failed endpoints
    failed_endpoints = [r for r in results['details'] if not r['success']]
    if failed_endpoints:
        print("\nFailed Endpoints:")
        for r in failed_endpoints:
            error_info = f" - {r['error']}" if r['error'] else f" - Expected {r['expected_status']}, got {r['status_code']}"
            print(f"  - {r['agent'].upper():10} {r['endpoint']:30}{error_info}")

    print("\n" + "="*70)
    if pass_rate >= 90:
        print("✅ TEST SUITE PASSED - Ready for production deployment")
    elif pass_rate >= 70:
        print("🟡 TEST SUITE PARTIAL - Some issues detected")
    else:
        print("❌ TEST SUITE FAILED - Critical issues detected")
    print("="*70 + "\n")


def generate_json_report(results: Dict, filename: str):
    """Generate JSON test report"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "phase": "ETAP2_VALIDATION",
        "summary": {
            "total": results['total'],
            "passed": results['passed'],
            "failed": results['failed'],
            "timeout": results['timeout'],
            "success_rate": f"{results['passed']/results['total']*100:.1f}%" if results['total'] > 0 else "0%"
        },
        "test_details": results['details']
    }

    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"JSON report saved to: {filename}")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("ADRION 369 v4.0 - COMPREHENSIVE TEST SUITE (42 Endpoints)")
    print("="*70 + "\n")

    runner = TestRunner()
    results = runner.run_test_suite()

    if "error" not in results:
        print_summary(runner, results)

        # Save JSON report
        report_file = f"TEST_RESULTS_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        generate_json_report(results, report_file)
    else:
        logger.error(f"Test suite error: {results['error']}")
        sys.exit(1)
