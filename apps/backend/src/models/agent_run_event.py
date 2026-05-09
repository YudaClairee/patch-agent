import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Column, DateTime, Enum as SAEnum, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlmodel import Field, Relationship, SQLModel

from src.models.enums import EventType

if TYPE_CHECKING:
    from src.models.agent_run import AgentRun


class AgentRunEvent(SQLModel, table=True):
    __tablename__ = "agent_run_events"
    __table_args__ = (
        Index("ix_agent_run_events_run_seq", "agent_run_id", "sequence", unique=True),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    agent_run_id: uuid.UUID = Field(
        sa_column=Column(
            PG_UUID(as_uuid=True),
            ForeignKey("agent_runs.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    sequence: int = Field(nullable=False)
    event_type: EventType = Field(
        sa_column=Column(SAEnum(EventType, name="event_type"), nullable=False)
    )
    payload: dict[str, Any] = Field(
        default_factory=dict, sa_column=Column(JSONB, nullable=False)
    )
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), nullable=False
        )
    )

    agent_run: "AgentRun" = Relationship(back_populates="events")
