from enum import Enum


class RunStatus(str, Enum):
    queued = "queued"
    preparing_workspace = "preparing_workspace"
    cloning_repo = "cloning_repo"
    indexing = "indexing"
    planning = "planning"
    executing = "executing"
    verifying = "verifying"
    review_required = "review_required"
    pr_created = "pr_created"
    failed = "failed"
    cancelled = "cancelled"


class EventType(str, Enum):
    status_change = "status_change"
    plan = "plan"
    message = "message"
    tool_call = "tool_call"
    tool_result = "tool_result"
    verification = "verification"
    error = "error"
    summary = "summary"


class ToolCallStatus(str, Enum):
    pending = "pending"
    success = "success"
    error = "error"


class ChangeType(str, Enum):
    added = "added"
    modified = "modified"
    deleted = "deleted"
    renamed = "renamed"


class CheckType(str, Enum):
    test = "test"
    lint = "lint"
    typecheck = "typecheck"
    custom = "custom"


class CheckStatus(str, Enum):
    passed = "passed"
    failed = "failed"
    error = "error"
    skipped = "skipped"


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
