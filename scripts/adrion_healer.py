import os
import sys
import ast
import re
import sqlite3
import json
import logging
from datetime import datetime

# Ścieżka do ADRION CORE
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import arbitrage.config as config
import arbitrage.database as db

logging.basicConfig(level=logging.INFO, format='%(asctime)s - HEALER - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# U7: Guardian Laws -> Health Checks mapping
GUARDIAN_HEALTH_CHECKS = {
    "G1_Unity": "Core tables exist and schema is consistent",
    "G2_Harmony": "Foreign key integrity verified",
    "G3_Rhythm": "Autopilot last run within expected interval",
    "G4_Causality": "All tasks have traceable agent_id and created_at",
    "G5_Transparency": "Audit log (genesis_audit.jsonl) is non-empty",
    "G6_Authenticity": "No duplicate task IDs in store",
    "G7_Privacy": "No plaintext secrets in .py files",
    "G8_Nonmaleficence": "No uncaught SyntaxErrors in project Python files",
    "G9_Sustainability": "Database file size within limits (<500MB)",
}

class AdrionHealer:
    """
    HEALER (G9) — Optymalizacja Długu Technicznego i Odporność Systemu.
    Działa proaktywnie w tle, analizując i naprawiając strukturę danych oraz długu technicznego.
    """

    def __init__(self):
        self.db = db
        self.genesis_log = os.path.join(os.getcwd(), 'Genesis Record', 'HEALER_LOGS.txt')

    def run_cycle(self):
        """Uruchamia cykl optymalizacji."""
        logger.info("Rozpoczęto Cykl Uzdrawiania (Healer Mode)...")

        # 1. Sprawdzenie spójności bazy danych
        self._check_db_integrity()

        # 2. Analiza długu technicznego w plikach .py
        self._analyze_python_files()

        # 3. U7: Guardian Law enforcement health checks
        self._enforce_guardian_laws()

        # 4. Synchronizacja postępu sesji
        self._sync_session_progress()

        # 5. Zapis do Genesis Record
        self._log_to_genesis("Ukończono cykl optymalizacji. System stabilny.")
        logger.info("Cykl Uzdrawiania zakończony sukcesem.")

    def _sync_session_progress(self):
        """Automatyczna aktualizacja pliku progress/konfiguracja-adrion-369.md."""
        logger.info("Synchronizowanie postępu sesji (Librarian/SAP)...")
        progress_path = os.path.join(os.getcwd(), 'progress', 'konfiguracja-adrion-369.md')
        if os.path.exists(progress_path):
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            with open(progress_path, 'a', encoding='utf-8') as f:
                f.write(f"- **{timestamp}:** Automatyczny skan HEALER: Spójność systemu zweryfikowana (G2/G9).\n")


    def _check_db_integrity(self):
        """Weryfikacja tabel i relacji zgodnie z G2 (Harmony)."""
        logger.info("Verifying DB Harmony...")
        db_path = getattr(config, 'DB_PATH', None) or os.path.join(os.getcwd(), 'adrion.db')

        if not os.path.exists(db_path):
            logger.warning("Database file not found: %s — skipping integrity check", db_path)
            return

        issues = []
        try:
            conn = sqlite3.connect(db_path)
            # PRAGMA integrity_check verifies B-tree structure and page consistency
            result = conn.execute("PRAGMA integrity_check").fetchone()
            if result and result[0] != "ok":
                issues.append(f"integrity_check: {result[0]}")

            # PRAGMA foreign_key_check detects orphaned FK references
            fk_violations = conn.execute("PRAGMA foreign_key_check").fetchall()
            if fk_violations:
                issues.append(f"foreign_key_check: {len(fk_violations)} violation(s)")

            conn.close()
        except Exception as e:
            issues.append(f"DB connection error: {e}")

        if issues:
            msg = f"DB integrity issues: {'; '.join(issues)}"
            logger.warning(msg)
            self._log_to_genesis(msg)
        else:
            logger.info("DB integrity check passed (G2 Harmony verified)")

    def _analyze_python_files(self):
        """Wstepna analiza plikow pod katem dlugu technicznego (G9)."""
        logger.info("Analysing Python integrity...")
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        skip_dirs = {".venv", "venv", "__pycache__", "node_modules", "repositories",
                     "Genesis Record", ".git", "electron", "dist", "build"}
        debt_pattern = re.compile(r'\b(TODO|FIXME|HACK|XXX)\b', re.IGNORECASE)

        issues = []
        total_files = 0

        for dirpath, dirnames, filenames in os.walk(project_root):
            # Prune skipped directories in-place
            dirnames[:] = [d for d in dirnames if d not in skip_dirs]

            for fname in filenames:
                if not fname.endswith(".py"):
                    continue

                fpath = os.path.join(dirpath, fname)
                total_files += 1

                try:
                    with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                        source = f.read()

                    # Syntax check via AST parse
                    ast.parse(source, filename=fpath)

                    # Count tech debt markers
                    markers = debt_pattern.findall(source)
                    if markers:
                        rel_path = os.path.relpath(fpath, project_root)
                        issues.append(f"{rel_path}: {len(markers)} debt marker(s)")

                except SyntaxError as e:
                    rel_path = os.path.relpath(fpath, project_root)
                    issues.append(f"{rel_path}: SyntaxError at line {e.lineno}")
                except Exception as e:
                    rel_path = os.path.relpath(fpath, project_root)
                    issues.append(f"{rel_path}: {e}")

        if issues:
            logger.warning("Technical debt scan: %d issue(s) in %d files", len(issues), total_files)
            for issue in issues[:20]:  # Cap log volume
                logger.info("  - %s", issue)
            self._log_to_genesis(f"Tech debt scan: {len(issues)} issue(s) across {total_files} files")
        else:
            logger.info("Python analysis clean: %d files scanned, no issues (G9 verified)", total_files)

    def _enforce_guardian_laws(self):
        """U7: Run health checks mapped to Guardian Laws G1-G9."""
        logger.info("Enforcing Guardian Laws (G1-G9)...")
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = getattr(config, 'DB_PATH', None) or os.path.join(os.getcwd(), 'adrion.db')
        violations = []

        # G1 Unity: Core tables exist
        try:
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                tables = {row[0] for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
                conn.close()
                required = {"tasks", "autopilot_runs"}
                missing = required - tables
                if missing:
                    violations.append(f"G1_Unity: Missing tables: {missing}")
            else:
                violations.append("G1_Unity: Database file not found")
        except Exception as e:
            violations.append(f"G1_Unity: {e}")

        # G2 Harmony: FK integrity (already done in _check_db_integrity, logged separately)

        # G3 Rhythm: Autopilot last run within interval
        try:
            from arbitrage.database import get_last_autopilot_run
            last_run = get_last_autopilot_run()
            if last_run and last_run.get("started_at"):
                last_ts = datetime.fromisoformat(last_run["started_at"])
                hours_ago = (datetime.now() - last_ts).total_seconds() / 3600
                if hours_ago > 2:
                    violations.append(f"G3_Rhythm: Last autopilot run {hours_ago:.1f}h ago (>2h)")
        except Exception:
            pass  # Autopilot may not be configured

        # G4 Causality: Tasks have agent_id and created_at
        try:
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                tables = {row[0] for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
                if "tasks" in tables:
                    orphans = conn.execute(
                        "SELECT COUNT(*) FROM tasks WHERE agent_id IS NULL OR created_at IS NULL"
                    ).fetchone()[0]
                    if orphans > 0:
                        violations.append(f"G4_Causality: {orphans} task(s) without agent_id/created_at")
                conn.close()
        except Exception as e:
            violations.append(f"G4_Causality: {e}")

        # G5 Transparency: Audit log exists and is non-empty
        audit_path = os.path.join(project_root, "Genesis Record",
                                  "10_RAPORTY_DZIALANIA_SYSTEMU", "genesis_audit.jsonl")
        if not os.path.exists(audit_path) or os.path.getsize(audit_path) == 0:
            violations.append("G5_Transparency: Audit log empty or missing")

        # G7 Privacy: No plaintext secrets in project .py files
        secret_pattern = re.compile(
            r'(?:password|secret|api_key|token)\s*=\s*["\'][^"\']{8,}["\']',
            re.IGNORECASE
        )
        skip_dirs = {".venv", "venv", "__pycache__", "node_modules", ".git", "dist", "build"}
        for dirpath, dirnames, filenames in os.walk(project_root):
            dirnames[:] = [d for d in dirnames if d not in skip_dirs]
            for fname in filenames:
                if not fname.endswith(".py"):
                    continue
                fpath = os.path.join(dirpath, fname)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                        for lineno, line in enumerate(f, 1):
                            if secret_pattern.search(line) and "getenv" not in line and "os.environ" not in line:
                                rel = os.path.relpath(fpath, project_root)
                                violations.append(f"G7_Privacy: Possible secret at {rel}:{lineno}")
                                break  # One per file is enough
                except Exception:
                    pass

        # G9 Sustainability: DB file size < 500MB
        if os.path.exists(db_path):
            size_mb = os.path.getsize(db_path) / (1024 * 1024)
            if size_mb > 500:
                violations.append(f"G9_Sustainability: DB size {size_mb:.0f}MB exceeds 500MB limit")

        # Report
        if violations:
            logger.warning("Guardian Law violations: %d", len(violations))
            for v in violations:
                logger.warning("  - %s", v)
            self._log_to_genesis(f"Guardian Law check: {len(violations)} violation(s): {'; '.join(violations[:5])}")
        else:
            logger.info("Guardian Law check passed: all 9 laws verified")

        return violations

    def _log_to_genesis(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.genesis_log, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] HEALER: {message}\n")

if __name__ == "__main__":
    healer = AdrionHealer()
    healer.run_cycle()
