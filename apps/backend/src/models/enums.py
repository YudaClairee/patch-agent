from enum import Enum


class RunStatus(str, Enum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"


class EventType(str, Enum):
    status_change = "status_change"
    plan = "plan"
    message = "message"
    tool_call = "tool_call"
    tool_result = "tool_result"
    error = "error"
    summary = "summary"


class ToolCallStatus(str, Enum):
    pending = "pending"
    success = "success"
    error = "error"


class IndexStatus(str, Enum):
    pending = "pending"
    indexing = "indexing"
    ready = "ready"
    failed = "failed"


class PRState(str, Enum):
    open = "open"
    closed = "closed"
    merged = "merged"
    draft = "draft"
