"""
Terminal sentinel tool: creates (or comments on, for follow-ups) the GitHub PR.

Inlines its own git ops via subprocess so it has no dependency on the deleted
workspace_* tool wrappers.
"""
import os
import subprocess
import tempfile
import uuid
from contextlib import contextmanager
from urllib.parse import urlparse

from github import Github, GithubException
from sqlmodel import Session, select

from src.core.database import engine
from src.models.agent_run import AgentRun
from src.models.pull_request import PullRequest
from src.models.enums import PRState

WORKSPACE = "/workspace"


def _git_base_env() -> dict[str, str]:
    return {
        "PATH": os.environ.get(
            "PATH",
            "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
        ),
        "HOME": "/tmp",
        "USER": os.environ.get("USER", "patch"),
        "LOGNAME": os.environ.get("LOGNAME", "patch"),
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        "LC_ALL": os.environ.get("LC_ALL", "C.UTF-8"),
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_PAGER": "cat",
        "PAGER": "cat",
    }


@contextmanager
def _git_auth_env(github_token: str | None = None):
    if not github_token:
        yield _git_base_env()
        return

    askpass = tempfile.NamedTemporaryFile("w", delete=False)
    askpass.write(
        "#!/bin/sh\n"
        "case \"$1\" in\n"
        "  *Username*) printf '%s\\n' x-access-token ;;\n"
        "  *) printf '%s\\n' \"$GITHUB_TOKEN\" ;;\n"
        "esac\n"
    )
    askpass.close()
    os.chmod(askpass.name, 0o700)

    env = _git_base_env()
    env["GIT_ASKPASS"] = askpass.name
    env["GITHUB_TOKEN"] = github_token
    try:
        yield env
    finally:
        try:
            os.unlink(askpass.name)
        except OSError:
            pass


def _run_git(
    args: list[str],
    check: bool = True,
    github_token: str | None = None,
) -> subprocess.CompletedProcess:
    with _git_auth_env(github_token) as env:
        return subprocess.run(
            ["git"] + args,
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            timeout=60,
            check=check,
            env=env,
        )


def _parse_github_owner_repo(clone_url: str) -> tuple[str, str]:
    if clone_url.startswith("https://"):
        path = urlparse(clone_url).path.lstrip("/").removesuffix(".git")
    else:
        path = clone_url.split(":")[-1].removesuffix(".git")
    owner, repo = path.split("/", 1)
    return owner, repo


def _check_has_changes() -> None:
    diff = _run_git(["diff", "--stat"], check=False)
    staged = _run_git(["diff", "--cached", "--stat"], check=False)
    log_ahead = _run_git(["log", "--oneline", "@{upstream}..HEAD"], check=False)
    if (
        not diff.stdout.strip()
        and not staged.stdout.strip()
        and not log_ahead.stdout.strip()
    ):
        raise RuntimeError(
            "No changes detected in the workspace. Make edits before submitting a PR."
        )


def submit_pull_request(title: str, body: str) -> dict:
    """
    Create or update a Pull Request for the current agent run.

    Initial run: creates a new branch, commits, pushes, opens a PR.
    Follow-up run (PARENT_RUN_ID set): commits to the parent's branch, comments on the PR.
    """
    agent_run_id = os.environ["AGENT_RUN_ID"]
    github_token = os.environ["GITHUB_TOKEN"]
    repo_clone_url = os.environ["REPO_CLONE_URL"]
    base_branch = os.environ["BASE_BRANCH"]
    repository_id = os.environ["REPOSITORY_ID"]
    parent_run_id = os.environ.get("PARENT_RUN_ID")
    head_branch = os.environ.get("HEAD_BRANCH")

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
            github_token=github_token,
        )
    return _handle_initial(
        agent_run_id=agent_run_id,
        repository_id=repository_id,
        base_branch=base_branch,
        title=title,
        body=body,
        gh_repo=gh_repo,
        github_token=github_token,
    )


def _stage_commit_push(branch: str, commit_message: str, github_token: str) -> None:
    _run_git(["checkout", "-B", branch])
    _run_git(["add", "-A"])
    commit = _run_git(["commit", "--no-verify", "-m", commit_message], check=False)
    if commit.returncode != 0 and "nothing to commit" not in (commit.stdout + commit.stderr).lower():
        raise RuntimeError(f"git commit failed: {commit.stderr or commit.stdout}")
    _run_git(["push", "--no-verify", "-u", "origin", branch], github_token=github_token)


def _find_existing_pr(gh_repo, branch_name: str):
    """Return the open PR for `branch_name` if one already exists, else None.
    Used to recover from a partial submit (branch+PR created on GitHub but
    DB row never written) — without this, the agent gets stuck because the
    workspace is now clean and `create_pull` would error with "already exists"."""
    owner = gh_repo.owner.login
    pulls = gh_repo.get_pulls(state="open", head=f"{owner}:{branch_name}")
    for pr in pulls:
        return pr
    return None


def _body_with_notification_mentions(body: str) -> tuple[str, list[str]]:
    """Return the PR/comment body plus any GitHub mentions to add.

    Notification wiring is intentionally a no-op until reviewer/mention settings
    exist; keeping the helper explicit avoids submit-time NameErrors.
    """
    return body, []


