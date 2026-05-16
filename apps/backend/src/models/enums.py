from enum import Enum


class RunStatus(str, Enum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"


class RunRole(str, Enum):
    developer = "developer"
    reviewer = "reviewer"
    fixer = "fixer"


class EventType(str, Enum):
    status_change = "status_change"
    plan = "plan"
    message = "message"
    tool_call = "tool_call"
    tool_result = "tool_result"
    error = "error"
    summary = "summary"
    review_finding = "review_finding"


class ToolCallStatus(str, Enum):
    pending = "pending"
    success = "success"
    error = "error"


class PRState(str, Enum):
    open = "open"
    closed = "closed"
    merged = "merged"
    draft = "draft"
