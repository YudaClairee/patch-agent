import subprocess
import pytest
from pathlib import Path
from src.ai.tools.git_tools import get_git_status

def _init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)

def test_git_status_clean_repo(tmp_path: Path) -> None:
    _init_git_repo(tmp_path)
    result = get_git_status(str(tmp_path))
    assert result["returncode"] == "0"

def test_git_raises_on_invalid_path() -> None:
    with pytest.raises((TimeoutError, RuntimeError, Exception)):
        get_git_status("/invalid/nonexistent/path")