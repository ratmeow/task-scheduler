"""Add task events.

Revision ID: 58a3c80e1b72
Revises: a4ef097f0364
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "58a3c80e1b72"
down_revision: str = "a4ef097f0364"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "task_events",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("task_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("details", postgresql.JSONB(), nullable=False),
        sa.Column("event_ts", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("action IN ('created', 'updated', 'deleted')", name="ck_task_events_action"),
    )


def downgrade() -> None:
    op.drop_table("task_events")
