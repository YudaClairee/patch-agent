import uuid
from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest


@pytest.fixture(name="session")
def session_fixture():
    session = MagicMock()
    session.exec.return_value.first.return_value = None
    session.refresh.side_effect = lambda _: None
    return session


def _make_mock_github_repo(
    owner: str = "octocat",
    name: str = "Hello-World",
):
    mock_repo = MagicMock()
    mock_repo.id = 1296269
    mock_repo.clone_url = f"https://github.com/{owner}/{name}.git"
    mock_repo.default_branch = "main"
    mock_repo.language = "Python"
    return mock_repo


@patch("src.services.repositories.Repository")
@patch("src.services.repositories.select")
@patch("src.services.repositories.Github")
def test_connect_repo_creates_repository_row(
    mock_github_cls: MagicMock,
    mock_select: MagicMock,
    mock_repository_cls: MagicMock,
    session: MagicMock,
):
    mock_select.return_value.where.return_value = MagicMock()

    mock_github_cls.return_value.get_repo.return_value = _make_mock_github_repo()

    created_repo = MagicMock()
    created_repo.github_owner = "octocat"
    created_repo.github_repo = "Hello-World"
    created_repo.default_branch = "main"
    created_repo.clone_url = "https://github.com/octocat/Hello-World.git"
    created_repo.user_id = UUID("550e8400-e29b-41d4-a716-446655440000")
    created_repo.github_repo_id = 1296269

    mock_repository_cls.return_value = created_repo

    from src.services.repositories import connect_repo

    repo = connect_repo(
        user_id=UUID("550e8400-e29b-41d4-a716-446655440000"),
        owner="octocat",
        name="Hello-World",
        pat="ghp_test_token",
        session=session,
    )

    assert repo.github_owner == "octocat"
    assert repo.github_repo == "Hello-World"
    assert repo.default_branch == "main"
    assert repo.clone_url == "https://github.com/octocat/Hello-World.git"
    assert repo.user_id == UUID("550e8400-e29b-41d4-a716-446655440000")
    assert repo.github_repo_id == 1296269

    session.add.assert_called_once_with(created_repo)
    session.commit.assert_called_once()
    session.refresh.assert_called_once_with(created_repo)


@patch("src.services.repositories.Github")
def test_connect_repo_raises_on_invalid_repo(
    mock_github_cls: MagicMock,
    session: MagicMock,
):
    from github import GithubException
    from src.services.repositories import connect_repo

    mock_github_cls.return_value.get_repo.side_effect = GithubException(
        404,
        {"message": "Not Found"},
        {},
    )

    with pytest.raises(
        ValueError,
        match="Repository octocat/ghost-repo not found",
    ):
        connect_repo(
            user_id=UUID("550e8400-e29b-41d4-a716-446655440000"),
            owner="octocat",
            name="ghost-repo",
            pat="ghp_test_token",
            session=session,
        )


def test_disconnect_repo_raises_for_non_owner(
    session: MagicMock,
):
    from src.services.repositories import disconnect_repo

    user_id = UUID("550e8400-e29b-41d4-a716-446655440000")
    evil_user_id = UUID("660e8400-e29b-41d4-a716-446655440001")

    repo_id = uuid.uuid4()

    mock_repo = MagicMock()
    mock_repo.user_id = user_id

    session.get.return_value = mock_repo

    with pytest.raises(
        PermissionError,
        match="not authorized",
    ):
        disconnect_repo(
            user_id=evil_user_id,
            repository_id=repo_id,
            session=session,
        )


@patch("src.services.repositories.select")
@patch("src.services.repositories.Github")
def test_connect_repo_returns_existing_on_duplicate(
    mock_github_cls: MagicMock,
    mock_select: MagicMock,
    session: MagicMock,
):
    mock_select.return_value.where.return_value = MagicMock()

    from src.services.repositories import connect_repo

    user_id = UUID("550e8400-e29b-41d4-a716-446655440000")

    existing_repo = MagicMock()
    existing_repo.id = uuid.uuid4()

    session.exec.return_value.first.return_value = existing_repo

    repo = connect_repo(
        user_id=user_id,
        owner="octocat",
        name="Hello-World",
        pat="ghp_test_token",
        session=session,
    )

    assert repo.id == existing_repo.id

    mock_github_cls.assert_not_called()

    session.add.assert_not_called()
    session.commit.assert_not_called()
    session.refresh.assert_not_called()