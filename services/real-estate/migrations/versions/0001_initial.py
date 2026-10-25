"""initial projects table

Revision ID: 0001
Revises:
Create Date: 2026-07-24
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("reg_no", sa.String(), primary_key=True),
        sa.Column("project_name", sa.String(), nullable=False, server_default=""),
        sa.Column("promoter", sa.String(), nullable=False, server_default=""),
        sa.Column("distressed_builder", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_table("projects")
