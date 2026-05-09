from pathlib import Path

_BLOCKED_PATTERNS: list[str] = [
    ".env", ".env.local", "id_rsa", "id_ed25519",
    "secrets.", ".pem", ".key",
]

def _is_blocked(file_path: str) -> bool:
    for pattern in _BLOCKED_PATTERNS:
        if pattern in file_path:
            return True
    return False

def list_files(workspace_path: str) -> dict[str, list[str] | int]:
    """List all files in the workspace directory."""
    base = Path(workspace_path)
    if not base.exists():
        raise FileNotFoundError(f"Path {workspace_path} does not exist.")

    files: list[str] = []
    for f in base.rglob("*"):
        if f.is_file():
            rel = str(f.relative_to(base))
            if not _is_blocked(rel):
                files.append(rel)

    return {"files": files, "count": len(files)}

def read_file(workspace_path: str, file_path: str) -> dict[str, str]:
    """Read the content of a specific file."""
    if _is_blocked(file_path):
        raise PermissionError(f"Access to {file_path} is blocked for security reasons.")

    full_path = Path(workspace_path) / file_path
    if not full_path.exists():
        raise FileNotFoundError(f"File {file_path} not found.")

    content = full_path.read_text(encoding="utf-8", errors="replace")
    return {"file_path": file_path, "content": content}

def write_file(workspace_path: str, file_path: str, content: str) -> dict[str, str]:
    """Write or overwrite content to a specific file."""
    if _is_blocked(file_path):
        raise PermissionError(f"Writing to {file_path} is blocked for security reasons.")

    full_path = Path(workspace_path) / file_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")
    return {"status": "success", "file_path": file_path}

def search_file(workspace_path: str, pattern: str) -> dict[str, list[str] | int]:
    """Search for files by name pattern."""
    base = Path(workspace_path)
    matches: list[str] = []

    for f in base.rglob(f"*{pattern}*"):
        if f.is_file() and not _is_blocked(str(f.relative_to(base))):
            matches.append(str(f.relative_to(base)))

    return {"matches": matches, "count": len(matches)}