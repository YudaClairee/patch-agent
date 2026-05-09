import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Column, Enum as SAEnum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, Relationship, SQLModel

from src.models.enums import ChangeType

if TYPE_CHECKING:
    from src.models.agent_run import AgentRun


class FileChange(SQLModel, table=True):
    __tablename__ = "file_changes"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    agent_run_id: uuid.UUID = Field(
        sa_column=Column(
            PG_UUID(as_uuid=True),
            ForeignKey("agent_runs.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    file_path: str = Field(max_length=2048)
    change_type: ChangeType = Field(
        sa_column=Column(SAEnum(ChangeType, name="change_type"), nullable=False)
    )
    old_path: str | None = Field(default=None, max_length=2048)
    additions: int = Field(default=0, nullable=False)
    deletions: int = Field(default=0, nullable=False)
    patch: str = Field(sa_column=Column(Text, nullable=False))

    agent_run: "AgentRun" = Relationship(back_populates="file_changes")
