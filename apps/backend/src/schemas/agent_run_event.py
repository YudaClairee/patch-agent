import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict
from src.models.enums import EventType


class AgentRunEventRead(BaseModel):
    id: uuid.UUID
    agent_run_id: uuid.UUID
    sequence: int
    event_type: EventType
    payload: dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
