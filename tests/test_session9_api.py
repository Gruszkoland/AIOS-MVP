#!/usr/bin/env python3
"""Sesja 9 - Automated API Testing"""

import subprocess
import time
import requests
import sys

def test_api():
    print("🚀 TEST 1: Starting Flask backend...")
    backend = subprocess.Popen([sys.executable, "server.py"],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               text=True)
    time.sleep(3)

    tests_passed = 0
    tests_failed = 0

    print("✓ Backend started, checking /health endpoint...")
    try:
        r = requests.get("http://localhost:8002/mapi/v1/health", timeout=2)
        print(f"✅ /health: {r.status_code} - OK")
        tests_passed += 1
    except Exception as e:
        print(f"❌ /health failed: {e}")
        tests_failed += 1

    print("✓ Testing /agents endpoint...")
    try:
        r = requests.get("http://localhost:8002/mapi/v1/agents", timeout=2)
        if r.status_code == 200:
            agents = r.json()
            print(f"✅ /agents: {r.status_code} - {len(agents)} agents found")
            for agent in agents[:4]:
                name = agent.get("name", "Unknown")
                trust = agent.get("trust_score", 0)
                print(f"  - {name}: {trust}% trust")
            tests_passed += 1
        else:
            print(f"❌ /agents: {r.status_code}")
            tests_failed += 1
    except Exception as e:
        print(f"❌ /agents failed: {e}")
        tests_failed += 1

    print("✓ Testing /tasks endpoint...")
    try:
        r = requests.get("http://localhost:8002/mapi/v1/tasks", timeout=2)
        if r.status_code == 200:
            print(f"✅ /tasks: {r.status_code} - OK")
            tests_passed += 1
        else:
            print(f"❌ /tasks: {r.status_code}")
            tests_failed += 1
    except Exception as e:
        print(f"❌ /tasks failed: {e}")
        tests_failed += 1

    print("\n🛑 Stopping backend gracefully...")
    try:
        backend.terminate()
        backend.wait(timeout=3)
    except:
        backend.kill()
    print("✓ Backend stopped")

    print(f"\n📊 RESULTS: {tests_passed}/3 tests passed")
    return tests_failed == 0

if __name__ == "__main__":
    success = test_api()
    sys.exit(0 if success else 1)
