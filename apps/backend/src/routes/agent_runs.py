import logging
import uuid

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from src.core.auth import current_user
from src.core.database import get_session
from src.models.repository import Repository
from src.models.user import User
from src.repositories import agent_runs as agent_runs_repo
from src.schemas.agent_run import AgentRunRead
from src.schemas.agent_run_event import AgentRunEventRead
from src.schemas.diff import DiffFileRead
from src.schemas.pull_request import PullRequestRead
from src.services.credentials import decrypt_token

logger = logging.getLogger(__name__)

agent_runs_router = APIRouter(prefix="/agent_runs", tags=["Agent Runs"])


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

    # STUB: decrypt_token expects a credential, passing None for now
    try:
        pat = decrypt_token(None)
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))

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
