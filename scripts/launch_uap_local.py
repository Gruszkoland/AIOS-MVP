#!/usr/bin/env python3
"""
Autonomous UAP Local Stack Launcher
- Initializes SQLite database
- Starts Backend API (port 8002)
- Starts Frontend HTTP server (port 8003)
- Validates both are responding
"""

import os
import sys
import subprocess
import time
import socket
import requests
import psutil
from pathlib import Path
from datetime import datetime

# Configuration
BACKEND_PORT = 8002
FRONTEND_PORT = 8003
BACKEND_HOST = "localhost"
FRONTEND_HOST = "localhost"
MAX_STARTUP_WAIT = 30  # seconds
HEALTH_CHECK_INTERVAL = 1  # seconds

WORK_DIR = Path(__file__).parent.parent
os.chdir(WORK_DIR)

# Create logs directory
LOGS_DIR = WORK_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

print("=" * 70)
print("  ADRION 369 — UAP LOCAL STACK LAUNCHER")
print("=" * 70)
print()

def log(msg, level="INFO", color=None):
    """Print timestamped log message"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    colors = {
        "INFO": "\033[94m",    # Blue
        "OK": "\033[92m",      # Green
        "WARN": "\033[93m",    # Yellow
        "ERROR": "\033[91m",   # Red
        "END": "\033[0m"       # Reset
    }
    color_code = colors.get(level, colors.get(color, ""))
    print(f"{color_code}[{timestamp} {level}]{colors['END']} {msg}")

def port_is_listening(port):
    """Check if port is listening"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((BACKEND_HOST, port))
    sock.close()
    return result == 0

def kill_process_on_port(port):
    """Kill process listening on port"""
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                conns = proc.net_connections()
                for conn in conns:
                    if conn.laddr.port == port:
                        log(f"Killing process {proc.pid} ({proc.name()}) on port {port}", "WARN")
                        proc.kill()
                        time.sleep(0.5)
                        return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except Exception as e:
        log(f"Error killing process on port {port}: {e}", "WARN")
    return False

def wait_for_port(port, timeout=30):
    """Wait for port to be listening"""
    elapsed = 0
    while elapsed < timeout:
        if port_is_listening(port):
            return True
        time.sleep(1)
        elapsed += 1
    return False

def check_health_endpoint(url, timeout=2):
    """Check if health endpoint responds"""
    try:
        resp = requests.get(url, timeout=timeout)
        return resp.status_code == 200
    except:
        return False

# ─────────────────────────────────────────────────────────────────────────
# STEP 1: Initialize Database
# ─────────────────────────────────────────────────────────────────────────

log("[STEP 1] Initializing SQLite database...", "INFO")

