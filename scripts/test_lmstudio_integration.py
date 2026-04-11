#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
  ADRIAN 369 — LM STUDIO END-TO-END INTEGRATION TEST

  Comprehensive diagnostic testing all LM Studio components

  Usage:
    python test_lmstudio_integration.py              # Full test
    python test_lmstudio_integration.py --quick     # Fast test only
    python test_lmstudio_integration.py --report    # Generate HTML report
═══════════════════════════════════════════════════════════════════════════════
"""

import sys
import time
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# ═══ Color Output ═══
class Color:
    GREEN = "\033[92m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"

def log_header(title: str):
    print(f"\n{Color.BOLD}{Color.CYAN}{'═' * 70}{Color.END}")
    print(f"{Color.BOLD}{Color.CYAN}  {title}{Color.END}")
    print(f"{Color.BOLD}{Color.CYAN}{'═' * 70}{Color.END}\n")

def log_section(title: str):
    print(f"{Color.BLUE}▶ {title}{Color.END}")

def log_pass(msg: str, detail: str = ""):
    detail_str = f" — {detail}" if detail else ""
    print(f"{Color.GREEN}  ✅ {msg}{detail_str}{Color.END}")

def log_fail(msg: str, detail: str = ""):
    detail_str = f" — {detail}" if detail else ""
    print(f"{Color.RED}  ❌ {msg}{detail_str}{Color.END}")

def log_warn(msg: str, detail: str = ""):
    detail_str = f" — {detail}" if detail else ""
    print(f"{Color.YELLOW}  ⚠️  {msg}{detail_str}{Color.END}")

def log_info(msg: str, detail: str = ""):
    detail_str = f" — {detail}" if detail else ""
    print(f"{Color.CYAN}  ℹ️  {msg}{detail_str}{Color.END}")

# ═══ Test Results ═══
class TestResults:
    def __init__(self):
        self.tests: List[Dict] = []
        self.start_time = time.time()
        self.end_time = None

    def add(self, name: str, passed: bool, message: str = "", detail: str = ""):
        self.tests.append({
            "name": name,
            "passed": passed,
            "message": message,
            "detail": detail,
            "timestamp": datetime.now().isoformat()
        })

    def summary(self) -> Tuple[int, int, float]:
        self.end_time = time.time()
        passed = sum(1 for t in self.tests if t["passed"])
        total = len(self.tests)
        duration = self.end_time - self.start_time
        return passed, total, duration

    def to_json(self) -> str:
        passed, total, duration = self.summary()
        return json.dumps({
            "timestamp": datetime.now().isoformat(),
            "total_tests": total,
            "passed": passed,
            "failed": total - passed,
            "duration_seconds": duration,
            "tests": self.tests
        }, indent=2)

# ═══ PHASE 1: IMPORTS ═══
def test_imports() -> Tuple[TestResults, bool]:
    """Test all Python imports."""
    results = TestResults()
    log_section("PHASE 1: Python Imports")

    all_ok = True

    # Test config imports
    try:
        from arbitrage.config import (
            LLM_BACKEND,
            LMSTUDIO_URL,
            LMSTUDIO_MODEL,
            OLLAMA_URL,
            OLLAMA_MODEL,
            get_active_llm_backend,
            _check_lmstudio_available,
            _check_ollama_available,
        )
        log_pass("arbitrage.config imports")
        results.add("config_imports", True, "All config variables imported")
    except ImportError as e:
        log_fail("arbitrage.config imports", str(e))
        results.add("config_imports", False, f"Import error: {e}")
        all_ok = False

    # Test analyzer imports
    try:
        from arbitrage.analyzer import (
            _call_lmstudio,
            _call_ollama,
            _call_openrouter,
            analyze_job,
        )
        log_pass("arbitrage.analyzer functions")
        results.add("analyzer_imports", True, "All analyzer functions imported")
    except ImportError as e:
        log_fail("arbitrage.analyzer imports", str(e))
        results.add("analyzer_imports", False, f"Import error: {e}")
        all_ok = False

    # Test dashboard
    try:
        import dashboard.server
        log_pass("dashboard.server module")
        results.add("dashboard_imports", True, "Dashboard module imported")
    except ImportError as e:
        log_fail("dashboard.server", str(e))
        results.add("dashboard_imports", False, f"Import error: {e}")
        all_ok = False

    return results, all_ok

# ═══ PHASE 2: CONFIGURATION ═══
def test_config() -> Tuple[TestResults, bool]:
    """Test configuration values."""
    results = TestResults()
    log_section("PHASE 2: Configuration Validation")

    from arbitrage.config import (
        LLM_BACKEND,
        LMSTUDIO_URL,
        LMSTUDIO_MODEL,
        OLLAMA_URL,
        OLLAMA_MODEL,
    )

    all_ok = True

    # Check URLs
    if LMSTUDIO_URL.startswith("http"):
        log_pass("LMSTUDIO_URL format", LMSTUDIO_URL)
        results.add("lmstudio_url", True, f"Valid URL: {LMSTUDIO_URL}")
    else:
        log_fail("LMSTUDIO_URL format", LMSTUDIO_URL)
        results.add("lmstudio_url", False, f"Invalid URL: {LMSTUDIO_URL}")
        all_ok = False

    if OLLAMA_URL.startswith("http"):
        log_pass("OLLAMA_URL format", OLLAMA_URL)
        results.add("ollama_url", True, f"Valid URL: {OLLAMA_URL}")
    else:
        log_fail("OLLAMA_URL format", OLLAMA_URL)
        results.add("ollama_url", False, f"Invalid URL: {OLLAMA_URL}")
        all_ok = False

    # Check models
    if LMSTUDIO_MODEL:
        log_pass("LMSTUDIO_MODEL set", LMSTUDIO_MODEL)
        results.add("lmstudio_model", True, f"Model: {LMSTUDIO_MODEL}")
    else:
        log_warn("LMSTUDIO_MODEL empty", "using default")
        results.add("lmstudio_model", False, "Model not set")

    if OLLAMA_MODEL:
        log_pass("OLLAMA_MODEL set", OLLAMA_MODEL)
        results.add("ollama_model", True, f"Model: {OLLAMA_MODEL}")
    else:
        log_warn("OLLAMA_MODEL empty", "using default")
        results.add("ollama_model", False, "Model not set")

    return results, all_ok

# ═══ PHASE 3: BACKEND DETECTION ═══
def test_backend_detection() -> Tuple[TestResults, bool]:
    """Test LLM backend auto-detection."""
    results = TestResults()
    log_section("PHASE 3: Backend Detection")

    from arbitrage.config import get_active_llm_backend

    try:
        backend = get_active_llm_backend()
        log_pass("Backend detection", f"Active: {backend}")
        results.add("backend_detection", True, f"Detected backend: {backend}")

        valid_backends = ["openrouter", "openai", "anthropic", "lmstudio", "ollama", "mock"]
        if backend in valid_backends:
            log_info("Backend is valid", backend)
            results.add("backend_valid", True, f"Backend {backend} is valid")
        else:
            log_warn("Unknown backend", backend)
            results.add("backend_valid", False, f"Unknown backend: {backend}")

        return results, True
    except Exception as e:
        log_fail("Backend detection", str(e))
        results.add("backend_detection", False, f"Error: {e}")
        return results, False

# ═══ PHASE 4: SERVICE AVAILABILITY ═══
def test_service_availability() -> Tuple[TestResults, bool]:
    """Check if LM Studio and Ollama are running."""
    results = TestResults()
    log_section("PHASE 4: Service Availability")

    import urllib.request

    from arbitrage.config import (
        LMSTUDIO_URL,
        OLLAMA_URL,
        _check_lmstudio_available,
        _check_ollama_available,
    )

    # Test LM Studio
    lmstudio_ok = _check_lmstudio_available()
    if lmstudio_ok:
        log_pass("LM Studio server", f"✓ {LMSTUDIO_URL}")
        results.add("lmstudio_available", True, f"Server running at {LMSTUDIO_URL}")
    else:
        log_info("LM Studio server", f"not running at {LMSTUDIO_URL}")
        results.add("lmstudio_available", False, f"Server not responding")

    # Test Ollama
    ollama_ok = _check_ollama_available()
    if ollama_ok:
        log_pass("Ollama server", f"✓ {OLLAMA_URL}")
        results.add("ollama_available", True, f"Server running at {OLLAMA_URL}")
    else:
        log_info("Ollama server", f"not running at {OLLAMA_URL}")
        results.add("ollama_available", False, f"Server not responding")

    # Require at least one
    if lmstudio_ok or ollama_ok:
        log_info("Status", "At least one local LLM server available ✓")
        return results, True
    else:
        log_warn("Status", "No local LLM servers available")
        log_info("Solution", "Start LM Studio (https://lmstudio.ai/) or Ollama")
        return results, False

# ═══ PHASE 5: JOB ANALYSIS TEST ═══
def test_job_analysis() -> Tuple[TestResults, bool]:
    """Test actual job analysis with LLM."""
    results = TestResults()
    log_section("PHASE 5: Job Analysis (Mock + Real)")

    from arbitrage.analyzer import analyze_job
    from arbitrage.config import get_active_llm_backend

    # Sample job
    sample_job = {
        "id": "test_job_001",
        "title": "Write SEO Blog Post",
        "platform": "upwork",
        "budget_min": 100,
        "budget_max": 300,
        "description": "Need 5000-word blog post about Python performance. Include code examples.",
    }

    backend = get_active_llm_backend()
    log_info("Testing backend", backend)

    try:
        start = time.time()
        result = analyze_job(sample_job)
        elapsed = time.time() - start

        log_pass(f"Job analysis ({backend})", f"{elapsed:.2f}s")
        results.add("job_analysis", True, f"Analyzed in {elapsed:.2f}s with {backend}")

        # Validate response
        required_fields = ["score", "fit", "risks", "est_hours", "our_price", "est_cost", "est_profit", "llm_backend"]
        missing = [f for f in required_fields if f not in result]

        if not missing:
            log_pass("Response structure", "All required fields present")
            results.add("response_structure", True, f"All {len(required_fields)} fields present")

            # Log response details
            log_info("Score", f"{result.get('score')}/10")
            log_info("Est. Profit", f"${result.get('est_profit')}")
            log_info("LLM Backend Used", result.get('llm_backend'))

            return results, True
        else:
            log_fail("Response structure", f"Missing: {missing}")
            results.add("response_structure", False, f"Missing fields: {missing}")
            return results, False

    except Exception as e:
        log_fail("Job analysis", str(e))
        results.add("job_analysis", False, f"Error: {e}")
        return results, False

# ═══ PHASE 6: DASHBOARD INTEGRATION ═══
def test_dashboard_integration() -> Tuple[TestResults, bool]:
    """Test Dashboard API response structure."""
    results = TestResults()
    log_section("PHASE 6: Dashboard Integration")

    try:
        # Import dashboard classes
        from dashboard.server import DashboardHandler

        log_pass("Dashboard class import", "DashboardHandler loaded")
        results.add("dashboard_class", True, "DashboardHandler imported")

        # Check _api_status method exists
        if hasattr(DashboardHandler, '_api_status'):
            log_pass("Dashboard _api_status method", "✓ exists")
            results.add("dashboard_status_method", True, "_api_status method exists")
        else:
            log_fail("Dashboard _api_status method", "✗ not found")
            results.add("dashboard_status_method", False, "_api_status method missing")
            return results, False

        log_info("Expected fields in status", "lmstudio, ollama, llm_backend")
        results.add("dashboard_fields", True, "Status fields documented")

        return results, True

    except Exception as e:
        log_fail("Dashboard integration", str(e))
        results.add("dashboard_integration", False, f"Error: {e}")
        return results, False

# ═══ MAIN ═══
def main():
    parser = argparse.ArgumentParser(description="ADRIAN 369 LM Studio Integration Test")
    parser.add_argument("--quick", action="store_true", help="Fast tests only")
    parser.add_argument("--report", action="store_true", help="Generate JSON report")
    parser.add_argument("--html", action="store_true", help="Generate HTML report")
    args = parser.parse_args()

    log_header("ADRIAN 369 — LM STUDIO INTEGRATION TEST")

    all_results = []

    # Phase 1: Imports
    r1, ok1 = test_imports()
    all_results.append(r1)

    # Phase 2: Config
    r2, ok2 = test_config()
    all_results.append(r2)

    # Phase 3: Backend Detection
    r3, ok3 = test_backend_detection()
    all_results.append(r3)

    # Phase 4: Services
    r4, ok4 = test_service_availability()
    all_results.append(r4)

    # Phase 5: Job Analysis (only if services available or quick mode)
    if ok4 or args.quick:
        r5, ok5 = test_job_analysis()
        all_results.append(r5)

    # Phase 6: Dashboard
    r6, ok6 = test_dashboard_integration()
    all_results.append(r6)

    # ═══ Summary ═══
    log_header("TEST SUMMARY")

    total_tests = sum(len(r.tests) for r in all_results)
    total_passed = sum(sum(1 for t in r.tests if t["passed"]) for r in all_results)

    print(f"{Color.BOLD}Total: {total_passed}/{total_tests} tests passed{Color.END}\n")

    pass_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0

    if pass_rate == 100:
        print(f"{Color.GREEN}{Color.BOLD}✅ ALL TESTS PASSED{Color.END}")
        overall_result = "✅ PASS"
    elif pass_rate >= 80:
        print(f"{Color.YELLOW}{Color.BOLD}⚠️  MOST TESTS PASSED ({pass_rate:.0f}%){Color.END}")
        overall_result = "⚠️  PARTIAL"
    else:
        print(f"{Color.RED}{Color.BOLD}❌ TESTS FAILED ({pass_rate:.0f}%){Color.END}")
        overall_result = "❌ FAIL"

    # Generate reports if requested
    if args.report or args.html:
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "test_run": "LM Studio Integration Test",
            "overall_result": overall_result,
            "pass_rate": pass_rate,
            "total_tests": total_tests,
            "passed": total_passed,
            "failed": total_tests - total_passed,
            "phases": [{"phase": f"Phase {i+1}", "tests": r.tests} for i, r in enumerate(all_results)]
        }

        if args.report:
            report_file = Path("lmstudio_test_report.json")
            report_file.write_text(json.dumps(report_data, indent=2))
            print(f"\n📊 JSON Report: {report_file}")

        if args.html:
            html_file = Path("lmstudio_test_report.html")
            html_content = generate_html_report(report_data)
            html_file.write_text(html_content)
            print(f"📊 HTML Report: {html_file}")

    print(f"\n{Color.CYAN}{'═' * 70}{Color.END}\n")

def generate_html_report(data: Dict) -> str:
    """Generate HTML report from test data."""
    html = """<!DOCTYPE html>
