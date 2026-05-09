import datetime
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Column, Date, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.models.user import User


class UsageRecord(SQLModel, table=True):
    __tablename__ = "usage_records"
    __table_args__ = (UniqueConstraint("user_id", "date", name="uq_usage_user_date"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        sa_column=Column(
            PG_UUID(as_uuid=True),
            ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    date: datetime.date = Field(sa_column=Column(Date, nullable=False))
    run_count: int = Field(default=0, nullable=False)

    user: "User" = Relationship(back_populates="usage_records")
