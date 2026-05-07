"""
Alembic migration environment — ADRION 369 micro-saas.

Supports:
  - SQLite  (dev)  via SAAS_DB_PATH env var (default: micro-saas/data/subscriptions.db)
  - PostgreSQL (prod) via DATABASE_URL env var when SAAS_DB_DRIVER=postgres
"""
from __future__ import annotations

import logging
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# ── Alembic Config object ─────────────────────────────────────────────────
config = context.config

# Populate Python logging from alembic.ini [loggers] section
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

logger = logging.getLogger("alembic.env")

# ── Resolve DB URL at runtime ─────────────────────────────────────────────

def _resolve_url() -> str:
    """
    Priority:
    1. SAAS_DB_DRIVER=postgres → DATABASE_URL (PostgreSQL)
    2. Fallback                → SQLite at SAAS_DB_PATH
    """
    driver = os.getenv("SAAS_DB_DRIVER", "sqlite").lower()
    if driver == "postgres":
        url = os.getenv("DATABASE_URL")
        if not url:
            raise RuntimeError(
                "SAAS_DB_DRIVER=postgres but DATABASE_URL is not set"
            )
        # SQLAlchemy 2.x requires 'postgresql+psycopg2://' not 'postgres://'
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg2://", 1)
        logger.info("Alembic using PostgreSQL: %s", url.split("@")[-1])
        return url
    else:
        db_path = os.getenv("SAAS_DB_PATH", "micro-saas/data/subscriptions.db")
        url = f"sqlite:///{db_path}"
        logger.info("Alembic using SQLite: %s", db_path)
        return url


# target_metadata = None  — we use raw SQL migrations, not declarative Base
target_metadata = None


# ── Offline migration (generate SQL script) ───────────────────────────────

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (no DB connection, emits SQL)."""
    url = _resolve_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ── Online migration (connect to DB and apply) ────────────────────────────

def run_migrations_online() -> None:
    """Run migrations against a live database connection."""
    url = _resolve_url()

    # Override sqlalchemy.url from alembic.ini (which intentionally omits it)
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # NullPool: safe for short-lived migration runs
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


# ── Entry point ───────────────────────────────────────────────────────────

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
