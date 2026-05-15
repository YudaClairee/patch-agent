"""drop codebase_indexes table and add pr last_synced_at

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-13 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(op.f("ix_codebase_indexes_repository_id"), table_name="codebase_indexes")
    op.drop_table("codebase_indexes")
    op.execute("DROP TYPE IF EXISTS index_status")

    op.add_column(
        "pull_requests",
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("pull_requests", "last_synced_at")

    index_status = sa.Enum("pending", "indexing", "ready", "failed", name="index_status")
    index_status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "codebase_indexes",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("repository_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("branch", sa.String(length=255), nullable=False),
        sa.Column("indexed_commit_sha", sa.String(length=64), nullable=True),
        sa.Column("chroma_collection_name", sa.String(length=63), nullable=False),
        sa.Column("chunk_count", sa.Integer(), nullable=False),
        sa.Column("status", index_status, nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("indexed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("repository_id", "branch", name="uq_codebase_index_repo_branch"),
    )
    op.create_index(op.f("ix_codebase_indexes_repository_id"), "codebase_indexes", ["repository_id"])
