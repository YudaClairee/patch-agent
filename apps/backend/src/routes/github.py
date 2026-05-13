"""GitHub-facing endpoints: list the authenticated user's repositories."""
from __future__ import annotations

import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session

from src.core.auth import current_user
from src.core.database import get_session
from src.models.user import User
from src.services.credentials import get_active_token

logger = logging.getLogger(__name__)

github_router = APIRouter(prefix="/github", tags=["GitHub"])


class GithubRepoSummary(BaseModel):
    full_name: str
    owner: str
    name: str
    default_branch: str
    private: bool
    language: str | None
    description: str | None
    html_url: str
    updated_at: str | None


@github_router.get("/repositories", response_model=list[GithubRepoSummary])
async def list_github_repositories(
    per_page: int = Query(50, ge=1, le=100),
    page: int = Query(1, ge=1, le=10),
    session: Session = Depends(get_session),
    user: User = Depends(current_user),
) -> list[GithubRepoSummary]:
    token = get_active_token(session, user.id)
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            "https://api.github.com/user/repos",
            params={
                "per_page": per_page,
                "page": page,
                "sort": "updated",
                "affiliation": "owner,collaborator,organization_member",
            },
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
        )
    if resp.status_code == 401:
        raise HTTPException(status_code=401, detail="GitHub token rejected; reconnect GitHub")
    if resp.status_code != 200:
        logger.warning("GitHub /user/repos returned %s: %s", resp.status_code, resp.text[:200])
        raise HTTPException(status_code=502, detail="GitHub API error")

    items = resp.json()
    out: list[GithubRepoSummary] = []
    for item in items:
        owner = (item.get("owner") or {}).get("login") or ""
        name = item.get("name") or ""
        out.append(
            GithubRepoSummary(
                full_name=item.get("full_name") or f"{owner}/{name}",
                owner=owner,
                name=name,
                default_branch=item.get("default_branch") or "main",
                private=bool(item.get("private")),
                language=item.get("language"),
                description=item.get("description"),
                html_url=item.get("html_url") or "",
                updated_at=item.get("updated_at"),
            )
        )
    return out
