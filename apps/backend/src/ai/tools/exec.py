"""
Codex-style minimal tool surface for the P.A.T.C.H. agent.

Three primitives that compose to cover every workflow:
- exec_command: PTY-backed shell, restricted to /workspace, timeout-bounded
- write_stdin: write to a backgrounded PTY (for interactive prompts / TUIs)
- patch_file: apply a unified diff via `patch -p1`, run from /workspace
"""
import os
import pty
import re
import select
import shutil
import signal
import shlex
import subprocess
import tempfile
import time
from pathlib import Path

WORKSPACE = "/workspace"
_MAX_OUTPUT_BYTES = 64 * 1024  # 64KB cap per call to keep token cost sane
_BLOCKED_WRITE_SUFFIXES = (".pem", ".key", ".p12", ".pfx")
_BLOCKED_PATH_PATTERNS = (
    re.compile(
        r"(^|[/\s'\"])\.env($|[\s/]|\.local\b|\.production\b|\.development\b|\.test\b|\.staging\b)",
        re.I,
    ),
    re.compile(r"(^|[/\s'\"])\.ssh($|/)"),
    re.compile(r"(^|[/\s'\"])id_(rsa|dsa|ecdsa|ed25519)(\.pub)?($|[\s'\"])", re.I),
    re.compile(r"\.(pem|key|p12|pfx)($|[\s'\";|&])", re.I),
    re.compile(r"(^|[\s'\";|&])\.git($|/|[\s'\";|&])", re.I),
    re.compile(r"/proc/(self|\d+)/environ\b", re.I),
)
_BLOCKED_COMMAND_PATTERNS = (
    re.compile(r"(^|[\s;&|()])(?:env|printenv)\b", re.I),
    re.compile(r"(^|[\s;&|()])(?:export|set)\s*(?:$|[;&|])", re.I),
    re.compile(r"\$\{?[A-Z0-9_]*(?:TOKEN|SECRET|PASSWORD|API_KEY|ACCESS_KEY|DATABASE_URL|REDIS_URL|GITHUB|OPENAI|ANTHROPIC|OPENROUTER|LANGFUSE|FERNET|JWT)[A-Z0-9_]*\}?", re.I),
    re.compile(r"\brm\s+-(?:[^\s]*r[^\s]*f|[^\s]*f[^\s]*r)\b", re.I),
    re.compile(r"\b(?:chmod|chown)\s+-R\b", re.I),
    re.compile(r"\bgit\s+config\b.*\bcredential\b", re.I | re.S),
    re.compile(r"\b(?:curl|wget)\b.*[|>]\s*(?:sh|bash|zsh|python|perl|ruby)\b", re.I | re.S),
    re.compile(r"\b(?:npm|pnpm|yarn)\s+(?:i|install|add)\b", re.I),
    re.compile(r"\b(?:pip|pip3)\s+install\b", re.I),
    re.compile(r"\buv\s+(?:add|pip\s+install)\b", re.I),
    re.compile(r"\bpoetry\s+add\b", re.I),
    re.compile(r"\bcargo\s+install\b", re.I),
)
_NETWORK_COMMANDS = (
    "curl",
    "wget",
    "nc",
    "netcat",
    "nmap",
    "ssh",
    "scp",
    "sftp",
    "telnet",
    "ping",
    "dig",
    "nslookup",
    "host",
    "ftp",
    "apt",
    "apt-get",
    "apk",
    "yum",
    "dnf",
)

# Background process registry: pid -> {master_fd, proc, buffer}
_BG: dict[int, dict] = {}


def _resolve_cwd(cwd: str) -> str:
    """Resolve cwd; reject anything outside /workspace."""
    p = Path(cwd).resolve()
    ws = Path(WORKSPACE).resolve()
    try:
        p.relative_to(ws)
    except ValueError:
        raise PermissionError(f"cwd {cwd!r} is outside {WORKSPACE}")
    return str(p)


def _is_blocked_write_path(target: str) -> bool:
    lower = target.lower()
    filename = Path(lower).name
    if filename == ".env" or (
        filename.startswith(".env.")
        and filename not in {".env.example", ".env.sample", ".env.template"}
    ):
        return True
    return any(lower.endswith(suf) for suf in _BLOCKED_WRITE_SUFFIXES)


