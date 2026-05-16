import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, field_serializer, model_validator
from src.models.enums import PRState, RunRole, RunStatus
from src.schemas.tool_call import ToolCallRead
from src.schemas.pull_request import PullRequestRead


def _resolve_instruction(run) -> str | None:
    """Pull the human-readable task description for a run. Follow-up runs override
    the parent task's instruction with their own follow_up_instruction."""
    follow_up = getattr(run, "follow_up_instruction", None)
    if follow_up:
        return follow_up
    task = getattr(run, "task", None)
    if task is not None:
        return getattr(task, "instruction", None)
    return None


class PullRequestSummaryRead(BaseModel):
    github_pr_number: int
    title: str
    url: str
    state: PRState

    model_config = ConfigDict(from_attributes=True)


class AgentRunListItemRead(BaseModel):
    id: uuid.UUID
    task_id: uuid.UUID
    instruction: str | None = None
    status: RunStatus
    run_role: RunRole = RunRole.developer
    branch_name: str | None
    queued_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    pull_request: PullRequestSummaryRead | None = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def _inject_instruction(cls, obj):
        if isinstance(obj, dict) or obj is None:
            return obj
        obj.__dict__["instruction"] = _resolve_instruction(obj)
        return obj


class AgentRunRead(BaseModel):
    id: uuid.UUID
    task_id: uuid.UUID
    instruction: str | None = None
    status: RunStatus
    run_role: RunRole = RunRole.developer
    parent_run_id: uuid.UUID | None
    reviewer_run_id: uuid.UUID | None = None
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
    
    tool_calls: list[ToolCallRead] = []
    pull_request: PullRequestRead | None = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def _inject_instruction(cls, obj):
        if isinstance(obj, dict) or obj is None:
            return obj
        obj.__dict__["instruction"] = _resolve_instruction(obj)
        return obj

    @field_serializer("cost_usd")
    def serialize_cost_usd(self, cost_usd: Decimal | None, _info) -> str | None:
        if cost_usd is None:
            return None
        return str(cost_usd)
