import subprocess
import shlex

ALLOWED_COMMANDS: list[str] = [
    "uv", "pytest", "ruff", "pnpm", "npm", "git",
    "python", "pip", "ls", "cat", "echo", "pwd",
]

BLOCKED_TERMS: list[str] = [
    "sudo", "rm", "mkfs", "dd", "chmod",
    ".env", "printenv", "curl", "wget",
]

BLOCKED_OPERATORS: list[str] = ["&&", "||", ";", "|", ">", "<"]

def run_command(workspace_path: str, command: str, timeout: int = 60) -> dict[str, str]:
    """Run a shell command safely inside the workspace."""
    if not command.strip():
        raise ValueError("Empty command execution is not permitted.")

    cmd_lower = command.lower()
    if any(blocked in cmd_lower for blocked in BLOCKED_TERMS):
        raise PermissionError("Command execution blocked: contains restricted security terms.")

    try:
        tokens = shlex.split(command)
    except ValueError as e:
        raise ValueError(f"Invalid shell command format: {e}")

    first_word = tokens[0]
    if first_word not in ALLOWED_COMMANDS:
        raise PermissionError(f"Command '{first_word}' is not in the system allowlist.")

    if any(t in BLOCKED_OPERATORS for t in tokens):
        raise PermissionError("Command chaining operations are strictly prohibited.")

    try:
        result = subprocess.run(
            tokens,
            shell=False,
            cwd=workspace_path,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": str(result.returncode),
            "command": command,
        }
    except subprocess.TimeoutExpired:
        raise TimeoutError(f"Command timed out after {timeout} seconds.")

def run_test(workspace_path: str, test_command: str) -> dict[str, str]:
    """Run testing commands (e.g. pytest)."""
    return run_command(workspace_path, test_command, timeout=120)

def run_lint(workspace_path: str, lint_command: str) -> dict[str, str]:
    """Run linting commands (e.g. ruff)."""
    return run_command(workspace_path, lint_command, timeout=60)