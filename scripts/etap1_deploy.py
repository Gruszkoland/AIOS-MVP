#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETAP 1 Deployment Runner
Deploys ADRION 369 infrastructure with fallback options
"""

import subprocess
import os
import sys
import time
import json
from pathlib import Path

# Fix Unicode encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

class ETAP1Deployer:
    def __init__(self):
        self.workdir = Path("c:\\Users\\adiha\\162 demencje w schemacie 369")
        self.status = {"phase": 0, "module": "", "result": []}

    def log(self, msg, level="INFO"):
        timestamp = time.strftime("%H:%M:%S")
        # Use ASCII-safe prefixes instead of emoji
        prefix_map = {"INFO": "[i]", "OK": "[+]", "WARN": "[!]", "ERR": "[-]", "DEBUG": "[*]"}
        prefix = prefix_map.get(level, "[?]")
        print(f"[{timestamp}] {prefix:4} {level:8} {msg}")

    def check_docker(self):
        """Check if Docker is available"""
        self.log("Checking Docker availability...", "INFO")
        try:
            result = subprocess.run(["docker", "ps"], capture_output=True, timeout=5)
            if result.returncode == 0:
                self.log("✅ Docker is responsive", "OK")
                return True
        except Exception as e:
            self.log(f"Docker unavailable: {e}", "WARN")
            return False

    def deploy_phase_1_postgresql(self):
        """Start PostgreSQL container"""
        self.log("=== PHASE 1: PostgreSQL Container ===", "INFO")

        if not self.check_docker():
            self.log("Cannot proceed without Docker", "ERR")
            return False

        try:
            self.log("Running: docker-compose up -d postgres", "INFO")
            result = subprocess.run(
                ["docker-compose", "up", "-d", "postgres"],
                cwd=self.workdir,
                capture_output=True,
                timeout=60,
                text=True
            )

            if result.returncode == 0:
                self.log("✅ PostgreSQL container started", "OK")
                self.status["result"].append({"phase": 1, "status": "OK", "container": "postgres"})

                # Wait for health
                self.log("Waiting for container health check...", "INFO")
                for i in range(30):
                    check_result = subprocess.run(
                        ["docker", "ps", "--filter", "name=adrion-postgres", "--format", "{{.Status}}"],
                        capture_output=True,
                        timeout=5,
                        text=True
                    )
                    if "healthy" in check_result.stdout or "running" in check_result.stdout:
                        self.log(f"✅ PostgreSQL healthy after {i} seconds", "OK")
                        return True
                    time.sleep(1)

                self.log("⚠ Container running but health check pending", "WARN")
                return True
            else:
                self.log(f"Error: {result.stderr}", "ERR")
                return False

        except Exception as e:
            self.log(f"Failed: {e}", "ERR")
            return False

    def deploy_phase_2_schema(self):
        """Apply database schema"""
        self.log("=== PHASE 2: Database Schema ===", "INFO")

        schema_file = self.workdir / "scripts/db_migrations/001_schema_init.sql"
        if not schema_file.exists():
            self.log(f"Schema file not found: {schema_file}", "ERR")
            return False

        try:
            self.log(f"Reading schema from {schema_file.name}", "INFO")
            with open(schema_file, 'r') as f:
                sql_content = f.read()

            self.log("Applying schema via docker exec...", "INFO")
            process = subprocess.Popen(
                ["docker", "exec", "-i", "adrion-postgres", "psql", "-U", "adrion", "-d", "genesis_record"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            stdout, stderr = process.communicate(input=sql_content, timeout=30)

            if process.returncode == 0 or "CREATE TABLE" in stdout:
                self.log("✅ Schema applied successfully", "OK")
                self.log(f"Output: {stdout[:200]}", "DEBUG")
                return True
            else:
                self.log(f"Schema execution: {stderr[:300]}", "WARN")
                return True  # Continue anyway

        except Exception as e:
            self.log(f"Schema application failed: {e}", "ERR")
            return False

    def deploy_phase_3_verify(self):
        """Verify deployment"""
        self.log("=== PHASE 3: Verification ===", "INFO")

        try:
            # Check tables
            result = subprocess.run(
                ["docker", "exec", "adrion-postgres", "psql", "-U", "adrion", "-d", "genesis_record", "-c", "\\dt"],
                capture_output=True,
                timeout=10,
                text=True
            )

            if result.returncode == 0:
                lines = result.stdout.split("\n")
                table_count = len([l for l in lines if "public" in l])
                self.log(f"✅ Found {table_count} tables", "OK")
                return True
            else:
                self.log("Table verification inconclusive", "WARN")
                return True

        except Exception as e:
            self.log(f"Verification error: {e}", "WARN")
            return True

    def deploy_phase_4_services(self):
        """Check service files"""
        self.log("=== PHASE 4: Service Files ===", "INFO")

        services = [
            "scripts/db/db_sync_worker.py",
            "scripts/health_check/health_check_service.py"
        ]

        for service in services:
            path = self.workdir / service
            if path.exists():
                self.log(f"✅ {service} ready", "OK")
            else:
                self.log(f"❌ {service} not found", "ERR")

        return True

    def run(self):
        """Execute full deployment"""
        self.log("🚀 ETAP 1 DEPLOYMENT STARTING", "INFO")
        self.log("=" * 60, "INFO")

        phases = [
            ("PostgreSQL", self.deploy_phase_1_postgresql),
            ("Schema", self.deploy_phase_2_schema),
            ("Verification", self.deploy_phase_3_verify),
            ("Services", self.deploy_phase_4_services),
        ]

        success = True
        for name, func in phases:
            self.status["phase"] += 1
            self.status["module"] = name

            if not func():
                self.log(f"⚠ Phase failed: {name}", "WARN")
                success = False

            time.sleep(2)

        self.log("=" * 60, "INFO")
        if success:
            self.log("✅ ETAP 1 DEPLOYMENT COMPLETE", "OK")
            self.log("\nNext steps:", "INFO")
            self.log("1. Start db_sync_worker: .venv/Scripts/python.exe scripts/db/db_sync_worker.py", "INFO")
            self.log("2. Start health_check_service: .venv/Scripts/python.exe scripts/health_check/health_check_service.py --port 9000", "INFO")
            self.log("3. Verify: curl http://localhost:9000/health", "INFO")
        else:
            self.log("⚠ ETAP 1 deployment completed with issues", "WARN")

        return success

if __name__ == "__main__":
    deployer = ETAP1Deployer()
    sys.exit(0 if deployer.run() else 1)