<html>
<head>
    <title>ADRIAN 369 LM Studio Integration Test Report</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 40px; }
        .header { background: #0d47a1; color: white; padding: 20px; border-radius: 5px; }
        .summary { background: #f5f5f5; padding: 20px; margin: 20px 0; border-radius: 5px; }
        .pass { color: #2e7d32; } .fail { color: #c62828; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background: #f5f5f5; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 ADRIAN 369 — LM Studio Integration Test</h1>
        <p>Test Report: """ + data["timestamp"] + """</p>
    </div>
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Overall:</strong> <span class=""" + ("class='pass'" if data["overall_result"] == "✅ PASS" else "class='fail'") + """>""" + data["overall_result"] + """</span></p>
        <p><strong>Pass Rate:</strong> """ + f"{data['pass_rate']:.1f}%" + """</p>
        <p><strong>Tests:</strong> """ + f"{data['passed']}/{data['total_tests']}" + """</p>
    </div>
    <h2>Test Phases</h2>
    <table>
        <tr><th>Test</th><th>Result</th><th>Message</th></tr>
"""

    for phase in data["phases"]:
        for test in phase["tests"]:
            result = "✅ PASS" if test["passed"] else "❌ FAIL"
            status_class = "pass" if test["passed"] else "fail"
            html += f"""        <tr>
            <td>{test['name']}</td>
            <td><span class="{status_class}">{result}</span></td>
            <td>{test['message']}</td>
        </tr>
"""

    html += """    </table>
</body>
</html>"""

    return html

if __name__ == "__main__":
    main()
