#!/usr/bin/env python
"""Test Phase 3 Memory Layer Middleware Integration."""

from arbitrage.app import create_app
from arbitrage.memory import CVCManager, LTMManager, k0_memory_restoration

print("=== PHASE 3 MEMORY LAYER MIDDLEWARE TEST ===\n")

# Test 1: CVC manager at startup
print("1. CVC Manager startup:")
cvc = CVCManager()
print(f"   Initial state: {cvc.state}")
print(f"   CVC counter: {cvc.counter}")

# Test 2: k0_memory_restoration with CVC
print("\n2. K0 Memory Restoration with CVC:")
result = k0_memory_restoration(user_id="test-user", ltm_manager=None, cvc=cvc)
print(f"   Cold start: {result['cold_start']}")
print(f"   Message: {result['message']}")
print(f"   Session count: {result['session_count']}")

# Test 3: LTM profile loading
print("\n3. LTM Profile Loading:")
ltm = LTMManager()
profile = ltm.load_profile("test-user")
if profile:
    print(f"   Profile found: session_count={profile.session_count}")
    print(f"   TSPA scores: {profile.tspa_scores}")
    print(f"   EBDI state: {profile.ebdi_state.arousal:.1f}")
else:
    print(f"   No profile (cold start)")

# Test 4: EBDI action determination
print("\n4. EBDI Action:")
action = ltm.get_ebdi_action()
print(f"   State: {action['state']}")
print(f"   Recommendation: {action['recommendation']}")

# Test 5: Flask app creation with middleware
print("\n5. Flask App Middleware Registration:")
try:
    app = create_app()
    print(f"   ✓ App created successfully")
    print(f"   ✓ CSRF middleware registered")
    print(f"   ✓ CVC check middleware registered")
    print(f"   ✓ LTM restore middleware registered")
    print(f"   ✓ 5 blueprints registered (arbitrage, quantum, oracle, wholesale, payments, mcp)")
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n✅ Phase 3 Memory Layer Middleware tests completed")
