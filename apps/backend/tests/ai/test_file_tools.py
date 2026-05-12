import pytest
from pathlib import Path
from src.ai.tools.file_tools import list_files, read_file, write_file, search_file

def test_list_files_returns_files(tmp_path: Path) -> None:
    (tmp_path / "main.py").write_text("print('hello')")
    result = list_files(str(tmp_path))
    assert result["count"] == 1
    assert "main.py" in result["files"] # type: ignore

def test_list_files_excludes_blocked(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("SECRET=123")
    result = list_files(str(tmp_path))
    assert ".env" not in result["files"] # type: ignore
    assert result["count"] == 0

def test_read_file_returns_content(tmp_path: Path) -> None:
    (tmp_path / "hello.py").write_text("print('patch')")
    result = read_file(str(tmp_path), "hello.py")
    assert result["content"] == "print('patch')"

def test_read_file_raises_on_blocked_path(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("SECRET=123")
    with pytest.raises(PermissionError):
        read_file(str(tmp_path), ".env")

def test_write_file_creates_file(tmp_path: Path) -> None:
    result = write_file(str(tmp_path), "new_module.py", "x = 1")
    assert result["status"] == "success"
    assert (tmp_path / "new_module.py").read_text() == "x = 1"

def test_write_file_raises_on_blocked_path(tmp_path: Path) -> None:
    with pytest.raises(PermissionError):
        write_file(str(tmp_path), ".env", "SECRET=bad")

def test_search_file_finds_match(tmp_path: Path) -> None:
    (tmp_path / "auth_router.py").write_text("pass")
    result = search_file(str(tmp_path), "auth")
    assert "auth_router.py" in result["matches"] # type: ignore