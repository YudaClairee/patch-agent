"""add hashed_password to users

Revision ID: a1b2c3d4e5f6
Revises: 880e8eba07d0
Create Date: 2026-05-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "880e8eba07d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "hashed_password",
            sqlmodel.sql.sqltypes.AutoString(length=1024),
            nullable=False,
            server_default="",
        ),
    )
    op.alter_column("users", "hashed_password", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "hashed_password")
