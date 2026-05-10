import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict
from src.models.enums import RunStatus
from src.schemas.tool_call import ToolCallRead
from src.schemas.pull_request import PullRequestRead


class AgentRunRead(BaseModel):
    id: uuid.UUID
    task_id: uuid.UUID
    status: RunStatus
    parent_run_id: uuid.UUID | None
    follow_up_instruction: str | None
    branch_name: str | None
    model_id: str
    prompt_version: str
    max_turns: int
    total_tool_calls: int | None
    total_tokens: int | None
    cost_usd: Decimal | None
    error_message: str | None
    queued_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    # nested — include when loading single run detail
    tool_calls: list[ToolCallRead] = []
    pull_request: PullRequestRead | None = None

    model_config = ConfigDict(from_attributes=True)
