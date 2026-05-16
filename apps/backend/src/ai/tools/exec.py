"""
Codex-style minimal tool surface for the P.A.T.C.H. agent.

Three primitives that compose to cover every workflow:
- exec_command: PTY-backed shell, restricted to /workspace, timeout-bounded
- write_stdin: write to a backgrounded PTY (for interactive prompts / TUIs)
- patch_file: apply a targeted patch to one file under /workspace
"""
import os
import pty
import re
import select
import signal
import shlex
import subprocess
import tempfile
import time
from pathlib import Path

WORKSPACE = "/workspace"
_MAX_OUTPUT_BYTES = 64 * 1024  # 64KB cap per call to keep token cost sane
_FENCED_PATCH_RE = re.compile(r"```(?:diff|patch)?\s*\n(.*?)\n```", re.I | re.S)
_PATCH_MARKERS = ("diff --git ", "--- ", "@@ ", "*** Begin Patch")
_UNIFIED_HEADER_RE = re.compile(r"^(---|\+\+\+)\s+", re.M)
_NUMBERED_HUNK_RE = re.compile(
    r"^@@\s+-\d+(?:,\d+)?\s+\+\d+(?:,\d+)?\s+@@",
    re.M,
)
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


def _workspace_relative_path(target: Path) -> str:
    return target.relative_to(Path(WORKSPACE).resolve()).as_posix()


def _looks_like_patch(text: str) -> bool:
    return any(marker in text for marker in _PATCH_MARKERS) or bool(
        _UNIFIED_HEADER_RE.search(text) or _NUMBERED_HUNK_RE.search(text)
    )


def _extract_patch_payload(diff: str) -> str:
    """Accept raw patches and common markdown-wrapped patches from model output."""
    fenced_blocks = _FENCED_PATCH_RE.findall(diff)
    for block in fenced_blocks:
        if _looks_like_patch(block):
            text = block.strip("\n")
            return text + "\n"

    text = diff.strip("\n")
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if any(line.lstrip().startswith(marker) for marker in _PATCH_MARKERS):
            text = "\n".join(lines[index:])
            break
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0].rstrip("\n")
    return text + "\n"


def _patch_header_path(raw: str) -> str | None:
    token = raw.strip()
    if not token:
        return None
    try:
        parts = shlex.split(token, comments=False, posix=True)
    except ValueError:
        parts = token.split()
    if not parts:
        return None

    path = parts[0]
    if path == "/dev/null":
        return None
    if path.startswith("/workspace/"):
        path = path.removeprefix("/workspace/")
    if path.startswith(("a/", "b/")):
        path = path[2:]
    return Path(path).as_posix()


def _validate_patch_targets(diff: str, expected_path: str) -> None:
    paths: set[str] = set()
    for line in diff.splitlines():
        if line.startswith(("--- ", "+++ ")):
            path = _patch_header_path(line[4:])
            if path is None:
                continue
            _validate_workspace_path(path)
            paths.add(path)

    if paths and paths != {expected_path}:
        raise PermissionError(
            f"Patch targets {sorted(paths)!r}, but patch_file path is {expected_path!r}."
        )


def _patch_candidates(diff: str, expected_path: str) -> list[tuple[str, str]]:
    candidates = [("as-provided", diff)]
    if not _UNIFIED_HEADER_RE.search(diff) and _NUMBERED_HUNK_RE.search(diff):
        candidates.append(
            (
                "hunk-only",
                f"--- a/{expected_path}\n+++ b/{expected_path}\n{diff.lstrip()}",
            )
        )
    return candidates


def _run_git_apply(diff: str, strip: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "apply", "--recount", "--whitespace=fix", f"-p{strip}", "-"],
        cwd=WORKSPACE,
        input=diff,
        capture_output=True,
        text=True,
        timeout=30,
        env=_safe_subprocess_env(),
    )


