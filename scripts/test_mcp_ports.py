#!/usr/bin/env python3
"""Test MCP agent port connectivity"""
import socket
import time

agents = {
    'Router': 9001,
    'Genesis': 9004,
    'Guardian': 9002,
    'Healer': 9003,
    'Oracle': 9005,
    'Vortex': 9006
}

print("MCP Agent Port Listening Status:")
print("=" * 50)

listening_count = 0
for agent, port in agents.items():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    try:
        result = sock.connect_ex(('localhost', port))
        if result == 0:
            status = "[LISTENING]"
            listening_count += 1
        else:
            status = "[CLOSED]"
        print(f"{agent:12} (Port {port}): {status}")
    except Exception as e:
        print(f"{agent:12} (Port {port}): [ERROR] {str(e)[:20]}")
    finally:
        sock.close()

print("=" * 50)
print(f"Summary: {listening_count}/6 agents listening")
print("Status: {'✅ ALL AGENTS OPERATIONAL' if listening_count == 6 else '⚠️  PARTIAL DEPLOYMENT'}")
