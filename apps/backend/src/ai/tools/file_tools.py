from pathlib import Path
from typing import Dict, List
from langfuse.decorators import observe

BLOCKED_FILES = {".env", ".env.local", "id_rsa", "id_ed25519"}
BLOCKED_EXTENSIONS = {".pem", ".key", ".sqlite3"}

def _is_safe(path: Path) -> bool:
    if path.name in BLOCKED_FILES or any(path.name.startswith("secret") for f in [".env"]):
        return False
    if path.suffix in BLOCKED_EXTENSIONS:
        return False
    return True

@observe()
def list_files(workspace_path: str) -> Dict[str, List[str]]:
    """Melihat struktur file dan direktori dalam workspace."""
    root = Path(workspace_path)
    if not root.exists():
        raise FileNotFoundError(f"Workspace path {workspace_path} tidak ditemukan.")
        
    files = []
    for f in root.rglob("*"):
        if f.is_file() and _is_safe(f):
            rel = str(f.relative_to(root))
            if any(part in rel for part in [".git", ".venv", "node_modules", "__pycache__"]):
                continue
            files.append(rel)
    return {"files": sorted(files)}

@observe()
def read_file(workspace_path: str, file_path: str) -> Dict[str, str]:
    """Membaca isi file spesifik di dalam workspace."""
    target = Path(workspace_path) / file_path
    if not _is_safe(target):
         raise PermissionError(f"Akses ditolak: File {file_path} diblokir oleh sistem.")
    if not target.exists():
         raise FileNotFoundError(f"File {file_path} tidak ditemukan.")
    return {"content": target.read_text(encoding="utf-8", errors="replace")}

@observe()
def write_file(workspace_path: str, file_path: str, content: str) -> Dict[str, str]:
    """Menulis atau menimpa konten ke dalam file."""
    target = Path(workspace_path) / file_path
    if not _is_safe(target):
         raise PermissionError(f"Akses ditolak: Tidak dapat menulis ke {file_path}.")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return {"status": "success", "path": file_path}

@observe()
def search_file(workspace_path: str, pattern: str) -> Dict[str, List[str]]:
    """Mencari file berdasarkan nama atau pola ekstensi."""
    root = Path(workspace_path)
    matches = []
    for f in root.rglob(f"*{pattern}*"):
        if f.is_file() and _is_safe(f):
            rel = str(f.relative_to(root))
            if any(part in rel for part in [".git", ".venv", "node_modules"]):
                continue
            matches.append(rel)
    return {"matches": matches}