init_db_script = WORK_DIR / "scripts/init_local_db.py"
if init_db_script.exists():
    try:
        result = subprocess.run(
            [sys.executable, str(init_db_script)],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            log("Database initialized successfully", "OK")
            if "--verbose" in sys.argv:
                print(result.stdout)
        else:
            log(f"Database initialization failed: {result.stderr}", "ERROR")
            sys.exit(1)
    except Exception as e:
        log(f"Failed to run init_local_db.py: {e}", "ERROR")
        sys.exit(1)
else:
    log(f"scripts/init_local_db.py not found", "ERROR")
    sys.exit(1)

print()

# ─────────────────────────────────────────────────────────────────────────
# STEP 2: Clear Ports 8002-8003
# ─────────────────────────────────────────────────────────────────────────

log("[STEP 2] Checking ports 8002-8003...", "INFO")

for port in [BACKEND_PORT, FRONTEND_PORT]:
    if port_is_listening(port):
        kill_process_on_port(port)
        time.sleep(0.5)

print()

# ─────────────────────────────────────────────────────────────────────────
# STEP 3: Start Backend API (Port 8002)
# ─────────────────────────────────────────────────────────────────────────

log("[STEP 3] Starting Backend API on port 8002...", "INFO")

backend_script = WORK_DIR / "uap/backend/api.py"
if not backend_script.exists():
    log(f"uap/backend/api.py not found", "ERROR")
    sys.exit(1)

backend_process = subprocess.Popen(
    [sys.executable, str(backend_script)],
    stdout=open(LOGS_DIR / "backend.log", "w"),
    stderr=open(LOGS_DIR / "backend.err", "w"),
    cwd=str(WORK_DIR)
)

log(f"Backend process started (PID: {backend_process.pid})", "INFO")
log(f"Waiting for health endpoint response (timeout: 30s)...", "INFO")

backend_health_url = f"http://{BACKEND_HOST}:{BACKEND_PORT}/mapi/v1/health"

if wait_for_port(BACKEND_PORT, MAX_STARTUP_WAIT):
    time.sleep(1)  # Let Flask fully initialize
    if check_health_endpoint(backend_health_url):
        log("Backend API responding (Status: 200)", "OK")
    else:
        log("Backend API listening but health check failed", "WARN")
else:
    log(f"Backend API failed to respond after {MAX_STARTUP_WAIT} seconds", "ERROR")
    try:
        backend_log = (LOGS_DIR / "backend.log").read_text()
        backend_err = (LOGS_DIR / "backend.err").read_text()
        print("Backend log (last 20 lines):")
        print("\n".join(backend_log.split("\n")[-20:]))
        print("\nBackend errors (last 20 lines):")
        print("\n".join(backend_err.split("\n")[-20:]))
    except:
        pass
    backend_process.terminate()
    sys.exit(1)

print()

# ─────────────────────────────────────────────────────────────────────────
# STEP 4: Start Frontend HTTP Server (Port 8003)
# ─────────────────────────────────────────────────────────────────────────

log("[STEP 4] Starting Frontend HTTP server on port 8003...", "INFO")

frontend_dir = WORK_DIR / "uap/frontend"
if not frontend_dir.exists():
    log(f"uap/frontend directory not found", "ERROR")
    backend_process.terminate()
    sys.exit(1)

frontend_process = subprocess.Popen(
    [sys.executable, "-m", "http.server", str(FRONTEND_PORT), "--directory", str(frontend_dir)],
    stdout=open(LOGS_DIR / "frontend.log", "w"),
    stderr=open(LOGS_DIR / "frontend.err", "w"),
    cwd=str(WORK_DIR)
)

log(f"Frontend process started (PID: {frontend_process.pid})", "INFO")
log(f"Waiting for HTTP response (timeout: 15s)...", "INFO")

frontend_url = f"http://{FRONTEND_HOST}:{FRONTEND_PORT}/"

if wait_for_port(FRONTEND_PORT, 15):
    time.sleep(1)
    if check_health_endpoint(frontend_url):
        log("Frontend server responding (Status: 200)", "OK")
    else:
        log("Frontend server listening but HTTP check failed", "WARN")
else:
    log(f"Frontend server failed to respond after 15 seconds", "ERROR")
    try:
        frontend_log = (LOGS_DIR / "frontend.log").read_text()
        frontend_err = (LOGS_DIR / "frontend.err").read_text()
        print("Frontend log (last 10 lines):")
        print("\n".join(frontend_log.split("\n")[-10:]))
        print("\nFrontend errors (last 10 lines):")
        print("\n".join(frontend_err.split("\n")[-10:]))
    except:
        pass
    backend_process.terminate()
    frontend_process.terminate()
    sys.exit(1)

print()

# ─────────────────────────────────────────────────────────────────────────
# STEP 5: Display Startup Summary
# ─────────────────────────────────────────────────────────────────────────

log("[STEP 5] Startup Complete!", "INFO")
print()
print("=" * 70)
print("  UAP LOCAL STACK IS READY")
print("=" * 70)
print()
print("ENDPOINTS:")
print(f"  Frontend:  http://localhost:{FRONTEND_PORT}/")
print(f"  Backend:   http://localhost:{BACKEND_PORT}/mapi/v1/")
print(f"  Health:    http://localhost:{BACKEND_PORT}/mapi/v1/health")
print()
print("PROCESSES:")
print(f"  Backend PID:  {backend_process.pid}")
print(f"  Frontend PID: {frontend_process.pid}")
print()
print("LOGS:")
print(f"  Backend:  {LOGS_DIR / 'backend.log'}")
print(f"  Frontend: {LOGS_DIR / 'frontend.log'}")
print()

print("Processes are running. Press Ctrl+C to stop.")

# Keep running
try:
    while True:
        time.sleep(1)
        # Check if processes are still alive
        if backend_process.poll() is not None:
            log("Backend process has exited", "WARN")
        if frontend_process.poll() is not None:
            log("Frontend process has exited", "WARN")
except KeyboardInterrupt:
    print()
    log("Shutting down...", "WARN")
    backend_process.terminate()
    frontend_process.terminate()
    backend_process.wait(timeout=5)
    frontend_process.wait(timeout=5)
    log("All processes stopped", "OK")
