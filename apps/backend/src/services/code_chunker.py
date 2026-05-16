"""Line-window code chunker for repository indexing.

Splits source files into overlapping line-window chunks suitable for
embedding and semantic search. Skips binary/noisy files and directories.
"""
from __future__ import annotations

import hashlib
import logging
import os
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

SKIP_DIRS: set[str] = {
    ".git",
    "node_modules",
    "dist",
    "build",
    ".next",
    ".turbo",
    ".venv",
    "venv",
    "__pycache__",
    "coverage",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".idea",
    ".vscode",
    ".github",
}

SKIP_EXTENSIONS: set[str] = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".ico",
    ".webp",
    ".mp4",
    ".mov",
    ".avi",
    ".webm",
    ".zip",
    ".tar",
    ".gz",
    ".bz2",
    ".7z",
    ".rar",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".lock",
    ".min.js",
    ".min.css",
    ".map",
    ".pyc",
    ".pyo",
    ".class",
    ".o",
    ".so",
    ".dll",
    ".exe",
    ".bin",
    ".pdf",
    ".mp3",
    ".wav",
}

MAX_FILE_SIZE_BYTES = 256 * 1024  # 256 KB
CHUNK_SIZE = 80  # lines per chunk
CHUNK_OVERLAP = 15  # overlapping lines between chunks
MAX_CHARS_PER_CHUNK = 12_000

LANG_MAP: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
    ".java": "java",
    ".kt": "kotlin",
    ".swift": "swift",
    ".c": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".h": "c",
    ".hpp": "cpp",
    ".cs": "csharp",
    ".php": "php",
    ".lua": "lua",
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "bash",
    ".sql": "sql",
    ".html": "html",
    ".htm": "html",
    ".css": "css",
    ".scss": "scss",
    ".sass": "sass",
    ".less": "less",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".xml": "xml",
    ".md": "markdown",
    ".rst": "rst",
    ".proto": "protobuf",
    ".graphql": "graphql",
    ".gql": "graphql",
    ".tf": "hcl",
    ".dart": "dart",
    ".ex": "elixir",
    ".exs": "elixir",
    ".erl": "erlang",
    ".hs": "haskell",
    ".ml": "ocaml",
    ".r": "r",
    ".R": "r",
    ".scala": "scala",
    ".clj": "clojure",
    ".vue": "vue",
    ".svelte": "svelte",
}


@dataclass
class CodeChunk:
    file_path: str
    language: str | None
    start_line: int
    end_line: int
    content: str
    content_hash: str


def _content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:64]


def _detect_language(file_path: str) -> str | None:
    ext = Path(file_path).suffix.lower()
    return LANG_MAP.get(ext)


def _should_skip_path(path: str, root: str) -> bool:
    rel = os.path.relpath(path, root)
    parts = Path(rel).parts
    return any(part in SKIP_DIRS for part in parts)


def _is_binary(file_path: str) -> bool:
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(8192)
        return b"\x00" in chunk
    except (OSError, PermissionError):
        return True


def chunk_file(
    file_path: str,
    root: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[CodeChunk]:
    """Read a file and split it into overlapping line-window chunks."""
    rel_path = os.path.relpath(file_path, root)

    if _should_skip_path(file_path, root):
        return []

    ext = Path(file_path).suffix.lower()
    if ext in SKIP_EXTENSIONS:
        return []

    try:
        file_size = os.path.getsize(file_path)
    except OSError:
        return []
    if file_size > MAX_FILE_SIZE_BYTES or file_size == 0:
        return []

    if _is_binary(file_path):
        return []

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except (OSError, PermissionError):
        return []

    if not lines:
        return []

    language = _detect_language(file_path)
    chunks: list[CodeChunk] = []
    step = max(chunk_size - overlap, 1)
    total_lines = len(lines)

    for start_idx in range(0, total_lines, step):
        end_idx = min(start_idx + chunk_size, total_lines)
        chunk_lines = lines[start_idx:end_idx]
        content = "".join(chunk_lines)

        if len(content) > MAX_CHARS_PER_CHUNK:
            content = content[:MAX_CHARS_PER_CHUNK]

        if not content.strip():
            continue

        chunks.append(
            CodeChunk(
                file_path=rel_path,
                language=language,
                start_line=start_idx + 1,
                end_line=end_idx,
                content=content,
                content_hash=_content_hash(content),
            )
        )

        if end_idx >= total_lines:
            break

    return chunks


def chunk_repository(workspace_path: str) -> list[CodeChunk]:
    """Scan a repository and return all code chunks."""
    all_chunks: list[CodeChunk] = []
    workspace_path = os.path.abspath(workspace_path)

    for dirpath, dirnames, filenames in os.walk(workspace_path):
        dirnames[:] = [
            d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")
        ]

        for filename in sorted(filenames):
            file_path = os.path.join(dirpath, filename)
            chunks = chunk_file(file_path, workspace_path)
            all_chunks.extend(chunks)

    logger.info(
        "Chunked repository %s: %d files, %d chunks",
        workspace_path,
        len({c.file_path for c in all_chunks}),
        len(all_chunks),
    )
    return all_chunks
