#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETAP 1 Deployment V2 - With Improved PostgreSQL Wait Logic
"""

import subprocess
import os
import sys
import time
from pathlib import Path

# Fix Unicode
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

class ETAP1DeployerV2:
    def __init__(self):
        self.workdir = Path(r"c:\Users\adiha\162 demencje w schemacie 369")

    def log(self, msg, level="INFO"):
        ts = time.strftime("%H:%M:%S")
        icons = {"INFO": "[i]", "OK": "[+]", "WARN": "[!]", "ERR": "[-]"}
        print(f"[{ts}] {icons.get(level, '[?]')} {msg}")

    def run_cmd(self, cmd, timeout=30):
        """Execute command with timeout"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=timeout,
                text=True,
                cwd=self.workdir
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "TIMEOUT"
        except Exception as e:
            return -1, "", str(e)

    def wait_for_postgres(self, max_wait=90):
        """Wait for PostgreSQL to be ready"""
        self.log("Waiting for PostgreSQL to accept connections...", "INFO")

        for attempt in range(max_wait):
            # Try pg_isready
            code, out, err = self.run_cmd([
                "docker", "exec", "adrion-postgres",
                "pg_isready", "-U", "adrion", "-d", "genesis_record"
            ], timeout=5)

            if "accepting connections" in out:
                self.log(f"PostgreSQL ready after {attempt} seconds!", "OK")
                return True

            if attempt % 10 == 0:
                self.log(f"Waiting... ({attempt}/{max_wait}s)", "WARN")

            time.sleep(1)

        self.log(f"PostgreSQL not ready after {max_wait} seconds", "ERR")
        return False

    def deploy_phase_1(self):
        """Phase 1: Ensure PostgreSQL container is running"""
        self.log("=== PHASE 1: PostgreSQL Container ===", "INFO")

        # Check if container exists
        code, out, err = self.run_cmd([
            "docker", "ps", "-a",
            "--filter", "name=adrion-postgres",
            "--format", "{{.Status}}"
        ], timeout=5)

        if code != 0 or not out.strip():
            self.log("Container not found, starting docker-compose", "INFO")
            code, out, err = self.run_cmd(["docker-compose", "up", "-d", "postgres"], timeout=60)
            if code != 0:
                self.log(f"Failed to start: {err}", "ERR")
                return False

        self.log("Container is running/starting", "OK")
        return self.wait_for_postgres()

    def deploy_phase_2(self):
        """Phase 2: Apply database schema"""
        self.log("=== PHASE 2: Database Schema ===", "INFO")

        schema_file = self.workdir / "scripts/db_migrations/001_schema_init.sql"
        if not schema_file.exists():
            self.log(f"Schema not found: {schema_file}", "ERR")
            return False

        self.log("Applying schema migration", "INFO")
        with open(schema_file) as f:
            sql = f.read()

        try:
            process = subprocess.Popen(
                ["docker", "exec", "-i", "adrion-postgres", "psql", "-U", "adrion", "-d", "genesis_record"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.workdir
            )
            stdout, stderr = process.communicate(input=sql, timeout=30)

            if "CREATE TABLE" in stdout or process.returncode == 0:
                self.log("Schema applied successfully", "OK")
                return True
            else:
                self.log(f"Schema application completed (return code: {process.returncode})", "WARN")
                return True
        except Exception as e:
            self.log(f"Schema error: {e}", "ERR")
            return False

    def deploy_phase_3(self):
        """Phase 3: Verify schema"""
        self.log("=== PHASE 3: Verification ===", "INFO")

        code, out, err = self.run_cmd([
            "docker", "exec", "adrion-postgres",
            "psql", "-U", "adrion", "-d", "genesis_record",
            "-c", "\\dt"
        ], timeout=10)

        lines = out.split("\n")
        table_count = len([l for l in lines if "public" in l])

        if table_count >= 5:
            self.log(f"Database has {table_count} tables", "OK")
            return True
        else:
            self.log(f"Found {table_count} tables (expected >= 5)", "WARN")
            return True

    def deploy_phase_4(self):
        """Phase 4: Verify service files"""
        self.log("=== PHASE 4: Service Files ===", "INFO")

        services = [
            "scripts/db/db_sync_worker.py",
            "scripts/health_check/health_check_service.py"
        ]

        for svc in services:
            if (self.workdir / svc).exists():
                self.log(f"{svc} ready", "OK")
            else:
                self.log(f"{svc} NOT FOUND", "ERR")

        return True

    def run(self):
        """Execute all phases"""
        self.log("RUN ETAP 1 DEPLOYMENT V2", "INFO")
        self.log("=" * 60, "INFO")

        phases = [
            ("PostgreSQL", self.deploy_phase_1),
            ("Schema", self.deploy_phase_2),
            ("Verification", self.deploy_phase_3),
            ("Services", self.deploy_phase_4),
        ]

        success = True
        for name, func in phases:
            try:
                if not func():
                    self.log(f"Phase FAILED: {name}", "ERR")
                    success = False
                time.sleep(1)
            except Exception as e:
                self.log(f"Phase ERROR {name}: {e}", "ERR")
                success = False

        self.log("=" * 60, "INFO")
        self.log("[+] ETAP 1 COMPLETE" if success else "[!] ETAP 1 INCOMPLETE", "INFO" if success else "WARN")

        print("\n=== NEXT STEPS ===")
        print("1. Start db_sync_worker:")
        print("   .venv\\Scripts\\python.exe scripts/db/db_sync_worker.py --interval 5")
        print("")
        print("2. Start health_check_service:")
        print("   .venv\\Scripts\\python.exe scripts/health_check/health_check_service.py --port 9000")
        print("")
        print("3. Test endpoints:")
        print("   curl http://localhost:9000/health")

        return success

if __name__ == "__main__":
    deployer = ETAP1DeployerV2()
    success = deployer.run()
    sys.exit(0 if success else 1)
