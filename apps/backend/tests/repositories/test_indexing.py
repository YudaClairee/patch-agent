import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session, SQLModel, create_engine

from src.models.codebase_index import CodebaseIndex
from src.models.repository import Repository
from src.models.enums import IndexStatus

@pytest.fixture(name="engine")
def engine_fixture():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(name="session")
def session_fixture(engine):
    with Session(engine) as session:
        yield session

@pytest.fixture(name="repo_row")
def repo_row_fixture(session: Session) -> Repository:
    repo = Repository(
        user_id=uuid.uuid4(),
        github_owner="octocat",
        github_repo="Hello-World",
        github_repo_id=123456,
        clone_url="https://github.com/octocat/Hello-World.git",
        default_branch="main",
        language="Python",
    )
    session.add(repo)
    session.commit()
    session.refresh(repo)
    return repo

@pytest.fixture(name="index_row")
def index_row_fixture(session: Session, repo_row: Repository) -> CodebaseIndex:
    idx = CodebaseIndex(
        repository_id=repo_row.id,
        branch="main",
        status=IndexStatus.pending,
        chroma_collection_name="repo_test_main_123",
    )
    session.add(idx)
    session.commit()
    session.refresh(idx)
    return idx

def _fake_embedding(_: str) -> list[float]:
    return [0.1, 0.2, 0.3]

@patch("src.services.indexing._get_embedding", side_effect=_fake_embedding)
@patch("src.services.indexing._chroma_client")
@patch("src.services.indexing._clone_repo")
def test_index_repository_transitions_to_ready(
    mock_clone: MagicMock,
    mock_chroma: MagicMock,
    mock_embed: MagicMock,
    tmp_path,
    session: Session,
    repo_row: Repository,
    index_row: CodebaseIndex,
):
    mock_clone.return_value = str(tmp_path)
    (tmp_path / "main.py").write_text("def hello(): pass")

    mock_collection = MagicMock()
    mock_chroma.create_collection.return_value = mock_collection

    from src.services.indexing import _run_index

    _run_index(index_row.id, repo_row.id, "main", session)

    session.refresh(index_row)
    assert index_row.status == IndexStatus.ready
    assert index_row.chunk_count > 0
    assert index_row.indexed_at is not None
    mock_collection.add.assert_called_once()


@patch("src.services.indexing._clone_repo")
def test_index_repository_transitions_to_failed_on_clone_error(
    mock_clone: MagicMock,
    session: Session,
    repo_row: Repository,
    index_row: CodebaseIndex,
):
    mock_clone.side_effect = RuntimeError("Clone failed: repo not found")

    from src.services.indexing import _run_index

    _run_index(index_row.id, repo_row.id, "main", session)

    session.refresh(index_row)
    assert index_row.status == IndexStatus.failed
    assert index_row.error_message is not None
    assert "Clone failed" in index_row.error_message

@patch("src.services.indexing._get_embedding", side_effect=_fake_embedding)
@patch("src.services.indexing._chroma_client")
@patch("src.services.indexing._clone_repo")
def test_index_repository_ignored_paths_not_indexed(
    mock_clone: MagicMock,
    mock_chroma: MagicMock,
    mock_embed: MagicMock,
    tmp_path,
    session: Session,
    repo_row: Repository,
    index_row: CodebaseIndex,
):
    mock_clone.return_value = str(tmp_path)
    (tmp_path / "main.py").write_text("def hello(): pass")
    (tmp_path / ".env").write_text("SECRET=bad")
    env_git = tmp_path / ".git"
    env_git.mkdir()
    (env_git / "config").write_text("[core]")

    mock_collection = MagicMock()
    mock_chroma.create_collection.return_value = mock_collection

    from src.services.indexing import _run_index

    _run_index(index_row.id, repo_row.id, "main", session)

    call_kwargs = mock_collection.add.call_args.kwargs
    all_file_paths = [m["file_path"] for m in call_kwargs["metadatas"]]
    assert ".env" not in all_file_paths
    assert not any(".git" in fp for fp in all_file_paths)
    assert "main.py" in all_file_paths

@patch("src.services.indexing._get_embedding", side_effect=_fake_embedding)
@patch("src.services.indexing._chroma_client")
@patch("src.services.indexing._clone_repo")
def test_index_repository_chunk_count_positive(
    mock_clone: MagicMock,
    mock_chroma: MagicMock,
    mock_embed: MagicMock,
    tmp_path,
    session: Session,
    repo_row: Repository,
    index_row: CodebaseIndex,
):
    mock_clone.return_value = str(tmp_path)
    (tmp_path / "app.py").write_text("def foo(): pass\ndef bar(): return 1")

    mock_collection = MagicMock()
    mock_chroma.create_collection.return_value = mock_collection

    from src.services.indexing import _run_index

    _run_index(index_row.id, repo_row.id, "main", session)

    session.refresh(index_row)
    assert index_row.chunk_count > 0