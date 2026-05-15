import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Column, DateTime, Enum as SAEnum, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, Relationship, SQLModel

from src.models.enums import PRState

if TYPE_CHECKING:
    from src.models.agent_run import AgentRun
    from src.models.repository import Repository


class PullRequest(SQLModel, table=True):
    __tablename__ = "pull_requests"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    agent_run_id: uuid.UUID = Field(
        sa_column=Column(
            PG_UUID(as_uuid=True),
            ForeignKey("agent_runs.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        )
    )
    repository_id: uuid.UUID = Field(
        sa_column=Column(
            PG_UUID(as_uuid=True),
            ForeignKey("repositories.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    github_pr_number: int = Field(nullable=False)
    # GitHub's global PR id has long exceeded 2^31; must be BIGINT.
    github_pr_id: int | None = Field(
        default=None, sa_column=Column(BigInteger, nullable=True)
    )
    title: str = Field(max_length=512)
    body: str = Field(
        default="", sa_column=Column(Text, nullable=False, server_default="")
    )
    head_branch: str = Field(max_length=255)
    base_branch: str = Field(max_length=255)
    url: str = Field(max_length=2048)
    state: PRState = Field(
        sa_column=Column(SAEnum(PRState, name="pr_state"), nullable=False)
    )
    merged_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    last_synced_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )

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

    agent_run: "AgentRun" = Relationship(back_populates="pull_request")
    repository: "Repository" = Relationship(back_populates="pull_requests")