def _request_pr_reviewers(pr) -> dict:
    """Best-effort reviewer notification hook.

    The product does not currently persist reviewer handles, so this returns a
    stable result shape without making GitHub API calls.
    """
    _ = pr
    return {"requested_reviewers": [], "errors": []}


def _upsert_pr_row(
    agent_run_id: str,
    repository_id: str,
    branch_name: str,
    base_branch: str,
    title: str,
    body: str,
    pr,
) -> None:
    with Session(engine) as session:
        run = session.get(AgentRun, uuid.UUID(agent_run_id))
        if run is not None:
            run.branch_name = branch_name
            session.add(run)

        existing = session.exec(
            select(PullRequest).where(PullRequest.agent_run_id == uuid.UUID(agent_run_id))
        ).first()
        if existing is not None:
            existing.github_pr_number = pr.number
            existing.github_pr_id = pr.id
            existing.title = f"[P.A.T.C.H.] {title}"
            existing.body = body
            existing.head_branch = branch_name
            existing.base_branch = base_branch
            existing.url = pr.html_url
            existing.state = PRState.open
            session.add(existing)
        else:
            session.add(
                PullRequest(
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
            )
        session.commit()


def _handle_initial(
    agent_run_id: str,
    repository_id: str,
    base_branch: str,
    title: str,
    body: str,
    gh_repo,
    github_token: str,
) -> dict:
    branch_name = f"patch/task-{agent_run_id}"
    pr_body, mentions = _body_with_notification_mentions(body)

    # Recovery path: a previous attempt may have pushed the branch and opened
    # the PR but failed to persist the DB row. If so, just upsert and return —
    # don't error with "no changes detected".
    existing_pr = _find_existing_pr(gh_repo, branch_name)
    if existing_pr is not None:
        notification_result = _request_pr_reviewers(existing_pr)
        if mentions:
            try:
                existing_pr.edit(body=pr_body)
            except GithubException as exc:
                notification_result["errors"].append(
                    f"Failed to update PR body with mentions: {exc.data}"
                )
                pr_body = body
        _upsert_pr_row(
            agent_run_id, repository_id, branch_name, base_branch, title, pr_body, existing_pr
        )
        return {
            "status": "pr_recovered",
            "pr_number": existing_pr.number,
            "pr_url": existing_pr.html_url,
            "branch": branch_name,
            "notifications": notification_result,
        }

    _check_has_changes()
    _stage_commit_push(branch_name, f"[P.A.T.C.H.] {title}", github_token)

    try:
        pr = gh_repo.create_pull(
            title=f"[P.A.T.C.H.] {title}",
            body=pr_body,
            head=branch_name,
            base=base_branch,
        )
    except GithubException as e:
        raise RuntimeError(f"Failed to create pull request: {e.data}") from e

    notification_result = _request_pr_reviewers(pr)
    _upsert_pr_row(agent_run_id, repository_id, branch_name, base_branch, title, pr_body, pr)
    return {
        "status": "pr_created",
        "pr_number": pr.number,
        "pr_url": pr.html_url,
        "branch": branch_name,
        "notifications": notification_result,
    }


def _handle_follow_up(
    agent_run_id: str,
    parent_run_id: str,
    head_branch: str,
    title: str,
    body: str,
    gh_repo,
    github_token: str,
) -> dict:
    if not head_branch:
        raise RuntimeError("HEAD_BRANCH not set; cannot resolve parent's branch for follow-up.")

    _run_git(["checkout", head_branch], check=False)
    _run_git(["add", "-A"])
    commit = _run_git(
        ["commit", "--no-verify", "-m", f"[P.A.T.C.H. follow-up] {title}"],
        check=False,
    )
    if commit.returncode != 0 and "nothing to commit" not in (commit.stdout + commit.stderr).lower():
        raise RuntimeError(f"git commit failed: {commit.stderr or commit.stdout}")
    _run_git(["push", "--no-verify", "origin", head_branch], github_token=github_token)

    with Session(engine) as session:
        existing_pr = session.exec(
            select(PullRequest).where(
                PullRequest.agent_run_id == uuid.UUID(parent_run_id)
            )
        ).first()

    pr_url = ""
    pr_number = 0
    if existing_pr:
        try:
            gh_pr = gh_repo.get_pull(existing_pr.github_pr_number)
            comment_body, _mentions = _body_with_notification_mentions(body)
            gh_pr.create_issue_comment(
                f"**P.A.T.C.H. follow-up committed**\n\n{comment_body}"
            )
            pr_url = existing_pr.url
            pr_number = existing_pr.github_pr_number
        except GithubException as e:
            raise RuntimeError(f"Failed to comment on pull request: {e.data}") from e

    with Session(engine) as session:
        run = session.get(AgentRun, uuid.UUID(agent_run_id))
        if run is not None:
            run.branch_name = head_branch
            session.add(run)
            session.commit()

    return {
        "status": "follow_up_committed",
        "pr_number": pr_number,
        "pr_url": pr_url,
        "branch": head_branch,
    }
