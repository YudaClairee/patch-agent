import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, Enum as SAEnum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, Relationship, SQLModel

from src.models.enums import CheckStatus, CheckType

if TYPE_CHECKING:
    from src.models.agent_run import AgentRun


class VerificationCheck(SQLModel, table=True):
    __tablename__ = "verification_checks"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    agent_run_id: uuid.UUID = Field(
        sa_column=Column(
            PG_UUID(as_uuid=True),
            ForeignKey("agent_runs.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    check_type: CheckType = Field(
        sa_column=Column(SAEnum(CheckType, name="check_type"), nullable=False)
    )
    name: str = Field(max_length=128)
    command: str = Field(max_length=2048)
    status: CheckStatus = Field(
        sa_column=Column(SAEnum(CheckStatus, name="check_status"), nullable=False)
    )
    exit_code: int | None = Field(default=None)
    stdout: str = Field(
        default="", sa_column=Column(Text, nullable=False, server_default="")
    )
    stderr: str = Field(
        default="", sa_column=Column(Text, nullable=False, server_default="")
    )
    duration_ms: int | None = Field(default=None)

    started_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    finished_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )

    agent_run: "AgentRun" = Relationship(back_populates="verification_checks")
