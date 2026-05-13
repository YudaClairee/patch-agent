"""
Entrypoint for the P.A.T.C.H. agent Docker container.
Reads env vars, clones the repo, runs the agent loop, persists events and tool calls to Postgres,
publishes every event to Redis, and exits with code 0 on success or 1 on failure.
"""
import asyncio
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone

from sqlmodel import Session

from src.core.database import engine
from src.models.agent_run import AgentRun
from src.models.agent_run_event import AgentRunEvent
from src.models.tool_call import ToolCall
from src.models.enums import EventType, RunStatus, ToolCallStatus
from src.services.events import publish_event
from src.ai.agent import run_agent_stream, SYSTEM_PROMPT

WORKSPACE = "/workspace"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _set_run_status(agent_run_id: uuid.UUID, status: RunStatus, **kwargs) -> None:
    with Session(engine) as session:
        run = session.get(AgentRun, agent_run_id)
        if run is None:
            return
        run.status = status
        for key, value in kwargs.items():
            setattr(run, key, value)
        session.add(run)
        session.commit()


def _append_event(
    agent_run_id: uuid.UUID,
    event_type: EventType,
    payload: dict,
    sequence: int,
) -> None:
    with Session(engine) as session:
        event = AgentRunEvent(
            agent_run_id=agent_run_id,
            sequence=sequence,
            event_type=event_type,
            payload=payload,
        )
        session.add(event)
        session.commit()


def _upsert_tool_call(
    agent_run_id: uuid.UUID,
    sequence: int,
    tool_name: str,
    tool_input: dict,
    status: ToolCallStatus,
    tool_output: dict | None = None,
    error_message: str | None = None,
    duration_ms: int | None = None,
    started_at: datetime | None = None,
    finished_at: datetime | None = None,
) -> uuid.UUID:
    with Session(engine) as session:
        tc = ToolCall(
            agent_run_id=agent_run_id,
            sequence=sequence,
            tool_name=tool_name,
            tool_input=tool_input,
            status=status,
            tool_output=tool_output,
            error_message=error_message,
            duration_ms=duration_ms,
            started_at=started_at,
            finished_at=finished_at,
        )
        session.add(tc)
        session.commit()
        session.refresh(tc)
        return tc.id


def _clone_repo(repo_clone_url: str, github_token: str) -> None:
    """Clone the repository into /workspace using an authenticated HTTPS URL."""
    if repo_clone_url.startswith("https://"):
        auth_url = repo_clone_url.replace("https://", f"https://{github_token}@", 1)
    else:
        # SSH URL — convert to HTTPS with token
        # git@github.com:owner/repo.git -> https://token@github.com/owner/repo.git
        path = repo_clone_url.split(":")[-1]
        auth_url = f"https://{github_token}@github.com/{path}"

    subprocess.run(
        ["git", "clone", auth_url, WORKSPACE],
        check=True,
        timeout=300,
        capture_output=True,
        text=True,
    )


def _configure_git_identity() -> None:
    """Set git user identity for commits inside the container."""
    subprocess.run(
        ["git", "config", "user.email", "patch@patch.ai"],
        cwd=WORKSPACE, check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "P.A.T.C.H."],
        cwd=WORKSPACE, check=True, capture_output=True,
    )


def _checkout_branch(branch: str) -> None:
    subprocess.run(
        ["git", "checkout", branch],
        cwd=WORKSPACE, check=True, timeout=30, capture_output=True, text=True,
    )


def _parse_tool_call_args(raw: str | dict) -> dict:
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw)
    except Exception:
        return {"raw": str(raw)}


