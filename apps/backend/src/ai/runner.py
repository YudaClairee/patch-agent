"""
Entrypoint for the P.A.T.C.H. agent Docker container.
Reads env vars, clones the repo, runs the agent loop, persists events and tool calls to Postgres,
publishes every event to Redis, and exits with code 0 on success or 1 on failure.
"""
import asyncio
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone

from sqlmodel import Session

from src.ai.agent import run_agent
from src.core.config import settings
from src.core.database import engine
from src.models.agent_run import AgentRun
from src.models.enums import RunStatus
from src.services.events import RunEmitter, publish_error, publish_status_change

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


def _clone_repo(repo_clone_url: str, github_token: str) -> None:
    if repo_clone_url.startswith("https://"):
        auth_url = repo_clone_url.replace("https://", f"https://{github_token}@", 1)
    else:
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

    # Live-only status frames use negative sequences so they don't collide
    # with the RunEmitter's per-event counter.
    live_seq = -1

    def _publish_status(new_status: str) -> None:
        nonlocal live_seq
        publish_status_change(agent_run_id_str, new_status, live_seq)
        live_seq -= 1

    def _publish_error_live(message: str) -> None:
        nonlocal live_seq
        publish_error(agent_run_id_str, message, live_seq)
        live_seq -= 1

    _set_run_status(agent_run_id, RunStatus.running, started_at=_now())
    _publish_status("running")

    emitter = RunEmitter(
        agent_run_id,
        max_steps=settings.agent_max_steps,
        duplicate_streak_limit=settings.agent_duplicate_streak_limit,
    )

    try:
        _publish_status("cloning_repo")
        _clone_repo(repo_clone_url, github_token)
        _configure_git_identity()

        branch_to_checkout = head_branch if head_branch else base_branch
        _checkout_branch(branch_to_checkout)

        _publish_status("executing")
        await run_agent(
            emitter=emitter,
            instruction=effective_instruction,
            workspace_path=WORKSPACE,
            repository_id=repository_id,
            branch=branch_to_checkout,
            agent_run_id=agent_run_id_str,
            follow_up_context=follow_up_context,
        )

        _set_run_status(
            agent_run_id,
            RunStatus.succeeded,
            finished_at=_now(),
            total_tool_calls=emitter.total_tool_calls,
        )
        _publish_status("succeeded")

    except subprocess.CalledProcessError as e:
        error_msg = f"Git command failed: {e.stderr or str(e)}"
        _set_run_status(agent_run_id, RunStatus.failed, finished_at=_now(), error_message=error_msg)
        _publish_error_live(error_msg)
        _publish_status("failed")
        sys.exit(1)

    except Exception as e:
        error_msg = str(e)
        _set_run_status(agent_run_id, RunStatus.failed, finished_at=_now(), error_message=error_msg)
        _publish_error_live(error_msg)
        _publish_status("failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
