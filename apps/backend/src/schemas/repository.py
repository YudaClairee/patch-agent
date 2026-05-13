import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class RepositoryRead(BaseModel):
    id: uuid.UUID
    github_owner: str
    github_repo: str
    default_branch: str
    language: str | None
    clone_url: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
