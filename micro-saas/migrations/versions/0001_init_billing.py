"""Init billing schema — subscriptions + saas_events

Revision ID: 0001
Revises:
Create Date: 2026-05-07 00:00:00.000000 UTC
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "subscriptions",
        sa.Column("sub_id", sa.Text, primary_key=True, nullable=False),
        sa.Column("user_id", sa.Text, nullable=False),
        sa.Column("tier", sa.Text, nullable=False, server_default="free"),
        sa.Column("status", sa.Text, nullable=False, server_default="active"),
        sa.Column("created_at", sa.Text, nullable=False),
        sa.Column("expires_at", sa.Text, nullable=True),
        sa.Column("bids_used_today", sa.Integer, nullable=False, server_default="0"),
        sa.Column("last_bid_date", sa.Text, nullable=True),
    )
    op.create_index("ix_subscriptions_user_id", "subscriptions", ["user_id"])
    op.create_index("ix_subscriptions_status", "subscriptions", ["status"])

    op.create_table(
        "saas_events",
        sa.Column("event_id", sa.Text, primary_key=True, nullable=False),
        sa.Column("sub_id", sa.Text, nullable=False),
        sa.Column("event_type", sa.Text, nullable=False),
        sa.Column("payload", sa.Text, nullable=True),
        sa.Column("created_at", sa.Text, nullable=False),
    )
    op.create_index("ix_saas_events_sub_id", "saas_events", ["sub_id"])
    op.create_index("ix_saas_events_event_type", "saas_events", ["event_type"])


def downgrade() -> None:
    op.drop_index("ix_saas_events_event_type", table_name="saas_events")
    op.drop_index("ix_saas_events_sub_id", table_name="saas_events")
    op.drop_table("saas_events")
    op.drop_index("ix_subscriptions_status", table_name="subscriptions")
    op.drop_index("ix_subscriptions_user_id", table_name="subscriptions")
    op.drop_table("subscriptions")
