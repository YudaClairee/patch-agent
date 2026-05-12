import uuid
from unittest.mock import MagicMock, patch

import pytest

from src.models.enums import IndexStatus

@pytest.fixture
def repo_row():
    repo = MagicMock()
    repo.id = uuid.uuid4()
    repo.clone_url = "https://github.com/octocat/Hello-World.git"
    return repo

@pytest.fixture
def index_row(repo_row):
    idx = MagicMock()
    idx.id = uuid.uuid4()
    idx.repository_id = repo_row.id
    idx.branch = "main"
    idx.status = IndexStatus.pending
    idx.chroma_collection_name = "repo_test_main_123"
    idx.chunk_count = 0
    idx.error_message = None
    idx.indexed_at = None
    return idx

@pytest.fixture
def mock_session(repo_row, index_row):
    session = MagicMock()
    
    def side_effect_get(model_class, obj_id):
        if model_class.__name__ == 'Repository' and obj_id == repo_row.id:
            return repo_row
        if model_class.__name__ == 'CodebaseIndex' and obj_id == index_row.id:
            return index_row
        return None

    session.get.side_effect = side_effect_get
    return session

def _fake_embedding(_: str) -> list[float]:
    return [0.1, 0.2, 0.3]

@patch("src.services.indexing.Repository")
@patch("src.services.indexing.CodebaseIndex")
@patch("src.services.indexing._get_embedding", side_effect=_fake_embedding)
@patch("src.services.indexing._chroma_client")
@patch("src.services.indexing._clone_repo")
def test_index_repository_transitions_to_ready(
    mock_clone: MagicMock,
    mock_chroma: MagicMock,
    mock_embed: MagicMock,
    mock_codebase_index_cls: MagicMock,
    mock_repo_cls: MagicMock,
    tmp_path,
    mock_session: MagicMock,
    repo_row: MagicMock,
    index_row: MagicMock,
):
    mock_clone.return_value = str(tmp_path)
    (tmp_path / "main.py").write_text("def hello(): pass")

    mock_collection = MagicMock()
    mock_chroma.create_collection.return_value = mock_collection

    mock_codebase_index_cls.__name__ = 'CodebaseIndex'
    mock_repo_cls.__name__ = 'Repository'

    from src.services.indexing import _run_index

    _run_index(index_row.id, repo_row.id, "main", mock_session)

    assert index_row.status == IndexStatus.ready
    assert index_row.chunk_count > 0
    assert index_row.indexed_at is not None
    mock_collection.add.assert_called_once()
    mock_session.commit.assert_called()


@patch("src.services.indexing.Repository")
@patch("src.services.indexing.CodebaseIndex")
@patch("src.services.indexing._clone_repo")
def test_index_repository_transitions_to_failed_on_clone_error(
    mock_clone: MagicMock,
    mock_codebase_index_cls: MagicMock,
    mock_repo_cls: MagicMock,
    mock_session: MagicMock,
    repo_row: MagicMock,
    index_row: MagicMock,
):
    mock_clone.side_effect = RuntimeError("Clone failed: repo not found")
    
    mock_codebase_index_cls.__name__ = 'CodebaseIndex'
    mock_repo_cls.__name__ = 'Repository'

    from src.services.indexing import _run_index

    _run_index(index_row.id, repo_row.id, "main", mock_session)

    assert index_row.status == IndexStatus.failed
    assert index_row.error_message is not None
    assert "Clone failed" in index_row.error_message
    mock_session.commit.assert_called()


@patch("src.services.indexing.Repository")
@patch("src.services.indexing.CodebaseIndex")
@patch("src.services.indexing._get_embedding", side_effect=_fake_embedding)
@patch("src.services.indexing._chroma_client")
@patch("src.services.indexing._clone_repo")
def test_index_repository_ignored_paths_not_indexed(
    mock_clone: MagicMock,
    mock_chroma: MagicMock,
    mock_embed: MagicMock,
    mock_codebase_index_cls: MagicMock,
    mock_repo_cls: MagicMock,
    tmp_path,
    mock_session: MagicMock,
    repo_row: MagicMock,
    index_row: MagicMock,
):
    mock_clone.return_value = str(tmp_path)
    (tmp_path / "main.py").write_text("def hello(): pass")
    (tmp_path / ".env").write_text("SECRET=bad")
    env_git = tmp_path / ".git"
    env_git.mkdir()
    (env_git / "config").write_text("[core]")

    mock_collection = MagicMock()
    mock_chroma.create_collection.return_value = mock_collection
    
    mock_codebase_index_cls.__name__ = 'CodebaseIndex'
    mock_repo_cls.__name__ = 'Repository'

    from src.services.indexing import _run_index

    _run_index(index_row.id, repo_row.id, "main", mock_session)

    call_kwargs = mock_collection.add.call_args.kwargs
    all_file_paths = [m["file_path"] for m in call_kwargs["metadatas"]]
    assert ".env" not in all_file_paths
    assert not any(".git" in fp for fp in all_file_paths)
    assert "main.py" in all_file_paths


@patch("src.services.indexing.Repository")
@patch("src.services.indexing.CodebaseIndex")
@patch("src.services.indexing._get_embedding", side_effect=_fake_embedding)
@patch("src.services.indexing._chroma_client")
@patch("src.services.indexing._clone_repo")
def test_index_repository_collection_name_convention(
    mock_clone: MagicMock,
    mock_chroma: MagicMock,
    mock_embed: MagicMock,
    mock_codebase_index_cls: MagicMock,
    mock_repo_cls: MagicMock,
    tmp_path,
    mock_session: MagicMock,
    repo_row: MagicMock,
    index_row: MagicMock,
):
    mock_clone.return_value = str(tmp_path)
    (tmp_path / "app.py").write_text("x = 1")

    mock_collection = MagicMock()
    mock_chroma.create_collection.return_value = mock_collection

    mock_codebase_index_cls.__name__ = 'CodebaseIndex'
    mock_repo_cls.__name__ = 'Repository'

    from src.services.indexing import _run_index

    _run_index(index_row.id, repo_row.id, "main", mock_session)

    expected_name = index_row.chroma_collection_name
    mock_chroma.create_collection.assert_called_with(expected_name)


@patch("src.services.indexing.Repository")
@patch("src.services.indexing.CodebaseIndex")
@patch("src.services.indexing._get_embedding", side_effect=_fake_embedding)
@patch("src.services.indexing._chroma_client")
@patch("src.services.indexing._clone_repo")
def test_index_repository_chunk_count_positive(
    mock_clone: MagicMock,
    mock_chroma: MagicMock,
    mock_embed: MagicMock,
    mock_codebase_index_cls: MagicMock,
    mock_repo_cls: MagicMock,
    tmp_path,
    mock_session: MagicMock,
    repo_row: MagicMock,
    index_row: MagicMock,
):
    mock_clone.return_value = str(tmp_path)
    (tmp_path / "app.py").write_text("def foo(): pass\ndef bar(): return 1")

    mock_collection = MagicMock()
    mock_chroma.create_collection.return_value = mock_collection
    
    mock_codebase_index_cls.__name__ = 'CodebaseIndex'
    mock_repo_cls.__name__ = 'Repository'

    from src.services.indexing import _run_index

    _run_index(index_row.id, repo_row.id, "main", mock_session)

    assert index_row.chunk_count > 0