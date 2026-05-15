import logging
import uuid
from datetime import datetime, timezone

import docker
import httpx
from celery.exceptions import CeleryError
from docker.errors import DockerException, NotFound
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from src.celery_app import celery_app
from src.core.auth import current_user
from src.core.database import get_session
from src.models.enums import RunStatus
from src.models.user import User
from src.repositories import agent_runs as agent_runs_repo
from src.schemas.agent_run import AgentRunListItemRead, AgentRunRead
from src.schemas.agent_run_event import AgentRunEventRead
from src.schemas.diff import DiffFileRead
from src.schemas.pull_request import PullRequestRead
from src.services.credentials import get_active_token
from src.services.events import publish_status_change
from src.services.github_pr import maybe_refresh_pr

TERMINAL_STATUSES = {RunStatus.succeeded, RunStatus.failed, RunStatus.cancelled}

logger = logging.getLogger(__name__)

agent_runs_router = APIRouter(prefix="/agent_runs", tags=["Agent Runs"])


@agent_runs_router.get("/", response_model=list[AgentRunListItemRead])
def list_agent_runs(
    limit: int = Query(50, ge=1, le=100),
    repository_id: uuid.UUID | None = Query(None),
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
):
    runs = agent_runs_repo.list_agent_runs_for_user(
        session, user.id, limit, repository_id=repository_id
    )
    return [AgentRunListItemRead.model_validate(r) for r in runs]


@agent_runs_router.get("/{id}", response_model=AgentRunRead)
def get_agent_run(
    id: uuid.UUID,
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
):
    run = agent_runs_repo.get_agent_run_detail_for_user(session, id, user.id)
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")
    return AgentRunRead.model_validate(run)


@agent_runs_router.get("/{id}/events", response_model=list[AgentRunEventRead])
def list_agent_run_events(
    id: uuid.UUID,
    limit: int = Query(50, ge=1, le=100),
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
):
    run = agent_runs_repo.get_agent_run_for_user(session, id, user.id)
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")
    events = agent_runs_repo.list_events_for_user(session, id, user.id, limit)
    return [AgentRunEventRead.model_validate(e) for e in events]


@agent_runs_router.get("/{id}/pull_request", response_model=PullRequestRead)
def get_pull_request(
    id: uuid.UUID,
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
):
    pr = agent_runs_repo.get_pull_request_for_run_for_user(session, id, user.id)
    if not pr:
        raise HTTPException(status_code=404, detail="Pull request not found")

    repository = agent_runs_repo.get_repository_for_pull_request_for_user(session, pr, user.id)
    if repository is not None:
        try:
            pat = get_active_token(session, user.id)
            pr = maybe_refresh_pr(pr, repository, pat, session)
        except Exception as exc:
            logger.warning("PR lazy-refresh skipped: %s", exc)

    return PullRequestRead.model_validate(pr)


@agent_runs_router.get("/{id}/diff", response_model=list[DiffFileRead])
def get_agent_run_diff(
    id: uuid.UUID,
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
):
    pr = agent_runs_repo.get_pull_request_for_run_for_user(session, id, user.id)
    if not pr:
        raise HTTPException(status_code=404, detail="Pull request not found")

    repository = agent_runs_repo.get_repository_for_pull_request_for_user(session, pr, user.id)
    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")

    pat = get_active_token(session, user.id)

    url = f"https://api.github.com/repos/{repository.github_owner}/{repository.github_repo}/pulls/{pr.github_pr_number}/files"
    headers = {
        "Authorization": f"token {pat}",
        "Accept": "application/vnd.github.v3+json",
    }

    try:
        response = httpx.get(url, headers=headers, timeout=10.0)
        if response.status_code == 401:
            raise HTTPException(status_code=401, detail="Invalid GitHub credential")
        if response.status_code == 403:
            raise HTTPException(status_code=403, detail="GitHub API forbidden")
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="GitHub PR not found")
        response.raise_for_status()
        files = response.json()

        return [
            DiffFileRead(
                file_path=f["filename"],
                status=f["status"],
                additions=f["additions"],
                deletions=f["deletions"],
                patch=f.get("patch"),
            )
            for f in files
        ]
    except httpx.HTTPError as e:
        logger.error(f"GitHub API error: {e}")
        raise HTTPException(status_code=502, detail="GitHub API error")


@agent_runs_router.post("/{id}/cancel", response_model=AgentRunRead, status_code=202)
def cancel_agent_run(
    id: uuid.UUID,
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
):
    run = agent_runs_repo.get_agent_run_for_user(session, id, user.id)
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")
    if run.status in TERMINAL_STATUSES:
        raise HTTPException(status_code=409, detail=f"Agent run already {run.status.value}")

    if run.celery_task_id:
        try:
            celery_app.control.revoke(run.celery_task_id, terminate=True, signal="SIGTERM")
        except CeleryError as exc:
            logger.warning("Celery revoke failed for %s: %s", run.celery_task_id, exc)

    if run.container_id:
        try:
            client = docker.from_env()
            container = client.containers.get(run.container_id)
            container.stop(timeout=5)
        except NotFound:
            pass  # container already gone — common when the run is finishing on its own
        except DockerException as exc:
            logger.warning("Docker stop failed for %s: %s", run.container_id, exc)

    run.status = RunStatus.cancelled
    run.finished_at = datetime.now(timezone.utc)
    session.add(run)
    session.commit()
    session.refresh(run)

    # Notify any open WebSocket so it closes via the terminal-status-change branch in ws.py.
    publish_status_change(str(run.id), RunStatus.cancelled.value, sequence=-(2**31))

    return AgentRunRead.model_validate(run)
