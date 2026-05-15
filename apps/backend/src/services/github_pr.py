"""
Lazy GitHub PR state refresher.

Called from GET /agent_runs/{id}/pull_request so the UI sees `merged` / `closed`
without needing a webhook listener. Throttled: if the row was synced <30s ago,
the call is a no-op.
"""
import logging
from datetime import datetime, timezone, timedelta

import httpx
from sqlmodel import Session

from src.models.enums import PRState
from src.models.pull_request import PullRequest
from src.models.repository import Repository

logger = logging.getLogger(__name__)

_SYNC_INTERVAL = timedelta(seconds=30)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def maybe_refresh_pr(
    pr: PullRequest,
    repository: Repository,
    github_token: str,
    session: Session,
) -> PullRequest:
    """Refresh the PR row from GitHub if it's open and stale. Returns the (possibly updated) row."""
    if pr.state == PRState.merged:
        return pr  # terminal
    if pr.last_synced_at and (_now() - pr.last_synced_at) < _SYNC_INTERVAL:
        return pr

    url = (
        f"https://api.github.com/repos/{repository.github_owner}/"
        f"{repository.github_repo}/pulls/{pr.github_pr_number}"
    )
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        logger.warning("PR refresh failed for #%s: %s", pr.github_pr_number, exc)
        pr.last_synced_at = _now()
        session.add(pr)
        session.commit()
        session.refresh(pr)
        return pr

    if data.get("merged"):
        pr.state = PRState.merged
        merged_at_str = data.get("merged_at")
        if merged_at_str:
            pr.merged_at = datetime.fromisoformat(merged_at_str.replace("Z", "+00:00"))
    elif data.get("state") == "closed":
        pr.state = PRState.closed
    elif data.get("draft"):
        pr.state = PRState.draft
    else:
        pr.state = PRState.open

    pr.last_synced_at = _now()
    session.add(pr)
    session.commit()
    session.refresh(pr)
    return pr
