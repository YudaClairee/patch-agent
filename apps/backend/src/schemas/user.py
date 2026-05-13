import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class UserRead(BaseModel):
    id: uuid.UUID
    email: str
    name: str | None
    daily_run_quota: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
