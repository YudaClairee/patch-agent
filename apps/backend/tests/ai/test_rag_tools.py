import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.ai.tools.rag_tools import search_code, get_code_context

def test_get_code_context_returns_content(tmp_path: Path) -> None:
    (tmp_path / "auth.py").write_text("def login(): pass")
    result = get_code_context(str(tmp_path), "auth.py")
    assert "def login" in result["content"]

def test_get_code_context_raises_on_blocked(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("SECRET=123")
    with pytest.raises(PermissionError):
        get_code_context(str(tmp_path), ".env")

@patch("src.ai.tools.rag_tools._get_chroma_client")
def test_search_code_raises_when_collection_missing(mock_chroma: MagicMock) -> None:
    mock_client = MagicMock()
    mock_client.get_collection.side_effect = Exception("Collection not found")
    mock_chroma.return_value = mock_client

    with pytest.raises(FileNotFoundError):
        search_code("login", "repo_123", "main")