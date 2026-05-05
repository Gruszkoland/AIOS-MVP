#!/usr/bin/env python3
"""
ADRION 369 v4.0 - DATABASE SYNC WORKER
Synchronizes in-memory TASKS_STORE to PostgreSQL for persistence.
Prevents data loss and enables state recovery across restarts.

Usage:
    python scripts/db_sync_worker.py --interval 5 --batch-size 100 --log-level INFO
"""

import asyncio
import logging
import os
import sys
import json
import time
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional, Dict, List, Any
from enum import Enum
import uuid

import psycopg2
from psycopg2.extras import Json, RealDictCursor
from psycopg2.pool import SimpleConnectionPool
import click

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)-8s | %(message)s',
    handlers=[
        logging.FileHandler('/var/log/adrion/db_sync_worker.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


# ============================================================================
# DATA MODELS
# ============================================================================

class TaskStatus(Enum):
    """Task execution status"""
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'


@dataclass
class Task:
    """In-memory task representation"""
    id: str
    agent_id: str
    task_name: str
    status: str = TaskStatus.PENDING.value
    priority: int = 0
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int = 0

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'agent_id': self.agent_id,
            'task_name': self.task_name,
            'status': self.status,
            'priority': self.priority,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'metadata': self.metadata,
            'result_data': self.result_data,
            'error_message': self.error_message,
            'retry_count': self.retry_count
        }


# ============================================================================
# DATABASE CONNECTION POOL
# ============================================================================

class DatabasePool:
    """PostgreSQL connection pool management"""

    def __init__(self, dsn: str, min_connections: int = 2, max_connections: int = 10):
        self.dsn = dsn
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.pool = None
        self.connected = False

    def connect(self):
        """Initialize connection pool"""
        try:
            self.pool = SimpleConnectionPool(
                self.min_connections,
                self.max_connections,
                self.dsn
            )
            self.connected = True
            logger.info(f"✅ Database pool connected ({self.min_connections}-{self.max_connections} connections)")
        except psycopg2.Error as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            self.connected = False
            raise

    def get_connection(self):
        """Get connection from pool"""
        if not self.connected or self.pool is None:
            raise RuntimeError("Database pool not connected")
        return self.pool.getconn()

    def return_connection(self, conn):
        """Return connection to pool"""
        if self.pool:
            self.pool.putconn(conn)

    def close(self):
        """Close all connections in pool"""
        if self.pool:
            self.pool.closeall()
            self.connected = False
            logger.info("Database pool closed")


# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

class TaskRepository:
    """Data access layer for tasks"""

    def __init__(self, pool: DatabasePool):
        self.pool = pool

    def insert_or_update_task(self, task: Task) -> bool:
        """Insert new task or update existing (upsert)"""
        conn = self.pool.get_connection()
        try:
            with conn.cursor() as cur:
                # PostgreSQL UPSERT (INSERT ... ON CONFLICT ... DO UPDATE)
                query = """
                    INSERT INTO tasks (
                        id, agent_id, task_name, status, priority,
                        created_at, started_at, completed_at, metadata,
                        result_data, error_message, retry_count
                    ) VALUES (
                        %(id)s, %(agent_id)s, %(task_name)s, %(status)s, %(priority)s,
                        %(created_at)s, %(started_at)s, %(completed_at)s, %(metadata)s,
                        %(result_data)s, %(error_message)s, %(retry_count)s
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        status = EXCLUDED.status,
                        started_at = EXCLUDED.started_at,
                        completed_at = EXCLUDED.completed_at,
                        metadata = EXCLUDED.metadata,
                        result_data = EXCLUDED.result_data,
                        error_message = EXCLUDED.error_message,
                        retry_count = EXCLUDED.retry_count,
                        updated_at = CURRENT_TIMESTAMP
                """

                cur.execute(query, {
                    'id': uuid.UUID(task.id),
                    'agent_id': task.agent_id,
                    'task_name': task.task_name,
                    'status': task.status,
                    'priority': task.priority,
                    'created_at': task.created_at,
                    'started_at': task.started_at,
                    'completed_at': task.completed_at,
                    'metadata': Json(task.metadata),
                    'result_data': Json(task.result_data) if task.result_data else None,
                    'error_message': task.error_message,
                    'retry_count': task.retry_count
                })

                conn.commit()
                return True

        except psycopg2.Error as e:
            conn.rollback()
            logger.error(f"Failed to upsert task {task.id}: {e}")
            return False
        finally:
            self.pool.return_connection(conn)

    def batch_insert_or_update_tasks(self, tasks: List[Task]) -> int:
        """Batch insert/update multiple tasks"""
        conn = self.pool.get_connection()
        successful = 0

        try:
            with conn.cursor() as cur:
                for task in tasks:
                    try:
                        query = """
                            INSERT INTO tasks (
                                id, agent_id, task_name, status, priority,
                                created_at, started_at, completed_at, metadata,
                                result_data, error_message, retry_count
                            ) VALUES (
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                            )
                            ON CONFLICT (id) DO UPDATE SET
                                status = EXCLUDED.status,
                                started_at = EXCLUDED.started_at,
                                completed_at = EXCLUDED.completed_at,
                                metadata = EXCLUDED.metadata,
                                result_data = EXCLUDED.result_data,
                                error_message = EXCLUDED.error_message,
                                retry_count = EXCLUDED.retry_count,
                                updated_at = CURRENT_TIMESTAMP
                        """

                        cur.execute(query, (
                            uuid.UUID(task.id),
                            task.agent_id,
                            task.task_name,
                            task.status,
                            task.priority,
                            task.created_at,
                            task.started_at,
                            task.completed_at,
                            Json(task.metadata),
                            Json(task.result_data) if task.result_data else None,
                            task.error_message,
                            task.retry_count
                        ))

                        successful += 1

                    except psycopg2.Error as e:
                        logger.warning(f"Failed to sync task {task.id}: {e}")
                        continue

                conn.commit()
                logger.info(f"✅ Synced {successful}/{len(tasks)} tasks to PostgreSQL")

        except psycopg2.Error as e:
            conn.rollback()
            logger.error(f"Batch sync failed: {e}")
        finally:
            self.pool.return_connection(conn)

        return successful

    def get_all_tasks(self) -> List[Task]:
        """Retrieve all tasks from database"""
        conn = self.pool.get_connection()
        tasks = []

        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM tasks ORDER BY created_at DESC LIMIT 1000")
                rows = cur.fetchall()

                for row in rows:
                    task = Task(
                        id=str(row['id']),
                        agent_id=row['agent_id'],
                        task_name=row['task_name'],
                        status=row['status'],
                        priority=row['priority'],
                        created_at=row['created_at'],
                        started_at=row['started_at'],
                        completed_at=row['completed_at'],
                        metadata=row['metadata'] or {},
                        result_data=row['result_data'],
                        error_message=row['error_message'],
                        retry_count=row['retry_count']
                    )
                    tasks.append(task)

        except psycopg2.Error as e:
            logger.error(f"Failed to retrieve tasks: {e}")
        finally:
            self.pool.return_connection(conn)

        return tasks

    def health_check(self) -> bool:
        """Test database connectivity"""
        conn = self.pool.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                result = cur.fetchone()
                return result is not None
        except psycopg2.Error as e:
            logger.error(f"Health check failed: {e}")
            return False
        finally:
            self.pool.return_connection(conn)


# ============================================================================
# SYNC WORKER
# ============================================================================

class SyncWorker:
    """Main synchronization worker"""

    def __init__(
        self,
        db_url: str,
        interval_seconds: int = 5,
        batch_size: int = 100,
        log_level: str = 'INFO',
        task_store_getter=None,
    ):
        self.interval_seconds = interval_seconds
        self.batch_size = batch_size
        self.pool = DatabasePool(db_url)
        self.repository = TaskRepository(self.pool)
        self.running = False
        self.stats = {
            'synced_count': 0,
            'failed_syncs': 0,
            'last_sync_time': None,
            'uptime_seconds': 0
        }
        self.start_time = None
        self._task_store_getter = task_store_getter

        # Set logging level
        logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    async def start(self):
        """Start the sync worker"""
        logger.info("🚀 DB Sync Worker starting...")
        self.running = True
        self.start_time = time.time()

        try:
            self.pool.connect()
            logger.info(f"📊 Sync interval: {self.interval_seconds}s, batch size: {self.batch_size}")

            # Health check
            if not self.repository.health_check():
                raise RuntimeError("Database health check failed")

            logger.info("✅ Database health check passed")

            # Main sync loop
            while self.running:
                try:
                    await self._sync_cycle()
                    await asyncio.sleep(self.interval_seconds)

                except KeyboardInterrupt:
                    logger.info("⏹️  Graceful shutdown...")
                    break
                except Exception as e:
                    logger.error(f"Sync cycle error: {e}")
                    self.stats['failed_syncs'] += 1
                    await asyncio.sleep(self.interval_seconds)

        finally:
            self._shutdown()

    async def _sync_cycle(self):
        """Single synchronization cycle"""
        # TODO: Replace with actual in-memory TASKS_STORE from your application
        # Example: tasks = get_tasks_from_application_memory()
        tasks = self._get_sample_tasks()  # Placeholder

        if tasks:
            synced = self.repository.batch_insert_or_update_tasks(tasks)
            self.stats['synced_count'] += synced
            self.stats['last_sync_time'] = datetime.utcnow().isoformat()

            # Update uptime
            if self.start_time:
                self.stats['uptime_seconds'] = int(time.time() - self.start_time)

    def _get_sample_tasks(self) -> List[Task]:
        """
        Retrieve tasks from application TASKS_STORE (or external callable).

        Returns Task objects converted from the in-memory store dict format:
            { task_id: { "agent": str, "task_description": str, "status": str, ... } }
        """
        if self._task_store_getter is None:
            return []

        try:
            raw_store = self._task_store_getter()
            if not raw_store:
                return []

            tasks = []
            for task_id, data in raw_store.items():
                tasks.append(Task(
                    id=task_id if len(task_id) >= 32 else task_id.ljust(32, "0"),
                    agent_id=data.get("agent", "unknown"),
                    task_name=data.get("task_description", "")[:255],
                    status=data.get("status", "pending"),
                    priority=data.get("priority", 0),
                    metadata=data,
                ))
            return tasks[:self.batch_size]
        except Exception as e:
            logger.warning("Failed to retrieve tasks from store: %s", e)
            return []

    def _shutdown(self):
        """Graceful shutdown"""
        self.running = False
        self.pool.close()
        logger.info(f"📊 Final stats: {self.stats}")
        logger.info("✅ DB Sync Worker stopped")


# ============================================================================
# CLI INTERFACE
# ============================================================================

@click.command()
@click.option(
    '--db-url',
    default=None,
    help='PostgreSQL connection string (or use DATABASE_URL env var)'
)
@click.option(
    '--interval',
    default=5,
    type=int,
    help='Sync interval in seconds'
)
@click.option(
    '--batch-size',
    default=100,
    type=int,
    help='Number of tasks to sync per batch'
)
@click.option(
    '--log-level',
    default='INFO',
    type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']),
    help='Logging level'
)
def main(db_url: str, interval: int, batch_size: int, log_level: str):
    """ADRION 369 Database Sync Worker

    Continuously synchronizes in-memory tasks to PostgreSQL for persistence.
    """

    # Get database URL from parameter or environment
    if not db_url:
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            logger.error("❌ DATABASE_URL not set. Provide --db-url or set DATABASE_URL env var")
            sys.exit(1)

    logger.info(f"Database: {db_url.split('@')[1] if '@' in db_url else 'localhost'}")
    logger.info(f"Sync Interval: {interval}s | Batch Size: {batch_size}")

    worker = SyncWorker(
        db_url=db_url,
        interval_seconds=interval,
        batch_size=batch_size,
        log_level=log_level
    )

    # Run async worker
    try:
        asyncio.run(worker.start())
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