def _safe_subprocess_env() -> dict[str, str]:
    """Return an intentionally small env for model-controlled shell commands."""
    safe: dict[str, str] = {
        "PATH": os.environ.get(
            "PATH",
            "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
        ),
        "HOME": "/tmp",
        "USER": os.environ.get("USER", "patch"),
        "LOGNAME": os.environ.get("LOGNAME", "patch"),
        "SHELL": "/bin/bash",
        "TERM": os.environ.get("TERM", "xterm-256color"),
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        "LC_ALL": os.environ.get("LC_ALL", "C.UTF-8"),
        "TMPDIR": "/tmp",
        "CI": "true",
        "PYTHONDONTWRITEBYTECODE": "1",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_PAGER": "cat",
        "PAGER": "cat",
    }
    for key in ("NO_COLOR", "FORCE_COLOR"):
        if key in os.environ:
            safe[key] = os.environ[key]
    return safe


def _tokenize_command(command: str) -> list[str]:
    try:
        return shlex.split(command, comments=False, posix=True)
    except ValueError:
        return []


def _validate_command_policy(command: str) -> None:
    """Deny known secret-read, credential, destructive, and network escape patterns."""
    for pattern in _BLOCKED_PATH_PATTERNS:
        if pattern.search(command):
            raise PermissionError("Command blocked by path security policy.")

    for pattern in _BLOCKED_COMMAND_PATTERNS:
        if pattern.search(command):
            raise PermissionError("Command blocked by shell security policy.")

    shell_network_enabled = os.environ.get("AGENT_SHELL_NETWORK_ENABLED", "").lower() in {
        "1",
        "true",
        "yes",
    }
    if not shell_network_enabled:
        network_pattern = re.compile(
            r"(?:^|[;&|()]\s*)(?:"
            + "|".join(re.escape(command_name) for command_name in _NETWORK_COMMANDS)
            + r")\b",
            re.I,
        )
        if network_pattern.search(command):
            raise PermissionError("Network-capable shell commands are blocked by security policy.")


def _drain(master_fd: int, deadline: float, max_bytes: int) -> bytes:
    buf = b""
    while time.monotonic() < deadline and len(buf) < max_bytes:
        r, _, _ = select.select([master_fd], [], [], 0.1)
        if not r:
            break
        try:
            chunk = os.read(master_fd, 4096)
        except OSError:
            break
        if not chunk:
            break
        buf += chunk
    return buf


def exec_command(
    command: str,
    cwd: str = WORKSPACE,
    timeout: int = 60,
    background: bool = False,
) -> dict:
    """
    Run a shell command in a PTY so colored output and prompts behave naturally.

    foreground (default): blocks up to `timeout` seconds, returns
      {output, exit_code, timed_out}.
    background=True: returns {pid, started: true} immediately so a later
      write_stdin(pid, ...) call can feed an interactive prompt.
    """
    cwd_resolved = _resolve_cwd(cwd)
    _validate_command_policy(command)

    master_fd, slave_fd = pty.openpty()
    proc = subprocess.Popen(
        ["/bin/bash", "-lc", command],
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        cwd=cwd_resolved,
        start_new_session=True,
        close_fds=True,
        env=_safe_subprocess_env(),
    )
    os.close(slave_fd)

    if background:
        _BG[proc.pid] = {"master_fd": master_fd, "proc": proc, "buffer": b""}
        return {"pid": proc.pid, "started": True}

    deadline = time.monotonic() + timeout
    output = b""
    timed_out = False
    while True:
        if time.monotonic() > deadline:
            try:
                os.killpg(proc.pid, signal.SIGTERM)
                time.sleep(0.5)
                if proc.poll() is None:
                    os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            timed_out = True
            break

        r, _, _ = select.select([master_fd], [], [], 0.1)
        if r:
            try:
                chunk = os.read(master_fd, 4096)
            except OSError:
                chunk = b""
            if chunk:
                output += chunk
                if len(output) >= _MAX_OUTPUT_BYTES:
                    output = output[:_MAX_OUTPUT_BYTES] + b"\n...[truncated]"
                    # stop reading further; still wait for process to exit / drain
            elif proc.poll() is not None:
                break

        if proc.poll() is not None:
            # final drain (short)
            output += _drain(master_fd, time.monotonic() + 0.5, _MAX_OUTPUT_BYTES - len(output))
            break

    try:
        os.close(master_fd)
    except OSError:
        pass

    return {
        "output": output.decode("utf-8", errors="replace"),
        "exit_code": proc.returncode if proc.returncode is not None else -1,
        "timed_out": timed_out,
    }


