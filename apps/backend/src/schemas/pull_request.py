import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from src.models.enums import PRState


class PullRequestRead(BaseModel):
    id: uuid.UUID
    agent_run_id: uuid.UUID
    repository_id: uuid.UUID
    github_pr_number: int
    title: str
    body: str
    head_branch: str
    base_branch: str
    url: str
    state: PRState
    merged_at: datetime | None
    last_synced_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
