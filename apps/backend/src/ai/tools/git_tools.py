import subprocess

def _run_git(workspace_path: str, args: list[str]) -> dict[str, str]:
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=workspace_path,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return {
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": str(result.returncode),
        }
    except subprocess.TimeoutExpired:
        raise TimeoutError(f"Git command {' '.join(args)} timed out after 30s.")
    except Exception as e:
        raise RuntimeError(f"Git command execution failed: {str(e)}")

def get_git_status(workspace_path: str) -> dict[str, str]:
    """Get the current git status of the workspace."""
    return _run_git(workspace_path, ["status", "--porcelain"])

def get_git_diff(workspace_path: str) -> dict[str, str]:
    """Get the git diff of all current changes."""
    return _run_git(workspace_path, ["diff"])

def create_branch(workspace_path: str, branch_name: str) -> dict[str, str]:
    """Create and checkout a new git branch."""
    return _run_git(workspace_path, ["checkout", "-b", branch_name])

def commit_changes(workspace_path: str, message: str) -> dict[str, str]:
    """Stage all changes and commit them with a message."""
    stage = _run_git(workspace_path, ["add", "-A"])
    if stage["returncode"] != "0":
        raise RuntimeError(f"Git add failed: {stage['stderr']}")
    return _run_git(workspace_path, ["commit", "-m", message])

def push_branch(workspace_path: str, branch_name: str) -> dict[str, str]:
    """Push the branch to origin."""
    return _run_git(workspace_path, ["push", "origin", branch_name])