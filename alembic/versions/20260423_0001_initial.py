"""initial

Revision ID: 0001
Revises:
Create Date: 2026-04-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("gps_lat", sa.Float(), nullable=False),
        sa.Column("gps_lon", sa.Float(), nullable=False),
        sa.Column("hourly_irradiance", postgresql.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "charges",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("max_power_w", sa.Float(), nullable=False),
        sa.Column("real_usage_rate", sa.Float(), nullable=False),
        sa.Column("hourly_slots", postgresql.JSON(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("charges")
    op.drop_table("projects")
