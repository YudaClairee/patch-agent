"""
Integration test: calls runner.main() directly in-process against a real repo.
Reads GITHUB_TOKEN and OPENROUTER_API_KEY from your .env via settings.

Usage:
  REPO_CLONE_URL=https://github.com/YOUR_ORG/YOUR_REPO.git \
  DATABASE_URL=postgresql://postgres:postgres@localhost:5432/postgres \
  REDIS_URL=redis://localhost:6379/0 \
  uv run python scripts/test_integration.py
"""
import asyncio
import os
import sys
import uuid

from cryptography.fernet import Fernet
from sqlmodel import Session, select

sys.path.insert(0, ".")

from src.core.config import settings
from src.core.database import engine
from src.models.agent_run import AgentRun
from src.models.agent_run_event import AgentRunEvent
from src.models.github_credential import GithubCredential
from src.models.pull_request import PullRequest
from src.models.repository import Repository
from src.models.task import Task
from src.models.tool_call import ToolCall
from src.models.user import User
from src.models.enums import RunStatus


REPO_CLONE_URL = os.environ.get("REPO_CLONE_URL", "").strip()
INSTRUCTION = os.environ.get(
    "INSTRUCTION",
    "Search for Python files in the repo, then write a file called PATCH_ANALYSIS.md "
    "with a brief summary of what the repo does. Run any available tests and lint checks. "
    "Then submit a pull request."
)


def _require(name: str, value: str) -> str:
    if not value:
        print(f"ERROR: {name} is not set. Set it in .env or as an env var.")
        sys.exit(1)
    return value


def setup_test_data() -> tuple[uuid.UUID, str]:
    """Insert a minimal User + Repo + Task + AgentRun into the DB. Returns (run_id, repo_id)."""
    github_token = os.environ.get("GITHUB_TOKEN", "")
    _require("GITHUB_TOKEN", github_token)
    _require("REPO_CLONE_URL", REPO_CLONE_URL)
    _require("OPENROUTER_API_KEY", settings.openrouter_api_key)
    _require("FERNET_KEY", settings.fernet_key)

    fernet = Fernet(settings.fernet_key.encode())
    encrypted = fernet.encrypt(github_token.encode())

    parts = REPO_CLONE_URL.rstrip("/").removesuffix(".git").split("/")
    github_owner = parts[-2]
    github_repo = parts[-1]

    with Session(engine) as session:
        user = User(email=f"test-{uuid.uuid4()}@patch.ai", name="Integration Test")
        session.add(user)
        session.flush()

        cred = GithubCredential(
            user_id=user.id,
            github_username=github_owner,
            encrypted_token=encrypted,
        )
        session.add(cred)

        repo = Repository(
            user_id=user.id,
            github_owner=github_owner,
            github_repo=github_repo,
            default_branch="main",
            clone_url=REPO_CLONE_URL,
        )
        session.add(repo)
        session.flush()

        task = Task(
            user_id=user.id,
            repository_id=repo.id,
            title="Integration test task",
            instruction=INSTRUCTION,
            target_branch="main",
        )
        session.add(task)
        session.flush()

        run = AgentRun(
            task_id=task.id,
            status=RunStatus.queued,
            model_id="openrouter/google/gemini-2.0-flash-001",
        )
        session.add(run)
        session.commit()

        return run.id, str(repo.id)


def inject_env(run_id: uuid.UUID, repo_id: str) -> None:
    """Set env vars that runner.main() reads."""
    github_token = os.environ.get("GITHUB_TOKEN", "")
    os.environ.update({
        "AGENT_RUN_ID":        str(run_id),
        "INSTRUCTION":         INSTRUCTION,
        "REPO_CLONE_URL":      REPO_CLONE_URL,
        "BASE_BRANCH":         "main",
        "GITHUB_TOKEN":        github_token,
        "REPOSITORY_ID":       repo_id,
        "DATABASE_URL":        settings.database_url,
        "REDIS_URL":           settings.redis_url,
        "OPENROUTER_API_KEY":  settings.openrouter_api_key,
        "OPENROUTER_BASE_URL": settings.openrouter_base_url,
        "LANGFUSE_PUBLIC_KEY": settings.langfuse_public_key,
        "LANGFUSE_SECRET_KEY": settings.langfuse_secret_key,
        "LANGFUSE_HOST":       settings.langfuse_host,
        "FERNET_KEY":          settings.fernet_key,
    })


def print_results(run_id: uuid.UUID) -> None:
    with Session(engine) as session:
        run = session.get(AgentRun, run_id)
        events = session.exec(
            select(AgentRunEvent)
            .where(AgentRunEvent.agent_run_id == run_id)
            .order_by(AgentRunEvent.sequence)
        ).all()
        tool_calls = session.exec(
            select(ToolCall)
            .where(ToolCall.agent_run_id == run_id)
            .order_by(ToolCall.sequence)
        ).all()
        pr = session.exec(
            select(PullRequest).where(PullRequest.agent_run_id == run_id)
        ).first()

    print("\n" + "=" * 60)
    print(f"AGENT RUN:  {run_id}")
    print(f"Status:     {run.status}")
    print(f"Branch:     {run.branch_name}")
    print(f"Error:      {run.error_message}")
    print(f"Started:    {run.started_at}")
    print(f"Finished:   {run.finished_at}")
    print(f"Tool calls: {run.total_tool_calls}")
    print("=" * 60)

    print(f"\nEVENTS ({len(events)}):")
    for e in events:
        print(f"  [{e.sequence:02d}] {e.event_type.value:15s} {str(e.payload)[:80]}")

    print(f"\nTOOL CALLS ({len(tool_calls)}):")
    for tc in tool_calls:
        print(f"  [{tc.sequence:02d}] {tc.tool_name:35s} status={tc.status.value}")

    if pr:
        print(f"\nPULL REQUEST: #{pr.github_pr_number}")
        print(f"  URL:   {pr.url}")
        print(f"  State: {pr.state.value}")
    else:
        print("\nNo pull request created.")
    print("=" * 60)


async def run() -> None:
    run_id, repo_id = setup_test_data()
    inject_env(run_id, repo_id)

    print(f"\nStarting integration test for AgentRun {run_id}")
    print(f"Repo:  {REPO_CLONE_URL}")
    print(f"Task:  {INSTRUCTION[:80]}...\n")

    # Import runner here so env vars are already set before any module-level code runs
    from src.ai import runner
    await runner.main()


if __name__ == "__main__":
    asyncio.run(run())
    # Re-read run_id from env (set during setup)
    run_id = uuid.UUID(os.environ["AGENT_RUN_ID"])
    print_results(run_id)
