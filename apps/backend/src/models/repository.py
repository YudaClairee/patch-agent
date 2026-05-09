import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.models.codebase_index import CodebaseIndex
    from src.models.pull_request import PullRequest
    from src.models.task import Task
    from src.models.user import User


class Repository(SQLModel, table=True):
    __tablename__ = "repositories"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "github_owner", "github_repo", name="uq_repo_user_owner_name"
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        sa_column=Column(
            PG_UUID(as_uuid=True),
            ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    github_owner: str = Field(max_length=255)
    github_repo: str = Field(max_length=255)
    github_repo_id: int | None = Field(default=None)
    default_branch: str = Field(max_length=255)
    language: str | None = Field(default=None, max_length=64)
    clone_url: str = Field(max_length=2048)

    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), nullable=False
        )
    )
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        )
    )

    user: "User" = Relationship(back_populates="repositories")
    codebase_indexes: list["CodebaseIndex"] = Relationship(
        back_populates="repository",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    tasks: list["Task"] = Relationship(back_populates="repository")
    pull_requests: list["PullRequest"] = Relationship(back_populates="repository")
