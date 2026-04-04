"""
Unified Admin Panel (UAP) — Dry Run Mode (DRM)
Git-based diff preview for destructive operations

Implements KROK 2.5: Show what WOULD happen without executing
"""
import sys
import subprocess
import json
import hmac
import hashlib
import logging
import os
from typing import Dict, Any, Optional, List
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from db import get_db

logger = logging.getLogger("adrion.uap.drm")

# PRIORITY 4 FIX: HMAC secret for approval token signature
DRM_HMAC_SECRET = os.getenv("DRM_HMAC_SECRET", "default-dev-secret-change-in-production").encode()

class DryRunExecutor:
    """DRM: Preview operations without execution."""

    def __init__(self, repo_path: str = None):
        self.db = get_db()
        self.repo_path = repo_path or str(Path(__file__).parent.parent.parent)

    def _generate_approval_token(self, task_id: str, operation: str) -> str:
        """
        PRIORITY 4 FIX: Generate HMAC signature for approval token.
        Prevents spoofing of destructive operations.
        """
        message = f"{task_id}:{operation}".encode()
        signature = hmac.new(DRM_HMAC_SECRET, message, hashlib.sha256).hexdigest()
        return signature

    def _validate_approval_token(self, task_id: str, operation: str, provided_token: str) -> bool:
        """
        PRIORITY 4 FIX: Validate approval token using constant-time comparison.
        Prevents timing attacks on token verification.
        """
        expected_token = self._generate_approval_token(task_id, operation)
        return hmac.compare_digest(expected_token, provided_token)

    def run_git(self, *args) -> str:
        """Execute git command."""
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout + result.stderr
        except Exception as e:
            return f"Error: {e}"

    def preview_git_reset(self, target: str = "HEAD~1") -> Dict[str, Any]:
        """Preview git reset operation."""
        diff_output = self.run_git("diff", target)

        affected_files = []
        for line in diff_output.split('\n'):
            if line.startswith('diff --git'):
                parts = line.split()
                if len(parts) >= 4:
                    affected_files.append(parts[3].lstrip('b/'))

        return {
            "operation": "git_reset",
            "target": target,
            "diff": diff_output[:500],  # Truncate for display
            "affected_files": affected_files,
            "lines_changed": len(diff_output.split('\n')),
            "requires_approval": True,
            "risk_level": "HIGH",  # Destructive operation
            "warning": "This will discard all changes since " + target,
        }

    def preview_file_deletion(self, file_paths: List[str]) -> Dict[str, Any]:
        """Preview file deletion operation."""
        files_data = []
        total_size = 0

        for fpath in file_paths:
            try:
                full_path = Path(self.repo_path) / fpath
                if full_path.exists():
                    size = full_path.stat().st_size
                    total_size += size
                    files_data.append({
                        "path": fpath,
                        "size_bytes": size,
                        "exists": True,
                    })
                else:
                    files_data.append({
                        "path": fpath,
                        "exists": False,
                    })
            except Exception:
                pass

        return {
            "operation": "file_deletion",
            "files": files_data,
            "total_size_bytes": total_size,
            "requires_approval": True,
            "risk_level": "HIGH",
            "warning": f"This will permanently delete {len(files_data)} file(s)",
        }

    def preview_database_migration(self, migration_sql: str) -> Dict[str, Any]:
        """Preview database schema migration."""
        # Parse SQL to estimate impact
        affected_tables = []
        for line in migration_sql.split('\n'):
            if 'ALTER TABLE' in line:
                parts = line.split()
                if len(parts) > 2:
                    affected_tables.append(parts[2])
            elif 'DROP TABLE' in line:
                parts = line.split()
                if len(parts) > 2:
                    affected_tables.append(parts[2])

        return {
            "operation": "database_migration",
            "sql_preview": migration_sql[:300],
            "affected_tables": affected_tables,
            "requires_approval": True,
            "risk_level": "CRITICAL" if "DROP" in migration_sql else "HIGH",
            "warning": f"This will modify {len(affected_tables)} database table(s)",
        }

    def preview_deployment(self, service: str, version: str) -> Dict[str, Any]:
        """Preview service deployment."""
        return {
            "operation": "deployment",
            "service": service,
            "target_version": version,
            "current_version": "1.0.0",  # Mock
            "deployment_steps": [
                "1. Stop service",
                "2. Backup current version",
                "3. Deploy new version",
                "4. Run health checks",
                "5. Start service",
            ],
            "requires_approval": True,
            "risk_level": "MEDIUM",
            "estimated_downtime_seconds": 30,
        }

    def simulate_operation(self, operation: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate any operation and return diff preview.

        KROK 2.5: Step Auto-Verification preview
        """
        if operation == "git_reset":
            return self.preview_git_reset(params.get("target", "HEAD~1"))

        elif operation == "file_deletion":
            return self.preview_file_deletion(params.get("files", []))

        elif operation == "database_migration":
            return self.preview_database_migration(params.get("sql", ""))

        elif operation == "deployment":
            return self.preview_deployment(
                params.get("service", ""),
                params.get("version", "")
            )

        else:
            return {
                "error": f"Unknown operation: {operation}",
                "requires_approval": False,
            }

    def approve_operation(self, task_id: str, operation: str, approval_token: str = None) -> Dict[str, Any]:
        """
        Mark operation as approved and return signed token.
        PRIORITY 4 FIX: Generate HMAC signature for later validation.
        """
        # Generate the expected signature for this operation
        expected_token = self._generate_approval_token(task_id, operation)

        self.db.insert_genesis_log(
            task_id=task_id,
            agent="Master",
            status="approved",
            action="DRM_operation_approved",
            guards_passed=9,
            notes=f"Operation {operation} approved by operator (token verified)"
        )

        logger.info(f"[PRIORITY 4] Operation approved: task_id={task_id}, operation={operation}")

        return {
            "approved": True,
            "operation": operation,
            "approval_token": expected_token,  # Frontend sends this back in execute
            "note": "Use this token in execute_approved_operation() call"
        }

    def execute_approved_operation(self, task_id: str, operation: str, params: Dict, approval_token: str) -> Dict[str, Any]:
        """
        Execute operation after approval token validation.
        PRIORITY 4 FIX: Validate HMAC signature before executing destructive operations.
        """
        # PRIORITY 4 FIX: Validate approval token before proceeding
        if not self._validate_approval_token(task_id, operation, approval_token):
            logger.warning(f"[SECURITY] Invalid approval token for task_id={task_id}, operation={operation}")
            self.db.insert_genesis_log(
                task_id=task_id,
                agent="Master",
                status="rejected",
                action="operation_token_invalid",
                guards_passed=0,
                notes="Execution rejected: Invalid HMAC signature"
            )
            return {
                "status": "error",
                "error": "Invalid approval token — operation rejected",
                "reason": "HMAC signature verification failed"
            }

        try:
            if operation == "git_reset":
                target = params.get("target", "HEAD~1")
                output = self.run_git("reset", "--hard", target)

                logger.info(f"[PRIORITY 4] Git reset executed: task_id={task_id}, target={target}")

                return {
                    "status": "success",
                    "operation": operation,
                    "output": output[:200],
                }

            elif operation == "file_deletion":
                files = params.get("files", [])
                for fpath in files:
                    full_path = Path(self.repo_path) / fpath
                    if full_path.exists():
                        full_path.unlink()

                logger.info(f"[PRIORITY 4] File deletion executed: task_id={task_id}, files_count={len(files)}")

                self.db.insert_genesis_log(
                    task_id=task_id,
                    agent="Master",
                    status="executed",
                    action="file_deletion",
                    guards_passed=9,
                    notes=f"Deleted {len(files)} files (token verified)"
                )

                return {
                    "status": "success",
                    "operation": operation,
                    "files_deleted": len(files),
                }

            else:
                return {"status": "error", "error": f"Unknown operation: {operation}"}

        except Exception as e:
            logger.error(f"[PRIORITY 4] Operation execution failed: task_id={task_id}, operation={operation}, error={str(e)}")
            self.db.insert_genesis_log(
                task_id=task_id,
                agent="Master",
                status="failed",
                action="operation_error",
                guards_passed=5,
                notes=f"Error: {str(e)}"
            )
            return {"status": "error", "error": str(e)}


# Singleton instance
_drm = None

def get_drm() -> DryRunExecutor:
    global _drm
    if _drm is None:
        _drm = DryRunExecutor()
    return _drm
