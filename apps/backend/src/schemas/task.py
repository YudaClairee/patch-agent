import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints


class TaskCreate(BaseModel):
    repository_id: uuid.UUID
    instruction: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20000)]
    target_branch: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]
    parent_run_id: uuid.UUID | None = None
    follow_up_instruction: Annotated[str, StringConstraints(strip_whitespace=True, max_length=20000)] | None = None


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
