import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, Relationship, SQLModel

from src.models.enums import IndexStatus

if TYPE_CHECKING:
    from src.models.repository import Repository


class CodebaseIndex(SQLModel, table=True):
    __tablename__ = "codebase_indexes"
    __table_args__ = (
        UniqueConstraint(
            "repository_id", "branch", name="uq_codebase_index_repo_branch"
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    repository_id: uuid.UUID = Field(
        sa_column=Column(
            PG_UUID(as_uuid=True),
            ForeignKey("repositories.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    branch: str = Field(max_length=255)
    indexed_commit_sha: str | None = Field(default=None, max_length=64)
    chroma_collection_name: str = Field(max_length=63)
    chunk_count: int = Field(default=0, nullable=False)
    status: IndexStatus = Field(
        sa_column=Column(SAEnum(IndexStatus, name="index_status"), nullable=False)
    )
    error_message: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    indexed_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )

    repository: "Repository" = Relationship(back_populates="codebase_indexes")
