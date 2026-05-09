import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, Enum as SAEnum, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, Relationship, SQLModel

from src.models.enums import RunStatus

if TYPE_CHECKING:
    from src.models.agent_run_event import AgentRunEvent
    from src.models.file_change import FileChange
    from src.models.pull_request import PullRequest
    from src.models.task import Task
    from src.models.tool_call import ToolCall
    from src.models.verification_check import VerificationCheck


class AgentRun(SQLModel, table=True):
    __tablename__ = "agent_runs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    task_id: uuid.UUID = Field(
        sa_column=Column(
            PG_UUID(as_uuid=True),
            ForeignKey("tasks.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    status: RunStatus = Field(
        sa_column=Column(SAEnum(RunStatus, name="run_status"), nullable=False)
    )

    container_id: str | None = Field(default=None, max_length=128)
    container_image: str | None = Field(default=None, max_length=512)
    branch_name: str | None = Field(default=None, max_length=255)
    celery_task_id: str | None = Field(default=None, max_length=128)

    model_id: str = Field(max_length=255)
    max_turns: int = Field(default=15, nullable=False)
    total_tool_calls: int | None = Field(default=None)
    total_tokens: int | None = Field(default=None)
    error_message: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )

    queued_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), nullable=False
        )
    )
    started_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    finished_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )

    task: "Task" = Relationship(back_populates="agent_runs")
    events: list["AgentRunEvent"] = Relationship(
        back_populates="agent_run",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    tool_calls: list["ToolCall"] = Relationship(
        back_populates="agent_run",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    file_changes: list["FileChange"] = Relationship(
        back_populates="agent_run",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    verification_checks: list["VerificationCheck"] = Relationship(
        back_populates="agent_run",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    pull_request: "PullRequest | None" = Relationship(
        back_populates="agent_run",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "uselist": False},
    )