def _run_patch(diff: str, strip: int) -> subprocess.CompletedProcess[str]:
    with tempfile.NamedTemporaryFile("w", suffix=".patch", delete=False) as f:
        f.write(diff)
        patch_path = f.name
    try:
        dry_run = subprocess.run(
            [
                "patch",
                f"-p{strip}",
                "-F3",
                "--dry-run",
                "--no-backup-if-mismatch",
                "-i",
                patch_path,
            ],
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            timeout=30,
            env=_safe_subprocess_env(),
        )
        if dry_run.returncode != 0:
            return dry_run

        return subprocess.run(
            ["patch", f"-p{strip}", "-F3", "--no-backup-if-mismatch", "-i", patch_path],
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


def _find_line_sequence(lines: list[str], sequence: list[str], start: int) -> int | None:
    if not sequence:
        return None
    max_start = len(lines) - len(sequence)
    for index in range(start, max_start + 1):
        if lines[index : index + len(sequence)] == sequence:
            return index
    for index in range(0, start):
        if lines[index : index + len(sequence)] == sequence:
            return index
    return None


def _parse_line_patch_hunks(lines: list[str]) -> list[list[tuple[str, str]]]:
    hunks: list[list[tuple[str, str]]] = []
    current: list[tuple[str, str]] = []

    for line in lines:
        if line.startswith("@@"):
            if current:
                hunks.append(current)
                current = []
            continue
        if line == "*** End of File" or line.startswith("*** "):
            continue
        if line.startswith((" ", "-", "+")):
            current.append((line[0], line[1:]))
            continue
        if line == "":
            current.append((" ", ""))
            continue
        raise ValueError(f"Unsupported patch line: {line!r}")

    if current:
        hunks.append(current)
    return hunks


def _apply_line_hunks(target: Path, hunks: list[list[tuple[str, str]]]) -> int:
    if not hunks:
        raise ValueError("No editable hunks were found in the patch.")

    original = target.read_text()
    file_lines = original.splitlines()
    final_newline = original.endswith("\n")
    cursor = 0

    for hunk in hunks:
        old_lines = [text for kind, text in hunk if kind in {" ", "-"}]
        new_lines = [text for kind, text in hunk if kind in {" ", "+"}]
        start = _find_line_sequence(file_lines, old_lines, cursor)
        if start is None:
            raise ValueError(
                "Could not locate patch hunk in target file. "
                "Read the file again or provide more context lines."
            )
        file_lines[start : start + len(old_lines)] = new_lines
        cursor = start + len(new_lines)

    updated = "\n".join(file_lines)
    if final_newline or original == "":
        updated += "\n"
    target.write_text(updated)
    return len(hunks)


def _apply_codex_style_patch(target: Path, expected_path: str, diff: str) -> dict | None:
    if "*** Begin Patch" not in diff or "*** Update File:" not in diff:
        return None

    blocks: list[list[str]] = []
    current_path: str | None = None
    current_lines: list[str] = []

    def flush_current() -> None:
        nonlocal current_path, current_lines
        if current_path is None:
            return
        if current_path != expected_path:
            raise PermissionError(
                f"Patch targets {current_path!r}, but patch_file path is {expected_path!r}."
            )
        blocks.append(current_lines)
        current_path = None
        current_lines = []

    for line in diff.splitlines():
        if line.startswith("*** Update File:"):
            flush_current()
            path = _patch_header_path(line.split(":", 1)[1])
            if path is None:
                raise ValueError("Codex patch is missing an update file path.")
            _validate_workspace_path(path)
            current_path = path
            current_lines = []
            continue
        if line == "*** End Patch":
            flush_current()
            break
        if current_path is not None:
            current_lines.append(line)

    if not blocks:
        raise ValueError("Codex patch did not contain an update block.")

    all_hunks: list[list[tuple[str, str]]] = []
    for block in blocks:
        all_hunks.extend(_parse_line_patch_hunks(block))
    hunk_count = _apply_line_hunks(target, all_hunks)

    return {
        "ok": True,
        "path": expected_path,
        "applied_with": "codex apply_patch format",
        "hunks_applied": hunk_count,
        "stdout": "",
        "stderr": "",
    }


def _patch_failure(
    expected_path: str,
    message: str,
    stdout: str = "",
    stderr: str = "",
    git_apply_stderr: str = "",
    exit_code: int = 1,
    attempts: list[dict[str, str | int]] | None = None,
) -> dict:
    return {
        "ok": False,
        "path": expected_path,
        "applied_with": "failed",
        "stdout": stdout,
        "stderr": stderr or message,
        "git_apply_stderr": git_apply_stderr,
        "exit_code": exit_code,
        "attempts": (attempts or [])[-8:],
        "hint": (
            "Patch was rejected. Accepted formats: unified diff with ---/+++ headers, "
            "numbered hunk-only diff starting with @@, or Codex-style "
            "*** Begin Patch / *** Update File. Context lines must include their "
            "leading space. For new files or full rewrites, use write_file(path, content)."
        ),
    }


def patch_file(path: str, diff: str) -> dict:
    """
    Apply a targeted patch to an EXISTING file under /workspace.
    Accepts unified diffs, hunk-only unified diffs, and Codex-style update patches.
    Tries `git apply --recount` first, then falls back to `patch -F3`.
    For NEW files / full rewrites, prefer `write_file`.
    """
    target = _validate_workspace_path(path)
    expected_path = _workspace_relative_path(target)
    if not target.exists() or not target.is_file():
        return _patch_failure(
            expected_path,
            f"patch_file requires an existing file: {expected_path}",
        )

    diff = _extract_patch_payload(diff)
    try:
        codex_result = _apply_codex_style_patch(target, expected_path, diff)
    except ValueError as exc:
        return _patch_failure(expected_path, str(exc))
    if codex_result is not None:
        return codex_result

    attempts: list[dict[str, str | int]] = []
    first_git_stderr = ""
    last_result: subprocess.CompletedProcess[str] | None = None

    for source, candidate in _patch_candidates(diff, expected_path):
        _validate_patch_targets(candidate, expected_path)

        for strip in (1, 0):
            result = _run_git_apply(candidate, strip)
            last_result = result
            first_git_stderr = first_git_stderr or result.stderr
            attempts.append(
                {
                    "tool": f"git apply -p{strip}",
                    "source": source,
                    "exit_code": result.returncode,
                    "stderr": result.stderr,
                }
            )
            if result.returncode == 0:
                return {
                    "ok": True,
                    "path": expected_path,
                    "applied_with": f"git apply --recount -p{strip}",
                    "normalized_from": source,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }

        for strip in (1, 0):
            result = _run_patch(candidate, strip)
            last_result = result
            attempts.append(
                {
                    "tool": f"patch -p{strip} -F3",
                    "source": source,
                    "exit_code": result.returncode,
                    "stderr": result.stderr,
                }
            )
            if result.returncode == 0:
                return {
                    "ok": True,
                    "path": expected_path,
                    "applied_with": f"patch -p{strip} -F3",
                    "normalized_from": source,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }

    stdout = last_result.stdout if last_result is not None else ""
    stderr = last_result.stderr if last_result is not None else ""
    exit_code = last_result.returncode if last_result is not None else 1

    return _patch_failure(
        expected_path,
        "Patch was rejected.",
        stdout=stdout,
        stderr=stderr,
        git_apply_stderr=first_git_stderr,
        exit_code=exit_code,
        attempts=attempts,
    )


__all__ = ["exec_command", "write_stdin", "patch_file", "write_file"]

