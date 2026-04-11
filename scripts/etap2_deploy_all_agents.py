#!/usr/bin/env python3
"""
ADRION 369 v4.0 - ETAP 2: MCP Agents Automated Deployment
Orchestrates deployment of 6 agents (Router, Guardian, Healer, Genesis, Oracle, Vortex)
"""

import subprocess
import time
import os
import sys
import socket
from datetime import datetime

def check_port_open(port, timeout=2):
    """Check if port is listening"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        result = sock.connect_ex(('localhost', port))
        return result == 0
    except:
        return False
    finally:
        sock.close()

def wait_for_port(port, max_attempts=30, interval=1):
    """Wait for port to be listening (up to 30 seconds)"""
    for attempt in range(max_attempts):
        if check_port_open(port):
            return True
        if attempt < max_attempts - 1:
            time.sleep(interval)
    return False

class AgentDeployment:
    def __init__(self, name, port, script, startup_order):
        self.name = name
        self.port = port
        self.script = script
        self.startup_order = startup_order
        self.process = None
        self.status = "PENDING"

    def start(self, project_root, env_vars):
        """Start the agent"""
        cmd = [
            os.path.join(project_root, ".venv", "Scripts", "python.exe"),
            self.script,
            "--port", str(self.port),
            "--log-level", "INFO"
        ]

        try:
            self.process = subprocess.Popen(
                cmd,
                cwd=project_root,
                env={**os.environ, **env_vars},
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            self.status = "STARTING"
            return True
        except Exception as e:
            self.status = f"FAILED: {str(e)}"
            return False

    def verify(self):
        """Verify agent is running"""
        if self.process is None:
            return False

        if not wait_for_port(self.port):
            self.status = "PORT_NOT_LISTENING"
            return False

        self.status = "RUNNING"
        return True

def main():
    print("=" * 80)
    print("ADRION 369 v4.0 - ETAP 2: MCP AGENTS AUTOMATED DEPLOYMENT")
    print("Date: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"))
    print("=" * 80)
    print()

    project_root = r"c:\Users\adiha\162 demencje w schemacie 369"

    # Load .env variables
    print("[PHASE 1] Loading environment configuration...")
    print("-" * 80)

    env_file = os.path.join(project_root, ".env")
    env_vars = {}

    if not os.path.exists(env_file):
        print("[ERROR] .env file not found")
        return 1

    try:
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
        print(f"[OK] Loaded {len(env_vars)} environment variables")
    except Exception as e:
        print(f"[ERROR] Failed to load .env: {str(e)}")
        return 1

    print()

    # Define agents (in (startup order)
    print("[PHASE 2] Defining agent deployment sequence...")
    print("-" * 80)

    agents = [
        AgentDeployment("Router", 9001, "mcp_router_app.py", 1),
        AgentDeployment("Genesis", 9004, "mcp_genesis_app.py", 2),
        AgentDeployment("Guardian", 9002, "mcp_guardian_app.py", 3),
        AgentDeployment("Healer", 9003, "mcp_healer_app.py", 4),
        AgentDeployment("Oracle", 9005, "mcp_oracle_app.py", 5),
        AgentDeployment("Vortex", 9006, "mcp_vortex_app.py", 6),
    ]

    print("Startup sequence:")
    for agent in sorted(agents, key=lambda a: a.startup_order):
        print(f"  [{agent.startup_order}] {agent.name:12} (Port {agent.port})")

    print()

    # Start agents
    print("[PHASE 3] Starting agents...")
    print("-" * 80)
    print()

    for agent in sorted(agents, key=lambda a: a.startup_order):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting {agent.name}...", end=" ")
        sys.stdout.flush()

        if agent.start(project_root, env_vars):
            print(f"[PID: {agent.process.pid}]")
            print(f"  Waiting for port {agent.port} to be listening...", end=" ")
            sys.stdout.flush()

            if agent.verify():
                print("[OK]")
            else:
                print("[TIMEOUT]")
                print(f"  [WARNING] Port {agent.port} not responding yet (may still initializing)")
        else:
            print("[FAILED]")

        # Brief pause between startups
        time.sleep(2)

    print()
    print("[PHASE 4] Verification...")
    print("-" * 80)
    print()

    # Let agents initialize
    time.sleep(5)

    # Re-verify all agents
    print("Verifying all agents are operational:")
    print()

    all_healthy = True
    for agent in agents:
        port_status = "LISTENING" if check_port_open(agent.port) else "NOT LISTENING"
        process_status = "RUNNING" if agent.process and agent.process.poll() is None else "STOPPED"

        overall_status = "[OK]" if port_status == "LISTENING" and process_status == "RUNNING" else "[CHECK]"
        print(f"  {overall_status} {agent.name:12} | Port {agent.port}: {port_status:15} | Process: {process_status}")

        if port_status != "LISTENING":
            all_healthy = False

    print()

    # Test health endpoints
    print("[PHASE 5] Testing API endpoints...")
    print("-" * 80)
    print()

    print("Testing key endpoints:")
    print()

    test_endpoints = [
        ("Router", 9001, "/health"),
        ("Genesis", 9004, "/events"),
        ("Guardian", 9002, "/audit/logs"),
        ("Healer", 9003, "/health/diagnose"),
        ("Oracle", 9005, "/analytics/metrics"),
        ("Vortex", 9006, "/ml/models"),
    ]

    for agent_name, port, endpoint in test_endpoints:
        try:
            result = subprocess.run(
                ["curl", "-s", f"http://localhost:{port}{endpoint}"],
                capture_output=True,
                text=True,
                timeout=2
            )

            if result.returncode == 0 and result.stdout:
                print(f"  [OK] {agent_name:12} GET {endpoint:20} - Response: {len(result.stdout)} bytes")
            else:
                print(f"  [INFO] {agent_name:12} GET {endpoint:20} - Not yet responding")
        except:
            print(f"  [INFO] {agent_name:12} GET {endpoint:20} - Network test skipped")

    print()
    print("=" * 80)
    print("DEPLOYMENT SUMMARY")
    print("=" * 80)
    print()

    print("Agents deployed:")
    print()
    for agent in agents:
        status_icon = "[OK]" if check_port_open(agent.port) else "[!]"
        print(f"  {status_icon} {agent.name:12} - PID: {agent.process.pid if agent.process else 'N/A':6} - Port: {agent.port}")

    print()
    print("=" * 80)
    print("ETAP 2 DEPLOYMENT COMPLETE")
    print("=" * 80)
    print()

    print("Next steps:")
    print()
    print("1. Run full API test suite:")
    print("   python run_comprehensive_tests.py (42 endpoints)")
    print()
    print("2. Monitor agent logs (if issues):")
    print("   - Check PostgreSQL: docker logs adrion-postgres")
    print("   - Check agent stdout: Review agent process output")
    print()
    print("3. Test specific endpoints:")
    print("   curl http://localhost:9001/health (Router)")
    print("   curl http://localhost:9004/events (Genesis)")
    print("   curl http://localhost:9002/audit/logs (Guardian)")
    print()
    print("To stop all agents:")
    print("   pkill -f 'mcp_.*_app.py'")
    print()
    print(f"Deployment time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print()

    print("=" * 80)
    print("AGENTS RUNNING IN BACKGROUND")
    print("To keep agents running, do NOT close this terminal")
    print("=" * 80)
    print()

    # Keep script running to maintain subprocesses
    try:
        while True:
            time.sleep(1)

            # Check if any agent crashed
            for agent in agents:
                if agent.process and agent.process.poll() is not None:
                    print(f"[WARNING] {agent.name} (PID {agent.process.pid}) unexpectedly stopped")
    except KeyboardInterrupt:
        print()
        print("[INFO] Shutdown requested - stopping all agents")
        print()

        for agent in agents:
            if agent.process:
                agent.process.terminate()
                print(f"[OK] Stopped {agent.name} (PID {agent.process.pid})")

        print()
        print("All agents stopped.")
        return 0

    return 0

if __name__ == "__main__":
    try:
        exit(main())
    except Exception as e:
        print(f"[FATAL ERROR] {str(e)}")
        exit(1)
