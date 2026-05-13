"""
Host-side Celery task that spawns and monitors the agent Docker container.
The container runs src.ai.runner, which handles all agent logic and DB persistence.
This task is responsible for: container lifecycle, env injection, and failure finalization.
"""
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass

import docker
from celery import Celery
from sqlmodel import Session, select

from src.core.config import settings
from src.core.database import engine
from src.models.agent_run import AgentRun
from src.models.github_credential import GithubCredential
from src.models.enums import RunStatus
from src.services.credentials import decrypt_token
from src.services.sandboxing import get_sandbox_options

celery_app = Celery(
    "patch",
    broker=settings.redis_url,
    backend=settings.redis_url,
)
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]
celery_app.conf.timezone = "UTC"


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class _RunContext:
    agent_run_id: str
    instruction: str
    clone_url: str
    base_branch: str
    repository_id: str
    github_token: str
    parent_run_id: str | None
    head_branch: str | None
    follow_up_instruction: str | None


def _load_run_context(agent_run_id: uuid.UUID) -> _RunContext:
    """Load everything the container needs from the DB, returning only primitives."""
    with Session(engine) as session:
        run = session.get(AgentRun, agent_run_id)
        if run is None:
            raise ValueError(f"AgentRun {agent_run_id} not found")

        task = run.task
        repo = task.repository

        credential = session.exec(
            select(GithubCredential).where(
                GithubCredential.user_id == task.user_id,
                GithubCredential.revoked_at.is_(None),  # type: ignore[attr-defined]
            )
        ).first()

        if credential is None:
            raise ValueError(f"No valid GitHub credential found for user {task.user_id}")

        github_token = decrypt_token(credential)

        # For follow-up runs, resolve the parent's working branch
        head_branch: str | None = None
        if run.parent_run_id:
            parent = session.get(AgentRun, run.parent_run_id)
            if parent and parent.branch_name:
                head_branch = parent.branch_name

        return _RunContext(
            agent_run_id=str(run.id),
            instruction=task.instruction,
            clone_url=repo.clone_url,
            base_branch=task.target_branch,
            repository_id=str(repo.id),
            github_token=github_token,
            parent_run_id=str(run.parent_run_id) if run.parent_run_id else None,
            head_branch=head_branch,
            follow_up_instruction=run.follow_up_instruction,
        )


def _build_env(ctx: _RunContext) -> dict[str, str]:
    env = {
        "AGENT_RUN_ID": ctx.agent_run_id,
        "INSTRUCTION": ctx.instruction,
        "REPO_CLONE_URL": ctx.clone_url,
        "BASE_BRANCH": ctx.base_branch,
        "GITHUB_TOKEN": ctx.github_token,
        "REPOSITORY_ID": ctx.repository_id,
        "DATABASE_URL": settings.database_url,
        "REDIS_URL": settings.redis_url,
        "OPENROUTER_API_KEY": settings.openrouter_api_key,
        "OPENROUTER_BASE_URL": settings.openrouter_base_url,
        "LANGFUSE_PUBLIC_KEY": settings.langfuse_public_key,
        "LANGFUSE_SECRET_KEY": settings.langfuse_secret_key,
        "LANGFUSE_HOST": settings.langfuse_host,
        "FERNET_KEY": settings.fernet_key,
    }
    if ctx.head_branch:
        env["HEAD_BRANCH"] = ctx.head_branch
    if ctx.parent_run_id:
        env["PARENT_RUN_ID"] = ctx.parent_run_id
    if ctx.follow_up_instruction:
        env["FOLLOW_UP_INSTRUCTION"] = ctx.follow_up_instruction
    return env


@celery_app.task(bind=True, name="dispatch_agent_run")
def dispatch_agent_run(self, agent_run_id: str) -> None:
    run_uuid = uuid.UUID(agent_run_id)
    network_name = f"patch_{agent_run_id}"
    client = docker.from_env()
    container = None
    network = None

    try:
        ctx = _load_run_context(run_uuid)
        env = _build_env(ctx)
        sandbox_opts = get_sandbox_options(agent_run_id)

        # Create an isolated bridge network for this run
        network = client.networks.create(network_name, driver="bridge")

        # 'network' key in sandbox_opts refers to the network name;
        # docker-py uses the 'network' kwarg on containers.run directly
        container = client.containers.run(
            image=settings.docker_agent_image,
            environment=env,
            **sandbox_opts,
        )

        # Record container metadata
        with Session(engine) as session:
            run_row = session.get(AgentRun, run_uuid)
            if run_row:
                run_row.container_id = container.id[:128]
                run_row.container_image = settings.docker_agent_image
                run_row.celery_task_id = self.request.id
                session.add(run_row)
                session.commit()

        # Block until the container exits
        wait_timeout = settings.agent_max_wall_time_sec + 120
        result = container.wait(timeout=wait_timeout)
        exit_code = result.get("StatusCode", -1)

        # If the container exited non-zero and the runner didn't already set a terminal status,
        # finalize the failure here so the row is never left in `running`.
        if exit_code != 0:
            with Session(engine) as session:
                run_row = session.get(AgentRun, run_uuid)
                if run_row and run_row.status == RunStatus.running:
                    run_row.status = RunStatus.failed
                    run_row.finished_at = _now()
                    run_row.error_message = f"Container exited with code {exit_code}"
                    session.add(run_row)
                    session.commit()

    except Exception as e:
        # Finalize any run that's still in a non-terminal state due to host-side errors
        try:
            with Session(engine) as session:
                run_row = session.get(AgentRun, run_uuid)
                if run_row and run_row.status in (RunStatus.queued, RunStatus.running):
                    run_row.status = RunStatus.failed
                    run_row.finished_at = _now()
                    run_row.error_message = f"Host dispatch error: {str(e)}"
                    session.add(run_row)
                    session.commit()
        except Exception:
            pass
        raise

    finally:
        if container is not None:
            try:
                container.remove(force=True)
            except Exception:
                pass
        if network is not None:
            try:
                client.networks.remove(network_name)
            except Exception:
                pass
