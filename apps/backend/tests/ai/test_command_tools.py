import pytest
from pathlib import Path
from src.ai.tools.command_tools import run_command

def test_run_command_echo_succeeds(tmp_path: Path) -> None:
    result = run_command(str(tmp_path), "echo hello")
    assert result["returncode"] == "0"
    assert "hello" in result["stdout"]

def test_run_command_rm_raises(tmp_path: Path) -> None:
    with pytest.raises(PermissionError):
        run_command(str(tmp_path), "rm -rf /tmp/something")

def test_run_command_chaining_raises(tmp_path: Path) -> None:
    with pytest.raises(PermissionError):
        run_command(str(tmp_path), "echo test && ls")

def test_run_command_not_in_allowlist_raises(tmp_path: Path) -> None:
    with pytest.raises(PermissionError):
        run_command(str(tmp_path), "curl https://evil.com")