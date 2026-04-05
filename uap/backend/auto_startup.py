"""
Auto-Startup System — Autonomous startup sequence for ADRION 369

Executes on system start:
1. Health Check (K8s, DB, API, Ollama)
2. Session Recovery (restore previous session)
3. Task Resume (continue incomplete tasks)
4. Self-Healing (auto-heal detected issues)
"""

import json
import logging
import subprocess
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger("adrion.uap.auto_startup")


class AutoStartupSequence:
    """Orchestrates autonomous startup sequence."""

    def __init__(self, session_manager, db_instance, chat_orchestrator=None):
        """
        Initialize auto-startup.

        Args:
            session_manager: SessionManager instance
            db_instance: PostgreSQL DB instance
            chat_orchestrator: ChatOrchestrator for autonomous actions
        """
        self.sm = session_manager
        self.db = db_instance
        self.chat = chat_orchestrator
        self.startup_log: List[Dict] = []

    def run_full_sequence(self, user_id: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Run complete auto-startup sequence.

        Returns:
            {
                "status": "success|warning|error",
                "timestamp": ISO datetime,
                "steps": [
                    {"step": 1, "name": "Health Check", "status": "passed", "details": "..."},
                    ...
                ],
                "session_id": "...",
                "summary": "..."
            }
        """
        context = context or {}
        timestamp = datetime.now().isoformat()

        self.startup_log = []
        session_id = None

        try:
            # STEP 1: Health Check
            health_result = self.run_health_check()
            self._log_step(1, "Health Check", health_result)

            # STEP 2: Session Recovery
            session_id = self.recover_previous_session(user_id)
            recovery_result = "recovered" if session_id else "new_session"
            self._log_step(2, "Session Recovery", recovery_result)

            # If no previous session, create new one
            if not session_id:
                session_id = self.sm.create_session(user_id, context)
                self._log_step(2, "Session Creation", f"created {str(session_id)[:8]}...")

            # STEP 3: Task Resume
            if session_id:
                resume_result = self.resume_incomplete_tasks(session_id)
                self._log_step(3, "Task Resume", resume_result)

            # STEP 4: Self-Healing
            if self.chat and health_result.get("status") in ["warning", "error"]:
                heal_result = self.auto_heal(session_id)
                self._log_step(4, "Self-Healing", heal_result)
            else:
                self._log_step(4, "Self-Healing", "skipped (no issues detected)")

            # Determine overall status
            overall_status = self._determine_status()

            return {
                "status": overall_status,
                "timestamp": timestamp,
                "steps": self.startup_log,
                "session_id": session_id,
                "summary": self._generate_summary(),
            }

        except Exception as e:
            logger.error(f"❌ Auto-startup sequence failed: {str(e)}")
            return {
                "status": "error",
                "timestamp": timestamp,
                "steps": self.startup_log,
                "session_id": session_id,
                "summary": f"❌ Startup error: {str(e)}",
            }

    # ┌─────────────────────────────────────────────────────────────────────┐
    # │ STEP 1: HEALTH CHECK                                                │
    # └─────────────────────────────────────────────────────────────────────┘

    def run_health_check(self) -> Dict[str, Any]:
        """
        Check system health across all components.

        Returns:
            {
                "status": "healthy|warning|error",
                "checks": {
                    "kubernetes": {"status": "...", "detail": "..."},
                    "database": {...},
                    "backend_api": {...},
                    "ollama": {...}
                }
            }
        """
        checks = {
            "kubernetes": self._check_kubernetes(),
            "database": self._check_database(),
            "backend_api": self._check_backend_api(),
            "ollama": self._check_ollama(),
        }

        # Determine overall status
        statuses = [c.get("status") for c in checks.values()]
        if "error" in statuses:
            overall_status = "error"
        elif "warning" in statuses:
            overall_status = "warning"
        else:
            overall_status = "healthy"

        logger.info(f"🏥 Health check completed: {overall_status}")

        return {
            "status": overall_status,
            "checks": checks,
        }

    def _check_kubernetes(self) -> Dict[str, str]:
        """Check Kubernetes cluster status."""
        try:
            result = subprocess.run(
                ["kubectl", "cluster-info"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return {"status": "healthy", "detail": "K8s cluster running"}
            else:
                return {"status": "error", "detail": "kubectl failed"}
        except Exception as e:
            return {"status": "error", "detail": f"K8s check failed: {str(e)}"}

    def _check_database(self) -> Dict[str, str]:
        """Check PostgreSQL database connectivity."""
        try:
            with self.db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    return {"status": "healthy", "detail": "PostgreSQL responding"}
        except Exception as e:
            return {"status": "error", "detail": f"DB error: {str(e)}"}

    def _check_backend_api(self) -> Dict[str, str]:
        """Check Backend API (port 8002) responsiveness."""
        try:
            import urllib.request

            response = urllib.request.urlopen("http://localhost:8002/mapi/v1/status", timeout=3)
            if response.status == 200:
                return {"status": "healthy", "detail": "Backend API responding"}
            else:
                return {"status": "warning", "detail": f"API returned {response.status}"}
        except Exception as e:
            return {"status": "error", "detail": f"API check failed: {str(e)}"}

    def _check_ollama(self) -> Dict[str, str]:
        """Check Ollama LLM availability (port 11434)."""
        try:
            import urllib.request

            response = urllib.request.urlopen("http://localhost:11434/api/models", timeout=3)
            if response.status == 200:
                return {"status": "healthy", "detail": "Ollama responding"}
            else:
                return {"status": "warning", "detail": "Ollama available"}
        except Exception as e:
            return {"status": "warning", "detail": "Ollama not available (optional)"}

    # ┌─────────────────────────────────────────────────────────────────────┐
    # │ STEP 2: SESSION RECOVERY                                            │
    # └─────────────────────────────────────────────────────────────────────┘

    def recover_previous_session(self, user_id: str, max_age_hours: int = 24) -> Optional[str]:
        """
        Recover previous session if available (within max_age_hours).

        Returns:
            Previous session_id or None
        """
        try:
            session_id = self.sm.recover_previous_session(user_id, max_age_hours)
            if session_id:
                logger.info(f"🔄 Previous session recovered: {str(session_id)[:8]}...")
                return session_id
            else:
                logger.info(f"ℹ️  No previous session to recover for user: {user_id}")
                return None
        except Exception as e:
            logger.error(f"⚠️  Session recovery failed: {str(e)}")
            return None

    # ┌─────────────────────────────────────────────────────────────────────┐
    # │ STEP 3: TASK RESUME                                                 │
    # └─────────────────────────────────────────────────────────────────────┘

    def resume_incomplete_tasks(self, session_id: str) -> str:
        """
        Resume incomplete tasks from previous session.

        Returns:
            Message describing resume results
        """
        try:
            resume_tasks = self.sm.get_resumed_tasks(session_id)

            if not resume_tasks:
                logger.info(f"ℹ️  No tasks to resume in session {str(session_id)[:8]}...")
                return "no_tasks"

            count = len(resume_tasks)
            logger.info(f"🔄 Resuming {count} tasks from previous session")

            # Auto-resume top priority task (if chat orchestrator available)
            if self.chat and count > 0:
                task_id = self.chat._execute_continue(session_id)
                if task_id:
                    return f"resumed_{count}_tasks"

            return f"found_{count}_tasks"

        except Exception as e:
            logger.error(f"⚠️  Task resume failed: {str(e)}")
            return "error"

    # ┌─────────────────────────────────────────────────────────────────────┐
    # │ STEP 4: SELF-HEALING                                                │
    # └─────────────────────────────────────────────────────────────────────┘

    def auto_heal(self, session_id: str) -> str:
        """
        Auto-heal detected issues (if any).

        Returns:
            Message describing healing action
        """
        if not self.chat:
            logger.warning("⚠️  ChatOrchestrator not available for healing")
            return "skipped_no_orchestrator"

        try:
            # Initiate autonomous healing via chat_orchestrator
            result = self.chat._execute_heal(session_id, {})

            if result:
                logger.info(f"🔧 Auto-healing initiated: {result}")
                return f"healing_started_{result[:8]}"
            else:
                logger.info("ℹ️  No healing action needed")
                return "no_action_needed"

        except Exception as e:
            logger.error(f"⚠️  Auto-healing failed: {str(e)}")
            return "error"

    # ┌─────────────────────────────────────────────────────────────────────┐
    # │ LOGGING & STATUS                                                    │
    # └─────────────────────────────────────────────────────────────────────┘

    def _log_step(self, step_num: int, name: str, result: Any) -> None:
        """Log startup step."""
        status = "passed" if result else "failed"

        # Determine status based on result type
        if isinstance(result, dict):
            status = result.get("status", "unknown")
            detail = json.dumps(result)
        elif isinstance(result, str):
            detail = result
            if "error" in result.lower():
                status = "error"
            elif "warning" in result.lower():
                status = "warning"
            else:
                status = "passed"
        else:
            detail = str(result)

        self.startup_log.append(
            {
                "step": step_num,
                "name": name,
                "status": status,
                "detail": detail,
            }
        )

    def _determine_status(self) -> str:
        """Determine overall startup status from steps."""
        statuses = [step["status"] for step in self.startup_log]
        if any(s == "error" for s in statuses):
            return "error"
        elif any(s == "warning" for s in statuses):
            return "warning"
        else:
            return "success"

    def _generate_summary(self) -> str:
        """Generate human-readable summary."""
        status_counts = {}
        for step in self.startup_log:
            st = step["status"]
            status_counts[st] = status_counts.get(st, 0) + 1

        parts = []
        if status_counts.get("passed"):
            parts.append(f"✅ {status_counts['passed']} passed")
        if status_counts.get("warning"):
            parts.append(f"⚠️ {status_counts['warning']} warnings")
        if status_counts.get("error"):
            parts.append(f"❌ {status_counts['error']} errors")

        return " | ".join(parts) or "No steps executed"
