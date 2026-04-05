"""
Session Manager — Persistent user sessions with chat history and task recovery

Integrates with PostgreSQL to store:
- User sessions (create_at, last_seen_at, status)
- Chat messages (user ↔ orchestrator conversations)
- Task resume state (continue incomplete tasks from previous session)
"""

import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger("adrion.uap.session_manager")


class SessionManager:
    """Manages user sessions, chat history, and task recovery."""

    def __init__(self, db_instance):
        """
        Initialize with existing PostgreSQL connection.

        Args:
            db_instance: PostgresDB instance from db.py
        """
        self.db = db_instance
        self._init_schema()

    def _init_schema(self):
        """Create session tables if they don't exist."""
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                # Sessions table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        session_id UUID PRIMARY KEY,
                        user_id VARCHAR(255) NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        session_state JSONB DEFAULT '{}',
                        status VARCHAR(50) DEFAULT 'active',
                        is_auto_recovered BOOLEAN DEFAULT FALSE
                    );
                    CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
                    CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);
                    CREATE INDEX IF NOT EXISTS idx_sessions_last_seen ON sessions(last_seen_at);
                """)

                # Chat messages table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS chat_messages (
                        id SERIAL PRIMARY KEY,
                        session_id UUID NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
                        sender VARCHAR(20) NOT NULL,
                        message TEXT NOT NULL,
                        response_type VARCHAR(50),
                        genesis_logged BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                    );
                    CREATE INDEX IF NOT EXISTS idx_chat_session ON chat_messages(session_id);
                    CREATE INDEX IF NOT EXISTS idx_chat_sender ON chat_messages(sender);
                    CREATE INDEX IF NOT EXISTS idx_chat_created ON chat_messages(created_at);
                """)

                # Task resume state table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS task_resume_state (
                        task_id VARCHAR(64) PRIMARY KEY,
                        session_id UUID NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
                        status VARCHAR(50) NOT NULL,
                        previous_result JSONB,
                        resume_priority INT DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        resumed_at TIMESTAMP,
                        FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                    );
                    CREATE INDEX IF NOT EXISTS idx_task_resume_session ON task_resume_state(session_id);
                    CREATE INDEX IF NOT EXISTS idx_task_resume_status ON task_resume_state(status);
                """)

                logger.info("✅ Session schema initialized")

    # ╔════════════════════════════════════════════════════════════════════  ╗
    # ║  SESSION MANAGEMENT                                                 ║
    # ╚════════════════════════════════════════════════════════════════════  ╝

    def create_session(self, user_id: str, metadata: Optional[Dict] = None) -> str:
        """
        Create new user session.

        Args:
            user_id: User identifier
            metadata: Optional metadata (e.g., {"ip": "127.0.0.1", "device": "VS Code"})

        Returns:
            session_id (UUID)
        """
        session_id = str(uuid.uuid4())
        session_state = metadata or {}

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO sessions (session_id, user_id, session_state, status)
                    VALUES (%s, %s, %s, %s)
                """, (session_id, user_id, json.dumps(session_state), "active"))

        logger.info(f"📝 Session created: {session_id[:8]}... for user: {user_id}")
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID."""
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT session_id, user_id, created_at, last_seen_at, session_state, status, is_auto_recovered
                    FROM sessions WHERE session_id = %s
                """, (session_id,))
                row = cur.fetchone()
                if not row:
                    return None

                return {
                    "session_id": str(row[0]),
                    "user_id": row[1],
                    "created_at": row[2].isoformat() if row[2] else None,
                    "last_seen_at": row[3].isoformat() if row[3] else None,
                    "session_state": json.loads(row[4]) if row[4] else {},
                    "status": row[5],
                    "is_auto_recovered": row[6],
                }

    def list_previous_sessions(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        List previous sessions for user (for recovery).

        Returns:
            List of sessions sorted by last_seen_at DESC
        """
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT session_id, user_id, created_at, last_seen_at, status,
                           (SELECT COUNT(*) FROM chat_messages WHERE session_id = sessions.session_id) as msg_count,
                           (SELECT COUNT(*) FROM task_resume_state WHERE session_id = sessions.session_id) as task_count
                    FROM sessions
                    WHERE user_id = %s AND status IN ('closed', 'auto-resumed')
                    ORDER BY last_seen_at DESC
                    LIMIT %s
                """, (user_id, limit))
                rows = cur.fetchall()
                return [
                    {
                        "session_id": str(row[0]),
                        "user_id": row[1],
                        "created_at": row[2].isoformat() if row[2] else None,
                        "last_seen_at": row[3].isoformat() if row[3] else None,
                        "status": row[4],
                        "msg_count": row[5],
                        "task_count": row[6],
                    }
                    for row in rows
                ]

    def close_session(self, session_id: str) -> bool:
        """Close session (mark as 'closed')."""
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE sessions SET status = 'closed', last_seen_at = CURRENT_TIMESTAMP
                    WHERE session_id = %s
                """, (session_id,))
        logger.info(f"🔒 Session closed: {session_id[:8]}...")
        return True

    def update_last_seen(self, session_id: str) -> None:
        """Update last_seen_at timestamp."""
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE sessions SET last_seen_at = CURRENT_TIMESTAMP
                    WHERE session_id = %s
                """, (session_id,))

    # ╔════════════════════════════════════════════════════════════════════  ╗
    # ║  CHAT MESSAGE STORAGE                                               ║
    # ╚════════════════════════════════════════════════════════════════════  ╝

    def save_chat_message(
        self,
        session_id: str,
        sender: str,
        message: str,
        response_type: Optional[str] = None,
        genesis_logged: bool = False,
    ) -> int:
        """
        Save chat message to session.

        Args:
            session_id: Session ID
            sender: 'user' or 'orchestrator'
            message: Message text
            response_type: 'info', 'action', 'decision', etc.
            genesis_logged: Whether already logged to Genesis Record

        Returns:
            Message ID
        """
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO chat_messages
                    (session_id, sender, message, response_type, genesis_logged)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (session_id, sender, message, response_type, genesis_logged))
                msg_id = cur.fetchone()[0]

        self.update_last_seen(session_id)
        return msg_id

    def get_chat_history(self, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get chat message history for session."""
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, sender, message, response_type, created_at
                    FROM chat_messages
                    WHERE session_id = %s
                    ORDER BY created_at ASC
                    LIMIT %s
                """, (session_id, limit))
                rows = cur.fetchall()
                return [
                    {
                        "id": row[0],
                        "sender": row[1],
                        "message": row[2],
                        "response_type": row[3],
                        "created_at": row[4].isoformat() if row[4] else None,
                    }
                    for row in rows
                ]

    # ╔════════════════════════════════════════════════════════════════════  ╗
    # ║  TASK RECOVERY & RESUME                                             ║
    # ╚════════════════════════════════════════════════════════════════════  ╝

    def save_task_to_session(
        self,
        session_id: str,
        task_id: str,
        status: str,
        previous_result: Optional[Dict] = None,
        priority: int = 0,
    ) -> bool:
        """
        Save task state for recovery.

        Args:
            session_id: Session ID
            task_id: Task ID
            status: 'pending', 'paused', 'completed'
            previous_result: Task result from previous execution
            priority: Resume priority (higher = earlier)
        """
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO task_resume_state
                    (task_id, session_id, status, previous_result, resume_priority)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (task_id) DO UPDATE SET
                        status = EXCLUDED.status,
                        previous_result = EXCLUDED.previous_result,
                        resume_priority = EXCLUDED.resume_priority
                """, (task_id, session_id, status, json.dumps(previous_result or {}), priority))

        logger.info(f"💾 Task saved for recovery: {task_id[:8]}... (priority: {priority})")
        return True

    def get_resumed_tasks(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get tasks ready for resume from previous session.

        Returns:
            List of tasks sorted by resume_priority DESC
        """
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT task_id, status, previous_result, resume_priority, created_at
                    FROM task_resume_state
                    WHERE session_id = %s AND status IN ('pending', 'paused')
                    ORDER BY resume_priority DESC, created_at ASC
                """, (session_id,))
                rows = cur.fetchall()
                return [
                    {
                        "task_id": row[0],
                        "status": row[1],
                        "previous_result": json.loads(row[2]) if row[2] else {},
                        "resume_priority": row[3],
                        "created_at": row[4].isoformat() if row[4] else None,
                    }
                    for row in rows
                ]

    def mark_task_resumed(self, task_id: str) -> bool:
        """Mark task as resumed (completed recovery)."""
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE task_resume_state
                    SET status = 'completed', resumed_at = CURRENT_TIMESTAMP
                    WHERE task_id = %s
                """, (task_id,))
        return True

    # ╔════════════════════════════════════════════════════════════════════  ╗
    # ║  RECOVERY & AUTO-RESUME                                             ║
    # ╚════════════════════════════════════════════════════════════════════  ╝

    def recover_previous_session(self, user_id: str, max_age_hours: int = 24) -> Optional[str]:
        """
        Recover previous active session for user (auto-resume).

        Returns:
            Previous session_id or None if not found
        """
        cut_off_time = (datetime.now() - timedelta(hours=max_age_hours)).isoformat()

        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                # Find most recent session closed within time window
                cur.execute("""
                    SELECT session_id FROM sessions
                    WHERE user_id = %s AND status = 'closed' AND last_seen_at > %s
                    ORDER BY last_seen_at DESC
                    LIMIT 1
                """, (user_id, cut_off_time))
                row = cur.fetchone()

                if row:
                    session_id = row[0]
                    # Mark as auto-recovered
                    cur.execute("""
                        UPDATE sessions
                        SET status = 'auto-resumed', is_auto_recovered = TRUE, last_seen_at = CURRENT_TIMESTAMP
                        WHERE session_id = %s
                    """, (session_id,))
                    logger.info(f"🔄 Session auto-recovered: {str(session_id)[:8]}... for user: {user_id}")
                    return str(session_id)

        return None
