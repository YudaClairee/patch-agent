import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Column, DateTime, Enum as SAEnum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlmodel import Field, Relationship, SQLModel

from src.models.enums import ToolCallStatus

if TYPE_CHECKING:
    from src.models.agent_run import AgentRun


class ToolCall(SQLModel, table=True):
    __tablename__ = "tool_calls"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    agent_run_id: uuid.UUID = Field(
        sa_column=Column(
            PG_UUID(as_uuid=True),
            ForeignKey("agent_runs.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    sequence: int = Field(nullable=False)
    tool_name: str = Field(max_length=128)
    tool_input: dict[str, Any] = Field(
        default_factory=dict, sa_column=Column(JSONB, nullable=False)
    )
    tool_output: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSONB, nullable=True)
    )
    status: ToolCallStatus = Field(
        sa_column=Column(
            SAEnum(ToolCallStatus, name="tool_call_status"), nullable=False
        )
    )
    error_message: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )
    duration_ms: int | None = Field(default=None)

    started_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    finished_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )

    agent_run: "AgentRun" = Relationship(back_populates="tool_calls")
