"""add run_role and reviewer_run_id to agent_runs

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-05-16 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Postgres ENUM type name must match SAEnum(name=...) in the model
RUN_ROLE_ENUM = sa.Enum("developer", "reviewer", "fixer", name="run_role")


def upgrade() -> None:
    RUN_ROLE_ENUM.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "agent_runs",
        sa.Column(
            "run_role",
            RUN_ROLE_ENUM,
            nullable=False,
            server_default="developer",
        ),
    )
    op.add_column(
        "agent_runs",
        sa.Column(
            "reviewer_run_id",
            sa.UUID(),
            sa.ForeignKey("agent_runs.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("agent_runs", "reviewer_run_id")
    op.drop_column("agent_runs", "run_role")
    RUN_ROLE_ENUM.drop(op.get_bind(), checkfirst=True)