async def _run_agent(
    agent_run_id: uuid.UUID,
    instruction: str,
    repository_id: str,
    branch: str,
    follow_up_context: str | None,
) -> tuple[int, int]:
    """
    Stream agent events, persist to DB, publish to Redis.
    Returns (total_tool_calls, total_tokens).
    """
    sequence = 0
    total_tool_calls = 0
    # Maps tool_call sequence -> started_at for duration tracking
    pending_calls: dict[int, tuple[str, dict, datetime]] = {}

    async for raw_event in run_agent_stream(
        instruction=instruction,
        workspace_path=WORKSPACE,
        repository_id=repository_id,
        branch=branch,
        agent_run_id=str(agent_run_id),
        follow_up_context=follow_up_context,
    ):
        # raw_event is an SSE-formatted string: "data: {...}\n\n"
        if not raw_event.startswith("data:"):
            continue

        try:
            payload = json.loads(raw_event.removeprefix("data:").strip())
        except json.JSONDecodeError:
            continue

        event_type_str = payload.get("type", "")
        publish_event(str(agent_run_id), payload)

        if event_type_str == "text_delta":
            _append_event(agent_run_id, EventType.message, payload, sequence)
            sequence += 1

        elif event_type_str == "tool_call":
            tool_name = payload.get("tool_name", "")
            tool_input = _parse_tool_call_args(payload.get("tool_input", {}))
            started = _now()
            pending_calls[sequence] = (tool_name, tool_input, started)

            _append_event(agent_run_id, EventType.tool_call, payload, sequence)
            _upsert_tool_call(
                agent_run_id=agent_run_id,
                sequence=sequence,
                tool_name=tool_name,
                tool_input=tool_input,
                status=ToolCallStatus.success,  # optimistically success; tool errors bubble as agent errors
                started_at=started,
                finished_at=_now(),
            )
            total_tool_calls += 1
            sequence += 1

        elif event_type_str == "tool_result":
            tool_name = payload.get("tool_name", "")
            tool_output = payload.get("tool_output", {})
            tool_status_str = payload.get("status", "success")
            tool_status = ToolCallStatus.success if tool_status_str == "success" else ToolCallStatus.error

            _append_event(agent_run_id, EventType.tool_result, payload, sequence)
            _upsert_tool_call(
                agent_run_id=agent_run_id,
                sequence=sequence,
                tool_name=tool_name,
                tool_input={},
                status=tool_status,
                tool_output=tool_output if isinstance(tool_output, dict) else {"result": str(tool_output)},
                finished_at=_now(),
            )
            sequence += 1

        elif event_type_str == "error":
            _append_event(agent_run_id, EventType.error, payload, sequence)
            sequence += 1

        elif event_type_str == "done":
            _append_event(agent_run_id, EventType.summary, payload, sequence)
            sequence += 1

    return total_tool_calls, 0  # token counting from OpenRouter headers — future work


async def main() -> None:
    agent_run_id_str = os.environ["AGENT_RUN_ID"]
    instruction = os.environ["INSTRUCTION"]
    repo_clone_url = os.environ["REPO_CLONE_URL"]
    base_branch = os.environ["BASE_BRANCH"]
    github_token = os.environ["GITHUB_TOKEN"]
    repository_id = os.environ["REPOSITORY_ID"]
    head_branch = os.environ.get("HEAD_BRANCH")
    parent_run_id = os.environ.get("PARENT_RUN_ID")
    follow_up_instruction = os.environ.get("FOLLOW_UP_INSTRUCTION")

    agent_run_id = uuid.UUID(agent_run_id_str)

    # Build follow-up context prompt if this is a follow-up run
    follow_up_context: str | None = None
    if parent_run_id and follow_up_instruction:
        with Session(engine) as session:
            parent_run = session.get(AgentRun, uuid.UUID(parent_run_id))
            parent_summary = parent_run.error_message or "(no summary available)" if parent_run else "(parent run not found)"
        follow_up_context = (
            f"You are resuming work on an existing Pull Request.\n\n"
            f"Previous run summary:\n{parent_summary}\n\n"
            f"New follow-up instruction:\n{follow_up_instruction}"
        )
        effective_instruction = follow_up_instruction
    else:
        effective_instruction = instruction

    # Mark as running
    _set_run_status(agent_run_id, RunStatus.running, started_at=_now())
    publish_event(agent_run_id_str, {"type": "status_change", "status": "running"})

    try:
        # Clone and set up workspace
        publish_event(agent_run_id_str, {"type": "status_change", "status": "cloning_repo"})
        _clone_repo(repo_clone_url, github_token)
        _configure_git_identity()

        # Checkout branch
        branch_to_checkout = head_branch if head_branch else base_branch
        _checkout_branch(branch_to_checkout)

        # Run agent
        publish_event(agent_run_id_str, {"type": "status_change", "status": "executing"})
        total_tool_calls, total_tokens = await _run_agent(
            agent_run_id=agent_run_id,
            instruction=effective_instruction,
            repository_id=repository_id,
            branch=branch_to_checkout,
            follow_up_context=follow_up_context,
        )

        # Finalize success
        _set_run_status(
            agent_run_id,
            RunStatus.succeeded,
            finished_at=_now(),
            total_tool_calls=total_tool_calls,
            total_tokens=total_tokens if total_tokens else None,
        )
        publish_event(agent_run_id_str, {"type": "status_change", "status": "succeeded"})

    except subprocess.CalledProcessError as e:
        error_msg = f"Git command failed: {e.stderr or str(e)}"
        _set_run_status(agent_run_id, RunStatus.failed, finished_at=_now(), error_message=error_msg)
        publish_event(agent_run_id_str, {"type": "error", "error": error_msg})
        sys.exit(1)

    except Exception as e:
        error_msg = str(e)
        _set_run_status(agent_run_id, RunStatus.failed, finished_at=_now(), error_message=error_msg)
        publish_event(agent_run_id_str, {"type": "error", "error": error_msg})
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
