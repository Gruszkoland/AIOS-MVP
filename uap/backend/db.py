"""
Unified Admin Panel (UAP) — PostgreSQL Integration
Replaces in-memory stores with persistent database

Database Schema:
- tasks table
- genesis_logs table
- checkpoints table
- agent_metrics table
"""
import json
import logging
import os
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

from psycopg2 import pool

logger = logging.getLogger("adrion.uap.db")

PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = int(os.getenv("PG_PORT", "5432"))
PG_DB = os.getenv("PG_DB", "genesis_record")
PG_USER = os.getenv("PG_USER", "adrion")
PG_PASSWORD = os.getenv("PG_PASSWORD", "adrion_pass")

# PRIORITY 3 FIX: Warn if using default credentials
if PG_PASSWORD == "adrion_pass":
    logger.warning(
        "[SECURITY] PostgreSQL password is not set — using insecure default 'adrion_pass'. "
        "Set PG_PASSWORD env var before exposing this service on a network."
    )
    if os.getenv("ENVIRONMENT") == "production":
        logger.critical("[SECURITY] PostgreSQL default password in PRODUCTION — refusing to start.")
        import sys
        sys.exit(1)

class PostgresDB:
    """PostgreSQL connection pool & operations."""

    def __init__(self):
        self.conn_string = f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}"
        self._pool = pool.ThreadedConnectionPool(2, 10, self.conn_string)
        self._init_schema()

    @contextmanager
    def get_conn(self):
        """Get a raw connection from the pool; caller is responsible for commit/rollback."""
        conn = self._pool.getconn()
        try:
            yield conn
        finally:
            self._pool.putconn(conn)

    @contextmanager
    def get_connection(self):
        """Context manager for database connections with automatic commit/rollback."""
        conn = self._pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self._pool.putconn(conn)

    def _init_schema(self):
        """Create tables if they don't exist."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Tasks table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS tasks (
                        task_id VARCHAR(64) PRIMARY KEY,
                        task_description TEXT NOT NULL,
                        assigned_agent VARCHAR(50) NOT NULL,
                        dry_run BOOLEAN DEFAULT FALSE,
                        budget_max FLOAT DEFAULT 1000,
                        status VARCHAR(20) DEFAULT 'submitted',
                        trust_score FLOAT,
                        result JSONB,
                        errors JSONB DEFAULT '[]',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE INDEX IF NOT EXISTS idx_tasks_agent ON tasks(assigned_agent);
                    CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
                    CREATE INDEX IF NOT EXISTS idx_tasks_created ON tasks(created_at);
                """)

                # Genesis logs table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS genesis_logs (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        task_id VARCHAR(64),
                        agent VARCHAR(50) NOT NULL,
                        status VARCHAR(20) NOT NULL,
                        action VARCHAR(100) NOT NULL,
                        guards_passed INT DEFAULT 9,
                        notes TEXT,
                        FOREIGN KEY (task_id) REFERENCES tasks(task_id) ON DELETE CASCADE
                    );
                    CREATE INDEX IF NOT EXISTS idx_genesis_agent ON genesis_logs(agent);
                    CREATE INDEX IF NOT EXISTS idx_genesis_timestamp ON genesis_logs(timestamp);
                    CREATE INDEX IF NOT EXISTS idx_genesis_action ON genesis_logs(action);
                """)

                # Checkpoints table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS checkpoints (
                        checkpoint_id VARCHAR(64) PRIMARY KEY,
                        label TEXT,
                        git_commit VARCHAR(40),
                        session_state JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE INDEX IF NOT EXISTS idx_checkpoints_created ON checkpoints(created_at);
                """)

                # Agent metrics table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS agent_metrics (
                        id SERIAL PRIMARY KEY,
                        agent VARCHAR(50) NOT NULL,
                        trust_score FLOAT,
                        pleasure FLOAT,
                        arousal FLOAT,
                        dominance FLOAT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE INDEX IF NOT EXISTS idx_metrics_agent ON agent_metrics(agent);
                    CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON agent_metrics(timestamp);
                """)

    # ────────────────────────────────────────────────────────────────────
    # TASKS
    # ────────────────────────────────────────────────────────────────────

    def insert_task(self, task_id: str, description: str, agent: str, dry_run: bool,
                    budget_max: float, trust_score: float) -> bool:
        """Insert new task."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO tasks
                    (task_id, task_description, assigned_agent, dry_run, budget_max, trust_score)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (task_id, description, agent, dry_run, budget_max, trust_score))
        return True

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task by ID."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT task_id, task_description, assigned_agent, dry_run, budget_max,
                           status, trust_score, result, errors, created_at, updated_at
                    FROM tasks WHERE task_id = %s
                """, (task_id,))
                row = cur.fetchone()
                if not row:
                    return None
                return {
                    "task_id": row[0],
                    "task_description": row[1],
                    "assigned_agent": row[2],
                    "dry_run": row[3],
                    "budget_max": row[4],
                    "status": row[5],
                    "trust_score": row[6],
                    "result": row[7],
                    "errors": row[8],
                    "created_at": row[9].isoformat() if row[9] else None,
                    "updated_at": row[10].isoformat() if row[10] else None,
                }

    def list_tasks(self, status: Optional[str] = None, agent: Optional[str] = None,
                   limit: int = 50) -> List[Dict[str, Any]]:
        """List tasks with optional filters."""
        query = "SELECT task_id, task_description, assigned_agent, status, trust_score, created_at FROM tasks WHERE 1=1"
        params = []

        if status:
            query += " AND status = %s"
            params.append(status)
        if agent:
            query += " AND assigned_agent = %s"
            params.append(agent)

        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                rows = cur.fetchall()
                return [
                    {
                        "task_id": row[0],
                        "task_description": row[1][:100],
                        "assigned_agent": row[2],
                        "status": row[3],
                        "trust_score": row[4],
                        "created_at": row[5].isoformat() if row[5] else None,
                    }
                    for row in rows
                ]

    def update_task_status(self, task_id: str, status: str, result: Optional[Dict] = None):
        """Update task status and/or result."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                if result:
                    cur.execute("""
                        UPDATE tasks SET status = %s, result = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE task_id = %s
                    """, (status, json.dumps(result), task_id))
                else:
                    cur.execute("""
                        UPDATE tasks SET status = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE task_id = %s
                    """, (status, task_id))

    # ────────────────────────────────────────────────────────────────────
    # GENESIS LOGS
    # ────────────────────────────────────────────────────────────────────

    def insert_genesis_log(self, task_id: str, agent: str, status: str, action: str,
                          guards_passed: int = 9, notes: str = "") -> bool:
        """Insert Genesis Record log entry."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO genesis_logs
                    (task_id, agent, status, action, guards_passed, notes)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (task_id, agent, status, action, guards_passed, notes))
        return True

    def query_genesis_logs(self, agent: Optional[str] = None, since_hours: int = 1,
                          status: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Query Genesis logs with filters."""
        query = """
            SELECT timestamp, task_id, agent, status, action, guards_passed, notes
            FROM genesis_logs
            WHERE timestamp > CURRENT_TIMESTAMP - (%s * INTERVAL '1 hour')
        """
        params = [since_hours]

        if agent:
            query += " AND agent = %s"
            params.append(agent)
        if status:
            query += " AND status = %s"
            params.append(status)

        query += " ORDER BY timestamp DESC LIMIT %s"
        params.append(limit)

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                rows = cur.fetchall()
                return [
                    {
                        "timestamp": row[0].isoformat() if row[0] else None,
                        "task_id": row[1],
                        "agent": row[2],
                        "status": row[3],
                        "action": row[4],
                        "guards_passed": row[5],
                        "notes": row[6],
                    }
                    for row in rows
                ]

    def export_genesis_logs(self) -> List[Dict[str, Any]]:
        """Export all Genesis logs."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT timestamp, task_id, agent, status, action, guards_passed, notes
                    FROM genesis_logs ORDER BY timestamp DESC
                """)
                rows = cur.fetchall()
                return [
                    {
                        "timestamp": row[0].isoformat() if row[0] else None,
                        "task_id": row[1],
                        "agent": row[2],
                        "status": row[3],
                        "action": row[4],
                        "guards_passed": row[5],
                        "notes": row[6],
                    }
                    for row in rows
                ]

    # ────────────────────────────────────────────────────────────────────
    # CHECKPOINTS
    # ────────────────────────────────────────────────────────────────────

    def insert_checkpoint(self, checkpoint_id: str, label: str, git_commit: str,
                         session_state: Dict) -> bool:
        """Insert checkpoint."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO checkpoints
                    (checkpoint_id, label, git_commit, session_state)
                    VALUES (%s, %s, %s, %s)
                """, (checkpoint_id, label, git_commit, json.dumps(session_state)))
        return True

    def list_checkpoints(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List all checkpoints."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT checkpoint_id, label, git_commit, created_at
                    FROM checkpoints ORDER BY created_at DESC LIMIT %s
                """, (limit,))
                rows = cur.fetchall()
                return [
                    {
                        "checkpoint_id": row[0],
                        "label": row[1],
                        "git_commit": row[2],
                        "created_at": row[3].isoformat() if row[3] else None,
                    }
                    for row in rows
                ]

    def get_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """Get checkpoint by ID."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT checkpoint_id, label, git_commit, session_state, created_at
                    FROM checkpoints WHERE checkpoint_id = %s
                """, (checkpoint_id,))
                row = cur.fetchone()
                if not row:
                    return None
                return {
                    "checkpoint_id": row[0],
                    "label": row[1],
                    "git_commit": row[2],
                    "session_state": row[3],
                    "created_at": row[4].isoformat() if row[4] else None,
                }

    # ────────────────────────────────────────────────────────────────────
    # AGENT METRICS
    # ────────────────────────────────────────────────────────────────────

    def insert_agent_metric(self, agent: str, trust_score: float, pleasure: float,
                           arousal: float, dominance: float) -> bool:
        """Insert agent EBDI metric."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO agent_metrics
                    (agent, trust_score, pleasure, arousal, dominance)
                    VALUES (%s, %s, %s, %s, %s)
                """, (agent, trust_score, pleasure, arousal, dominance))
        return True

    def get_latest_metrics(self, agent: str) -> Optional[Dict[str, Any]]:
        """Get latest metric for agent."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT agent, trust_score, pleasure, arousal, dominance, timestamp
                    FROM agent_metrics WHERE agent = %s
                    ORDER BY timestamp DESC LIMIT 1
                """, (agent,))
                row = cur.fetchone()
                if not row:
                    return None
                return {
                    "agent": row[0],
                    "trust_score": row[1],
                    "pleasure": row[2],
                    "arousal": row[3],
                    "dominance": row[4],
                    "timestamp": row[5].isoformat() if row[5] else None,
                }

    def cleanup(self):
        """Close all connections in the pool."""
        if hasattr(self, "_pool") and self._pool:
            self._pool.closeall()


# Singleton instance
_db = None

def get_db() -> PostgresDB:
    global _db
    if _db is None:
        _db = PostgresDB()
    return _db
