#!/usr/bin/env python
"""
UAP Launcher: Start Backend API + Frontend HTTP Server
Cross-platform (Windows, Linux, macOS)
"""
import os
import sys
import time
import socket
import subprocess
import signal
import json
from pathlib import Path
from datetime import datetime

# Configuration
BACKEND_HOST = os.getenv("MAPI_HOST", "127.0.0.1")
BACKEND_PORT = int(os.getenv("MAPI_PORT", "8002"))
FRONTEND_PORT = 8003
DB_ENGINE = os.getenv("DB_ENGINE", "sqlite")

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
BACKEND_DIR = PROJECT_ROOT / "uap" / "backend"
FRONTEND_DIR = PROJECT_ROOT / "uap" / "frontend"
DB_DIR = PROJECT_ROOT / "db"
INIT_DB_SCRIPT = SCRIPT_DIR / "init_local_db.py"


def print_banner():
    """Print startup banner."""
    print("\n" + "=" * 70)
    print("  Unified Admin Panel (UAP) — Local Development Launcher")
    print("  Backend: {host}:{port} | Frontend: localhost:{frontend_port}".format(
        host=BACKEND_HOST, port=BACKEND_PORT, frontend_port=FRONTEND_PORT
    ))
    print("=" * 70 + "\n")


def is_port_available(host: str, port: int) -> bool:
    """Check if port is available."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((host, port))
        sock.close()
        return result != 0
    except Exception:
        return True


def init_database():
    """Initialize SQLite database."""
    print("[DB] Initializing SQLite database...")
    
    if not DB_DIR.exists():
        DB_DIR.mkdir(parents=True, exist_ok=True)
    
    db_path = DB_DIR / "adrion_local.db"
    
    if db_path.exists():
        print(f"[DB] Database already exists at {db_path}")
        return True
    
    # Run init script if it exists
    if INIT_DB_SCRIPT.exists():
        print(f"[DB] Running init script: {INIT_DB_SCRIPT}")
        try:
            result = subprocess.run(
                [sys.executable, str(INIT_DB_SCRIPT)],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode != 0:
                print(f"[ERROR] Init script failed: {result.stderr}")
                return False
            print("[DB] Database initialized successfully")
            return True
        except subprocess.TimeoutExpired:
            print("[ERROR] Database init timed out")
            return False
        except Exception as e:
            print(f"[ERROR] Database init failed: {e}")
            return False
    
    # Create basic SQLite schema if init script doesn't exist
    print("[DB] Creating basic SQLite schema...")
    try:
        sys.path.insert(0, str(BACKEND_DIR))
        from db import SQLiteDB
        db = SQLiteDB(str(db_path))
        print("[DB] Database initialized successfully")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to initialize database: {e}")
        return False


def start_backend():
    """Start Flask backend API server."""
    print("[BACKEND] Starting Flask API server on {host}:{port}...".format(
        host=BACKEND_HOST, port=BACKEND_PORT
    ))
    
    if not is_port_available(BACKEND_HOST, BACKEND_PORT):
        print(f"[ERROR] Port {BACKEND_PORT} is already in use")
        return None
    
    backend_env = os.environ.copy()
    backend_env["PYTHONUNBUFFERED"] = "1"
    backend_env["FLASK_APP"] = "api.py"
    backend_env["FLASK_ENV"] = "development"
    backend_env["DB_ENGINE"] = DB_ENGINE
    
    try:
        # Use explicit python interpreter to avoid path issues
        python_exe = sys.executable
        api_script = BACKEND_DIR / "api.py"
        
        proc = subprocess.Popen(
            [python_exe, str(api_script)],
            cwd=str(BACKEND_DIR),
            env=backend_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        print(f"[BACKEND] Process started (PID: {proc.pid})")
        return proc
    except Exception as e:
        print(f"[ERROR] Failed to start backend: {e}")
        return None


def start_frontend():
    """Start HTTP server for frontend on port 8003."""
    print("[FRONTEND] Starting HTTP server on localhost:{port}...".format(
        port=FRONTEND_PORT
    ))
    
    if not is_port_available("127.0.0.1", FRONTEND_PORT):
        print(f"[ERROR] Port {FRONTEND_PORT} is already in use")
        return None
    
    if not FRONTEND_DIR.exists():
        print(f"[ERROR] Frontend directory not found: {FRONTEND_DIR}")
        return None
    
    frontend_env = os.environ.copy()
    frontend_env["PYTHONUNBUFFERED"] = "1"
    
    try:
        python_exe = sys.executable
        
        # Start HTTP server
        proc = subprocess.Popen(
            [python_exe, "-m", "http.server", str(FRONTEND_PORT)],
            cwd=str(FRONTEND_DIR),
            env=frontend_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        print(f"[FRONTEND] Process started (PID: {proc.pid})")
        return proc
    except Exception as e:
        print(f"[ERROR] Failed to start frontend: {e}")
        return None


def health_check(host: str, port: int) -> bool:
    """Quick health check."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


