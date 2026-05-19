#!/usr/bin/env python3
from mcp_servers.guardian_mcp import GuardianMCP

server = GuardianMCP()
result = server.handle_validate_policy(
    operation="export",
    context={"scope": "local"}  # Compliant
)

print(f"Success: {result['success']}")
print(f"Result: {result['result']}")
print(f"Checkpoint: {result.get('checkpoint', 'N/A')}")
