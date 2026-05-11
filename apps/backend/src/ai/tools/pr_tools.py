import os
import uuid
from urllib.parse import urlparse

from cryptography.fernet import Fernet
from github import Github, GithubException
from sqlmodel import Session, select

from src.core.config import settings
from src.core.database import engine
from src.models.agent_run import AgentRun
from src.models.github_credential import GithubCredential
from src.models.pull_request import PullRequest
from src.models.tool_call import ToolCall
from src.models.enums import PRState, ToolCallStatus
from src.ai.tools.git_tools import create_branch, commit_changes, push_branch, get_git_diff

WORKSPACE = "/workspace"


def decrypt_token(credential: GithubCredential) -> str:
    """Decrypt a Fernet-encrypted GitHub PAT from the database."""
    f = Fernet(settings.fernet_key.encode())
    return f.decrypt(credential.encrypted_token).decode()


def _parse_github_owner_repo(clone_url: str) -> tuple[str, str]:
    """Parse owner and repo name from a GitHub clone URL (HTTPS or SSH)."""
    if clone_url.startswith("https://"):
        path = urlparse(clone_url).path.lstrip("/").removesuffix(".git")
    else:
        # git@github.com:owner/repo.git
        path = clone_url.split(":")[-1].removesuffix(".git")
    owner, repo = path.split("/", 1)
    return owner, repo


def _check_preconditions(agent_run_id: str) -> None:
    """
    Raise RuntimeError if tests or lint have not passed, or if there is no diff.
    The agent must call run_test and run_lint (successfully) before submit_pull_request.
    """
    with Session(engine) as session:
        successful_calls = session.exec(
            select(ToolCall).where(
                ToolCall.agent_run_id == uuid.UUID(agent_run_id),
                ToolCall.status == ToolCallStatus.success,
            )
        ).all()

    passed_tools = {tc.tool_name for tc in successful_calls}

    if "workspace_run_test" not in passed_tools:
        raise RuntimeError(
            "Precondition failed: run_test must complete successfully before creating a PR. "
            "Run the test command first."
        )
    if "workspace_run_lint" not in passed_tools:
        raise RuntimeError(
            "Precondition failed: run_lint must complete successfully before creating a PR. "
            "Run the lint command first."
        )

    diff = get_git_diff(WORKSPACE)
    if not diff.get("stdout", "").strip():
        raise RuntimeError(
            "Precondition failed: no changes detected in the workspace. "
            "Make code changes before creating a PR."
        )


def submit_pull_request(title: str, body: str) -> dict:
    """
    Create or update a Pull Request for the current agent run.

    Initial run: creates a new branch, commits, pushes, and opens a PR.
    Follow-up run (PARENT_RUN_ID set): commits to the existing branch and adds a PR comment.

    Preconditions: run_test and run_lint must have passed, and the diff must be non-empty.
    """
    agent_run_id = os.environ["AGENT_RUN_ID"]
    github_token = os.environ["GITHUB_TOKEN"]
    repo_clone_url = os.environ["REPO_CLONE_URL"]
    base_branch = os.environ["BASE_BRANCH"]
    repository_id = os.environ["REPOSITORY_ID"]
    parent_run_id = os.environ.get("PARENT_RUN_ID")
    head_branch = os.environ.get("HEAD_BRANCH")

    _check_preconditions(agent_run_id)

    owner, repo_name = _parse_github_owner_repo(repo_clone_url)
    gh = Github(github_token)
    gh_repo = gh.get_repo(f"{owner}/{repo_name}")

    if parent_run_id:
        return _handle_follow_up(
            agent_run_id=agent_run_id,
            parent_run_id=parent_run_id,
            head_branch=head_branch or "",
            title=title,
            body=body,
            gh_repo=gh_repo,
        )
    else:
        return _handle_initial(
            agent_run_id=agent_run_id,
            repository_id=repository_id,
            base_branch=base_branch,
            title=title,
            body=body,
            gh_repo=gh_repo,
        )


def _handle_initial(
    agent_run_id: str,
    repository_id: str,
    base_branch: str,
    title: str,
    body: str,
    gh_repo,
) -> dict:
    branch_name = f"patch/task-{agent_run_id}"

    create_branch(WORKSPACE, branch_name)
    commit_changes(WORKSPACE, f"[P.A.T.C.H.] {title}")
    push_branch(WORKSPACE, branch_name)

    try:
        pr = gh_repo.create_pull(
            title=f"[P.A.T.C.H.] {title}",
            body=body,
            head=branch_name,
            base=base_branch,
        )
    except GithubException as e:
        raise RuntimeError(f"Failed to create pull request: {e.data}") from e

    with Session(engine) as session:
        run = session.get(AgentRun, uuid.UUID(agent_run_id))
        run.branch_name = branch_name
        session.add(run)

        pr_row = PullRequest(
            agent_run_id=uuid.UUID(agent_run_id),
            repository_id=uuid.UUID(repository_id),
            github_pr_number=pr.number,
            github_pr_id=pr.id,
            title=f"[P.A.T.C.H.] {title}",
            body=body,
            head_branch=branch_name,
            base_branch=base_branch,
            url=pr.html_url,
            state=PRState.open,
        )
        session.add(pr_row)
        session.commit()

    return {
        "status": "pr_created",
        "pr_number": pr.number,
        "pr_url": pr.html_url,
        "branch": branch_name,
    }


def _handle_follow_up(
    agent_run_id: str,
    parent_run_id: str,
    head_branch: str,
    title: str,
    body: str,
    gh_repo,
) -> dict:
    commit_changes(WORKSPACE, f"[P.A.T.C.H. follow-up] {title}")
    push_branch(WORKSPACE, head_branch)

    with Session(engine) as session:
        existing_pr = session.exec(
            select(PullRequest).where(
                PullRequest.agent_run_id == uuid.UUID(parent_run_id)
            )
        ).first()

    if existing_pr:
        try:
            gh_pr = gh_repo.get_pull(existing_pr.github_pr_number)
            gh_pr.create_issue_comment(
                f"**P.A.T.C.H. follow-up committed**\n\n{body}"
            )
            pr_url = existing_pr.url
            pr_number = existing_pr.github_pr_number
        except GithubException as e:
            raise RuntimeError(f"Failed to comment on pull request: {e.data}") from e
    else:
        pr_url = ""
        pr_number = 0

    return {
        "status": "follow_up_committed",
        "pr_number": pr_number,
        "pr_url": pr_url,
        "branch": head_branch,
    }