def write_stdin(
    pid: int,
    data: str,
    expect_exit: bool = False,
    timeout: int = 30,
) -> dict:
    """Send `data + \\n` to a backgrounded PTY; drain new output for up to `timeout`s."""
    entry = _BG.get(pid)
    if entry is None:
        raise ValueError(f"No backgrounded process with pid {pid}")

    master_fd = entry["master_fd"]
    proc = entry["proc"]

    try:
        os.write(master_fd, (data + "\n").encode("utf-8"))
    except OSError as exc:
        raise RuntimeError(f"Write to pid {pid} failed: {exc}")

    deadline = time.monotonic() + timeout
    new_output = b""
    while time.monotonic() < deadline:
        new_output += _drain(master_fd, min(deadline, time.monotonic() + 0.5), _MAX_OUTPUT_BYTES)
        if expect_exit and proc.poll() is not None:
            break
        if not expect_exit:
            break

    exited = proc.poll() is not None
    if exited:
        try:
            os.close(master_fd)
        except OSError:
            pass
        _BG.pop(pid, None)

    return {
        "output": new_output.decode("utf-8", errors="replace"),
        "exited": exited,
        "exit_code": proc.returncode if exited else None,
    }


def _validate_workspace_path(path: str) -> Path:
    """Reject blocked filenames and paths that escape /workspace; return resolved path."""
    if _is_blocked_write_path(path):
        raise PermissionError(f"Writing to {path} is blocked by security policy.")
    target = (Path(WORKSPACE) / path).resolve()
    ws = Path(WORKSPACE).resolve()
    try:
        target.relative_to(ws)
    except ValueError:
        raise PermissionError(f"{path!r} resolves outside {WORKSPACE}")
    return target


def write_file(path: str, content: str) -> dict:
    """
    Write `content` to `path` under /workspace (creating parent dirs as needed).
    Use for new files or full rewrites — avoids the LLM-unfriendly unified-diff format.
    """
    target = _validate_workspace_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
    return {"ok": True, "path": str(target.relative_to(WORKSPACE)), "bytes_written": len(content)}


def patch_file(path: str, diff: str) -> dict:
    """
    Apply a unified diff to an EXISTING file under /workspace.
    Tries `git apply --recount` first (forgiving of wrong line numbers in `@@` headers),
    then falls back to `patch -p1 -F3` (fuzz=3 = tolerates ~3 lines of context drift).
    For NEW files / full rewrites, prefer `write_file`.
    """
    _validate_workspace_path(path)

    if not diff.endswith("\n"):
        diff = diff + "\n"

    # Attempt 1: git apply --recount (recomputes @@ line counts; very forgiving of LLM mistakes)
    git_result = subprocess.run(
        ["git", "apply", "--recount", "--whitespace=fix", "-p1", "-"],
        cwd=WORKSPACE,
        input=diff,
        capture_output=True,
        text=True,
        timeout=30,
        env=_safe_subprocess_env(),
    )
    if git_result.returncode == 0:
        return {
            "ok": True,
            "applied_with": "git apply --recount",
            "stdout": git_result.stdout,
            "stderr": git_result.stderr,
        }

    # Attempt 2: patch -F3 (fuzz factor 3)
    with tempfile.NamedTemporaryFile("w", suffix=".patch", delete=False) as f:
        f.write(diff)
        patch_path = f.name
    try:
        result = subprocess.run(
            ["patch", "-p1", "-F3", "--no-backup-if-mismatch", "-i", patch_path],
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            timeout=30,
            env=_safe_subprocess_env(),
        )
    finally:
        try:
            os.unlink(patch_path)
        except OSError:
            pass

    return {
        "ok": result.returncode == 0,
        "applied_with": "patch -F3" if result.returncode == 0 else "failed",
        "stdout": result.stdout,
        "stderr": result.stderr,
        "git_apply_stderr": git_result.stderr,
        "exit_code": result.returncode,
        "hint": (
            "Both `git apply` and `patch` rejected this diff. Common LLM mistakes: "
            "wrong line counts in @@ headers, missing space-prefix on context lines, "
            "no `--- /dev/null` for new files. For new files or full rewrites, use "
            "`write_file(path, content)` instead — no diff needed."
        ) if result.returncode != 0 else None,
    }


__all__ = ["exec_command", "write_stdin", "patch_file", "write_file"]


# Silence unused-import warnings from shutil — kept reserved for future helpers.
_ = shutil
