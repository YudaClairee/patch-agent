import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict
from src.models.enums import ToolCallStatus


class ToolCallRead(BaseModel):
    id: uuid.UUID
    agent_run_id: uuid.UUID
    sequence: int
    tool_name: str
    tool_input: dict[str, Any]
    tool_output: dict[str, Any] | None
    status: ToolCallStatus
    error_message: str | None
    duration_ms: int | None
    started_at: datetime | None
    finished_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
