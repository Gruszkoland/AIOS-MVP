"""Add webhook_sent column to saas_events

Tracks whether each event was successfully delivered via the webhook worker.
NULL = not yet attempted, TRUE = delivered, FALSE = all retries exhausted.

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-07 00:01:00.000000 UTC
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("saas_events") as batch_op:
        batch_op.add_column(
            sa.Column(
                "webhook_sent",
                sa.Boolean,
                nullable=True,
                server_default=None,
                comment="NULL=pending, True=delivered, False=failed all retries",
            )
        )
        batch_op.add_column(
            sa.Column(
                "webhook_attempts",
                sa.Integer,
                nullable=False,
                server_default="0",
                comment="Number of delivery attempts made",
            )
        )
    op.create_index(
        "ix_saas_events_webhook_sent",
        "saas_events",
        ["webhook_sent"],
    )


def downgrade() -> None:
    op.drop_index("ix_saas_events_webhook_sent", table_name="saas_events")
    with op.batch_alter_table("saas_events") as batch_op:
        batch_op.drop_column("webhook_attempts")
        batch_op.drop_column("webhook_sent")
