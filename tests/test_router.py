"""Quick validation of slim webhook_server."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "harmonia-dashboard"))

from webhook_server import _router, WebhookHandler

routes = _router.list_routes()
print(f"Routes registered: {len(routes)}")
for r in routes:
    print(f"  {r['method']:6s} {r['pattern']}")

# Validate all expected routes exist
expected = [
    ("POST", "/webhook/harmonia-369"),
    ("GET", "/api/leads"),
    ("GET", "/api/stats"),
    ("GET", "/api/leads/search"),
    ("POST", "/api/feedback/observe"),
    ("POST", "/api/feedback/orient"),
    ("POST", "/api/feedback/act"),
    ("POST", "/api/golden"),
    ("GET", "/api/feedback/decide"),
    ("GET", "/api/feedback/status"),
    ("GET", "/api/golden"),
    ("GET", "/api/memory/stats"),
    ("GET", "/api/events/metrics"),
    ("POST", "/api/outreach/analyze"),
    ("POST", "/api/outreach/generate-email"),
    ("POST", "/api/pipeline/run"),
    ("POST", "/api/ai/report"),
    ("POST", "/api/blacklist"),
    ("GET", "/api/genesis"),
    ("GET", "/api/swarm/status"),
    ("GET", "/api/pipeline/status"),
    ("GET", "/api/blacklist"),
    ("GET", "/health"),
]

registered = {(r["method"], r["pattern"]) for r in routes}
missing = [f"{m} {p}" for m, p in expected if (m, p) not in registered]

if missing:
    print(f"\nMISSING ROUTES ({len(missing)}):")
    for m in missing:
        print(f"  {m}")
    sys.exit(1)
else:
    print(f"\nAll {len(expected)} expected routes registered.")

# Test router resolution
from webhook_server import _router
assert _router.resolve("GET", "/health") is not None, "/health not resolvable"
assert _router.resolve("POST", "/webhook/harmonia-369") is not None, "/webhook not resolvable"
assert _router.resolve("GET", "/api/leads/search?q=test") is not None, "search with query not resolvable"
assert _router.resolve("GET", "/nonexistent") is None, "nonexistent should resolve to None"

print("Router resolution: OK")
print("\nALL CHECKS PASSED")
