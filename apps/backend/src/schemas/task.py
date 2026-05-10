import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TaskCreate(BaseModel):
    repository_id: uuid.UUID
    instruction: str = Field(..., min_length=1, max_length=20000, strip_whitespace=True)
    target_branch: str = Field(..., min_length=1, max_length=255, strip_whitespace=True)
    parent_run_id: uuid.UUID | None = None
    follow_up_instruction: str | None = Field(None, max_length=20000, strip_whitespace=True)


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
