import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, DateTime, ForeignKey, Index, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, SQLModel

from src.core.config import settings


class CodeChunk(SQLModel, table=True):
    __tablename__ = "code_chunks"
    __table_args__ = (
        Index(
            "ix_code_chunks_repo_file_lines",
            "repository_id",
            "file_path",
            "start_line",
            "end_line",
        ),
        UniqueConstraint(
            "repository_id",
            "file_path",
            "start_line",
            "content_hash",
            name="uq_code_chunks_repo_path_start_hash",
        ),
        {"extend_existing": True},
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
    commit_sha: str | None = Field(default=None, max_length=64)
    file_path: str = Field(max_length=1024, nullable=False)
    language: str | None = Field(default=None, max_length=64)
    symbol_name: str | None = Field(default=None, max_length=255)
    symbol_type: str | None = Field(default=None, max_length=64)
    start_line: int = Field(nullable=False)
    end_line: int = Field(nullable=False)
    content: str = Field(sa_column=Column(Text, nullable=False))
    content_hash: str = Field(max_length=64, nullable=False)
    embedding: list[float] = Field(
        sa_column=Column(Vector(settings.embedding_dimensions), nullable=False)
    )
    created_at: datetime | None = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), nullable=False
        ),
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        ),
    )
