import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class TaskCreate(BaseModel):
    repository_id: uuid.UUID
    instruction: str
    target_branch: str
    parent_run_id: uuid.UUID | None = None
    follow_up_instruction: str | None = None

    @field_validator("instruction", mode="before")
    @classmethod
    def trim_instruction(cls, v: str) -> str:
        return v.strip()

    @field_validator("instruction")
    @classmethod
    def validate_instruction(cls, v: str) -> str:
        if not v:
            raise ValueError("instruction must not be empty")
        if len(v) > 20000:
            raise ValueError("instruction must be at most 20000 characters")
        return v

    @field_validator("target_branch", mode="before")
    @classmethod
    def trim_target_branch(cls, v: str) -> str:
        return v.strip()

    @field_validator("target_branch")
    @classmethod
    def validate_target_branch(cls, v: str) -> str:
        if not v:
            raise ValueError("target_branch must not be empty")
        if len(v) > 255:
            raise ValueError("target_branch must be at most 255 characters")
        return v

    @field_validator("follow_up_instruction", mode="before")
    @classmethod
    def trim_follow_up_instruction(cls, v: str | None) -> str | None:
        if v is not None:
            return v.strip()
        return v

    @field_validator("follow_up_instruction")
    @classmethod
    def validate_follow_up_instruction(cls, v: str | None) -> str | None:
        if v is not None and not v:
            raise ValueError("follow_up_instruction must not be whitespace-only")
        if v is not None and len(v) > 20000:
            raise ValueError("follow_up_instruction must be at most 20000 characters")
        return v


class TaskRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    repository_id: uuid.UUID
    title: str
    instruction: str
    target_branch: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
