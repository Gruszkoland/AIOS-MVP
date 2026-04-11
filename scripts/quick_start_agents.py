#!/usr/bin/env python3
"""Quick agent starter for ETAP 2"""
import subprocess
import time
import os

agents = [
    {"name": "Router", "port": 9001, "file": "mcp_router_app.py"},
    {"name": "Guardian", "port": 9002, "file": "mcp_guardian_app.py"},
    {"name": "Healer", "port": 9003, "file": "mcp_healer_app.py"},
    {"name": "Genesis", "port": 9004, "file": "mcp_genesis_app.py"},
    {"name": "Oracle", "port": 9005, "file": "mcp_oracle_app.py"},
    {"name": "Vortex", "port": 9006, "file": "mcp_vortex_app.py"},
]

env = os.environ.copy()

for agent in agents:
    env[f"MCP_{agent['name'].upper()}_PORT"] = str(agent["port"])

    cmd = [".venv/Scripts/python.exe", agent["file"]]
    print(f"[START] {agent['name']} (port {agent['port']})")

    subprocess.Popen(
        cmd,
        env=env,
        cwd=".",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    time.sleep(1)  # Stagger startup

print("\n[OK] All 6 agents started")
print("Waiting 10 seconds for initialization...")

time.sleep(10)

# Quick check
import socket

def check(port):
    s = socket.socket()
    s.settimeout(1)
    try:
        return s.connect_ex(('localhost', port)) == 0
    finally:
        s.close()

print("\nStatus:")
ports = [9001, 9002, 9003, 9004, 9005, 9006]
online = sum(1 for p in ports if check(p))
print(f"Agents online: {online}/6")

if online >= 5:
    print("\nReady for testing!")
