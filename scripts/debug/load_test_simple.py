#!/usr/bin/env python3
"""Quick MCP Load Test - Simplified"""

import socket
import time

agents = {
    'Router': 9001,
    'Guardian': 9002,
    'Healer': 9003,
    'Genesis': 9004,
    'Oracle': 9005,
    'Vortex': 9006
}

print("MCP Agent Load Test - Sequential")
print("=" * 60)

total_time = 0
success_count = 0
error_count = 0

for phase in [1, 2, 3]:
    iterations = 20 if phase == 1 else (40 if phase == 2 else 60)
    print(f"\n[PHASE {phase}] {iterations} iterations per agent")
    print("-" * 60)

    phase_start = time.time()
    phase_success = 0

    for i in range(iterations):
        for agent, port in agents.items():
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            try:
                result = sock.connect_ex(('localhost', port))
                if result == 0:
                    phase_success += 1
                    success_count += 1
                else:
                    error_count += 1
            except:
                error_count += 1
            finally:
                sock.close()

        if (i + 1) % 10 == 0:
            elapsed = time.time() - phase_start
            rps = ((i + 1) * 6) / elapsed
            print(f"  [{i+1:>2}/{iterations}] {rps:>6.1f} ops/sec")

    phase_elapsed = time.time() - phase_start
    total_time += phase_elapsed
    print(f"Phase {phase} Time: {phase_elapsed:.2f}s ({phase_success} successes)")

print("\n" + "=" * 60)
print("[RESULTS]")
print(f"Total Operations: {success_count + error_count}")
print(f"Success: {success_count} ({100*success_count/(success_count+error_count):.1f}%)")
print(f"Errors: {error_count}")
print(f"Total Time: {total_time:.2f}s")
print(f"Avg RPS: {(success_count + error_count) / total_time:.1f}")
print("\n✅ Load test complete")