def stream_process_output(proc, label: str):
    """Stream process output to stdout."""
    if proc and proc.stdout:
        try:
            for line in proc.stdout:
                if line:
                    print(f"[{label}] {line}", end='')
        except Exception as e:
            print(f"[ERROR] Failed to stream {label} output: {e}")


def main():
    """Main launcher orchestrator."""
    print_banner()
    
    # Step 1: Initialize database
    if not init_database():
        print("[ERROR] Database initialization failed. Aborting.")
        sys.exit(1)
    
    time.sleep(1)
    
    # Step 2: Start backend
    backend_proc = start_backend()
    if not backend_proc:
        print("[ERROR] Failed to start backend. Aborting.")
        sys.exit(1)
    
    # Wait for backend to be ready
    print("[WAIT] Waiting for backend to be ready...")
    max_retries = 30
    for i in range(max_retries):
        if health_check(BACKEND_HOST, BACKEND_PORT):
            print("[OK] Backend is ready!")
            break
        time.sleep(1)
        if i % 10 == 0:
            print(f"  ... attempt {i+1}/{max_retries}")
    else:
        print(f"[WARN] Backend health check failed after {max_retries} attempts (may still be starting)")
    
    time.sleep(1)
    
    # Step 3: Start frontend
    frontend_proc = start_frontend()
    if not frontend_proc:
        print("[WARN] Frontend failed to start, but backend is running")
    else:
        time.sleep(1)
        if health_check("127.0.0.1", FRONTEND_PORT):
            print("[OK] Frontend is ready!")
        else:
            print("[WARN] Frontend health check failed")
    
    # Step 4: Print access info
    print("\n" + "=" * 70)
    print("  SERVICES STARTED")
    print("=" * 70)
    print(f"  Backend API:  http://{BACKEND_HOST}:{BACKEND_PORT}/mapi/v1/health")
    if frontend_proc:
        print(f"  Frontend:     http://127.0.0.1:{FRONTEND_PORT}/")
    print(f"  Database:     {DB_DIR / 'adrion_local.db'}")
    print("\n  Press Ctrl+C to stop")
    print("=" * 70 + "\n")
    
    # Save launch info
    launch_info = {
        "timestamp": datetime.now().isoformat(),
        "backend_pid": backend_proc.pid if backend_proc else None,
        "frontend_pid": frontend_proc.pid if frontend_proc else None,
        "backend_url": f"http://{BACKEND_HOST}:{BACKEND_PORT}",
        "frontend_url": f"http://127.0.0.1:{FRONTEND_PORT}",
    }
    
    def signal_handler(sig, frame):
        """Handle Ctrl+C gracefully."""
        print("\n[SHUTDOWN] Stopping services...")
        
        if backend_proc:
            try:
                backend_proc.terminate()
                backend_proc.wait(timeout=5)
                print("[OK] Backend stopped")
            except Exception as e:
                print(f"[ERROR] Failed to stop backend: {e}")
                backend_proc.kill()
        
        if frontend_proc:
            try:
                frontend_proc.terminate()
                frontend_proc.wait(timeout=5)
                print("[OK] Frontend stopped")
            except Exception as e:
                print(f"[ERROR] Failed to stop frontend: {e}")
                frontend_proc.kill()
        
        print("[DONE] Services stopped")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Keep running and monitor processes
    try:
        while True:
            # Check if processes are still alive
            if backend_proc and backend_proc.poll() is not None:
                print("[ERROR] Backend process died!")
                # Try to restart
                # backend_proc = start_backend()
            
            if frontend_proc and frontend_proc.poll() is not None:
                print("[WARN] Frontend process died")
                # Try to restart
                # frontend_proc = start_frontend()
            
            time.sleep(5)
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)


if __name__ == "__main__":
    main()
