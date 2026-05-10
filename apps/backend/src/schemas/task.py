import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class TaskCreate(BaseModel):
    repository_id: uuid.UUID
    instruction: str
    target_branch: str
    parent_run_id: uuid.UUID | None = None
    follow_up_instruction: str | None = None


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
